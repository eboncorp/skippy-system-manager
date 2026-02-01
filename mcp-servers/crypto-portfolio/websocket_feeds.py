"""
WebSocket Real-Time Feeds
=========================

Live price updates and order book streams from exchanges.

Features:
- Price streaming from multiple exchanges
- Order book updates
- Trade stream
- Account balance updates
- Automatic reconnection

Usage:
    from websocket_feeds import PriceFeedManager

    async def on_price(symbol, price, exchange):
        print(f"{exchange}: {symbol} = ${price}")

    manager = PriceFeedManager()
    manager.subscribe("BTC-USD", on_price)
    await manager.start()
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Callable, Dict, List, Optional, Set

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PriceUpdate:
    """Real-time price update."""
    symbol: str
    price: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    exchange: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class TradeUpdate:
    """Real-time trade update."""
    symbol: str
    price: Decimal
    amount: Decimal
    side: str  # buy or sell
    trade_id: str
    exchange: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class OrderBookUpdate:
    """Order book update."""
    symbol: str
    bids: List[tuple]  # [(price, amount), ...]
    asks: List[tuple]  # [(price, amount), ...]
    exchange: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


# =============================================================================
# CALLBACK TYPES
# =============================================================================

PriceCallback = Callable[[PriceUpdate], None]
TradeCallback = Callable[[TradeUpdate], None]
OrderBookCallback = Callable[[OrderBookUpdate], None]


# =============================================================================
# BASE WEBSOCKET FEED
# =============================================================================


class BaseWebSocketFeed(ABC):
    """Base class for exchange WebSocket feeds."""

    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.subscriptions: Set[str] = set()

        self.price_callbacks: Dict[str, List[PriceCallback]] = {}
        self.trade_callbacks: Dict[str, List[TradeCallback]] = {}
        self.orderbook_callbacks: Dict[str, List[OrderBookCallback]] = {}

        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 60.0

    @property
    @abstractmethod
    def websocket_url(self) -> str:
        """WebSocket endpoint URL."""
        pass

    @abstractmethod
    async def _subscribe(self, symbols: List[str]):
        """Send subscription message."""
        pass

    @abstractmethod
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message."""
        pass

    async def connect(self):
        """Establish WebSocket connection."""
        logger.info(f"Connecting to {self.exchange_name} WebSocket...")
        self.ws = await websockets.connect(
            self.websocket_url,
            ping_interval=30,
            ping_timeout=10,
        )
        logger.info(f"Connected to {self.exchange_name}")
        self.reconnect_delay = 1.0  # Reset on successful connect

    async def disconnect(self):
        """Close WebSocket connection."""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info(f"Disconnected from {self.exchange_name}")

    async def start(self):
        """Start the WebSocket feed."""
        self.running = True

        while self.running:
            try:
                await self.connect()

                # Re-subscribe to all symbols
                if self.subscriptions:
                    await self._subscribe(list(self.subscriptions))

                # Message loop
                async for message in self.ws:
                    if not self.running:
                        break
                    try:
                        await self._handle_message(message)
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")

            except ConnectionClosed as e:
                logger.warning(f"{self.exchange_name} connection closed: {e}")
            except Exception as e:
                logger.error(f"{self.exchange_name} error: {e}")

            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    def subscribe_price(self, symbol: str, callback: PriceCallback):
        """Subscribe to price updates."""
        self.subscriptions.add(symbol)
        if symbol not in self.price_callbacks:
            self.price_callbacks[symbol] = []
        self.price_callbacks[symbol].append(callback)

    def subscribe_trades(self, symbol: str, callback: TradeCallback):
        """Subscribe to trade updates."""
        self.subscriptions.add(symbol)
        if symbol not in self.trade_callbacks:
            self.trade_callbacks[symbol] = []
        self.trade_callbacks[symbol].append(callback)

    def subscribe_orderbook(self, symbol: str, callback: OrderBookCallback):
        """Subscribe to order book updates."""
        self.subscriptions.add(symbol)
        if symbol not in self.orderbook_callbacks:
            self.orderbook_callbacks[symbol] = []
        self.orderbook_callbacks[symbol].append(callback)

    async def _emit_price(self, update: PriceUpdate):
        """Emit price update to callbacks."""
        update.exchange = self.exchange_name
        for callback in self.price_callbacks.get(update.symbol, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                logger.error(f"Price callback error: {e}")

    async def _emit_trade(self, update: TradeUpdate):
        """Emit trade update to callbacks."""
        update.exchange = self.exchange_name
        for callback in self.trade_callbacks.get(update.symbol, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                logger.error(f"Trade callback error: {e}")

    async def _emit_orderbook(self, update: OrderBookUpdate):
        """Emit order book update to callbacks."""
        update.exchange = self.exchange_name
        for callback in self.orderbook_callbacks.get(update.symbol, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                logger.error(f"OrderBook callback error: {e}")


# =============================================================================
# COINBASE WEBSOCKET FEED
# =============================================================================


class CoinbaseWebSocketFeed(BaseWebSocketFeed):
    """Coinbase Advanced Trade WebSocket feed."""

    def __init__(self):
        super().__init__("coinbase")

    @property
    def websocket_url(self) -> str:
        return "wss://advanced-trade-ws.coinbase.com"

    async def _subscribe(self, symbols: List[str]):
        """Subscribe to Coinbase channels."""
        # Ticker channel for prices
        subscribe_msg = {
            "type": "subscribe",
            "product_ids": symbols,
            "channel": "ticker"
        }
        await self.ws.send(json.dumps(subscribe_msg))

        # Matches channel for trades
        subscribe_msg["channel"] = "matches"
        await self.ws.send(json.dumps(subscribe_msg))

    async def _handle_message(self, message: str):
        """Handle Coinbase WebSocket message."""
        data = json.loads(message)

        if data.get("channel") == "ticker":
            for event in data.get("events", []):
                if event.get("type") == "update":
                    for ticker in event.get("tickers", []):
                        update = PriceUpdate(
                            symbol=ticker["product_id"],
                            price=Decimal(ticker["price"]),
                            bid=Decimal(ticker.get("best_bid", "0")),
                            ask=Decimal(ticker.get("best_ask", "0")),
                            volume_24h=Decimal(ticker.get("volume_24_h", "0")),
                        )
                        await self._emit_price(update)

        elif data.get("channel") == "matches":
            for event in data.get("events", []):
                for match in event.get("matches", []):
                    update = TradeUpdate(
                        symbol=match["product_id"],
                        price=Decimal(match["price"]),
                        amount=Decimal(match["size"]),
                        side=match["side"],
                        trade_id=match["trade_id"],
                    )
                    await self._emit_trade(update)


# =============================================================================
# KRAKEN WEBSOCKET FEED
# =============================================================================


class KrakenWebSocketFeed(BaseWebSocketFeed):
    """Kraken WebSocket feed."""

    def __init__(self):
        super().__init__("kraken")
        self.symbol_map: Dict[str, str] = {}  # Kraken uses different symbol format

    @property
    def websocket_url(self) -> str:
        return "wss://ws.kraken.com"

    def _convert_symbol(self, symbol: str) -> str:
        """Convert symbol to Kraken format."""
        # BTC-USD -> XBT/USD
        symbol = symbol.replace("BTC", "XBT").replace("-", "/")
        return symbol

    async def _subscribe(self, symbols: List[str]):
        """Subscribe to Kraken channels."""
        kraken_symbols = [self._convert_symbol(s) for s in symbols]

        # Store mapping
        for orig, kraken in zip(symbols, kraken_symbols):
            self.symbol_map[kraken] = orig

        # Ticker subscription
        subscribe_msg = {
            "event": "subscribe",
            "pair": kraken_symbols,
            "subscription": {"name": "ticker"}
        }
        await self.ws.send(json.dumps(subscribe_msg))

        # Trade subscription
        subscribe_msg["subscription"] = {"name": "trade"}
        await self.ws.send(json.dumps(subscribe_msg))

    async def _handle_message(self, message: str):
        """Handle Kraken WebSocket message."""
        data = json.loads(message)

        # Kraken sends arrays for data messages
        if isinstance(data, list) and len(data) >= 4:
            channel = data[-2]
            pair = data[-1]
            original_symbol = self.symbol_map.get(pair, pair)

            if channel == "ticker":
                ticker = data[1]
                update = PriceUpdate(
                    symbol=original_symbol,
                    price=Decimal(ticker["c"][0]),  # Last trade price
                    bid=Decimal(ticker["b"][0]),
                    ask=Decimal(ticker["a"][0]),
                    volume_24h=Decimal(ticker["v"][1]),
                )
                await self._emit_price(update)

            elif channel == "trade":
                for trade in data[1]:
                    update = TradeUpdate(
                        symbol=original_symbol,
                        price=Decimal(trade[0]),
                        amount=Decimal(trade[1]),
                        side="buy" if trade[3] == "b" else "sell",
                        trade_id=f"{trade[2]}",  # Timestamp as ID
                    )
                    await self._emit_trade(update)


# =============================================================================
# BINANCE WEBSOCKET FEED (for reference/future)
# =============================================================================


class BinanceWebSocketFeed(BaseWebSocketFeed):
    """Binance WebSocket feed."""

    def __init__(self):
        super().__init__("binance")
        self.stream_names: List[str] = []

    @property
    def websocket_url(self) -> str:
        if self.stream_names:
            streams = "/".join(self.stream_names)
            return f"wss://stream.binance.com:9443/stream?streams={streams}"
        return "wss://stream.binance.com:9443/ws"

    def _convert_symbol(self, symbol: str) -> str:
        """Convert symbol to Binance format."""
        # BTC-USD -> btcusdt
        return symbol.replace("-", "").replace("USD", "USDT").lower()

    async def _subscribe(self, symbols: List[str]):
        """Subscribe to Binance streams."""
        self.stream_names = []

        for symbol in symbols:
            binance_symbol = self._convert_symbol(symbol)
            self.stream_names.append(f"{binance_symbol}@ticker")
            self.stream_names.append(f"{binance_symbol}@trade")

        # Reconnect with new stream URL
        if self.ws:
            await self.ws.close()
            self.ws = await websockets.connect(self.websocket_url)

    async def _handle_message(self, message: str):
        """Handle Binance WebSocket message."""
        data = json.loads(message)

        if "stream" in data:
            stream = data["stream"]
            payload = data["data"]

            if "@ticker" in stream:
                update = PriceUpdate(
                    symbol=payload["s"],
                    price=Decimal(payload["c"]),
                    bid=Decimal(payload["b"]),
                    ask=Decimal(payload["a"]),
                    volume_24h=Decimal(payload["v"]),
                )
                await self._emit_price(update)

            elif "@trade" in stream:
                update = TradeUpdate(
                    symbol=payload["s"],
                    price=Decimal(payload["p"]),
                    amount=Decimal(payload["q"]),
                    side="buy" if payload["m"] else "sell",
                    trade_id=str(payload["t"]),
                )
                await self._emit_trade(update)


# =============================================================================
# PRICE FEED MANAGER
# =============================================================================


class PriceFeedManager:
    """
    Manages multiple exchange WebSocket feeds.

    Usage:
        manager = PriceFeedManager()

        def on_price(update: PriceUpdate):
            print(f"{update.exchange}: {update.symbol} = ${update.price}")

        manager.subscribe("BTC-USD", on_price)
        manager.subscribe("ETH-USD", on_price)

        await manager.start()
    """

    def __init__(self, exchanges: Optional[List[str]] = None):
        """
        Initialize with optional list of exchanges.

        Args:
            exchanges: List of exchange names. Default: ["coinbase", "kraken"]
        """
        self.feeds: Dict[str, BaseWebSocketFeed] = {}
        self.tasks: List[asyncio.Task] = []
        self.running = False

        # Initialize feeds
        exchange_classes = {
            "coinbase": CoinbaseWebSocketFeed,
            "kraken": KrakenWebSocketFeed,
            "binance": BinanceWebSocketFeed,
        }

        exchanges = exchanges or ["coinbase", "kraken"]
        for exchange in exchanges:
            if exchange in exchange_classes:
                self.feeds[exchange] = exchange_classes[exchange]()

    def subscribe(
        self,
        symbol: str,
        callback: PriceCallback,
        exchanges: Optional[List[str]] = None
    ):
        """
        Subscribe to price updates for a symbol.

        Args:
            symbol: Trading pair (e.g., "BTC-USD")
            callback: Function to call with PriceUpdate
            exchanges: Specific exchanges (default: all)
        """
        target_feeds = exchanges or list(self.feeds.keys())
        for exchange in target_feeds:
            if exchange in self.feeds:
                self.feeds[exchange].subscribe_price(symbol, callback)

    def subscribe_trades(
        self,
        symbol: str,
        callback: TradeCallback,
        exchanges: Optional[List[str]] = None
    ):
        """Subscribe to trade updates."""
        target_feeds = exchanges or list(self.feeds.keys())
        for exchange in target_feeds:
            if exchange in self.feeds:
                self.feeds[exchange].subscribe_trades(symbol, callback)

    def subscribe_orderbook(
        self,
        symbol: str,
        callback: OrderBookCallback,
        exchanges: Optional[List[str]] = None
    ):
        """Subscribe to order book updates."""
        target_feeds = exchanges or list(self.feeds.keys())
        for exchange in target_feeds:
            if exchange in self.feeds:
                self.feeds[exchange].subscribe_orderbook(symbol, callback)

    async def start(self):
        """Start all WebSocket feeds."""
        self.running = True

        for name, feed in self.feeds.items():
            task = asyncio.create_task(feed.start())
            self.tasks.append(task)
            logger.info(f"Started {name} feed")

        # Wait for all tasks
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def stop(self):
        """Stop all WebSocket feeds."""
        self.running = False

        for feed in self.feeds.values():
            await feed.disconnect()

        for task in self.tasks:
            task.cancel()

        self.tasks = []
        logger.info("All feeds stopped")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def example_usage():
    """Demonstrate WebSocket feed usage."""

    def on_price(update: PriceUpdate):
        print(f"[{update.exchange}] {update.symbol}: ${update.price:.2f}")

    def on_trade(update: TradeUpdate):
        print(f"[{update.exchange}] Trade: {update.side} {update.amount} {update.symbol} @ ${update.price:.2f}")

    manager = PriceFeedManager(exchanges=["coinbase"])

    # Subscribe to BTC and ETH prices
    manager.subscribe("BTC-USD", on_price)
    manager.subscribe("ETH-USD", on_price)
    manager.subscribe_trades("BTC-USD", on_trade)

    # Run for 30 seconds
    try:
        await asyncio.wait_for(manager.start(), timeout=30)
    except asyncio.TimeoutError:
        print("Timeout reached")
    finally:
        await manager.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())
