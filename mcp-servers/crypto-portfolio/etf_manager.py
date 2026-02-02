"""
GTI Virtual ETF Manager
========================

Core class that manages the 50+1 asset virtual ETF:
- Reads current portfolio from the aggregator
- Compares against target allocations
- Generates daily DCA orders (prioritizing most underweight)
- Handles war chest deployment/refill based on Fear & Greed
- Tracks ETF NAV over time
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional

from etf_config import (
    AssetCategory,
    ETF_ASSETS,
    ETF_DAILY_BUDGET,
    ExchangeRoute,
    LOCKED_ASSETS,
    MIN_ORDER_USD,
    REBALANCE_BAND_PCT,
    get_war_chest_rule,
    validate_weights,
)

logger = logging.getLogger(__name__)

NAV_HISTORY_PATH = Path(os.environ.get(
    "NAV_HISTORY_PATH",
    os.path.expanduser("~/skippy/work/crypto/etf_nav_history.json")
))


@dataclass
class AssetAllocation:
    """Current vs target allocation for a single asset."""
    symbol: str
    category: AssetCategory
    target_pct: Decimal
    current_pct: Decimal
    current_value_usd: Decimal
    target_value_usd: Decimal
    drift_pct: Decimal         # current_pct - target_pct
    exchange: ExchangeRoute
    is_locked: bool = False

    @property
    def is_underweight(self) -> bool:
        return self.drift_pct < -REBALANCE_BAND_PCT and not self.is_locked

    @property
    def is_overweight(self) -> bool:
        return self.drift_pct > REBALANCE_BAND_PCT


@dataclass
class DCAOrder:
    """A single DCA buy order to execute."""
    symbol: str
    exchange: ExchangeRoute
    amount_usd: Decimal
    reason: str
    category: AssetCategory
    priority: int = 0  # lower = higher priority


@dataclass
class ETFStatus:
    """Complete ETF status snapshot."""
    timestamp: str
    nav_usd: Decimal
    allocations: List[AssetAllocation]
    war_chest_usd: Decimal
    war_chest_pct: Decimal
    fear_greed: int
    war_chest_rule: str
    assets_count: int
    categories: Dict[str, Dict[str, Any]]


class GTIVirtualETF:
    """Manages the GTI 50+1 virtual ETF."""

    def __init__(self):
        if not validate_weights():
            raise ValueError("ETF weights do not sum to 100%")
        self._nav_history: List[dict] = []
        self._load_nav_history()

    def _load_nav_history(self):
        if NAV_HISTORY_PATH.exists():
            try:
                with open(NAV_HISTORY_PATH) as f:
                    self._nav_history = json.load(f)
            except Exception:
                self._nav_history = []

    def _save_nav_history(self):
        NAV_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(NAV_HISTORY_PATH, "w") as f:
            json.dump(self._nav_history[-365:], f, indent=2, default=str)

    # ------------------------------------------------------------------
    # Core: Calculate Allocations
    # ------------------------------------------------------------------

    def calculate_allocations(
        self,
        holdings_by_symbol: Dict[str, Decimal],
        prices: Dict[str, Decimal],
    ) -> List[AssetAllocation]:
        """Compare current holdings against ETF targets.

        Args:
            holdings_by_symbol: symbol -> total quantity across all accounts
            prices: symbol -> USD price

        Returns:
            List of AssetAllocation sorted by drift (most underweight first)
        """
        # Calculate total ETF value (only ETF assets)
        total_value = Decimal("0")
        asset_values: Dict[str, Decimal] = {}

        for symbol, asset_cfg in ETF_ASSETS.items():
            qty = holdings_by_symbol.get(symbol, Decimal("0"))
            price = prices.get(symbol, Decimal("0"))
            value = qty * price
            asset_values[symbol] = value
            total_value += value

        # Also count non-ETF holdings that exist in the portfolio
        # (they contribute to total but have 0% target)
        for symbol, qty in holdings_by_symbol.items():
            if symbol not in ETF_ASSETS and symbol not in ("USD", "EUR", "GBP"):
                price = prices.get(symbol, Decimal("0"))
                value = qty * price
                if value > Decimal("0.01"):
                    total_value += value

        if total_value == 0:
            total_value = Decimal("1")  # avoid division by zero

        allocations = []
        for symbol, asset_cfg in ETF_ASSETS.items():
            value = asset_values.get(symbol, Decimal("0"))
            current_pct = (value / total_value * 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
            target_pct = asset_cfg.target_weight_pct
            drift = current_pct - target_pct

            target_value = total_value * target_pct / 100

            allocations.append(AssetAllocation(
                symbol=symbol,
                category=asset_cfg.category,
                target_pct=target_pct,
                current_pct=current_pct,
                current_value_usd=value,
                target_value_usd=target_value,
                drift_pct=drift,
                exchange=asset_cfg.exchange,
                is_locked=symbol in LOCKED_ASSETS,
            ))

        # Sort: most underweight first
        allocations.sort(key=lambda a: a.drift_pct)
        return allocations

    # ------------------------------------------------------------------
    # DCA Order Generation
    # ------------------------------------------------------------------

    def generate_dca_orders(
        self,
        allocations: List[AssetAllocation],
        fear_greed: int = 50,
        daily_budget: Optional[Decimal] = None,
    ) -> List[DCAOrder]:
        """Generate today's DCA buy orders prioritizing underweight assets.

        Args:
            allocations: output of calculate_allocations()
            fear_greed: current Fear & Greed index (0-100)
            daily_budget: override ETF daily budget

        Returns:
            List of DCAOrder to execute
        """
        budget = daily_budget or ETF_DAILY_BUDGET
        wc_rule = get_war_chest_rule(fear_greed)
        orders: List[DCAOrder] = []

        # Separate war chest from crypto assets
        usdc_alloc = next((a for a in allocations if a.symbol == "USDC"), None)
        crypto_allocs = [a for a in allocations if a.symbol != "USDC" and not a.is_locked]

        # --- War Chest allocation ---
        # In greed: increase USDC target; in fear: decrease
        wc_budget = budget * wc_rule.target_usdc_pct / Decimal("100")
        crypto_budget = budget - wc_budget

        if wc_budget >= MIN_ORDER_USD:
            orders.append(DCAOrder(
                symbol="USDC",
                exchange=ExchangeRoute.COINBASE_GTI,
                amount_usd=wc_budget.quantize(Decimal("0.01")),
                reason=f"War chest ({wc_rule.label}, F&G={fear_greed})",
                category=AssetCategory.WAR_CHEST,
                priority=99,
            ))

        # --- Deploy war chest in fear conditions ---
        deploy_orders = self._deploy_war_chest(
            allocations, fear_greed, usdc_alloc
        )
        orders.extend(deploy_orders)

        # --- Distribute remaining budget to underweight crypto assets ---
        # Weight by how underweight each asset is
        underweight = [a for a in crypto_allocs if a.drift_pct < 0]

        if not underweight:
            # Everything at or above target - distribute proportionally to targets
            underweight = crypto_allocs

        total_deficit = sum(abs(a.drift_pct) for a in underweight)
        if total_deficit == 0:
            total_deficit = Decimal("1")

        for i, alloc in enumerate(underweight):
            weight = abs(alloc.drift_pct) / total_deficit
            amount = (crypto_budget * weight).quantize(Decimal("0.01"), ROUND_HALF_UP)

            if amount >= MIN_ORDER_USD:
                orders.append(DCAOrder(
                    symbol=alloc.symbol,
                    exchange=alloc.exchange,
                    amount_usd=amount,
                    reason=f"DCA underweight ({alloc.drift_pct:+.1f}% drift)",
                    category=alloc.category,
                    priority=i,
                ))

        return orders

    # ------------------------------------------------------------------
    # War Chest Deployment
    # ------------------------------------------------------------------

    def _deploy_war_chest(
        self,
        allocations: List[AssetAllocation],
        fear_greed: int,
        usdc_alloc: Optional[AssetAllocation],
    ) -> List[DCAOrder]:
        """Deploy USDC war chest into underweight assets during fear.

        Returns additional DCA orders funded from war chest.
        """
        wc_rule = get_war_chest_rule(fear_greed)

        if wc_rule.deploy_pct <= 0 or usdc_alloc is None:
            return []

        available_usdc = usdc_alloc.current_value_usd
        deploy_amount = (available_usdc * wc_rule.deploy_pct / 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        if deploy_amount < MIN_ORDER_USD:
            return []

        # Deploy into most underweight non-locked, non-USDC assets
        underweight = [
            a for a in allocations
            if a.symbol != "USDC" and not a.is_locked and a.drift_pct < 0
        ]
        if not underweight:
            return []

        total_deficit = sum(abs(a.drift_pct) for a in underweight)
        if total_deficit == 0:
            return []

        orders = []
        for i, alloc in enumerate(underweight[:10]):  # top 10 most underweight
            weight = abs(alloc.drift_pct) / total_deficit
            amount = (deploy_amount * weight).quantize(Decimal("0.01"), ROUND_HALF_UP)

            if amount >= MIN_ORDER_USD:
                orders.append(DCAOrder(
                    symbol=alloc.symbol,
                    exchange=alloc.exchange,
                    amount_usd=amount,
                    reason=f"War chest deploy ({wc_rule.label}, {wc_rule.deploy_pct}% of USDC)",
                    category=alloc.category,
                    priority=100 + i,
                ))

        return orders

    # ------------------------------------------------------------------
    # NAV Tracking
    # ------------------------------------------------------------------

    def get_etf_nav(
        self,
        holdings_by_symbol: Dict[str, Decimal],
        prices: Dict[str, Decimal],
    ) -> Decimal:
        """Calculate current Net Asset Value of ETF holdings only."""
        nav = Decimal("0")
        for symbol in ETF_ASSETS:
            qty = holdings_by_symbol.get(symbol, Decimal("0"))
            price = prices.get(symbol, Decimal("0"))
            nav += qty * price
        return nav

    def record_nav(
        self,
        holdings_by_symbol: Dict[str, Decimal],
        prices: Dict[str, Decimal],
    ):
        """Record a NAV snapshot."""
        nav = self.get_etf_nav(holdings_by_symbol, prices)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "nav_usd": str(nav),
        }
        self._nav_history.append(entry)
        self._save_nav_history()

    # ------------------------------------------------------------------
    # Performance
    # ------------------------------------------------------------------

    def get_etf_performance(self) -> Dict[str, Any]:
        """Calculate ETF performance from NAV history."""
        if len(self._nav_history) < 2:
            return {"message": "Insufficient NAV history for performance calculation"}

        current = Decimal(self._nav_history[-1]["nav_usd"])
        first = Decimal(self._nav_history[0]["nav_usd"])

        total_return = ((current - first) / first * 100) if first > 0 else Decimal("0")

        # 7-day return
        seven_day_return = None
        if len(self._nav_history) >= 7:
            nav_7d = Decimal(self._nav_history[-7]["nav_usd"])
            if nav_7d > 0:
                seven_day_return = (current - nav_7d) / nav_7d * 100

        return {
            "current_nav": str(current),
            "first_nav": str(first),
            "total_return_pct": str(total_return.quantize(Decimal("0.01"))),
            "seven_day_return_pct": str(seven_day_return.quantize(Decimal("0.01"))) if seven_day_return else None,
            "data_points": len(self._nav_history),
        }

    # ------------------------------------------------------------------
    # Full Status
    # ------------------------------------------------------------------

    def get_etf_status(
        self,
        holdings_by_symbol: Dict[str, Decimal],
        prices: Dict[str, Decimal],
        fear_greed: int = 50,
    ) -> ETFStatus:
        """Get complete ETF status."""
        allocations = self.calculate_allocations(holdings_by_symbol, prices)
        nav = self.get_etf_nav(holdings_by_symbol, prices)
        wc_rule = get_war_chest_rule(fear_greed)

        usdc_alloc = next((a for a in allocations if a.symbol == "USDC"), None)
        war_chest_usd = usdc_alloc.current_value_usd if usdc_alloc else Decimal("0")
        war_chest_pct = usdc_alloc.current_pct if usdc_alloc else Decimal("0")

        # Category summaries
        categories: Dict[str, Dict[str, Any]] = {}
        for cat in AssetCategory:
            cat_allocs = [a for a in allocations if a.category == cat]
            cat_value = sum(a.current_value_usd for a in cat_allocs)
            cat_target = sum(a.target_pct for a in cat_allocs)
            cat_current = sum(a.current_pct for a in cat_allocs)
            categories[cat.value] = {
                "value_usd": str(cat_value),
                "target_pct": str(cat_target),
                "current_pct": str(cat_current),
                "drift_pct": str(cat_current - cat_target),
                "assets": len(cat_allocs),
            }

        return ETFStatus(
            timestamp=datetime.now().isoformat(),
            nav_usd=nav,
            allocations=allocations,
            war_chest_usd=war_chest_usd,
            war_chest_pct=war_chest_pct,
            fear_greed=fear_greed,
            war_chest_rule=wc_rule.label,
            assets_count=len(ETF_ASSETS),
            categories=categories,
        )

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def format_status_markdown(self, status: ETFStatus) -> str:
        """Format ETF status as markdown."""
        md = f"""# GTI Virtual ETF Status

**NAV:** ${status.nav_usd:,.2f}
**Assets:** {status.assets_count}
**Fear & Greed:** {status.fear_greed} ({status.war_chest_rule})
**War Chest:** ${status.war_chest_usd:,.2f} ({status.war_chest_pct:.1f}%)
**Timestamp:** {status.timestamp}

## Category Breakdown
| Category | Value | Target | Current | Drift |
|----------|-------|--------|---------|-------|
"""
        for cat_name, cat_data in status.categories.items():
            md += f"| {cat_name} | ${Decimal(cat_data['value_usd']):,.2f} | {cat_data['target_pct']}% | {Decimal(cat_data['current_pct']):.1f}% | {Decimal(cat_data['drift_pct']):+.1f}% |\n"

        # Top 10 most underweight
        underweight = [a for a in status.allocations if a.drift_pct < 0 and not a.is_locked][:10]
        if underweight:
            md += "\n## Most Underweight Assets\n"
            md += "| Asset | Target | Current | Drift | Value |\n"
            md += "|-------|--------|---------|-------|-------|\n"
            for a in underweight:
                md += f"| {a.symbol} | {a.target_pct}% | {a.current_pct}% | {a.drift_pct:+.1f}% | ${a.current_value_usd:,.2f} |\n"

        # Top 5 overweight
        overweight = [a for a in status.allocations if a.drift_pct > REBALANCE_BAND_PCT][:5]
        if overweight:
            md += "\n## Overweight Assets (DCA paused)\n"
            md += "| Asset | Target | Current | Drift |\n"
            md += "|-------|--------|---------|-------|\n"
            for a in overweight:
                md += f"| {a.symbol} | {a.target_pct}% | {a.current_pct}% | {a.drift_pct:+.1f}% |\n"

        return md

    def format_orders_markdown(self, orders: List[DCAOrder]) -> str:
        """Format DCA orders as markdown."""
        if not orders:
            return "No DCA orders to execute today."

        total = sum(o.amount_usd for o in orders)
        md = f"""# Today's DCA Orders

**Total:** ${total:,.2f}
**Orders:** {len(orders)}

## Orders by Exchange

"""
        # Group by exchange
        by_exchange: Dict[str, List[DCAOrder]] = {}
        for o in orders:
            ex = o.exchange.value
            by_exchange.setdefault(ex, []).append(o)

        for exchange, ex_orders in by_exchange.items():
            ex_total = sum(o.amount_usd for o in ex_orders)
            md += f"### {exchange} (${ex_total:,.2f})\n"
            md += "| Asset | Amount | Category | Reason |\n"
            md += "|-------|--------|----------|--------|\n"
            for o in sorted(ex_orders, key=lambda x: x.amount_usd, reverse=True):
                md += f"| {o.symbol} | ${o.amount_usd:,.2f} | {o.category.value} | {o.reason} |\n"
            md += "\n"

        return md

    def format_status_json(self, status: ETFStatus) -> dict:
        """Format ETF status as JSON-serializable dict."""
        return {
            "timestamp": status.timestamp,
            "nav_usd": str(status.nav_usd),
            "assets_count": status.assets_count,
            "fear_greed": status.fear_greed,
            "war_chest_rule": status.war_chest_rule,
            "war_chest_usd": str(status.war_chest_usd),
            "war_chest_pct": str(status.war_chest_pct),
            "categories": status.categories,
            "allocations": [
                {
                    "symbol": a.symbol,
                    "category": a.category.value,
                    "target_pct": str(a.target_pct),
                    "current_pct": str(a.current_pct),
                    "current_value_usd": str(a.current_value_usd),
                    "drift_pct": str(a.drift_pct),
                    "exchange": a.exchange.value,
                    "is_locked": a.is_locked,
                }
                for a in status.allocations
            ],
            "performance": self.get_etf_performance(),
        }
