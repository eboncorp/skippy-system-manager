"""
Mock Exchange Client
====================

A realistic mock exchange implementation for testing and development.
Simulates order matching, price movements, staking, and more.
"""

import asyncio
import hashlib
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional

from . import (
    Balance,
    BaseExchangeClient,
    OHLCV,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    StakingPosition,
    Ticker,
    TimeInForce,
    Transaction,
    TransactionType,
    # Exceptions
    AssetNotFoundError,
    AuthenticationError,
    InsufficientFundsError,
    InvalidOrderError,
    OrderNotFoundError,
    RateLimitError,
    StakingError,
)


# =============================================================================
# CONFIGURATION
# =============================================================================


# Default starting balances for mock accounts
DEFAULT_BALANCES = {
    "BTC": Decimal("1.5"),
    "ETH": Decimal("15.0"),
    "SOL": Decimal("150.0"),
    "USDC": Decimal("10000.0"),
    "USD": Decimal("5000.0"),
}

# Base prices for assets (USD)
BASE_PRICES = {
    "BTC": Decimal("45000"),
    "ETH": Decimal("2750"),
    "SOL": Decimal("120"),
    "USDC": Decimal("1.0"),
    "ATOM": Decimal("9.50"),
    "DOT": Decimal("7.25"),
    "ADA": Decimal("0.55"),
    "AVAX": Decimal("35.00"),
    "MATIC": Decimal("0.85"),
    "LINK": Decimal("15.00"),
}

# Staking APY rates by asset
STAKING_RATES = {
    "ETH": Decimal("4.2"),
    "SOL": Decimal("7.1"),
    "ATOM": Decimal("15.2"),
    "DOT": Decimal("12.0"),
    "ADA": Decimal("3.5"),
    "AVAX": Decimal("8.5"),
    "MATIC": Decimal("4.8"),
}

# Trading fee rate (0.1%)
TRADING_FEE_RATE = Decimal("0.001")


# =============================================================================
# MOCK EXCHANGE CLIENT
# =============================================================================


class MockExchangeClient(BaseExchangeClient):
    """
    Mock exchange client for testing and development.
    
    Features:
    - Simulated balances and order execution
    - Realistic price movements
    - Staking with reward accumulation
    - Configurable failure modes for testing
    - State persistence within session
    
    Usage:
        client = MockExchangeClient("mock_coinbase")
        await client.authenticate()
        balances = await client.get_balances()
    """
    
    def __init__(
        self,
        exchange_name: str = "mock_exchange",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        initial_balances: Optional[Dict[str, Decimal]] = None,
        price_volatility: float = 0.02,  # 2% max price movement
        simulated_latency_ms: int = 50,  # Simulated network latency
        failure_rate: float = 0.0,  # Probability of random failures
        rate_limit_requests: int = 100,  # Requests per minute
    ):
        super().__init__(api_key, api_secret)
        
        self._exchange_name = exchange_name
        self._price_volatility = price_volatility
        self._simulated_latency_ms = simulated_latency_ms
        self._failure_rate = failure_rate
        self._rate_limit_requests = rate_limit_requests
        
        # State
        self._balances: Dict[str, Balance] = {}
        self._orders: Dict[str, Order] = {}
        self._transactions: List[Transaction] = []
        self._staking_positions: Dict[str, StakingPosition] = {}
        self._current_prices: Dict[str, Decimal] = dict(BASE_PRICES)
        
        # Rate limiting
        self._request_timestamps: List[datetime] = []
        
        # Initialize balances
        initial = initial_balances or DEFAULT_BALANCES
        for asset, amount in initial.items():
            self._balances[asset] = Balance(asset=asset, available=amount)
        
        # Price update task
        self._price_update_task: Optional[asyncio.Task] = None
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def name(self) -> str:
        return self._exchange_name
    
    @property
    def supported_assets(self) -> List[str]:
        return list(BASE_PRICES.keys())
    
    @property
    def trading_pairs(self) -> List[str]:
        pairs = []
        for asset in self.supported_assets:
            if asset not in ["USD", "USDC"]:
                pairs.append(f"{asset}-USD")
                pairs.append(f"{asset}-USDC")
        return pairs
    
    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    
    async def _simulate_latency(self):
        """Simulate network latency."""
        if self._simulated_latency_ms > 0:
            # Add some randomness to latency
            latency = self._simulated_latency_ms * (0.5 + random.random())
            await asyncio.sleep(latency / 1000)
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Remove old timestamps
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > minute_ago
        ]
        
        if len(self._request_timestamps) >= self._rate_limit_requests:
            raise RateLimitError(
                f"Rate limit exceeded: {self._rate_limit_requests} requests/minute"
            )
        
        self._request_timestamps.append(now)
    
    def _maybe_fail(self):
        """Randomly fail based on configured failure rate."""
        if self._failure_rate > 0 and random.random() < self._failure_rate:
            errors = [
                ("Network timeout", TimeoutError),
                ("Connection refused", ConnectionError),
                ("Internal server error", Exception),
            ]
            msg, exc_type = random.choice(errors)
            raise exc_type(f"Simulated failure: {msg}")
    
    def _generate_id(self, prefix: str = "ord") -> str:
        """Generate a unique ID."""
        return f"{prefix}_{uuid.uuid4().hex[:12]}"
    
    def _get_price(self, asset: str) -> Decimal:
        """Get current price for an asset."""
        if asset in ["USD", "USDC", "USDT"]:
            return Decimal("1.0")
        return self._current_prices.get(asset, Decimal("0"))
    
    def _update_prices(self):
        """Simulate price movements."""
        for asset in self._current_prices:
            if asset in ["USDC", "USDT"]:
                continue
            
            # Random walk with mean reversion
            base = BASE_PRICES.get(asset, self._current_prices[asset])
            current = self._current_prices[asset]
            
            # Calculate change
            volatility = self._price_volatility
            change = Decimal(str(random.gauss(0, volatility)))
            
            # Mean reversion factor
            reversion = (base - current) / base * Decimal("0.1")
            
            # Apply change
            new_price = current * (1 + change + reversion)
            
            # Ensure price stays positive and within reasonable bounds
            min_price = base * Decimal("0.5")
            max_price = base * Decimal("2.0")
            new_price = max(min_price, min(max_price, new_price))
            
            self._current_prices[asset] = new_price.quantize(Decimal("0.01"))
    
    def _execute_order(self, order: Order) -> Order:
        """Execute an order (market orders only for now)."""
        base, quote = self.parse_symbol(order.symbol)
        price = self._get_price(base)
        
        if order.order_type == OrderType.MARKET:
            # Market order - execute immediately at current price
            order.average_fill_price = price
            order.filled_amount = order.amount
            order.status = OrderStatus.FILLED
            
            # Calculate fees
            order.fees = order.amount * price * TRADING_FEE_RATE
            order.fee_asset = quote
            
            # Update balances
            if order.side == OrderSide.BUY:
                cost = order.amount * price + order.fees
                self._balances[quote].available -= cost
                
                if base not in self._balances:
                    self._balances[base] = Balance(asset=base, available=Decimal("0"))
                self._balances[base].available += order.amount
            else:  # SELL
                self._balances[base].available -= order.amount
                proceeds = order.amount * price - order.fees
                
                if quote not in self._balances:
                    self._balances[quote] = Balance(asset=quote, available=Decimal("0"))
                self._balances[quote].available += proceeds
            
            # Record transaction
            self._transactions.append(Transaction(
                id=self._generate_id("tx"),
                tx_type=TransactionType.BUY if order.side == OrderSide.BUY else TransactionType.SELL,
                asset=base,
                amount=order.amount,
                timestamp=datetime.utcnow(),
                price_usd=price,
                fee=order.fees,
                fee_asset=order.fee_asset,
                order_id=order.id
            ))
        
        elif order.order_type == OrderType.LIMIT:
            # Limit order - check if price matches
            if order.side == OrderSide.BUY and price <= order.price:
                order.average_fill_price = order.price
                order.filled_amount = order.amount
                order.status = OrderStatus.FILLED
                # ... similar balance updates
            elif order.side == OrderSide.SELL and price >= order.price:
                order.average_fill_price = order.price
                order.filled_amount = order.amount
                order.status = OrderStatus.FILLED
                # ... similar balance updates
            else:
                order.status = OrderStatus.OPEN
        
        order.updated_at = datetime.utcnow()
        return order
    
    # -------------------------------------------------------------------------
    # Authentication
    # -------------------------------------------------------------------------
    
    async def authenticate(self) -> bool:
        await self._simulate_latency()
        self._maybe_fail()
        
        # Mock authentication - accept any non-empty credentials
        if self.api_key and self.api_secret:
            self._authenticated = True
            return True
        
        # For testing, also accept no credentials
        self._authenticated = True
        return True
    
    # -------------------------------------------------------------------------
    # Account Information
    # -------------------------------------------------------------------------
    
    async def get_balances(self) -> List[Balance]:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        return [b for b in self._balances.values() if b.total > 0]
    
    async def get_balance(self, asset: str) -> Balance:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        asset = asset.upper()
        if asset not in self._balances:
            return Balance(asset=asset, available=Decimal("0"))
        return self._balances[asset]
    
    # -------------------------------------------------------------------------
    # Market Data
    # -------------------------------------------------------------------------
    
    async def get_ticker(self, symbol: str) -> Ticker:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        base, quote = self.parse_symbol(symbol)
        price = self._get_price(base)
        
        # Simulate bid/ask spread (0.1%)
        spread = price * Decimal("0.001")
        bid = price - spread / 2
        ask = price + spread / 2
        
        # Generate realistic 24h data
        change_24h = Decimal(str(random.gauss(0, 3)))  # ~3% daily volatility
        high_24h = price * (1 + abs(change_24h) / 100 + Decimal("0.02"))
        low_24h = price * (1 - abs(change_24h) / 100 - Decimal("0.02"))
        volume_24h = price * Decimal(str(random.uniform(1000, 10000)))
        
        return Ticker(
            symbol=symbol,
            bid=bid.quantize(Decimal("0.01")),
            ask=ask.quantize(Decimal("0.01")),
            last=price,
            volume_24h=volume_24h.quantize(Decimal("0.01")),
            change_24h=change_24h.quantize(Decimal("0.01")),
            high_24h=high_24h.quantize(Decimal("0.01")),
            low_24h=low_24h.quantize(Decimal("0.01"))
        )
    
    async def get_tickers(self, symbols: Optional[List[str]] = None) -> List[Ticker]:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        if symbols is None:
            symbols = self.trading_pairs
        
        tickers = []
        for symbol in symbols:
            try:
                ticker = await self.get_ticker(symbol)
                tickers.append(ticker)
            except Exception:
                continue
        
        return tickers
    
    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[OHLCV]:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        base, _ = self.parse_symbol(symbol)
        base_price = self._get_price(base)
        
        # Parse interval to timedelta
        interval_map = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
        }
        delta = interval_map.get(interval, timedelta(hours=1))
        
        # Generate historical data
        end = end_time or datetime.utcnow()
        candles = []
        
        price = base_price
        for i in range(limit):
            timestamp = end - (delta * (limit - i - 1))
            
            # Generate OHLCV
            volatility = Decimal(str(random.gauss(0, 0.02)))
            open_price = price
            close_price = price * (1 + volatility)
            high_price = max(open_price, close_price) * (1 + Decimal(str(random.random() * 0.01)))
            low_price = min(open_price, close_price) * (1 - Decimal(str(random.random() * 0.01)))
            volume = base_price * Decimal(str(random.uniform(100, 1000)))
            
            candles.append(OHLCV(
                timestamp=timestamp,
                open=open_price.quantize(Decimal("0.01")),
                high=high_price.quantize(Decimal("0.01")),
                low=low_price.quantize(Decimal("0.01")),
                close=close_price.quantize(Decimal("0.01")),
                volume=volume.quantize(Decimal("0.01"))
            ))
            
            price = close_price
        
        return candles
    
    # -------------------------------------------------------------------------
    # Trading
    # -------------------------------------------------------------------------
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        amount: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        client_order_id: Optional[str] = None
    ) -> Order:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        # Validate order
        if amount <= 0:
            raise InvalidOrderError("Amount must be positive")
        
        if order_type == OrderType.LIMIT and price is None:
            raise InvalidOrderError("Price required for limit orders")
        
        base, quote = self.parse_symbol(symbol)
        current_price = self._get_price(base)
        
        # Check sufficient balance
        if side == OrderSide.BUY:
            required = amount * (price or current_price) * (1 + TRADING_FEE_RATE)
            if self._balances.get(quote, Balance(quote, Decimal("0"))).available < required:
                raise InsufficientFundsError(
                    f"Insufficient {quote} balance. Required: {required}, "
                    f"Available: {self._balances.get(quote, Balance(quote, Decimal('0'))).available}"
                )
            # Lock funds
            self._balances[quote].available -= required
            self._balances[quote].locked += required
        else:  # SELL
            if self._balances.get(base, Balance(base, Decimal("0"))).available < amount:
                raise InsufficientFundsError(
                    f"Insufficient {base} balance. Required: {amount}, "
                    f"Available: {self._balances.get(base, Balance(base, Decimal('0'))).available}"
                )
            # Lock funds
            self._balances[base].available -= amount
            self._balances[base].locked += amount
        
        # Create order
        order = Order(
            id=self._generate_id("ord"),
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            client_order_id=client_order_id
        )
        
        # Execute order
        order = self._execute_order(order)
        
        # Unlock funds if filled
        if order.status == OrderStatus.FILLED:
            if side == OrderSide.BUY:
                self._balances[quote].locked = Decimal("0")
            else:
                self._balances[base].locked = Decimal("0")
        
        self._orders[order.id] = order
        return order
    
    async def cancel_order(self, order_id: str) -> Order:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        if order_id not in self._orders:
            raise OrderNotFoundError(f"Order not found: {order_id}")
        
        order = self._orders[order_id]
        
        if order.is_complete:
            raise InvalidOrderError(f"Cannot cancel {order.status.value} order")
        
        # Unlock funds
        base, quote = self.parse_symbol(order.symbol)
        if order.side == OrderSide.BUY:
            locked = order.remaining_amount * (order.price or self._get_price(base))
            self._balances[quote].locked -= locked
            self._balances[quote].available += locked
        else:
            self._balances[base].locked -= order.remaining_amount
            self._balances[base].available += order.remaining_amount
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        
        return order
    
    async def get_order(self, order_id: str) -> Order:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        if order_id not in self._orders:
            raise OrderNotFoundError(f"Order not found: {order_id}")
        
        return self._orders[order_id]
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        orders = [
            o for o in self._orders.values()
            if not o.is_complete
            and (symbol is None or o.symbol == symbol)
        ]
        return orders
    
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Order]:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        orders = list(self._orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        if start_time:
            orders = [o for o in orders if o.created_at >= start_time]
        if end_time:
            orders = [o for o in orders if o.created_at <= end_time]
        
        orders.sort(key=lambda o: o.created_at, reverse=True)
        return orders[:limit]
    
    # -------------------------------------------------------------------------
    # Transactions
    # -------------------------------------------------------------------------
    
    async def get_transactions(
        self,
        asset: Optional[str] = None,
        tx_type: Optional[TransactionType] = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Transaction]:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        txs = list(self._transactions)
        
        if asset:
            txs = [t for t in txs if t.asset == asset.upper()]
        if tx_type:
            txs = [t for t in txs if t.tx_type == tx_type]
        if start_time:
            txs = [t for t in txs if t.timestamp >= start_time]
        if end_time:
            txs = [t for t in txs if t.timestamp <= end_time]
        
        txs.sort(key=lambda t: t.timestamp, reverse=True)
        return txs[:limit]
    
    # -------------------------------------------------------------------------
    # Staking
    # -------------------------------------------------------------------------
    
    async def get_staking_positions(self) -> List[StakingPosition]:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        # Update rewards
        for pos in self._staking_positions.values():
            if pos.status == "active":
                # Calculate rewards since start
                days = (datetime.utcnow() - pos.started_at).days
                annual_reward = pos.amount * pos.apy / 100
                pos.rewards_earned = annual_reward * Decimal(days) / 365
        
        return list(self._staking_positions.values())
    
    async def stake(
        self,
        asset: str,
        amount: Decimal,
        validator: Optional[str] = None
    ) -> StakingPosition:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        asset = asset.upper()
        
        if asset not in STAKING_RATES:
            raise StakingError(f"Staking not available for {asset}")
        
        balance = self._balances.get(asset)
        if not balance or balance.available < amount:
            raise InsufficientFundsError(f"Insufficient {asset} balance")
        
        # Move funds from available to staked
        balance.available -= amount
        balance.staked += amount
        
        # Create or update staking position
        pos_id = f"stake_{asset}_{self.name}"
        if pos_id in self._staking_positions:
            pos = self._staking_positions[pos_id]
            pos.amount += amount
        else:
            pos = StakingPosition(
                id=pos_id,
                asset=asset,
                amount=amount,
                apy=STAKING_RATES[asset],
                validator=validator
            )
            self._staking_positions[pos_id] = pos
        
        # Record transaction
        self._transactions.append(Transaction(
            id=self._generate_id("tx"),
            tx_type=TransactionType.STAKE,
            asset=asset,
            amount=amount,
            timestamp=datetime.utcnow(),
            price_usd=self._get_price(asset)
        ))
        
        return pos
    
    async def unstake(
        self,
        asset: str,
        amount: Optional[Decimal] = None
    ) -> StakingPosition:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        asset = asset.upper()
        pos_id = f"stake_{asset}_{self.name}"
        
        if pos_id not in self._staking_positions:
            raise StakingError(f"No staking position for {asset}")
        
        pos = self._staking_positions[pos_id]
        unstake_amount = amount or pos.amount
        
        if unstake_amount > pos.amount:
            raise StakingError(f"Cannot unstake more than staked amount")
        
        # Update position
        pos.amount -= unstake_amount
        pos.status = "unbonding"
        pos.unlock_date = datetime.utcnow() + timedelta(days=21)  # 21 day unbonding
        
        # Update balance (funds still locked during unbonding)
        self._balances[asset].staked -= unstake_amount
        self._balances[asset].locked += unstake_amount
        
        # Record transaction
        self._transactions.append(Transaction(
            id=self._generate_id("tx"),
            tx_type=TransactionType.UNSTAKE,
            asset=asset,
            amount=unstake_amount,
            timestamp=datetime.utcnow(),
            price_usd=self._get_price(asset),
            notes=f"Unbonding until {pos.unlock_date.isoformat()}"
        ))
        
        return pos
    
    async def claim_staking_rewards(self, asset: Optional[str] = None) -> List[Transaction]:
        await self._simulate_latency()
        self._check_rate_limit()
        self._maybe_fail()
        
        rewards = []
        
        for pos in self._staking_positions.values():
            if asset and pos.asset != asset.upper():
                continue
            
            if pos.rewards_earned > 0:
                # Add rewards to available balance
                if pos.asset not in self._balances:
                    self._balances[pos.asset] = Balance(asset=pos.asset, available=Decimal("0"))
                
                self._balances[pos.asset].available += pos.rewards_earned
                
                # Record transaction
                tx = Transaction(
                    id=self._generate_id("tx"),
                    tx_type=TransactionType.STAKING_REWARD,
                    asset=pos.asset,
                    amount=pos.rewards_earned,
                    timestamp=datetime.utcnow(),
                    price_usd=self._get_price(pos.asset)
                )
                self._transactions.append(tx)
                rewards.append(tx)
                
                # Reset earned rewards
                pos.rewards_earned = Decimal("0")
                pos.started_at = datetime.utcnow()
        
        return rewards
    
    # -------------------------------------------------------------------------
    # Testing Utilities
    # -------------------------------------------------------------------------
    
    def set_balance(self, asset: str, amount: Decimal):
        """Set balance for testing."""
        self._balances[asset] = Balance(asset=asset, available=amount)
    
    def set_price(self, asset: str, price: Decimal):
        """Set price for testing."""
        self._current_prices[asset] = price
    
    def trigger_price_update(self):
        """Manually trigger price update."""
        self._update_prices()
    
    def reset(self):
        """Reset all state to initial values."""
        self._balances = {}
        self._orders = {}
        self._transactions = []
        self._staking_positions = {}
        self._current_prices = dict(BASE_PRICES)
        
        for asset, amount in DEFAULT_BALANCES.items():
            self._balances[asset] = Balance(asset=asset, available=amount)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state for debugging."""
        return {
            "balances": {k: v.to_dict() for k, v in self._balances.items()},
            "orders": {k: v.to_dict() for k, v in self._orders.items()},
            "transactions": [t.to_dict() for t in self._transactions],
            "staking_positions": {k: v.to_dict() for k, v in self._staking_positions.items()},
            "prices": {k: str(v) for k, v in self._current_prices.items()}
        }


# =============================================================================
# EXCHANGE FACTORY
# =============================================================================


# Pre-configured mock exchanges
MOCK_EXCHANGES = {
    "coinbase": {
        "name": "mock_coinbase",
        "initial_balances": {
            "BTC": Decimal("1.0"),
            "ETH": Decimal("10.0"),
            "USDC": Decimal("5000.0"),
            "USD": Decimal("2500.0"),
        }
    },
    "kraken": {
        "name": "mock_kraken",
        "initial_balances": {
            "BTC": Decimal("0.5"),
            "ETH": Decimal("5.0"),
            "SOL": Decimal("100.0"),
            "USD": Decimal("3000.0"),
        }
    },
    "crypto.com": {
        "name": "mock_crypto_com",
        "initial_balances": {
            "ETH": Decimal("3.0"),
            "ATOM": Decimal("200.0"),
            "USDC": Decimal("2000.0"),
        }
    },
    "gemini": {
        "name": "mock_gemini",
        "initial_balances": {
            "BTC": Decimal("0.25"),
            "ETH": Decimal("2.0"),
            "USD": Decimal("1500.0"),
        }
    },
}


def create_mock_exchange(
    exchange: str,
    **kwargs
) -> MockExchangeClient:
    """
    Create a pre-configured mock exchange client.
    
    Args:
        exchange: Exchange name ('coinbase', 'kraken', 'crypto.com', 'gemini')
        **kwargs: Additional arguments passed to MockExchangeClient
        
    Returns:
        Configured MockExchangeClient
    """
    config = MOCK_EXCHANGES.get(exchange.lower(), {})
    
    return MockExchangeClient(
        exchange_name=config.get("name", f"mock_{exchange}"),
        initial_balances=config.get("initial_balances"),
        **kwargs
    )


async def create_all_mock_exchanges() -> Dict[str, MockExchangeClient]:
    """
    Create and authenticate all mock exchanges.
    
    Returns:
        Dictionary of exchange name to authenticated client
    """
    exchanges = {}
    
    for name in MOCK_EXCHANGES:
        client = create_mock_exchange(name)
        await client.authenticate()
        exchanges[name] = client
    
    return exchanges
