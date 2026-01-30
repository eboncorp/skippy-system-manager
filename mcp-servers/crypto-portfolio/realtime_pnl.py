"""
Real-time PnL Streaming via WebSocket.

Provides live portfolio value updates, PnL tracking,
and real-time alerts to connected clients.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Set, Any
from enum import Enum
import asyncio
import json
import uuid


class StreamEventType(Enum):
    """Types of streaming events."""
    PORTFOLIO_UPDATE = "portfolio_update"
    PRICE_UPDATE = "price_update"
    PNL_UPDATE = "pnl_update"
    ALERT = "alert"
    TRADE_EXECUTED = "trade_executed"
    STAKING_REWARD = "staking_reward"
    CONNECTION_STATUS = "connection_status"


@dataclass
class PriceUpdate:
    """Real-time price update for an asset."""
    asset: str
    price: Decimal
    change_24h: Decimal
    change_24h_pct: float
    volume_24h: Decimal
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "asset": self.asset,
            "price": str(self.price),
            "change_24h": str(self.change_24h),
            "change_24h_pct": self.change_24h_pct,
            "volume_24h": str(self.volume_24h),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PnLUpdate:
    """Real-time PnL update for the portfolio or an asset."""
    asset: Optional[str]  # None for portfolio-level
    current_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: float
    realized_pnl_today: Decimal
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "asset": self.asset,
            "current_value": str(self.current_value),
            "cost_basis": str(self.cost_basis),
            "unrealized_pnl": str(self.unrealized_pnl),
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "realized_pnl_today": str(self.realized_pnl_today),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PortfolioSnapshot:
    """Complete portfolio snapshot."""
    total_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_pct: float
    total_realized_pnl_today: Decimal
    holdings: Dict[str, Dict]  # asset -> {amount, value, pnl, etc.}
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "total_value": str(self.total_value),
            "total_cost_basis": str(self.total_cost_basis),
            "total_unrealized_pnl": str(self.total_unrealized_pnl),
            "total_unrealized_pnl_pct": self.total_unrealized_pnl_pct,
            "total_realized_pnl_today": str(self.total_realized_pnl_today),
            "holdings": self.holdings,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class StreamEvent:
    """Event to be streamed to clients."""
    event_type: StreamEventType
    data: Dict
    timestamp: datetime = field(default_factory=datetime.now)

    def to_json(self) -> str:
        return json.dumps({
            "type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        })


class PriceStreamer:
    """
    Streams real-time price updates.

    Connects to exchange WebSocket feeds and broadcasts
    price updates to subscribers.
    """

    def __init__(self, exchanges: List[str] = None):
        """
        Initialize price streamer.

        Args:
            exchanges: List of exchange names to connect to
        """
        self.exchanges = exchanges or ["coinbase", "binance"]
        self.subscribers: Set[Callable] = set()
        self.prices: Dict[str, PriceUpdate] = {}
        self.running = False
        self._tasks: List[asyncio.Task] = []

    def subscribe(self, callback: Callable[[PriceUpdate], None]):
        """Subscribe to price updates."""
        self.subscribers.add(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from price updates."""
        self.subscribers.discard(callback)

    async def start(self, assets: List[str]):
        """Start streaming prices for specified assets."""
        self.running = True

        # Start price fetching tasks
        for asset in assets:
            task = asyncio.create_task(self._price_loop(asset))
            self._tasks.append(task)

    async def stop(self):
        """Stop streaming."""
        self.running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

    async def _price_loop(self, asset: str):
        """Continuously fetch and broadcast price updates."""
        last_price = Decimal("0")

        while self.running:
            try:
                # In production, this would connect to WebSocket
                # For now, we simulate with polling
                price_data = await self._fetch_price(asset)

                if price_data:
                    update = PriceUpdate(
                        asset=asset,
                        price=price_data["price"],
                        change_24h=price_data["change_24h"],
                        change_24h_pct=price_data["change_24h_pct"],
                        volume_24h=price_data["volume_24h"],
                    )

                    self.prices[asset] = update

                    # Notify subscribers
                    for callback in self.subscribers:
                        try:
                            await self._call_callback(callback, update)
                        except Exception as e:
                            print(f"Subscriber callback error: {e}")

                    last_price = price_data["price"]

            except Exception as e:
                print(f"Price fetch error for {asset}: {e}")

            await asyncio.sleep(1)  # Update every second

    async def _call_callback(self, callback: Callable, update: PriceUpdate):
        """Call callback, handling both sync and async."""
        if asyncio.iscoroutinefunction(callback):
            await callback(update)
        else:
            callback(update)

    async def _fetch_price(self, asset: str) -> Optional[Dict]:
        """Fetch current price (placeholder for actual exchange API)."""
        # This would be replaced with actual exchange WebSocket or API call
        import random

        # Simulate price data
        base_prices = {
            "BTC": 45000,
            "ETH": 2500,
            "SOL": 100,
            "AVAX": 35,
            "MATIC": 0.80,
        }

        if asset in base_prices:
            base = base_prices[asset]
            variation = random.uniform(-0.001, 0.001)
            price = Decimal(str(base * (1 + variation)))

            return {
                "price": price,
                "change_24h": price * Decimal(str(random.uniform(-0.05, 0.05))),
                "change_24h_pct": random.uniform(-5, 5),
                "volume_24h": Decimal(str(random.uniform(1000000, 10000000))),
            }

        return None

    def get_latest_price(self, asset: str) -> Optional[PriceUpdate]:
        """Get latest cached price for an asset."""
        return self.prices.get(asset)


class PnLTracker:
    """
    Tracks real-time PnL for portfolio and individual positions.

    Updates PnL as prices change and broadcasts updates.
    """

    def __init__(self):
        self.holdings: Dict[str, Dict] = {}  # asset -> {amount, cost_basis}
        self.prices: Dict[str, Decimal] = {}
        self.subscribers: Set[Callable] = set()
        self.realized_pnl_today: Decimal = Decimal("0")
        self._last_snapshot: Optional[PortfolioSnapshot] = None

    def subscribe(self, callback: Callable[[PnLUpdate], None]):
        """Subscribe to PnL updates."""
        self.subscribers.add(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from PnL updates."""
        self.subscribers.discard(callback)

    def set_holdings(self, holdings: Dict[str, Dict]):
        """
        Set current holdings.

        Args:
            holdings: Dict of asset -> {amount: Decimal, cost_basis: Decimal}
        """
        self.holdings = holdings

    def update_price(self, asset: str, price: Decimal):
        """Update price for an asset and recalculate PnL."""
        self.prices[asset] = price
        self._recalculate_and_notify(asset)

    def record_realized_pnl(self, pnl: Decimal):
        """Record realized PnL from a trade."""
        self.realized_pnl_today += pnl

    def _recalculate_and_notify(self, updated_asset: str):
        """Recalculate PnL and notify subscribers."""
        if updated_asset not in self.holdings:
            return

        holding = self.holdings[updated_asset]
        amount = Decimal(str(holding.get("amount", 0)))
        cost_basis = Decimal(str(holding.get("cost_basis", 0)))
        price = self.prices.get(updated_asset, Decimal("0"))

        current_value = amount * price
        unrealized_pnl = current_value - cost_basis
        unrealized_pnl_pct = float(
            (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
        )

        update = PnLUpdate(
            asset=updated_asset,
            current_value=current_value,
            cost_basis=cost_basis,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            realized_pnl_today=self.realized_pnl_today,
        )

        # Notify subscribers
        for callback in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(update))
                else:
                    callback(update)
            except Exception as e:
                print(f"PnL subscriber error: {e}")

    def get_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Get current portfolio snapshot with all holdings."""
        total_value = Decimal("0")
        total_cost_basis = Decimal("0")
        holdings_data = {}

        for asset, holding in self.holdings.items():
            amount = Decimal(str(holding.get("amount", 0)))
            cost_basis = Decimal(str(holding.get("cost_basis", 0)))
            price = self.prices.get(asset, Decimal("0"))

            current_value = amount * price
            unrealized_pnl = current_value - cost_basis
            unrealized_pnl_pct = float(
                (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            )

            total_value += current_value
            total_cost_basis += cost_basis

            holdings_data[asset] = {
                "amount": str(amount),
                "price": str(price),
                "current_value": str(current_value),
                "cost_basis": str(cost_basis),
                "unrealized_pnl": str(unrealized_pnl),
                "unrealized_pnl_pct": unrealized_pnl_pct,
            }

        total_unrealized_pnl = total_value - total_cost_basis
        total_unrealized_pnl_pct = float(
            (total_unrealized_pnl / total_cost_basis * 100)
            if total_cost_basis > 0 else 0
        )

        snapshot = PortfolioSnapshot(
            total_value=total_value,
            total_cost_basis=total_cost_basis,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_pct=total_unrealized_pnl_pct,
            total_realized_pnl_today=self.realized_pnl_today,
            holdings=holdings_data,
        )

        self._last_snapshot = snapshot
        return snapshot


class RealtimeStreamManager:
    """
    Manages all real-time streaming for the portfolio.

    Coordinates price streaming, PnL tracking, and client connections.
    """

    def __init__(self, portfolio_manager=None):
        """
        Initialize stream manager.

        Args:
            portfolio_manager: Optional portfolio manager for data sync
        """
        self.portfolio_manager = portfolio_manager
        self.price_streamer = PriceStreamer()
        self.pnl_tracker = PnLTracker()
        self.clients: Dict[str, Dict] = {}  # client_id -> {websocket, subscriptions}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._broadcast_task: Optional[asyncio.Task] = None

    async def start(self, assets: List[str]):
        """
        Start real-time streaming.

        Args:
            assets: List of assets to track
        """
        self.running = True

        # Connect price updates to PnL tracker
        self.price_streamer.subscribe(self._on_price_update)

        # Start price streaming
        await self.price_streamer.start(assets)

        # Start event broadcast loop
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())

    async def stop(self):
        """Stop streaming."""
        self.running = False
        await self.price_streamer.stop()

        if self._broadcast_task:
            self._broadcast_task.cancel()

    def register_client(
        self,
        client_id: str,
        websocket: Any,
        subscriptions: List[str] = None,
    ):
        """
        Register a new client connection.

        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection object
            subscriptions: List of event types to subscribe to
        """
        self.clients[client_id] = {
            "websocket": websocket,
            "subscriptions": set(subscriptions or ["all"]),
            "connected_at": datetime.now(),
        }

    def unregister_client(self, client_id: str):
        """Unregister a client."""
        if client_id in self.clients:
            del self.clients[client_id]

    async def _on_price_update(self, update: PriceUpdate):
        """Handle price update from streamer."""
        # Update PnL tracker
        self.pnl_tracker.update_price(update.asset, update.price)

        # Queue event for broadcast
        event = StreamEvent(
            event_type=StreamEventType.PRICE_UPDATE,
            data=update.to_dict(),
        )
        await self.event_queue.put(event)

    async def _broadcast_loop(self):
        """Continuously broadcast events to clients."""
        while self.running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )

                # Broadcast to subscribed clients
                await self._broadcast_event(event)

            except asyncio.TimeoutError:
                # Send heartbeat/portfolio update periodically
                await self._send_portfolio_update()
            except Exception as e:
                print(f"Broadcast error: {e}")

    async def _broadcast_event(self, event: StreamEvent):
        """Broadcast event to all subscribed clients."""
        event_json = event.to_json()

        for client_id, client in list(self.clients.items()):
            subs = client["subscriptions"]

            # Check if client is subscribed to this event type
            if "all" in subs or event.event_type.value in subs:
                try:
                    ws = client["websocket"]
                    if hasattr(ws, 'send'):
                        await ws.send(event_json)
                    elif hasattr(ws, 'send_text'):
                        await ws.send_text(event_json)
                except Exception as e:
                    print(f"Failed to send to client {client_id}: {e}")
                    self.unregister_client(client_id)

    async def _send_portfolio_update(self):
        """Send periodic portfolio snapshot."""
        snapshot = self.pnl_tracker.get_portfolio_snapshot()

        event = StreamEvent(
            event_type=StreamEventType.PORTFOLIO_UPDATE,
            data=snapshot.to_dict(),
        )
        await self._broadcast_event(event)

    def set_holdings(self, holdings: Dict[str, Dict]):
        """Update holdings in PnL tracker."""
        self.pnl_tracker.set_holdings(holdings)

    def send_alert(self, alert_type: str, message: str, data: Dict = None):
        """Send an alert to all clients."""
        event = StreamEvent(
            event_type=StreamEventType.ALERT,
            data={
                "alert_type": alert_type,
                "message": message,
                "data": data or {},
            },
        )
        asyncio.create_task(self._broadcast_event(event))

    def notify_trade(self, trade_data: Dict):
        """Notify clients of a trade execution."""
        event = StreamEvent(
            event_type=StreamEventType.TRADE_EXECUTED,
            data=trade_data,
        )
        asyncio.create_task(self._broadcast_event(event))


# FastAPI/Starlette WebSocket endpoint example
async def websocket_endpoint(websocket, stream_manager: RealtimeStreamManager):
    """
    WebSocket endpoint for real-time streaming.

    Example usage with FastAPI:

    ```python
    from fastapi import FastAPI, WebSocket

    app = FastAPI()
    stream_manager = RealtimeStreamManager()

    @app.websocket("/ws/portfolio")
    async def portfolio_ws(websocket: WebSocket):
        await websocket.accept()
        await websocket_endpoint(websocket, stream_manager)
    ```
    """
    client_id = str(uuid.uuid4())[:8]

    try:
        # Accept connection
        if hasattr(websocket, 'accept'):
            await websocket.accept()

        # Register client
        stream_manager.register_client(client_id, websocket)

        # Send initial snapshot
        snapshot = stream_manager.pnl_tracker.get_portfolio_snapshot()
        await websocket.send_text(json.dumps({
            "type": "initial_snapshot",
            "data": snapshot.to_dict(),
        }))

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle subscription changes
                if message.get("action") == "subscribe":
                    events = message.get("events", [])
                    stream_manager.clients[client_id]["subscriptions"].update(events)
                elif message.get("action") == "unsubscribe":
                    events = message.get("events", [])
                    stream_manager.clients[client_id]["subscriptions"].difference_update(events)

            except Exception:
                break

    finally:
        stream_manager.unregister_client(client_id)


# Convenience function to create streaming server
def create_streaming_server(
    portfolio_manager=None,
    host: str = "0.0.0.0",
    port: int = 8765,
):
    """
    Create a standalone WebSocket streaming server.

    Returns the stream manager for integration with the rest of the app.
    """
    stream_manager = RealtimeStreamManager(portfolio_manager)

    # This would typically be integrated with your web framework
    # Example with websockets library:
    #
    # async def handler(websocket, path):
    #     await websocket_endpoint(websocket, stream_manager)
    #
    # server = await websockets.serve(handler, host, port)

    return stream_manager
