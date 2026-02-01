"""
Rebalancing agent.

Monitors portfolio drift and executes rebalancing trades
according to configured rules.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from pathlib import Path

from config import REBALANCE_RULES
from exchanges import ExchangeClient
from tracking.portfolio import Portfolio, PortfolioSnapshot


@dataclass
class RebalanceTrade:
    """A proposed or executed rebalancing trade."""
    asset: str
    side: str  # "buy" or "sell"
    usd_amount: Decimal
    exchange: str
    status: str = "proposed"  # proposed, pending, executed, failed
    order_id: Optional[str] = None
    filled_amount: Optional[Decimal] = None
    filled_price: Optional[Decimal] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "asset": self.asset,
            "side": self.side,
            "usd_amount": str(self.usd_amount),
            "exchange": self.exchange,
            "status": self.status,
            "order_id": self.order_id,
            "filled_amount": str(self.filled_amount) if self.filled_amount else None,
            "filled_price": str(self.filled_price) if self.filled_price else None,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class RebalanceSession:
    """A complete rebalancing session."""
    id: str
    timestamp: datetime
    snapshot_before: PortfolioSnapshot
    trades: List[RebalanceTrade]
    status: str = "pending"  # pending, executing, completed, failed

    @property
    def total_sell_volume(self) -> Decimal:
        return sum(t.usd_amount for t in self.trades if t.side == "sell")

    @property
    def total_buy_volume(self) -> Decimal:
        return sum(t.usd_amount for t in self.trades if t.side == "buy")


class Rebalancer:
    """Portfolio rebalancing agent."""

    def __init__(
        self,
        portfolio: Portfolio,
        exchanges: Dict[str, ExchangeClient],
        rules: Optional[object] = None,
    ):
        self.portfolio = portfolio
        self.exchanges = exchanges  # name -> client mapping
        self.rules = rules or REBALANCE_RULES

        self._history: List[RebalanceSession] = []
        self._history_path = Path("./data/rebalance_history.json")

    def analyze_drift(self, snapshot: PortfolioSnapshot) -> Dict[str, dict]:
        """
        Analyze portfolio drift and determine what needs rebalancing.

        Returns:
            Dict of asset -> analysis details
        """
        analysis = {}

        for asset, drift in snapshot.drift.items():
            target_pct = snapshot.target_allocation.get(asset, 0)
            actual_pct = float(snapshot.actual_allocation.get(asset, 0))
            drift_pct = float(drift)

            position = snapshot.positions.get(asset)
            current_value = float(position.usd_value) if position else 0
            target_value = float(snapshot.total_usd_value) * target_pct
            value_diff = current_value - target_value

            needs_action = abs(drift_pct) > self.rules.drift_threshold

            analysis[asset] = {
                "target_pct": target_pct,
                "actual_pct": actual_pct,
                "drift_pct": drift_pct,
                "current_value": current_value,
                "target_value": target_value,
                "value_diff": value_diff,
                "needs_action": needs_action,
                "action": "sell" if value_diff > 0 else "buy" if needs_action else None,
            }

        return analysis

    def plan_trades(
        self,
        snapshot: PortfolioSnapshot,
        prefer_exchange: Optional[str] = None,
    ) -> List[RebalanceTrade]:
        """
        Create a rebalancing trade plan.

        Args:
            snapshot: Current portfolio snapshot
            prefer_exchange: Preferred exchange for trades

        Returns:
            List of proposed trades
        """
        trades = []
        analysis = self.analyze_drift(snapshot)

        # First pass: calculate all trades
        sell_trades = []
        buy_trades = []

        for asset, details in analysis.items():
            if not details["needs_action"] or asset == "CASH":
                continue

            # Calculate trade size
            trade_value = abs(details["value_diff"])

            # Apply limits
            if trade_value < self.rules.min_trade_usd:
                continue

            # Limit to percentage of position
            if details["action"] == "sell":
                max_trade = details["current_value"] * self.rules.max_trade_pct
                trade_value = min(trade_value, max_trade)

            # Determine which exchange to use
            exchange = prefer_exchange or self._select_exchange_for_trade(
                asset, details["action"]
            )

            trade = RebalanceTrade(
                asset=asset,
                side=details["action"],
                usd_amount=Decimal(str(trade_value)),
                exchange=exchange,
            )

            if details["action"] == "sell":
                sell_trades.append(trade)
            else:
                buy_trades.append(trade)

        # Balance buys with available sell proceeds
        total_sells = sum(t.usd_amount for t in sell_trades)
        total_buys = sum(t.usd_amount for t in buy_trades)

        if total_buys > total_sells:
            # Scale down buys to match sells
            scale = float(total_sells / total_buys) if total_buys > 0 else 0
            for trade in buy_trades:
                trade.usd_amount = Decimal(str(float(trade.usd_amount) * scale))

        # Filter out trades that became too small
        trades = [
            t for t in (sell_trades + buy_trades)
            if t.usd_amount >= self.rules.min_trade_usd
        ]

        # Sort: sells first, then buys
        trades.sort(key=lambda t: (0 if t.side == "sell" else 1, -float(t.usd_amount)))

        return trades

    def _select_exchange_for_trade(self, asset: str, side: str) -> str:
        """Select the best exchange for a trade based on balances."""
        # Default logic: use the exchange with the most balance for sells,
        # or any available exchange for buys

        if side == "sell":
            # Check where we have the asset
            for name, client in self.exchanges.items():
                # In a real implementation, check balances
                return name

        # For buys, prefer the primary exchange
        return list(self.exchanges.keys())[0]

    async def execute_trades(
        self,
        trades: List[RebalanceTrade],
        dry_run: bool = True,
    ) -> List[RebalanceTrade]:
        """
        Execute a list of trades.

        Args:
            trades: List of trades to execute
            dry_run: If True, don't actually execute

        Returns:
            Updated trades with execution status
        """
        for trade in trades:
            if dry_run:
                trade.status = "dry_run"
                trade.timestamp = datetime.now()
                continue

            # Get the exchange client
            client = self.exchanges.get(trade.exchange)
            if not client:
                trade.status = "failed"
                trade.error = f"Exchange not found: {trade.exchange}"
                continue

            try:
                trade.status = "pending"

                # Execute the trade
                if trade.side == "sell":
                    # For sells, we need to calculate amount from USD value
                    price = await client.get_ticker_price(trade.asset)
                    amount = trade.usd_amount / price
                    result = await client.place_market_order(
                        asset=trade.asset,
                        side="sell",
                        amount=amount,
                    )
                else:
                    # For buys, use quote amount
                    result = await client.place_market_order(
                        asset=trade.asset,
                        side="buy",
                        quote_amount=trade.usd_amount,
                    )

                if result.success:
                    trade.status = "executed"
                    trade.order_id = result.order_id
                    trade.filled_amount = result.filled_amount
                    trade.filled_price = result.filled_price
                else:
                    trade.status = "failed"
                    trade.error = result.error

            except Exception as e:
                trade.status = "failed"
                trade.error = str(e)

            trade.timestamp = datetime.now()

            # Small delay between trades
            await asyncio.sleep(0.5)

        return trades

    async def rebalance(
        self,
        dry_run: bool = True,
        prefer_exchange: Optional[str] = None,
    ) -> RebalanceSession:
        """
        Perform a full rebalancing operation.

        Args:
            dry_run: If True, plan but don't execute
            prefer_exchange: Preferred exchange for trades

        Returns:
            RebalanceSession with results
        """
        # Get current portfolio state
        snapshot = await self.portfolio.sync()

        # Check if rebalancing is needed
        if not snapshot.needs_rebalance(self.rules.drift_threshold):
            return RebalanceSession(
                id=f"rebal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                snapshot_before=snapshot,
                trades=[],
                status="skipped",
            )

        # Plan trades
        trades = self.plan_trades(snapshot, prefer_exchange)

        # Create session
        session = RebalanceSession(
            id=f"rebal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            snapshot_before=snapshot,
            trades=trades,
            status="pending" if trades else "skipped",
        )

        if trades:
            # Execute trades
            await self.execute_trades(trades, dry_run)

            # Update session status
            if all(t.status == "executed" for t in trades):
                session.status = "completed"
            elif all(t.status == "dry_run" for t in trades):
                session.status = "dry_run"
            elif any(t.status == "failed" for t in trades):
                session.status = "partial" if any(t.status == "executed" for t in trades) else "failed"

        self._history.append(session)
        return session

    def format_plan(self, trades: List[RebalanceTrade]) -> str:
        """Format a trade plan for display."""
        if not trades:
            return "No trades needed - portfolio is balanced."

        lines = []
        lines.append("Rebalancing Plan")
        lines.append("=" * 50)

        total_sell = sum(t.usd_amount for t in trades if t.side == "sell")
        total_buy = sum(t.usd_amount for t in trades if t.side == "buy")

        lines.append(f"Total Sells: ${total_sell:,.2f}")
        lines.append(f"Total Buys:  ${total_buy:,.2f}")
        lines.append("")

        lines.append(f"{'Action':<8} {'Asset':<8} {'Amount':>12} {'Exchange':<15} {'Status':<10}")
        lines.append("-" * 50)

        for trade in trades:
            lines.append(
                f"{trade.side.upper():<8} {trade.asset:<8} "
                f"${float(trade.usd_amount):>11,.2f} {trade.exchange:<15} {trade.status:<10}"
            )

        return "\n".join(lines)
