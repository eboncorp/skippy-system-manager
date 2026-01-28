"""
Advanced Order Types for Crypto Portfolio Manager.

Implements:
- TWAP (Time-Weighted Average Price)
- VWAP (Volume-Weighted Average Price)
- Iceberg Orders
- Conditional Orders (stop-loss, take-profit)
- Bracket Orders
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import asyncio
import uuid


class OrderStatus(Enum):
    """Status of an advanced order."""
    PENDING = "pending"
    ACTIVE = "active"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


class OrderSide(Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class OrderFill:
    """Record of a partial or complete order fill."""
    fill_id: str
    timestamp: datetime
    amount: Decimal
    price: Decimal
    fee: Decimal

    @property
    def total_value(self) -> Decimal:
        """Total value of fill (amount * price)."""
        return self.amount * self.price


@dataclass
class AdvancedOrderResult:
    """Result of an advanced order execution."""
    order_id: str
    status: OrderStatus
    total_amount: Decimal
    filled_amount: Decimal
    average_price: Decimal
    total_fees: Decimal
    fills: List[OrderFill]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def fill_percentage(self) -> float:
        """Percentage of order filled."""
        if self.total_amount == 0:
            return 0
        return float(self.filled_amount / self.total_amount * 100)

    @property
    def total_value(self) -> Decimal:
        """Total value traded."""
        return self.filled_amount * self.average_price


class TWAPOrder:
    """
    Time-Weighted Average Price Order.

    Executes order in equal slices over a specified time period.
    Aims to achieve average execution price close to TWAP.
    """

    def __init__(
        self,
        exchange_client,  # Exchange client instance
        asset: str,
        side: OrderSide,
        total_amount: Decimal,
        duration_minutes: int = 60,
        num_slices: int = 12,
        randomize: bool = True,
        max_price_deviation: Decimal = Decimal("0.02"),  # 2% max deviation
    ):
        """
        Initialize TWAP order.

        Args:
            exchange_client: Exchange client for order execution
            asset: Asset to trade
            side: Buy or sell
            total_amount: Total amount to trade
            duration_minutes: Total execution duration
            num_slices: Number of order slices
            randomize: Randomize timing slightly to avoid detection
            max_price_deviation: Cancel if price moves beyond this %
        """
        self.exchange = exchange_client
        self.asset = asset
        self.side = side
        self.total_amount = total_amount
        self.duration_minutes = duration_minutes
        self.num_slices = num_slices
        self.randomize = randomize
        self.max_price_deviation = max_price_deviation

        self.order_id = str(uuid.uuid4())[:8]
        self.status = OrderStatus.PENDING
        self.fills: List[OrderFill] = []
        self.start_price: Optional[Decimal] = None
        self.started_at: Optional[datetime] = None
        self._cancelled = False

    @property
    def slice_amount(self) -> Decimal:
        """Amount per slice."""
        return self.total_amount / self.num_slices

    @property
    def slice_interval_seconds(self) -> float:
        """Seconds between slices."""
        return (self.duration_minutes * 60) / self.num_slices

    @property
    def filled_amount(self) -> Decimal:
        """Total amount filled so far."""
        return sum(f.amount for f in self.fills)

    @property
    def average_price(self) -> Decimal:
        """Average fill price."""
        if not self.fills:
            return Decimal("0")
        total_value = sum(f.amount * f.price for f in self.fills)
        total_amount = sum(f.amount for f in self.fills)
        return total_value / total_amount if total_amount > 0 else Decimal("0")

    async def execute(self) -> AdvancedOrderResult:
        """
        Execute the TWAP order.

        Returns:
            AdvancedOrderResult with execution details
        """
        import random

        self.status = OrderStatus.ACTIVE
        self.started_at = datetime.now()

        # Get starting price for deviation check
        self.start_price = await self.exchange.get_ticker_price(self.asset)

        for i in range(self.num_slices):
            if self._cancelled:
                self.status = OrderStatus.CANCELLED
                break

            # Check price deviation
            current_price = await self.exchange.get_ticker_price(self.asset)
            deviation = abs(current_price - self.start_price) / self.start_price

            if deviation > self.max_price_deviation:
                self.status = OrderStatus.CANCELLED
                break

            # Execute slice
            try:
                if self.side == OrderSide.BUY:
                    result = await self.exchange.place_market_order(
                        self.asset, "buy", amount=self.slice_amount
                    )
                else:
                    result = await self.exchange.place_market_order(
                        self.asset, "sell", amount=self.slice_amount
                    )

                if result.success:
                    self.fills.append(OrderFill(
                        fill_id=result.order_id or str(uuid.uuid4())[:8],
                        timestamp=datetime.now(),
                        amount=result.filled_amount,
                        price=result.filled_price,
                        fee=result.fee,
                    ))
                    self.status = OrderStatus.PARTIALLY_FILLED

            except Exception as e:
                print(f"TWAP slice {i+1} failed: {e}")

            # Wait for next slice (with optional randomization)
            if i < self.num_slices - 1:
                wait_time = self.slice_interval_seconds
                if self.randomize:
                    wait_time *= random.uniform(0.8, 1.2)
                await asyncio.sleep(wait_time)

        # Final status
        if self.filled_amount >= self.total_amount * Decimal("0.99"):
            self.status = OrderStatus.FILLED

        return AdvancedOrderResult(
            order_id=self.order_id,
            status=self.status,
            total_amount=self.total_amount,
            filled_amount=self.filled_amount,
            average_price=self.average_price,
            total_fees=sum(f.fee for f in self.fills),
            fills=self.fills,
            started_at=self.started_at,
            completed_at=datetime.now(),
        )

    def cancel(self):
        """Cancel the TWAP order."""
        self._cancelled = True


class VWAPOrder:
    """
    Volume-Weighted Average Price Order.

    Executes order according to historical volume profile.
    Larger slices during high-volume periods, smaller during low-volume.
    """

    def __init__(
        self,
        exchange_client,
        asset: str,
        side: OrderSide,
        total_amount: Decimal,
        duration_minutes: int = 60,
        volume_profile: Optional[List[float]] = None,
        participation_rate: float = 0.1,  # Max 10% of volume
    ):
        """
        Initialize VWAP order.

        Args:
            exchange_client: Exchange client for order execution
            asset: Asset to trade
            side: Buy or sell
            total_amount: Total amount to trade
            duration_minutes: Total execution duration
            volume_profile: Normalized volume profile (sums to 1)
            participation_rate: Max participation rate of market volume
        """
        self.exchange = exchange_client
        self.asset = asset
        self.side = side
        self.total_amount = total_amount
        self.duration_minutes = duration_minutes
        self.participation_rate = participation_rate

        # Default volume profile if not provided (typical crypto 24h pattern)
        self.volume_profile = volume_profile or self._default_volume_profile()

        self.order_id = str(uuid.uuid4())[:8]
        self.status = OrderStatus.PENDING
        self.fills: List[OrderFill] = []
        self.started_at: Optional[datetime] = None
        self._cancelled = False

    def _default_volume_profile(self) -> List[float]:
        """
        Default hourly volume profile for crypto.

        Higher volume during US market hours, lower during Asian session.
        """
        # 24 hourly buckets (normalized weights)
        profile = [
            0.02, 0.02, 0.02, 0.03, 0.03, 0.04,  # 0-5 UTC (Asia evening)
            0.05, 0.05, 0.05, 0.05, 0.05, 0.05,  # 6-11 UTC (Europe morning)
            0.06, 0.06, 0.06, 0.06, 0.05, 0.05,  # 12-17 UTC (US morning)
            0.04, 0.04, 0.04, 0.03, 0.03, 0.02,  # 18-23 UTC (US evening)
        ]
        total = sum(profile)
        return [p / total for p in profile]

    @property
    def filled_amount(self) -> Decimal:
        """Total amount filled so far."""
        return sum(f.amount for f in self.fills)

    @property
    def average_price(self) -> Decimal:
        """Average fill price."""
        if not self.fills:
            return Decimal("0")
        total_value = sum(f.amount * f.price for f in self.fills)
        total_amount = sum(f.amount for f in self.fills)
        return total_value / total_amount if total_amount > 0 else Decimal("0")

    async def execute(self) -> AdvancedOrderResult:
        """Execute the VWAP order."""
        self.status = OrderStatus.ACTIVE
        self.started_at = datetime.now()

        # Calculate slice amounts based on volume profile
        num_slices = min(len(self.volume_profile), self.duration_minutes)
        slice_weights = self.volume_profile[:num_slices]

        # Normalize weights
        total_weight = sum(slice_weights)
        slice_amounts = [
            self.total_amount * Decimal(str(w / total_weight))
            for w in slice_weights
        ]

        interval_seconds = (self.duration_minutes * 60) / num_slices

        for i, slice_amount in enumerate(slice_amounts):
            if self._cancelled:
                self.status = OrderStatus.CANCELLED
                break

            if slice_amount < Decimal("0.0001"):
                continue

            try:
                if self.side == OrderSide.BUY:
                    result = await self.exchange.place_market_order(
                        self.asset, "buy", amount=slice_amount
                    )
                else:
                    result = await self.exchange.place_market_order(
                        self.asset, "sell", amount=slice_amount
                    )

                if result.success:
                    self.fills.append(OrderFill(
                        fill_id=result.order_id or str(uuid.uuid4())[:8],
                        timestamp=datetime.now(),
                        amount=result.filled_amount,
                        price=result.filled_price,
                        fee=result.fee,
                    ))
                    self.status = OrderStatus.PARTIALLY_FILLED

            except Exception as e:
                print(f"VWAP slice {i+1} failed: {e}")

            if i < len(slice_amounts) - 1:
                await asyncio.sleep(interval_seconds)

        if self.filled_amount >= self.total_amount * Decimal("0.99"):
            self.status = OrderStatus.FILLED

        return AdvancedOrderResult(
            order_id=self.order_id,
            status=self.status,
            total_amount=self.total_amount,
            filled_amount=self.filled_amount,
            average_price=self.average_price,
            total_fees=sum(f.fee for f in self.fills),
            fills=self.fills,
            started_at=self.started_at,
            completed_at=datetime.now(),
        )

    def cancel(self):
        """Cancel the VWAP order."""
        self._cancelled = True


class IcebergOrder:
    """
    Iceberg Order.

    Shows only a small visible portion of the total order.
    Automatically replenishes when visible portion is filled.
    """

    def __init__(
        self,
        exchange_client,
        asset: str,
        side: OrderSide,
        total_amount: Decimal,
        visible_amount: Decimal,
        limit_price: Decimal,
        price_variance: Decimal = Decimal("0.001"),  # 0.1% price variance
    ):
        """
        Initialize Iceberg order.

        Args:
            exchange_client: Exchange client for order execution
            asset: Asset to trade
            side: Buy or sell
            total_amount: Total order amount (hidden)
            visible_amount: Amount shown on order book
            limit_price: Limit price for orders
            price_variance: Random variance to add to price
        """
        self.exchange = exchange_client
        self.asset = asset
        self.side = side
        self.total_amount = total_amount
        self.visible_amount = visible_amount
        self.limit_price = limit_price
        self.price_variance = price_variance

        self.order_id = str(uuid.uuid4())[:8]
        self.status = OrderStatus.PENDING
        self.fills: List[OrderFill] = []
        self.active_order_id: Optional[str] = None
        self._cancelled = False

    @property
    def remaining_amount(self) -> Decimal:
        """Amount remaining to be filled."""
        return self.total_amount - sum(f.amount for f in self.fills)

    @property
    def filled_amount(self) -> Decimal:
        """Total amount filled so far."""
        return sum(f.amount for f in self.fills)

    @property
    def average_price(self) -> Decimal:
        """Average fill price."""
        if not self.fills:
            return Decimal("0")
        total_value = sum(f.amount * f.price for f in self.fills)
        total_amount = sum(f.amount for f in self.fills)
        return total_value / total_amount if total_amount > 0 else Decimal("0")

    async def execute(self) -> AdvancedOrderResult:
        """Execute the Iceberg order."""
        import random

        self.status = OrderStatus.ACTIVE
        started_at = datetime.now()

        while self.remaining_amount > Decimal("0") and not self._cancelled:
            # Calculate this slice
            slice_amount = min(self.visible_amount, self.remaining_amount)

            # Add small random variance to price
            variance = Decimal(str(random.uniform(
                float(-self.price_variance),
                float(self.price_variance)
            )))
            order_price = self.limit_price * (1 + variance)

            try:
                # Place limit order
                if hasattr(self.exchange, 'place_limit_order'):
                    result = await self.exchange.place_limit_order(
                        self.asset,
                        self.side.value,
                        slice_amount,
                        order_price,
                    )
                else:
                    # Fallback to market order
                    result = await self.exchange.place_market_order(
                        self.asset,
                        self.side.value,
                        amount=slice_amount,
                    )

                if result.success and result.filled_amount > 0:
                    self.fills.append(OrderFill(
                        fill_id=result.order_id or str(uuid.uuid4())[:8],
                        timestamp=datetime.now(),
                        amount=result.filled_amount,
                        price=result.filled_price or order_price,
                        fee=result.fee,
                    ))
                    self.status = OrderStatus.PARTIALLY_FILLED

                self.active_order_id = result.order_id

            except Exception as e:
                print(f"Iceberg slice failed: {e}")

            # Wait before next slice
            await asyncio.sleep(1)

        if self._cancelled:
            self.status = OrderStatus.CANCELLED
        elif self.filled_amount >= self.total_amount * Decimal("0.99"):
            self.status = OrderStatus.FILLED

        return AdvancedOrderResult(
            order_id=self.order_id,
            status=self.status,
            total_amount=self.total_amount,
            filled_amount=self.filled_amount,
            average_price=self.average_price,
            total_fees=sum(f.fee for f in self.fills),
            fills=self.fills,
            started_at=started_at,
            completed_at=datetime.now(),
        )

    def cancel(self):
        """Cancel the Iceberg order."""
        self._cancelled = True


@dataclass
class ConditionalTrigger:
    """Trigger condition for conditional orders."""
    trigger_type: str  # "price_above", "price_below", "time"
    trigger_value: Any  # Price or datetime
    triggered: bool = False
    triggered_at: Optional[datetime] = None


class BracketOrder:
    """
    Bracket Order (OCO - One Cancels Other).

    Places entry order with attached stop-loss and take-profit.
    When one side triggers, the other is cancelled.
    """

    def __init__(
        self,
        exchange_client,
        asset: str,
        entry_side: OrderSide,
        entry_amount: Decimal,
        entry_price: Optional[Decimal],  # None for market order
        stop_loss_price: Decimal,
        take_profit_price: Decimal,
    ):
        """
        Initialize Bracket order.

        Args:
            exchange_client: Exchange client for order execution
            asset: Asset to trade
            entry_side: Buy or sell for entry
            entry_amount: Amount to trade
            entry_price: Entry limit price (None for market)
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price
        """
        self.exchange = exchange_client
        self.asset = asset
        self.entry_side = entry_side
        self.entry_amount = entry_amount
        self.entry_price = entry_price
        self.stop_loss_price = stop_loss_price
        self.take_profit_price = take_profit_price

        self.order_id = str(uuid.uuid4())[:8]
        self.status = OrderStatus.PENDING
        self.entry_fill: Optional[OrderFill] = None
        self.exit_fill: Optional[OrderFill] = None
        self.exit_reason: Optional[str] = None  # "stop_loss" or "take_profit"
        self._cancelled = False

    @property
    def exit_side(self) -> OrderSide:
        """Exit side is opposite of entry."""
        return OrderSide.SELL if self.entry_side == OrderSide.BUY else OrderSide.BUY

    async def execute(self) -> AdvancedOrderResult:
        """Execute the Bracket order."""
        started_at = datetime.now()
        self.status = OrderStatus.ACTIVE

        # Place entry order
        try:
            if self.entry_price:
                if hasattr(self.exchange, 'place_limit_order'):
                    entry_result = await self.exchange.place_limit_order(
                        self.asset,
                        self.entry_side.value,
                        self.entry_amount,
                        self.entry_price,
                    )
                else:
                    entry_result = await self.exchange.place_market_order(
                        self.asset, self.entry_side.value, amount=self.entry_amount
                    )
            else:
                entry_result = await self.exchange.place_market_order(
                    self.asset, self.entry_side.value, amount=self.entry_amount
                )

            if not entry_result.success:
                self.status = OrderStatus.FAILED
                return self._build_result(started_at, error="Entry order failed")

            self.entry_fill = OrderFill(
                fill_id=entry_result.order_id or str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                amount=entry_result.filled_amount,
                price=entry_result.filled_price,
                fee=entry_result.fee,
            )

        except Exception as e:
            self.status = OrderStatus.FAILED
            return self._build_result(started_at, error=str(e))

        # Monitor for stop-loss or take-profit
        while not self._cancelled:
            try:
                current_price = await self.exchange.get_ticker_price(self.asset)

                # Check stop loss
                if self.entry_side == OrderSide.BUY:
                    if current_price <= self.stop_loss_price:
                        self.exit_reason = "stop_loss"
                        break
                    if current_price >= self.take_profit_price:
                        self.exit_reason = "take_profit"
                        break
                else:  # Short position
                    if current_price >= self.stop_loss_price:
                        self.exit_reason = "stop_loss"
                        break
                    if current_price <= self.take_profit_price:
                        self.exit_reason = "take_profit"
                        break

            except Exception:
                pass

            await asyncio.sleep(1)

        if self._cancelled:
            self.status = OrderStatus.CANCELLED
            return self._build_result(started_at)

        # Execute exit order
        try:
            exit_result = await self.exchange.place_market_order(
                self.asset,
                self.exit_side.value,
                amount=self.entry_fill.amount,
            )

            if exit_result.success:
                self.exit_fill = OrderFill(
                    fill_id=exit_result.order_id or str(uuid.uuid4())[:8],
                    timestamp=datetime.now(),
                    amount=exit_result.filled_amount,
                    price=exit_result.filled_price,
                    fee=exit_result.fee,
                )
                self.status = OrderStatus.FILLED

        except Exception as e:
            self.status = OrderStatus.FAILED
            return self._build_result(started_at, error=f"Exit failed: {e}")

        return self._build_result(started_at)

    def _build_result(
        self,
        started_at: datetime,
        error: Optional[str] = None,
    ) -> AdvancedOrderResult:
        """Build result object."""
        fills = []
        if self.entry_fill:
            fills.append(self.entry_fill)
        if self.exit_fill:
            fills.append(self.exit_fill)

        filled_amount = self.entry_fill.amount if self.entry_fill else Decimal("0")
        avg_price = self.entry_fill.price if self.entry_fill else Decimal("0")

        return AdvancedOrderResult(
            order_id=self.order_id,
            status=self.status,
            total_amount=self.entry_amount,
            filled_amount=filled_amount,
            average_price=avg_price,
            total_fees=sum(f.fee for f in fills),
            fills=fills,
            started_at=started_at,
            completed_at=datetime.now(),
            error=error,
        )

    def cancel(self):
        """Cancel the Bracket order."""
        self._cancelled = True


class AdvancedOrderManager:
    """
    Manages advanced order execution.

    Provides a unified interface for creating and monitoring
    TWAP, VWAP, Iceberg, and Bracket orders.
    """

    def __init__(self, exchange_client):
        self.exchange = exchange_client
        self.active_orders: Dict[str, Any] = {}
        self.completed_orders: List[AdvancedOrderResult] = []

    async def create_twap_order(
        self,
        asset: str,
        side: str,
        amount: Decimal,
        duration_minutes: int = 60,
        num_slices: int = 12,
    ) -> str:
        """Create and start a TWAP order."""
        order = TWAPOrder(
            self.exchange,
            asset,
            OrderSide(side),
            amount,
            duration_minutes,
            num_slices,
        )
        self.active_orders[order.order_id] = order

        # Execute in background
        asyncio.create_task(self._execute_order(order))

        return order.order_id

    async def create_vwap_order(
        self,
        asset: str,
        side: str,
        amount: Decimal,
        duration_minutes: int = 60,
    ) -> str:
        """Create and start a VWAP order."""
        order = VWAPOrder(
            self.exchange,
            asset,
            OrderSide(side),
            amount,
            duration_minutes,
        )
        self.active_orders[order.order_id] = order

        asyncio.create_task(self._execute_order(order))

        return order.order_id

    async def create_iceberg_order(
        self,
        asset: str,
        side: str,
        total_amount: Decimal,
        visible_amount: Decimal,
        limit_price: Decimal,
    ) -> str:
        """Create and start an Iceberg order."""
        order = IcebergOrder(
            self.exchange,
            asset,
            OrderSide(side),
            total_amount,
            visible_amount,
            limit_price,
        )
        self.active_orders[order.order_id] = order

        asyncio.create_task(self._execute_order(order))

        return order.order_id

    async def create_bracket_order(
        self,
        asset: str,
        side: str,
        amount: Decimal,
        entry_price: Optional[Decimal],
        stop_loss_price: Decimal,
        take_profit_price: Decimal,
    ) -> str:
        """Create and start a Bracket order."""
        order = BracketOrder(
            self.exchange,
            asset,
            OrderSide(side),
            amount,
            entry_price,
            stop_loss_price,
            take_profit_price,
        )
        self.active_orders[order.order_id] = order

        asyncio.create_task(self._execute_order(order))

        return order.order_id

    async def _execute_order(self, order):
        """Execute order and handle completion."""
        try:
            result = await order.execute()
            self.completed_orders.append(result)
        finally:
            if order.order_id in self.active_orders:
                del self.active_orders[order.order_id]

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an active order."""
        if order_id in self.active_orders:
            self.active_orders[order_id].cancel()
            return True
        return False

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get status of an order."""
        if order_id in self.active_orders:
            order = self.active_orders[order_id]
            return {
                "order_id": order_id,
                "status": order.status.value,
                "filled_amount": str(order.filled_amount),
                "total_amount": str(order.total_amount),
                "average_price": str(order.average_price),
                "fills_count": len(order.fills),
            }

        for result in self.completed_orders:
            if result.order_id == order_id:
                return {
                    "order_id": order_id,
                    "status": result.status.value,
                    "filled_amount": str(result.filled_amount),
                    "total_amount": str(result.total_amount),
                    "average_price": str(result.average_price),
                    "total_fees": str(result.total_fees),
                    "fills_count": len(result.fills),
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                }

        return None

    def list_active_orders(self) -> List[Dict]:
        """List all active orders."""
        return [
            {
                "order_id": order_id,
                "type": order.__class__.__name__,
                "asset": order.asset,
                "side": order.side.value,
                "status": order.status.value,
                "progress": f"{order.filled_amount}/{order.total_amount}",
            }
            for order_id, order in self.active_orders.items()
        ]
