"""
Dollar-Cost Averaging (DCA) automation agent.

Executes scheduled DCA purchases according to configured allocation,
with optional timing optimization based on volatility and trends.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import json
from pathlib import Path
import random

from config import DCA_ALLOCATION, settings
from exchanges import ExchangeClient, OrderResult
from data.prices import PriceService


@dataclass
class DCAExecution:
    """Record of a DCA execution."""
    id: str
    timestamp: datetime
    asset: str
    usd_amount: Decimal
    filled_amount: Optional[Decimal] = None
    filled_price: Optional[Decimal] = None
    exchange: str = ""
    status: str = "pending"  # pending, executed, failed
    order_id: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "asset": self.asset,
            "usd_amount": str(self.usd_amount),
            "filled_amount": str(self.filled_amount) if self.filled_amount else None,
            "filled_price": str(self.filled_price) if self.filled_price else None,
            "exchange": self.exchange,
            "status": self.status,
            "order_id": self.order_id,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DCAExecution":
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            asset=data["asset"],
            usd_amount=Decimal(data["usd_amount"]),
            filled_amount=Decimal(data["filled_amount"]) if data.get("filled_amount") else None,
            filled_price=Decimal(data["filled_price"]) if data.get("filled_price") else None,
            exchange=data.get("exchange", ""),
            status=data.get("status", "pending"),
            order_id=data.get("order_id"),
            error=data.get("error"),
        )


@dataclass
class DCAStats:
    """Statistics for DCA performance."""
    total_invested: Decimal
    total_value_now: Decimal
    total_gain_loss: Decimal
    gain_loss_pct: Decimal
    execution_count: int
    by_asset: Dict[str, dict] = field(default_factory=dict)


class DCAAgent:
    """Dollar-cost averaging automation agent."""
    
    def __init__(
        self,
        exchanges: Dict[str, ExchangeClient],
        price_service: PriceService,
        allocation: Optional[Dict[str, float]] = None,
        daily_amount: Optional[float] = None,
        storage_path: str = "./data/dca_history.json",
    ):
        self.exchanges = exchanges
        self.price_service = price_service
        self.allocation = allocation or DCA_ALLOCATION
        self.daily_amount = Decimal(str(daily_amount or settings.portfolio.dca_daily_amount))
        self.storage_path = Path(storage_path)
        
        self._history: List[DCAExecution] = []
        self._load_history()
    
    def _load_history(self):
        """Load execution history from storage."""
        if self.storage_path.exists():
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self._history = [DCAExecution.from_dict(e) for e in data]
    
    def _save_history(self):
        """Save execution history to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump([e.to_dict() for e in self._history], f, indent=2)
    
    def get_daily_allocation(self) -> Dict[str, Decimal]:
        """Calculate USD allocation for each asset based on daily amount."""
        allocations = {}
        
        for asset, pct in self.allocation.items():
            if asset == "TACTICAL":
                continue  # Handle tactical allocation separately
            
            amount = self.daily_amount * Decimal(str(pct))
            if amount >= settings.portfolio.min_trade_size:
                allocations[asset] = amount
        
        return allocations
    
    def should_execute_today(self) -> bool:
        """Check if DCA should execute today (hasn't run yet)."""
        today = datetime.now().date()
        
        for execution in reversed(self._history):
            if execution.timestamp.date() == today and execution.status == "executed":
                return False
        
        return True
    
    def _select_exchange(self, asset: str) -> Optional[str]:
        """Select the best exchange for buying an asset."""
        # Priority: primary exchange with lowest fees
        # In practice, you'd check which exchanges support the asset
        for name in self.exchanges.keys():
            return name
        return None
    
    async def execute_dca(
        self,
        dry_run: bool = True,
        assets: Optional[List[str]] = None,
        custom_amounts: Optional[Dict[str, Decimal]] = None,
    ) -> List[DCAExecution]:
        """
        Execute DCA purchases for today.
        
        Args:
            dry_run: If True, simulate but don't execute
            assets: Optional list of specific assets to buy (default: all in allocation)
            custom_amounts: Optional dict of asset -> USD amount (overrides allocation)
                           Used by dip buyer to adjust amounts based on market conditions.
            
        Returns:
            List of execution records
        """
        executions = []
        
        # Use custom amounts if provided, otherwise use standard allocation
        if custom_amounts:
            allocations = custom_amounts
        else:
            allocations = self.get_daily_allocation()
        
        if assets:
            # Filter to specified assets
            allocations = {k: v for k, v in allocations.items() if k in assets}
        
        for asset, usd_amount in allocations.items():
            execution = DCAExecution(
                id=f"dca_{asset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                asset=asset,
                usd_amount=usd_amount,
            )
            
            exchange_name = self._select_exchange(asset)
            if not exchange_name:
                execution.status = "failed"
                execution.error = f"No exchange available for {asset}"
                executions.append(execution)
                continue
            
            execution.exchange = exchange_name
            
            if dry_run:
                # Get current price for simulation
                try:
                    price = await self.price_service.get_price(asset)
                    execution.filled_price = price
                    execution.filled_amount = usd_amount / price
                    execution.status = "dry_run"
                except Exception as e:
                    execution.status = "failed"
                    execution.error = str(e)
            else:
                # Execute actual purchase
                client = self.exchanges[exchange_name]
                
                try:
                    result = await client.place_market_order(
                        asset=asset,
                        side="buy",
                        quote_amount=usd_amount,
                    )
                    
                    if result.success:
                        execution.status = "executed"
                        execution.order_id = result.order_id
                        execution.filled_amount = result.filled_amount
                        execution.filled_price = result.filled_price
                    else:
                        execution.status = "failed"
                        execution.error = result.error
                        
                except Exception as e:
                    execution.status = "failed"
                    execution.error = str(e)
            
            executions.append(execution)
            
            # Small delay between orders
            await asyncio.sleep(0.3)
        
        # Save to history
        self._history.extend(executions)
        self._save_history()
        
        return executions
    
    async def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> DCAStats:
        """
        Calculate DCA performance statistics.
        
        Args:
            start_date: Start of period (default: all time)
            end_date: End of period (default: now)
            
        Returns:
            DCAStats with performance metrics
        """
        # Filter executions
        executions = [
            e for e in self._history
            if e.status == "executed"
        ]
        
        if start_date:
            executions = [e for e in executions if e.timestamp >= start_date]
        if end_date:
            executions = [e for e in executions if e.timestamp <= end_date]
        
        if not executions:
            return DCAStats(
                total_invested=Decimal("0"),
                total_value_now=Decimal("0"),
                total_gain_loss=Decimal("0"),
                gain_loss_pct=Decimal("0"),
                execution_count=0,
            )
        
        # Calculate by asset
        by_asset: Dict[str, dict] = {}
        assets = list(set(e.asset for e in executions))
        
        # Get current prices
        current_prices = await self.price_service.get_prices(assets)
        
        total_invested = Decimal("0")
        total_value_now = Decimal("0")
        
        for asset in assets:
            asset_executions = [e for e in executions if e.asset == asset]
            invested = sum(e.usd_amount for e in asset_executions)
            amount_held = sum(e.filled_amount or Decimal("0") for e in asset_executions)
            current_price = current_prices.get(asset, Decimal("0"))
            current_value = amount_held * current_price
            
            gain_loss = current_value - invested
            gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else Decimal("0")
            
            by_asset[asset] = {
                "invested": invested,
                "amount_held": amount_held,
                "current_value": current_value,
                "gain_loss": gain_loss,
                "gain_loss_pct": gain_loss_pct,
                "avg_cost": invested / amount_held if amount_held > 0 else Decimal("0"),
                "current_price": current_price,
                "execution_count": len(asset_executions),
            }
            
            total_invested += invested
            total_value_now += current_value
        
        total_gain_loss = total_value_now - total_invested
        gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else Decimal("0")
        
        return DCAStats(
            total_invested=total_invested,
            total_value_now=total_value_now,
            total_gain_loss=total_gain_loss,
            gain_loss_pct=gain_loss_pct,
            execution_count=len(executions),
            by_asset=by_asset,
        )
    
    def format_stats(self, stats: DCAStats) -> str:
        """Format stats for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("DCA Performance Summary")
        lines.append("=" * 60)
        lines.append(f"Total Invested:  ${stats.total_invested:,.2f}")
        lines.append(f"Current Value:   ${stats.total_value_now:,.2f}")
        
        sign = "+" if stats.total_gain_loss >= 0 else ""
        lines.append(f"Gain/Loss:       {sign}${stats.total_gain_loss:,.2f} ({sign}{stats.gain_loss_pct:.1f}%)")
        lines.append(f"Executions:      {stats.execution_count}")
        lines.append("")
        
        lines.append(f"{'Asset':<8} {'Invested':>12} {'Value':>12} {'Gain/Loss':>14} {'Avg Cost':>10} {'Price':>10}")
        lines.append("-" * 60)
        
        for asset, data in sorted(stats.by_asset.items(), key=lambda x: -float(x[1]["invested"])):
            sign = "+" if data["gain_loss"] >= 0 else ""
            lines.append(
                f"{asset:<8} ${float(data['invested']):>11,.2f} ${float(data['current_value']):>11,.2f} "
                f"{sign}${float(data['gain_loss']):>10,.2f} ${float(data['avg_cost']):>9,.2f} ${float(data['current_price']):>9,.2f}"
            )
        
        return "\n".join(lines)
    
    def format_executions(self, executions: List[DCAExecution]) -> str:
        """Format execution list for display."""
        if not executions:
            return "No DCA executions to display."
        
        lines = []
        lines.append("DCA Executions")
        lines.append("=" * 70)
        
        total = sum(e.usd_amount for e in executions)
        lines.append(f"Total: ${total:,.2f}")
        lines.append("")
        
        lines.append(f"{'Asset':<8} {'Amount':>12} {'Price':>10} {'Qty':>14} {'Exchange':<12} {'Status':<10}")
        lines.append("-" * 70)
        
        for e in executions:
            price = f"${float(e.filled_price):,.2f}" if e.filled_price else "N/A"
            qty = f"{float(e.filled_amount):.6f}" if e.filled_amount else "N/A"
            lines.append(
                f"{e.asset:<8} ${float(e.usd_amount):>11,.2f} {price:>10} {qty:>14} "
                f"{e.exchange:<12} {e.status:<10}"
            )
        
        return "\n".join(lines)
