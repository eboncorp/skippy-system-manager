"""
Tax Loss Harvesting Detection and Optimization.

Identifies opportunities to realize losses for tax benefits while
maintaining market exposure through correlated assets.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from enum import Enum


class HarvestingStrategy(Enum):
    """Tax loss harvesting strategies."""
    DIRECT_SWAP = "direct_swap"  # Sell losing asset, buy correlated asset
    WAIT_30_DAYS = "wait_30_days"  # Sell and wait to avoid wash sale
    PARTIAL_HARVEST = "partial_harvest"  # Harvest portion of loss


@dataclass
class TaxLot:
    """Represents a tax lot (purchase) of an asset."""
    asset: str
    amount: Decimal
    cost_basis: Decimal  # Total cost basis
    acquisition_date: datetime
    source: str = ""  # Exchange where held

    @property
    def cost_per_unit(self) -> Decimal:
        """Cost per unit of asset."""
        if self.amount == 0:
            return Decimal("0")
        return self.cost_basis / self.amount

    @property
    def is_long_term(self) -> bool:
        """True if held over 1 year (qualifies for long-term rates)."""
        return (datetime.now() - self.acquisition_date).days > 365

    @property
    def holding_days(self) -> int:
        """Number of days held."""
        return (datetime.now() - self.acquisition_date).days


@dataclass
class HarvestOpportunity:
    """Represents a tax loss harvesting opportunity."""
    asset: str
    tax_lots: List[TaxLot]
    current_price: Decimal
    unrealized_loss: Decimal
    loss_percent: Decimal
    recommended_action: HarvestingStrategy
    replacement_assets: List[str]
    estimated_tax_savings: Decimal
    wash_sale_warning: bool = False
    notes: str = ""

    @property
    def total_amount(self) -> Decimal:
        """Total amount across all lots."""
        return sum(lot.amount for lot in self.tax_lots)

    @property
    def total_cost_basis(self) -> Decimal:
        """Total cost basis across all lots."""
        return sum(lot.cost_basis for lot in self.tax_lots)

    @property
    def current_value(self) -> Decimal:
        """Current market value."""
        return self.total_amount * self.current_price


@dataclass
class WashSaleRisk:
    """Tracks potential wash sale violations."""
    asset: str
    sale_date: datetime
    sale_amount: Decimal
    loss_amount: Decimal
    wash_sale_window_end: datetime
    replacement_purchases: List[dict] = field(default_factory=list)

    @property
    def is_in_wash_window(self) -> bool:
        """Check if still in 61-day wash sale window."""
        return datetime.now() < self.wash_sale_window_end

    @property
    def disallowed_loss(self) -> Decimal:
        """Amount of loss disallowed due to wash sales."""
        if not self.replacement_purchases:
            return Decimal("0")

        # Loss is disallowed proportionally to repurchased amount
        repurchased = sum(
            Decimal(str(p.get("amount", 0)))
            for p in self.replacement_purchases
        )

        if repurchased >= self.sale_amount:
            return self.loss_amount

        return self.loss_amount * (repurchased / self.sale_amount)


# Correlation data for replacement assets (assets that move similarly)
# These maintain market exposure while avoiding wash sales
CORRELATED_ASSETS: Dict[str, List[str]] = {
    "BTC": ["WBTC", "MSTR", "BITO"],  # Wrapped BTC, MicroStrategy, BTC ETF
    "ETH": ["WETH", "stETH", "rETH"],  # Wrapped/staked ETH variants
    "SOL": ["BONK", "JTO", "RAY"],  # Solana ecosystem
    "AVAX": ["JOE", "GMX", "QI"],  # Avalanche ecosystem
    "MATIC": ["SAND", "MANA", "AAVE"],  # Polygon ecosystem
    "ADA": ["WMT", "AGIX", "COTI"],  # Cardano ecosystem
    "DOT": ["GLMR", "ASTR", "ACA"],  # Polkadot ecosystem
    "LINK": ["GRT", "API3", "BAND"],  # Oracle tokens
    "UNI": ["SUSHI", "CRV", "BAL"],  # DEX tokens
    "AAVE": ["COMP", "MKR", "SNX"],  # DeFi lending
    "LTC": ["BCH", "DOGE", "XMR"],  # Payment coins
    "XRP": ["XLM", "ALGO", "HBAR"],  # Payment/settlement
    "ATOM": ["OSMO", "JUNO", "SCRT"],  # Cosmos ecosystem
    "NEAR": ["AURORA", "OCT", "REF"],  # NEAR ecosystem
    "FTM": ["BOO", "SPIRIT", "TOMB"],  # Fantom ecosystem
}


class TaxLossHarvester:
    """
    Detects and manages tax loss harvesting opportunities.

    Tax loss harvesting allows investors to:
    1. Sell assets at a loss to offset capital gains
    2. Reduce taxable income (up to $3,000/year against ordinary income)
    3. Carry forward unused losses to future years

    Important: Must avoid wash sales (repurchasing substantially identical
    assets within 30 days before or after the sale).
    """

    def __init__(
        self,
        tax_rate_short_term: Decimal = Decimal("0.35"),  # 35% default
        tax_rate_long_term: Decimal = Decimal("0.15"),  # 15% default
        min_loss_threshold: Decimal = Decimal("100"),  # Minimum loss to consider
        min_loss_percent: Decimal = Decimal("5"),  # Minimum % loss
    ):
        self.tax_rate_short_term = tax_rate_short_term
        self.tax_rate_long_term = tax_rate_long_term
        self.min_loss_threshold = min_loss_threshold
        self.min_loss_percent = min_loss_percent
        self.wash_sale_tracker: Dict[str, WashSaleRisk] = {}

    def find_opportunities(
        self,
        tax_lots: List[TaxLot],
        current_prices: Dict[str, Decimal],
        recent_gains: Decimal = Decimal("0"),
    ) -> List[HarvestOpportunity]:
        """
        Find tax loss harvesting opportunities in portfolio.

        Args:
            tax_lots: List of all tax lots in portfolio
            current_prices: Current market prices by asset
            recent_gains: Capital gains realized this year (to offset)

        Returns:
            List of HarvestOpportunity objects, sorted by estimated savings
        """
        opportunities = []

        # Group lots by asset
        lots_by_asset: Dict[str, List[TaxLot]] = {}
        for lot in tax_lots:
            if lot.asset not in lots_by_asset:
                lots_by_asset[lot.asset] = []
            lots_by_asset[lot.asset].append(lot)

        # Analyze each asset
        for asset, lots in lots_by_asset.items():
            if asset not in current_prices:
                continue

            current_price = current_prices[asset]

            # Find lots with unrealized losses
            loss_lots = []
            total_loss = Decimal("0")
            total_cost_basis = Decimal("0")

            for lot in lots:
                current_value = lot.amount * current_price
                unrealized_pnl = current_value - lot.cost_basis

                if unrealized_pnl < 0:
                    loss_lots.append(lot)
                    total_loss += abs(unrealized_pnl)
                    total_cost_basis += lot.cost_basis

            if not loss_lots:
                continue

            # Calculate loss percentage
            if total_cost_basis > 0:
                loss_percent = (total_loss / total_cost_basis) * 100
            else:
                loss_percent = Decimal("0")

            # Check if meets thresholds
            if total_loss < self.min_loss_threshold:
                continue
            if loss_percent < self.min_loss_percent:
                continue

            # Determine best strategy
            strategy = self._determine_strategy(asset, loss_lots)

            # Get replacement assets
            replacements = CORRELATED_ASSETS.get(asset, [])

            # Calculate estimated tax savings
            tax_savings = self._estimate_tax_savings(
                loss_lots, total_loss, recent_gains
            )

            # Check for wash sale risk
            wash_warning = self._check_wash_sale_risk(asset)

            opportunity = HarvestOpportunity(
                asset=asset,
                tax_lots=loss_lots,
                current_price=current_price,
                unrealized_loss=total_loss,
                loss_percent=loss_percent,
                recommended_action=strategy,
                replacement_assets=replacements,
                estimated_tax_savings=tax_savings,
                wash_sale_warning=wash_warning,
                notes=self._generate_notes(asset, loss_lots, strategy),
            )

            opportunities.append(opportunity)

        # Sort by estimated tax savings (highest first)
        opportunities.sort(key=lambda x: x.estimated_tax_savings, reverse=True)

        return opportunities

    def _determine_strategy(
        self,
        asset: str,
        loss_lots: List[TaxLot],
    ) -> HarvestingStrategy:
        """Determine best harvesting strategy."""
        # If correlated assets available, recommend direct swap
        if asset in CORRELATED_ASSETS and CORRELATED_ASSETS[asset]:
            return HarvestingStrategy.DIRECT_SWAP

        # If small position, wait 30 days
        total_value = sum(lot.cost_basis for lot in loss_lots)
        if total_value < Decimal("1000"):
            return HarvestingStrategy.WAIT_30_DAYS

        # For larger positions without good replacements, partial harvest
        return HarvestingStrategy.PARTIAL_HARVEST

    def _estimate_tax_savings(
        self,
        loss_lots: List[TaxLot],
        total_loss: Decimal,
        recent_gains: Decimal,
    ) -> Decimal:
        """Estimate tax savings from harvesting losses."""
        savings = Decimal("0")
        remaining_loss = total_loss

        # First, offset capital gains
        if recent_gains > 0:
            offset = min(remaining_loss, recent_gains)

            # Calculate weighted average tax rate for lots
            short_term_loss = sum(
                lot.cost_basis - (lot.amount * lot.cost_per_unit)
                for lot in loss_lots
                if not lot.is_long_term
            )

            # Use appropriate rate
            if short_term_loss > total_loss * Decimal("0.5"):
                savings += offset * self.tax_rate_short_term
            else:
                savings += offset * self.tax_rate_long_term

            remaining_loss -= offset

        # Can offset up to $3,000 of ordinary income
        ordinary_income_offset = min(remaining_loss, Decimal("3000"))
        savings += ordinary_income_offset * self.tax_rate_short_term

        return savings.quantize(Decimal("0.01"))

    def _check_wash_sale_risk(self, asset: str) -> bool:
        """Check if asset has wash sale risk from recent activity."""
        if asset in self.wash_sale_tracker:
            return self.wash_sale_tracker[asset].is_in_wash_window
        return False

    def _generate_notes(
        self,
        asset: str,
        loss_lots: List[TaxLot],
        strategy: HarvestingStrategy,
    ) -> str:
        """Generate helpful notes for the opportunity."""
        notes = []

        # Holding period info
        long_term_lots = [lot for lot in loss_lots if lot.is_long_term]
        short_term_lots = [lot for lot in loss_lots if not lot.is_long_term]

        if long_term_lots:
            notes.append(f"{len(long_term_lots)} lots qualify as long-term")
        if short_term_lots:
            notes.append(f"{len(short_term_lots)} lots are short-term")

        # Strategy-specific notes
        if strategy == HarvestingStrategy.DIRECT_SWAP:
            replacements = CORRELATED_ASSETS.get(asset, [])
            if replacements:
                notes.append(f"Consider swapping to: {', '.join(replacements[:3])}")
        elif strategy == HarvestingStrategy.WAIT_30_DAYS:
            notes.append("Small position - wait 30+ days before repurchasing")
        else:
            notes.append("Consider harvesting 50% to maintain some exposure")

        return "; ".join(notes)

    def record_harvest(
        self,
        asset: str,
        sale_amount: Decimal,
        loss_amount: Decimal,
        sale_date: Optional[datetime] = None,
    ) -> WashSaleRisk:
        """
        Record a tax loss harvest to track wash sale window.

        Args:
            asset: Asset sold
            sale_amount: Amount sold
            loss_amount: Loss realized
            sale_date: Date of sale (defaults to now)

        Returns:
            WashSaleRisk tracker for this sale
        """
        if sale_date is None:
            sale_date = datetime.now()

        # Wash sale window is 30 days before and after sale (61 days total)
        window_end = sale_date + timedelta(days=30)

        wash_risk = WashSaleRisk(
            asset=asset,
            sale_date=sale_date,
            sale_amount=sale_amount,
            loss_amount=loss_amount,
            wash_sale_window_end=window_end,
        )

        self.wash_sale_tracker[asset] = wash_risk
        return wash_risk

    def record_purchase(
        self,
        asset: str,
        amount: Decimal,
        purchase_date: Optional[datetime] = None,
    ) -> Optional[Decimal]:
        """
        Record a purchase that may trigger wash sale.

        Args:
            asset: Asset purchased
            amount: Amount purchased
            purchase_date: Date of purchase (defaults to now)

        Returns:
            Disallowed loss amount if wash sale triggered, None otherwise
        """
        if asset not in self.wash_sale_tracker:
            return None

        wash_risk = self.wash_sale_tracker[asset]

        if not wash_risk.is_in_wash_window:
            return None

        if purchase_date is None:
            purchase_date = datetime.now()

        # Record the replacement purchase
        wash_risk.replacement_purchases.append({
            "amount": str(amount),
            "date": purchase_date.isoformat(),
        })

        return wash_risk.disallowed_loss

    def get_wash_sale_calendar(self) -> List[Dict]:
        """
        Get calendar of wash sale windows.

        Returns:
            List of dicts with asset and window end dates
        """
        calendar = []

        for asset, risk in self.wash_sale_tracker.items():
            if risk.is_in_wash_window:
                calendar.append({
                    "asset": asset,
                    "sale_date": risk.sale_date.isoformat(),
                    "window_ends": risk.wash_sale_window_end.isoformat(),
                    "days_remaining": (risk.wash_sale_window_end - datetime.now()).days,
                    "loss_at_risk": str(risk.loss_amount),
                })

        calendar.sort(key=lambda x: x["window_ends"])
        return calendar

    def generate_harvest_plan(
        self,
        opportunities: List[HarvestOpportunity],
        target_loss: Optional[Decimal] = None,
        max_positions: int = 5,
    ) -> Dict:
        """
        Generate an actionable harvest plan.

        Args:
            opportunities: List of harvest opportunities
            target_loss: Target loss amount to realize (optional)
            max_positions: Maximum positions to harvest

        Returns:
            Dict with harvest plan details
        """
        plan = {
            "actions": [],
            "total_loss_to_harvest": Decimal("0"),
            "estimated_tax_savings": Decimal("0"),
            "wash_sale_warnings": [],
        }

        remaining_target = target_loss

        for opp in opportunities[:max_positions]:
            if remaining_target is not None and remaining_target <= 0:
                break

            action = {
                "asset": opp.asset,
                "action": "SELL",
                "amount": str(opp.total_amount),
                "current_value": str(opp.current_value),
                "loss_to_realize": str(opp.unrealized_loss),
                "strategy": opp.recommended_action.value,
            }

            if opp.replacement_assets:
                action["replacement_suggestion"] = opp.replacement_assets[0]

            if opp.wash_sale_warning:
                plan["wash_sale_warnings"].append(opp.asset)

            plan["actions"].append(action)
            plan["total_loss_to_harvest"] += opp.unrealized_loss
            plan["estimated_tax_savings"] += opp.estimated_tax_savings

            if remaining_target is not None:
                remaining_target -= opp.unrealized_loss

        plan["total_loss_to_harvest"] = str(plan["total_loss_to_harvest"])
        plan["estimated_tax_savings"] = str(plan["estimated_tax_savings"])

        return plan


async def analyze_portfolio_for_tlh(
    portfolio_manager,  # Type hint omitted to avoid circular import
    tax_rate_short: Decimal = Decimal("0.35"),
    tax_rate_long: Decimal = Decimal("0.15"),
    ytd_gains: Decimal = Decimal("0"),
) -> Dict:
    """
    Convenience function to analyze portfolio for TLH opportunities.

    Args:
        portfolio_manager: Portfolio manager instance with tax lot data
        tax_rate_short: Short-term capital gains rate
        tax_rate_long: Long-term capital gains rate
        ytd_gains: Year-to-date realized gains

    Returns:
        Dict with opportunities and harvest plan
    """
    harvester = TaxLossHarvester(
        tax_rate_short_term=tax_rate_short,
        tax_rate_long_term=tax_rate_long,
    )

    # Get tax lots from portfolio (implementation depends on portfolio_manager)
    tax_lots = await portfolio_manager.get_tax_lots()
    current_prices = await portfolio_manager.get_current_prices()

    opportunities = harvester.find_opportunities(
        tax_lots=tax_lots,
        current_prices=current_prices,
        recent_gains=ytd_gains,
    )

    plan = harvester.generate_harvest_plan(opportunities)

    return {
        "opportunities": [
            {
                "asset": opp.asset,
                "unrealized_loss": str(opp.unrealized_loss),
                "loss_percent": str(opp.loss_percent),
                "current_value": str(opp.current_value),
                "estimated_savings": str(opp.estimated_tax_savings),
                "strategy": opp.recommended_action.value,
                "replacements": opp.replacement_assets,
                "wash_sale_warning": opp.wash_sale_warning,
                "notes": opp.notes,
            }
            for opp in opportunities
        ],
        "harvest_plan": plan,
        "wash_sale_calendar": harvester.get_wash_sale_calendar(),
        "summary": {
            "total_harvestable_loss": str(sum(o.unrealized_loss for o in opportunities)),
            "total_potential_savings": str(sum(o.estimated_tax_savings for o in opportunities)),
            "opportunities_count": len(opportunities),
        },
    }
