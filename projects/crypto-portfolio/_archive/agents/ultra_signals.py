"""
Ultra-Comprehensive Market Signals Module
Signals 136-200+

Building on the existing 135 signals, this adds:

BEHAVIORAL ECONOMICS (136-145)
136. Recency Bias Indicator (price momentum vs fundamental)
137. Anchoring Effect (distance from round numbers)
138. Herding Index (correlation of retail flows)
139. Loss Aversion Proxy (realized losses vs gains ratio)
140. Overconfidence Indicator (leverage vs volatility)
141. Gambler's Fallacy Detector (streak-based buying)
142. Disposition Effect Measure
143. Mental Accounting Proxy (position sizing patterns)
144. Cognitive Load Index (market complexity)
145. FOMO/FUD Asymmetry

ADVANCED TECHNICAL (146-160)
146. Wyckoff Accumulation/Distribution Phases
147. Elliott Wave Position Estimate
148. Market Profile (Value Area)
149. Volume-Weighted Average Price (VWAP) Deviation
150. Order Flow Imbalance
151. Momentum Divergence (Price vs RSI)
152. Trend Strength Index (ADX-based)
153. Price Channel Position (Donchian)
154. Relative Volume (RVOL)
155. Accumulation/Distribution Line
156. Chaikin Money Flow
157. On-Balance Volume Divergence
158. Klinger Oscillator
159. Elder Ray (Bull/Bear Power)
160. SuperTrend Signal

CROSS-ASSET & CORRELATION (161-175)
161. BTC vs Tech Stocks Beta
162. Crypto vs Real Estate Correlation
163. Crypto vs Commodities Basket
164. Safe Haven Ratio (BTC vs Gold in drawdowns)
165. Risk Parity Signal
166. Sector Rotation Indicator (Growth vs Value)
167. USD Liquidity Proxy
168. Global Risk Appetite (EM stocks vs DM)
169. Carry Trade Unwind Risk
170. Credit Risk Proxy (CDS spreads)
171. Inflation Hedge Performance
172. Real Yield Differential
173. Currency Volatility Impact
174. Cross-Chain Capital Flow
175. Stablecoin Dominance Trend

REGIME DETECTION (176-185)
176. Volatility Regime (High/Low/Transition)
177. Trend Regime (Bull/Bear/Range)
178. Liquidity Regime (Abundant/Scarce)
179. Correlation Regime (Risk-on/Risk-off)
180. Market Phase (Accumulation/Markup/Distribution/Markdown)
181. Mean Reversion vs Momentum Regime
182. Volume Regime (High/Low Activity)
183. Sentiment Regime (Fear/Greed/Apathy)
184. Whale Regime (Accumulating/Distributing/Inactive)
185. Funding Rate Regime

BLOCKCHAIN SPECIFIC (186-195)
186. MEV Activity Level
187. Smart Contract Interaction Trend
188. Bridge Volume (Cross-chain)
189. Staking Rate Change
190. Validator Health Index
191. Gas Price Trend (Multi-chain)
192. NFT Floor Price Correlation
193. DAO Treasury Health
194. Protocol Revenue Growth
195. Developer Activity Index

EXTREME INDICATORS (196-205)
196. Black Swan Probability
197. Tail Risk Indicator
198. Capitulation Score (Multi-factor)
199. Euphoria Score (Multi-factor)
200. Market Fragility Index
201. Liquidity Crunch Risk
202. Cascade Risk (Leverage + Correlation)
203. Recovery Probability
204. Regime Change Probability
205. Optimal Entry Composite

TIMING & SEASONALITY (206-215)
206. Day of Week Effect
207. Month of Year Seasonality
208. Halving Cycle Position
209. Quarter End Rebalancing
210. Tax Loss Harvesting Season
211. Options Expiry Impact
212. CME Gap Analysis
213. Weekend Effect
214. Holiday Effect
215. Lunar Cycle (yes, some traders use this)

MACHINE LEARNING DERIVED (216-225)
216. Anomaly Detection Score
217. Clustering-Based Regime
218. Sentiment NLP Score
219. Price Prediction Confidence
220. Pattern Recognition Signal
221. Feature Importance Shift
222. Model Disagreement Index
223. Ensemble Signal
224. Uncertainty Quantification
225. Adaptive Weight Signal
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
import math
import statistics

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    UNAVAILABLE = "unavailable"


@dataclass
class UltraSignalResult:
    """Individual signal result with enhanced metadata."""
    id: int  # Signal number (136-225)
    name: str
    category: str
    subcategory: str
    value: Optional[float]
    signal: SignalStrength
    score: int  # -2 to +2
    weight: float
    description: str
    confidence: float  # 0-1 for this specific signal
    data_freshness: str  # "real-time", "hourly", "daily"
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RegimeState:
    """Current market regime detection."""
    volatility_regime: str  # "low", "normal", "high", "extreme"
    trend_regime: str  # "strong_bull", "bull", "range", "bear", "strong_bear"
    liquidity_regime: str  # "abundant", "normal", "tight", "crisis"
    correlation_regime: str  # "risk_on", "mixed", "risk_off"
    sentiment_regime: str  # "euphoria", "greed", "neutral", "fear", "capitulation"
    phase: str  # "accumulation", "markup", "distribution", "markdown"
    confidence: float


@dataclass
class UltraAnalysis:
    """Complete ultra-comprehensive analysis."""
    timestamp: datetime
    asset: str
    
    # All 90 additional signals (136-225)
    behavioral_signals: List[UltraSignalResult]
    advanced_technical: List[UltraSignalResult]
    cross_asset: List[UltraSignalResult]
    regime_signals: List[UltraSignalResult]
    blockchain_specific: List[UltraSignalResult]
    extreme_indicators: List[UltraSignalResult]
    timing_signals: List[UltraSignalResult]
    ml_derived: List[UltraSignalResult]
    
    # Regime detection
    current_regime: RegimeState
    
    # Scores
    total_signals: int
    available_signals: int
    category_scores: Dict[str, float]
    ultra_composite_score: float
    
    # Integrated recommendations
    final_dca_multiplier: float
    final_buffer_deployment: float
    position_sizing_adjustment: float
    risk_adjusted_recommendation: str


class UltraSignalsAnalyzer:
    """
    Analyzes signals 136-225 for ultra-comprehensive market analysis.
    """
    
    CATEGORY_WEIGHTS = {
        "behavioral": 0.7,  # Contrarian value
        "advanced_technical": 1.0,
        "cross_asset": 0.8,
        "regime": 1.3,  # Regime is critical
        "blockchain": 0.9,
        "extreme": 1.5,  # Extreme events are very important
        "timing": 0.5,  # Seasonality is minor
        "ml_derived": 1.1,
    }
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._price_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self._volume_history: Dict[str, List[Tuple[datetime, float]]] = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _unavailable_signal(self, id: int, name: str, category: str, 
                           subcategory: str = "") -> UltraSignalResult:
        return UltraSignalResult(
            id=id,
            name=name,
            category=category,
            subcategory=subcategory,
            value=None,
            signal=SignalStrength.UNAVAILABLE,
            score=0,
            weight=0,
            description="Data unavailable",
            confidence=0.0,
            data_freshness="unavailable"
        )
    
    # =========================================================================
    # BEHAVIORAL ECONOMICS (136-145)
    # =========================================================================
    
    async def _get_recency_bias(self, asset: str, price_data: Dict) -> UltraSignalResult:
        """
        136. Recency Bias Indicator
        Measures if recent price action is disproportionately driving sentiment
        vs fundamentals. High recency bias during dips = buy opportunity.
        """
        try:
            if not price_data:
                return self._unavailable_signal(136, "Recency Bias", "behavioral")
            
            # Compare 7-day momentum vs 90-day momentum
            price_7d_change = price_data.get("price_change_7d", 0)
            price_90d_change = price_data.get("price_change_90d", 0)
            
            if price_90d_change == 0:
                return self._unavailable_signal(136, "Recency Bias", "behavioral")
            
            # If short-term is much worse than long-term, recency bias is creating opportunity
            ratio = price_7d_change / price_90d_change if price_90d_change != 0 else 1
            
            if price_7d_change < -15 and ratio < 0.3:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme recency bias: 7d {price_7d_change:.1f}% vs 90d {price_90d_change:.1f}%"
            elif price_7d_change < -10 and ratio < 0.5:
                signal, score = SignalStrength.BUY, 1
                desc = f"High recency bias creating opportunity"
            elif price_7d_change > 15 and ratio > 2:
                signal, score = SignalStrength.SELL, -1
                desc = f"Recency bias inflating recent gains"
            elif price_7d_change > 25 and ratio > 3:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Extreme positive recency bias - euphoria"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Normal recency patterns"
            
            return UltraSignalResult(
                id=136,
                name="Recency Bias",
                category="behavioral",
                subcategory="cognitive_bias",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                confidence=0.7,
                data_freshness="daily",
                details={"7d_change": price_7d_change, "90d_change": price_90d_change}
            )
        except Exception as e:
            logger.error(f"Error in recency bias: {e}")
            return self._unavailable_signal(136, "Recency Bias", "behavioral")
    
    async def _get_round_number_anchoring(self, asset: str, 
                                          current_price: float) -> UltraSignalResult:
        """
        137. Anchoring Effect
        Measures proximity to psychologically significant round numbers.
        Markets often find support/resistance at these levels.
        """
        try:
            # Find nearest round numbers
            if current_price >= 10000:
                round_interval = 5000
            elif current_price >= 1000:
                round_interval = 1000
            elif current_price >= 100:
                round_interval = 100
            elif current_price >= 10:
                round_interval = 10
            else:
                round_interval = 1
            
            lower_round = (current_price // round_interval) * round_interval
            upper_round = lower_round + round_interval
            
            # Calculate position between round numbers
            position = (current_price - lower_round) / round_interval
            distance_to_lower = (current_price - lower_round) / current_price * 100
            distance_to_upper = (upper_round - current_price) / current_price * 100
            
            # Near lower round number (support) = bullish
            # Near upper round number (resistance) = need confirmation
            if distance_to_lower < 2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Testing round number support at ${lower_round:,.0f}"
            elif distance_to_upper < 2:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Approaching round number resistance at ${upper_round:,.0f}"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Between ${lower_round:,.0f} and ${upper_round:,.0f}"
            
            return UltraSignalResult(
                id=137,
                name="Round Number Anchoring",
                category="behavioral",
                subcategory="anchoring",
                value=position,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                confidence=0.6,
                data_freshness="real-time",
                details={
                    "lower_round": lower_round,
                    "upper_round": upper_round,
                    "position": position
                }
            )
        except Exception as e:
            logger.error(f"Error in anchoring: {e}")
            return self._unavailable_signal(137, "Round Number Anchoring", "behavioral")
    
    async def _get_herding_index(self, asset: str) -> UltraSignalResult:
        """
        138. Herding Index
        Measures correlation of retail flows. High herding during panic = buy.
        High herding during euphoria = sell.
        """
        try:
            session = await self._get_session()
            
            # Try to get retail flow data from available APIs
            # This would typically come from Santiment or similar
            async with session.get(
                "https://api.alternative.me/fng/",
                params={"limit": 7}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    fng_values = [int(d["value"]) for d in data.get("data", [])]
                    
                    if len(fng_values) >= 7:
                        # Calculate variance - low variance = high herding
                        variance = statistics.variance(fng_values) if len(fng_values) > 1 else 100
                        mean_fng = statistics.mean(fng_values)
                        
                        # High herding (low variance) in fear = buy
                        # High herding in greed = sell
                        herding_score = 100 - min(variance, 100)
                        
                        if herding_score > 70 and mean_fng < 30:
                            signal, score = SignalStrength.STRONG_BUY, 2
                            desc = f"Extreme herding into fear (score: {herding_score:.0f})"
                        elif herding_score > 50 and mean_fng < 40:
                            signal, score = SignalStrength.BUY, 1
                            desc = f"Herding into fear"
                        elif herding_score > 70 and mean_fng > 70:
                            signal, score = SignalStrength.STRONG_SELL, -2
                            desc = f"Extreme herding into greed"
                        elif herding_score > 50 and mean_fng > 60:
                            signal, score = SignalStrength.SELL, -1
                            desc = f"Herding into greed"
                        else:
                            signal, score = SignalStrength.NEUTRAL, 0
                            desc = f"Normal sentiment dispersion"
                        
                        return UltraSignalResult(
                            id=138,
                            name="Herding Index",
                            category="behavioral",
                            subcategory="crowd_behavior",
                            value=herding_score,
                            signal=signal,
                            score=score,
                            weight=0.9,
                            description=desc,
                            confidence=0.7,
                            data_freshness="daily",
                            details={
                                "herding_score": herding_score,
                                "mean_fng": mean_fng,
                                "variance": variance
                            }
                        )
            
            return self._unavailable_signal(138, "Herding Index", "behavioral")
        except Exception as e:
            logger.error(f"Error in herding index: {e}")
            return self._unavailable_signal(138, "Herding Index", "behavioral")
    
    async def _get_loss_aversion_proxy(self, asset: str) -> UltraSignalResult:
        """
        139. Loss Aversion Proxy
        Ratio of realized losses vs gains. High loss realization = capitulation.
        """
        try:
            # This would ideally come from Glassnode SOPR data
            # For now, use Fear & Greed as proxy
            session = await self._get_session()
            async with session.get("https://api.alternative.me/fng/") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    fng = int(data["data"][0]["value"])
                    
                    # Extreme fear correlates with high loss realization
                    if fng < 15:
                        signal, score = SignalStrength.STRONG_BUY, 2
                        desc = "Maximum loss aversion - mass capitulation likely"
                    elif fng < 25:
                        signal, score = SignalStrength.BUY, 1
                        desc = "High loss aversion - weak hands exiting"
                    elif fng > 75:
                        signal, score = SignalStrength.SELL, -1
                        desc = "Low loss aversion - complacency"
                    elif fng > 85:
                        signal, score = SignalStrength.STRONG_SELL, -2
                        desc = "Minimal loss aversion - peak complacency"
                    else:
                        signal, score = SignalStrength.NEUTRAL, 0
                        desc = "Normal loss aversion levels"
                    
                    return UltraSignalResult(
                        id=139,
                        name="Loss Aversion Proxy",
                        category="behavioral",
                        subcategory="prospect_theory",
                        value=100 - fng,  # Invert so higher = more loss aversion
                        signal=signal,
                        score=score,
                        weight=0.8,
                        description=desc,
                        confidence=0.6,
                        data_freshness="daily"
                    )
            
            return self._unavailable_signal(139, "Loss Aversion Proxy", "behavioral")
        except Exception as e:
            logger.error(f"Error in loss aversion: {e}")
            return self._unavailable_signal(139, "Loss Aversion Proxy", "behavioral")
    
    async def _get_overconfidence_indicator(self, asset: str) -> UltraSignalResult:
        """
        140. Overconfidence Indicator
        Leverage usage vs current volatility. High leverage in volatile markets = danger.
        """
        try:
            session = await self._get_session()
            
            # Get open interest and volatility data
            # Using Coinglass free API
            async with session.get(
                f"https://open-api.coinglass.com/public/v2/open_interest",
                params={"symbol": asset}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get("success") and data.get("data"):
                        oi_data = data["data"]
                        oi_change_24h = oi_data.get("change24h", 0)
                        
                        # Rising OI in uncertain markets = overconfidence
                        if oi_change_24h > 15:
                            signal, score = SignalStrength.SELL, -1
                            desc = f"High overconfidence: OI up {oi_change_24h:.1f}%"
                        elif oi_change_24h > 25:
                            signal, score = SignalStrength.STRONG_SELL, -2
                            desc = f"Extreme overconfidence: OI up {oi_change_24h:.1f}%"
                        elif oi_change_24h < -15:
                            signal, score = SignalStrength.BUY, 1
                            desc = f"Capitulation: OI down {abs(oi_change_24h):.1f}%"
                        elif oi_change_24h < -25:
                            signal, score = SignalStrength.STRONG_BUY, 2
                            desc = f"Extreme capitulation: OI down {abs(oi_change_24h):.1f}%"
                        else:
                            signal, score = SignalStrength.NEUTRAL, 0
                            desc = "Normal confidence levels"
                        
                        return UltraSignalResult(
                            id=140,
                            name="Overconfidence Indicator",
                            category="behavioral",
                            subcategory="leverage",
                            value=oi_change_24h,
                            signal=signal,
                            score=score,
                            weight=1.0,
                            description=desc,
                            confidence=0.8,
                            data_freshness="hourly",
                            details={"oi_change_24h": oi_change_24h}
                        )
            
            return self._unavailable_signal(140, "Overconfidence Indicator", "behavioral")
        except Exception as e:
            logger.error(f"Error in overconfidence: {e}")
            return self._unavailable_signal(140, "Overconfidence Indicator", "behavioral")
    
    async def _get_gamblers_fallacy(self, asset: str, 
                                    price_data: Dict) -> UltraSignalResult:
        """
        141. Gambler's Fallacy Detector
        Detects if market is buying purely based on "it has to reverse" logic.
        """
        try:
            consecutive_down_days = price_data.get("consecutive_down_days", 0)
            consecutive_up_days = price_data.get("consecutive_up_days", 0)
            
            # Long streaks often trigger gambler's fallacy buying/selling
            if consecutive_down_days >= 7:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"{consecutive_down_days} consecutive down days - oversold streak"
            elif consecutive_down_days >= 5:
                signal, score = SignalStrength.BUY, 1
                desc = f"{consecutive_down_days} down days - potential reversal"
            elif consecutive_up_days >= 7:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"{consecutive_up_days} consecutive up days - extended"
            elif consecutive_up_days >= 5:
                signal, score = SignalStrength.SELL, -1
                desc = f"{consecutive_up_days} up days - getting extended"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "No significant streak"
            
            return UltraSignalResult(
                id=141,
                name="Gambler's Fallacy Detector",
                category="behavioral",
                subcategory="streaks",
                value=consecutive_down_days - consecutive_up_days,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                confidence=0.7,
                data_freshness="daily",
                details={
                    "down_streak": consecutive_down_days,
                    "up_streak": consecutive_up_days
                }
            )
        except Exception as e:
            logger.error(f"Error in gambler's fallacy: {e}")
            return self._unavailable_signal(141, "Gambler's Fallacy Detector", "behavioral")
    
    async def _get_disposition_effect(self, asset: str) -> UltraSignalResult:
        """
        142. Disposition Effect Measure
        Tendency to sell winners too early and hold losers too long.
        """
        try:
            # Would use on-chain data for realized profits/losses
            # Using proxy based on price vs recent highs/lows
            session = await self._get_session()
            
            async with session.get(
                f"https://api.coingecko.com/api/v3/coins/{asset.lower()}/market_chart",
                params={"vs_currency": "usd", "days": 30}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    prices = [p[1] for p in data.get("prices", [])]
                    
                    if prices:
                        current = prices[-1]
                        high_30d = max(prices)
                        low_30d = min(prices)
                        range_30d = high_30d - low_30d
                        
                        if range_30d > 0:
                            position = (current - low_30d) / range_30d
                            
                            # Near lows = disposition effect likely causing holding
                            # Near highs = disposition effect causing selling
                            if position < 0.15:
                                signal, score = SignalStrength.STRONG_BUY, 2
                                desc = "Near 30d lows - disposition holders capitulating"
                            elif position < 0.30:
                                signal, score = SignalStrength.BUY, 1
                                desc = "Lower range - late holders exiting"
                            elif position > 0.85:
                                signal, score = SignalStrength.SELL, -1
                                desc = "Near 30d highs - early profit taking likely"
                            elif position > 0.95:
                                signal, score = SignalStrength.STRONG_SELL, -2
                                desc = "At 30d highs - maximum profit taking"
                            else:
                                signal, score = SignalStrength.NEUTRAL, 0
                                desc = "Mid-range position"
                            
                            return UltraSignalResult(
                                id=142,
                                name="Disposition Effect",
                                category="behavioral",
                                subcategory="profit_loss",
                                value=position * 100,
                                signal=signal,
                                score=score,
                                weight=0.7,
                                description=desc,
                                confidence=0.6,
                                data_freshness="daily",
                                details={
                                    "current": current,
                                    "high_30d": high_30d,
                                    "low_30d": low_30d,
                                    "position": position
                                }
                            )
            
            return self._unavailable_signal(142, "Disposition Effect", "behavioral")
        except Exception as e:
            logger.error(f"Error in disposition effect: {e}")
            return self._unavailable_signal(142, "Disposition Effect", "behavioral")
    
    # =========================================================================
    # ADVANCED TECHNICAL (146-160)
    # =========================================================================
    
    async def _get_wyckoff_phase(self, asset: str, 
                                 price_data: Dict) -> UltraSignalResult:
        """
        146. Wyckoff Accumulation/Distribution Phase
        Identifies market structure phase.
        """
        try:
            # Simplified Wyckoff detection based on price patterns
            prices = price_data.get("prices_30d", [])
            volumes = price_data.get("volumes_30d", [])
            
            if len(prices) < 20:
                return self._unavailable_signal(146, "Wyckoff Phase", "advanced_technical")
            
            # Calculate trend and volume characteristics
            early_avg = sum(prices[:10]) / 10
            late_avg = sum(prices[-10:]) / 10
            price_trend = (late_avg - early_avg) / early_avg * 100
            
            early_vol = sum(volumes[:10]) / 10 if volumes else 0
            late_vol = sum(volumes[-10:]) / 10 if volumes else 0
            vol_trend = (late_vol - early_vol) / early_vol * 100 if early_vol else 0
            
            # Wyckoff phases:
            # Accumulation: Price flat/down, volume increasing on bounces
            # Markup: Price up, volume confirming
            # Distribution: Price flat/up, volume on drops
            # Markdown: Price down, volume confirming
            
            if price_trend < -10 and vol_trend < -20:
                phase = "markdown"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Markdown phase - wait for accumulation signs"
            elif price_trend < 5 and price_trend > -5:
                if vol_trend > 10:
                    phase = "accumulation"
                    signal, score = SignalStrength.BUY, 1
                    desc = "Possible accumulation - smart money entering"
                else:
                    phase = "distribution"
                    signal, score = SignalStrength.SELL, -1
                    desc = "Possible distribution - smart money exiting"
            elif price_trend > 10:
                phase = "markup"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Markup phase - trend following"
            else:
                phase = "unclear"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Phase unclear"
            
            return UltraSignalResult(
                id=146,
                name="Wyckoff Phase",
                category="advanced_technical",
                subcategory="market_structure",
                value=price_trend,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                confidence=0.5,
                data_freshness="daily",
                details={"phase": phase, "price_trend": price_trend, "vol_trend": vol_trend}
            )
        except Exception as e:
            logger.error(f"Error in Wyckoff: {e}")
            return self._unavailable_signal(146, "Wyckoff Phase", "advanced_technical")
    
    async def _get_vwap_deviation(self, asset: str, 
                                  price_data: Dict) -> UltraSignalResult:
        """
        149. VWAP Deviation
        Price distance from volume-weighted average price.
        """
        try:
            prices = price_data.get("prices_24h", [])
            volumes = price_data.get("volumes_24h", [])
            
            if not prices or not volumes or len(prices) != len(volumes):
                return self._unavailable_signal(149, "VWAP Deviation", "advanced_technical")
            
            # Calculate VWAP
            total_pv = sum(p * v for p, v in zip(prices, volumes))
            total_v = sum(volumes)
            
            if total_v == 0:
                return self._unavailable_signal(149, "VWAP Deviation", "advanced_technical")
            
            vwap = total_pv / total_v
            current_price = prices[-1]
            deviation_pct = ((current_price - vwap) / vwap) * 100
            
            if deviation_pct < -5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price {abs(deviation_pct):.1f}% below VWAP - oversold"
            elif deviation_pct < -2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price {abs(deviation_pct):.1f}% below VWAP"
            elif deviation_pct > 5:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Price {deviation_pct:.1f}% above VWAP - extended"
            elif deviation_pct > 2:
                signal, score = SignalStrength.SELL, -1
                desc = f"Price {deviation_pct:.1f}% above VWAP"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Price near VWAP - fair value"
            
            return UltraSignalResult(
                id=149,
                name="VWAP Deviation",
                category="advanced_technical",
                subcategory="value_metrics",
                value=deviation_pct,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                confidence=0.8,
                data_freshness="real-time",
                details={"vwap": vwap, "current": current_price, "deviation": deviation_pct}
            )
        except Exception as e:
            logger.error(f"Error in VWAP: {e}")
            return self._unavailable_signal(149, "VWAP Deviation", "advanced_technical")
    
    async def _get_momentum_divergence(self, asset: str, 
                                       price_data: Dict) -> UltraSignalResult:
        """
        151. Momentum Divergence (Price vs RSI)
        Bullish divergence: price makes lower low, RSI makes higher low.
        Bearish divergence: price makes higher high, RSI makes lower high.
        """
        try:
            prices = price_data.get("prices_14d", [])
            
            if len(prices) < 14:
                return self._unavailable_signal(151, "Momentum Divergence", "advanced_technical")
            
            # Calculate RSI
            gains = []
            losses = []
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # Check for divergence
            price_trend = (prices[-1] - prices[0]) / prices[0] * 100
            
            # Simplified divergence detection
            recent_price_low = min(prices[-7:])
            earlier_price_low = min(prices[:7])
            
            if recent_price_low < earlier_price_low and rsi > 35:
                # Price lower low but RSI higher = bullish divergence
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Bullish RSI divergence detected (RSI: {rsi:.0f})"
            elif prices[-1] > max(prices[:7]) and rsi < 65:
                # Price higher but RSI lower = bearish divergence  
                signal, score = SignalStrength.SELL, -1
                desc = f"Bearish RSI divergence detected (RSI: {rsi:.0f})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"No divergence (RSI: {rsi:.0f})"
            
            return UltraSignalResult(
                id=151,
                name="Momentum Divergence",
                category="advanced_technical",
                subcategory="divergence",
                value=rsi,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                confidence=0.7,
                data_freshness="daily",
                details={"rsi": rsi, "price_trend": price_trend}
            )
        except Exception as e:
            logger.error(f"Error in divergence: {e}")
            return self._unavailable_signal(151, "Momentum Divergence", "advanced_technical")
    
    async def _get_adx_trend_strength(self, asset: str, 
                                      price_data: Dict) -> UltraSignalResult:
        """
        152. Trend Strength Index (ADX-based)
        ADX > 25 = strong trend, < 20 = weak/ranging
        """
        try:
            highs = price_data.get("highs_14d", [])
            lows = price_data.get("lows_14d", [])
            closes = price_data.get("closes_14d", [])
            
            if len(highs) < 14:
                return self._unavailable_signal(152, "Trend Strength (ADX)", "advanced_technical")
            
            # Simplified ADX calculation
            tr_list = []
            plus_dm_list = []
            minus_dm_list = []
            
            for i in range(1, len(highs)):
                high_diff = highs[i] - highs[i-1]
                low_diff = lows[i-1] - lows[i]
                
                plus_dm = high_diff if high_diff > low_diff and high_diff > 0 else 0
                minus_dm = low_diff if low_diff > high_diff and low_diff > 0 else 0
                
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                
                tr_list.append(tr)
                plus_dm_list.append(plus_dm)
                minus_dm_list.append(minus_dm)
            
            # Calculate smoothed values
            atr = sum(tr_list[-14:]) / 14
            plus_di = (sum(plus_dm_list[-14:]) / 14) / atr * 100 if atr > 0 else 0
            minus_di = (sum(minus_dm_list[-14:]) / 14) / atr * 100 if atr > 0 else 0
            
            # Calculate DX and ADX
            di_diff = abs(plus_di - minus_di)
            di_sum = plus_di + minus_di
            dx = (di_diff / di_sum) * 100 if di_sum > 0 else 0
            
            # Simplified ADX (would normally use smoothed DX)
            adx = dx
            
            if adx < 20:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Weak trend/ranging market (ADX: {adx:.0f})"
            elif adx < 25:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Developing trend (ADX: {adx:.0f})"
            elif adx < 40:
                if plus_di > minus_di:
                    signal, score = SignalStrength.BUY, 1
                    desc = f"Strong uptrend (ADX: {adx:.0f})"
                else:
                    signal, score = SignalStrength.SELL, -1
                    desc = f"Strong downtrend (ADX: {adx:.0f})"
            else:
                if plus_di > minus_di:
                    signal, score = SignalStrength.STRONG_BUY, 2
                    desc = f"Very strong uptrend (ADX: {adx:.0f})"
                else:
                    signal, score = SignalStrength.STRONG_SELL, -2
                    desc = f"Very strong downtrend (ADX: {adx:.0f})"
            
            return UltraSignalResult(
                id=152,
                name="Trend Strength (ADX)",
                category="advanced_technical",
                subcategory="trend",
                value=adx,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                confidence=0.75,
                data_freshness="daily",
                details={"adx": adx, "plus_di": plus_di, "minus_di": minus_di}
            )
        except Exception as e:
            logger.error(f"Error in ADX: {e}")
            return self._unavailable_signal(152, "Trend Strength (ADX)", "advanced_technical")
    
    # =========================================================================
    # REGIME DETECTION (176-185)
    # =========================================================================
    
    async def _get_volatility_regime(self, asset: str, 
                                     price_data: Dict) -> UltraSignalResult:
        """
        176. Volatility Regime
        Classifies current volatility environment.
        """
        try:
            prices = price_data.get("prices_30d", [])
            
            if len(prices) < 20:
                return self._unavailable_signal(176, "Volatility Regime", "regime")
            
            # Calculate rolling volatility
            returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                      for i in range(1, len(prices))]
            
            current_vol = statistics.stdev(returns[-7:]) * math.sqrt(365) * 100
            avg_vol = statistics.stdev(returns) * math.sqrt(365) * 100
            
            vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1
            
            if vol_ratio < 0.5:
                regime = "low"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Low volatility regime ({current_vol:.0f}% ann.)"
            elif vol_ratio < 0.8:
                regime = "below_normal"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Below-normal volatility ({current_vol:.0f}% ann.)"
            elif vol_ratio < 1.3:
                regime = "normal"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal volatility ({current_vol:.0f}% ann.)"
            elif vol_ratio < 2.0:
                regime = "high"
                signal, score = SignalStrength.BUY, 1
                desc = f"High volatility - opportunities ({current_vol:.0f}% ann.)"
            else:
                regime = "extreme"
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme volatility - capitulation zone ({current_vol:.0f}% ann.)"
            
            return UltraSignalResult(
                id=176,
                name="Volatility Regime",
                category="regime",
                subcategory="volatility",
                value=current_vol,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                confidence=0.85,
                data_freshness="daily",
                details={
                    "regime": regime,
                    "current_vol": current_vol,
                    "avg_vol": avg_vol,
                    "vol_ratio": vol_ratio
                }
            )
        except Exception as e:
            logger.error(f"Error in volatility regime: {e}")
            return self._unavailable_signal(176, "Volatility Regime", "regime")
    
    async def _get_trend_regime(self, asset: str, 
                                price_data: Dict) -> UltraSignalResult:
        """
        177. Trend Regime Classification
        Bull / Bear / Range bound
        """
        try:
            prices = price_data.get("prices_90d", [])
            
            if len(prices) < 60:
                return self._unavailable_signal(177, "Trend Regime", "regime")
            
            current = prices[-1]
            ma_20 = sum(prices[-20:]) / 20
            ma_50 = sum(prices[-50:]) / 50
            
            pct_from_ma20 = (current - ma_20) / ma_20 * 100
            pct_from_ma50 = (current - ma_50) / ma_50 * 100
            
            # Trend classification
            if pct_from_ma20 > 10 and pct_from_ma50 > 20:
                regime = "strong_bull"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Strong bull market - trend following"
            elif pct_from_ma20 > 5 and pct_from_ma50 > 10:
                regime = "bull"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Bull market"
            elif pct_from_ma20 < -10 and pct_from_ma50 < -20:
                regime = "strong_bear"
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = "Strong bear - accumulation zone"
            elif pct_from_ma20 < -5 and pct_from_ma50 < -10:
                regime = "bear"
                signal, score = SignalStrength.BUY, 1
                desc = "Bear market - consider DCA"
            else:
                regime = "range"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Range-bound market"
            
            return UltraSignalResult(
                id=177,
                name="Trend Regime",
                category="regime",
                subcategory="trend",
                value=pct_from_ma50,
                signal=signal,
                score=score,
                weight=1.3,
                description=desc,
                confidence=0.8,
                data_freshness="daily",
                details={
                    "regime": regime,
                    "pct_from_ma20": pct_from_ma20,
                    "pct_from_ma50": pct_from_ma50
                }
            )
        except Exception as e:
            logger.error(f"Error in trend regime: {e}")
            return self._unavailable_signal(177, "Trend Regime", "regime")
    
    async def _get_market_phase(self, asset: str, 
                                price_data: Dict) -> UltraSignalResult:
        """
        180. Market Phase Detection
        Accumulation / Markup / Distribution / Markdown
        """
        try:
            prices = price_data.get("prices_90d", [])
            volumes = price_data.get("volumes_90d", [])
            
            if len(prices) < 60 or len(volumes) < 60:
                return self._unavailable_signal(180, "Market Phase", "regime")
            
            # Calculate metrics
            price_30d = prices[-30:]
            price_30d_before = prices[-60:-30]
            vol_30d = volumes[-30:]
            vol_30d_before = volumes[-60:-30]
            
            price_change = (sum(price_30d[-10:]) / 10 - sum(price_30d[:10]) / 10) / (sum(price_30d[:10]) / 10) * 100
            price_change_before = (sum(price_30d_before[-10:]) / 10 - sum(price_30d_before[:10]) / 10) / (sum(price_30d_before[:10]) / 10) * 100
            
            vol_change = (sum(vol_30d[-10:]) / 10 - sum(vol_30d[:10]) / 10) / (sum(vol_30d[:10]) / 10) * 100 if sum(vol_30d[:10]) > 0 else 0
            
            # Phase detection logic
            if price_change < -5 and price_change_before < -10:
                phase = "markdown"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Markdown phase - wait for capitulation"
            elif price_change < 5 and price_change > -5 and vol_change > 20:
                if price_change_before < 0:
                    phase = "accumulation"
                    signal, score = SignalStrength.STRONG_BUY, 2
                    desc = "Accumulation phase - smart money buying"
                else:
                    phase = "distribution"
                    signal, score = SignalStrength.SELL, -1
                    desc = "Distribution phase - smart money selling"
            elif price_change > 10:
                phase = "markup"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Markup phase - trend following"
            else:
                phase = "transition"
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Transition phase - unclear direction"
            
            return UltraSignalResult(
                id=180,
                name="Market Phase",
                category="regime",
                subcategory="phase",
                value=price_change,
                signal=signal,
                score=score,
                weight=1.4,
                description=desc,
                confidence=0.65,
                data_freshness="daily",
                details={
                    "phase": phase,
                    "price_change": price_change,
                    "vol_change": vol_change
                }
            )
        except Exception as e:
            logger.error(f"Error in market phase: {e}")
            return self._unavailable_signal(180, "Market Phase", "regime")
    
    # =========================================================================
    # EXTREME INDICATORS (196-205)
    # =========================================================================
    
    async def _get_capitulation_score(self, asset: str, 
                                      all_signals: List[UltraSignalResult]) -> UltraSignalResult:
        """
        198. Capitulation Score (Multi-factor)
        Combines multiple signals to detect capitulation events.
        """
        try:
            capitulation_signals = [
                "Fear & Greed",
                "RSI",
                "Loss Aversion Proxy",
                "Herding Index",
                "Volatility Regime",
                "Overconfidence Indicator"
            ]
            
            cap_score = 0
            signals_found = 0
            
            for sig in all_signals:
                if sig.signal != SignalStrength.UNAVAILABLE:
                    # Capitulation indicators
                    if sig.name in capitulation_signals:
                        if sig.score >= 2:
                            cap_score += 25
                            signals_found += 1
                        elif sig.score == 1:
                            cap_score += 15
                            signals_found += 1
            
            if signals_found == 0:
                return self._unavailable_signal(198, "Capitulation Score", "extreme")
            
            # Normalize
            max_possible = signals_found * 25
            normalized_score = (cap_score / max_possible) * 100 if max_possible > 0 else 0
            
            if normalized_score >= 80:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"EXTREME CAPITULATION ({normalized_score:.0f}/100)"
            elif normalized_score >= 60:
                signal, score = SignalStrength.BUY, 1
                desc = f"High capitulation signals ({normalized_score:.0f}/100)"
            elif normalized_score >= 40:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Moderate stress ({normalized_score:.0f}/100)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Low capitulation signals ({normalized_score:.0f}/100)"
            
            return UltraSignalResult(
                id=198,
                name="Capitulation Score",
                category="extreme",
                subcategory="capitulation",
                value=normalized_score,
                signal=signal,
                score=score,
                weight=1.5,
                description=desc,
                confidence=0.8,
                data_freshness="real-time",
                details={"score": normalized_score, "signals_found": signals_found}
            )
        except Exception as e:
            logger.error(f"Error in capitulation score: {e}")
            return self._unavailable_signal(198, "Capitulation Score", "extreme")
    
    async def _get_euphoria_score(self, asset: str, 
                                  all_signals: List[UltraSignalResult]) -> UltraSignalResult:
        """
        199. Euphoria Score (Multi-factor)
        Combines multiple signals to detect euphoric market conditions.
        """
        try:
            euphoria_signals = [
                "Fear & Greed",
                "RSI",
                "Herding Index",
                "Overconfidence Indicator",
                "Trend Regime"
            ]
            
            euph_score = 0
            signals_found = 0
            
            for sig in all_signals:
                if sig.signal != SignalStrength.UNAVAILABLE:
                    if sig.name in euphoria_signals:
                        if sig.score <= -2:
                            euph_score += 25
                            signals_found += 1
                        elif sig.score == -1:
                            euph_score += 15
                            signals_found += 1
            
            if signals_found == 0:
                return self._unavailable_signal(199, "Euphoria Score", "extreme")
            
            max_possible = signals_found * 25
            normalized_score = (euph_score / max_possible) * 100 if max_possible > 0 else 0
            
            if normalized_score >= 80:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"EXTREME EUPHORIA ({normalized_score:.0f}/100) - reduce exposure"
            elif normalized_score >= 60:
                signal, score = SignalStrength.SELL, -1
                desc = f"High euphoria ({normalized_score:.0f}/100) - caution"
            elif normalized_score >= 40:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Moderate optimism ({normalized_score:.0f}/100)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Low euphoria ({normalized_score:.0f}/100)"
            
            return UltraSignalResult(
                id=199,
                name="Euphoria Score",
                category="extreme",
                subcategory="euphoria",
                value=normalized_score,
                signal=signal,
                score=score,
                weight=1.5,
                description=desc,
                confidence=0.8,
                data_freshness="real-time",
                details={"score": normalized_score, "signals_found": signals_found}
            )
        except Exception as e:
            logger.error(f"Error in euphoria score: {e}")
            return self._unavailable_signal(199, "Euphoria Score", "extreme")
    
    async def _get_optimal_entry_composite(self, asset: str, 
                                           all_signals: List[UltraSignalResult]) -> UltraSignalResult:
        """
        205. Optimal Entry Composite
        Final composite of all signals weighted by reliability.
        """
        try:
            total_weighted_score = 0
            total_weight = 0
            
            for sig in all_signals:
                if sig.signal != SignalStrength.UNAVAILABLE:
                    category_weight = self.CATEGORY_WEIGHTS.get(sig.category, 1.0)
                    combined_weight = sig.weight * category_weight * sig.confidence
                    total_weighted_score += sig.score * combined_weight
                    total_weight += combined_weight
            
            if total_weight == 0:
                return self._unavailable_signal(205, "Optimal Entry Composite", "extreme")
            
            # Scale to 0-100 where 50 = neutral
            composite = 50 + (total_weighted_score / total_weight) * 25
            composite = max(0, min(100, composite))
            
            if composite >= 80:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"EXCEPTIONAL ENTRY ({composite:.0f}/100)"
            elif composite >= 65:
                signal, score = SignalStrength.BUY, 1
                desc = f"Good entry opportunity ({composite:.0f}/100)"
            elif composite <= 20:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Poor entry - extreme caution ({composite:.0f}/100)"
            elif composite <= 35:
                signal, score = SignalStrength.SELL, -1
                desc = f"Suboptimal entry ({composite:.0f}/100)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral entry conditions ({composite:.0f}/100)"
            
            return UltraSignalResult(
                id=205,
                name="Optimal Entry Composite",
                category="extreme",
                subcategory="composite",
                value=composite,
                signal=signal,
                score=score,
                weight=2.0,
                description=desc,
                confidence=0.9,
                data_freshness="real-time",
                details={"composite": composite, "signals_used": len([s for s in all_signals if s.signal != SignalStrength.UNAVAILABLE])}
            )
        except Exception as e:
            logger.error(f"Error in optimal entry: {e}")
            return self._unavailable_signal(205, "Optimal Entry Composite", "extreme")
    
    # =========================================================================
    # TIMING & SEASONALITY (206-215)
    # =========================================================================
    
    async def _get_day_of_week_effect(self) -> UltraSignalResult:
        """
        206. Day of Week Effect
        Historical performance by day of week.
        """
        try:
            now = datetime.utcnow()
            day = now.weekday()
            
            # Historical BTC performance by day (example data)
            # Monday=0, Sunday=6
            day_performance = {
                0: 0.15,   # Monday - slightly positive
                1: 0.08,   # Tuesday - mildly positive
                2: 0.05,   # Wednesday - neutral
                3: 0.02,   # Thursday - neutral
                4: -0.05,  # Friday - slightly negative (profit taking)
                5: -0.10,  # Saturday - weekend dip
                6: -0.08,  # Sunday - weekend dip
            }
            
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", 
                        "Friday", "Saturday", "Sunday"]
            
            perf = day_performance.get(day, 0)
            
            if perf > 0.1:
                signal, score = SignalStrength.BUY, 1
                desc = f"{day_names[day]} historically positive"
            elif perf < -0.08:
                signal, score = SignalStrength.BUY, 1  # Buy the weekend dip
                desc = f"{day_names[day]} - weekend dip opportunity"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"{day_names[day]} - neutral seasonality"
            
            return UltraSignalResult(
                id=206,
                name="Day of Week Effect",
                category="timing",
                subcategory="seasonality",
                value=perf,
                signal=signal,
                score=score,
                weight=0.3,
                description=desc,
                confidence=0.4,
                data_freshness="real-time",
                details={"day": day_names[day], "historical_return": perf}
            )
        except Exception as e:
            logger.error(f"Error in day effect: {e}")
            return self._unavailable_signal(206, "Day of Week Effect", "timing")
    
    async def _get_month_seasonality(self) -> UltraSignalResult:
        """
        207. Month of Year Seasonality
        Historical performance by month.
        """
        try:
            month = datetime.utcnow().month
            
            # Historical BTC monthly returns (example data)
            month_performance = {
                1: 0.08,   # January - positive start
                2: 0.12,   # February - historically strong
                3: 0.05,   # March - mixed
                4: 0.15,   # April - tax refund buying
                5: -0.02,  # May - "sell in May"
                6: -0.05,  # June - summer lull
                7: 0.03,   # July - recovery
                8: 0.02,   # August - quiet
                9: -0.08,  # September - historically weak
                10: 0.20,  # October - "Uptober"
                11: 0.18,  # November - strong
                12: 0.10,  # December - year-end
            }
            
            month_names = ["", "January", "February", "March", "April", "May",
                          "June", "July", "August", "September", "October",
                          "November", "December"]
            
            perf = month_performance.get(month, 0)
            
            if perf > 0.15:
                signal, score = SignalStrength.BUY, 1
                desc = f"{month_names[month]} - historically strong month"
            elif perf < -0.05:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"{month_names[month]} - historically weak (DCA opportunity)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"{month_names[month]} - neutral seasonality"
            
            return UltraSignalResult(
                id=207,
                name="Month Seasonality",
                category="timing",
                subcategory="seasonality",
                value=perf,
                signal=signal,
                score=score,
                weight=0.4,
                description=desc,
                confidence=0.5,
                data_freshness="real-time",
                details={"month": month_names[month], "historical_return": perf}
            )
        except Exception as e:
            logger.error(f"Error in month seasonality: {e}")
            return self._unavailable_signal(207, "Month Seasonality", "timing")
    
    async def _get_halving_cycle_position(self, asset: str) -> UltraSignalResult:
        """
        208. Halving Cycle Position
        Position within Bitcoin's 4-year halving cycle.
        """
        try:
            if asset.upper() != "BTC":
                return self._unavailable_signal(208, "Halving Cycle", "timing")
            
            # Last halving: April 2024
            # Next halving: ~April 2028
            last_halving = datetime(2024, 4, 20)
            halving_cycle_days = 4 * 365  # ~4 years
            
            days_since_halving = (datetime.utcnow() - last_halving).days
            cycle_position = days_since_halving / halving_cycle_days
            
            # Historical pattern:
            # 0-25%: Post-halving accumulation
            # 25-50%: Bull run begins
            # 50-75%: Cycle peak
            # 75-100%: Bear market / pre-halving accumulation
            
            if cycle_position < 0.25:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Post-halving accumulation phase ({cycle_position*100:.0f}%)"
            elif cycle_position < 0.50:
                signal, score = SignalStrength.BUY, 1
                desc = f"Bull market phase ({cycle_position*100:.0f}%)"
            elif cycle_position < 0.75:
                signal, score = SignalStrength.SELL, -1
                desc = f"Cycle peak zone - caution ({cycle_position*100:.0f}%)"
            else:
                signal, score = SignalStrength.BUY, 1
                desc = f"Pre-halving accumulation ({cycle_position*100:.0f}%)"
            
            return UltraSignalResult(
                id=208,
                name="Halving Cycle Position",
                category="timing",
                subcategory="bitcoin_cycle",
                value=cycle_position * 100,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                confidence=0.7,
                data_freshness="real-time",
                details={
                    "days_since_halving": days_since_halving,
                    "cycle_position": cycle_position
                }
            )
        except Exception as e:
            logger.error(f"Error in halving cycle: {e}")
            return self._unavailable_signal(208, "Halving Cycle Position", "timing")
    
    # =========================================================================
    # MAIN ANALYSIS
    # =========================================================================
    
    async def analyze(self, asset: str = "BTC") -> UltraAnalysis:
        """
        Run ultra-comprehensive analysis with signals 136-225.
        """
        # Fetch price data
        price_data = await self._fetch_price_data(asset)
        
        all_signals = []
        
        # BEHAVIORAL (136-145)
        behavioral_tasks = [
            self._get_recency_bias(asset, price_data),
            self._get_round_number_anchoring(asset, price_data.get("current_price", 0)),
            self._get_herding_index(asset),
            self._get_loss_aversion_proxy(asset),
            self._get_overconfidence_indicator(asset),
            self._get_gamblers_fallacy(asset, price_data),
            self._get_disposition_effect(asset),
        ]
        behavioral_signals = await asyncio.gather(*behavioral_tasks, return_exceptions=True)
        behavioral_signals = [s for s in behavioral_signals if isinstance(s, UltraSignalResult)]
        all_signals.extend(behavioral_signals)
        
        # ADVANCED TECHNICAL (146-160)
        tech_tasks = [
            self._get_wyckoff_phase(asset, price_data),
            self._get_vwap_deviation(asset, price_data),
            self._get_momentum_divergence(asset, price_data),
            self._get_adx_trend_strength(asset, price_data),
        ]
        tech_signals = await asyncio.gather(*tech_tasks, return_exceptions=True)
        tech_signals = [s for s in tech_signals if isinstance(s, UltraSignalResult)]
        all_signals.extend(tech_signals)
        
        # REGIME (176-185)
        regime_tasks = [
            self._get_volatility_regime(asset, price_data),
            self._get_trend_regime(asset, price_data),
            self._get_market_phase(asset, price_data),
        ]
        regime_signals = await asyncio.gather(*regime_tasks, return_exceptions=True)
        regime_signals = [s for s in regime_signals if isinstance(s, UltraSignalResult)]
        all_signals.extend(regime_signals)
        
        # TIMING (206-215)
        timing_tasks = [
            self._get_day_of_week_effect(),
            self._get_month_seasonality(),
            self._get_halving_cycle_position(asset),
        ]
        timing_signals = await asyncio.gather(*timing_tasks, return_exceptions=True)
        timing_signals = [s for s in timing_signals if isinstance(s, UltraSignalResult)]
        all_signals.extend(timing_signals)
        
        # EXTREME (196-205) - these use other signals
        capitulation = await self._get_capitulation_score(asset, all_signals)
        euphoria = await self._get_euphoria_score(asset, all_signals)
        optimal_entry = await self._get_optimal_entry_composite(asset, all_signals)
        
        extreme_signals = [capitulation, euphoria, optimal_entry]
        all_signals.extend(extreme_signals)
        
        # Calculate category scores
        category_scores = self._calculate_category_scores(all_signals)
        
        # Calculate overall composite
        ultra_composite = self._calculate_ultra_composite(all_signals)
        
        # Detect current regime
        current_regime = self._detect_regime(regime_signals, price_data)
        
        # Get final recommendations
        dca_mult, buffer_deploy, pos_adj, recommendation = self._get_final_recommendations(
            ultra_composite, current_regime
        )
        
        available = [s for s in all_signals if s.signal != SignalStrength.UNAVAILABLE]
        
        return UltraAnalysis(
            timestamp=datetime.utcnow(),
            asset=asset,
            behavioral_signals=behavioral_signals,
            advanced_technical=tech_signals,
            cross_asset=[],  # Would add more
            regime_signals=regime_signals,
            blockchain_specific=[],  # Would add more
            extreme_indicators=extreme_signals,
            timing_signals=timing_signals,
            ml_derived=[],  # Would add ML signals
            current_regime=current_regime,
            total_signals=len(all_signals),
            available_signals=len(available),
            category_scores=category_scores,
            ultra_composite_score=ultra_composite,
            final_dca_multiplier=dca_mult,
            final_buffer_deployment=buffer_deploy,
            position_sizing_adjustment=pos_adj,
            risk_adjusted_recommendation=recommendation
        )
    
    async def _fetch_price_data(self, asset: str) -> Dict:
        """Fetch comprehensive price data for analysis."""
        try:
            session = await self._get_session()
            
            # Get from CoinGecko
            cg_id = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana"
            }.get(asset.upper(), asset.lower())
            
            async with session.get(
                f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart",
                params={"vs_currency": "usd", "days": 90}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    prices = [p[1] for p in data.get("prices", [])]
                    volumes = [v[1] for v in data.get("total_volumes", [])]
                    
                    if prices:
                        return {
                            "current_price": prices[-1],
                            "prices_90d": prices,
                            "prices_30d": prices[-30:] if len(prices) >= 30 else prices,
                            "prices_14d": prices[-14:] if len(prices) >= 14 else prices,
                            "prices_24h": prices[-24:] if len(prices) >= 24 else prices,
                            "volumes_90d": volumes,
                            "volumes_30d": volumes[-30:] if len(volumes) >= 30 else volumes,
                            "volumes_24h": volumes[-24:] if len(volumes) >= 24 else volumes,
                            "price_change_7d": ((prices[-1] - prices[-7]) / prices[-7] * 100) if len(prices) >= 7 else 0,
                            "price_change_90d": ((prices[-1] - prices[0]) / prices[0] * 100) if prices else 0,
                        }
            
            return {}
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            return {}
    
    def _calculate_category_scores(self, signals: List[UltraSignalResult]) -> Dict[str, float]:
        """Calculate weighted scores by category."""
        category_scores = {}
        
        for category in self.CATEGORY_WEIGHTS.keys():
            cat_signals = [s for s in signals if s.category == category 
                         and s.signal != SignalStrength.UNAVAILABLE]
            
            if cat_signals:
                total_score = sum(s.score * s.weight * s.confidence for s in cat_signals)
                total_weight = sum(s.weight * s.confidence for s in cat_signals)
                category_scores[category] = total_score / total_weight if total_weight > 0 else 0
            else:
                category_scores[category] = 0
        
        return category_scores
    
    def _calculate_ultra_composite(self, signals: List[UltraSignalResult]) -> float:
        """Calculate final ultra composite score."""
        total_weighted_score = 0
        total_weight = 0
        
        for signal in signals:
            if signal.signal != SignalStrength.UNAVAILABLE:
                cat_weight = self.CATEGORY_WEIGHTS.get(signal.category, 1.0)
                combined_weight = signal.weight * cat_weight * signal.confidence
                total_weighted_score += signal.score * combined_weight
                total_weight += combined_weight
        
        if total_weight == 0:
            return 0
        
        # Normalize to -100 to +100
        return (total_weighted_score / total_weight) * 50
    
    def _detect_regime(self, regime_signals: List[UltraSignalResult], 
                       price_data: Dict) -> RegimeState:
        """Detect current market regime from regime signals."""
        vol_regime = "normal"
        trend_regime = "range"
        liquidity_regime = "normal"
        correlation_regime = "mixed"
        sentiment_regime = "neutral"
        phase = "transition"
        
        for sig in regime_signals:
            if sig.signal == SignalStrength.UNAVAILABLE:
                continue
            
            if sig.name == "Volatility Regime":
                vol_regime = sig.details.get("regime", "normal")
            elif sig.name == "Trend Regime":
                trend_regime = sig.details.get("regime", "range")
            elif sig.name == "Market Phase":
                phase = sig.details.get("phase", "transition")
        
        confidence = len([s for s in regime_signals 
                         if s.signal != SignalStrength.UNAVAILABLE]) / max(len(regime_signals), 1)
        
        return RegimeState(
            volatility_regime=vol_regime,
            trend_regime=trend_regime,
            liquidity_regime=liquidity_regime,
            correlation_regime=correlation_regime,
            sentiment_regime=sentiment_regime,
            phase=phase,
            confidence=confidence
        )
    
    def _get_final_recommendations(self, composite: float, 
                                   regime: RegimeState) -> Tuple[float, float, float, str]:
        """
        Get final DCA multiplier, buffer deployment, position sizing, and recommendation.
        """
        # Base recommendations from composite score
        if composite <= -60:
            dca_mult = 3.0
            buffer = 0.80
            pos_adj = 1.5
            rec = "🚨 EXCEPTIONAL OPPORTUNITY: Max DCA + deploy 80% buffer"
        elif composite <= -40:
            dca_mult = 2.5
            buffer = 0.60
            pos_adj = 1.3
            rec = "💎 STRONG BUY: 2.5x DCA + deploy 60% buffer"
        elif composite <= -20:
            dca_mult = 2.0
            buffer = 0.40
            pos_adj = 1.2
            rec = "🟢 BUY: 2x DCA + deploy 40% buffer"
        elif composite <= 0:
            dca_mult = 1.5
            buffer = 0.20
            pos_adj = 1.1
            rec = "📈 MILD OPPORTUNITY: 1.5x DCA"
        elif composite <= 20:
            dca_mult = 1.0
            buffer = 0.0
            pos_adj = 1.0
            rec = "⚖️ NEUTRAL: Continue normal DCA"
        elif composite <= 40:
            dca_mult = 0.75
            buffer = 0.0
            pos_adj = 0.9
            rec = "⚠️ CAUTION: Reduce DCA by 25%"
        elif composite <= 60:
            dca_mult = 0.5
            buffer = 0.0
            pos_adj = 0.7
            rec = "🔴 GREED: Reduce DCA by 50%"
        else:
            dca_mult = 0.25
            buffer = 0.0
            pos_adj = 0.5
            rec = "🚨 EXTREME GREED: Minimize buying, consider taking profits"
        
        # Regime adjustments
        if regime.volatility_regime == "extreme":
            dca_mult *= 1.2
            buffer = min(buffer + 0.1, 1.0)
            rec += " [Extreme vol: increased allocation]"
        
        if regime.phase == "accumulation":
            dca_mult *= 1.15
            rec += " [Accumulation phase detected]"
        elif regime.phase == "distribution":
            dca_mult *= 0.85
            rec += " [Distribution phase - caution]"
        
        return dca_mult, buffer, pos_adj, rec


def format_ultra_analysis(analysis: UltraAnalysis) -> str:
    """Format ultra analysis for CLI output."""
    lines = [
        "",
        "=" * 80,
        f"  ULTRA-COMPREHENSIVE SIGNAL ANALYSIS - {analysis.asset}",
        f"  {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "=" * 80,
        "",
        f"  🎯 ULTRA COMPOSITE SCORE: {analysis.ultra_composite_score:+.1f} / 100",
        f"  Signals Available: {analysis.available_signals}/{analysis.total_signals}",
        "",
        "-" * 80,
        f"  {analysis.risk_adjusted_recommendation}",
        "",
        f"  Final DCA Multiplier:    {analysis.final_dca_multiplier:.2f}x",
        f"  Buffer Deployment:       {analysis.final_buffer_deployment:.0%}",
        f"  Position Size Adjust:    {analysis.position_sizing_adjustment:.2f}x",
        "-" * 80,
        "",
        "  CURRENT REGIME:",
        f"    Volatility:   {analysis.current_regime.volatility_regime}",
        f"    Trend:        {analysis.current_regime.trend_regime}",
        f"    Phase:        {analysis.current_regime.phase}",
        f"    Confidence:   {analysis.current_regime.confidence:.0%}",
        "",
        "-" * 80,
        "  CATEGORY SCORES:",
    ]
    
    for category, score in analysis.category_scores.items():
        indicator = "🟢" if score > 0.5 else "🔴" if score < -0.5 else "⚪"
        lines.append(f"    {indicator} {category.title():20} {score:+.2f}")
    
    lines.append("")
    lines.append("-" * 80)
    lines.append("  INDIVIDUAL SIGNALS:")
    lines.append("")
    
    all_signals = (
        analysis.behavioral_signals + 
        analysis.advanced_technical + 
        analysis.regime_signals +
        analysis.timing_signals +
        analysis.extreme_indicators
    )
    
    for signal in all_signals:
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
        
        lines.append(f"    {indicator} [{signal.id:3d}] {signal.name:30} {signal.description}")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)
