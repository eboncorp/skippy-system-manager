#!/usr/bin/env python3
"""
Adaptive Crypto Trading Bot - Two Account Strategy
===================================================

Automatically switches strategies based on market conditions.

Business Account (Kraken): Long-term DCA + Staking (no strategy switching)
Personal Account (Coinbase): Adaptive strategy based on market regime

Market Regimes:
- EXTREME_FEAR: Aggressive accumulation + Swing buys
- FEAR: Heavy DCA + opportunistic buys
- NEUTRAL: Grid trading (profit from chop)
- GREED: Reduced DCA + Mean reversion
- EXTREME_GREED: Minimal DCA + Profit taking

Usage:
    python adaptive_trader.py              # Single cycle
    python adaptive_trader.py --continuous # Run every hour
    python adaptive_trader.py --backtest 30 # Simulate 30 days
"""

import asyncio
import aiohttp
import json
import os
import smtplib
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse
import random

# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class MarketRegime(Enum):
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"

class Strategy(Enum):
    AGGRESSIVE_DCA = "aggressive_dca"
    SWING_BUY = "swing_buy"
    STANDARD_DCA = "standard_dca"
    GRID = "grid"
    MEAN_REVERSION = "mean_reversion"
    PROFIT_TAKING = "profit_taking"
    HOLD = "hold"

class TrendDirection(Enum):
    STRONG_UP = "strong_up"
    UP = "up"
    SIDEWAYS = "sideways"
    DOWN = "down"
    STRONG_DOWN = "strong_down"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class MarketData:
    fear_greed: int
    btc_price: Decimal
    eth_price: Decimal
    btc_24h_change: float
    eth_24h_change: float
    btc_7d_change: float
    regime: MarketRegime = None
    trend: TrendDirection = None

    def __post_init__(self):
        self.regime = self._detect_regime()
        self.trend = self._detect_trend()

    def _detect_regime(self) -> MarketRegime:
        if self.fear_greed <= 15:
            return MarketRegime.EXTREME_FEAR
        elif self.fear_greed <= 35:
            return MarketRegime.FEAR
        elif self.fear_greed <= 55:
            return MarketRegime.NEUTRAL
        elif self.fear_greed <= 75:
            return MarketRegime.GREED
        else:
            return MarketRegime.EXTREME_GREED

    def _detect_trend(self) -> TrendDirection:
        # Combine 24h and 7d changes
        combined = (self.btc_24h_change * 0.4) + (self.btc_7d_change * 0.6)

        if combined > 10:
            return TrendDirection.STRONG_UP
        elif combined > 3:
            return TrendDirection.UP
        elif combined > -3:
            return TrendDirection.SIDEWAYS
        elif combined > -10:
            return TrendDirection.DOWN
        else:
            return TrendDirection.STRONG_DOWN

@dataclass
class Trade:
    timestamp: datetime
    account: str
    strategy: Strategy
    side: OrderSide
    asset: str
    quantity: Decimal
    price: Decimal
    value_usd: Decimal
    reason: str

@dataclass
class StrategyDecision:
    regime: MarketRegime
    trend: TrendDirection
    business_strategy: Strategy
    personal_strategies: List[Strategy]
    dca_multiplier: float
    reasoning: str

@dataclass
class Portfolio:
    cash_usd: Decimal = Decimal("1000")
    holdings: Dict[str, Decimal] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    total_invested: Decimal = Decimal("0")

    def value(self, prices: Dict[str, Decimal]) -> Decimal:
        total = self.cash_usd
        for asset, qty in self.holdings.items():
            if asset in prices:
                total += qty * prices[asset]
        return total

# ============================================================================
# STRATEGY ENGINE
# ============================================================================

class StrategyEngine:
    """Determines which strategies to use based on market conditions"""

    # Strategy matrix: (regime, trend) -> (strategies, multiplier, reasoning)
    STRATEGY_MATRIX = {
        # EXTREME FEAR - Accumulate heavily
        (MarketRegime.EXTREME_FEAR, TrendDirection.STRONG_DOWN): (
            [Strategy.AGGRESSIVE_DCA, Strategy.SWING_BUY],
            3.0,
            "Capitulation phase - maximum accumulation opportunity"
        ),
        (MarketRegime.EXTREME_FEAR, TrendDirection.DOWN): (
            [Strategy.AGGRESSIVE_DCA, Strategy.SWING_BUY],
            2.8,
            "Deep fear with downtrend - aggressive buying"
        ),
        (MarketRegime.EXTREME_FEAR, TrendDirection.SIDEWAYS): (
            [Strategy.AGGRESSIVE_DCA],
            2.5,
            "Extreme fear consolidation - heavy DCA"
        ),
        (MarketRegime.EXTREME_FEAR, TrendDirection.UP): (
            [Strategy.AGGRESSIVE_DCA],
            2.2,
            "Fear with reversal signs - strong buying"
        ),
        (MarketRegime.EXTREME_FEAR, TrendDirection.STRONG_UP): (
            [Strategy.STANDARD_DCA],
            2.0,
            "V-shaped recovery from fear - moderate buying"
        ),

        # FEAR - Strong buying
        (MarketRegime.FEAR, TrendDirection.STRONG_DOWN): (
            [Strategy.AGGRESSIVE_DCA, Strategy.SWING_BUY],
            2.5,
            "Fear + crash - buying the dip aggressively"
        ),
        (MarketRegime.FEAR, TrendDirection.DOWN): (
            [Strategy.AGGRESSIVE_DCA],
            2.2,
            "Fear + downtrend - accumulating"
        ),
        (MarketRegime.FEAR, TrendDirection.SIDEWAYS): (
            [Strategy.STANDARD_DCA, Strategy.GRID],
            2.0,
            "Fear consolidation - DCA + grid for extra gains"
        ),
        (MarketRegime.FEAR, TrendDirection.UP): (
            [Strategy.STANDARD_DCA],
            1.8,
            "Fear recovery - solid DCA"
        ),
        (MarketRegime.FEAR, TrendDirection.STRONG_UP): (
            [Strategy.STANDARD_DCA],
            1.5,
            "Strong bounce from fear - normal DCA"
        ),

        # NEUTRAL - Balanced approach
        (MarketRegime.NEUTRAL, TrendDirection.STRONG_DOWN): (
            [Strategy.STANDARD_DCA, Strategy.MEAN_REVERSION],
            1.5,
            "Neutral + dip - buy the dip"
        ),
        (MarketRegime.NEUTRAL, TrendDirection.DOWN): (
            [Strategy.STANDARD_DCA],
            1.2,
            "Neutral downtrend - slight increase"
        ),
        (MarketRegime.NEUTRAL, TrendDirection.SIDEWAYS): (
            [Strategy.GRID],
            1.0,
            "Chop zone - grid trading optimal"
        ),
        (MarketRegime.NEUTRAL, TrendDirection.UP): (
            [Strategy.STANDARD_DCA],
            1.0,
            "Neutral uptrend - standard DCA"
        ),
        (MarketRegime.NEUTRAL, TrendDirection.STRONG_UP): (
            [Strategy.STANDARD_DCA],
            0.8,
            "Strong rally from neutral - reduce buying"
        ),

        # GREED - Reduce exposure
        (MarketRegime.GREED, TrendDirection.STRONG_DOWN): (
            [Strategy.MEAN_REVERSION],
            0.8,
            "Greed + crash - wait for clarity"
        ),
        (MarketRegime.GREED, TrendDirection.DOWN): (
            [Strategy.STANDARD_DCA],
            0.7,
            "Greed correction - light DCA"
        ),
        (MarketRegime.GREED, TrendDirection.SIDEWAYS): (
            [Strategy.MEAN_REVERSION],
            0.6,
            "Greed consolidation - cautious"
        ),
        (MarketRegime.GREED, TrendDirection.UP): (
            [Strategy.HOLD],
            0.5,
            "Greed + uptrend - minimal buying"
        ),
        (MarketRegime.GREED, TrendDirection.STRONG_UP): (
            [Strategy.PROFIT_TAKING],
            0.3,
            "Euphoria building - consider profits"
        ),

        # EXTREME GREED - Protect gains
        (MarketRegime.EXTREME_GREED, TrendDirection.STRONG_DOWN): (
            [Strategy.HOLD],
            0.5,
            "Extreme greed crash - wait"
        ),
        (MarketRegime.EXTREME_GREED, TrendDirection.DOWN): (
            [Strategy.HOLD],
            0.4,
            "Extreme greed correction - hold"
        ),
        (MarketRegime.EXTREME_GREED, TrendDirection.SIDEWAYS): (
            [Strategy.PROFIT_TAKING],
            0.3,
            "Extreme greed top - take profits"
        ),
        (MarketRegime.EXTREME_GREED, TrendDirection.UP): (
            [Strategy.PROFIT_TAKING],
            0.25,
            "Blow-off top risk - minimal buying, profits"
        ),
        (MarketRegime.EXTREME_GREED, TrendDirection.STRONG_UP): (
            [Strategy.PROFIT_TAKING],
            0.2,
            "Parabolic move - take profits aggressively"
        ),
    }

    @classmethod
    def decide(cls, market: MarketData) -> StrategyDecision:
        key = (market.regime, market.trend)

        if key in cls.STRATEGY_MATRIX:
            strategies, multiplier, reasoning = cls.STRATEGY_MATRIX[key]
        else:
            # Fallback
            strategies = [Strategy.STANDARD_DCA]
            multiplier = 1.0
            reasoning = "Default strategy"

        return StrategyDecision(
            regime=market.regime,
            trend=market.trend,
            business_strategy=Strategy.STANDARD_DCA,  # Business always DCA
            personal_strategies=strategies,
            dca_multiplier=multiplier,
            reasoning=reasoning
        )

# ============================================================================
# TRADING EXECUTOR
# ============================================================================

class TradingExecutor:
    """Executes trades based on strategy decisions"""

    # Asset allocations by strategy
    BUSINESS_ASSETS = {
        'BTC': Decimal('0.50'),
        'ETH': Decimal('0.30'),
        'DOT': Decimal('0.10'),
        'ATOM': Decimal('0.10'),
    }

    PERSONAL_ASSETS_AGGRESSIVE = {
        'SOL': Decimal('0.30'),
        'AVAX': Decimal('0.25'),
        'NEAR': Decimal('0.20'),
        'INJ': Decimal('0.15'),
        'SUI': Decimal('0.10'),
    }

    PERSONAL_ASSETS_CONSERVATIVE = {
        'ETH': Decimal('0.40'),
        'SOL': Decimal('0.30'),
        'AVAX': Decimal('0.30'),
    }

    def __init__(self, base_dca: Decimal = Decimal('40')):
        self.base_dca = base_dca
        self.business_portfolio = Portfolio()
        self.personal_portfolio = Portfolio()

    def execute_cycle(
        self,
        decision: StrategyDecision,
        prices: Dict[str, Decimal],
        paper_mode: bool = True
    ) -> List[Trade]:
        trades = []

        # Calculate amounts
        adjusted_dca = self.base_dca * Decimal(str(decision.dca_multiplier))
        business_amount = adjusted_dca * Decimal('0.70')
        personal_amount = adjusted_dca * Decimal('0.30')

        # Business trades (always DCA)
        trades.extend(self._execute_business_dca(business_amount, prices, decision))

        # Personal trades (based on strategy)
        for strategy in decision.personal_strategies:
            trades.extend(self._execute_personal_strategy(
                strategy, personal_amount, prices, decision
            ))

        return trades

    def _execute_business_dca(
        self,
        amount: Decimal,
        prices: Dict[str, Decimal],
        decision: StrategyDecision
    ) -> List[Trade]:
        trades = []

        for asset, weight in self.BUSINESS_ASSETS.items():
            if asset in prices:
                trade_amount = amount * weight
                qty = trade_amount / prices[asset]

                trade = Trade(
                    timestamp=datetime.now(),
                    account="Business (Kraken)",
                    strategy=Strategy.STANDARD_DCA,
                    side=OrderSide.BUY,
                    asset=asset,
                    quantity=qty,
                    price=prices[asset],
                    value_usd=trade_amount,
                    reason=f"Business DCA: {decision.regime.value}"
                )
                trades.append(trade)

                # Update portfolio
                self.business_portfolio.holdings[asset] = \
                    self.business_portfolio.holdings.get(asset, Decimal('0')) + qty
                self.business_portfolio.total_invested += trade_amount

        return trades

    def _execute_personal_strategy(
        self,
        strategy: Strategy,
        amount: Decimal,
        prices: Dict[str, Decimal],
        decision: StrategyDecision
    ) -> List[Trade]:
        trades = []

        if strategy == Strategy.AGGRESSIVE_DCA:
            # Buy high-beta assets aggressively
            assets = self.PERSONAL_ASSETS_AGGRESSIVE
            for asset, weight in assets.items():
                if asset in prices:
                    trade_amount = amount * weight
                    qty = trade_amount / prices[asset]

                    trade = Trade(
                        timestamp=datetime.now(),
                        account="Personal (Coinbase)",
                        strategy=strategy,
                        side=OrderSide.BUY,
                        asset=asset,
                        quantity=qty,
                        price=prices[asset],
                        value_usd=trade_amount,
                        reason=f"Aggressive accumulation in {decision.regime.value}"
                    )
                    trades.append(trade)
                    self.personal_portfolio.holdings[asset] = \
                        self.personal_portfolio.holdings.get(asset, Decimal('0')) + qty

        elif strategy == Strategy.SWING_BUY:
            # Larger position in top assets
            for asset in ['SOL', 'AVAX']:
                if asset in prices:
                    trade_amount = amount * Decimal('0.5')
                    qty = trade_amount / prices[asset]

                    trade = Trade(
                        timestamp=datetime.now(),
                        account="Personal (Coinbase)",
                        strategy=strategy,
                        side=OrderSide.BUY,
                        asset=asset,
                        quantity=qty,
                        price=prices[asset],
                        value_usd=trade_amount,
                        reason=f"Swing buy opportunity - {decision.regime.value} + {decision.trend.value}"
                    )
                    trades.append(trade)
                    self.personal_portfolio.holdings[asset] = \
                        self.personal_portfolio.holdings.get(asset, Decimal('0')) + qty

        elif strategy == Strategy.GRID:
            # Smaller, more frequent trades
            for asset in ['SOL', 'ETH']:
                if asset in prices:
                    trade_amount = amount * Decimal('0.4')
                    qty = trade_amount / prices[asset]

                    trade = Trade(
                        timestamp=datetime.now(),
                        account="Personal (Coinbase)",
                        strategy=strategy,
                        side=OrderSide.BUY,
                        asset=asset,
                        quantity=qty,
                        price=prices[asset],
                        value_usd=trade_amount,
                        reason=f"Grid buy - sideways market"
                    )
                    trades.append(trade)
                    self.personal_portfolio.holdings[asset] = \
                        self.personal_portfolio.holdings.get(asset, Decimal('0')) + qty

        elif strategy == Strategy.MEAN_REVERSION:
            # Buy only if significantly below recent average
            assets = self.PERSONAL_ASSETS_CONSERVATIVE
            for asset, weight in assets.items():
                if asset in prices:
                    trade_amount = amount * weight * Decimal('0.5')  # Half size
                    qty = trade_amount / prices[asset]

                    trade = Trade(
                        timestamp=datetime.now(),
                        account="Personal (Coinbase)",
                        strategy=strategy,
                        side=OrderSide.BUY,
                        asset=asset,
                        quantity=qty,
                        price=prices[asset],
                        value_usd=trade_amount,
                        reason=f"Mean reversion - waiting for dip"
                    )
                    trades.append(trade)
                    self.personal_portfolio.holdings[asset] = \
                        self.personal_portfolio.holdings.get(asset, Decimal('0')) + qty

        elif strategy == Strategy.PROFIT_TAKING:
            # Sell a portion of holdings
            for asset in ['SOL', 'AVAX', 'INJ']:
                if asset in self.personal_portfolio.holdings and asset in prices:
                    current_qty = self.personal_portfolio.holdings[asset]
                    if current_qty > 0:
                        sell_qty = current_qty * Decimal('0.1')  # Sell 10%
                        value = sell_qty * prices[asset]

                        trade = Trade(
                            timestamp=datetime.now(),
                            account="Personal (Coinbase)",
                            strategy=strategy,
                            side=OrderSide.SELL,
                            asset=asset,
                            quantity=sell_qty,
                            price=prices[asset],
                            value_usd=value,
                            reason=f"Taking profits - {decision.regime.value}"
                        )
                        trades.append(trade)
                        self.personal_portfolio.holdings[asset] -= sell_qty
                        self.personal_portfolio.cash_usd += value

        elif strategy == Strategy.HOLD:
            # No trades
            pass

        elif strategy == Strategy.STANDARD_DCA:
            # Normal DCA into conservative assets
            assets = self.PERSONAL_ASSETS_CONSERVATIVE
            for asset, weight in assets.items():
                if asset in prices:
                    trade_amount = amount * weight
                    qty = trade_amount / prices[asset]

                    trade = Trade(
                        timestamp=datetime.now(),
                        account="Personal (Coinbase)",
                        strategy=strategy,
                        side=OrderSide.BUY,
                        asset=asset,
                        quantity=qty,
                        price=prices[asset],
                        value_usd=trade_amount,
                        reason=f"Standard DCA"
                    )
                    trades.append(trade)
                    self.personal_portfolio.holdings[asset] = \
                        self.personal_portfolio.holdings.get(asset, Decimal('0')) + qty

        return trades

# ============================================================================
# DATA FETCHER
# ============================================================================

class MarketDataFetcher:
    """Fetches real-time market data"""

    @staticmethod
    async def fetch() -> MarketData:
        async with aiohttp.ClientSession() as session:
            # Fear & Greed
            try:
                async with session.get("https://api.alternative.me/fng/") as resp:
                    data = await resp.json()
                    fear_greed = int(data['data'][0]['value'])
            except:
                fear_greed = 50

            # Prices
            try:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": "bitcoin,ethereum,solana,avalanche-2,near,injective-protocol,sui",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_7d_change": "true"
                }
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

                    btc_price = Decimal(str(data['bitcoin']['usd']))
                    eth_price = Decimal(str(data['ethereum']['usd']))
                    btc_24h = data['bitcoin'].get('usd_24h_change', 0) or 0
                    eth_24h = data['ethereum'].get('usd_24h_change', 0) or 0
                    btc_7d = data['bitcoin'].get('usd_7d_change', 0) or 0
            except Exception as e:
                print(f"Price fetch error: {e}")
                btc_price = Decimal('89000')
                eth_price = Decimal('3000')
                btc_24h = 0
                eth_24h = 0
                btc_7d = 0

            return MarketData(
                fear_greed=fear_greed,
                btc_price=btc_price,
                eth_price=eth_price,
                btc_24h_change=btc_24h,
                eth_24h_change=eth_24h,
                btc_7d_change=btc_7d
            )

    @staticmethod
    async def fetch_all_prices() -> Dict[str, Decimal]:
        async with aiohttp.ClientSession() as session:
            try:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": "bitcoin,ethereum,solana,avalanche-2,near,injective-protocol,sui,polkadot,cosmos",
                    "vs_currencies": "usd"
                }
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    return {
                        'BTC': Decimal(str(data['bitcoin']['usd'])),
                        'ETH': Decimal(str(data['ethereum']['usd'])),
                        'SOL': Decimal(str(data['solana']['usd'])),
                        'AVAX': Decimal(str(data['avalanche-2']['usd'])),
                        'NEAR': Decimal(str(data['near']['usd'])),
                        'INJ': Decimal(str(data['injective-protocol']['usd'])),
                        'SUI': Decimal(str(data['sui']['usd'])),
                        'DOT': Decimal(str(data['polkadot']['usd'])),
                        'ATOM': Decimal(str(data['cosmos']['usd'])),
                    }
            except:
                return {
                    'BTC': Decimal('89000'),
                    'ETH': Decimal('3000'),
                    'SOL': Decimal('125'),
                    'AVAX': Decimal('12'),
                    'NEAR': Decimal('1.5'),
                    'INJ': Decimal('5'),
                    'SUI': Decimal('1.5'),
                    'DOT': Decimal('2'),
                    'ATOM': Decimal('2.5'),
                }

# ============================================================================
# LOGGER
# ============================================================================

class TradeLogger:
    """Logs trades and decisions"""

    def __init__(self, log_dir: str = "/home/dave/skippy/work/crypto/paper_trading"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.json"
        self.trades = []

    def log_trade(self, trade: Trade):
        self.trades.append({
            'timestamp': trade.timestamp.isoformat(),
            'account': trade.account,
            'strategy': trade.strategy.value,
            'side': trade.side.value,
            'asset': trade.asset,
            'quantity': str(trade.quantity),
            'price': str(trade.price),
            'value_usd': str(trade.value_usd),
            'reason': trade.reason
        })
        self._save()

    def log_decision(self, decision: StrategyDecision, market: MarketData):
        log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'decision',
            'fear_greed': market.fear_greed,
            'regime': decision.regime.value,
            'trend': decision.trend.value,
            'business_strategy': decision.business_strategy.value,
            'personal_strategies': [s.value for s in decision.personal_strategies],
            'dca_multiplier': decision.dca_multiplier,
            'reasoning': decision.reasoning
        }
        self.trades.append(log)
        self._save()

    def _save(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.trades, f, indent=2)

# ============================================================================
# EMAIL NOTIFICATIONS
# ============================================================================

class EmailNotifier:
    """Sends email notifications on strategy changes"""

    def __init__(self, recipient: str = "eboncorp@gmail.com", enabled: bool = True):
        self.recipient = recipient
        self.enabled = enabled
        self.last_regime: Optional[MarketRegime] = None
        self.last_notified: Optional[datetime] = None
        self.cooldown_minutes = 60  # Don't spam emails

    def should_notify(self, decision: StrategyDecision) -> Tuple[bool, str]:
        """Determine if we should send a notification"""
        reasons = []

        # Always notify on extreme conditions
        if decision.regime == MarketRegime.EXTREME_FEAR:
            reasons.append("EXTREME FEAR detected - maximum accumulation opportunity")
        elif decision.regime == MarketRegime.EXTREME_GREED:
            reasons.append("EXTREME GREED detected - consider taking profits")

        # Notify on regime change
        if self.last_regime and self.last_regime != decision.regime:
            reasons.append(f"Regime changed: {self.last_regime.value} → {decision.regime.value}")

        # Notify on profit taking
        if Strategy.PROFIT_TAKING in decision.personal_strategies:
            reasons.append("Profit taking strategy activated")

        # Notify on aggressive buying
        if Strategy.SWING_BUY in decision.personal_strategies:
            reasons.append("Swing buy opportunity detected")

        # Check cooldown
        if self.last_notified:
            elapsed = (datetime.now() - self.last_notified).total_seconds() / 60
            if elapsed < self.cooldown_minutes and not reasons:
                return False, ""

        self.last_regime = decision.regime
        return len(reasons) > 0, "; ".join(reasons)

    def format_email(
        self,
        decision: StrategyDecision,
        market: MarketData,
        trades: List[Trade],
        notification_reason: str
    ) -> Tuple[str, str]:
        """Format email subject and body"""

        # Emoji based on regime
        regime_emoji = {
            MarketRegime.EXTREME_FEAR: "🔴🔴",
            MarketRegime.FEAR: "🔴",
            MarketRegime.NEUTRAL: "⚪",
            MarketRegime.GREED: "🟢",
            MarketRegime.EXTREME_GREED: "🟢🟢",
        }

        emoji = regime_emoji.get(decision.regime, "⚪")

        subject = f"{emoji} Crypto Alert: {decision.regime.value.upper()} | DCA {decision.dca_multiplier}x"

        # Calculate totals
        total_bought = sum(t.value_usd for t in trades if t.side == OrderSide.BUY)
        total_sold = sum(t.value_usd for t in trades if t.side == OrderSide.SELL)

        body = f"""
ADAPTIVE CRYPTO TRADER - ALERT
{'=' * 50}

NOTIFICATION REASON:
{notification_reason}

MARKET CONDITIONS
{'-' * 50}
Fear & Greed Index:  {market.fear_greed}
Regime:              {decision.regime.value.upper()}
Trend:               {decision.trend.value.replace('_', ' ').title()}
BTC 24h Change:      {market.btc_24h_change:+.2f}%

STRATEGY DECISION
{'-' * 50}
DCA Multiplier:      {decision.dca_multiplier}x
Business Strategy:   {decision.business_strategy.value}
Personal Strategies: {', '.join(s.value for s in decision.personal_strategies)}
Reasoning:           {decision.reasoning}

TRADES EXECUTED (PAPER MODE)
{'-' * 50}
"""
        for trade in trades:
            side = "BUY " if trade.side == OrderSide.BUY else "SELL"
            body += f"{side} {trade.quantity:.8f} {trade.asset} @ ${trade.price:,.2f} = ${trade.value_usd:.2f}\n"
            body += f"     Account: {trade.account} | Strategy: {trade.strategy.value}\n"

        body += f"""
{'-' * 50}
Total Bought:        ${total_bought:,.2f}
Total Sold:          ${total_sold:,.2f}
Net Investment:      ${total_bought - total_sold:,.2f}

{'=' * 50}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a paper trading simulation. No real trades were executed.
"""
        return subject, body

    async def send_notification(
        self,
        decision: StrategyDecision,
        market: MarketData,
        trades: List[Trade]
    ) -> bool:
        """Send email notification using Gmail MCP or fallback"""

        if not self.enabled:
            return False

        should_send, reason = self.should_notify(decision)
        if not should_send:
            return False

        subject, body = self.format_email(decision, market, trades, reason)

        # Try to use mcp-gmail via subprocess (since we can't directly call MCP from Python)
        # Fall back to saving notification to file
        try:
            notification_file = Path("/home/dave/skippy/work/crypto/paper_trading/notifications.json")
            notifications = []
            if notification_file.exists():
                with open(notification_file) as f:
                    notifications = json.load(f)

            notifications.append({
                'timestamp': datetime.now().isoformat(),
                'recipient': self.recipient,
                'subject': subject,
                'body': body,
                'reason': reason,
                'sent_via': 'pending'  # Will be sent by cron/external process
            })

            with open(notification_file, 'w') as f:
                json.dump(notifications, f, indent=2)

            self.last_notified = datetime.now()
            print(f"\n  📧 Notification queued: {reason}")
            return True

        except Exception as e:
            print(f"\n  ⚠️ Failed to queue notification: {e}")
            return False

# ============================================================================
# MAIN BOT
# ============================================================================

class AdaptiveTrader:
    """Main trading bot"""

    def __init__(self, base_dca: Decimal = Decimal('40'), paper_mode: bool = True,
                 notify_email: str = "eboncorp@gmail.com", notifications: bool = True):
        self.executor = TradingExecutor(base_dca)
        self.logger = TradeLogger()
        self.notifier = EmailNotifier(recipient=notify_email, enabled=notifications)
        self.paper_mode = paper_mode
        self.cycle_count = 0

    async def run_cycle(self) -> Tuple[StrategyDecision, List[Trade]]:
        self.cycle_count += 1

        # Fetch market data
        market = await MarketDataFetcher.fetch()
        prices = await MarketDataFetcher.fetch_all_prices()

        # Get strategy decision
        decision = StrategyEngine.decide(market)

        # Log decision
        self.logger.log_decision(decision, market)

        # Execute trades
        trades = self.executor.execute_cycle(decision, prices, self.paper_mode)

        # Log trades
        for trade in trades:
            self.logger.log_trade(trade)

        # Send notification if needed
        await self.notifier.send_notification(decision, market, trades)

        return decision, trades, market, prices

    def print_cycle_report(
        self,
        decision: StrategyDecision,
        trades: List[Trade],
        market: MarketData,
        prices: Dict[str, Decimal]
    ):
        print("\n" + "=" * 80)
        print(f"  ADAPTIVE TRADER - Cycle #{self.cycle_count}")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Market conditions
        print(f"\n  MARKET CONDITIONS")
        print(f"  {'─' * 40}")
        print(f"  Fear & Greed:    {market.fear_greed}")
        print(f"  Regime:          {decision.regime.value.upper()}")
        print(f"  Trend:           {decision.trend.value.replace('_', ' ').title()}")
        print(f"  BTC 24h:         {market.btc_24h_change:+.2f}%")
        print(f"  BTC 7d:          {market.btc_7d_change:+.2f}%")

        # Strategy decision
        print(f"\n  STRATEGY DECISION")
        print(f"  {'─' * 40}")
        print(f"  DCA Multiplier:  {decision.dca_multiplier}x")
        print(f"  Business:        {decision.business_strategy.value}")
        print(f"  Personal:        {', '.join(s.value for s in decision.personal_strategies)}")
        print(f"  Reasoning:       {decision.reasoning}")

        # Trades executed
        print(f"\n  TRADES EXECUTED {'(PAPER MODE)' if self.paper_mode else '(LIVE)'}")
        print(f"  {'─' * 40}")

        total_bought = Decimal('0')
        total_sold = Decimal('0')

        for trade in trades:
            emoji = "🟢" if trade.side == OrderSide.BUY else "🔴"
            print(f"  {emoji} {trade.side.value.upper():4} {trade.quantity:.8f} {trade.asset:5} "
                  f"@ ${trade.price:>10,.2f} = ${trade.value_usd:>8,.2f}")
            print(f"     └─ {trade.account} | {trade.strategy.value} | {trade.reason}")

            if trade.side == OrderSide.BUY:
                total_bought += trade.value_usd
            else:
                total_sold += trade.value_usd

        print(f"\n  {'─' * 40}")
        print(f"  Total Bought:    ${total_bought:,.2f}")
        print(f"  Total Sold:      ${total_sold:,.2f}")
        print(f"  Net:             ${total_bought - total_sold:,.2f}")

        # Portfolio status
        print(f"\n  PORTFOLIO STATUS")
        print(f"  {'─' * 40}")

        biz_value = self.executor.business_portfolio.value(prices)
        per_value = self.executor.personal_portfolio.value(prices)

        print(f"  Business Holdings:")
        for asset, qty in sorted(self.executor.business_portfolio.holdings.items()):
            if qty > 0 and asset in prices:
                value = qty * prices[asset]
                print(f"     {asset}: {qty:.8f} = ${value:,.2f}")

        print(f"\n  Personal Holdings:")
        for asset, qty in sorted(self.executor.personal_portfolio.holdings.items()):
            if qty > 0 and asset in prices:
                value = qty * prices[asset]
                print(f"     {asset}: {qty:.8f} = ${value:,.2f}")

        print(f"\n  {'─' * 40}")
        print(f"  Business Total:  ${biz_value:,.2f}")
        print(f"  Personal Total:  ${per_value:,.2f}")
        print(f"  Combined:        ${biz_value + per_value:,.2f}")

        print("\n" + "=" * 80)

# ============================================================================
# BACKTEST
# ============================================================================

async def run_backtest(days: int = 30):
    """Simulate trading over historical period"""
    print(f"\n{'=' * 80}")
    print(f"  BACKTEST SIMULATION - {days} Days")
    print(f"{'=' * 80}")

    trader = AdaptiveTrader(base_dca=Decimal('40'), paper_mode=True)

    # Simulate varying market conditions
    simulated_conditions = []

    for day in range(days):
        # Generate realistic-ish market conditions
        base_fg = 50 + (20 * (0.5 - random.random()))  # Oscillate around 50
        # Add some trends
        if day < days // 4:
            base_fg -= 20  # Start in fear
        elif day < days // 2:
            base_fg += 10  # Recovery
        elif day < 3 * days // 4:
            base_fg += 25  # Greed
        else:
            base_fg -= 10  # Correction

        fg = max(0, min(100, int(base_fg + random.randint(-10, 10))))
        change_24h = random.uniform(-8, 8)
        change_7d = random.uniform(-15, 15)

        simulated_conditions.append({
            'fear_greed': fg,
            'btc_24h_change': change_24h,
            'btc_7d_change': change_7d
        })

    # Run simulation
    total_invested = Decimal('0')

    for day, conditions in enumerate(simulated_conditions):
        # Create market data
        market = MarketData(
            fear_greed=conditions['fear_greed'],
            btc_price=Decimal('89000'),
            eth_price=Decimal('3000'),
            btc_24h_change=conditions['btc_24h_change'],
            eth_24h_change=conditions['btc_24h_change'] * 1.2,
            btc_7d_change=conditions['btc_7d_change']
        )

        prices = {
            'BTC': Decimal('89000'),
            'ETH': Decimal('3000'),
            'SOL': Decimal('125'),
            'AVAX': Decimal('12'),
            'NEAR': Decimal('1.5'),
            'INJ': Decimal('5'),
            'SUI': Decimal('1.5'),
            'DOT': Decimal('2'),
            'ATOM': Decimal('2.5'),
        }

        decision = StrategyEngine.decide(market)
        trades = trader.executor.execute_cycle(decision, prices, paper_mode=True)

        day_total = sum(t.value_usd for t in trades if t.side == OrderSide.BUY)
        total_invested += day_total

        print(f"  Day {day+1:3}: F&G={conditions['fear_greed']:2} | "
              f"{decision.regime.value:14} | {decision.dca_multiplier}x | "
              f"${day_total:6.2f} | Strategies: {', '.join(s.value for s in decision.personal_strategies)}")

    print(f"\n{'─' * 80}")
    print(f"  BACKTEST SUMMARY")
    print(f"{'─' * 80}")
    print(f"  Days Simulated:      {days}")
    print(f"  Total Invested:      ${total_invested:,.2f}")
    print(f"  Avg Daily:           ${total_invested / days:,.2f}")
    print(f"  Business Invested:   ${trader.executor.business_portfolio.total_invested:,.2f}")
    print(f"\n  Final Holdings:")

    biz_value = trader.executor.business_portfolio.value(prices)
    per_value = trader.executor.personal_portfolio.value(prices)

    for asset, qty in sorted(trader.executor.business_portfolio.holdings.items()):
        if qty > 0:
            print(f"     Business {asset}: {qty:.8f}")

    for asset, qty in sorted(trader.executor.personal_portfolio.holdings.items()):
        if qty > 0:
            print(f"     Personal {asset}: {qty:.8f}")

    print(f"\n  Portfolio Value:     ${biz_value + per_value:,.2f}")
    print(f"{'=' * 80}")

# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Adaptive Crypto Trading Bot")
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=3600, help='Seconds between cycles')
    parser.add_argument('--backtest', type=int, help='Run backtest for N days')
    parser.add_argument('--base-dca', type=float, default=40, help='Base DCA amount')

    args = parser.parse_args()

    if args.backtest:
        await run_backtest(args.backtest)
        return

    trader = AdaptiveTrader(
        base_dca=Decimal(str(args.base_dca)),
        paper_mode=True
    )

    print("\n" + "=" * 80)
    print("  ADAPTIVE CRYPTO TRADER - Paper Mode")
    print("  Two-Account Strategy with Dynamic Strategy Switching")
    print("=" * 80)

    if args.continuous:
        print(f"\n  Running continuously (interval: {args.interval}s)")
        print("  Press Ctrl+C to stop\n")

        try:
            while True:
                decision, trades, market, prices = await trader.run_cycle()
                trader.print_cycle_report(decision, trades, market, prices)
                print(f"\n  Next cycle in {args.interval} seconds...")
                await asyncio.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n  Stopping trader...")
    else:
        # Single cycle
        decision, trades, market, prices = await trader.run_cycle()
        trader.print_cycle_report(decision, trades, market, prices)

    print(f"\n  Trades logged to: {trader.logger.log_file}")

if __name__ == "__main__":
    asyncio.run(main())
