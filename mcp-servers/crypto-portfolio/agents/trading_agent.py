"""
Crypto Trading Agent Framework

Transforms signal analysis into automated trading actions.
Supports multiple strategies, risk management, and exchange integration.

IMPORTANT: Trading cryptocurrencies involves substantial risk. 
Always start with paper trading and small positions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import asyncio
import logging
import json
import hashlib
import hmac
import time

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class TradingMode(Enum):
    PAPER = "paper"          # Simulated trading
    LIVE = "live"            # Real money
    BACKTEST = "backtest"    # Historical simulation


class StrategyType(Enum):
    DCA_SIGNAL = "dca_signal"           # Signal-adjusted DCA
    SWING = "swing"                      # Swing trading on signals
    MEAN_REVERSION = "mean_reversion"   # Buy dips, sell rips
    MOMENTUM = "momentum"                # Trend following
    GRID = "grid"                        # Grid trading
    REBALANCE = "rebalance"             # Portfolio rebalancing
    ARBITRAGE = "arbitrage"             # Cross-exchange arb


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Order:
    """Represents a trading order."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: Decimal = Decimal("0")
    filled_price: Optional[Decimal] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    exchange_order_id: Optional[str] = None
    fees: Decimal = Decimal("0")
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    side: PositionSide
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    opened_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def value(self) -> Decimal:
        return self.quantity * self.current_price
    
    @property
    def pnl_percent(self) -> Decimal:
        if self.entry_price == 0:
            return Decimal("0")
        return ((self.current_price - self.entry_price) / self.entry_price) * 100


@dataclass
class Trade:
    """Represents a completed trade."""
    id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fees: Decimal
    timestamp: datetime
    order_id: str
    pnl: Optional[Decimal] = None
    strategy: Optional[str] = None


@dataclass
class Portfolio:
    """Portfolio state."""
    cash_balance: Decimal
    positions: Dict[str, Position] = field(default_factory=dict)
    total_value: Decimal = Decimal("0")
    initial_value: Decimal = Decimal("0")
    
    @property
    def total_pnl(self) -> Decimal:
        return self.total_value - self.initial_value
    
    @property
    def total_pnl_percent(self) -> Decimal:
        if self.initial_value == 0:
            return Decimal("0")
        return (self.total_pnl / self.initial_value) * 100


@dataclass
class RiskLimits:
    """Risk management limits."""
    max_position_size_pct: Decimal = Decimal("0.10")     # Max 10% per position
    max_portfolio_risk_pct: Decimal = Decimal("0.02")    # Max 2% portfolio risk per trade
    max_daily_loss_pct: Decimal = Decimal("0.05")        # Max 5% daily loss
    max_drawdown_pct: Decimal = Decimal("0.20")          # Max 20% drawdown
    min_cash_reserve_pct: Decimal = Decimal("0.10")      # Keep 10% cash minimum
    max_open_positions: int = 10
    max_orders_per_hour: int = 20
    max_leverage: Decimal = Decimal("1.0")               # No leverage by default
    
    # Signal thresholds
    min_composite_score_buy: float = -20.0   # Only buy when score < -20
    max_composite_score_buy: float = 30.0    # Don't buy when score > 30
    min_composite_score_sell: float = 40.0   # Consider selling when score > 40


@dataclass
class TradingConfig:
    """Trading configuration."""
    mode: TradingMode = TradingMode.PAPER
    base_currency: str = "USD"
    supported_assets: List[str] = field(default_factory=lambda: ["BTC", "ETH"])
    risk_limits: RiskLimits = field(default_factory=RiskLimits)
    
    # DCA settings
    dca_base_amount: Decimal = Decimal("100")
    dca_frequency_hours: int = 24
    
    # Execution settings
    slippage_tolerance_pct: Decimal = Decimal("0.5")
    order_timeout_seconds: int = 300
    retry_attempts: int = 3
    
    # Notifications
    notify_on_trade: bool = True
    notify_on_error: bool = True


@dataclass
class SignalAction:
    """Action derived from signal analysis."""
    action: str                    # "buy", "sell", "hold", "rebalance"
    symbol: str
    suggested_quantity: Decimal
    suggested_price: Optional[Decimal]
    confidence: float
    reasoning: str
    signal_score: float
    urgency: str                   # "immediate", "soon", "patient"
    risk_level: str


# =============================================================================
# EXCHANGE INTERFACE
# =============================================================================

class ExchangeInterface(ABC):
    """Abstract base class for exchange integrations."""
    
    @abstractmethod
    async def get_balance(self, currency: str) -> Decimal:
        """Get balance for a currency."""
        pass
    
    @abstractmethod
    async def get_price(self, symbol: str) -> Decimal:
        """Get current price for a symbol."""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        """Place an order on the exchange."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Order:
        """Get order status."""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders."""
        pass


class PaperExchange(ExchangeInterface):
    """
    Simulated exchange for paper trading.
    Tracks balances and simulates order execution.
    """
    
    def __init__(self, initial_balances: Dict[str, Decimal] = None):
        self.balances: Dict[str, Decimal] = initial_balances or {
            "USD": Decimal("10000"),
            "BTC": Decimal("0"),
            "ETH": Decimal("0"),
        }
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        self._order_counter = 0
        self._prices: Dict[str, Decimal] = {}
        self._price_callbacks: List[Callable] = []
    
    def set_price(self, symbol: str, price: Decimal):
        """Set simulated price (would come from real feed)."""
        self._prices[symbol] = price
        # Check if any limit orders should fill
        asyncio.create_task(self._check_limit_orders())
    
    async def get_balance(self, currency: str) -> Decimal:
        return self.balances.get(currency, Decimal("0"))
    
    async def get_price(self, symbol: str) -> Decimal:
        if symbol in self._prices:
            return self._prices[symbol]
        # Fetch from CoinGecko or similar
        return Decimal("0")
    
    async def place_order(self, order: Order) -> Order:
        self._order_counter += 1
        order.id = f"PAPER-{self._order_counter:06d}"
        order.exchange_order_id = order.id
        order.status = OrderStatus.OPEN
        
        if order.order_type == OrderType.MARKET:
            # Execute immediately at current price
            price = await self.get_price(order.symbol)
            if price > 0:
                order = await self._execute_order(order, price)
        else:
            # Store for later execution
            self.orders[order.id] = order
        
        return order
    
    async def _execute_order(self, order: Order, price: Decimal) -> Order:
        """Execute an order at given price."""
        base, quote = order.symbol.split("/") if "/" in order.symbol else (order.symbol, "USD")
        
        total_cost = order.quantity * price
        fee = total_cost * Decimal("0.001")  # 0.1% fee
        
        if order.side == OrderSide.BUY:
            if self.balances.get(quote, Decimal("0")) < total_cost + fee:
                order.status = OrderStatus.REJECTED
                return order
            
            self.balances[quote] -= total_cost + fee
            self.balances[base] = self.balances.get(base, Decimal("0")) + order.quantity
        
        else:  # SELL
            if self.balances.get(base, Decimal("0")) < order.quantity:
                order.status = OrderStatus.REJECTED
                return order
            
            self.balances[base] -= order.quantity
            self.balances[quote] = self.balances.get(quote, Decimal("0")) + total_cost - fee
        
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = price
        order.fees = fee
        order.updated_at = datetime.utcnow()
        
        # Record trade
        trade = Trade(
            id=f"T-{order.id}",
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            fees=fee,
            timestamp=datetime.utcnow(),
            order_id=order.id,
        )
        self.trades.append(trade)
        
        logger.info(f"Paper trade executed: {order.side.value} {order.quantity} {order.symbol} @ {price}")
        
        return order
    
    async def _check_limit_orders(self):
        """Check if any limit orders should fill."""
        for order_id, order in list(self.orders.items()):
            if order.status != OrderStatus.OPEN:
                continue
            
            price = await self.get_price(order.symbol)
            
            should_fill = False
            if order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and price <= order.price:
                    should_fill = True
                elif order.side == OrderSide.SELL and price >= order.price:
                    should_fill = True
            
            elif order.order_type == OrderType.STOP_LOSS:
                if order.side == OrderSide.SELL and price <= order.stop_price:
                    should_fill = True
            
            if should_fill:
                await self._execute_order(order, price)
    
    async def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False
    
    async def get_order_status(self, order_id: str) -> Order:
        return self.orders.get(order_id)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        orders = [o for o in self.orders.values() if o.status == OrderStatus.OPEN]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders


# =============================================================================
# COINBASE EXCHANGE (EXAMPLE LIVE INTEGRATION)
# =============================================================================

class CoinbaseExchange(ExchangeInterface):
    """
    Coinbase Advanced Trade API integration.
    
    Requires API key with trading permissions.
    """
    
    BASE_URL = "https://api.coinbase.com/api/v3/brokerage"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self._session = None
    
    async def _get_session(self):
        if self._session is None:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session
    
    def _sign_request(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate signature for authenticated requests."""
        message = timestamp + method + path + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make authenticated request to Coinbase."""
        session = await self._get_session()
        
        timestamp = str(int(time.time()))
        path = f"/api/v3/brokerage{endpoint}"
        body = json.dumps(data) if data else ""
        
        signature = self._sign_request(timestamp, method, path, body)
        
        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
        }
        
        url = f"{self.BASE_URL}{endpoint}"
        
        async with session.request(method, url, headers=headers, data=body) as response:
            return await response.json()
    
    async def get_balance(self, currency: str) -> Decimal:
        """Get account balance for currency."""
        result = await self._request("GET", "/accounts")
        for account in result.get("accounts", []):
            if account["currency"] == currency:
                return Decimal(account["available_balance"]["value"])
        return Decimal("0")
    
    async def get_price(self, symbol: str) -> Decimal:
        """Get current price from order book."""
        product_id = symbol.replace("/", "-")
        result = await self._request("GET", f"/products/{product_id}/ticker")
        return Decimal(result.get("price", "0"))
    
    async def place_order(self, order: Order) -> Order:
        """Place order on Coinbase."""
        product_id = order.symbol.replace("/", "-")
        
        order_config = {
            "product_id": product_id,
            "side": order.side.value.upper(),
        }
        
        if order.order_type == OrderType.MARKET:
            if order.side == OrderSide.BUY:
                order_config["order_configuration"] = {
                    "market_market_ioc": {
                        "quote_size": str(order.quantity * (order.price or Decimal("1")))
                    }
                }
            else:
                order_config["order_configuration"] = {
                    "market_market_ioc": {
                        "base_size": str(order.quantity)
                    }
                }
        
        elif order.order_type == OrderType.LIMIT:
            order_config["order_configuration"] = {
                "limit_limit_gtc": {
                    "base_size": str(order.quantity),
                    "limit_price": str(order.price),
                }
            }
        
        result = await self._request("POST", "/orders", order_config)
        
        if result.get("success"):
            order.exchange_order_id = result["order_id"]
            order.status = OrderStatus.OPEN
        else:
            order.status = OrderStatus.REJECTED
            logger.error(f"Order rejected: {result}")
        
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on Coinbase."""
        result = await self._request("POST", "/orders/batch_cancel", {
            "order_ids": [order_id]
        })
        return result.get("success", False)
    
    async def get_order_status(self, order_id: str) -> Order:
        """Get order status from Coinbase."""
        result = await self._request("GET", f"/orders/historical/{order_id}")
        # Parse and return Order object
        # ... implementation details
        pass
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders."""
        params = {"order_status": "OPEN"}
        if symbol:
            params["product_id"] = symbol.replace("/", "-")
        result = await self._request("GET", "/orders/historical/batch", params)
        # Parse and return list of Order objects
        # ... implementation details
        return []
    
    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()


# =============================================================================
# TRADING STRATEGIES
# =============================================================================

class TradingStrategy(ABC):
    """Base class for trading strategies."""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.name = "base"
    
    @abstractmethod
    async def evaluate(
        self,
        signal_score: float,
        market_condition: str,
        cycle_phase: str,
        portfolio: Portfolio,
        current_prices: Dict[str, Decimal]
    ) -> List[SignalAction]:
        """Evaluate signals and return suggested actions."""
        pass


class DCASignalStrategy(TradingStrategy):
    """
    Signal-adjusted DCA strategy.
    
    Adjusts regular DCA amounts based on composite signal score.
    This is the core strategy from the signal system.
    """
    
    def __init__(self, config: TradingConfig):
        super().__init__(config)
        self.name = "dca_signal"
        self.last_dca_time: Dict[str, datetime] = {}
    
    async def evaluate(
        self,
        signal_score: float,
        market_condition: str,
        cycle_phase: str,
        portfolio: Portfolio,
        current_prices: Dict[str, Decimal]
    ) -> List[SignalAction]:
        actions = []
        
        for asset in self.config.supported_assets:
            # Check if it's time for DCA
            last_time = self.last_dca_time.get(asset, datetime.min)
            hours_since = (datetime.utcnow() - last_time).total_seconds() / 3600
            
            if hours_since < self.config.dca_frequency_hours:
                continue
            
            # Calculate DCA multiplier based on signal score
            if signal_score <= -60:
                multiplier = Decimal("3.0")
                buffer_pct = Decimal("0.75")
            elif signal_score <= -40:
                multiplier = Decimal("2.5")
                buffer_pct = Decimal("0.50")
            elif signal_score <= -20:
                multiplier = Decimal("2.0")
                buffer_pct = Decimal("0.35")
            elif signal_score <= 0:
                multiplier = Decimal("1.5")
                buffer_pct = Decimal("0.20")
            elif signal_score <= 20:
                multiplier = Decimal("1.0")
                buffer_pct = Decimal("0.0")
            elif signal_score <= 40:
                multiplier = Decimal("0.75")
                buffer_pct = Decimal("0.0")
            elif signal_score <= 60:
                multiplier = Decimal("0.5")
                buffer_pct = Decimal("0.0")
            else:
                multiplier = Decimal("0.25")
                buffer_pct = Decimal("0.0")
            
            # Calculate amount
            base_amount = self.config.dca_base_amount
            adjusted_amount = base_amount * multiplier
            
            # Check risk limits
            if signal_score > self.config.risk_limits.max_composite_score_buy:
                actions.append(SignalAction(
                    action="hold",
                    symbol=f"{asset}/USD",
                    suggested_quantity=Decimal("0"),
                    suggested_price=current_prices.get(asset),
                    confidence=0.8,
                    reasoning=f"Signal score {signal_score:.1f} > {self.config.risk_limits.max_composite_score_buy} - too risky to buy",
                    signal_score=signal_score,
                    urgency="patient",
                    risk_level="high",
                ))
                continue
            
            # Calculate quantity
            price = current_prices.get(asset, Decimal("0"))
            if price > 0:
                quantity = (adjusted_amount / price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
                
                actions.append(SignalAction(
                    action="buy",
                    symbol=f"{asset}/USD",
                    suggested_quantity=quantity,
                    suggested_price=price,
                    confidence=min(0.9, 0.5 + abs(signal_score) / 100),
                    reasoning=f"DCA {multiplier}x at score {signal_score:.1f} ({market_condition})",
                    signal_score=signal_score,
                    urgency="immediate" if signal_score < -40 else "soon",
                    risk_level="low" if signal_score < 0 else "medium",
                ))
        
        return actions


class SwingStrategy(TradingStrategy):
    """
    Swing trading strategy.
    
    Buys on strong fear signals, sells on strong greed signals.
    Uses larger position sizes than DCA.
    """
    
    def __init__(self, config: TradingConfig):
        super().__init__(config)
        self.name = "swing"
    
    async def evaluate(
        self,
        signal_score: float,
        market_condition: str,
        cycle_phase: str,
        portfolio: Portfolio,
        current_prices: Dict[str, Decimal]
    ) -> List[SignalAction]:
        actions = []
        
        for asset in self.config.supported_assets:
            symbol = f"{asset}/USD"
            price = current_prices.get(asset, Decimal("0"))
            position = portfolio.positions.get(symbol)
            
            # Strong buy signal
            if signal_score < -50 and cycle_phase in ["accumulation", "capitulation"]:
                # Size based on signal strength and risk limits
                max_position = portfolio.total_value * self.config.risk_limits.max_position_size_pct
                current_position_value = position.value if position else Decimal("0")
                available_to_buy = max_position - current_position_value
                
                if available_to_buy > 0 and price > 0:
                    quantity = (available_to_buy * Decimal("0.5") / price).quantize(
                        Decimal("0.00000001"), rounding=ROUND_DOWN
                    )
                    
                    actions.append(SignalAction(
                        action="buy",
                        symbol=symbol,
                        suggested_quantity=quantity,
                        suggested_price=price,
                        confidence=min(0.85, 0.6 + abs(signal_score) / 200),
                        reasoning=f"Swing buy: {cycle_phase} phase with score {signal_score:.1f}",
                        signal_score=signal_score,
                        urgency="immediate",
                        risk_level="medium",
                    ))
            
            # Strong sell signal
            elif signal_score > 50 and position and position.quantity > 0:
                # Sell portion based on greed level
                sell_pct = min(Decimal("0.5"), Decimal(str((signal_score - 50) / 100)))
                quantity = (position.quantity * sell_pct).quantize(
                    Decimal("0.00000001"), rounding=ROUND_DOWN
                )
                
                if quantity > 0:
                    actions.append(SignalAction(
                        action="sell",
                        symbol=symbol,
                        suggested_quantity=quantity,
                        suggested_price=price,
                        confidence=min(0.8, 0.5 + signal_score / 200),
                        reasoning=f"Swing sell: Taking profits at score {signal_score:.1f}",
                        signal_score=signal_score,
                        urgency="soon",
                        risk_level="low",
                    ))
        
        return actions


class MeanReversionStrategy(TradingStrategy):
    """
    Mean reversion strategy.
    
    Buys when price is significantly below moving average,
    sells when significantly above. Uses technical signals heavily.
    """
    
    def __init__(self, config: TradingConfig):
        super().__init__(config)
        self.name = "mean_reversion"
        self.price_history: Dict[str, List[Decimal]] = {}
    
    async def evaluate(
        self,
        signal_score: float,
        market_condition: str,
        cycle_phase: str,
        portfolio: Portfolio,
        current_prices: Dict[str, Decimal]
    ) -> List[SignalAction]:
        actions = []
        
        for asset in self.config.supported_assets:
            symbol = f"{asset}/USD"
            price = current_prices.get(asset, Decimal("0"))
            
            # Track price history
            if asset not in self.price_history:
                self.price_history[asset] = []
            self.price_history[asset].append(price)
            
            # Keep last 200 prices
            if len(self.price_history[asset]) > 200:
                self.price_history[asset] = self.price_history[asset][-200:]
            
            if len(self.price_history[asset]) < 20:
                continue
            
            # Calculate mean
            prices = self.price_history[asset]
            sma_20 = sum(prices[-20:]) / 20
            
            # Calculate deviation
            deviation_pct = ((price - sma_20) / sma_20) * 100
            
            position = portfolio.positions.get(symbol)
            
            # Buy when significantly below mean
            if deviation_pct < -10 and signal_score < 20:
                max_position = portfolio.total_value * self.config.risk_limits.max_position_size_pct
                current_value = position.value if position else Decimal("0")
                
                if current_value < max_position and price > 0:
                    buy_amount = (max_position - current_value) * Decimal("0.3")
                    quantity = (buy_amount / price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
                    
                    actions.append(SignalAction(
                        action="buy",
                        symbol=symbol,
                        suggested_quantity=quantity,
                        suggested_price=price,
                        confidence=0.7,
                        reasoning=f"Mean reversion buy: {deviation_pct:.1f}% below 20-SMA",
                        signal_score=signal_score,
                        urgency="soon",
                        risk_level="medium",
                    ))
            
            # Sell when significantly above mean
            elif deviation_pct > 15 and position and position.quantity > 0:
                sell_pct = min(Decimal("0.4"), Decimal(str(deviation_pct / 50)))
                quantity = (position.quantity * sell_pct).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
                
                if quantity > 0:
                    actions.append(SignalAction(
                        action="sell",
                        symbol=symbol,
                        suggested_quantity=quantity,
                        suggested_price=price,
                        confidence=0.65,
                        reasoning=f"Mean reversion sell: {deviation_pct:.1f}% above 20-SMA",
                        signal_score=signal_score,
                        urgency="patient",
                        risk_level="low",
                    ))
        
        return actions


class GridStrategy(TradingStrategy):
    """
    Grid trading strategy.
    
    Places buy orders at regular intervals below current price,
    and sell orders above. Profits from volatility.
    """
    
    def __init__(self, config: TradingConfig, grid_levels: int = 10, grid_spacing_pct: Decimal = Decimal("2")):
        super().__init__(config)
        self.name = "grid"
        self.grid_levels = grid_levels
        self.grid_spacing_pct = grid_spacing_pct
        self.active_grids: Dict[str, List[Decimal]] = {}
    
    async def evaluate(
        self,
        signal_score: float,
        market_condition: str,
        cycle_phase: str,
        portfolio: Portfolio,
        current_prices: Dict[str, Decimal]
    ) -> List[SignalAction]:
        actions = []
        
        for asset in self.config.supported_assets:
            symbol = f"{asset}/USD"
            price = current_prices.get(asset, Decimal("0"))
            
            if price == 0:
                continue
            
            # Only run grid in neutral/accumulation phases
            if cycle_phase not in ["neutral", "accumulation", "bull_market"]:
                continue
            
            # Calculate grid levels
            amount_per_level = self.config.dca_base_amount / self.grid_levels
            
            # Generate buy grid (below current price)
            for i in range(1, self.grid_levels + 1):
                grid_price = price * (1 - self.grid_spacing_pct / 100 * i)
                quantity = (amount_per_level / grid_price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
                
                actions.append(SignalAction(
                    action="limit_buy",
                    symbol=symbol,
                    suggested_quantity=quantity,
                    suggested_price=grid_price,
                    confidence=0.6,
                    reasoning=f"Grid buy level {i} at {grid_price:.2f}",
                    signal_score=signal_score,
                    urgency="patient",
                    risk_level="low",
                ))
            
            # Generate sell grid for existing positions
            position = portfolio.positions.get(symbol)
            if position and position.quantity > 0:
                sell_per_level = position.quantity / self.grid_levels
                
                for i in range(1, self.grid_levels + 1):
                    grid_price = price * (1 + self.grid_spacing_pct / 100 * i)
                    
                    actions.append(SignalAction(
                        action="limit_sell",
                        symbol=symbol,
                        suggested_quantity=sell_per_level,
                        suggested_price=grid_price,
                        confidence=0.6,
                        reasoning=f"Grid sell level {i} at {grid_price:.2f}",
                        signal_score=signal_score,
                        urgency="patient",
                        risk_level="low",
                    ))
        
        return actions


class RebalanceStrategy(TradingStrategy):
    """
    Portfolio rebalancing strategy.
    
    Maintains target allocations across assets.
    """
    
    def __init__(self, config: TradingConfig, target_allocations: Dict[str, Decimal] = None):
        super().__init__(config)
        self.name = "rebalance"
        self.target_allocations = target_allocations or {
            "BTC": Decimal("0.60"),
            "ETH": Decimal("0.30"),
            "USD": Decimal("0.10"),
        }
        self.rebalance_threshold = Decimal("0.05")  # Rebalance if 5% off target
    
    async def evaluate(
        self,
        signal_score: float,
        market_condition: str,
        cycle_phase: str,
        portfolio: Portfolio,
        current_prices: Dict[str, Decimal]
    ) -> List[SignalAction]:
        actions = []
        
        if portfolio.total_value == 0:
            return actions
        
        # Calculate current allocations
        current_allocations = {"USD": portfolio.cash_balance / portfolio.total_value}
        
        for symbol, position in portfolio.positions.items():
            asset = symbol.split("/")[0]
            current_allocations[asset] = position.value / portfolio.total_value
        
        # Check each target
        for asset, target in self.target_allocations.items():
            current = current_allocations.get(asset, Decimal("0"))
            diff = current - target
            
            if abs(diff) < self.rebalance_threshold:
                continue
            
            # Calculate rebalance amount
            rebalance_value = abs(diff) * portfolio.total_value
            
            if asset == "USD":
                continue  # Don't trade USD directly
            
            symbol = f"{asset}/USD"
            price = current_prices.get(asset, Decimal("0"))
            
            if price == 0:
                continue
            
            quantity = (rebalance_value / price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
            
            if diff > 0:
                # Over-allocated, sell
                actions.append(SignalAction(
                    action="sell",
                    symbol=symbol,
                    suggested_quantity=quantity,
                    suggested_price=price,
                    confidence=0.75,
                    reasoning=f"Rebalance: {asset} at {current:.1%} vs target {target:.1%}",
                    signal_score=signal_score,
                    urgency="patient",
                    risk_level="low",
                ))
            else:
                # Under-allocated, buy
                actions.append(SignalAction(
                    action="buy",
                    symbol=symbol,
                    suggested_quantity=quantity,
                    suggested_price=price,
                    confidence=0.75,
                    reasoning=f"Rebalance: {asset} at {current:.1%} vs target {target:.1%}",
                    signal_score=signal_score,
                    urgency="patient",
                    risk_level="low",
                ))
        
        return actions


# =============================================================================
# RISK MANAGER
# =============================================================================

class RiskManager:
    """
    Risk management and position sizing.
    
    Enforces risk limits and validates orders before execution.
    """
    
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.daily_pnl = Decimal("0")
        self.daily_orders = 0
        self.last_reset = datetime.utcnow().date()
        self.peak_value = Decimal("0")
    
    def reset_daily(self):
        """Reset daily counters."""
        today = datetime.utcnow().date()
        if today > self.last_reset:
            self.daily_pnl = Decimal("0")
            self.daily_orders = 0
            self.last_reset = today
    
    def validate_order(
        self,
        order: Order,
        portfolio: Portfolio,
        current_price: Decimal
    ) -> tuple[bool, str]:
        """
        Validate an order against risk limits.
        Returns (is_valid, reason).
        """
        self.reset_daily()
        
        # Check order rate limit
        if self.daily_orders >= self.limits.max_orders_per_hour * 24:
            return False, "Daily order limit reached"
        
        # Check daily loss limit
        daily_loss_limit = portfolio.initial_value * self.limits.max_daily_loss_pct
        if self.daily_pnl < -daily_loss_limit:
            return False, f"Daily loss limit reached ({self.daily_pnl})"
        
        # Check drawdown
        if self.peak_value > 0:
            current_drawdown = (self.peak_value - portfolio.total_value) / self.peak_value
            if current_drawdown > self.limits.max_drawdown_pct:
                return False, f"Max drawdown reached ({current_drawdown:.1%})"
        
        # Check position limits
        if order.side == OrderSide.BUY:
            # Check max positions
            if len(portfolio.positions) >= self.limits.max_open_positions:
                return False, "Max open positions reached"
            
            # Check position size
            order_value = order.quantity * current_price
            max_position = portfolio.total_value * self.limits.max_position_size_pct
            
            existing_position = portfolio.positions.get(order.symbol)
            current_position_value = existing_position.value if existing_position else Decimal("0")
            
            if current_position_value + order_value > max_position:
                return False, f"Position size limit exceeded ({order_value} + {current_position_value} > {max_position})"
            
            # Check cash reserve
            min_cash = portfolio.total_value * self.limits.min_cash_reserve_pct
            if portfolio.cash_balance - order_value < min_cash:
                return False, f"Would violate minimum cash reserve ({min_cash})"
        
        return True, "OK"
    
    def calculate_position_size(
        self,
        portfolio: Portfolio,
        entry_price: Decimal,
        stop_loss_price: Decimal,
        risk_per_trade_pct: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate position size based on risk.
        
        Uses the risk per trade to determine quantity where
        hitting stop loss = losing X% of portfolio.
        """
        risk_pct = risk_per_trade_pct or self.limits.max_portfolio_risk_pct
        risk_amount = portfolio.total_value * risk_pct
        
        price_risk = abs(entry_price - stop_loss_price)
        if price_risk == 0:
            return Decimal("0")
        
        quantity = risk_amount / price_risk
        
        # Cap at max position size
        max_quantity = (portfolio.total_value * self.limits.max_position_size_pct) / entry_price
        
        return min(quantity, max_quantity).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
    
    def update_tracking(self, trade: Trade, portfolio: Portfolio):
        """Update risk tracking after a trade."""
        self.daily_orders += 1
        
        if trade.pnl:
            self.daily_pnl += trade.pnl
        
        if portfolio.total_value > self.peak_value:
            self.peak_value = portfolio.total_value


# =============================================================================
# TRADING AGENT
# =============================================================================

class TradingAgent:
    """
    Main trading agent that orchestrates everything.
    
    Combines signal analysis, strategies, risk management,
    and execution into a cohesive trading system.
    """
    
    def __init__(
        self,
        config: TradingConfig,
        exchange: ExchangeInterface,
        strategies: List[TradingStrategy] = None
    ):
        self.config = config
        self.exchange = exchange
        self.risk_manager = RiskManager(config.risk_limits)
        
        # Initialize strategies
        self.strategies = strategies or [
            DCASignalStrategy(config),
            SwingStrategy(config),
        ]
        
        # Portfolio tracking
        self.portfolio = Portfolio(
            cash_balance=Decimal("0"),
            positions={},
            initial_value=Decimal("0"),
        )
        
        # Trade history
        self.trades: List[Trade] = []
        self.pending_orders: Dict[str, Order] = {}
        
        # State
        self.is_running = False
        self._signal_analyzer = None
    
    async def initialize(self):
        """Initialize the agent."""
        # Import signal analyzer
        from .unified_analyzer import UnifiedSignalAnalyzer
        self._signal_analyzer = UnifiedSignalAnalyzer()
        
        # Fetch initial balances
        await self._update_portfolio()
        
        self.portfolio.initial_value = self.portfolio.total_value
        self.risk_manager.peak_value = self.portfolio.total_value
        
        logger.info(f"Trading agent initialized with ${self.portfolio.total_value} portfolio")
    
    async def _update_portfolio(self):
        """Update portfolio state from exchange."""
        # Get cash balance
        self.portfolio.cash_balance = await self.exchange.get_balance(
            self.config.base_currency
        )
        
        # Get prices and update positions
        for asset in self.config.supported_assets:
            price = await self.exchange.get_price(asset)
            balance = await self.exchange.get_balance(asset)
            
            symbol = f"{asset}/{self.config.base_currency}"
            
            if balance > 0:
                if symbol in self.portfolio.positions:
                    self.portfolio.positions[symbol].quantity = balance
                    self.portfolio.positions[symbol].current_price = price
                    self.portfolio.positions[symbol].unrealized_pnl = (
                        (price - self.portfolio.positions[symbol].entry_price) * balance
                    )
                else:
                    self.portfolio.positions[symbol] = Position(
                        symbol=symbol,
                        side=PositionSide.LONG,
                        quantity=balance,
                        entry_price=price,  # Assume entry at current price for new tracking
                        current_price=price,
                    )
            elif symbol in self.portfolio.positions:
                del self.portfolio.positions[symbol]
        
        # Calculate total value
        self.portfolio.total_value = self.portfolio.cash_balance
        for position in self.portfolio.positions.values():
            self.portfolio.total_value += position.value
    
    async def run_cycle(self) -> List[Trade]:
        """
        Run one trading cycle.
        
        1. Get signal analysis
        2. Get strategy recommendations
        3. Validate against risk limits
        4. Execute approved orders
        
        Returns list of executed trades.
        """
        executed_trades = []
        
        # Update portfolio
        await self._update_portfolio()
        
        # Get signal analysis
        analysis = await self._signal_analyzer.analyze("BTC")
        
        signal_score = analysis.composite_score
        market_condition = analysis.market_condition.value
        cycle_phase = analysis.cycle_phase.value
        
        logger.info(f"Signal score: {signal_score:.1f}, Condition: {market_condition}, Phase: {cycle_phase}")
        
        # Get current prices
        current_prices = {}
        for asset in self.config.supported_assets:
            current_prices[asset] = await self.exchange.get_price(asset)
        
        # Get actions from all strategies
        all_actions: List[SignalAction] = []
        for strategy in self.strategies:
            actions = await strategy.evaluate(
                signal_score=signal_score,
                market_condition=market_condition,
                cycle_phase=cycle_phase,
                portfolio=self.portfolio,
                current_prices=current_prices,
            )
            all_actions.extend(actions)
        
        # Process actions
        for action in all_actions:
            if action.action == "hold":
                logger.info(f"Holding {action.symbol}: {action.reasoning}")
                continue
            
            # Create order
            order = Order(
                id="",
                symbol=action.symbol,
                side=OrderSide.BUY if "buy" in action.action else OrderSide.SELL,
                order_type=OrderType.LIMIT if "limit" in action.action else OrderType.MARKET,
                quantity=action.suggested_quantity,
                price=action.suggested_price,
                metadata={
                    "strategy": action.reasoning,
                    "signal_score": action.signal_score,
                    "confidence": action.confidence,
                }
            )
            
            # Validate against risk limits
            is_valid, reason = self.risk_manager.validate_order(
                order, self.portfolio, action.suggested_price
            )
            
            if not is_valid:
                logger.warning(f"Order rejected by risk manager: {reason}")
                continue
            
            # Execute order
            try:
                executed_order = await self.exchange.place_order(order)
                
                if executed_order.status == OrderStatus.FILLED:
                    trade = Trade(
                        id=f"T-{executed_order.id}",
                        symbol=executed_order.symbol,
                        side=executed_order.side,
                        quantity=executed_order.filled_quantity,
                        price=executed_order.filled_price,
                        fees=executed_order.fees,
                        timestamp=datetime.utcnow(),
                        order_id=executed_order.id,
                        strategy=action.reasoning,
                    )
                    
                    self.trades.append(trade)
                    executed_trades.append(trade)
                    self.risk_manager.update_tracking(trade, self.portfolio)
                    
                    logger.info(f"Trade executed: {trade.side.value} {trade.quantity} {trade.symbol} @ {trade.price}")
                
                elif executed_order.status == OrderStatus.OPEN:
                    self.pending_orders[executed_order.id] = executed_order
                    logger.info(f"Limit order placed: {executed_order.id}")
                
                else:
                    logger.warning(f"Order failed: {executed_order.status}")
            
            except Exception as e:
                logger.error(f"Order execution failed: {e}")
        
        return executed_trades
    
    async def run_continuous(self, interval_seconds: int = 3600):
        """Run continuous trading loop."""
        self.is_running = True
        
        while self.is_running:
            try:
                trades = await self.run_cycle()
                
                if trades:
                    logger.info(f"Cycle complete: {len(trades)} trades executed")
                else:
                    logger.info("Cycle complete: no trades")
                
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop the trading loop."""
        self.is_running = False
    
    async def close(self):
        """Clean up resources."""
        if self._signal_analyzer:
            await self._signal_analyzer.close()
        if hasattr(self.exchange, 'close'):
            await self.exchange.close()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "mode": self.config.mode.value,
            "is_running": self.is_running,
            "portfolio": {
                "cash": str(self.portfolio.cash_balance),
                "total_value": str(self.portfolio.total_value),
                "pnl": str(self.portfolio.total_pnl),
                "pnl_pct": str(self.portfolio.total_pnl_percent),
                "positions": {
                    symbol: {
                        "quantity": str(pos.quantity),
                        "entry_price": str(pos.entry_price),
                        "current_price": str(pos.current_price),
                        "unrealized_pnl": str(pos.unrealized_pnl),
                    }
                    for symbol, pos in self.portfolio.positions.items()
                }
            },
            "risk": {
                "daily_pnl": str(self.risk_manager.daily_pnl),
                "daily_orders": self.risk_manager.daily_orders,
                "peak_value": str(self.risk_manager.peak_value),
            },
            "trades_today": len([t for t in self.trades if t.timestamp.date() == datetime.utcnow().date()]),
            "total_trades": len(self.trades),
            "strategies": [s.name for s in self.strategies],
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_paper_agent(
    initial_cash: Decimal = Decimal("10000"),
    assets: List[str] = None,
    strategies: List[str] = None
) -> TradingAgent:
    """Create a paper trading agent for testing."""
    
    config = TradingConfig(
        mode=TradingMode.PAPER,
        supported_assets=assets or ["BTC", "ETH"],
        dca_base_amount=Decimal("100"),
    )
    
    exchange = PaperExchange(initial_balances={
        "USD": initial_cash,
        "BTC": Decimal("0"),
        "ETH": Decimal("0"),
    })
    
    # Initialize strategies
    strategy_map = {
        "dca": DCASignalStrategy(config),
        "swing": SwingStrategy(config),
        "mean_reversion": MeanReversionStrategy(config),
        "grid": GridStrategy(config),
        "rebalance": RebalanceStrategy(config),
    }
    
    strategy_list = []
    for name in (strategies or ["dca"]):
        if name in strategy_map:
            strategy_list.append(strategy_map[name])
    
    return TradingAgent(config, exchange, strategy_list)


async def run_paper_backtest(
    agent: TradingAgent,
    price_history: Dict[str, List[tuple[datetime, Decimal]]],
    interval_hours: int = 24
) -> Dict[str, Any]:
    """
    Run a simple backtest with historical prices.
    
    price_history format: {"BTC": [(datetime, price), ...]}
    """
    await agent.initialize()
    
    results = {
        "trades": [],
        "portfolio_history": [],
        "final_value": Decimal("0"),
        "total_return": Decimal("0"),
    }
    
    # Get all timestamps
    all_times = set()
    for prices in price_history.values():
        for dt, _ in prices:
            all_times.add(dt)
    
    sorted_times = sorted(all_times)
    
    for i, timestamp in enumerate(sorted_times):
        # Update prices in paper exchange
        for asset, prices in price_history.items():
            price_at_time = next(
                (p for dt, p in prices if dt == timestamp),
                None
            )
            if price_at_time:
                agent.exchange.set_price(asset, price_at_time)
        
        # Run cycle at intervals
        if i % interval_hours == 0:
            trades = await agent.run_cycle()
            results["trades"].extend(trades)
        
        # Record portfolio value
        await agent._update_portfolio()
        results["portfolio_history"].append({
            "timestamp": timestamp,
            "value": agent.portfolio.total_value,
        })
    
    results["final_value"] = agent.portfolio.total_value
    results["total_return"] = agent.portfolio.total_pnl_percent
    
    await agent.close()
    
    return results
