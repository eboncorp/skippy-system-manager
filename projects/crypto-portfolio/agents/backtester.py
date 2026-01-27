"""
Crypto Trading Backtester

Test trading strategies against historical data before deploying capital.

Features:
- Historical data fetching (CoinGecko, CSV import)
- Strategy simulation with realistic execution
- Performance metrics (Sharpe, Sortino, Max Drawdown, etc.)
- Comparison across strategies
- Detailed trade logs and reporting
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
import asyncio
import aiohttp
import json
import math
import statistics
from collections import defaultdict

# Import trading components
from .trading_agent import (
    Order, OrderSide, OrderType, OrderStatus,
    Position, PositionSide, Trade, Portfolio,
    TradingConfig, TradingMode, RiskLimits,
    TradingStrategy, DCASignalStrategy, SwingStrategy,
    MeanReversionStrategy, GridStrategy, RebalanceStrategy,
    RiskManager, SignalAction,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class OHLCV:
    """Open, High, Low, Close, Volume candle data."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    
    @property
    def typical_price(self) -> Decimal:
        return (self.high + self.low + self.close) / 3


@dataclass
class BacktestTrade:
    """Trade executed during backtest."""
    timestamp: datetime
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    value: Decimal
    fees: Decimal
    signal_score: float
    strategy: str
    portfolio_value_before: Decimal
    portfolio_value_after: Decimal
    
    @property
    def pnl(self) -> Decimal:
        return self.portfolio_value_after - self.portfolio_value_before


@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time."""
    timestamp: datetime
    cash: Decimal
    positions: Dict[str, Decimal]  # symbol -> quantity
    prices: Dict[str, Decimal]     # symbol -> price
    total_value: Decimal
    drawdown: Decimal
    drawdown_pct: Decimal


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    # Returns
    total_return_pct: float
    annualized_return_pct: float
    
    # Risk metrics
    volatility_pct: float
    annualized_volatility_pct: float
    max_drawdown_pct: float
    max_drawdown_duration_days: int
    
    # Risk-adjusted returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    avg_trade_pct: float
    
    # Exposure
    time_in_market_pct: float
    avg_position_size_pct: float
    max_position_size_pct: float
    
    # Comparison
    buy_hold_return_pct: float
    alpha_pct: float  # Excess return vs buy & hold
    beta: float       # Correlation to market
    
    # Period stats
    best_day_pct: float
    worst_day_pct: float
    best_month_pct: float
    worst_month_pct: float
    positive_months: int
    negative_months: int


@dataclass 
class BacktestResult:
    """Complete backtest results."""
    # Configuration
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    assets: List[str]
    
    # Final state
    final_value: Decimal
    final_cash: Decimal
    final_positions: Dict[str, Decimal]
    
    # Performance
    metrics: PerformanceMetrics
    
    # History
    trades: List[BacktestTrade]
    portfolio_history: List[PortfolioSnapshot]
    daily_returns: List[float]
    
    # Signals used (for analysis)
    signal_history: List[Tuple[datetime, float]]


# =============================================================================
# HISTORICAL DATA
# =============================================================================

class HistoricalDataProvider:
    """Fetches and manages historical price data."""
    
    COINGECKO_IDS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "BNB": "binancecoin",
        "XRP": "ripple",
        "ADA": "cardano",
        "AVAX": "avalanche-2",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "ATOM": "cosmos",
        "LTC": "litecoin",
    }
    
    def __init__(self):
        self._cache: Dict[str, List[OHLCV]] = {}
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
    
    async def fetch_coingecko(
        self,
        asset: str,
        days: int = 365,
        vs_currency: str = "usd"
    ) -> List[OHLCV]:
        """
        Fetch historical data from CoinGecko.
        
        Note: Free tier has rate limits. For production, use paid API or local data.
        """
        cache_key = f"{asset}_{days}_{vs_currency}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        coin_id = self.COINGECKO_IDS.get(asset, asset.lower())
        
        session = await self._get_session()
        
        # CoinGecko market_chart endpoint
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days,
            "interval": "daily" if days > 90 else "hourly",
        }
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    # Rate limited - wait and retry
                    await asyncio.sleep(60)
                    return await self.fetch_coingecko(asset, days, vs_currency)
                
                data = await response.json()
        except Exception as e:
            print(f"Error fetching {asset} data: {e}")
            return []
        
        # Parse into OHLCV (CoinGecko gives price, market_cap, volume)
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        
        candles = []
        for i, (ts, price) in enumerate(prices):
            dt = datetime.fromtimestamp(ts / 1000)
            price_dec = Decimal(str(price))
            vol = Decimal(str(volumes[i][1])) if i < len(volumes) else Decimal("0")
            
            # CoinGecko doesn't give OHLC, so we simulate with small variance
            variance = price_dec * Decimal("0.01")
            
            candles.append(OHLCV(
                timestamp=dt,
                open=price_dec - variance / 2,
                high=price_dec + variance,
                low=price_dec - variance,
                close=price_dec,
                volume=vol,
            ))
        
        self._cache[cache_key] = candles
        return candles
    
    async def fetch_ohlcv_coingecko(
        self,
        asset: str,
        days: int = 365,
    ) -> List[OHLCV]:
        """Fetch OHLCV data (wrapper for consistency)."""
        return await self.fetch_coingecko(asset, days)
    
    def load_from_csv(self, filepath: str, asset: str) -> List[OHLCV]:
        """
        Load historical data from CSV file.
        
        Expected columns: timestamp/date, open, high, low, close, volume
        """
        import csv
        
        candles = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle various date formats
                date_str = row.get('timestamp') or row.get('date') or row.get('Date')
                try:
                    if 'T' in date_str:
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    continue
                
                candles.append(OHLCV(
                    timestamp=dt,
                    open=Decimal(row.get('open') or row.get('Open', '0')),
                    high=Decimal(row.get('high') or row.get('High', '0')),
                    low=Decimal(row.get('low') or row.get('Low', '0')),
                    close=Decimal(row.get('close') or row.get('Close', '0')),
                    volume=Decimal(row.get('volume') or row.get('Volume', '0')),
                ))
        
        self._cache[f"{asset}_csv"] = candles
        return sorted(candles, key=lambda x: x.timestamp)
    
    def generate_synthetic(
        self,
        asset: str,
        start_price: Decimal,
        days: int = 365,
        volatility: float = 0.03,
        trend: float = 0.0002,
    ) -> List[OHLCV]:
        """
        Generate synthetic price data for testing.
        
        Uses geometric Brownian motion with configurable volatility and trend.
        """
        import random
        
        candles = []
        price = float(start_price)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        for day in range(days):
            dt = start_date + timedelta(days=day)
            
            # Random walk with drift
            daily_return = random.gauss(trend, volatility)
            price *= (1 + daily_return)
            
            # Generate OHLCV
            open_p = price * (1 + random.gauss(0, 0.005))
            high_p = price * (1 + abs(random.gauss(0, 0.015)))
            low_p = price * (1 - abs(random.gauss(0, 0.015)))
            close_p = price
            volume = Decimal(str(random.uniform(1e9, 5e10)))
            
            candles.append(OHLCV(
                timestamp=dt,
                open=Decimal(str(open_p)),
                high=Decimal(str(high_p)),
                low=Decimal(str(low_p)),
                close=Decimal(str(close_p)),
                volume=volume,
            ))
        
        self._cache[f"{asset}_synthetic"] = candles
        return candles


# =============================================================================
# SIMULATED SIGNAL GENERATOR
# =============================================================================

class SimulatedSignalGenerator:
    """
    Generates simulated signal scores for backtesting.
    
    Uses price action and simple indicators to approximate
    what the real 130+ signal system would produce.
    """
    
    def __init__(self):
        self.rsi_period = 14
        self.ma_short = 20
        self.ma_long = 50
    
    def calculate_rsi(self, prices: List[Decimal], period: int = 14) -> float:
        """Calculate RSI."""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = float(prices[i] - prices[i-1])
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_ma(self, prices: List[Decimal], period: int) -> Optional[Decimal]:
        """Calculate simple moving average."""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def generate_score(
        self,
        price_history: List[OHLCV],
        current_index: int
    ) -> float:
        """
        Generate a simulated composite signal score.
        
        Combines:
        - RSI (oversold/overbought)
        - Moving average crossover
        - Price momentum
        - Volatility regime
        
        Returns score from -100 to +100
        """
        if current_index < 50:
            return 0.0
        
        # Get recent prices
        recent = price_history[max(0, current_index-100):current_index+1]
        closes = [c.close for c in recent]
        
        score = 0.0
        
        # RSI component (-30 to +30)
        rsi = self.calculate_rsi(closes)
        if rsi < 30:
            score += (30 - rsi)  # Oversold = bullish
        elif rsi > 70:
            score -= (rsi - 70)  # Overbought = bearish
        
        # MA crossover component (-25 to +25)
        ma_short = self.calculate_ma(closes, self.ma_short)
        ma_long = self.calculate_ma(closes, self.ma_long)
        
        if ma_short and ma_long:
            ma_diff_pct = float((ma_short - ma_long) / ma_long) * 100
            score += max(-25, min(25, ma_diff_pct * 5))
        
        # Momentum component (-20 to +20)
        if len(closes) >= 30:
            momentum = float((closes[-1] - closes[-30]) / closes[-30]) * 100
            score += max(-20, min(20, -momentum))  # Negative = contrarian
        
        # Volatility regime (-15 to +15)
        if len(closes) >= 20:
            returns = [(float(closes[i]) - float(closes[i-1])) / float(closes[i-1]) 
                      for i in range(1, len(closes))]
            if len(returns) >= 20:
                volatility = statistics.stdev(returns[-20:]) * 100
                if volatility > 5:
                    score += 10  # High vol often means fear = opportunity
                elif volatility < 1:
                    score -= 5   # Low vol complacency
        
        # Distance from recent high/low (-10 to +10)
        if len(closes) >= 50:
            high_50 = max(closes[-50:])
            low_50 = min(closes[-50:])
            current = closes[-1]
            
            range_pos = float((current - low_50) / (high_50 - low_50)) if high_50 != low_50 else 0.5
            score += (0.5 - range_pos) * 20  # Lower in range = more bullish
        
        return max(-100, min(100, score))


# =============================================================================
# BACKTEST ENGINE
# =============================================================================

class BacktestEngine:
    """
    Core backtesting engine.
    
    Simulates strategy execution against historical data
    with realistic fills, fees, and slippage.
    """
    
    def __init__(
        self,
        initial_capital: Decimal = Decimal("10000"),
        fee_rate: Decimal = Decimal("0.001"),    # 0.1% per trade
        slippage_rate: Decimal = Decimal("0.001"), # 0.1% slippage
    ):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        
        self.data_provider = HistoricalDataProvider()
        self.signal_generator = SimulatedSignalGenerator()
    
    async def close(self):
        """Clean up resources."""
        await self.data_provider.close()
    
    async def run(
        self,
        strategy: TradingStrategy,
        assets: List[str] = None,
        days: int = 365,
        data: Dict[str, List[OHLCV]] = None,
    ) -> BacktestResult:
        """
        Run a backtest.
        
        Args:
            strategy: Trading strategy to test
            assets: List of assets to trade
            days: Number of days to backtest
            data: Pre-loaded historical data (optional)
        
        Returns:
            BacktestResult with full performance analysis
        """
        assets = assets or ["BTC"]
        
        # Load historical data
        if data is None:
            data = {}
            for asset in assets:
                print(f"Fetching {asset} historical data...")
                data[asset] = await self.data_provider.fetch_coingecko(asset, days)
                await asyncio.sleep(1)  # Rate limit
        
        # Validate data
        if not all(data.get(a) for a in assets):
            raise ValueError("Missing historical data for some assets")
        
        # Align data to common timestamps
        min_len = min(len(data[a]) for a in assets)
        for asset in assets:
            data[asset] = data[asset][-min_len:]
        
        start_date = data[assets[0]][0].timestamp
        end_date = data[assets[0]][-1].timestamp
        
        # Initialize portfolio
        portfolio = Portfolio(
            cash_balance=self.initial_capital,
            positions={},
            total_value=self.initial_capital,
            initial_value=self.initial_capital,
        )
        
        # Risk manager
        risk_manager = RiskManager(strategy.config.risk_limits)
        risk_manager.peak_value = self.initial_capital
        
        # Tracking
        trades: List[BacktestTrade] = []
        portfolio_history: List[PortfolioSnapshot] = []
        signal_history: List[Tuple[datetime, float]] = []
        daily_values: List[Decimal] = []
        peak_value = self.initial_capital
        
        # Strategy state
        strategy.last_dca_time = {a: datetime.min for a in assets}
        
        print(f"Running backtest: {strategy.name}")
        print(f"  Period: {start_date.date()} to {end_date.date()}")
        print(f"  Assets: {', '.join(assets)}")
        print(f"  Initial capital: ${self.initial_capital:,.2f}")
        print()
        
        # Main simulation loop
        for i in range(50, min_len):  # Start at 50 for indicator warmup
            current_time = data[assets[0]][i].timestamp
            
            # Get current prices
            current_prices = {}
            for asset in assets:
                current_prices[asset] = data[asset][i].close
            
            # Update portfolio value
            portfolio.total_value = portfolio.cash_balance
            for symbol, position in portfolio.positions.items():
                asset = symbol.split("/")[0]
                if asset in current_prices:
                    position.current_price = current_prices[asset]
                    position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
                    portfolio.total_value += position.quantity * position.current_price
            
            # Track peak for drawdown
            if portfolio.total_value > peak_value:
                peak_value = portfolio.total_value
            
            drawdown = peak_value - portfolio.total_value
            drawdown_pct = (drawdown / peak_value * 100) if peak_value > 0 else Decimal("0")
            
            # Generate signal score
            signal_score = self.signal_generator.generate_score(data[assets[0]], i)
            signal_history.append((current_time, signal_score))
            
            # Determine market condition and cycle phase (simplified)
            if signal_score < -40:
                market_condition = "fear"
                cycle_phase = "accumulation"
            elif signal_score < -10:
                market_condition = "mild_fear"
                cycle_phase = "early_bull"
            elif signal_score < 20:
                market_condition = "neutral"
                cycle_phase = "bull_market"
            elif signal_score < 50:
                market_condition = "mild_greed"
                cycle_phase = "euphoria"
            else:
                market_condition = "greed"
                cycle_phase = "distribution"
            
            # Get strategy actions
            actions = await strategy.evaluate(
                signal_score=signal_score,
                market_condition=market_condition,
                cycle_phase=cycle_phase,
                portfolio=portfolio,
                current_prices=current_prices,
            )
            
            # Execute actions
            for action in actions:
                if action.action == "hold":
                    continue
                
                asset = action.symbol.split("/")[0]
                price = current_prices.get(asset)
                
                if not price or action.suggested_quantity <= 0:
                    continue
                
                # Apply slippage
                if "buy" in action.action:
                    exec_price = price * (1 + self.slippage_rate)
                else:
                    exec_price = price * (1 - self.slippage_rate)
                
                # Calculate trade value and fees
                trade_value = action.suggested_quantity * exec_price
                fees = trade_value * self.fee_rate
                
                # Validate and execute
                order = Order(
                    id=f"BT-{len(trades)}",
                    symbol=action.symbol,
                    side=OrderSide.BUY if "buy" in action.action else OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=action.suggested_quantity,
                    price=exec_price,
                )
                
                is_valid, reason = risk_manager.validate_order(order, portfolio, exec_price)
                
                if not is_valid:
                    continue
                
                portfolio_before = portfolio.total_value
                
                if "buy" in action.action:
                    total_cost = trade_value + fees
                    if portfolio.cash_balance >= total_cost:
                        portfolio.cash_balance -= total_cost
                        
                        symbol = action.symbol
                        if symbol in portfolio.positions:
                            # Average into position
                            pos = portfolio.positions[symbol]
                            total_qty = pos.quantity + action.suggested_quantity
                            pos.entry_price = (
                                (pos.entry_price * pos.quantity + exec_price * action.suggested_quantity) 
                                / total_qty
                            )
                            pos.quantity = total_qty
                        else:
                            portfolio.positions[symbol] = Position(
                                symbol=symbol,
                                side=PositionSide.LONG,
                                quantity=action.suggested_quantity,
                                entry_price=exec_price,
                                current_price=exec_price,
                                opened_at=current_time,
                            )
                
                else:  # Sell
                    symbol = action.symbol
                    if symbol in portfolio.positions:
                        pos = portfolio.positions[symbol]
                        sell_qty = min(action.suggested_quantity, pos.quantity)
                        proceeds = sell_qty * exec_price - fees
                        
                        portfolio.cash_balance += proceeds
                        pos.quantity -= sell_qty
                        
                        if pos.quantity <= 0:
                            del portfolio.positions[symbol]
                
                # Update portfolio value after trade
                portfolio.total_value = portfolio.cash_balance
                for sym, pos in portfolio.positions.items():
                    asset_name = sym.split("/")[0]
                    if asset_name in current_prices:
                        portfolio.total_value += pos.quantity * current_prices[asset_name]
                
                # Record trade
                trades.append(BacktestTrade(
                    timestamp=current_time,
                    symbol=action.symbol,
                    side=order.side,
                    quantity=action.suggested_quantity,
                    price=exec_price,
                    value=trade_value,
                    fees=fees,
                    signal_score=signal_score,
                    strategy=action.reasoning,
                    portfolio_value_before=portfolio_before,
                    portfolio_value_after=portfolio.total_value,
                ))
            
            # Record daily snapshot (simplified - just track each candle)
            portfolio_history.append(PortfolioSnapshot(
                timestamp=current_time,
                cash=portfolio.cash_balance,
                positions={s: p.quantity for s, p in portfolio.positions.items()},
                prices=dict(current_prices),
                total_value=portfolio.total_value,
                drawdown=drawdown,
                drawdown_pct=drawdown_pct,
            ))
            
            daily_values.append(portfolio.total_value)
        
        # Calculate performance metrics
        daily_returns = []
        for i in range(1, len(daily_values)):
            ret = float((daily_values[i] - daily_values[i-1]) / daily_values[i-1])
            daily_returns.append(ret)
        
        metrics = self._calculate_metrics(
            initial_capital=self.initial_capital,
            final_value=portfolio.total_value,
            daily_returns=daily_returns,
            trades=trades,
            portfolio_history=portfolio_history,
            buy_hold_data=data[assets[0]],
        )
        
        print(f"Backtest complete!")
        print(f"  Final value: ${portfolio.total_value:,.2f}")
        print(f"  Total return: {metrics.total_return_pct:+.2f}%")
        print(f"  Max drawdown: {metrics.max_drawdown_pct:.2f}%")
        print(f"  Sharpe ratio: {metrics.sharpe_ratio:.2f}")
        print(f"  Total trades: {metrics.total_trades}")
        
        return BacktestResult(
            strategy_name=strategy.name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            assets=assets,
            final_value=portfolio.total_value,
            final_cash=portfolio.cash_balance,
            final_positions={s: p.quantity for s, p in portfolio.positions.items()},
            metrics=metrics,
            trades=trades,
            portfolio_history=portfolio_history,
            daily_returns=daily_returns,
            signal_history=signal_history,
        )
    
    def _calculate_metrics(
        self,
        initial_capital: Decimal,
        final_value: Decimal,
        daily_returns: List[float],
        trades: List[BacktestTrade],
        portfolio_history: List[PortfolioSnapshot],
        buy_hold_data: List[OHLCV],
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        
        # Basic returns
        total_return = float((final_value - initial_capital) / initial_capital) * 100
        
        days = len(daily_returns)
        years = days / 365
        
        if years > 0 and total_return > -100:
            annualized_return = ((1 + total_return/100) ** (1/years) - 1) * 100
        else:
            annualized_return = total_return
        
        # Volatility
        if len(daily_returns) > 1:
            volatility = statistics.stdev(daily_returns) * 100
            annualized_vol = volatility * math.sqrt(365)
        else:
            volatility = 0
            annualized_vol = 0
        
        # Max drawdown
        max_dd = 0
        max_dd_duration = 0
        dd_start = None
        peak = portfolio_history[0].total_value if portfolio_history else initial_capital
        
        for snapshot in portfolio_history:
            if snapshot.total_value > peak:
                peak = snapshot.total_value
                dd_start = None
            
            dd = float((peak - snapshot.total_value) / peak) * 100
            if dd > max_dd:
                max_dd = dd
            
            if dd > 0 and dd_start is None:
                dd_start = snapshot.timestamp
            elif dd == 0 and dd_start:
                duration = (snapshot.timestamp - dd_start).days
                max_dd_duration = max(max_dd_duration, duration)
                dd_start = None
        
        # Risk-adjusted returns
        risk_free_rate = 0.04 / 365  # ~4% annual
        
        if annualized_vol > 0:
            sharpe = (annualized_return/100 - 0.04) / (annualized_vol/100)
        else:
            sharpe = 0
        
        # Sortino (downside deviation)
        negative_returns = [r for r in daily_returns if r < 0]
        if negative_returns:
            downside_dev = statistics.stdev(negative_returns) * math.sqrt(365) * 100
            sortino = (annualized_return/100 - 0.04) / (downside_dev/100) if downside_dev > 0 else 0
        else:
            sortino = sharpe * 1.5  # Approximate if no negative returns
        
        # Calmar ratio
        calmar = annualized_return / max_dd if max_dd > 0 else 0
        
        # Trade statistics
        total_trades = len(trades)
        
        if trades:
            buy_trades = [t for t in trades if t.side == OrderSide.BUY]
            sell_trades = [t for t in trades if t.side == OrderSide.SELL]
            
            # Calculate trade P&L
            trade_pnls = []
            for i, trade in enumerate(trades):
                if i > 0:
                    pnl_pct = float(trade.pnl / trade.portfolio_value_before) * 100
                    trade_pnls.append(pnl_pct)
            
            winning = [p for p in trade_pnls if p > 0]
            losing = [p for p in trade_pnls if p < 0]
            
            win_rate = len(winning) / len(trade_pnls) * 100 if trade_pnls else 0
            avg_win = statistics.mean(winning) if winning else 0
            avg_loss = statistics.mean(losing) if losing else 0
            
            gross_profit = sum(winning)
            gross_loss = abs(sum(losing))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            avg_trade = statistics.mean(trade_pnls) if trade_pnls else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            avg_trade = 0
            winning = []
            losing = []
        
        # Exposure metrics
        total_time = len(portfolio_history)
        time_in_market = sum(1 for s in portfolio_history if s.positions) / total_time * 100 if total_time else 0
        
        position_sizes = []
        for snapshot in portfolio_history:
            for symbol, qty in snapshot.positions.items():
                asset = symbol.split("/")[0]
                price = snapshot.prices.get(asset, Decimal("0"))
                pos_value = qty * price
                if snapshot.total_value > 0:
                    position_sizes.append(float(pos_value / snapshot.total_value) * 100)
        
        avg_position = statistics.mean(position_sizes) if position_sizes else 0
        max_position = max(position_sizes) if position_sizes else 0
        
        # Buy & hold comparison
        if buy_hold_data and len(buy_hold_data) > 1:
            start_price = buy_hold_data[0].close
            end_price = buy_hold_data[-1].close
            buy_hold_return = float((end_price - start_price) / start_price) * 100
        else:
            buy_hold_return = 0
        
        alpha = total_return - buy_hold_return
        
        # Beta (correlation to market)
        if len(daily_returns) > 10 and len(buy_hold_data) > 10:
            market_returns = []
            for i in range(1, min(len(buy_hold_data), len(daily_returns) + 1)):
                mr = float((buy_hold_data[i].close - buy_hold_data[i-1].close) / buy_hold_data[i-1].close)
                market_returns.append(mr)
            
            if len(market_returns) == len(daily_returns):
                # Calculate covariance and variance
                mean_strat = statistics.mean(daily_returns)
                mean_market = statistics.mean(market_returns)
                
                covar = sum((daily_returns[i] - mean_strat) * (market_returns[i] - mean_market) 
                           for i in range(len(daily_returns))) / len(daily_returns)
                var_market = statistics.variance(market_returns)
                
                beta = covar / var_market if var_market > 0 else 1
            else:
                beta = 1
        else:
            beta = 1
        
        # Daily best/worst
        best_day = max(daily_returns) * 100 if daily_returns else 0
        worst_day = min(daily_returns) * 100 if daily_returns else 0
        
        # Monthly stats (approximate from daily)
        monthly_chunks = [daily_returns[i:i+30] for i in range(0, len(daily_returns), 30)]
        monthly_returns = [sum(chunk) * 100 for chunk in monthly_chunks if chunk]
        
        best_month = max(monthly_returns) if monthly_returns else 0
        worst_month = min(monthly_returns) if monthly_returns else 0
        positive_months = sum(1 for m in monthly_returns if m > 0)
        negative_months = sum(1 for m in monthly_returns if m < 0)
        
        return PerformanceMetrics(
            total_return_pct=total_return,
            annualized_return_pct=annualized_return,
            volatility_pct=volatility,
            annualized_volatility_pct=annualized_vol,
            max_drawdown_pct=max_dd,
            max_drawdown_duration_days=max_dd_duration,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            total_trades=total_trades,
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate_pct=win_rate,
            avg_win_pct=avg_win,
            avg_loss_pct=avg_loss,
            profit_factor=profit_factor,
            avg_trade_pct=avg_trade,
            time_in_market_pct=time_in_market,
            avg_position_size_pct=avg_position,
            max_position_size_pct=max_position,
            buy_hold_return_pct=buy_hold_return,
            alpha_pct=alpha,
            beta=beta,
            best_day_pct=best_day,
            worst_day_pct=worst_day,
            best_month_pct=best_month,
            worst_month_pct=worst_month,
            positive_months=positive_months,
            negative_months=negative_months,
        )


# =============================================================================
# COMPARISON & REPORTING
# =============================================================================

def compare_strategies(results: List[BacktestResult]) -> str:
    """Generate comparison report for multiple backtest results."""
    
    lines = [
        "",
        "╔" + "═" * 98 + "╗",
        "║" + "STRATEGY COMPARISON".center(98) + "║",
        "╚" + "═" * 98 + "╝",
        "",
    ]
    
    # Header
    header = f"{'Strategy':<20} {'Return':>10} {'Ann.Ret':>10} {'Sharpe':>8} {'Sortino':>8} {'MaxDD':>8} {'Trades':>8} {'WinRate':>8} {'Alpha':>8}"
    lines.append(header)
    lines.append("-" * 100)
    
    # Sort by Sharpe ratio
    sorted_results = sorted(results, key=lambda r: r.metrics.sharpe_ratio, reverse=True)
    
    for result in sorted_results:
        m = result.metrics
        line = (
            f"{result.strategy_name:<20} "
            f"{m.total_return_pct:>+9.1f}% "
            f"{m.annualized_return_pct:>+9.1f}% "
            f"{m.sharpe_ratio:>8.2f} "
            f"{m.sortino_ratio:>8.2f} "
            f"{m.max_drawdown_pct:>7.1f}% "
            f"{m.total_trades:>8} "
            f"{m.win_rate_pct:>7.1f}% "
            f"{m.alpha_pct:>+7.1f}%"
        )
        lines.append(line)
    
    lines.append("-" * 100)
    
    # Add buy & hold reference
    if results:
        bh = results[0].metrics.buy_hold_return_pct
        lines.append(f"{'Buy & Hold':<20} {bh:>+9.1f}%")
    
    lines.append("")
    
    # Best strategy summary
    best = sorted_results[0]
    lines.extend([
        "═" * 100,
        f"BEST STRATEGY: {best.strategy_name}",
        f"  Sharpe Ratio: {best.metrics.sharpe_ratio:.2f}",
        f"  Total Return: {best.metrics.total_return_pct:+.1f}%",
        f"  Alpha vs B&H: {best.metrics.alpha_pct:+.1f}%",
        "═" * 100,
    ])
    
    return "\n".join(lines)


def format_backtest_report(result: BacktestResult) -> str:
    """Generate detailed report for a single backtest."""
    m = result.metrics
    
    lines = [
        "",
        "█" * 80,
        f"█  BACKTEST REPORT: {result.strategy_name.upper()}".ljust(79) + "█",
        "█" * 80,
        "",
        "┌" + "─" * 78 + "┐",
        "│  OVERVIEW".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
        f"│  Period:           {result.start_date.date()} to {result.end_date.date()}".ljust(79) + "│",
        f"│  Initial Capital:  ${result.initial_capital:>12,.2f}".ljust(79) + "│",
        f"│  Final Value:      ${result.final_value:>12,.2f}".ljust(79) + "│",
        f"│  Total Return:     {m.total_return_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Annualized:       {m.annualized_return_pct:>+12.2f}%".ljust(79) + "│",
        "└" + "─" * 78 + "┘",
        "",
        "┌" + "─" * 78 + "┐",
        "│  RISK METRICS".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
        f"│  Volatility (Ann): {m.annualized_volatility_pct:>12.2f}%".ljust(79) + "│",
        f"│  Max Drawdown:     {m.max_drawdown_pct:>12.2f}%".ljust(79) + "│",
        f"│  Max DD Duration:  {m.max_drawdown_duration_days:>12} days".ljust(79) + "│",
        f"│  Sharpe Ratio:     {m.sharpe_ratio:>12.2f}".ljust(79) + "│",
        f"│  Sortino Ratio:    {m.sortino_ratio:>12.2f}".ljust(79) + "│",
        f"│  Calmar Ratio:     {m.calmar_ratio:>12.2f}".ljust(79) + "│",
        "└" + "─" * 78 + "┘",
        "",
        "┌" + "─" * 78 + "┐",
        "│  TRADE STATISTICS".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
        f"│  Total Trades:     {m.total_trades:>12}".ljust(79) + "│",
        f"│  Winning Trades:   {m.winning_trades:>12}".ljust(79) + "│",
        f"│  Losing Trades:    {m.losing_trades:>12}".ljust(79) + "│",
        f"│  Win Rate:         {m.win_rate_pct:>12.1f}%".ljust(79) + "│",
        f"│  Avg Win:          {m.avg_win_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Avg Loss:         {m.avg_loss_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Profit Factor:    {m.profit_factor:>12.2f}".ljust(79) + "│",
        f"│  Avg Trade:        {m.avg_trade_pct:>+12.2f}%".ljust(79) + "│",
        "└" + "─" * 78 + "┘",
        "",
        "┌" + "─" * 78 + "┐",
        "│  EXPOSURE".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
        f"│  Time in Market:   {m.time_in_market_pct:>12.1f}%".ljust(79) + "│",
        f"│  Avg Position:     {m.avg_position_size_pct:>12.1f}%".ljust(79) + "│",
        f"│  Max Position:     {m.max_position_size_pct:>12.1f}%".ljust(79) + "│",
        "└" + "─" * 78 + "┘",
        "",
        "┌" + "─" * 78 + "┐",
        "│  BENCHMARK COMPARISON".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
        f"│  Buy & Hold:       {m.buy_hold_return_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Alpha:            {m.alpha_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Beta:             {m.beta:>12.2f}".ljust(79) + "│",
        "└" + "─" * 78 + "┘",
        "",
        "┌" + "─" * 78 + "┐",
        "│  EXTREMES".ljust(79) + "│",
        "├" + "─" * 78 + "┤",
        f"│  Best Day:         {m.best_day_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Worst Day:        {m.worst_day_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Best Month:       {m.best_month_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Worst Month:      {m.worst_month_pct:>+12.2f}%".ljust(79) + "│",
        f"│  Positive Months:  {m.positive_months:>12}".ljust(79) + "│",
        f"│  Negative Months:  {m.negative_months:>12}".ljust(79) + "│",
        "└" + "─" * 78 + "┘",
        "",
    ]
    
    # Recent trades
    if result.trades:
        lines.extend([
            "RECENT TRADES (last 10):",
            "-" * 80,
        ])
        for trade in result.trades[-10:]:
            emoji = "🟢" if trade.side == OrderSide.BUY else "🔴"
            lines.append(
                f"  {emoji} {trade.timestamp.strftime('%Y-%m-%d')} | "
                f"{trade.side.value.upper():4} {float(trade.quantity):.6f} {trade.symbol} @ ${float(trade.price):,.2f} | "
                f"Score: {trade.signal_score:+.0f}"
            )
        lines.append("")
    
    # Final positions
    if result.final_positions:
        lines.extend([
            "FINAL POSITIONS:",
            "-" * 40,
        ])
        for symbol, qty in result.final_positions.items():
            lines.append(f"  {symbol}: {float(qty):.8f}")
        lines.append(f"  Cash: ${float(result.final_cash):,.2f}")
        lines.append("")
    
    lines.append("█" * 80)
    
    return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def run_strategy_backtest(
    strategy_name: str,
    initial_capital: float = 10000,
    days: int = 365,
    assets: List[str] = None,
) -> BacktestResult:
    """Quick function to backtest a strategy."""
    
    assets = assets or ["BTC"]
    
    config = TradingConfig(
        mode=TradingMode.BACKTEST,
        supported_assets=assets,
        dca_base_amount=Decimal(str(initial_capital / 100)),
        dca_frequency_hours=24,
    )
    
    strategy_map = {
        "dca": DCASignalStrategy,
        "swing": SwingStrategy,
        "mean_reversion": MeanReversionStrategy,
        "grid": GridStrategy,
        "rebalance": RebalanceStrategy,
    }
    
    if strategy_name not in strategy_map:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    strategy = strategy_map[strategy_name](config)
    
    engine = BacktestEngine(initial_capital=Decimal(str(initial_capital)))
    
    try:
        result = await engine.run(strategy, assets=assets, days=days)
        return result
    finally:
        await engine.close()


async def compare_all_strategies(
    initial_capital: float = 10000,
    days: int = 365,
    assets: List[str] = None,
) -> str:
    """Run all strategies and return comparison."""
    
    assets = assets or ["BTC"]
    strategies = ["dca", "swing", "mean_reversion", "rebalance"]
    
    results = []
    
    # Fetch data once
    provider = HistoricalDataProvider()
    data = {}
    
    for asset in assets:
        print(f"Fetching {asset} data...")
        data[asset] = await provider.fetch_coingecko(asset, days)
        await asyncio.sleep(1)
    
    await provider.close()
    
    # Run each strategy
    for strat_name in strategies:
        print(f"\nBacktesting {strat_name}...")
        
        config = TradingConfig(
            mode=TradingMode.BACKTEST,
            supported_assets=assets,
            dca_base_amount=Decimal(str(initial_capital / 100)),
            dca_frequency_hours=24,
        )
        
        strategy_map = {
            "dca": DCASignalStrategy,
            "swing": SwingStrategy,
            "mean_reversion": MeanReversionStrategy,
            "rebalance": RebalanceStrategy,
        }
        
        strategy = strategy_map[strat_name](config)
        engine = BacktestEngine(initial_capital=Decimal(str(initial_capital)))
        
        try:
            result = await engine.run(strategy, assets=assets, data=data)
            results.append(result)
        finally:
            await engine.close()
    
    return compare_strategies(results)
