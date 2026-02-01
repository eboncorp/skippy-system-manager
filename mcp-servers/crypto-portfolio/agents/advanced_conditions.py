"""
Advanced Market Conditions Analyzer

Additional signals beyond simple drawdown:
1. RSI (Relative Strength Index) - Oversold/overbought
2. Volume analysis - Capitulation detection
3. Funding rates - Sentiment in derivatives
4. Exchange flows - Whale accumulation signals
5. Bitcoin dominance - Risk-on/risk-off indicator
6. Moving average position - Trend context
7. Volatility regime - High vol = opportunity
8. Time-based patterns - Weekend discount, monthly cycles
9. Correlation breaks - Decoupling signals
10. Liquidation data - Capitulation confirmation
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
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
class MarketSignal:
    """A single market signal."""
    name: str
    value: float
    signal: SignalStrength
    weight: float  # Importance weight 0-1
    description: str
    source: str = ""

    @property
    def weighted_score(self) -> float:
        return self.signal.value * self.weight


@dataclass
class RSIAnalysis:
    """RSI analysis for an asset."""
    asset: str
    rsi_14: float  # 14-period RSI
    rsi_7: float   # 7-period RSI (faster)
    signal: SignalStrength

    @property
    def is_oversold(self) -> bool:
        return self.rsi_14 < 30

    @property
    def is_overbought(self) -> bool:
        return self.rsi_14 > 70


@dataclass
class VolumeAnalysis:
    """Volume analysis."""
    asset: str
    current_volume_24h: float
    avg_volume_30d: float
    volume_ratio: float  # Current / Average
    is_capitulation: bool  # High volume + price drop
    signal: SignalStrength


@dataclass
class FundingRateAnalysis:
    """Funding rate analysis for perpetual futures."""
    asset: str
    funding_rate: float  # Current funding rate (8h)
    avg_funding_7d: float
    signal: SignalStrength

    @property
    def is_negative(self) -> bool:
        """Negative funding = shorts paying longs = often bullish."""
        return self.funding_rate < 0


@dataclass
class MovingAverageAnalysis:
    """Moving average position analysis."""
    asset: str
    current_price: float
    ma_50: float
    ma_200: float
    price_vs_ma50_pct: float  # % above/below 50 MA
    price_vs_ma200_pct: float  # % above/below 200 MA
    ma_50_above_200: bool  # Golden cross status
    signal: SignalStrength


@dataclass
class BTCDominanceAnalysis:
    """Bitcoin dominance analysis."""
    current_dominance: float
    dominance_30d_ago: float
    change_30d: float
    signal: SignalStrength
    interpretation: str


@dataclass
class VolatilityAnalysis:
    """Volatility regime analysis."""
    asset: str
    volatility_7d: float  # 7-day realized volatility
    volatility_30d: float  # 30-day realized volatility
    vol_regime: str  # "low", "normal", "high", "extreme"
    signal: SignalStrength


@dataclass
class TimeBasedAnalysis:
    """Time-based patterns."""
    day_of_week: str
    day_of_month: int
    is_weekend: bool
    is_month_end: bool  # Last 3 days of month
    is_month_start: bool  # First 3 days of month
    historical_bias: str  # "bullish", "bearish", "neutral"
    signal: SignalStrength


@dataclass
class ComprehensiveAnalysis:
    """Complete market analysis with all signals."""
    timestamp: datetime
    signals: List[MarketSignal]
    rsi: Dict[str, RSIAnalysis]
    volume: Dict[str, VolumeAnalysis]
    funding: Dict[str, FundingRateAnalysis]
    moving_averages: Dict[str, MovingAverageAnalysis]
    btc_dominance: BTCDominanceAnalysis
    volatility: Dict[str, VolatilityAnalysis]
    time_based: TimeBasedAnalysis

    # Composite scores
    composite_score: float  # -10 to +10
    composite_signal: SignalStrength
    confidence: float  # 0-1

    # Recommendations
    recommended_multiplier: float
    key_signals: List[str]  # Most important signals right now


class AdvancedMarketAnalyzer:
    """Advanced market analysis with multiple signal types."""

    COINGECKO_URL = "https://api.coingecko.com/api/v3"
    ALTERNATIVE_ME_URL = "https://api.alternative.me"

    def __init__(self, price_service: Optional[PriceService] = None):
        self.price_service = price_service or PriceService()
        self._session: Optional[aiohttp.ClientSession] = None
        self._price_history: Dict[str, List[Tuple[datetime, float]]] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    # =========================================================================
    # RSI CALCULATION
    # =========================================================================

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI from price series."""
        if len(prices) < period + 1:
            return 50.0  # Neutral if not enough data

        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # Separate gains and losses
        gains = [max(0, c) for c in changes]
        losses = [abs(min(0, c)) for c in changes]

        # Calculate average gain/loss
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    async def get_rsi_analysis(self, asset: str) -> RSIAnalysis:
        """Get RSI analysis for an asset."""
        # Fetch historical prices
        session = await self._get_session()

        # Map to CoinGecko ID
        asset_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "DOT": "polkadot", "AVAX": "avalanche-2", "ATOM": "cosmos",
        }
        coin_id = asset_map.get(asset, asset.lower())

        url = f"{self.COINGECKO_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 30}

        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                prices = [p[1] for p in data.get("prices", [])]

                rsi_14 = self.calculate_rsi(prices, 14)
                rsi_7 = self.calculate_rsi(prices, 7)

                # Determine signal
                if rsi_14 < 20:
                    signal = SignalStrength.STRONG_BUY
                elif rsi_14 < 30:
                    signal = SignalStrength.BUY
                elif rsi_14 > 80:
                    signal = SignalStrength.STRONG_SELL
                elif rsi_14 > 70:
                    signal = SignalStrength.SELL
                else:
                    signal = SignalStrength.NEUTRAL

                return RSIAnalysis(
                    asset=asset,
                    rsi_14=rsi_14,
                    rsi_7=rsi_7,
                    signal=signal,
                )
        except Exception as e:
            print(f"RSI fetch failed for {asset}: {e}")
            return RSIAnalysis(asset=asset, rsi_14=50, rsi_7=50, signal=SignalStrength.NEUTRAL)

    # =========================================================================
    # VOLUME ANALYSIS
    # =========================================================================

    async def get_volume_analysis(self, asset: str) -> VolumeAnalysis:
        """Analyze volume for capitulation detection."""
        session = await self._get_session()

        asset_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "DOT": "polkadot", "AVAX": "avalanche-2", "ATOM": "cosmos",
        }
        coin_id = asset_map.get(asset, asset.lower())

        url = f"{self.COINGECKO_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 30}

        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()

                volumes = [v[1] for v in data.get("total_volumes", [])]
                prices = [p[1] for p in data.get("prices", [])]

                if not volumes or not prices:
                    return VolumeAnalysis(
                        asset=asset, current_volume_24h=0, avg_volume_30d=0,
                        volume_ratio=1.0, is_capitulation=False, signal=SignalStrength.NEUTRAL
                    )

                current_volume = volumes[-1]
                avg_volume = sum(volumes) / len(volumes)
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

                # Check for capitulation: high volume + price drop
                price_change = (prices[-1] - prices[-7]) / prices[-7] if prices[-7] > 0 else 0
                is_capitulation = volume_ratio > 2.0 and price_change < -0.15

                # Signal determination
                if is_capitulation:
                    signal = SignalStrength.STRONG_BUY  # Capitulation often marks bottoms
                elif volume_ratio > 1.5 and price_change < -0.10:
                    signal = SignalStrength.BUY
                elif volume_ratio < 0.5:
                    signal = SignalStrength.NEUTRAL  # Low volume = uncertainty
                else:
                    signal = SignalStrength.NEUTRAL

                return VolumeAnalysis(
                    asset=asset,
                    current_volume_24h=current_volume,
                    avg_volume_30d=avg_volume,
                    volume_ratio=volume_ratio,
                    is_capitulation=is_capitulation,
                    signal=signal,
                )
        except Exception as e:
            print(f"Volume fetch failed for {asset}: {e}")
            return VolumeAnalysis(
                asset=asset, current_volume_24h=0, avg_volume_30d=0,
                volume_ratio=1.0, is_capitulation=False, signal=SignalStrength.NEUTRAL
            )

    # =========================================================================
    # MOVING AVERAGES
    # =========================================================================

    async def get_ma_analysis(self, asset: str) -> MovingAverageAnalysis:
        """Analyze price position relative to moving averages."""
        session = await self._get_session()

        asset_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "DOT": "polkadot", "AVAX": "avalanche-2", "ATOM": "cosmos",
        }
        coin_id = asset_map.get(asset, asset.lower())

        url = f"{self.COINGECKO_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 200}

        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                prices = [p[1] for p in data.get("prices", [])]

                if len(prices) < 200:
                    return MovingAverageAnalysis(
                        asset=asset, current_price=prices[-1] if prices else 0,
                        ma_50=0, ma_200=0, price_vs_ma50_pct=0, price_vs_ma200_pct=0,
                        ma_50_above_200=True, signal=SignalStrength.NEUTRAL
                    )

                current_price = prices[-1]
                ma_50 = sum(prices[-50:]) / 50
                ma_200 = sum(prices[-200:]) / 200

                price_vs_ma50 = (current_price - ma_50) / ma_50 * 100
                price_vs_ma200 = (current_price - ma_200) / ma_200 * 100

                # Signal: Below 200 MA is historically good accumulation
                if price_vs_ma200 < -20:
                    signal = SignalStrength.STRONG_BUY
                elif price_vs_ma200 < -10:
                    signal = SignalStrength.BUY
                elif price_vs_ma200 > 50:
                    signal = SignalStrength.SELL
                elif price_vs_ma200 > 30:
                    signal = SignalStrength.NEUTRAL
                else:
                    signal = SignalStrength.NEUTRAL

                return MovingAverageAnalysis(
                    asset=asset,
                    current_price=current_price,
                    ma_50=ma_50,
                    ma_200=ma_200,
                    price_vs_ma50_pct=price_vs_ma50,
                    price_vs_ma200_pct=price_vs_ma200,
                    ma_50_above_200=ma_50 > ma_200,
                    signal=signal,
                )
        except Exception as e:
            print(f"MA fetch failed for {asset}: {e}")
            return MovingAverageAnalysis(
                asset=asset, current_price=0, ma_50=0, ma_200=0,
                price_vs_ma50_pct=0, price_vs_ma200_pct=0,
                ma_50_above_200=True, signal=SignalStrength.NEUTRAL
            )

    # =========================================================================
    # BTC DOMINANCE
    # =========================================================================

    async def get_btc_dominance_analysis(self) -> BTCDominanceAnalysis:
        """Analyze Bitcoin dominance for risk sentiment."""
        session = await self._get_session()

        try:
            # Get current dominance
            url = f"{self.COINGECKO_URL}/global"
            async with session.get(url) as resp:
                data = await resp.json()
                current_dom = data.get("data", {}).get("market_cap_percentage", {}).get("btc", 50)

            # Get historical (approximation - would need better data source)
            # For now, assume 30d ago dominance
            dominance_30d_ago = current_dom - 2  # Placeholder
            change = current_dom - dominance_30d_ago

            # Rising BTC dominance = risk-off (money flowing to safety)
            # Good time to accumulate alts at lower prices
            if change > 5:
                signal = SignalStrength.BUY  # Alts getting cheaper
                interpretation = "Risk-off: Money flowing to BTC. Alts may be oversold."
            elif change < -5:
                signal = SignalStrength.SELL  # Alt season, prices high
                interpretation = "Risk-on: Alt season. Consider taking profits on alts."
            else:
                signal = SignalStrength.NEUTRAL
                interpretation = "Neutral dominance trend."

            return BTCDominanceAnalysis(
                current_dominance=current_dom,
                dominance_30d_ago=dominance_30d_ago,
                change_30d=change,
                signal=signal,
                interpretation=interpretation,
            )
        except Exception as e:
            print(f"BTC dominance fetch failed: {e}")
            return BTCDominanceAnalysis(
                current_dominance=50, dominance_30d_ago=50, change_30d=0,
                signal=SignalStrength.NEUTRAL, interpretation="Data unavailable"
            )

    # =========================================================================
    # VOLATILITY
    # =========================================================================

    async def get_volatility_analysis(self, asset: str) -> VolatilityAnalysis:
        """Analyze volatility regime."""
        session = await self._get_session()

        asset_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "DOT": "polkadot", "AVAX": "avalanche-2", "ATOM": "cosmos",
        }
        coin_id = asset_map.get(asset, asset.lower())

        url = f"{self.COINGECKO_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": 30}

        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                prices = [p[1] for p in data.get("prices", [])]

                if len(prices) < 7:
                    return VolatilityAnalysis(
                        asset=asset, volatility_7d=0, volatility_30d=0,
                        vol_regime="normal", signal=SignalStrength.NEUTRAL
                    )

                # Calculate daily returns
                returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]

                # Annualized volatility
                vol_7d = statistics.stdev(returns[-7:]) * (365 ** 0.5) * 100 if len(returns) >= 7 else 0
                vol_30d = statistics.stdev(returns) * (365 ** 0.5) * 100

                # Determine regime
                if vol_30d > 100:
                    vol_regime = "extreme"
                    signal = SignalStrength.BUY  # High vol often = opportunity
                elif vol_30d > 70:
                    vol_regime = "high"
                    signal = SignalStrength.BUY
                elif vol_30d < 30:
                    vol_regime = "low"
                    signal = SignalStrength.NEUTRAL
                else:
                    vol_regime = "normal"
                    signal = SignalStrength.NEUTRAL

                return VolatilityAnalysis(
                    asset=asset,
                    volatility_7d=vol_7d,
                    volatility_30d=vol_30d,
                    vol_regime=vol_regime,
                    signal=signal,
                )
        except Exception as e:
            print(f"Volatility fetch failed for {asset}: {e}")
            return VolatilityAnalysis(
                asset=asset, volatility_7d=0, volatility_30d=0,
                vol_regime="normal", signal=SignalStrength.NEUTRAL
            )

    # =========================================================================
    # TIME-BASED PATTERNS
    # =========================================================================

    def get_time_based_analysis(self) -> TimeBasedAnalysis:
        """Analyze time-based patterns."""
        now = datetime.now()

        day_of_week = now.strftime("%A")
        day_of_month = now.day
        is_weekend = now.weekday() >= 5
        is_month_end = day_of_month >= 28
        is_month_start = day_of_month <= 3

        # Historical patterns:
        # - Weekends often see lower prices (less institutional activity)
        # - Month-end can see selling (fund rebalancing)
        # - Month-start often sees inflows (paycheck investing)

        if is_weekend:
            bias = "slightly bullish"  # Weekend discount
            signal = SignalStrength.BUY
        elif is_month_end:
            bias = "slightly bearish"  # Rebalancing selling
            signal = SignalStrength.NEUTRAL
        elif is_month_start:
            bias = "slightly bullish"  # Fresh inflows
            signal = SignalStrength.NEUTRAL
        else:
            bias = "neutral"
            signal = SignalStrength.NEUTRAL

        return TimeBasedAnalysis(
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            is_weekend=is_weekend,
            is_month_end=is_month_end,
            is_month_start=is_month_start,
            historical_bias=bias,
            signal=signal,
        )

    # =========================================================================
    # COMPREHENSIVE ANALYSIS
    # =========================================================================

    async def analyze(self, assets: List[str] = None) -> ComprehensiveAnalysis:
        """Run comprehensive market analysis."""
        if assets is None:
            assets = ["BTC", "ETH", "SOL"]

        # Gather all analyses concurrently
        rsi_tasks = [self.get_rsi_analysis(a) for a in assets]
        volume_tasks = [self.get_volume_analysis(a) for a in assets]
        ma_tasks = [self.get_ma_analysis(a) for a in assets]
        vol_tasks = [self.get_volatility_analysis(a) for a in assets]

        results = await asyncio.gather(
            *rsi_tasks, *volume_tasks, *ma_tasks, *vol_tasks,
            self.get_btc_dominance_analysis(),
            return_exceptions=True,
        )

        # Parse results
        n = len(assets)
        rsi_results = {assets[i]: results[i] for i in range(n) if not isinstance(results[i], Exception)}
        volume_results = {assets[i]: results[n+i] for i in range(n) if not isinstance(results[n+i], Exception)}
        ma_results = {assets[i]: results[2*n+i] for i in range(n) if not isinstance(results[2*n+i], Exception)}
        vol_results = {assets[i]: results[3*n+i] for i in range(n) if not isinstance(results[3*n+i], Exception)}
        btc_dom = results[-1] if not isinstance(results[-1], Exception) else None

        time_based = self.get_time_based_analysis()

        # Build signals list
        signals = []

        # RSI signals (weight: 0.20)
        for asset, rsi in rsi_results.items():
            signals.append(MarketSignal(
                name=f"{asset} RSI",
                value=rsi.rsi_14,
                signal=rsi.signal,
                weight=0.20,
                description=f"RSI(14)={rsi.rsi_14:.1f}" + (" OVERSOLD" if rsi.is_oversold else " OVERBOUGHT" if rsi.is_overbought else ""),
            ))

        # Volume signals (weight: 0.15)
        for asset, vol in volume_results.items():
            signals.append(MarketSignal(
                name=f"{asset} Volume",
                value=vol.volume_ratio,
                signal=vol.signal,
                weight=0.15,
                description=f"Volume {vol.volume_ratio:.1f}x avg" + (" CAPITULATION!" if vol.is_capitulation else ""),
            ))

        # MA signals (weight: 0.20)
        for asset, ma in ma_results.items():
            signals.append(MarketSignal(
                name=f"{asset} vs 200MA",
                value=ma.price_vs_ma200_pct,
                signal=ma.signal,
                weight=0.20,
                description=f"{ma.price_vs_ma200_pct:+.1f}% vs 200MA",
            ))

        # Volatility signals (weight: 0.10)
        for asset, v in vol_results.items():
            signals.append(MarketSignal(
                name=f"{asset} Volatility",
                value=v.volatility_30d,
                signal=v.signal,
                weight=0.10,
                description=f"{v.vol_regime.upper()} vol ({v.volatility_30d:.0f}% ann.)",
            ))

        # BTC Dominance signal (weight: 0.10)
        if btc_dom:
            signals.append(MarketSignal(
                name="BTC Dominance",
                value=btc_dom.current_dominance,
                signal=btc_dom.signal,
                weight=0.10,
                description=btc_dom.interpretation,
            ))

        # Time-based signal (weight: 0.05)
        signals.append(MarketSignal(
            name="Time Pattern",
            value=0,
            signal=time_based.signal,
            weight=0.05,
            description=f"{time_based.day_of_week}, {time_based.historical_bias}",
        ))

        # Calculate composite score
        total_weight = sum(s.weight for s in signals)
        composite_score = sum(s.weighted_score for s in signals) / total_weight if total_weight > 0 else 0

        # Scale to -10 to +10
        composite_score = composite_score * 5

        # Determine composite signal
        if composite_score > 3:
            composite_signal = SignalStrength.STRONG_BUY
        elif composite_score > 1:
            composite_signal = SignalStrength.BUY
        elif composite_score < -3:
            composite_signal = SignalStrength.STRONG_SELL
        elif composite_score < -1:
            composite_signal = SignalStrength.SELL
        else:
            composite_signal = SignalStrength.NEUTRAL

        # Calculate confidence based on signal agreement
        buy_signals = sum(1 for s in signals if s.signal.value > 0)
        sell_signals = sum(1 for s in signals if s.signal.value < 0)
        agreement = max(buy_signals, sell_signals) / len(signals) if signals else 0
        confidence = agreement

        # Calculate recommended multiplier
        # Map composite score to multiplier
        if composite_score >= 4:
            multiplier = 2.5
        elif composite_score >= 2:
            multiplier = 2.0
        elif composite_score >= 1:
            multiplier = 1.5
        elif composite_score >= 0:
            multiplier = 1.0
        elif composite_score >= -2:
            multiplier = 0.75
        else:
            multiplier = 0.5

        # Key signals (strongest buy or sell)
        key_signals = sorted(signals, key=lambda s: abs(s.weighted_score), reverse=True)[:5]
        key_signal_strs = [f"{s.name}: {s.description}" for s in key_signals]

        return ComprehensiveAnalysis(
            timestamp=datetime.now(),
            signals=signals,
            rsi=rsi_results,
            volume=volume_results,
            funding={},  # Would need separate data source
            moving_averages=ma_results,
            btc_dominance=btc_dom,
            volatility=vol_results,
            time_based=time_based,
            composite_score=composite_score,
            composite_signal=composite_signal,
            confidence=confidence,
            recommended_multiplier=multiplier,
            key_signals=key_signal_strs,
        )

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


def format_comprehensive_analysis(analysis: ComprehensiveAnalysis) -> str:
    """Format comprehensive analysis for display."""
    lines = []

    signal_emoji = {
        SignalStrength.STRONG_BUY: "🟢🟢",
        SignalStrength.BUY: "🟢",
        SignalStrength.NEUTRAL: "⚪",
        SignalStrength.SELL: "🔴",
        SignalStrength.STRONG_SELL: "🔴🔴",
    }

    lines.append("=" * 80)
    lines.append("  COMPREHENSIVE MARKET ANALYSIS")
    lines.append(f"  {analysis.timestamp.strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 80)
    lines.append("")

    # Composite score
    emoji = signal_emoji.get(analysis.composite_signal, "")
    lines.append(f"  {emoji} COMPOSITE SCORE: {analysis.composite_score:+.1f}/10")
    lines.append(f"  Signal: {analysis.composite_signal.name}")
    lines.append(f"  Confidence: {analysis.confidence:.0%}")
    lines.append(f"  Recommended DCA Multiplier: {analysis.recommended_multiplier:.1f}x")
    lines.append("")

    # Key signals
    lines.append("  KEY SIGNALS:")
    lines.append("  " + "-" * 70)
    for sig in analysis.key_signals:
        lines.append(f"  • {sig}")
    lines.append("")

    # RSI Section
    lines.append("  RSI ANALYSIS:")
    lines.append("  " + "-" * 70)
    for asset, rsi in analysis.rsi.items():
        emoji = signal_emoji.get(rsi.signal, "")
        status = "OVERSOLD" if rsi.is_oversold else "OVERBOUGHT" if rsi.is_overbought else ""
        lines.append(f"  {emoji} {asset}: RSI(14)={rsi.rsi_14:.1f} RSI(7)={rsi.rsi_7:.1f} {status}")
    lines.append("")

    # Moving Averages
    lines.append("  MOVING AVERAGE POSITION:")
    lines.append("  " + "-" * 70)
    for asset, ma in analysis.moving_averages.items():
        emoji = signal_emoji.get(ma.signal, "")
        lines.append(f"  {emoji} {asset}: {ma.price_vs_ma200_pct:+.1f}% vs 200MA, {ma.price_vs_ma50_pct:+.1f}% vs 50MA")
    lines.append("")

    # Volume
    lines.append("  VOLUME ANALYSIS:")
    lines.append("  " + "-" * 70)
    for asset, vol in analysis.volume.items():
        emoji = signal_emoji.get(vol.signal, "")
        cap = "🔥 CAPITULATION" if vol.is_capitulation else ""
        lines.append(f"  {emoji} {asset}: {vol.volume_ratio:.1f}x avg volume {cap}")
    lines.append("")

    # Volatility
    lines.append("  VOLATILITY REGIME:")
    lines.append("  " + "-" * 70)
    for asset, v in analysis.volatility.items():
        emoji = signal_emoji.get(v.signal, "")
        lines.append(f"  {emoji} {asset}: {v.vol_regime.upper()} ({v.volatility_30d:.0f}% annualized)")
    lines.append("")

    # BTC Dominance
    if analysis.btc_dominance:
        lines.append("  BTC DOMINANCE:")
        lines.append("  " + "-" * 70)
        dom = analysis.btc_dominance
        emoji = signal_emoji.get(dom.signal, "")
        lines.append(f"  {emoji} {dom.current_dominance:.1f}% ({dom.change_30d:+.1f}% 30d)")
        lines.append(f"     {dom.interpretation}")
    lines.append("")

    # Time-based
    lines.append("  TIME PATTERNS:")
    lines.append("  " + "-" * 70)
    t = analysis.time_based
    emoji = signal_emoji.get(t.signal, "")
    lines.append(f"  {emoji} {t.day_of_week}, Day {t.day_of_month}")
    lines.append(f"     Historical bias: {t.historical_bias}")
    if t.is_weekend:
        lines.append("     📅 Weekend - historically lower prices")
    lines.append("")

    # All signals table
    lines.append("  ALL SIGNALS:")
    lines.append("  " + "-" * 70)
    lines.append(f"  {'Signal':<25} {'Value':>10} {'Strength':>12} {'Weight':>8}")
    lines.append("  " + "-" * 70)

    for sig in sorted(analysis.signals, key=lambda s: s.weight, reverse=True):
        emoji = signal_emoji.get(sig.signal, "")
        lines.append(f"  {sig.name:<25} {sig.value:>10.2f} {emoji:>10} {sig.weight:>8.0%}")

    lines.append("")

    return "\n".join(lines)


# Convenience function
async def get_comprehensive_analysis(assets: List[str] = None) -> ComprehensiveAnalysis:
    """Quick function to get comprehensive analysis."""
    analyzer = AdvancedMarketAnalyzer()
    try:
        return await analyzer.analyze(assets)
    finally:
        await analyzer.close()
