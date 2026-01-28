"""
Extended Market Signals Module - 40+ Indicators

Comprehensive multi-factor analysis for intelligent dip buying:

CATEGORY 1: TECHNICAL INDICATORS (1-8)
1. RSI (Relative Strength Index)
2. Moving Averages (50/100/200 MA)
3. Bollinger Bands
4. MACD (Moving Average Convergence Divergence)
5. Volume Profile / Capitulation Detection
6. ATR (Average True Range) Volatility
7. Fibonacci Retracement Levels
8. Ichimoku Cloud

CATEGORY 2: SENTIMENT INDICATORS (9-16)
9. Fear & Greed Index
10. Google Trends (panic searches)
11. Social Sentiment (Twitter/Reddit)
12. News Sentiment Aggregation
13. YouTube/Media Sentiment
14. Long/Short Ratio
15. Retail vs Institutional Positioning
16. Crypto Twitter Influencer Sentiment

CATEGORY 3: ON-CHAIN METRICS (17-28)
17. Exchange Inflows/Outflows
18. Whale Wallet Movements
19. Active Addresses
20. MVRV Z-Score
21. SOPR (Spent Output Profit Ratio)
22. NUPL (Net Unrealized Profit/Loss)
23. Puell Multiple
24. Reserve Risk
25. Realized Price Bands
26. HODL Waves (LTH vs STH supply)
27. Coin Days Destroyed
28. NVT Ratio (Network Value to Transactions)

CATEGORY 4: DERIVATIVES DATA (29-36)
29. Funding Rates
30. Open Interest
31. Liquidation Data
32. Options Put/Call Ratio
33. Options Skew (25-delta)
34. Max Pain Price
35. Futures Basis (Premium/Discount)
36. Term Structure (Contango/Backwardation)

CATEGORY 5: MACRO & CROSS-MARKET (37-44)
37. DXY (Dollar Index)
38. S&P 500 / Risk Asset Correlation
39. Gold Correlation
40. Treasury Yields (10Y)
41. VIX (Fear Index)
42. Stablecoin Supply Ratio
43. Coinbase Premium (US institutional)
44. Korea Premium (Kimchi)

CATEGORY 6: NETWORK & MINING (45-50)
45. Hash Rate
46. Difficulty Ribbon
47. Miner Outflows
48. Miner Reserve
49. Thermocap Multiple
50. Stock-to-Flow Deviation

CATEGORY 7: INSTITUTIONAL (51-55)
51. ETF Flows (BTC/ETH)
52. Grayscale Premium/Discount
53. CME Futures Open Interest
54. MicroStrategy Premium
55. Institutional Wallet Tracking

CATEGORY 8: ADDITIONAL SIGNALS (56-60)
56. Stablecoin Mint/Burn
57. Tether Treasury Activity
58. DeFi TVL Changes
59. NFT Market Sentiment
60. Mempool Congestion / Fees
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels."""
    STRONG_BUY = "strong_buy"      # Score: +2
    BUY = "buy"                     # Score: +1
    NEUTRAL = "neutral"             # Score: 0
    SELL = "sell"                   # Score: -1
    STRONG_SELL = "strong_sell"    # Score: -2
    UNAVAILABLE = "unavailable"     # No data


@dataclass
class SignalResult:
    """Individual signal result."""
    name: str
    category: str
    value: Optional[float]
    signal: SignalStrength
    score: int  # -2 to +2
    weight: float  # How much this signal counts
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CategorySummary:
    """Summary for a category of signals."""
    name: str
    signals: List[SignalResult]
    avg_score: float
    weighted_score: float
    bullish_count: int
    bearish_count: int
    neutral_count: int


@dataclass 
class ComprehensiveSignalAnalysis:
    """Complete analysis with all 60 signals."""
    timestamp: datetime
    asset: str
    
    # Category summaries
    technical: CategorySummary
    sentiment: CategorySummary
    onchain: CategorySummary
    derivatives: CategorySummary
    macro: CategorySummary
    mining: CategorySummary
    institutional: CategorySummary
    additional: CategorySummary
    
    # Overall scores
    total_signals: int
    available_signals: int
    composite_score: float  # -100 to +100
    
    # Recommendations
    dca_multiplier: float
    buffer_deployment: float
    confidence: float  # 0-1 based on data availability
    recommendation: str
    
    # All individual signals
    all_signals: List[SignalResult] = field(default_factory=list)


class ExtendedSignalsAnalyzer:
    """
    Analyzes 60+ market signals to determine optimal buying conditions.
    """
    
    # Signal weights by category (higher = more important)
    CATEGORY_WEIGHTS = {
        "technical": 1.0,
        "sentiment": 0.8,
        "onchain": 1.2,  # On-chain is very reliable
        "derivatives": 1.0,
        "macro": 0.7,
        "mining": 0.9,
        "institutional": 1.1,
        "additional": 0.6,
    }
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                return data
        return None
    
    def _set_cached(self, key: str, data: Any):
        self._cache[key] = (data, datetime.utcnow())
    
    # =========================================================================
    # CATEGORY 1: TECHNICAL INDICATORS
    # =========================================================================
    
    async def _get_rsi(self, asset: str) -> SignalResult:
        """
        RSI (Relative Strength Index)
        < 20: Extremely oversold (Strong Buy)
        20-30: Oversold (Buy)
        30-70: Neutral
        70-80: Overbought (Sell)
        > 80: Extremely overbought (Strong Sell)
        """
        try:
            # In production, fetch from TradingView or calculate from price data
            session = await self._get_session()
            
            # Using Alternative.me or similar for crypto RSI
            # This is a placeholder - you'd use your price service
            rsi = await self._fetch_rsi_from_api(asset)
            
            if rsi is None:
                return self._unavailable_signal("RSI", "technical")
            
            if rsi < 20:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extremely oversold (RSI: {rsi:.1f})"
            elif rsi < 30:
                signal, score = SignalStrength.BUY, 1
                desc = f"Oversold (RSI: {rsi:.1f})"
            elif rsi < 70:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral range (RSI: {rsi:.1f})"
            elif rsi < 80:
                signal, score = SignalStrength.SELL, -1
                desc = f"Overbought (RSI: {rsi:.1f})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Extremely overbought (RSI: {rsi:.1f})"
            
            return SignalResult(
                name="RSI",
                category="technical",
                value=rsi,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={"rsi": rsi, "period": 14}
            )
        except Exception as e:
            logger.error(f"Error fetching RSI: {e}")
            return self._unavailable_signal("RSI", "technical")
    
    async def _get_moving_averages(self, asset: str) -> SignalResult:
        """
        Price position relative to key moving averages.
        Below 200 MA by >20%: Strong Buy
        Below 200 MA by 10-20%: Buy
        Near 200 MA (±10%): Neutral
        Above 200 MA by >30%: Sell
        Above 200 MA by >50%: Strong Sell
        """
        try:
            data = await self._fetch_ma_data(asset)
            if data is None:
                return self._unavailable_signal("Moving Averages", "technical")
            
            price = data["price"]
            ma_50 = data.get("ma_50")
            ma_100 = data.get("ma_100")
            ma_200 = data.get("ma_200")
            
            if ma_200 is None:
                return self._unavailable_signal("Moving Averages", "technical")
            
            pct_from_200ma = ((price - ma_200) / ma_200) * 100
            
            if pct_from_200ma < -20:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price {abs(pct_from_200ma):.1f}% below 200 MA - historically great entry"
            elif pct_from_200ma < -10:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price {abs(pct_from_200ma):.1f}% below 200 MA"
            elif pct_from_200ma < 30:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price {pct_from_200ma:+.1f}% vs 200 MA - normal range"
            elif pct_from_200ma < 50:
                signal, score = SignalStrength.SELL, -1
                desc = f"Price {pct_from_200ma:.1f}% above 200 MA - extended"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Price {pct_from_200ma:.1f}% above 200 MA - extremely extended"
            
            return SignalResult(
                name="Moving Averages",
                category="technical",
                value=pct_from_200ma,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={
                    "price": price,
                    "ma_50": ma_50,
                    "ma_100": ma_100,
                    "ma_200": ma_200,
                    "pct_from_200ma": pct_from_200ma
                }
            )
        except Exception as e:
            logger.error(f"Error fetching MAs: {e}")
            return self._unavailable_signal("Moving Averages", "technical")
    
    async def _get_bollinger_bands(self, asset: str) -> SignalResult:
        """
        Bollinger Band position.
        Below lower band: Buy signal
        Above upper band: Sell signal
        Band squeeze: Volatility incoming
        """
        try:
            data = await self._fetch_bollinger_data(asset)
            if data is None:
                return self._unavailable_signal("Bollinger Bands", "technical")
            
            price = data["price"]
            upper = data["upper"]
            lower = data["lower"]
            middle = data["middle"]
            bandwidth = (upper - lower) / middle * 100
            
            position = (price - lower) / (upper - lower) if upper != lower else 0.5
            
            if position < 0:  # Below lower band
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price below lower Bollinger Band - oversold"
            elif position < 0.2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price near lower band ({position*100:.0f}% of range)"
            elif position < 0.8:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price in middle of bands ({position*100:.0f}% of range)"
            elif position < 1.0:
                signal, score = SignalStrength.SELL, -1
                desc = f"Price near upper band ({position*100:.0f}% of range)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Price above upper Bollinger Band - overbought"
            
            # Note band squeeze
            if bandwidth < 5:
                desc += " [SQUEEZE: volatility incoming]"
            
            return SignalResult(
                name="Bollinger Bands",
                category="technical",
                value=position,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={
                    "price": price,
                    "upper": upper,
                    "lower": lower,
                    "middle": middle,
                    "bandwidth": bandwidth,
                    "position": position
                }
            )
        except Exception as e:
            logger.error(f"Error fetching Bollinger: {e}")
            return self._unavailable_signal("Bollinger Bands", "technical")
    
    async def _get_macd(self, asset: str) -> SignalResult:
        """
        MACD (Moving Average Convergence Divergence)
        Bullish crossover: Buy
        Bearish crossover: Sell
        Histogram increasing: Momentum building
        """
        try:
            data = await self._fetch_macd_data(asset)
            if data is None:
                return self._unavailable_signal("MACD", "technical")
            
            macd_line = data["macd"]
            signal_line = data["signal"]
            histogram = data["histogram"]
            prev_histogram = data.get("prev_histogram", histogram)
            
            # Determine signal
            if histogram > 0 and histogram > prev_histogram:
                signal, score = SignalStrength.BUY, 1
                desc = "Bullish momentum building (histogram expanding)"
            elif histogram > 0 and histogram < prev_histogram:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Bullish but momentum fading"
            elif histogram < 0 and histogram < prev_histogram:
                signal, score = SignalStrength.SELL, -1
                desc = "Bearish momentum building"
            elif histogram < 0 and histogram > prev_histogram:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Bearish but momentum fading (potential reversal)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "MACD neutral"
            
            # Check for crossovers
            if macd_line > signal_line and data.get("prev_macd", macd_line) <= data.get("prev_signal", signal_line):
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = "BULLISH CROSSOVER - buy signal"
            elif macd_line < signal_line and data.get("prev_macd", macd_line) >= data.get("prev_signal", signal_line):
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = "BEARISH CROSSOVER - sell signal"
            
            return SignalResult(
                name="MACD",
                category="technical",
                value=histogram,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={
                    "macd": macd_line,
                    "signal": signal_line,
                    "histogram": histogram
                }
            )
        except Exception as e:
            logger.error(f"Error fetching MACD: {e}")
            return self._unavailable_signal("MACD", "technical")
    
    async def _get_volume_capitulation(self, asset: str) -> SignalResult:
        """
        Volume analysis for capitulation detection.
        High volume + price drop = potential capitulation (buy)
        High volume + price rise = confirmation
        Low volume = low conviction
        """
        try:
            data = await self._fetch_volume_data(asset)
            if data is None:
                return self._unavailable_signal("Volume Analysis", "technical")
            
            volume = data["volume"]
            avg_volume = data["avg_volume"]
            price_change = data["price_change_24h"]
            
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            # Capitulation: High volume + big drop
            if volume_ratio > 2.0 and price_change < -15:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"CAPITULATION: {volume_ratio:.1f}x volume with {price_change:.1f}% drop"
            elif volume_ratio > 1.5 and price_change < -10:
                signal, score = SignalStrength.BUY, 1
                desc = f"High volume selling ({volume_ratio:.1f}x avg, {price_change:.1f}%)"
            elif volume_ratio < 0.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Low volume ({volume_ratio:.1f}x avg) - low conviction"
            elif volume_ratio > 1.5 and price_change > 10:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"High volume rally - wait for pullback"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal volume ({volume_ratio:.1f}x avg)"
            
            return SignalResult(
                name="Volume Analysis",
                category="technical",
                value=volume_ratio,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                details={
                    "volume": volume,
                    "avg_volume": avg_volume,
                    "volume_ratio": volume_ratio,
                    "price_change": price_change
                }
            )
        except Exception as e:
            logger.error(f"Error fetching volume: {e}")
            return self._unavailable_signal("Volume Analysis", "technical")
    
    async def _get_atr_volatility(self, asset: str) -> SignalResult:
        """
        ATR (Average True Range) for volatility analysis.
        High ATR after spike = volatility exhaustion (potential reversal)
        Low ATR = calm before storm
        """
        try:
            data = await self._fetch_atr_data(asset)
            if data is None:
                return self._unavailable_signal("ATR Volatility", "technical")
            
            atr = data["atr"]
            atr_percent = data["atr_percent"]  # ATR as % of price
            avg_atr_percent = data.get("avg_atr_percent", atr_percent)
            
            volatility_ratio = atr_percent / avg_atr_percent if avg_atr_percent > 0 else 1
            
            if volatility_ratio > 2.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Extreme volatility ({volatility_ratio:.1f}x normal) - exhaustion likely"
            elif volatility_ratio > 1.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Elevated volatility ({volatility_ratio:.1f}x normal)"
            elif volatility_ratio < 0.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Low volatility ({volatility_ratio:.1f}x normal) - breakout pending"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal volatility ({atr_percent:.2f}% daily range)"
            
            return SignalResult(
                name="ATR Volatility",
                category="technical",
                value=volatility_ratio,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={
                    "atr": atr,
                    "atr_percent": atr_percent,
                    "volatility_ratio": volatility_ratio
                }
            )
        except Exception as e:
            logger.error(f"Error fetching ATR: {e}")
            return self._unavailable_signal("ATR Volatility", "technical")
    
    async def _get_fibonacci(self, asset: str) -> SignalResult:
        """
        Fibonacci retracement levels from recent swing.
        At/below 0.618: Strong support
        At/below 0.786: Deep pullback
        """
        try:
            data = await self._fetch_fibonacci_data(asset)
            if data is None:
                return self._unavailable_signal("Fibonacci Levels", "technical")
            
            price = data["price"]
            fib_levels = data["levels"]  # {0.236, 0.382, 0.5, 0.618, 0.786}
            swing_high = data["swing_high"]
            swing_low = data["swing_low"]
            
            # Calculate which fib level we're at
            range_size = swing_high - swing_low
            retracement = (swing_high - price) / range_size if range_size > 0 else 0
            
            if retracement >= 0.786:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Deep retracement ({retracement:.1%}) - strong support zone"
            elif retracement >= 0.618:
                signal, score = SignalStrength.BUY, 1
                desc = f"At golden ratio ({retracement:.1%}) - key support"
            elif retracement >= 0.382:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Moderate retracement ({retracement:.1%})"
            elif retracement >= 0:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Shallow pullback ({retracement:.1%})"
            else:
                signal, score = SignalStrength.SELL, -1
                desc = f"Above swing high - extended"
            
            return SignalResult(
                name="Fibonacci Levels",
                category="technical",
                value=retracement,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={
                    "retracement": retracement,
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "fib_levels": fib_levels
                }
            )
        except Exception as e:
            logger.error(f"Error fetching Fibonacci: {e}")
            return self._unavailable_signal("Fibonacci Levels", "technical")
    
    async def _get_ichimoku(self, asset: str) -> SignalResult:
        """
        Ichimoku Cloud analysis.
        Price below cloud: Bearish trend (buy opportunity if oversold)
        Price above cloud: Bullish trend
        Cloud twist: Trend change coming
        """
        try:
            data = await self._fetch_ichimoku_data(asset)
            if data is None:
                return self._unavailable_signal("Ichimoku Cloud", "technical")
            
            price = data["price"]
            tenkan = data["tenkan"]  # Conversion line
            kijun = data["kijun"]    # Base line
            senkou_a = data["senkou_a"]  # Leading span A
            senkou_b = data["senkou_b"]  # Leading span B
            
            cloud_top = max(senkou_a, senkou_b)
            cloud_bottom = min(senkou_a, senkou_b)
            
            if price < cloud_bottom:
                # Below cloud - bearish but potential reversal
                pct_below = (cloud_bottom - price) / cloud_bottom * 100
                if pct_below > 20:
                    signal, score = SignalStrength.STRONG_BUY, 2
                    desc = f"Deep below cloud ({pct_below:.1f}%) - reversal zone"
                elif pct_below > 10:
                    signal, score = SignalStrength.BUY, 1
                    desc = f"Below cloud ({pct_below:.1f}%) - bearish but oversold"
                else:
                    signal, score = SignalStrength.NEUTRAL, 0
                    desc = f"Slightly below cloud - testing support"
            elif price > cloud_top:
                pct_above = (price - cloud_top) / cloud_top * 100
                if pct_above > 20:
                    signal, score = SignalStrength.SELL, -1
                    desc = f"Extended above cloud ({pct_above:.1f}%)"
                else:
                    signal, score = SignalStrength.NEUTRAL, 0
                    desc = f"Above cloud - bullish trend"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Inside cloud - consolidation zone"
            
            # Check TK cross
            if tenkan > kijun:
                desc += " [TK bullish]"
            else:
                desc += " [TK bearish]"
            
            return SignalResult(
                name="Ichimoku Cloud",
                category="technical",
                value=price - cloud_bottom,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={
                    "price": price,
                    "tenkan": tenkan,
                    "kijun": kijun,
                    "senkou_a": senkou_a,
                    "senkou_b": senkou_b,
                    "cloud_top": cloud_top,
                    "cloud_bottom": cloud_bottom
                }
            )
        except Exception as e:
            logger.error(f"Error fetching Ichimoku: {e}")
            return self._unavailable_signal("Ichimoku Cloud", "technical")
    
    # =========================================================================
    # CATEGORY 2: SENTIMENT INDICATORS
    # =========================================================================
    
    async def _get_fear_greed(self) -> SignalResult:
        """
        Crypto Fear & Greed Index (0-100).
        0-20: Extreme Fear (Strong Buy)
        20-35: Fear (Buy)
        35-65: Neutral
        65-80: Greed (Sell)
        80-100: Extreme Greed (Strong Sell)
        """
        try:
            session = await self._get_session()
            async with session.get("https://api.alternative.me/fng/?limit=1") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    fng = int(data["data"][0]["value"])
                    classification = data["data"][0]["value_classification"]
                else:
                    return self._unavailable_signal("Fear & Greed Index", "sentiment")
            
            if fng <= 20:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme Fear ({fng}) - historically great buying opportunity"
            elif fng <= 35:
                signal, score = SignalStrength.BUY, 1
                desc = f"Fear ({fng}) - {classification}"
            elif fng <= 65:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral ({fng}) - {classification}"
            elif fng <= 80:
                signal, score = SignalStrength.SELL, -1
                desc = f"Greed ({fng}) - {classification}"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Extreme Greed ({fng}) - euphoria, reduce exposure"
            
            return SignalResult(
                name="Fear & Greed Index",
                category="sentiment",
                value=fng,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={"fng": fng, "classification": classification}
            )
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")
            return self._unavailable_signal("Fear & Greed Index", "sentiment")
    
    async def _get_google_trends(self) -> SignalResult:
        """
        Google Trends for panic-related searches.
        Spike in "bitcoin crash", "crypto crash", "sell bitcoin": Contrarian buy
        """
        try:
            data = await self._fetch_google_trends()
            if data is None:
                return self._unavailable_signal("Google Trends", "sentiment")
            
            panic_score = data.get("panic_score", 50)  # 0-100
            search_volume = data.get("search_volume", "normal")
            
            if panic_score > 80:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme panic searches ({panic_score}) - contrarian buy"
            elif panic_score > 60:
                signal, score = SignalStrength.BUY, 1
                desc = f"Elevated panic searches ({panic_score})"
            elif panic_score < 20:
                signal, score = SignalStrength.SELL, -1
                desc = f"Low fear, high complacency ({panic_score})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal search patterns ({panic_score})"
            
            return SignalResult(
                name="Google Trends",
                category="sentiment",
                value=panic_score,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"panic_score": panic_score, "search_volume": search_volume}
            )
        except Exception as e:
            logger.error(f"Error fetching Google Trends: {e}")
            return self._unavailable_signal("Google Trends", "sentiment")
    
    async def _get_social_sentiment(self) -> SignalResult:
        """
        Social media sentiment (Twitter, Reddit).
        Extremely negative: Contrarian buy
        Extremely positive: Contrarian sell
        """
        try:
            data = await self._fetch_social_sentiment()
            if data is None:
                return self._unavailable_signal("Social Sentiment", "sentiment")
            
            sentiment_score = data.get("score", 0)  # -100 to +100
            volume = data.get("volume", "normal")
            
            if sentiment_score < -60:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme negative sentiment ({sentiment_score}) - contrarian buy"
            elif sentiment_score < -30:
                signal, score = SignalStrength.BUY, 1
                desc = f"Negative sentiment ({sentiment_score})"
            elif sentiment_score > 60:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Extreme euphoria ({sentiment_score}) - contrarian sell"
            elif sentiment_score > 30:
                signal, score = SignalStrength.SELL, -1
                desc = f"Very positive sentiment ({sentiment_score})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral sentiment ({sentiment_score})"
            
            return SignalResult(
                name="Social Sentiment",
                category="sentiment",
                value=sentiment_score,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"sentiment_score": sentiment_score, "volume": volume}
            )
        except Exception as e:
            logger.error(f"Error fetching social sentiment: {e}")
            return self._unavailable_signal("Social Sentiment", "sentiment")
    
    async def _get_news_sentiment(self) -> SignalResult:
        """
        Aggregated news sentiment from crypto news sources.
        """
        try:
            data = await self._fetch_news_sentiment()
            if data is None:
                return self._unavailable_signal("News Sentiment", "sentiment")
            
            sentiment = data.get("sentiment", 0)  # -100 to +100
            article_count = data.get("article_count", 0)
            
            if sentiment < -50:
                signal, score = SignalStrength.BUY, 1
                desc = f"Very negative news cycle ({sentiment})"
            elif sentiment > 50:
                signal, score = SignalStrength.SELL, -1
                desc = f"Very positive news cycle ({sentiment})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral news coverage ({sentiment})"
            
            return SignalResult(
                name="News Sentiment",
                category="sentiment",
                value=sentiment,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"sentiment": sentiment, "article_count": article_count}
            )
        except Exception as e:
            logger.error(f"Error fetching news sentiment: {e}")
            return self._unavailable_signal("News Sentiment", "sentiment")
    
    async def _get_youtube_sentiment(self) -> SignalResult:
        """
        YouTube crypto influencer sentiment.
        "Crypto is dead" videos spiking: Contrarian buy
        "To the moon" videos spiking: Contrarian sell
        """
        try:
            data = await self._fetch_youtube_sentiment()
            if data is None:
                return self._unavailable_signal("YouTube Sentiment", "sentiment")
            
            bearish_ratio = data.get("bearish_ratio", 0.5)  # 0-1
            
            if bearish_ratio > 0.7:
                signal, score = SignalStrength.BUY, 1
                desc = f"Influencers very bearish ({bearish_ratio:.0%}) - contrarian buy"
            elif bearish_ratio < 0.2:
                signal, score = SignalStrength.SELL, -1
                desc = f"Influencers very bullish ({1-bearish_ratio:.0%}) - caution"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Mixed influencer sentiment"
            
            return SignalResult(
                name="YouTube Sentiment",
                category="sentiment",
                value=bearish_ratio,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"bearish_ratio": bearish_ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching YouTube sentiment: {e}")
            return self._unavailable_signal("YouTube Sentiment", "sentiment")
    
    async def _get_long_short_ratio(self) -> SignalResult:
        """
        Long/Short ratio on major exchanges.
        Extreme longs: Contrarian sell (liquidation risk)
        Extreme shorts: Contrarian buy (squeeze potential)
        """
        try:
            data = await self._fetch_long_short_ratio()
            if data is None:
                return self._unavailable_signal("Long/Short Ratio", "sentiment")
            
            ratio = data.get("ratio", 1.0)  # >1 = more longs
            
            if ratio > 2.0:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Extreme long bias ({ratio:.2f}x) - liquidation risk"
            elif ratio > 1.5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Long bias ({ratio:.2f}x)"
            elif ratio < 0.5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme short bias ({ratio:.2f}x) - squeeze potential"
            elif ratio < 0.7:
                signal, score = SignalStrength.BUY, 1
                desc = f"Short bias ({ratio:.2f}x)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Balanced positioning ({ratio:.2f}x)"
            
            return SignalResult(
                name="Long/Short Ratio",
                category="sentiment",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"ratio": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching long/short ratio: {e}")
            return self._unavailable_signal("Long/Short Ratio", "sentiment")
    
    async def _get_retail_institutional(self) -> SignalResult:
        """
        Retail vs Institutional positioning.
        Retail panic selling + Institutional buying: Strong buy
        """
        try:
            data = await self._fetch_retail_institutional()
            if data is None:
                return self._unavailable_signal("Retail vs Institutional", "sentiment")
            
            retail_sentiment = data.get("retail", 0)  # -100 to +100
            institutional_sentiment = data.get("institutional", 0)
            
            divergence = institutional_sentiment - retail_sentiment
            
            if divergence > 50:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Smart money buying, retail selling (div: {divergence:+.0f})"
            elif divergence > 25:
                signal, score = SignalStrength.BUY, 1
                desc = f"Institutional accumulation (div: {divergence:+.0f})"
            elif divergence < -50:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Smart money selling, retail buying (div: {divergence:+.0f})"
            elif divergence < -25:
                signal, score = SignalStrength.SELL, -1
                desc = f"Institutional distribution (div: {divergence:+.0f})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Aligned positioning (div: {divergence:+.0f})"
            
            return SignalResult(
                name="Retail vs Institutional",
                category="sentiment",
                value=divergence,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={
                    "retail": retail_sentiment,
                    "institutional": institutional_sentiment,
                    "divergence": divergence
                }
            )
        except Exception as e:
            logger.error(f"Error fetching retail/institutional: {e}")
            return self._unavailable_signal("Retail vs Institutional", "sentiment")
    
    async def _get_influencer_sentiment(self) -> SignalResult:
        """
        Crypto Twitter influencer sentiment.
        Top accounts consensus bearish: Contrarian buy
        """
        try:
            data = await self._fetch_influencer_sentiment()
            if data is None:
                return self._unavailable_signal("Influencer Sentiment", "sentiment")
            
            bullish_pct = data.get("bullish_pct", 50)
            
            if bullish_pct < 20:
                signal, score = SignalStrength.BUY, 1
                desc = f"Influencers very bearish ({bullish_pct}% bullish)"
            elif bullish_pct > 80:
                signal, score = SignalStrength.SELL, -1
                desc = f"Influencers very bullish ({bullish_pct}% bullish) - caution"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Mixed influencer views ({bullish_pct}% bullish)"
            
            return SignalResult(
                name="Influencer Sentiment",
                category="sentiment",
                value=bullish_pct,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"bullish_pct": bullish_pct}
            )
        except Exception as e:
            logger.error(f"Error fetching influencer sentiment: {e}")
            return self._unavailable_signal("Influencer Sentiment", "sentiment")
    
    # =========================================================================
    # CATEGORY 3: ON-CHAIN METRICS
    # =========================================================================
    
    async def _get_exchange_flows(self, asset: str) -> SignalResult:
        """
        Exchange inflows/outflows.
        Net outflows: Bullish (coins to cold storage)
        Net inflows: Bearish (potential selling)
        """
        try:
            data = await self._fetch_exchange_flows(asset)
            if data is None:
                return self._unavailable_signal("Exchange Flows", "onchain")
            
            net_flow = data.get("net_flow", 0)  # Negative = outflows
            flow_usd = data.get("flow_usd", 0)
            
            if net_flow < -10000:  # Large outflows (BTC)
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Large exchange outflows ({net_flow:,.0f} {asset}) - accumulation"
            elif net_flow < -1000:
                signal, score = SignalStrength.BUY, 1
                desc = f"Net outflows ({net_flow:,.0f} {asset})"
            elif net_flow > 10000:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Large exchange inflows ({net_flow:+,.0f} {asset}) - sell pressure"
            elif net_flow > 1000:
                signal, score = SignalStrength.SELL, -1
                desc = f"Net inflows ({net_flow:+,.0f} {asset})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral exchange flow ({net_flow:+,.0f} {asset})"
            
            return SignalResult(
                name="Exchange Flows",
                category="onchain",
                value=net_flow,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={"net_flow": net_flow, "flow_usd": flow_usd}
            )
        except Exception as e:
            logger.error(f"Error fetching exchange flows: {e}")
            return self._unavailable_signal("Exchange Flows", "onchain")
    
    async def _get_whale_movements(self, asset: str) -> SignalResult:
        """
        Whale wallet movements (>1000 BTC or equivalent).
        Whale accumulation: Bullish
        Whale distribution: Bearish
        """
        try:
            data = await self._fetch_whale_data(asset)
            if data is None:
                return self._unavailable_signal("Whale Movements", "onchain")
            
            accumulation_score = data.get("accumulation", 0)  # -100 to +100
            large_txns = data.get("large_transactions", 0)
            
            if accumulation_score > 50:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Whales accumulating ({accumulation_score:+.0f})"
            elif accumulation_score > 20:
                signal, score = SignalStrength.BUY, 1
                desc = f"Whale buying trend ({accumulation_score:+.0f})"
            elif accumulation_score < -50:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Whales distributing ({accumulation_score:+.0f})"
            elif accumulation_score < -20:
                signal, score = SignalStrength.SELL, -1
                desc = f"Whale selling trend ({accumulation_score:+.0f})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral whale activity ({accumulation_score:+.0f})"
            
            return SignalResult(
                name="Whale Movements",
                category="onchain",
                value=accumulation_score,
                signal=signal,
                score=score,
                weight=1.3,
                description=desc,
                details={
                    "accumulation_score": accumulation_score,
                    "large_transactions": large_txns
                }
            )
        except Exception as e:
            logger.error(f"Error fetching whale data: {e}")
            return self._unavailable_signal("Whale Movements", "onchain")
    
    async def _get_active_addresses(self, asset: str) -> SignalResult:
        """
        Active addresses trend.
        Rising during dip: Bullish (accumulation)
        Falling sharply: Network exodus
        """
        try:
            data = await self._fetch_active_addresses(asset)
            if data is None:
                return self._unavailable_signal("Active Addresses", "onchain")
            
            current = data.get("current", 0)
            avg_30d = data.get("avg_30d", current)
            change_pct = ((current - avg_30d) / avg_30d * 100) if avg_30d > 0 else 0
            
            if change_pct > 20:
                signal, score = SignalStrength.BUY, 1
                desc = f"Active addresses surging ({change_pct:+.1f}%)"
            elif change_pct < -20:
                signal, score = SignalStrength.SELL, -1
                desc = f"Active addresses declining ({change_pct:+.1f}%)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stable address activity ({change_pct:+.1f}%)"
            
            return SignalResult(
                name="Active Addresses",
                category="onchain",
                value=change_pct,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={
                    "current": current,
                    "avg_30d": avg_30d,
                    "change_pct": change_pct
                }
            )
        except Exception as e:
            logger.error(f"Error fetching active addresses: {e}")
            return self._unavailable_signal("Active Addresses", "onchain")
    
    async def _get_mvrv_zscore(self, asset: str) -> SignalResult:
        """
        MVRV Z-Score: Market Value to Realized Value.
        < 0: Undervalued (Strong Buy)
        0-2: Fair value
        2-6: Overvalued
        > 6: Extremely overvalued (Strong Sell)
        """
        try:
            data = await self._fetch_mvrv(asset)
            if data is None:
                return self._unavailable_signal("MVRV Z-Score", "onchain")
            
            zscore = data.get("zscore", 0)
            mvrv = data.get("mvrv", 1)
            
            if zscore < 0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"MVRV Z-Score {zscore:.2f} - below realized value, historically rare"
            elif zscore < 2:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"MVRV Z-Score {zscore:.2f} - fair value range"
            elif zscore < 6:
                signal, score = SignalStrength.SELL, -1
                desc = f"MVRV Z-Score {zscore:.2f} - overvalued"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"MVRV Z-Score {zscore:.2f} - extreme overvaluation"
            
            return SignalResult(
                name="MVRV Z-Score",
                category="onchain",
                value=zscore,
                signal=signal,
                score=score,
                weight=1.4,
                description=desc,
                details={"zscore": zscore, "mvrv": mvrv}
            )
        except Exception as e:
            logger.error(f"Error fetching MVRV: {e}")
            return self._unavailable_signal("MVRV Z-Score", "onchain")
    
    async def _get_sopr(self, asset: str) -> SignalResult:
        """
        SOPR (Spent Output Profit Ratio).
        < 1: Selling at loss (capitulation) - Buy
        > 1: Selling at profit
        = 1: Breakeven (key level)
        """
        try:
            data = await self._fetch_sopr(asset)
            if data is None:
                return self._unavailable_signal("SOPR", "onchain")
            
            sopr = data.get("sopr", 1)
            sopr_7d = data.get("sopr_7d_avg", sopr)
            
            if sopr < 0.95:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"SOPR {sopr:.3f} - deep capitulation, selling at significant loss"
            elif sopr < 1.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"SOPR {sopr:.3f} - selling at loss"
            elif abs(sopr - 1.0) < 0.02:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"SOPR {sopr:.3f} - at breakeven (key support/resistance)"
            elif sopr > 1.05:
                signal, score = SignalStrength.SELL, -1
                desc = f"SOPR {sopr:.3f} - profit taking"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"SOPR {sopr:.3f} - slight profit"
            
            return SignalResult(
                name="SOPR",
                category="onchain",
                value=sopr,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={"sopr": sopr, "sopr_7d_avg": sopr_7d}
            )
        except Exception as e:
            logger.error(f"Error fetching SOPR: {e}")
            return self._unavailable_signal("SOPR", "onchain")
    
    async def _get_nupl(self, asset: str) -> SignalResult:
        """
        NUPL (Net Unrealized Profit/Loss).
        < 0: Capitulation (Buy)
        0-0.25: Hope/Fear
        0.25-0.5: Optimism
        0.5-0.75: Belief/Greed
        > 0.75: Euphoria (Sell)
        """
        try:
            data = await self._fetch_nupl(asset)
            if data is None:
                return self._unavailable_signal("NUPL", "onchain")
            
            nupl = data.get("nupl", 0)
            
            if nupl < 0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"NUPL {nupl:.2f} - CAPITULATION, market in loss"
            elif nupl < 0.25:
                signal, score = SignalStrength.BUY, 1
                desc = f"NUPL {nupl:.2f} - Hope/Fear zone"
            elif nupl < 0.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"NUPL {nupl:.2f} - Optimism"
            elif nupl < 0.75:
                signal, score = SignalStrength.SELL, -1
                desc = f"NUPL {nupl:.2f} - Belief/Greed"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"NUPL {nupl:.2f} - EUPHORIA, extreme profit"
            
            return SignalResult(
                name="NUPL",
                category="onchain",
                value=nupl,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                details={"nupl": nupl}
            )
        except Exception as e:
            logger.error(f"Error fetching NUPL: {e}")
            return self._unavailable_signal("NUPL", "onchain")
    
    async def _get_puell_multiple(self, asset: str) -> SignalResult:
        """
        Puell Multiple: Daily miner revenue vs 365-day average.
        < 0.5: Undervalued (Buy)
        0.5-1.2: Fair value
        > 4: Overvalued (Sell)
        """
        try:
            data = await self._fetch_puell_multiple(asset)
            if data is None:
                return self._unavailable_signal("Puell Multiple", "onchain")
            
            puell = data.get("puell", 1)
            
            if puell < 0.5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Puell Multiple {puell:.2f} - miners under stress, historically great entry"
            elif puell < 1.2:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Puell Multiple {puell:.2f} - fair value"
            elif puell < 4:
                signal, score = SignalStrength.SELL, -1
                desc = f"Puell Multiple {puell:.2f} - elevated"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Puell Multiple {puell:.2f} - extreme, cycle top territory"
            
            return SignalResult(
                name="Puell Multiple",
                category="onchain",
                value=puell,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"puell": puell}
            )
        except Exception as e:
            logger.error(f"Error fetching Puell: {e}")
            return self._unavailable_signal("Puell Multiple", "onchain")
    
    async def _get_reserve_risk(self, asset: str) -> SignalResult:
        """
        Reserve Risk: Confidence vs price.
        < 0.002: Undervalued (Strong Buy)
        0.002-0.008: Fair value
        > 0.008: Overvalued
        """
        try:
            data = await self._fetch_reserve_risk(asset)
            if data is None:
                return self._unavailable_signal("Reserve Risk", "onchain")
            
            reserve_risk = data.get("reserve_risk", 0.005)
            
            if reserve_risk < 0.002:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Reserve Risk {reserve_risk:.4f} - high confidence, low price"
            elif reserve_risk < 0.008:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Reserve Risk {reserve_risk:.4f} - fair value"
            else:
                signal, score = SignalStrength.SELL, -1
                desc = f"Reserve Risk {reserve_risk:.4f} - low confidence, high price"
            
            return SignalResult(
                name="Reserve Risk",
                category="onchain",
                value=reserve_risk,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"reserve_risk": reserve_risk}
            )
        except Exception as e:
            logger.error(f"Error fetching Reserve Risk: {e}")
            return self._unavailable_signal("Reserve Risk", "onchain")
    
    async def _get_realized_price_bands(self, asset: str) -> SignalResult:
        """
        Price vs Realized Price bands.
        Below realized price: Historically great buying zone
        """
        try:
            data = await self._fetch_realized_price(asset)
            if data is None:
                return self._unavailable_signal("Realized Price", "onchain")
            
            price = data.get("price", 0)
            realized_price = data.get("realized_price", price)
            ratio = price / realized_price if realized_price > 0 else 1
            
            if ratio < 0.8:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price {ratio:.0%} of realized - deep value"
            elif ratio < 1.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price {ratio:.0%} of realized - below avg cost basis"
            elif ratio < 1.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price {ratio:.0%} of realized - normal"
            elif ratio < 2.5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Price {ratio:.0%} of realized - extended"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Price {ratio:.0%} of realized - extreme"
            
            return SignalResult(
                name="Realized Price",
                category="onchain",
                value=ratio,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={
                    "price": price,
                    "realized_price": realized_price,
                    "ratio": ratio
                }
            )
        except Exception as e:
            logger.error(f"Error fetching Realized Price: {e}")
            return self._unavailable_signal("Realized Price", "onchain")
    
    async def _get_hodl_waves(self, asset: str) -> SignalResult:
        """
        HODL Waves: Long-term holder vs short-term holder supply.
        LTH accumulating: Bullish
        STH increasing (distribution): Bearish
        """
        try:
            data = await self._fetch_hodl_waves(asset)
            if data is None:
                return self._unavailable_signal("HODL Waves", "onchain")
            
            lth_supply_pct = data.get("lth_supply_pct", 60)
            lth_change = data.get("lth_change_30d", 0)
            
            if lth_change > 2:
                signal, score = SignalStrength.BUY, 1
                desc = f"LTH accumulating (+{lth_change:.1f}% in 30d)"
            elif lth_change < -3:
                signal, score = SignalStrength.SELL, -1
                desc = f"LTH distributing ({lth_change:.1f}% in 30d)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"LTH supply stable ({lth_supply_pct:.1f}% of total)"
            
            return SignalResult(
                name="HODL Waves",
                category="onchain",
                value=lth_supply_pct,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={
                    "lth_supply_pct": lth_supply_pct,
                    "lth_change_30d": lth_change
                }
            )
        except Exception as e:
            logger.error(f"Error fetching HODL waves: {e}")
            return self._unavailable_signal("HODL Waves", "onchain")
    
    async def _get_coin_days_destroyed(self, asset: str) -> SignalResult:
        """
        Coin Days Destroyed: Measures movement of old coins.
        Spike: Old coins moving (potential distribution)
        Low: Accumulation phase
        """
        try:
            data = await self._fetch_cdd(asset)
            if data is None:
                return self._unavailable_signal("Coin Days Destroyed", "onchain")
            
            cdd = data.get("cdd", 0)
            cdd_avg = data.get("cdd_avg_90d", cdd)
            ratio = cdd / cdd_avg if cdd_avg > 0 else 1
            
            if ratio > 3:
                signal, score = SignalStrength.SELL, -1
                desc = f"CDD spike ({ratio:.1f}x avg) - old coins moving"
            elif ratio < 0.5:
                signal, score = SignalStrength.BUY, 1
                desc = f"CDD low ({ratio:.1f}x avg) - accumulation"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"CDD normal ({ratio:.1f}x avg)"
            
            return SignalResult(
                name="Coin Days Destroyed",
                category="onchain",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"cdd": cdd, "cdd_avg_90d": cdd_avg, "ratio": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching CDD: {e}")
            return self._unavailable_signal("Coin Days Destroyed", "onchain")
    
    async def _get_nvt_ratio(self, asset: str) -> SignalResult:
        """
        NVT Ratio: Network Value to Transaction Volume.
        < 50: Undervalued (network busy)
        50-90: Fair
        > 90: Overvalued (network quiet)
        """
        try:
            data = await self._fetch_nvt(asset)
            if data is None:
                return self._unavailable_signal("NVT Ratio", "onchain")
            
            nvt = data.get("nvt", 70)
            
            if nvt < 50:
                signal, score = SignalStrength.BUY, 1
                desc = f"NVT {nvt:.0f} - high network usage, undervalued"
            elif nvt < 90:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"NVT {nvt:.0f} - fair value"
            elif nvt < 150:
                signal, score = SignalStrength.SELL, -1
                desc = f"NVT {nvt:.0f} - low usage, overvalued"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"NVT {nvt:.0f} - very low usage, bubble territory"
            
            return SignalResult(
                name="NVT Ratio",
                category="onchain",
                value=nvt,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"nvt": nvt}
            )
        except Exception as e:
            logger.error(f"Error fetching NVT: {e}")
            return self._unavailable_signal("NVT Ratio", "onchain")
    
    # =========================================================================
    # CATEGORY 4: DERIVATIVES DATA
    # =========================================================================
    
    async def _get_funding_rates(self, asset: str) -> SignalResult:
        """
        Perpetual funding rates.
        Very negative: Shorts paying (buy signal)
        Very positive: Longs paying (sell signal)
        """
        try:
            data = await self._fetch_funding_rates(asset)
            if data is None:
                return self._unavailable_signal("Funding Rates", "derivatives")
            
            rate = data.get("rate", 0)  # Typically -0.1% to +0.1%
            rate_pct = rate * 100
            
            if rate_pct < -0.05:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Negative funding ({rate_pct:.3f}%) - shorts crowded"
            elif rate_pct < -0.01:
                signal, score = SignalStrength.BUY, 1
                desc = f"Slightly negative funding ({rate_pct:.3f}%)"
            elif rate_pct > 0.1:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"High funding ({rate_pct:.3f}%) - longs overleveraged"
            elif rate_pct > 0.03:
                signal, score = SignalStrength.SELL, -1
                desc = f"Elevated funding ({rate_pct:.3f}%)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal funding ({rate_pct:.3f}%)"
            
            return SignalResult(
                name="Funding Rates",
                category="derivatives",
                value=rate,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                details={"rate": rate, "rate_pct": rate_pct}
            )
        except Exception as e:
            logger.error(f"Error fetching funding rates: {e}")
            return self._unavailable_signal("Funding Rates", "derivatives")
    
    async def _get_open_interest(self, asset: str) -> SignalResult:
        """
        Open Interest changes.
        Rising OI + rising price: Healthy trend
        Falling OI + falling price: Capitulation (buy)
        Rising OI + falling price: Short buildup
        """
        try:
            data = await self._fetch_open_interest(asset)
            if data is None:
                return self._unavailable_signal("Open Interest", "derivatives")
            
            oi_change = data.get("change_24h_pct", 0)
            price_change = data.get("price_change_24h", 0)
            
            if oi_change < -10 and price_change < -5:
                signal, score = SignalStrength.BUY, 1
                desc = f"OI declining ({oi_change:+.1f}%) with price ({price_change:+.1f}%) - deleveraging"
            elif oi_change > 10 and price_change < -5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"OI rising ({oi_change:+.1f}%) + price falling - shorts piling in"
            elif oi_change > 10 and price_change > 5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"OI and price rising - healthy trend"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"OI change {oi_change:+.1f}%, price {price_change:+.1f}%"
            
            return SignalResult(
                name="Open Interest",
                category="derivatives",
                value=oi_change,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={
                    "oi_change_24h_pct": oi_change,
                    "price_change_24h": price_change
                }
            )
        except Exception as e:
            logger.error(f"Error fetching OI: {e}")
            return self._unavailable_signal("Open Interest", "derivatives")
    
    async def _get_liquidations(self, asset: str) -> SignalResult:
        """
        Liquidation data (24h).
        Large long liquidations: Forced selling exhausted (buy)
        Large short liquidations: Squeeze may reverse (neutral)
        """
        try:
            data = await self._fetch_liquidations(asset)
            if data is None:
                return self._unavailable_signal("Liquidations", "derivatives")
            
            long_liq = data.get("long_liquidations_usd", 0)
            short_liq = data.get("short_liquidations_usd", 0)
            total = long_liq + short_liq
            
            # Thresholds in millions USD
            if long_liq > 500_000_000:  # $500M+ long liquidations
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Massive long liquidations (${long_liq/1e6:.0f}M) - capitulation"
            elif long_liq > 200_000_000:
                signal, score = SignalStrength.BUY, 1
                desc = f"Heavy long liquidations (${long_liq/1e6:.0f}M)"
            elif short_liq > 500_000_000:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Short squeeze (${short_liq/1e6:.0f}M) - may reverse"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal liquidations (${total/1e6:.0f}M total)"
            
            return SignalResult(
                name="Liquidations",
                category="derivatives",
                value=total,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={
                    "long_liquidations": long_liq,
                    "short_liquidations": short_liq,
                    "total": total
                }
            )
        except Exception as e:
            logger.error(f"Error fetching liquidations: {e}")
            return self._unavailable_signal("Liquidations", "derivatives")
    
    async def _get_options_put_call(self, asset: str) -> SignalResult:
        """
        Options Put/Call ratio.
        High put ratio: Hedging/fear (contrarian buy)
        High call ratio: Greed (contrarian sell)
        """
        try:
            data = await self._fetch_options_data(asset)
            if data is None:
                return self._unavailable_signal("Put/Call Ratio", "derivatives")
            
            pc_ratio = data.get("put_call_ratio", 1)
            
            if pc_ratio > 1.5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Put/Call {pc_ratio:.2f} - extreme hedging, contrarian buy"
            elif pc_ratio > 1.2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Put/Call {pc_ratio:.2f} - elevated fear"
            elif pc_ratio < 0.5:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Put/Call {pc_ratio:.2f} - extreme greed"
            elif pc_ratio < 0.7:
                signal, score = SignalStrength.SELL, -1
                desc = f"Put/Call {pc_ratio:.2f} - bullish positioning"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Put/Call {pc_ratio:.2f} - balanced"
            
            return SignalResult(
                name="Put/Call Ratio",
                category="derivatives",
                value=pc_ratio,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"put_call_ratio": pc_ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching put/call: {e}")
            return self._unavailable_signal("Put/Call Ratio", "derivatives")
    
    async def _get_options_skew(self, asset: str) -> SignalResult:
        """
        25-delta options skew.
        Positive skew (puts expensive): Fear/hedging
        Negative skew (calls expensive): Greed
        """
        try:
            data = await self._fetch_options_skew(asset)
            if data is None:
                return self._unavailable_signal("Options Skew", "derivatives")
            
            skew = data.get("skew_25d", 0)  # Positive = puts expensive
            
            if skew > 15:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"High put skew ({skew:+.1f}%) - extreme downside hedging"
            elif skew > 5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Put skew ({skew:+.1f}%) - defensive positioning"
            elif skew < -10:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Call skew ({skew:+.1f}%) - extreme greed"
            elif skew < -3:
                signal, score = SignalStrength.SELL, -1
                desc = f"Call skew ({skew:+.1f}%) - bullish options flow"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Balanced skew ({skew:+.1f}%)"
            
            return SignalResult(
                name="Options Skew",
                category="derivatives",
                value=skew,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"skew_25d": skew}
            )
        except Exception as e:
            logger.error(f"Error fetching options skew: {e}")
            return self._unavailable_signal("Options Skew", "derivatives")
    
    async def _get_max_pain(self, asset: str) -> SignalResult:
        """
        Options max pain price.
        Price far below max pain: Likely to gravitate up
        Price far above max pain: Likely to gravitate down
        """
        try:
            data = await self._fetch_max_pain(asset)
            if data is None:
                return self._unavailable_signal("Max Pain", "derivatives")
            
            price = data.get("price", 0)
            max_pain = data.get("max_pain", price)
            pct_diff = ((price - max_pain) / max_pain * 100) if max_pain > 0 else 0
            
            if pct_diff < -10:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price {abs(pct_diff):.1f}% below max pain - magnet pull up"
            elif pct_diff > 10:
                signal, score = SignalStrength.SELL, -1
                desc = f"Price {pct_diff:.1f}% above max pain - magnet pull down"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price near max pain ({pct_diff:+.1f}%)"
            
            return SignalResult(
                name="Max Pain",
                category="derivatives",
                value=pct_diff,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={
                    "price": price,
                    "max_pain": max_pain,
                    "pct_diff": pct_diff
                }
            )
        except Exception as e:
            logger.error(f"Error fetching max pain: {e}")
            return self._unavailable_signal("Max Pain", "derivatives")
    
    async def _get_futures_basis(self, asset: str) -> SignalResult:
        """
        Futures basis (premium/discount to spot).
        Deep discount: Bearish sentiment (buy)
        High premium: Bullish sentiment (sell)
        """
        try:
            data = await self._fetch_futures_basis(asset)
            if data is None:
                return self._unavailable_signal("Futures Basis", "derivatives")
            
            basis = data.get("annualized_basis", 0)  # %
            
            if basis < -5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Futures at discount ({basis:+.1f}% ann.) - extreme bearish"
            elif basis < 0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Slight backwardation ({basis:+.1f}% ann.)"
            elif basis > 30:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Extreme contango ({basis:+.1f}% ann.) - overleveraged"
            elif basis > 15:
                signal, score = SignalStrength.SELL, -1
                desc = f"High contango ({basis:+.1f}% ann.)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal basis ({basis:+.1f}% ann.)"
            
            return SignalResult(
                name="Futures Basis",
                category="derivatives",
                value=basis,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"annualized_basis": basis}
            )
        except Exception as e:
            logger.error(f"Error fetching futures basis: {e}")
            return self._unavailable_signal("Futures Basis", "derivatives")
    
    async def _get_term_structure(self, asset: str) -> SignalResult:
        """
        Futures term structure.
        Backwardation: Bearish near-term
        Steep contango: Bullish consensus
        """
        try:
            data = await self._fetch_term_structure(asset)
            if data is None:
                return self._unavailable_signal("Term Structure", "derivatives")
            
            structure = data.get("structure", "contango")  # contango/backwardation
            steepness = data.get("steepness", 0)  # % per month
            
            if structure == "backwardation" and steepness > 2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Backwardation ({steepness:.1f}%/mo) - near-term pressure"
            elif structure == "contango" and steepness > 3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Steep contango ({steepness:.1f}%/mo) - crowded longs"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal {structure} ({steepness:.1f}%/mo)"
            
            return SignalResult(
                name="Term Structure",
                category="derivatives",
                value=steepness,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"structure": structure, "steepness": steepness}
            )
        except Exception as e:
            logger.error(f"Error fetching term structure: {e}")
            return self._unavailable_signal("Term Structure", "derivatives")
    
    # =========================================================================
    # CATEGORY 5: MACRO & CROSS-MARKET
    # =========================================================================
    
    async def _get_dxy(self) -> SignalResult:
        """
        DXY (Dollar Index).
        Rising DXY: Risk-off, bearish for crypto
        Falling DXY: Risk-on, bullish for crypto
        """
        try:
            data = await self._fetch_dxy()
            if data is None:
                return self._unavailable_signal("DXY", "macro")
            
            dxy = data.get("value", 100)
            change_1w = data.get("change_1w", 0)
            
            if change_1w > 2:
                signal, score = SignalStrength.SELL, -1
                desc = f"DXY surging ({change_1w:+.1f}% weekly) - risk-off"
            elif change_1w < -2:
                signal, score = SignalStrength.BUY, 1
                desc = f"DXY falling ({change_1w:+.1f}% weekly) - risk-on"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"DXY stable at {dxy:.1f} ({change_1w:+.1f}% weekly)"
            
            return SignalResult(
                name="DXY",
                category="macro",
                value=dxy,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"dxy": dxy, "change_1w": change_1w}
            )
        except Exception as e:
            logger.error(f"Error fetching DXY: {e}")
            return self._unavailable_signal("DXY", "macro")
    
    async def _get_sp500_correlation(self, asset: str) -> SignalResult:
        """
        S&P 500 correlation and divergence.
        Crypto down, S&P up: Crypto-specific weakness (opportunity)
        Both down: Macro risk-off
        """
        try:
            data = await self._fetch_sp500_data()
            if data is None:
                return self._unavailable_signal("S&P 500 Correlation", "macro")
            
            sp500_change = data.get("change_1w", 0)
            crypto_change = data.get("btc_change_1w", 0)
            correlation = data.get("correlation_30d", 0.5)
            
            divergence = crypto_change - sp500_change
            
            if divergence < -10 and sp500_change > 0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Crypto lagging S&P by {abs(divergence):.1f}% - catch-up potential"
            elif divergence < -5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Crypto underperforming ({divergence:+.1f}%)"
            elif sp500_change < -5 and crypto_change < -5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Macro selloff - both down ~{abs(crypto_change):.1f}%"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Correlation: {correlation:.2f}, divergence: {divergence:+.1f}%"
            
            return SignalResult(
                name="S&P 500 Correlation",
                category="macro",
                value=divergence,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={
                    "sp500_change": sp500_change,
                    "crypto_change": crypto_change,
                    "correlation": correlation,
                    "divergence": divergence
                }
            )
        except Exception as e:
            logger.error(f"Error fetching S&P data: {e}")
            return self._unavailable_signal("S&P 500 Correlation", "macro")
    
    async def _get_gold_correlation(self) -> SignalResult:
        """
        Gold correlation with Bitcoin.
        BTC lagging gold rally: Potential catch-up
        """
        try:
            data = await self._fetch_gold_data()
            if data is None:
                return self._unavailable_signal("Gold Correlation", "macro")
            
            gold_change = data.get("change_1m", 0)
            btc_change = data.get("btc_change_1m", 0)
            
            divergence = btc_change - gold_change
            
            if gold_change > 5 and divergence < -10:
                signal, score = SignalStrength.BUY, 1
                desc = f"BTC lagging gold rally by {abs(divergence):.1f}%"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Gold {gold_change:+.1f}%, BTC {btc_change:+.1f}%"
            
            return SignalResult(
                name="Gold Correlation",
                category="macro",
                value=divergence,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={
                    "gold_change": gold_change,
                    "btc_change": btc_change,
                    "divergence": divergence
                }
            )
        except Exception as e:
            logger.error(f"Error fetching gold data: {e}")
            return self._unavailable_signal("Gold Correlation", "macro")
    
    async def _get_treasury_yields(self) -> SignalResult:
        """
        10Y Treasury yield changes.
        Rapidly rising yields: Risk-off
        Falling yields: Risk-on
        """
        try:
            data = await self._fetch_treasury_data()
            if data is None:
                return self._unavailable_signal("Treasury Yields", "macro")
            
            yield_10y = data.get("yield_10y", 4.0)
            change_1m = data.get("change_1m", 0)  # In basis points
            
            if change_1m > 50:  # +50bps in a month
                signal, score = SignalStrength.SELL, -1
                desc = f"Yields spiking ({change_1m:+.0f}bps/mo) - risk-off"
            elif change_1m < -30:
                signal, score = SignalStrength.BUY, 1
                desc = f"Yields falling ({change_1m:+.0f}bps/mo) - risk-on"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"10Y at {yield_10y:.2f}% ({change_1m:+.0f}bps/mo)"
            
            return SignalResult(
                name="Treasury Yields",
                category="macro",
                value=yield_10y,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"yield_10y": yield_10y, "change_1m_bps": change_1m}
            )
        except Exception as e:
            logger.error(f"Error fetching treasury data: {e}")
            return self._unavailable_signal("Treasury Yields", "macro")
    
    async def _get_vix(self) -> SignalResult:
        """
        VIX (CBOE Volatility Index).
        VIX spike: Market panic (contrarian opportunity)
        VIX very low: Complacency
        """
        try:
            data = await self._fetch_vix()
            if data is None:
                return self._unavailable_signal("VIX", "macro")
            
            vix = data.get("value", 20)
            
            if vix > 35:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"VIX spike ({vix:.1f}) - market panic, contrarian buy"
            elif vix > 25:
                signal, score = SignalStrength.BUY, 1
                desc = f"Elevated VIX ({vix:.1f}) - fear in markets"
            elif vix < 12:
                signal, score = SignalStrength.SELL, -1
                desc = f"VIX very low ({vix:.1f}) - extreme complacency"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"VIX normal ({vix:.1f})"
            
            return SignalResult(
                name="VIX",
                category="macro",
                value=vix,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"vix": vix}
            )
        except Exception as e:
            logger.error(f"Error fetching VIX: {e}")
            return self._unavailable_signal("VIX", "macro")
    
    async def _get_stablecoin_supply_ratio(self) -> SignalResult:
        """
        Stablecoin Supply Ratio (SSR).
        Low SSR: High buying power relative to BTC mcap
        High SSR: Low buying power
        """
        try:
            data = await self._fetch_stablecoin_data()
            if data is None:
                return self._unavailable_signal("Stablecoin Supply Ratio", "macro")
            
            ssr = data.get("ssr", 10)
            stablecoin_mcap = data.get("stablecoin_mcap", 0)
            
            if ssr < 5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Low SSR ({ssr:.1f}) - high buying power available"
            elif ssr > 20:
                signal, score = SignalStrength.SELL, -1
                desc = f"High SSR ({ssr:.1f}) - limited dry powder"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal SSR ({ssr:.1f})"
            
            return SignalResult(
                name="Stablecoin Supply Ratio",
                category="macro",
                value=ssr,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"ssr": ssr, "stablecoin_mcap": stablecoin_mcap}
            )
        except Exception as e:
            logger.error(f"Error fetching SSR: {e}")
            return self._unavailable_signal("Stablecoin Supply Ratio", "macro")
    
    async def _get_coinbase_premium(self, asset: str) -> SignalResult:
        """
        Coinbase premium (US institutional interest).
        Positive premium: US institutions buying
        Negative premium: US selling pressure
        """
        try:
            data = await self._fetch_coinbase_premium(asset)
            if data is None:
                return self._unavailable_signal("Coinbase Premium", "macro")
            
            premium = data.get("premium_pct", 0)
            
            if premium > 1.0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Strong Coinbase premium ({premium:+.2f}%) - US institutions buying"
            elif premium > 0.2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Coinbase premium ({premium:+.2f}%) - US demand"
            elif premium < -0.5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Coinbase discount ({premium:+.2f}%) - US selling"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral Coinbase spread ({premium:+.2f}%)"
            
            return SignalResult(
                name="Coinbase Premium",
                category="macro",
                value=premium,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"premium_pct": premium}
            )
        except Exception as e:
            logger.error(f"Error fetching Coinbase premium: {e}")
            return self._unavailable_signal("Coinbase Premium", "macro")
    
    async def _get_korea_premium(self, asset: str) -> SignalResult:
        """
        Korea premium (Kimchi premium).
        High premium: Korean retail FOMO
        Negative premium: Korean selling
        """
        try:
            data = await self._fetch_korea_premium(asset)
            if data is None:
                return self._unavailable_signal("Korea Premium", "macro")
            
            premium = data.get("premium_pct", 0)
            
            if premium > 5:
                signal, score = SignalStrength.SELL, -1
                desc = f"High Kimchi premium ({premium:+.1f}%) - retail FOMO"
            elif premium > 2:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Moderate Korea premium ({premium:+.1f}%)"
            elif premium < -2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Korea discount ({premium:+.1f}%) - local selling"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal Korea spread ({premium:+.1f}%)"
            
            return SignalResult(
                name="Korea Premium",
                category="macro",
                value=premium,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"premium_pct": premium}
            )
        except Exception as e:
            logger.error(f"Error fetching Korea premium: {e}")
            return self._unavailable_signal("Korea Premium", "macro")
    
    # =========================================================================
    # CATEGORY 6: NETWORK & MINING
    # =========================================================================
    
    async def _get_hash_rate(self, asset: str) -> SignalResult:
        """
        Hash rate trend.
        Rising hash rate: Network healthy, miners confident
        Falling hash rate: Miner stress
        """
        try:
            data = await self._fetch_hash_rate(asset)
            if data is None:
                return self._unavailable_signal("Hash Rate", "mining")
            
            hash_rate = data.get("hash_rate", 0)
            change_30d = data.get("change_30d_pct", 0)
            
            if change_30d > 10:
                signal, score = SignalStrength.BUY, 1
                desc = f"Hash rate surging ({change_30d:+.1f}%/mo) - miners bullish"
            elif change_30d < -10:
                signal, score = SignalStrength.SELL, -1
                desc = f"Hash rate declining ({change_30d:+.1f}%/mo) - miner stress"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stable hash rate ({change_30d:+.1f}%/mo)"
            
            return SignalResult(
                name="Hash Rate",
                category="mining",
                value=change_30d,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"hash_rate": hash_rate, "change_30d_pct": change_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching hash rate: {e}")
            return self._unavailable_signal("Hash Rate", "mining")
    
    async def _get_difficulty_ribbon(self, asset: str) -> SignalResult:
        """
        Difficulty ribbon compression.
        Compression: Miner capitulation (buy signal)
        Expansion: Healthy network
        """
        try:
            data = await self._fetch_difficulty_ribbon(asset)
            if data is None:
                return self._unavailable_signal("Difficulty Ribbon", "mining")
            
            compression = data.get("compression", 0)  # 0-1, higher = more compressed
            
            if compression > 0.8:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Ribbon compression ({compression:.0%}) - miner capitulation"
            elif compression > 0.6:
                signal, score = SignalStrength.BUY, 1
                desc = f"Moderate compression ({compression:.0%})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal ribbon ({compression:.0%})"
            
            return SignalResult(
                name="Difficulty Ribbon",
                category="mining",
                value=compression,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"compression": compression}
            )
        except Exception as e:
            logger.error(f"Error fetching difficulty ribbon: {e}")
            return self._unavailable_signal("Difficulty Ribbon", "mining")
    
    async def _get_miner_outflows(self, asset: str) -> SignalResult:
        """
        Miner wallet outflows.
        Large outflows: Forced selling (short-term bearish)
        Low outflows: Accumulation
        """
        try:
            data = await self._fetch_miner_flows(asset)
            if data is None:
                return self._unavailable_signal("Miner Outflows", "mining")
            
            outflow_zscore = data.get("outflow_zscore", 0)
            
            if outflow_zscore > 2:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"High miner outflows (z={outflow_zscore:.1f}) - capitulation"
            elif outflow_zscore < -1:
                signal, score = SignalStrength.BUY, 1
                desc = f"Low miner outflows (z={outflow_zscore:.1f}) - accumulating"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal miner flows (z={outflow_zscore:.1f})"
            
            return SignalResult(
                name="Miner Outflows",
                category="mining",
                value=outflow_zscore,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"outflow_zscore": outflow_zscore}
            )
        except Exception as e:
            logger.error(f"Error fetching miner outflows: {e}")
            return self._unavailable_signal("Miner Outflows", "mining")
    
    async def _get_miner_reserve(self, asset: str) -> SignalResult:
        """
        Miner reserve balance.
        Rising reserves: Miners holding (bullish)
        Falling reserves: Miners selling
        """
        try:
            data = await self._fetch_miner_reserve(asset)
            if data is None:
                return self._unavailable_signal("Miner Reserve", "mining")
            
            reserve = data.get("reserve", 0)
            change_30d = data.get("change_30d_pct", 0)
            
            if change_30d > 5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Miner reserves growing ({change_30d:+.1f}%/mo)"
            elif change_30d < -5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Miner reserves declining ({change_30d:+.1f}%/mo)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stable miner reserves ({change_30d:+.1f}%/mo)"
            
            return SignalResult(
                name="Miner Reserve",
                category="mining",
                value=change_30d,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"reserve": reserve, "change_30d_pct": change_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching miner reserve: {e}")
            return self._unavailable_signal("Miner Reserve", "mining")
    
    async def _get_thermocap(self, asset: str) -> SignalResult:
        """
        Thermocap Multiple: Market cap / cumulative miner revenue.
        < 5: Undervalued
        5-30: Fair
        > 40: Overvalued
        """
        try:
            data = await self._fetch_thermocap(asset)
            if data is None:
                return self._unavailable_signal("Thermocap Multiple", "mining")
            
            multiple = data.get("multiple", 15)
            
            if multiple < 5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Thermocap {multiple:.1f}x - deeply undervalued"
            elif multiple < 10:
                signal, score = SignalStrength.BUY, 1
                desc = f"Thermocap {multiple:.1f}x - undervalued"
            elif multiple < 30:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Thermocap {multiple:.1f}x - fair value"
            elif multiple < 50:
                signal, score = SignalStrength.SELL, -1
                desc = f"Thermocap {multiple:.1f}x - overvalued"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Thermocap {multiple:.1f}x - extreme overvaluation"
            
            return SignalResult(
                name="Thermocap Multiple",
                category="mining",
                value=multiple,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"multiple": multiple}
            )
        except Exception as e:
            logger.error(f"Error fetching thermocap: {e}")
            return self._unavailable_signal("Thermocap Multiple", "mining")
    
    async def _get_stock_to_flow(self, asset: str) -> SignalResult:
        """
        Stock-to-Flow deviation.
        Below model: Undervalued
        Above model: Overvalued
        """
        try:
            data = await self._fetch_s2f(asset)
            if data is None:
                return self._unavailable_signal("Stock-to-Flow", "mining")
            
            deviation = data.get("deviation_pct", 0)  # % from model price
            model_price = data.get("model_price", 0)
            actual_price = data.get("actual_price", 0)
            
            if deviation < -50:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"S2F: {deviation:+.0f}% from model - deeply undervalued"
            elif deviation < -20:
                signal, score = SignalStrength.BUY, 1
                desc = f"S2F: {deviation:+.0f}% from model - undervalued"
            elif deviation > 100:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"S2F: {deviation:+.0f}% from model - overextended"
            elif deviation > 50:
                signal, score = SignalStrength.SELL, -1
                desc = f"S2F: {deviation:+.0f}% from model - above fair value"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"S2F: {deviation:+.0f}% from model - fair value"
            
            return SignalResult(
                name="Stock-to-Flow",
                category="mining",
                value=deviation,
                signal=signal,
                score=score,
                weight=0.6,  # S2F has been criticized, lower weight
                description=desc,
                details={
                    "deviation_pct": deviation,
                    "model_price": model_price,
                    "actual_price": actual_price
                }
            )
        except Exception as e:
            logger.error(f"Error fetching S2F: {e}")
            return self._unavailable_signal("Stock-to-Flow", "mining")
    
    # =========================================================================
    # CATEGORY 7: INSTITUTIONAL
    # =========================================================================
    
    async def _get_etf_flows(self, asset: str) -> SignalResult:
        """
        ETF flows (BTC/ETH spot ETFs).
        Net inflows: Institutional demand
        Net outflows: Institutional selling
        """
        try:
            data = await self._fetch_etf_flows(asset)
            if data is None:
                return self._unavailable_signal("ETF Flows", "institutional")
            
            flow_1w = data.get("flow_1w_usd", 0)
            flow_1w_millions = flow_1w / 1e6
            
            if flow_1w > 1e9:  # > $1B weekly
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Massive ETF inflows (${flow_1w_millions:,.0f}M weekly)"
            elif flow_1w > 500e6:
                signal, score = SignalStrength.BUY, 1
                desc = f"Strong ETF inflows (${flow_1w_millions:,.0f}M weekly)"
            elif flow_1w < -500e6:
                signal, score = SignalStrength.SELL, -1
                desc = f"ETF outflows (${flow_1w_millions:,.0f}M weekly)"
            elif flow_1w < -1e9:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Heavy ETF outflows (${flow_1w_millions:,.0f}M weekly)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal ETF flows (${flow_1w_millions:,.0f}M weekly)"
            
            return SignalResult(
                name="ETF Flows",
                category="institutional",
                value=flow_1w,
                signal=signal,
                score=score,
                weight=1.3,
                description=desc,
                details={"flow_1w_usd": flow_1w}
            )
        except Exception as e:
            logger.error(f"Error fetching ETF flows: {e}")
            return self._unavailable_signal("ETF Flows", "institutional")
    
    async def _get_grayscale_premium(self, asset: str) -> SignalResult:
        """
        Grayscale trust premium/discount.
        Large discount: Institutional selling pressure
        Premium: Institutional demand
        """
        try:
            data = await self._fetch_grayscale_premium(asset)
            if data is None:
                return self._unavailable_signal("Grayscale Premium", "institutional")
            
            premium = data.get("premium_pct", 0)
            
            if premium < -20:
                signal, score = SignalStrength.BUY, 1
                desc = f"Deep Grayscale discount ({premium:+.1f}%) - distressed selling"
            elif premium > 10:
                signal, score = SignalStrength.SELL, -1
                desc = f"Grayscale premium ({premium:+.1f}%) - retail FOMO"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal Grayscale spread ({premium:+.1f}%)"
            
            return SignalResult(
                name="Grayscale Premium",
                category="institutional",
                value=premium,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"premium_pct": premium}
            )
        except Exception as e:
            logger.error(f"Error fetching Grayscale premium: {e}")
            return self._unavailable_signal("Grayscale Premium", "institutional")
    
    async def _get_cme_oi(self, asset: str) -> SignalResult:
        """
        CME Futures Open Interest.
        Rising CME OI: Institutional interest increasing
        """
        try:
            data = await self._fetch_cme_oi(asset)
            if data is None:
                return self._unavailable_signal("CME Open Interest", "institutional")
            
            change_1w = data.get("change_1w_pct", 0)
            oi_usd = data.get("oi_usd", 0)
            
            if change_1w > 20:
                signal, score = SignalStrength.BUY, 1
                desc = f"CME OI surging ({change_1w:+.1f}%/wk) - institutional interest"
            elif change_1w < -20:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"CME OI declining ({change_1w:+.1f}%/wk)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stable CME OI ({change_1w:+.1f}%/wk)"
            
            return SignalResult(
                name="CME Open Interest",
                category="institutional",
                value=change_1w,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"change_1w_pct": change_1w, "oi_usd": oi_usd}
            )
        except Exception as e:
            logger.error(f"Error fetching CME OI: {e}")
            return self._unavailable_signal("CME Open Interest", "institutional")
    
    async def _get_mstr_premium(self) -> SignalResult:
        """
        MicroStrategy NAV premium.
        High premium: Retail chasing BTC exposure
        Discount: Institutional skepticism
        """
        try:
            data = await self._fetch_mstr_data()
            if data is None:
                return self._unavailable_signal("MSTR Premium", "institutional")
            
            premium = data.get("nav_premium_pct", 0)
            
            if premium > 100:
                signal, score = SignalStrength.SELL, -1
                desc = f"MSTR at {premium:.0f}% premium - retail euphoria"
            elif premium < -20:
                signal, score = SignalStrength.BUY, 1
                desc = f"MSTR at {premium:.0f}% discount - skepticism"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"MSTR NAV premium: {premium:.0f}%"
            
            return SignalResult(
                name="MSTR Premium",
                category="institutional",
                value=premium,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"nav_premium_pct": premium}
            )
        except Exception as e:
            logger.error(f"Error fetching MSTR data: {e}")
            return self._unavailable_signal("MSTR Premium", "institutional")
    
    async def _get_institutional_wallets(self, asset: str) -> SignalResult:
        """
        Tracking known institutional wallet movements.
        """
        try:
            data = await self._fetch_institutional_wallets(asset)
            if data is None:
                return self._unavailable_signal("Institutional Wallets", "institutional")
            
            net_change = data.get("net_change_1w", 0)
            
            if net_change > 5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Institutions accumulating ({net_change:+.1f}%/wk)"
            elif net_change > 1:
                signal, score = SignalStrength.BUY, 1
                desc = f"Modest institutional buying ({net_change:+.1f}%/wk)"
            elif net_change < -5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Institutional distribution ({net_change:+.1f}%/wk)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stable institutional holdings ({net_change:+.1f}%/wk)"
            
            return SignalResult(
                name="Institutional Wallets",
                category="institutional",
                value=net_change,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                details={"net_change_1w": net_change}
            )
        except Exception as e:
            logger.error(f"Error fetching institutional wallets: {e}")
            return self._unavailable_signal("Institutional Wallets", "institutional")
    
    # =========================================================================
    # CATEGORY 8: ADDITIONAL SIGNALS
    # =========================================================================
    
    async def _get_stablecoin_mint_burn(self) -> SignalResult:
        """
        Stablecoin minting/burning activity.
        Large mints: Fresh capital entering
        Large burns: Capital exiting
        """
        try:
            data = await self._fetch_stablecoin_mint_burn()
            if data is None:
                return self._unavailable_signal("Stablecoin Mint/Burn", "additional")
            
            net_mint = data.get("net_mint_1w_usd", 0)
            net_mint_millions = net_mint / 1e6
            
            if net_mint > 1e9:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Massive stablecoin minting (${net_mint_millions:,.0f}M/wk)"
            elif net_mint > 500e6:
                signal, score = SignalStrength.BUY, 1
                desc = f"Stablecoin minting (${net_mint_millions:,.0f}M/wk)"
            elif net_mint < -500e6:
                signal, score = SignalStrength.SELL, -1
                desc = f"Stablecoin burning (${net_mint_millions:,.0f}M/wk)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal stablecoin flow (${net_mint_millions:,.0f}M/wk)"
            
            return SignalResult(
                name="Stablecoin Mint/Burn",
                category="additional",
                value=net_mint,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"net_mint_1w_usd": net_mint}
            )
        except Exception as e:
            logger.error(f"Error fetching stablecoin mint/burn: {e}")
            return self._unavailable_signal("Stablecoin Mint/Burn", "additional")
    
    async def _get_tether_treasury(self) -> SignalResult:
        """
        Tether treasury activity (authorized but not issued).
        Treasury accumulating: Preparing for demand
        Treasury depleting: Demand being met
        """
        try:
            data = await self._fetch_tether_treasury()
            if data is None:
                return self._unavailable_signal("Tether Treasury", "additional")
            
            treasury_balance = data.get("treasury_balance", 0)
            change_1w = data.get("change_1w_pct", 0)
            
            if change_1w > 20:
                signal, score = SignalStrength.BUY, 1
                desc = f"Tether treasury growing ({change_1w:+.1f}%) - preparing for demand"
            elif change_1w < -20:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Tether treasury depleting ({change_1w:+.1f}%) - demand being met"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stable treasury ({change_1w:+.1f}%)"
            
            return SignalResult(
                name="Tether Treasury",
                category="additional",
                value=treasury_balance,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={
                    "treasury_balance": treasury_balance,
                    "change_1w_pct": change_1w
                }
            )
        except Exception as e:
            logger.error(f"Error fetching Tether treasury: {e}")
            return self._unavailable_signal("Tether Treasury", "additional")
    
    async def _get_defi_tvl(self) -> SignalResult:
        """
        DeFi Total Value Locked changes.
        Rising TVL: Capital flowing into crypto ecosystem
        Falling TVL: Risk-off
        """
        try:
            data = await self._fetch_defi_tvl()
            if data is None:
                return self._unavailable_signal("DeFi TVL", "additional")
            
            tvl = data.get("tvl", 0)
            change_1w = data.get("change_1w_pct", 0)
            
            if change_1w > 10:
                signal, score = SignalStrength.BUY, 1
                desc = f"DeFi TVL growing ({change_1w:+.1f}%/wk)"
            elif change_1w < -15:
                signal, score = SignalStrength.SELL, -1
                desc = f"DeFi TVL declining ({change_1w:+.1f}%/wk)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stable DeFi TVL ({change_1w:+.1f}%/wk)"
            
            return SignalResult(
                name="DeFi TVL",
                category="additional",
                value=change_1w,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"tvl": tvl, "change_1w_pct": change_1w}
            )
        except Exception as e:
            logger.error(f"Error fetching DeFi TVL: {e}")
            return self._unavailable_signal("DeFi TVL", "additional")
    
    async def _get_nft_sentiment(self) -> SignalResult:
        """
        NFT market sentiment.
        NFT mania: Speculative excess (caution)
        NFT dead: Capitulation (opportunity)
        """
        try:
            data = await self._fetch_nft_data()
            if data is None:
                return self._unavailable_signal("NFT Sentiment", "additional")
            
            volume_change = data.get("volume_change_1m_pct", 0)
            
            if volume_change > 100:
                signal, score = SignalStrength.SELL, -1
                desc = f"NFT mania ({volume_change:+.0f}%/mo) - speculative excess"
            elif volume_change < -50:
                signal, score = SignalStrength.BUY, 1
                desc = f"NFT dead ({volume_change:+.0f}%/mo) - capitulation"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal NFT activity ({volume_change:+.0f}%/mo)"
            
            return SignalResult(
                name="NFT Sentiment",
                category="additional",
                value=volume_change,
                signal=signal,
                score=score,
                weight=0.3,
                description=desc,
                details={"volume_change_1m_pct": volume_change}
            )
        except Exception as e:
            logger.error(f"Error fetching NFT data: {e}")
            return self._unavailable_signal("NFT Sentiment", "additional")
    
    async def _get_mempool_fees(self, asset: str) -> SignalResult:
        """
        Mempool congestion and fees.
        High fees: Network demand/stress
        Low fees: Low activity
        """
        try:
            data = await self._fetch_mempool_data(asset)
            if data is None:
                return self._unavailable_signal("Mempool/Fees", "additional")
            
            fee_rate = data.get("avg_fee_rate", 0)  # sat/vB for BTC
            mempool_size = data.get("mempool_size_mb", 0)
            
            if fee_rate > 100:  # High fees
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"High network fees ({fee_rate:.0f} sat/vB) - congestion"
            elif fee_rate < 5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Low fees ({fee_rate:.0f} sat/vB) - low demand"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal fees ({fee_rate:.0f} sat/vB)"
            
            return SignalResult(
                name="Mempool/Fees",
                category="additional",
                value=fee_rate,
                signal=signal,
                score=score,
                weight=0.3,
                description=desc,
                details={
                    "avg_fee_rate": fee_rate,
                    "mempool_size_mb": mempool_size
                }
            )
        except Exception as e:
            logger.error(f"Error fetching mempool data: {e}")
            return self._unavailable_signal("Mempool/Fees", "additional")
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _unavailable_signal(self, name: str, category: str) -> SignalResult:
        """Return an unavailable signal result."""
        return SignalResult(
            name=name,
            category=category,
            value=None,
            signal=SignalStrength.UNAVAILABLE,
            score=0,
            weight=0,
            description="Data unavailable"
        )
    
    # =========================================================================
    # API FETCH METHODS (Placeholders - implement with real APIs)
    # =========================================================================
    
    async def _fetch_rsi_from_api(self, asset: str) -> Optional[float]:
        """Fetch RSI from API. Implement with your data provider."""
        # TODO: Implement with TradingView, CoinGecko Pro, or calculate from price data
        return None
    
    async def _fetch_ma_data(self, asset: str) -> Optional[Dict]:
        """Fetch moving average data."""
        return None
    
    async def _fetch_bollinger_data(self, asset: str) -> Optional[Dict]:
        """Fetch Bollinger Band data."""
        return None
    
    async def _fetch_macd_data(self, asset: str) -> Optional[Dict]:
        """Fetch MACD data."""
        return None
    
    async def _fetch_volume_data(self, asset: str) -> Optional[Dict]:
        """Fetch volume data."""
        return None
    
    async def _fetch_atr_data(self, asset: str) -> Optional[Dict]:
        """Fetch ATR data."""
        return None
    
    async def _fetch_fibonacci_data(self, asset: str) -> Optional[Dict]:
        """Fetch Fibonacci level data."""
        return None
    
    async def _fetch_ichimoku_data(self, asset: str) -> Optional[Dict]:
        """Fetch Ichimoku cloud data."""
        return None
    
    async def _fetch_google_trends(self) -> Optional[Dict]:
        """Fetch Google Trends data for panic searches."""
        return None
    
    async def _fetch_social_sentiment(self) -> Optional[Dict]:
        """Fetch social media sentiment."""
        return None
    
    async def _fetch_news_sentiment(self) -> Optional[Dict]:
        """Fetch news sentiment aggregation."""
        return None
    
    async def _fetch_youtube_sentiment(self) -> Optional[Dict]:
        """Fetch YouTube influencer sentiment."""
        return None
    
    async def _fetch_long_short_ratio(self) -> Optional[Dict]:
        """Fetch long/short ratio from exchanges."""
        return None
    
    async def _fetch_retail_institutional(self) -> Optional[Dict]:
        """Fetch retail vs institutional positioning."""
        return None
    
    async def _fetch_influencer_sentiment(self) -> Optional[Dict]:
        """Fetch crypto influencer sentiment."""
        return None
    
    async def _fetch_exchange_flows(self, asset: str) -> Optional[Dict]:
        """Fetch exchange flow data."""
        return None
    
    async def _fetch_whale_data(self, asset: str) -> Optional[Dict]:
        """Fetch whale movement data."""
        return None
    
    async def _fetch_active_addresses(self, asset: str) -> Optional[Dict]:
        """Fetch active address data."""
        return None
    
    async def _fetch_mvrv(self, asset: str) -> Optional[Dict]:
        """Fetch MVRV data."""
        return None
    
    async def _fetch_sopr(self, asset: str) -> Optional[Dict]:
        """Fetch SOPR data."""
        return None
    
    async def _fetch_nupl(self, asset: str) -> Optional[Dict]:
        """Fetch NUPL data."""
        return None
    
    async def _fetch_puell_multiple(self, asset: str) -> Optional[Dict]:
        """Fetch Puell Multiple."""
        return None
    
    async def _fetch_reserve_risk(self, asset: str) -> Optional[Dict]:
        """Fetch Reserve Risk."""
        return None
    
    async def _fetch_realized_price(self, asset: str) -> Optional[Dict]:
        """Fetch realized price data."""
        return None
    
    async def _fetch_hodl_waves(self, asset: str) -> Optional[Dict]:
        """Fetch HODL wave data."""
        return None
    
    async def _fetch_cdd(self, asset: str) -> Optional[Dict]:
        """Fetch Coin Days Destroyed."""
        return None
    
    async def _fetch_nvt(self, asset: str) -> Optional[Dict]:
        """Fetch NVT ratio."""
        return None
    
    async def _fetch_funding_rates(self, asset: str) -> Optional[Dict]:
        """Fetch funding rates from perpetual exchanges."""
        return None
    
    async def _fetch_open_interest(self, asset: str) -> Optional[Dict]:
        """Fetch open interest data."""
        return None
    
    async def _fetch_liquidations(self, asset: str) -> Optional[Dict]:
        """Fetch liquidation data."""
        return None
    
    async def _fetch_options_data(self, asset: str) -> Optional[Dict]:
        """Fetch options put/call data."""
        return None
    
    async def _fetch_options_skew(self, asset: str) -> Optional[Dict]:
        """Fetch options skew data."""
        return None
    
    async def _fetch_max_pain(self, asset: str) -> Optional[Dict]:
        """Fetch max pain data."""
        return None
    
    async def _fetch_futures_basis(self, asset: str) -> Optional[Dict]:
        """Fetch futures basis data."""
        return None
    
    async def _fetch_term_structure(self, asset: str) -> Optional[Dict]:
        """Fetch futures term structure."""
        return None
    
    async def _fetch_dxy(self) -> Optional[Dict]:
        """Fetch DXY data."""
        return None
    
    async def _fetch_sp500_data(self) -> Optional[Dict]:
        """Fetch S&P 500 correlation data."""
        return None
    
    async def _fetch_gold_data(self) -> Optional[Dict]:
        """Fetch gold correlation data."""
        return None
    
    async def _fetch_treasury_data(self) -> Optional[Dict]:
        """Fetch Treasury yield data."""
        return None
    
    async def _fetch_vix(self) -> Optional[Dict]:
        """Fetch VIX data."""
        return None
    
    async def _fetch_stablecoin_data(self) -> Optional[Dict]:
        """Fetch stablecoin supply ratio."""
        return None
    
    async def _fetch_coinbase_premium(self, asset: str) -> Optional[Dict]:
        """Fetch Coinbase premium."""
        return None
    
    async def _fetch_korea_premium(self, asset: str) -> Optional[Dict]:
        """Fetch Korea premium."""
        return None
    
    async def _fetch_hash_rate(self, asset: str) -> Optional[Dict]:
        """Fetch hash rate data."""
        return None
    
    async def _fetch_difficulty_ribbon(self, asset: str) -> Optional[Dict]:
        """Fetch difficulty ribbon data."""
        return None
    
    async def _fetch_miner_flows(self, asset: str) -> Optional[Dict]:
        """Fetch miner outflow data."""
        return None
    
    async def _fetch_miner_reserve(self, asset: str) -> Optional[Dict]:
        """Fetch miner reserve data."""
        return None
    
    async def _fetch_thermocap(self, asset: str) -> Optional[Dict]:
        """Fetch thermocap multiple."""
        return None
    
    async def _fetch_s2f(self, asset: str) -> Optional[Dict]:
        """Fetch Stock-to-Flow data."""
        return None
    
    async def _fetch_etf_flows(self, asset: str) -> Optional[Dict]:
        """Fetch ETF flow data."""
        return None
    
    async def _fetch_grayscale_premium(self, asset: str) -> Optional[Dict]:
        """Fetch Grayscale premium."""
        return None
    
    async def _fetch_cme_oi(self, asset: str) -> Optional[Dict]:
        """Fetch CME open interest."""
        return None
    
    async def _fetch_mstr_data(self) -> Optional[Dict]:
        """Fetch MicroStrategy data."""
        return None
    
    async def _fetch_institutional_wallets(self, asset: str) -> Optional[Dict]:
        """Fetch institutional wallet data."""
        return None
    
    async def _fetch_stablecoin_mint_burn(self) -> Optional[Dict]:
        """Fetch stablecoin mint/burn data."""
        return None
    
    async def _fetch_tether_treasury(self) -> Optional[Dict]:
        """Fetch Tether treasury data."""
        return None
    
    async def _fetch_defi_tvl(self) -> Optional[Dict]:
        """Fetch DeFi TVL data."""
        return None
    
    async def _fetch_nft_data(self) -> Optional[Dict]:
        """Fetch NFT market data."""
        return None
    
    async def _fetch_mempool_data(self, asset: str) -> Optional[Dict]:
        """Fetch mempool/fee data."""
        return None
    
    # =========================================================================
    # MAIN ANALYSIS METHOD
    # =========================================================================
    
    async def analyze(self, asset: str = "BTC") -> ComprehensiveSignalAnalysis:
        """
        Run comprehensive 60-signal analysis.
        
        Args:
            asset: Asset to analyze (default: BTC)
            
        Returns:
            ComprehensiveSignalAnalysis with all signal results and recommendations
        """
        # Gather all signals concurrently
        technical_tasks = [
            self._get_rsi(asset),
            self._get_moving_averages(asset),
            self._get_bollinger_bands(asset),
            self._get_macd(asset),
            self._get_volume_capitulation(asset),
            self._get_atr_volatility(asset),
            self._get_fibonacci(asset),
            self._get_ichimoku(asset),
        ]
        
        sentiment_tasks = [
            self._get_fear_greed(),
            self._get_google_trends(),
            self._get_social_sentiment(),
            self._get_news_sentiment(),
            self._get_youtube_sentiment(),
            self._get_long_short_ratio(),
            self._get_retail_institutional(),
            self._get_influencer_sentiment(),
        ]
        
        onchain_tasks = [
            self._get_exchange_flows(asset),
            self._get_whale_movements(asset),
            self._get_active_addresses(asset),
            self._get_mvrv_zscore(asset),
            self._get_sopr(asset),
            self._get_nupl(asset),
            self._get_puell_multiple(asset),
            self._get_reserve_risk(asset),
            self._get_realized_price_bands(asset),
            self._get_hodl_waves(asset),
            self._get_coin_days_destroyed(asset),
            self._get_nvt_ratio(asset),
        ]
        
        derivatives_tasks = [
            self._get_funding_rates(asset),
            self._get_open_interest(asset),
            self._get_liquidations(asset),
            self._get_options_put_call(asset),
            self._get_options_skew(asset),
            self._get_max_pain(asset),
            self._get_futures_basis(asset),
            self._get_term_structure(asset),
        ]
        
        macro_tasks = [
            self._get_dxy(),
            self._get_sp500_correlation(asset),
            self._get_gold_correlation(),
            self._get_treasury_yields(),
            self._get_vix(),
            self._get_stablecoin_supply_ratio(),
            self._get_coinbase_premium(asset),
            self._get_korea_premium(asset),
        ]
        
        mining_tasks = [
            self._get_hash_rate(asset),
            self._get_difficulty_ribbon(asset),
            self._get_miner_outflows(asset),
            self._get_miner_reserve(asset),
            self._get_thermocap(asset),
            self._get_stock_to_flow(asset),
        ]
        
        institutional_tasks = [
            self._get_etf_flows(asset),
            self._get_grayscale_premium(asset),
            self._get_cme_oi(asset),
            self._get_mstr_premium(),
            self._get_institutional_wallets(asset),
        ]
        
        additional_tasks = [
            self._get_stablecoin_mint_burn(),
            self._get_tether_treasury(),
            self._get_defi_tvl(),
            self._get_nft_sentiment(),
            self._get_mempool_fees(asset),
        ]
        
        # Run all tasks concurrently
        all_results = await asyncio.gather(
            *technical_tasks,
            *sentiment_tasks,
            *onchain_tasks,
            *derivatives_tasks,
            *macro_tasks,
            *mining_tasks,
            *institutional_tasks,
            *additional_tasks,
            return_exceptions=True
        )
        
        # Split results back into categories
        idx = 0
        technical_signals = [r if not isinstance(r, Exception) else self._unavailable_signal(f"Tech{i}", "technical") 
                           for i, r in enumerate(all_results[idx:idx+len(technical_tasks)])]
        idx += len(technical_tasks)
        
        sentiment_signals = [r if not isinstance(r, Exception) else self._unavailable_signal(f"Sent{i}", "sentiment")
                           for i, r in enumerate(all_results[idx:idx+len(sentiment_tasks)])]
        idx += len(sentiment_tasks)
        
        onchain_signals = [r if not isinstance(r, Exception) else self._unavailable_signal(f"Chain{i}", "onchain")
                         for i, r in enumerate(all_results[idx:idx+len(onchain_tasks)])]
        idx += len(onchain_tasks)
        
        derivatives_signals = [r if not isinstance(r, Exception) else self._unavailable_signal(f"Deriv{i}", "derivatives")
                              for i, r in enumerate(all_results[idx:idx+len(derivatives_tasks)])]
        idx += len(derivatives_tasks)
        
        macro_signals = [r if not isinstance(r, Exception) else self._unavailable_signal(f"Macro{i}", "macro")
                        for i, r in enumerate(all_results[idx:idx+len(macro_tasks)])]
        idx += len(macro_tasks)
        
        mining_signals = [r if not isinstance(r, Exception) else self._unavailable_signal(f"Mine{i}", "mining")
                         for i, r in enumerate(all_results[idx:idx+len(mining_tasks)])]
        idx += len(mining_tasks)
        
        institutional_signals = [r if not isinstance(r, Exception) else self._unavailable_signal(f"Inst{i}", "institutional")
                                for i, r in enumerate(all_results[idx:idx+len(institutional_tasks)])]
        idx += len(institutional_tasks)
        
        additional_signals = [r if not isinstance(r, Exception) else self._unavailable_signal(f"Add{i}", "additional")
                             for i, r in enumerate(all_results[idx:idx+len(additional_tasks)])]
        
        # Create category summaries
        def summarize_category(name: str, signals: List[SignalResult]) -> CategorySummary:
            available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]
            if not available:
                return CategorySummary(
                    name=name, signals=signals, avg_score=0, weighted_score=0,
                    bullish_count=0, bearish_count=0, neutral_count=0
                )
            
            total_weight = sum(s.weight for s in available)
            weighted_score = sum(s.score * s.weight for s in available) / total_weight if total_weight > 0 else 0
            avg_score = sum(s.score for s in available) / len(available)
            
            return CategorySummary(
                name=name,
                signals=signals,
                avg_score=avg_score,
                weighted_score=weighted_score,
                bullish_count=len([s for s in available if s.score > 0]),
                bearish_count=len([s for s in available if s.score < 0]),
                neutral_count=len([s for s in available if s.score == 0])
            )
        
        technical_summary = summarize_category("Technical", technical_signals)
        sentiment_summary = summarize_category("Sentiment", sentiment_signals)
        onchain_summary = summarize_category("On-Chain", onchain_signals)
        derivatives_summary = summarize_category("Derivatives", derivatives_signals)
        macro_summary = summarize_category("Macro", macro_signals)
        mining_summary = summarize_category("Mining", mining_signals)
        institutional_summary = summarize_category("Institutional", institutional_signals)
        additional_summary = summarize_category("Additional", additional_signals)
        
        # Calculate composite score
        all_signals = (technical_signals + sentiment_signals + onchain_signals + 
                      derivatives_signals + macro_signals + mining_signals + 
                      institutional_signals + additional_signals)
        
        available_signals = [s for s in all_signals if s.signal != SignalStrength.UNAVAILABLE]
        total_signals = len(all_signals)
        available_count = len(available_signals)
        
        if available_signals:
            # Weight by category and individual signal weight
            total_weighted_score = 0
            total_weight = 0
            
            for signal in available_signals:
                category_weight = self.CATEGORY_WEIGHTS.get(signal.category, 1.0)
                combined_weight = signal.weight * category_weight
                total_weighted_score += signal.score * combined_weight
                total_weight += combined_weight
            
            # Normalize to -100 to +100 scale
            composite_score = (total_weighted_score / total_weight) * 50 if total_weight > 0 else 0
        else:
            composite_score = 0
        
        # Calculate confidence based on data availability
        confidence = available_count / total_signals if total_signals > 0 else 0
        
        # Determine DCA multiplier and buffer deployment
        dca_multiplier, buffer_deployment, recommendation = self._get_recommendations(composite_score)
        
        return ComprehensiveSignalAnalysis(
            timestamp=datetime.utcnow(),
            asset=asset,
            technical=technical_summary,
            sentiment=sentiment_summary,
            onchain=onchain_summary,
            derivatives=derivatives_summary,
            macro=macro_summary,
            mining=mining_summary,
            institutional=institutional_summary,
            additional=additional_summary,
            total_signals=total_signals,
            available_signals=available_count,
            composite_score=composite_score,
            dca_multiplier=dca_multiplier,
            buffer_deployment=buffer_deployment,
            confidence=confidence,
            recommendation=recommendation,
            all_signals=all_signals
        )
    
    def _get_recommendations(self, composite_score: float) -> Tuple[float, float, str]:
        """
        Get DCA multiplier, buffer deployment, and recommendation based on composite score.
        
        Args:
            composite_score: Score from -100 to +100
            
        Returns:
            Tuple of (dca_multiplier, buffer_deployment_pct, recommendation_text)
        """
        if composite_score <= -60:
            return 2.5, 0.75, "EXTREME OPPORTUNITY: Maximum DCA + deploy 75% of cash buffer"
        elif composite_score <= -40:
            return 2.0, 0.50, "STRONG BUY: 2x DCA + deploy 50% of cash buffer"
        elif composite_score <= -20:
            return 1.5, 0.25, "BUY: Increase DCA by 50% + deploy 25% of cash buffer"
        elif composite_score <= 0:
            return 1.25, 0.10, "MILD OPPORTUNITY: Slight DCA increase"
        elif composite_score <= 20:
            return 1.0, 0.0, "NEUTRAL: Continue normal DCA"
        elif composite_score <= 40:
            return 0.75, 0.0, "CAUTION: Reduce DCA by 25%"
        elif composite_score <= 60:
            return 0.5, 0.0, "GREED: Reduce DCA by 50%"
        else:
            return 0.25, 0.0, "EXTREME GREED: Minimize DCA, consider taking profits"


def format_extended_signals(analysis: ComprehensiveSignalAnalysis) -> str:
    """
    Format the comprehensive signal analysis for CLI output.
    """
    lines = [
        "",
        "=" * 70,
        f"  COMPREHENSIVE SIGNAL ANALYSIS - {analysis.asset}",
        f"  {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "=" * 70,
        "",
        f"  COMPOSITE SCORE: {analysis.composite_score:+.1f} / 100",
        f"  Signals Available: {analysis.available_signals}/{analysis.total_signals} ({analysis.confidence:.0%} confidence)",
        "",
        "-" * 70,
        f"  RECOMMENDATION: {analysis.recommendation}",
        f"  DCA Multiplier: {analysis.dca_multiplier:.2f}x",
        f"  Buffer Deployment: {analysis.buffer_deployment:.0%}",
        "-" * 70,
        "",
    ]
    
    # Category summaries
    categories = [
        ("TECHNICAL", analysis.technical),
        ("SENTIMENT", analysis.sentiment),
        ("ON-CHAIN", analysis.onchain),
        ("DERIVATIVES", analysis.derivatives),
        ("MACRO", analysis.macro),
        ("MINING", analysis.mining),
        ("INSTITUTIONAL", analysis.institutional),
        ("ADDITIONAL", analysis.additional),
    ]
    
    for name, summary in categories:
        lines.append(f"  {name} ({summary.bullish_count}🟢 {summary.bearish_count}🔴 {summary.neutral_count}⚪)")
        lines.append(f"    Weighted Score: {summary.weighted_score:+.2f}")
        
        for signal in summary.signals:
            if signal.signal == SignalStrength.UNAVAILABLE:
                indicator = "❓"
            elif signal.score >= 2:
                indicator = "🟢🟢"
            elif signal.score == 1:
                indicator = "🟢"
            elif signal.score <= -2:
                indicator = "🔴🔴"
            elif signal.score == -1:
                indicator = "🔴"
            else:
                indicator = "⚪"
            
            lines.append(f"    {indicator} {signal.name}: {signal.description}")
        
        lines.append("")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)
