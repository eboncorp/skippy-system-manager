"""
Portfolio tracking and analytics.

Aggregates balances from all exchanges and wallets,
calculates allocation drift, and provides analytics.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from config import TARGET_ALLOCATION, REBALANCE_RULES, get_net_staking_yield
from exchanges import Balance, ExchangeClient
from data.prices import PriceService


@dataclass
class Position:
    """Represents a position in a single asset across all sources."""
    asset: str
    total_amount: Decimal = Decimal("0")
    available_amount: Decimal = Decimal("0")
    staked_amount: Decimal = Decimal("0")
    usd_value: Decimal = Decimal("0")
    price: Decimal = Decimal("0")

    # Breakdown by source
    by_source: Dict[str, Balance] = field(default_factory=dict)

    @property
    def allocation_pct(self) -> Decimal:
        """Allocation percentage (set externally after portfolio total known)."""
        return getattr(self, "_allocation_pct", Decimal("0"))

    @allocation_pct.setter
    def allocation_pct(self, value: Decimal):
        self._allocation_pct = value

    def add_balance(self, source: str, balance: Balance):
        """Add a balance from a source."""
        self.by_source[source] = balance
        self.total_amount += balance.total
        self.available_amount += balance.available
        self.staked_amount += balance.staked


@dataclass
class PortfolioSnapshot:
    """Complete portfolio state at a point in time."""
    timestamp: datetime
    positions: Dict[str, Position]
    total_usd_value: Decimal

    # Allocation analysis
    target_allocation: Dict[str, float]
    actual_allocation: Dict[str, Decimal]
    drift: Dict[str, Decimal]  # Actual - Target

    # Yield analysis
    total_staked_value: Decimal
    expected_annual_yield: Decimal

    def get_drift_status(self, threshold: float = 0.05) -> Dict[str, str]:
        """Get status for each position based on drift threshold."""
        status = {}
        for asset, drift_pct in self.drift.items():
            abs_drift = abs(float(drift_pct))
            if abs_drift > threshold:
                status[asset] = "OVER" if drift_pct > 0 else "UNDER"
            else:
                status[asset] = "OK"
        return status

    def needs_rebalance(self, threshold: float = 0.05) -> bool:
        """Check if any position exceeds drift threshold."""
        return any(abs(float(d)) > threshold for d in self.drift.values())

    def get_rebalance_trades(self) -> List[Tuple[str, str, Decimal]]:
        """
        Calculate trades needed to rebalance.

        Returns:
            List of (asset, side, usd_amount) tuples
        """
        trades = []

        for asset, drift_pct in self.drift.items():
            if asset == "CASH":
                continue

            drift_value = float(drift_pct) * float(self.total_usd_value)

            if abs(drift_value) < REBALANCE_RULES.min_trade_usd:
                continue

            # Limit trade size
            max_trade = float(self.positions[asset].usd_value) * REBALANCE_RULES.max_trade_pct
            trade_size = min(abs(drift_value), max_trade)

            if drift_value > 0:
                # Overweight - sell
                trades.append((asset, "sell", Decimal(str(trade_size))))
            else:
                # Underweight - buy
                trades.append((asset, "buy", Decimal(str(trade_size))))

        return trades


class Portfolio:
    """Main portfolio tracking class."""

    def __init__(
        self,
        exchanges: List[ExchangeClient],
        price_service: PriceService,
        target_allocation: Optional[Dict[str, float]] = None,
    ):
        self.exchanges = exchanges
        self.price_service = price_service
        self.target_allocation = target_allocation or TARGET_ALLOCATION

        self._last_snapshot: Optional[PortfolioSnapshot] = None

    async def sync(self) -> PortfolioSnapshot:
        """
        Sync all balances and create a portfolio snapshot.

        This is the main method to call to get current state.
        """
        # Gather balances from all exchanges concurrently
        balance_tasks = [ex.get_balances() for ex in self.exchanges]
        results = await asyncio.gather(*balance_tasks, return_exceptions=True)

        # Aggregate positions
        positions: Dict[str, Position] = defaultdict(lambda: Position(asset=""))
        all_assets = set()

        for exchange, result in zip(self.exchanges, results):
            if isinstance(result, Exception):
                print(f"Warning: Failed to get balances from {exchange.name}: {result}")
                continue

            for asset, balance in result.items():
                if positions[asset].asset == "":
                    positions[asset] = Position(asset=asset)

                positions[asset].add_balance(exchange.name, balance)
                all_assets.add(asset)

        # Get prices for all assets
        prices = await self.price_service.get_prices(list(all_assets))

        # Calculate USD values
        total_usd = Decimal("0")
        total_staked_usd = Decimal("0")

        for asset, position in positions.items():
            price = prices.get(asset, Decimal("0"))
            position.price = price
            position.usd_value = position.total_amount * price
            total_usd += position.usd_value

            staked_value = position.staked_amount * price
            total_staked_usd += staked_value

        # Calculate allocations and drift
        actual_allocation = {}
        drift = {}

        for asset in set(list(positions.keys()) + list(self.target_allocation.keys())):
            position = positions.get(asset)

            if position and total_usd > 0:
                actual_pct = position.usd_value / total_usd
                position.allocation_pct = actual_pct
                actual_allocation[asset] = actual_pct
            else:
                actual_allocation[asset] = Decimal("0")

            target_pct = Decimal(str(self.target_allocation.get(asset, 0)))
            drift[asset] = actual_allocation[asset] - target_pct

        # Calculate expected yield
        expected_yield = Decimal("0")
        for asset, position in positions.items():
            if position.staked_amount > 0:
                net_yield = Decimal(str(get_net_staking_yield(asset)))
                staked_value = position.staked_amount * position.price
                expected_yield += staked_value * net_yield

        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(),
            positions=dict(positions),
            total_usd_value=total_usd,
            target_allocation=self.target_allocation,
            actual_allocation=actual_allocation,
            drift=drift,
            total_staked_value=total_staked_usd,
            expected_annual_yield=expected_yield,
        )

        self._last_snapshot = snapshot
        return snapshot

    @property
    def last_snapshot(self) -> Optional[PortfolioSnapshot]:
        """Get the most recent snapshot."""
        return self._last_snapshot

    def format_summary(self, snapshot: Optional[PortfolioSnapshot] = None) -> str:
        """Format a human-readable portfolio summary."""
        snapshot = snapshot or self._last_snapshot
        if not snapshot:
            return "No portfolio data available. Run sync() first."

        lines = []
        lines.append("=" * 60)
        lines.append(f"Portfolio Summary - {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append(f"Total Value: ${snapshot.total_usd_value:,.2f}")
        lines.append(f"Staked Value: ${snapshot.total_staked_value:,.2f}")
        lines.append(f"Expected Annual Yield: ${snapshot.expected_annual_yield:,.2f}")
        lines.append("")
        lines.append(f"{'Asset':<8} {'Amount':>14} {'Price':>10} {'Value':>12} {'Actual':>8} {'Target':>8} {'Drift':>8}")
        lines.append("-" * 60)

        # Sort by value descending
        sorted_positions = sorted(
            snapshot.positions.items(),
            key=lambda x: float(x[1].usd_value),
            reverse=True
        )

        drift_status = snapshot.get_drift_status()

        for asset, position in sorted_positions:
            if position.usd_value < 1:
                continue

            target = self.target_allocation.get(asset, 0)
            actual = float(snapshot.actual_allocation.get(asset, 0))
            drift = float(snapshot.drift.get(asset, 0))

            status_icon = "🟢" if drift_status.get(asset) == "OK" else "🔴"

            lines.append(
                f"{asset:<8} {float(position.total_amount):>14.6f} "
                f"${float(position.price):>9,.2f} ${float(position.usd_value):>11,.2f} "
                f"{actual*100:>7.1f}% {target*100:>7.1f}% {drift*100:>+7.1f}% {status_icon}"
            )

        lines.append("-" * 60)

        if snapshot.needs_rebalance():
            lines.append("")
            lines.append("⚠️  Portfolio needs rebalancing!")
            trades = snapshot.get_rebalance_trades()
            if trades:
                lines.append("Suggested trades:")
                for asset, side, amount in trades:
                    lines.append(f"  {side.upper()} ${float(amount):,.2f} of {asset}")
        else:
            lines.append("")
            lines.append("✅ Portfolio is balanced")

        return "\n".join(lines)


async def create_portfolio(
    exchanges: List[ExchangeClient],
    target_allocation: Optional[Dict[str, float]] = None,
) -> Portfolio:
    """Factory function to create and initialize a portfolio."""
    price_service = PriceService()
    return Portfolio(
        exchanges=exchanges,
        price_service=price_service,
        target_allocation=target_allocation,
    )
