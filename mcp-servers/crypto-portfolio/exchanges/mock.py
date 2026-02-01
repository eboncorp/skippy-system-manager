"""
Mock Exchange Clients
=====================

Simulated exchange APIs for development, testing, and paper trading.
These clients mirror real exchange interfaces but use in-memory state.

Features:
- Paper trading with virtual balances
- Simulated order book and matching engine
- Latency simulation for realistic testing
- Error injection for testing error handling
- Historical data replay for backtesting

Usage:
    from exchanges.mock import MockExchangeFactory

    # Create mock Coinbase client
    coinbase = MockExchangeFactory.create("coinbase", initial_balance={"USD": 10000})

    # Place paper trade
    order = await coinbase.place_order("BTC-USD", "buy", 0.1, "market")
"""

import asyncio
import random
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================


class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"


@dataclass
class Order:
    """Represents a trading order."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    filled_amount: Decimal = Decimal("0")
    average_fill_price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    client_order_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "type": self.order_type.value,
            "amount": str(self.amount),
            "price": str(self.price) if self.price else None,
            "stop_price": str(self.stop_price) if self.stop_price else None,
            "filled_amount": str(self.filled_amount),
            "average_fill_price": str(self.average_fill_price) if self.average_fill_price else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "client_order_id": self.client_order_id
        }


@dataclass
class Trade:
    """Represents an executed trade."""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    amount: Decimal
    price: Decimal
    fee: Decimal
    fee_currency: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "amount": str(self.amount),
            "price": str(self.price),
            "fee": str(self.fee),
            "fee_currency": self.fee_currency,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class OrderBookEntry:
    """Single entry in order book."""
    price: Decimal
    amount: Decimal


@dataclass
class OrderBook:
    """Simulated order book."""
    symbol: str
    bids: List[OrderBookEntry] = field(default_factory=list)  # Buy orders (descending by price)
    asks: List[OrderBookEntry] = field(default_factory=list)  # Sell orders (ascending by price)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def best_bid(self) -> Optional[Decimal]:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> Optional[Decimal]:
        return self.asks[0].price if self.asks else None

    @property
    def spread(self) -> Optional[Decimal]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None


@dataclass
class StakingPosition:
    """Represents a staking position."""
    id: str
    asset: str
    amount: Decimal
    apy: Decimal
    rewards_earned: Decimal = Decimal("0")
    status: str = "active"
    staked_at: datetime = field(default_factory=datetime.utcnow)
    unbonding_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "asset": self.asset,
            "amount": str(self.amount),
            "apy": str(self.apy),
            "rewards_earned": str(self.rewards_earned),
            "status": self.status,
            "staked_at": self.staked_at.isoformat(),
            "unbonding_at": self.unbonding_at.isoformat() if self.unbonding_at else None
        }


# =============================================================================
# PRICE SIMULATION
# =============================================================================


class PriceSimulator:
    """Simulates realistic price movements."""

    # Base prices for common assets
    BASE_PRICES = {
        "BTC": Decimal("45000"),
        "ETH": Decimal("2750"),
        "SOL": Decimal("120"),
        "AVAX": Decimal("35"),
        "MATIC": Decimal("0.85"),
        "LINK": Decimal("15"),
        "UNI": Decimal("7.50"),
        "AAVE": Decimal("95"),
        "ATOM": Decimal("9.50"),
        "DOT": Decimal("7.00"),
        "ADA": Decimal("0.45"),
        "XRP": Decimal("0.55"),
        "DOGE": Decimal("0.08"),
        "SHIB": Decimal("0.000009"),
        "USDC": Decimal("1.00"),
        "USDT": Decimal("1.00"),
        "DAI": Decimal("1.00"),
    }

    # Volatility by asset (daily standard deviation)
    VOLATILITY = {
        "BTC": Decimal("0.03"),
        "ETH": Decimal("0.04"),
        "SOL": Decimal("0.06"),
        "AVAX": Decimal("0.07"),
        "MATIC": Decimal("0.08"),
        "USDC": Decimal("0.0001"),
        "USDT": Decimal("0.0001"),
        "DAI": Decimal("0.0002"),
    }

    DEFAULT_VOLATILITY = Decimal("0.05")

    def __init__(self, seed: Optional[int] = None):
        self.prices: Dict[str, Decimal] = {}
        self.random = random.Random(seed)
        self._initialize_prices()

    def _initialize_prices(self):
        """Initialize prices with small random offset from base."""
        for asset, base_price in self.BASE_PRICES.items():
            volatility = self.VOLATILITY.get(asset, self.DEFAULT_VOLATILITY)
            offset = Decimal(str(self.random.gauss(0, float(volatility) * 0.1)))
            self.prices[asset] = base_price * (1 + offset)

    def get_price(self, asset: str) -> Decimal:
        """Get current price for asset."""
        if asset not in self.prices:
            # Generate price for unknown asset
            self.prices[asset] = Decimal(str(self.random.uniform(0.01, 100)))
        return self.prices[asset]

    def tick(self):
        """Simulate one time step of price movement."""
        for asset in list(self.prices.keys()):
            volatility = self.VOLATILITY.get(asset, self.DEFAULT_VOLATILITY)
            # Random walk with mean reversion
            change = Decimal(str(self.random.gauss(0, float(volatility) * 0.01)))
            self.prices[asset] = max(Decimal("0.00000001"), self.prices[asset] * (1 + change))

    def get_order_book(self, symbol: str, depth: int = 10) -> OrderBook:
        """Generate simulated order book."""
        base_asset = symbol.split("-")[0]
        mid_price = self.get_price(base_asset)

        # Generate bids (buy orders below mid)
        bids = []
        for i in range(depth):
            offset = Decimal(str(0.001 * (i + 1)))
            price = mid_price * (1 - offset)
            amount = Decimal(str(self.random.uniform(0.1, 10)))
            bids.append(OrderBookEntry(price=price, amount=amount))

        # Generate asks (sell orders above mid)
        asks = []
        for i in range(depth):
            offset = Decimal(str(0.001 * (i + 1)))
            price = mid_price * (1 + offset)
            amount = Decimal(str(self.random.uniform(0.1, 10)))
            asks.append(OrderBookEntry(price=price, amount=amount))

        return OrderBook(symbol=symbol, bids=bids, asks=asks)


# =============================================================================
# ERROR INJECTION
# =============================================================================


class ErrorInjector:
    """Injects errors for testing error handling."""

    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)
        self.error_rates: Dict[str, float] = {
            "rate_limit": 0.0,
            "timeout": 0.0,
            "auth_failure": 0.0,
            "insufficient_funds": 0.0,
            "invalid_order": 0.0,
            "network_error": 0.0,
        }
        self.enabled = False

    def set_error_rate(self, error_type: str, rate: float):
        """Set probability of an error type (0.0 to 1.0)."""
        if error_type in self.error_rates:
            self.error_rates[error_type] = max(0.0, min(1.0, rate))

    def enable(self):
        """Enable error injection."""
        self.enabled = True

    def disable(self):
        """Disable error injection."""
        self.enabled = False

    def maybe_raise(self, *error_types: str):
        """Potentially raise an error based on configured rates."""
        if not self.enabled:
            return

        for error_type in error_types:
            rate = self.error_rates.get(error_type, 0.0)
            if self.random.random() < rate:
                self._raise_error(error_type)

    def _raise_error(self, error_type: str):
        """Raise the appropriate exception."""
        if error_type == "rate_limit":
            raise RateLimitError("Rate limit exceeded. Please wait.")
        elif error_type == "timeout":
            raise TimeoutError("Request timed out")
        elif error_type == "auth_failure":
            raise AuthenticationError("Invalid API credentials")
        elif error_type == "insufficient_funds":
            raise InsufficientFundsError("Insufficient balance for this operation")
        elif error_type == "invalid_order":
            raise InvalidOrderError("Order validation failed")
        elif error_type == "network_error":
            raise NetworkError("Network connection failed")


class ExchangeError(Exception):
    """Base exception for exchange errors."""
    pass


class RateLimitError(ExchangeError):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(ExchangeError):
    """Raised when authentication fails."""
    pass


class InsufficientFundsError(ExchangeError):
    """Raised when balance is insufficient."""
    pass


class InvalidOrderError(ExchangeError):
    """Raised when order is invalid."""
    pass


class NetworkError(ExchangeError):
    """Raised when network error occurs."""
    pass


# =============================================================================
# BASE MOCK EXCHANGE
# =============================================================================


class BaseMockExchange(ABC):
    """Base class for mock exchange implementations."""

    # Exchange-specific fee rates
    MAKER_FEE = Decimal("0.001")  # 0.1%
    TAKER_FEE = Decimal("0.002")  # 0.2%

    # Staking APYs by asset
    STAKING_APYS = {
        "ETH": Decimal("4.5"),
        "SOL": Decimal("7.0"),
        "ATOM": Decimal("15.0"),
        "DOT": Decimal("12.0"),
        "ADA": Decimal("3.5"),
        "AVAX": Decimal("8.0"),
    }

    def __init__(
        self,
        name: str,
        initial_balances: Optional[Dict[str, Decimal]] = None,
        latency_ms: Tuple[int, int] = (10, 100),
        seed: Optional[int] = None
    ):
        self.name = name
        self.balances: Dict[str, Decimal] = {}
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        self.staking_positions: Dict[str, StakingPosition] = {}

        self.price_simulator = PriceSimulator(seed)
        self.error_injector = ErrorInjector(seed)
        self.latency_range = latency_ms
        self.random = random.Random(seed)

        # Initialize balances
        if initial_balances:
            for asset, amount in initial_balances.items():
                self.balances[asset] = Decimal(str(amount))
        else:
            # Default paper trading balance
            self.balances = {
                "USD": Decimal("100000"),
                "USDC": Decimal("50000"),
                "BTC": Decimal("1.0"),
                "ETH": Decimal("10.0"),
            }

    async def _simulate_latency(self):
        """Simulate network latency."""
        latency = self.random.randint(*self.latency_range)
        await asyncio.sleep(latency / 1000)

    def _generate_id(self, prefix: str = "") -> str:
        """Generate unique ID."""
        return f"{prefix}{uuid.uuid4().hex[:12]}"

    # -------------------------------------------------------------------------
    # Balance Operations
    # -------------------------------------------------------------------------

    async def get_balances(self) -> Dict[str, Dict[str, Decimal]]:
        """Get all balances."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        result = {}
        for asset, amount in self.balances.items():
            # Calculate available (excluding open orders)
            reserved = self._get_reserved_balance(asset)
            result[asset] = {
                "total": amount,
                "available": amount - reserved,
                "reserved": reserved
            }
        return result

    async def get_balance(self, asset: str) -> Dict[str, Decimal]:
        """Get balance for specific asset."""
        balances = await self.get_balances()
        return balances.get(asset, {"total": Decimal("0"), "available": Decimal("0"), "reserved": Decimal("0")})

    def _get_reserved_balance(self, asset: str) -> Decimal:
        """Calculate balance reserved in open orders."""
        reserved = Decimal("0")
        for order in self.orders.values():
            if order.status not in [OrderStatus.OPEN, OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]:
                continue

            base, quote = order.symbol.split("-")
            remaining = order.amount - order.filled_amount

            if order.side == OrderSide.BUY and asset == quote:
                # Buying: reserve quote currency
                price = order.price or self.price_simulator.get_price(base)
                reserved += remaining * price
            elif order.side == OrderSide.SELL and asset == base:
                # Selling: reserve base currency
                reserved += remaining

        return reserved

    # -------------------------------------------------------------------------
    # Order Operations
    # -------------------------------------------------------------------------

    async def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None
    ) -> Order:
        """Place a new order."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "rate_limit", "network_error")

        # Parse inputs
        side_enum = OrderSide(side.lower())
        type_enum = OrderType(order_type.lower())
        amount_dec = Decimal(str(amount))
        price_dec = Decimal(str(price)) if price else None
        stop_price_dec = Decimal(str(stop_price)) if stop_price else None

        # Validate order
        base, quote = symbol.split("-")
        self._validate_order(symbol, side_enum, amount_dec, type_enum, price_dec)

        # Create order
        order = Order(
            id=self._generate_id("ord_"),
            symbol=symbol,
            side=side_enum,
            order_type=type_enum,
            amount=amount_dec,
            price=price_dec,
            stop_price=stop_price_dec,
            client_order_id=client_order_id,
            status=OrderStatus.OPEN
        )

        self.orders[order.id] = order

        # Execute market orders immediately
        if type_enum == OrderType.MARKET:
            await self._execute_market_order(order)

        return order

    def _validate_order(
        self,
        symbol: str,
        side: OrderSide,
        amount: Decimal,
        order_type: OrderType,
        price: Optional[Decimal]
    ):
        """Validate order parameters."""
        base, quote = symbol.split("-")

        # Check for sufficient balance
        if side == OrderSide.BUY:
            required = amount * (price or self.price_simulator.get_price(base))
            available = self.balances.get(quote, Decimal("0")) - self._get_reserved_balance(quote)
            if available < required:
                raise InsufficientFundsError(f"Insufficient {quote} balance. Required: {required}, Available: {available}")
        else:
            available = self.balances.get(base, Decimal("0")) - self._get_reserved_balance(base)
            if available < amount:
                raise InsufficientFundsError(f"Insufficient {base} balance. Required: {amount}, Available: {available}")

        # Validate limit order has price
        if order_type == OrderType.LIMIT and price is None:
            raise InvalidOrderError("Limit orders require a price")

    async def _execute_market_order(self, order: Order):
        """Execute a market order against the order book."""
        base, quote = order.symbol.split("-")
        book = self.price_simulator.get_order_book(order.symbol)

        # Determine execution price
        if order.side == OrderSide.BUY:
            exec_price = book.best_ask or self.price_simulator.get_price(base)
        else:
            exec_price = book.best_bid or self.price_simulator.get_price(base)

        # Add small slippage for realism
        slippage = Decimal(str(self.random.uniform(-0.001, 0.001)))
        exec_price = exec_price * (1 + slippage)

        # Calculate fee
        fee = order.amount * exec_price * self.TAKER_FEE

        # Update balances
        if order.side == OrderSide.BUY:
            cost = order.amount * exec_price + fee
            self.balances[quote] = self.balances.get(quote, Decimal("0")) - cost
            self.balances[base] = self.balances.get(base, Decimal("0")) + order.amount
        else:
            proceeds = order.amount * exec_price - fee
            self.balances[base] = self.balances.get(base, Decimal("0")) - order.amount
            self.balances[quote] = self.balances.get(quote, Decimal("0")) + proceeds

        # Update order
        order.filled_amount = order.amount
        order.average_fill_price = exec_price
        order.status = OrderStatus.FILLED
        order.updated_at = datetime.utcnow()

        # Record trade
        trade = Trade(
            id=self._generate_id("trd_"),
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            amount=order.amount,
            price=exec_price,
            fee=fee,
            fee_currency=quote
        )
        self.trades.append(trade)

    async def cancel_order(self, order_id: str) -> Order:
        """Cancel an open order."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        if order_id not in self.orders:
            raise InvalidOrderError(f"Order {order_id} not found")

        order = self.orders[order_id]

        if order.status not in [OrderStatus.OPEN, OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]:
            raise InvalidOrderError(f"Order {order_id} cannot be cancelled (status: {order.status})")

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()

        return order

    async def get_order(self, order_id: str) -> Order:
        """Get order by ID."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        if order_id not in self.orders:
            raise InvalidOrderError(f"Order {order_id} not found")

        return self.orders[order_id]

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        open_statuses = [OrderStatus.OPEN, OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
        orders = [o for o in self.orders.values() if o.status in open_statuses]

        if symbol:
            orders = [o for o in orders if o.symbol == symbol]

        return orders

    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Order]:
        """Get order history."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        orders = list(self.orders.values())

        if symbol:
            orders = [o for o in orders if o.symbol == symbol]

        # Sort by created_at descending
        orders.sort(key=lambda o: o.created_at, reverse=True)

        return orders[:limit]

    # -------------------------------------------------------------------------
    # Trade History
    # -------------------------------------------------------------------------

    async def get_trades(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Trade]:
        """Get trade history."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        trades = self.trades.copy()

        if symbol:
            trades = [t for t in trades if t.symbol == symbol]

        # Sort by timestamp descending
        trades.sort(key=lambda t: t.timestamp, reverse=True)

        return trades[:limit]

    # -------------------------------------------------------------------------
    # Market Data
    # -------------------------------------------------------------------------

    async def get_price(self, symbol: str) -> Decimal:
        """Get current price for a symbol."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("network_error")

        base = symbol.split("-")[0]
        return self.price_simulator.get_price(base)

    async def get_order_book(self, symbol: str, depth: int = 10) -> OrderBook:
        """Get order book for a symbol."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("network_error")

        return self.price_simulator.get_order_book(symbol, depth)

    # -------------------------------------------------------------------------
    # Staking Operations
    # -------------------------------------------------------------------------

    async def stake(self, asset: str, amount: float) -> StakingPosition:
        """Stake an asset."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        amount_dec = Decimal(str(amount))

        # Check balance
        available = self.balances.get(asset, Decimal("0"))
        if available < amount_dec:
            raise InsufficientFundsError(f"Insufficient {asset} balance")

        # Get APY
        apy = self.STAKING_APYS.get(asset, Decimal("5.0"))

        # Deduct from balance
        self.balances[asset] -= amount_dec

        # Create position
        position = StakingPosition(
            id=self._generate_id("stk_"),
            asset=asset,
            amount=amount_dec,
            apy=apy
        )

        self.staking_positions[position.id] = position

        return position

    async def unstake(self, position_id: str) -> StakingPosition:
        """Initiate unstaking."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        if position_id not in self.staking_positions:
            raise InvalidOrderError(f"Staking position {position_id} not found")

        position = self.staking_positions[position_id]
        position.status = "unbonding"
        position.unbonding_at = datetime.utcnow() + timedelta(days=21)

        return position

    async def claim_staking_rewards(self, position_id: Optional[str] = None) -> Dict[str, Decimal]:
        """Claim staking rewards."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        claimed = {}

        positions = [self.staking_positions[position_id]] if position_id else list(self.staking_positions.values())

        for position in positions:
            if position.rewards_earned > 0:
                asset = position.asset
                claimed[asset] = claimed.get(asset, Decimal("0")) + position.rewards_earned
                self.balances[asset] = self.balances.get(asset, Decimal("0")) + position.rewards_earned
                position.rewards_earned = Decimal("0")

        return claimed

    async def get_staking_positions(self) -> List[StakingPosition]:
        """Get all staking positions."""
        await self._simulate_latency()
        self.error_injector.maybe_raise("auth_failure", "network_error")

        return list(self.staking_positions.values())

    def accrue_staking_rewards(self, hours: float = 1.0):
        """Simulate reward accrual over time."""
        for position in self.staking_positions.values():
            if position.status != "active":
                continue

            # Calculate hourly reward rate
            hourly_rate = position.apy / Decimal("8760")  # 365 * 24
            reward = position.amount * hourly_rate * Decimal(str(hours)) / Decimal("100")
            position.rewards_earned += reward


# =============================================================================
# EXCHANGE-SPECIFIC IMPLEMENTATIONS
# =============================================================================


class MockCoinbase(BaseMockExchange):
    """Mock Coinbase exchange."""

    MAKER_FEE = Decimal("0.004")  # 0.4%
    TAKER_FEE = Decimal("0.006")  # 0.6%

    def __init__(self, **kwargs):
        super().__init__("coinbase", **kwargs)


class MockKraken(BaseMockExchange):
    """Mock Kraken exchange."""

    MAKER_FEE = Decimal("0.0016")  # 0.16%
    TAKER_FEE = Decimal("0.0026")  # 0.26%

    def __init__(self, **kwargs):
        super().__init__("kraken", **kwargs)


class MockCryptoCom(BaseMockExchange):
    """Mock Crypto.com exchange."""

    MAKER_FEE = Decimal("0.004")  # 0.4%
    TAKER_FEE = Decimal("0.004")  # 0.4%

    def __init__(self, **kwargs):
        super().__init__("crypto.com", **kwargs)


class MockGemini(BaseMockExchange):
    """Mock Gemini exchange."""

    MAKER_FEE = Decimal("0.002")  # 0.2%
    TAKER_FEE = Decimal("0.004")  # 0.4%

    def __init__(self, **kwargs):
        super().__init__("gemini", **kwargs)


# =============================================================================
# FACTORY
# =============================================================================


class MockExchangeFactory:
    """Factory for creating mock exchange instances."""

    EXCHANGES = {
        "coinbase": MockCoinbase,
        "kraken": MockKraken,
        "crypto.com": MockCryptoCom,
        "gemini": MockGemini,
    }

    @classmethod
    def create(
        cls,
        exchange_name: str,
        initial_balances: Optional[Dict[str, float]] = None,
        latency_ms: Tuple[int, int] = (10, 100),
        seed: Optional[int] = None
    ) -> BaseMockExchange:
        """Create a mock exchange instance."""
        exchange_name = exchange_name.lower()

        if exchange_name not in cls.EXCHANGES:
            raise ValueError(f"Unknown exchange: {exchange_name}. Available: {list(cls.EXCHANGES.keys())}")

        # Convert balances to Decimal
        balances = None
        if initial_balances:
            balances = {k: Decimal(str(v)) for k, v in initial_balances.items()}

        return cls.EXCHANGES[exchange_name](
            initial_balances=balances,
            latency_ms=latency_ms,
            seed=seed
        )

    @classmethod
    def create_all(
        cls,
        initial_balances: Optional[Dict[str, float]] = None,
        **kwargs
    ) -> Dict[str, BaseMockExchange]:
        """Create instances of all mock exchanges."""
        return {
            name: cls.create(name, initial_balances, **kwargs)
            for name in cls.EXCHANGES
        }


# =============================================================================
# HISTORICAL DATA REPLAY
# =============================================================================


class HistoricalDataReplayer:
    """Replay historical price data for backtesting."""

    def __init__(self, exchange: BaseMockExchange):
        self.exchange = exchange
        self.historical_data: Dict[str, List[Dict]] = {}
        self.current_index = 0

    def load_data(self, symbol: str, candles: List[Dict]):
        """
        Load historical candle data.

        Each candle should have: timestamp, open, high, low, close, volume
        """
        self.historical_data[symbol] = candles
        self.current_index = 0

    def step(self) -> bool:
        """
        Advance to next time step.

        Returns False if no more data.
        """
        if not self.historical_data:
            return False

        # Get the first symbol's data length as reference
        first_symbol = next(iter(self.historical_data))
        if self.current_index >= len(self.historical_data[first_symbol]):
            return False

        # Update prices based on historical close
        for symbol, candles in self.historical_data.items():
            if self.current_index < len(candles):
                candle = candles[self.current_index]
                base = symbol.split("-")[0]
                self.exchange.price_simulator.prices[base] = Decimal(str(candle["close"]))

        self.current_index += 1
        return True

    def reset(self):
        """Reset to beginning of data."""
        self.current_index = 0


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def example_usage():
    """Demonstrate mock exchange usage."""

    # Create mock Coinbase with custom balance
    coinbase = MockExchangeFactory.create(
        "coinbase",
        initial_balances={"USD": 10000, "BTC": 0.5},
        latency_ms=(50, 150),
        seed=42
    )

    # Get balances
    balances = await coinbase.get_balances()
    print(f"Initial balances: {balances}")

    # Get BTC price
    price = await coinbase.get_price("BTC-USD")
    print(f"BTC price: ${price:,.2f}")

    # Place market buy order
    order = await coinbase.place_order(
        symbol="BTC-USD",
        side="buy",
        amount=0.1,
        order_type="market"
    )
    print(f"Order placed: {order.to_dict()}")

    # Get updated balances
    balances = await coinbase.get_balances()
    print(f"Updated balances: {balances}")

    # Stake ETH
    coinbase.balances["ETH"] = Decimal("5.0")
    position = await coinbase.stake("ETH", 2.0)
    print(f"Staking position: {position.to_dict()}")

    # Simulate 24 hours of staking rewards
    coinbase.accrue_staking_rewards(hours=24)
    positions = await coinbase.get_staking_positions()
    print(f"After 24h: {positions[0].to_dict()}")

    # Enable error injection for testing
    coinbase.error_injector.enable()
    coinbase.error_injector.set_error_rate("rate_limit", 0.3)

    try:
        await coinbase.get_balances()
    except RateLimitError as e:
        print(f"Error injection worked: {e}")


if __name__ == "__main__":
    asyncio.run(example_usage())
