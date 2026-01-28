"""
Advanced Market Signals Module

Multi-factor analysis for smarter dip buying:
1. Technical indicators (RSI, Moving Averages, Bollinger Bands)
2. On-chain metrics (Exchange flows, whale movements)
3. Derivatives data (Funding rates, liquidations)
4. Macro conditions (DXY, risk sentiment)
5. Relative strength (BTC dominance, asset comparison)

Each signal contributes to an overall "opportunity score" that
adjusts DCA multipliers more intelligently than price alone.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import aiohttp
import statistics

from data.prices import PriceService


class SignalStrength(Enum):
    """Strength of a buy/sell signal."""
    STRONG_SELL = -2
    SELL = -1
    NEUTRAL = 0
    BUY = 1
    STRONG_BUY = 2


@dataclass
class Signal:
    """A single market signal."""
    name: str
    category: str
    value: float
    signal: SignalStrength
    weight: float = 1.0
    description: str = ""
    source: str = ""
    
    @property
    def weighted_score(self) -> float:
        return self.signal.value * self.weight


@dataclass
class TechnicalIndicators:
    """Technical analysis indicators for an asset."""
    asset: str
    price: Decimal
    rsi_14: Optional[float] = None
    rsi_signal: SignalStrength = SignalStrength.NEUTRAL
    
    sma_50: Optional[Decimal] = None
    sma_200: Optional[Decimal] = None
    price_vs_sma200: Optional[float] = None  # % above/below
    ma_signal: SignalStrength = SignalStrength.NEUTRAL
    
    bb_upper: Optional[Decimal] = None
    bb_lower: Optional[Decimal] = None
    bb_position: Optional[float] = None  # 0 = at lower, 1 = at upper
    bb_signal: SignalStrength = SignalStrength.NEUTRAL
    
    volume_24h: Optional[Decimal] = None
    volume_avg_7d: Optional[Decimal] = None
    volume_signal: SignalStrength = SignalStrength.NEUTRAL


@dataclass
class OnChainMetrics:
    """On-chain data for an asset."""
    asset: str
    
    # Exchange flows
    exchange_inflow_24h: Optional[Decimal] = None
    exchange_outflow_24h: Optional[Decimal] = None
    net_flow: Optional[Decimal] = None  # Negative = outflow (bullish)
    exchange_flow_signal: SignalStrength = SignalStrength.NEUTRAL
    
    # Active addresses
    active_addresses_24h: Optional[int] = None
    active_addresses_7d_avg: Optional[int] = None
    address_signal: SignalStrength = SignalStrength.NEUTRAL
    
    # Whale activity
    whale_transactions_24h: Optional[int] = None  # Transactions > $100k
    whale_signal: SignalStrength = SignalStrength.NEUTRAL


@dataclass
class DerivativesData:
    """Derivatives market data."""
    asset: str
    
    # Funding rates
    funding_rate: Optional[float] = None  # Negative = shorts paying
    funding_signal: SignalStrength = SignalStrength.NEUTRAL
    
    # Open interest
    open_interest: Optional[Decimal] = None
    oi_change_24h: Optional[float] = None
    oi_signal: SignalStrength = SignalStrength.NEUTRAL
    
    # Liquidations
    long_liquidations_24h: Optional[Decimal] = None
    short_liquidations_24h: Optional[Decimal] = None
    liquidation_signal: SignalStrength = SignalStrength.NEUTRAL


@dataclass
class MacroConditions:
    """Macro market conditions."""
    # Dollar index
    dxy_value: Optional[float] = None
    dxy_change_7d: Optional[float] = None
    dxy_signal: SignalStrength = SignalStrength.NEUTRAL
    
    # Market sentiment
    vix_value: Optional[float] = None  # Fear index
    vix_signal: SignalStrength = SignalStrength.NEUTRAL
    
    # Crypto-specific
    total_market_cap: Optional[Decimal] = None
    market_cap_change_24h: Optional[float] = None
    
    btc_dominance: Optional[float] = None
    btc_dominance_change_7d: Optional[float] = None
    dominance_signal: SignalStrength = SignalStrength.NEUTRAL
    
    # Stablecoin supply (dry powder)
    stablecoin_supply: Optional[Decimal] = None
    stablecoin_change_7d: Optional[float] = None


@dataclass
class OpportunityScore:
    """Combined opportunity score from all signals."""
    timestamp: datetime
    asset: str
    
    # Individual scores by category
    technical_score: float = 0
    onchain_score: float = 0
    derivatives_score: float = 0
    macro_score: float = 0
    sentiment_score: float = 0
    
    # Weights for each category
    technical_weight: float = 0.25
    onchain_weight: float = 0.20
    derivatives_weight: float = 0.20
    macro_weight: float = 0.15
    sentiment_weight: float = 0.20
    
    # All signals
    signals: List[Signal] = field(default_factory=list)
    
    @property
    def total_score(self) -> float:
        """Calculate weighted total score (-10 to +10 scale)."""
        return (
            self.technical_score * self.technical_weight +
            self.onchain_score * self.onchain_weight +
            self.derivatives_score * self.derivatives_weight +
            self.macro_score * self.macro_weight +
            self.sentiment_score * self.sentiment_weight
        )
    
    @property
    def normalized_score(self) -> float:
        """Normalize to 0-100 scale where 50 is neutral."""
        # Total score ranges from -10 to +10
        # Map to 0-100
        return (self.total_score + 10) * 5
    
    @property
    def recommendation(self) -> str:
        score = self.total_score
        if score >= 6:
            return "STRONG_BUY"
        elif score >= 3:
            return "BUY"
        elif score >= -3:
            return "NEUTRAL"
        elif score >= -6:
            return "REDUCE"
        else:
            return "STRONG_REDUCE"
    
    @property
    def dca_multiplier(self) -> float:
        """Convert score to DCA multiplier."""
        score = self.total_score
        
        if score >= 6:
            return 2.5   # Strong buy
        elif score >= 4:
            return 2.0
        elif score >= 2:
            return 1.5
        elif score >= 0:
            return 1.25
        elif score >= -2:
            return 1.0   # Neutral
        elif score >= -4:
            return 0.85
        else:
            return 0.70  # Strong reduce


class MarketSignalsAnalyzer:
    """Analyzes multiple market signals to generate opportunity scores."""
    
    COINGECKO_URL = "https://api.coingecko.com/api/v3"
    ALTERNATIVE_ME_URL = "https://api.alternative.me"
    
    def __init__(self, price_service: Optional[PriceService] = None):
        self.price_service = price_service or PriceService()
        self._session: Optional[aiohttp.ClientSession] = None
        self._price_history: Dict[str, List[Tuple[datetime, Decimal]]] = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    # =========================================================================
    # TECHNICAL INDICATORS
    # =========================================================================
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI from price history."""
        if len(prices) < period + 1:
            return None
        
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        recent_changes = changes[-(period):]
        
        gains = [c for c in recent_changes if c > 0]
        losses = [-c for c in recent_changes if c < 0]
        
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0.0001
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def calculate_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Optional[Tuple[float, float, float]]:
        """Calculate Bollinger Bands (upper, middle, lower)."""
        if len(prices) < period:
            return None
        
        recent = prices[-period:]
        middle = sum(recent) / period
        std = statistics.stdev(recent)
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    async def get_technical_indicators(self, asset: str) -> TechnicalIndicators:
        """Get technical indicators for an asset."""
        # Get price history from CoinGecko
        session = await self._get_session()
        
        symbol_to_id = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "DOT": "polkadot", "AVAX": "avalanche-2", "ATOM": "cosmos",
            "TIA": "celestia", "INJ": "injective-protocol", "NEAR": "near",
            "SUI": "sui",
        }
        
        coin_id = symbol_to_id.get(asset.upper(), asset.lower())
        
        try:
            url = f"{self.COINGECKO_URL}/coins/{coin_id}/market_chart"
            params = {"vs_currency": "usd", "days": 200}
            
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                prices = [p[1] for p in data.get("prices", [])]
                volumes = [v[1] for v in data.get("total_volumes", [])]
        except:
            prices = []
            volumes = []
        
        current_price = Decimal(str(prices[-1])) if prices else Decimal("0")
        
        indicators = TechnicalIndicators(asset=asset, price=current_price)
        
        if len(prices) >= 15:
            # RSI
            rsi = self.calculate_rsi(prices)
            if rsi:
                indicators.rsi_14 = rsi
                if rsi < 30:
                    indicators.rsi_signal = SignalStrength.STRONG_BUY
                elif rsi < 40:
                    indicators.rsi_signal = SignalStrength.BUY
                elif rsi > 70:
                    indicators.rsi_signal = SignalStrength.STRONG_SELL
                elif rsi > 60:
                    indicators.rsi_signal = SignalStrength.SELL
        
        if len(prices) >= 200:
            # Moving averages
            sma_50 = self.calculate_sma(prices, 50)
            sma_200 = self.calculate_sma(prices, 200)
            
            if sma_50:
                indicators.sma_50 = Decimal(str(sma_50))
            if sma_200:
                indicators.sma_200 = Decimal(str(sma_200))
                price_vs_200 = (prices[-1] - sma_200) / sma_200 * 100
                indicators.price_vs_sma200 = price_vs_200
                
                if price_vs_200 < -30:
                    indicators.ma_signal = SignalStrength.STRONG_BUY
                elif price_vs_200 < -15:
                    indicators.ma_signal = SignalStrength.BUY
                elif price_vs_200 > 50:
                    indicators.ma_signal = SignalStrength.SELL
        
        if len(prices) >= 20:
            # Bollinger Bands
            bb = self.calculate_bollinger_bands(prices)
            if bb:
                upper, middle, lower = bb
                indicators.bb_upper = Decimal(str(upper))
                indicators.bb_lower = Decimal(str(lower))
                
                if upper != lower:
                    position = (prices[-1] - lower) / (upper - lower)
                    indicators.bb_position = position
                    
                    if position < 0.1:
                        indicators.bb_signal = SignalStrength.STRONG_BUY
                    elif position < 0.25:
                        indicators.bb_signal = SignalStrength.BUY
                    elif position > 0.9:
                        indicators.bb_signal = SignalStrength.STRONG_SELL
                    elif position > 0.75:
                        indicators.bb_signal = SignalStrength.SELL
        
        if len(volumes) >= 7:
            # Volume analysis
            indicators.volume_24h = Decimal(str(volumes[-1]))
            avg_volume = sum(volumes[-7:]) / 7
            indicators.volume_avg_7d = Decimal(str(avg_volume))
            
            # High volume on down days = capitulation (bullish)
            if volumes[-1] > avg_volume * 2 and prices[-1] < prices[-2]:
                indicators.volume_signal = SignalStrength.BUY
        
        return indicators
    
    # =========================================================================
    # FEAR & GREED + SENTIMENT
    # =========================================================================
    
    async def get_fear_greed(self) -> Tuple[int, str, SignalStrength]:
        """Get Fear & Greed Index."""
        session = await self._get_session()
        
        try:
            url = f"{self.ALTERNATIVE_ME_URL}/fng/"
            async with session.get(url) as resp:
                data = await resp.json()
                
                if data.get("data"):
                    value = int(data["data"][0]["value"])
                    label = data["data"][0]["value_classification"]
                    
                    if value <= 20:
                        signal = SignalStrength.STRONG_BUY
                    elif value <= 35:
                        signal = SignalStrength.BUY
                    elif value >= 80:
                        signal = SignalStrength.STRONG_SELL
                    elif value >= 65:
                        signal = SignalStrength.SELL
                    else:
                        signal = SignalStrength.NEUTRAL
                    
                    return value, label, signal
        except:
            pass
        
        return 50, "Neutral", SignalStrength.NEUTRAL
    
    # =========================================================================
    # MACRO CONDITIONS
    # =========================================================================
    
    async def get_macro_conditions(self) -> MacroConditions:
        """Get macro market conditions."""
        session = await self._get_session()
        macro = MacroConditions()
        
        # Get global crypto data
        try:
            url = f"{self.COINGECKO_URL}/global"
            async with session.get(url) as resp:
                data = await resp.json()
                global_data = data.get("data", {})
                
                macro.total_market_cap = Decimal(str(
                    global_data.get("total_market_cap", {}).get("usd", 0)
                ))
                macro.market_cap_change_24h = global_data.get(
                    "market_cap_change_percentage_24h_usd", 0
                )
                macro.btc_dominance = global_data.get(
                    "market_cap_percentage", {}
                ).get("btc", 0)
        except:
            pass
        
        # BTC dominance signal
        # Rising dominance in downtrend = risk-off (alts will suffer more)
        # Falling dominance = alt season potential
        if macro.btc_dominance:
            if macro.btc_dominance > 55:
                macro.dominance_signal = SignalStrength.SELL  # Alts risky
            elif macro.btc_dominance < 45:
                macro.dominance_signal = SignalStrength.BUY   # Alt season
        
        return macro
    
    # =========================================================================
    # COMBINED ANALYSIS
    # =========================================================================
    
    async def analyze_asset(self, asset: str) -> OpportunityScore:
        """Generate full opportunity score for an asset."""
        signals = []
        
        # Get all data concurrently
        tech_task = self.get_technical_indicators(asset)
        fg_task = self.get_fear_greed()
        macro_task = self.get_macro_conditions()
        
        tech, fg_data, macro = await asyncio.gather(
            tech_task, fg_task, macro_task,
            return_exceptions=True,
        )
        
        # Process technical indicators
        technical_score = 0
        if isinstance(tech, TechnicalIndicators):
            if tech.rsi_signal != SignalStrength.NEUTRAL:
                signals.append(Signal(
                    name="RSI (14)",
                    category="technical",
                    value=tech.rsi_14 or 50,
                    signal=tech.rsi_signal,
                    weight=1.5,
                    description=f"RSI at {tech.rsi_14:.1f}" if tech.rsi_14 else "",
                ))
                technical_score += tech.rsi_signal.value * 1.5
            
            if tech.ma_signal != SignalStrength.NEUTRAL:
                signals.append(Signal(
                    name="Price vs 200 SMA",
                    category="technical",
                    value=tech.price_vs_sma200 or 0,
                    signal=tech.ma_signal,
                    weight=1.2,
                    description=f"{tech.price_vs_sma200:.1f}% from 200 SMA" if tech.price_vs_sma200 else "",
                ))
                technical_score += tech.ma_signal.value * 1.2
            
            if tech.bb_signal != SignalStrength.NEUTRAL:
                signals.append(Signal(
                    name="Bollinger Position",
                    category="technical",
                    value=tech.bb_position or 0.5,
                    signal=tech.bb_signal,
                    weight=1.0,
                    description=f"At {tech.bb_position:.0%} of bands" if tech.bb_position else "",
                ))
                technical_score += tech.bb_signal.value * 1.0
            
            if tech.volume_signal != SignalStrength.NEUTRAL:
                signals.append(Signal(
                    name="Volume Spike",
                    category="technical",
                    value=float(tech.volume_24h) if tech.volume_24h else 0,
                    signal=tech.volume_signal,
                    weight=0.8,
                    description="High volume on down day (capitulation)",
                ))
                technical_score += tech.volume_signal.value * 0.8
        
        # Process Fear & Greed
        sentiment_score = 0
        if isinstance(fg_data, tuple):
            fg_value, fg_label, fg_signal = fg_data
            signals.append(Signal(
                name="Fear & Greed Index",
                category="sentiment",
                value=fg_value,
                signal=fg_signal,
                weight=2.0,
                description=f"{fg_value} ({fg_label})",
            ))
            sentiment_score += fg_signal.value * 2.0
        
        # Process macro
        macro_score = 0
        if isinstance(macro, MacroConditions):
            if macro.dominance_signal != SignalStrength.NEUTRAL:
                signals.append(Signal(
                    name="BTC Dominance",
                    category="macro",
                    value=macro.btc_dominance or 50,
                    signal=macro.dominance_signal,
                    weight=1.0,
                    description=f"BTC dominance at {macro.btc_dominance:.1f}%",
                ))
                macro_score += macro.dominance_signal.value * 1.0
        
        # Normalize scores to -10 to +10 scale
        max_tech = 4.5  # Sum of weights
        max_sentiment = 2.0
        max_macro = 1.0
        
        return OpportunityScore(
            timestamp=datetime.now(),
            asset=asset,
            technical_score=(technical_score / max_tech) * 10 if max_tech > 0 else 0,
            sentiment_score=(sentiment_score / max_sentiment) * 10 if max_sentiment > 0 else 0,
            macro_score=(macro_score / max_macro) * 10 if max_macro > 0 else 0,
            signals=signals,
        )
    
    async def analyze_portfolio(
        self,
        assets: List[str],
    ) -> Dict[str, OpportunityScore]:
        """Analyze all portfolio assets."""
        tasks = [self.analyze_asset(asset) for asset in assets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scores = {}
        for asset, result in zip(assets, results):
            if isinstance(result, OpportunityScore):
                scores[asset] = result
        
        return scores
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


def format_opportunity_score(score: OpportunityScore) -> str:
    """Format opportunity score for display."""
    lines = []
    
    # Recommendation color/emoji
    rec_emoji = {
        "STRONG_BUY": "💎",
        "BUY": "🟢",
        "NEUTRAL": "⚪",
        "REDUCE": "🟡",
        "STRONG_REDUCE": "🔴",
    }
    
    emoji = rec_emoji.get(score.recommendation, "⚪")
    
    lines.append(f"\n  {score.asset} Opportunity Score")
    lines.append("  " + "=" * 50)
    lines.append(f"  {emoji} Recommendation: {score.recommendation}")
    lines.append(f"  DCA Multiplier: {score.dca_multiplier:.2f}x")
    lines.append(f"  Total Score: {score.total_score:.1f} / 10")
    lines.append(f"  Normalized: {score.normalized_score:.0f} / 100")
    lines.append("")
    
    # Category breakdown
    lines.append("  Category Scores:")
    lines.append(f"    Technical:  {score.technical_score:>+6.1f}")
    lines.append(f"    Sentiment:  {score.sentiment_score:>+6.1f}")
    lines.append(f"    Macro:      {score.macro_score:>+6.1f}")
    lines.append(f"    On-chain:   {score.onchain_score:>+6.1f}")
    lines.append(f"    Derivatives:{score.derivatives_score:>+6.1f}")
    lines.append("")
    
    # Individual signals
    if score.signals:
        lines.append("  Signals:")
        for signal in score.signals:
            signal_emoji = {
                SignalStrength.STRONG_BUY: "🟢🟢",
                SignalStrength.BUY: "🟢",
                SignalStrength.NEUTRAL: "⚪",
                SignalStrength.SELL: "🔴",
                SignalStrength.STRONG_SELL: "🔴🔴",
            }[signal.signal]
            
            lines.append(f"    {signal_emoji} {signal.name}: {signal.description}")
    
    return "\n".join(lines)


# Convenience function
async def get_opportunity_score(asset: str) -> OpportunityScore:
    """Quick function to get opportunity score for an asset."""
    analyzer = MarketSignalsAnalyzer()
    try:
        return await analyzer.analyze_asset(asset)
    finally:
        await analyzer.close()
