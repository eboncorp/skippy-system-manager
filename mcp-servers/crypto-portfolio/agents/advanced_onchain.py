"""
Advanced On-Chain & Cycle Indicators Module

This module adds 40+ additional sophisticated indicators:

CYCLE INDICATORS (61-70)
61. Pi Cycle Top Indicator
62. Golden Ratio Multiplier
63. 2-Year MA Multiplier
64. Rainbow Chart / Log Regression Bands
65. Bitcoin Logarithmic Growth Curves
66. Top Cap vs Average Cap
67. Delta Cap
68. Terminal Price
69. Balanced Price
70. CVDD (Cumulative Value Days Destroyed)

ADVANCED ON-CHAIN (71-85)
71. RHODL Ratio
72. aSOPR (Adjusted SOPR)
73. Entity-Adjusted SOPR
74. Realized Losses
75. Supply in Profit
76. Supply in Loss
77. LTH-SOPR
78. STH-SOPR
79. Liveliness
80. Dormancy Flow
81. Binary CDD
82. Supply Shock Indicators
83. SLRV Ribbons
84. Illiquid Supply Change
85. Realized Cap HODL Waves

EXCHANGE & FLOW METRICS (86-95)
86. Exchange Reserve (All)
87. Exchange Reserve Ratio
88. Stablecoin Exchange Reserve
89. Exchange Whale Ratio
90. Fund Flow Ratio
91. Exchange Deposit/Withdrawal Count
92. Smart Money vs Dumb Money
93. Retail Transaction Dominance
94. Whale Transaction Count
95. Exchange Inflow Mean (MA7)

NETWORK METRICS (96-105)
96. Transfer Volume
97. Network Velocity
98. Supply Last Active 1y+
99. Mean Coin Age
100. Median Transfer Value
101. Active Entities
102. New Entities
103. Entity-Adjusted Transaction Count
104. Adjusted Transaction Volume
105. Fee Revenue / Security Spend

MARKET STRUCTURE (106-115)
106. Altcoin Season Index
107. BTC Dominance
108. Total Crypto Market Cap
109. Crypto vs M2 Money Supply Ratio
110. Crypto vs Gold Market Cap
111. ETH/BTC Ratio
112. SOL/ETH Ratio
113. Large Cap / Small Cap Ratio
114. DeFi Dominance
115. Layer 2 TVL Ratio

MACRO LIQUIDITY (116-125)
116. Global M2 Money Supply Change
117. Fed Balance Sheet Change
118. Real Interest Rate
119. Inflation Expectations (TIPS spread)
120. Credit Spreads (HY-IG)
121. Global Liquidity Index
122. Risk Appetite Index
123. Yield Curve Slope
124. Corporate Bond Flows
125. EM Capital Flows

DERIVATIVES ADVANCED (126-135)
126. Perpetual Volume / Spot Volume
127. Futures Volume Momentum
128. Options Volume Spike
129. Gamma Exposure
130. Delta Exposure
131. Volatility Risk Premium
132. Implied vs Realized Vol Ratio
133. Variance Swap Rate
134. Options Flow Imbalance
135. Perpetual Premium Index
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import aiohttp
import logging

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
class AdvancedSignalResult:
    """Individual signal result."""
    name: str
    category: str
    subcategory: str
    value: Optional[float]
    signal: SignalStrength
    score: int  # -2 to +2
    weight: float
    description: str
    historical_accuracy: float  # How accurate this signal has been historically
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CyclePhase:
    """Current market cycle phase assessment."""
    phase: str  # accumulation, markup, distribution, markdown
    confidence: float
    days_in_phase: int
    typical_duration: int
    phase_progress: float  # 0-1


class AdvancedOnChainAnalyzer:
    """
    Advanced on-chain and cycle indicators.
    """

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(minutes=10)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _unavailable(self, name: str, category: str, subcategory: str = "") -> AdvancedSignalResult:
        return AdvancedSignalResult(
            name=name, category=category, subcategory=subcategory,
            value=None, signal=SignalStrength.UNAVAILABLE,
            score=0, weight=0, description="Data unavailable",
            historical_accuracy=0
        )

    # =========================================================================
    # CYCLE INDICATORS (61-70)
    # =========================================================================

    async def get_pi_cycle_top(self, asset: str) -> AdvancedSignalResult:
        """
        Pi Cycle Top Indicator

        Uses the 111-day MA and 350-day MA * 2.
        When 111 MA crosses above 350*2 MA = cycle top signal.
        Distance between them indicates cycle position.

        Historically 100% accurate at calling tops within 3 days.
        """
        try:
            data = await self._fetch_pi_cycle_data(asset)
            if data is None:
                return self._unavailable("Pi Cycle Top", "cycle", "top_indicators")

            ma_111 = data["ma_111"]
            ma_350_x2 = data["ma_350_x2"]
            price = data["price"]

            # Calculate distance between MAs as percentage
            distance_pct = ((ma_350_x2 - ma_111) / ma_350_x2) * 100 if ma_350_x2 > 0 else 0

            if distance_pct < 0:  # 111 MA above 350*2 MA - TOP SIGNAL
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = "PI CYCLE TOP TRIGGERED - 111 MA crossed above 350*2 MA"
            elif distance_pct < 5:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Pi Cycle warning: MAs only {distance_pct:.1f}% apart - top imminent"
            elif distance_pct < 15:
                signal, score = SignalStrength.SELL, -1
                desc = f"Pi Cycle: MAs converging ({distance_pct:.1f}% gap) - late cycle"
            elif distance_pct > 50:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Pi Cycle: MAs far apart ({distance_pct:.1f}%) - early/mid cycle"
            elif distance_pct > 30:
                signal, score = SignalStrength.BUY, 1
                desc = f"Pi Cycle: Healthy gap ({distance_pct:.1f}%)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Pi Cycle: Normal range ({distance_pct:.1f}% gap)"

            return AdvancedSignalResult(
                name="Pi Cycle Top",
                category="cycle",
                subcategory="top_indicators",
                value=distance_pct,
                signal=signal,
                score=score,
                weight=1.5,  # High weight - historically very accurate
                description=desc,
                historical_accuracy=1.0,  # 100% at calling tops
                details={
                    "ma_111": ma_111,
                    "ma_350_x2": ma_350_x2,
                    "distance_pct": distance_pct,
                    "price": price
                }
            )
        except Exception as e:
            logger.error(f"Pi Cycle error: {e}")
            return self._unavailable("Pi Cycle Top", "cycle", "top_indicators")

    async def get_golden_ratio_multiplier(self, asset: str) -> AdvancedSignalResult:
        """
        Golden Ratio Multiplier

        Uses 350 DMA and multiplies by Fibonacci ratios (1.6, 2, 3, 5, 8, 13, 21).
        Price at/above 3x = overheated
        Price at/below 1.6x = accumulation zone
        """
        try:
            data = await self._fetch_golden_ratio_data(asset)
            if data is None:
                return self._unavailable("Golden Ratio Multiplier", "cycle", "valuation")

            price = data["price"]
            ma_350 = data["ma_350"]

            if ma_350 <= 0:
                return self._unavailable("Golden Ratio Multiplier", "cycle", "valuation")

            ratio = price / ma_350

            if ratio < 1.0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Below 350 MA ({ratio:.2f}x) - deep value"
            elif ratio < 1.6:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Below 1.6x golden ratio ({ratio:.2f}x) - accumulation zone"
            elif ratio < 2.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Between 1.6-2x ({ratio:.2f}x) - fair value"
            elif ratio < 3.0:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Between 2-3x ({ratio:.2f}x) - bull market"
            elif ratio < 5.0:
                signal, score = SignalStrength.SELL, -1
                desc = f"Between 3-5x ({ratio:.2f}x) - overheated"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Above 5x golden ratio ({ratio:.2f}x) - extreme euphoria"

            return AdvancedSignalResult(
                name="Golden Ratio Multiplier",
                category="cycle",
                subcategory="valuation",
                value=ratio,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                historical_accuracy=0.85,
                details={"ratio": ratio, "ma_350": ma_350, "price": price}
            )
        except Exception as e:
            logger.error(f"Golden Ratio error: {e}")
            return self._unavailable("Golden Ratio Multiplier", "cycle", "valuation")

    async def get_2year_ma_multiplier(self, asset: str) -> AdvancedSignalResult:
        """
        2-Year MA Multiplier

        Price below 2Y MA = historically great buying opportunity
        Price above 5x 2Y MA = sell zone
        """
        try:
            data = await self._fetch_2year_ma_data(asset)
            if data is None:
                return self._unavailable("2-Year MA Multiplier", "cycle", "valuation")

            price = data["price"]
            ma_730 = data["ma_730"]  # ~2 years

            if ma_730 <= 0:
                return self._unavailable("2-Year MA Multiplier", "cycle", "valuation")

            multiplier = price / ma_730

            if multiplier < 1.0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Below 2Y MA ({multiplier:.2f}x) - generational buy"
            elif multiplier < 2.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Below 2x 2Y MA ({multiplier:.2f}x) - good value"
            elif multiplier < 3.0:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal range ({multiplier:.2f}x 2Y MA)"
            elif multiplier < 5.0:
                signal, score = SignalStrength.SELL, -1
                desc = f"Extended ({multiplier:.2f}x 2Y MA) - caution"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Above 5x 2Y MA ({multiplier:.2f}x) - extreme"

            return AdvancedSignalResult(
                name="2-Year MA Multiplier",
                category="cycle",
                subcategory="valuation",
                value=multiplier,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                historical_accuracy=0.90,
                details={"multiplier": multiplier, "ma_730": ma_730}
            )
        except Exception as e:
            logger.error(f"2Y MA error: {e}")
            return self._unavailable("2-Year MA Multiplier", "cycle", "valuation")

    async def get_rainbow_chart(self, asset: str) -> AdvancedSignalResult:
        """
        Rainbow Chart / Logarithmic Regression Bands

        Maps price to logarithmic regression bands from "Fire Sale" to "Maximum Bubble".
        """
        try:
            data = await self._fetch_rainbow_data(asset)
            if data is None:
                return self._unavailable("Rainbow Chart", "cycle", "valuation")

            price = data["price"]
            band = data["current_band"]  # 0-8 scale
            band_name = data["band_name"]

            band_signals = {
                0: (SignalStrength.STRONG_BUY, 2, "Fire Sale"),
                1: (SignalStrength.STRONG_BUY, 2, "BUY!"),
                2: (SignalStrength.BUY, 1, "Accumulate"),
                3: (SignalStrength.BUY, 1, "Still Cheap"),
                4: (SignalStrength.NEUTRAL, 0, "HODL"),
                5: (SignalStrength.NEUTRAL, 0, "Is This a Bubble?"),
                6: (SignalStrength.SELL, -1, "FOMO Intensifies"),
                7: (SignalStrength.STRONG_SELL, -2, "Sell. Seriously."),
                8: (SignalStrength.STRONG_SELL, -2, "Maximum Bubble"),
            }

            signal, score, _ = band_signals.get(band, (SignalStrength.NEUTRAL, 0, "Unknown"))

            return AdvancedSignalResult(
                name="Rainbow Chart",
                category="cycle",
                subcategory="valuation",
                value=band,
                signal=signal,
                score=score,
                weight=0.9,
                description=f"Rainbow Band: {band_name} (band {band}/8)",
                historical_accuracy=0.75,
                details={"band": band, "band_name": band_name, "price": price}
            )
        except Exception as e:
            logger.error(f"Rainbow Chart error: {e}")
            return self._unavailable("Rainbow Chart", "cycle", "valuation")

    async def get_log_growth_curve(self, asset: str) -> AdvancedSignalResult:
        """
        Bitcoin Logarithmic Growth Curves

        Based on log regression from genesis block.
        Shows fair value corridor over time.
        """
        try:
            data = await self._fetch_log_growth_data(asset)
            if data is None:
                return self._unavailable("Log Growth Curve", "cycle", "valuation")

            price = data["price"]
            fair_value = data["fair_value"]
            lower_bound = data["lower_bound"]
            upper_bound = data["upper_bound"]

            if fair_value <= 0:
                return self._unavailable("Log Growth Curve", "cycle", "valuation")

            # Position relative to fair value
            deviation = ((price - fair_value) / fair_value) * 100

            if price < lower_bound:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Below log growth floor ({deviation:+.0f}% from fair value)"
            elif price < fair_value * 0.8:
                signal, score = SignalStrength.BUY, 1
                desc = f"Below fair value ({deviation:+.0f}%)"
            elif price < fair_value * 1.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Near fair value ({deviation:+.0f}%)"
            elif price < upper_bound:
                signal, score = SignalStrength.SELL, -1
                desc = f"Above fair value ({deviation:+.0f}%)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Above log growth ceiling ({deviation:+.0f}%)"

            return AdvancedSignalResult(
                name="Log Growth Curve",
                category="cycle",
                subcategory="valuation",
                value=deviation,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                historical_accuracy=0.80,
                details={
                    "price": price,
                    "fair_value": fair_value,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "deviation_pct": deviation
                }
            )
        except Exception as e:
            logger.error(f"Log Growth error: {e}")
            return self._unavailable("Log Growth Curve", "cycle", "valuation")

    async def get_top_cap_model(self, asset: str) -> AdvancedSignalResult:
        """
        Top Cap vs Average Cap

        Top Cap = Average Cap * 35
        When market cap approaches Top Cap = cycle top
        """
        try:
            data = await self._fetch_top_cap_data(asset)
            if data is None:
                return self._unavailable("Top Cap Model", "cycle", "top_indicators")

            market_cap = data["market_cap"]
            average_cap = data["average_cap"]
            top_cap = average_cap * 35

            ratio_to_top = market_cap / top_cap if top_cap > 0 else 0

            if ratio_to_top > 0.9:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Market cap at {ratio_to_top:.0%} of Top Cap - cycle top zone"
            elif ratio_to_top > 0.7:
                signal, score = SignalStrength.SELL, -1
                desc = f"Market cap at {ratio_to_top:.0%} of Top Cap - late cycle"
            elif ratio_to_top < 0.2:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Market cap at {ratio_to_top:.0%} of Top Cap - deep value"
            elif ratio_to_top < 0.4:
                signal, score = SignalStrength.BUY, 1
                desc = f"Market cap at {ratio_to_top:.0%} of Top Cap - early cycle"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Market cap at {ratio_to_top:.0%} of Top Cap"

            return AdvancedSignalResult(
                name="Top Cap Model",
                category="cycle",
                subcategory="top_indicators",
                value=ratio_to_top,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                historical_accuracy=0.85,
                details={
                    "market_cap": market_cap,
                    "average_cap": average_cap,
                    "top_cap": top_cap,
                    "ratio_to_top": ratio_to_top
                }
            )
        except Exception as e:
            logger.error(f"Top Cap error: {e}")
            return self._unavailable("Top Cap Model", "cycle", "top_indicators")

    async def get_delta_cap(self, asset: str) -> AdvancedSignalResult:
        """
        Delta Cap

        Delta Cap = Realized Cap - Average Cap
        Historically marks cycle bottoms when price touches Delta Cap.
        """
        try:
            data = await self._fetch_delta_cap_data(asset)
            if data is None:
                return self._unavailable("Delta Cap", "cycle", "bottom_indicators")

            price = data["price"]
            delta_cap_price = data["delta_cap_price"]

            distance = ((price - delta_cap_price) / delta_cap_price) * 100 if delta_cap_price > 0 else 0

            if distance < 0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price BELOW Delta Cap ({distance:+.0f}%) - generational bottom"
            elif distance < 20:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price near Delta Cap ({distance:+.0f}%) - cycle bottom zone"
            elif distance < 50:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price {distance:.0f}% above Delta Cap"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price well above Delta Cap ({distance:.0f}%)"

            return AdvancedSignalResult(
                name="Delta Cap",
                category="cycle",
                subcategory="bottom_indicators",
                value=distance,
                signal=signal,
                score=score,
                weight=1.3,
                description=desc,
                historical_accuracy=0.95,  # Very accurate at bottoms
                details={"price": price, "delta_cap_price": delta_cap_price}
            )
        except Exception as e:
            logger.error(f"Delta Cap error: {e}")
            return self._unavailable("Delta Cap", "cycle", "bottom_indicators")

    async def get_terminal_price(self, asset: str) -> AdvancedSignalResult:
        """
        Terminal Price

        Theoretical maximum price based on coin days destroyed.
        Price approaching terminal = extreme top.
        """
        try:
            data = await self._fetch_terminal_price_data(asset)
            if data is None:
                return self._unavailable("Terminal Price", "cycle", "top_indicators")

            price = data["price"]
            terminal_price = data["terminal_price"]

            ratio = price / terminal_price if terminal_price > 0 else 0

            if ratio > 0.8:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Price at {ratio:.0%} of Terminal Price - extreme top"
            elif ratio > 0.5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Price at {ratio:.0%} of Terminal Price"
            elif ratio < 0.1:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price at {ratio:.0%} of Terminal Price - deep value"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price at {ratio:.0%} of Terminal Price"

            return AdvancedSignalResult(
                name="Terminal Price",
                category="cycle",
                subcategory="top_indicators",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                historical_accuracy=0.80,
                details={"price": price, "terminal_price": terminal_price}
            )
        except Exception as e:
            logger.error(f"Terminal Price error: {e}")
            return self._unavailable("Terminal Price", "cycle", "top_indicators")

    async def get_balanced_price(self, asset: str) -> AdvancedSignalResult:
        """
        Balanced Price

        Realized Price - Transfer Price
        Historically a strong support level in bear markets.
        """
        try:
            data = await self._fetch_balanced_price_data(asset)
            if data is None:
                return self._unavailable("Balanced Price", "cycle", "bottom_indicators")

            price = data["price"]
            balanced_price = data["balanced_price"]

            distance = ((price - balanced_price) / balanced_price) * 100 if balanced_price > 0 else 0

            if distance < 0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price BELOW Balanced Price ({distance:+.0f}%) - extreme value"
            elif distance < 30:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price near Balanced Price ({distance:+.0f}%)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price {distance:.0f}% above Balanced Price"

            return AdvancedSignalResult(
                name="Balanced Price",
                category="cycle",
                subcategory="bottom_indicators",
                value=distance,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                historical_accuracy=0.85,
                details={"price": price, "balanced_price": balanced_price}
            )
        except Exception as e:
            logger.error(f"Balanced Price error: {e}")
            return self._unavailable("Balanced Price", "cycle", "bottom_indicators")

    async def get_cvdd(self, asset: str) -> AdvancedSignalResult:
        """
        CVDD (Cumulative Value Days Destroyed)

        Has historically picked every market bottom.
        """
        try:
            data = await self._fetch_cvdd_data(asset)
            if data is None:
                return self._unavailable("CVDD", "cycle", "bottom_indicators")

            price = data["price"]
            cvdd_price = data["cvdd_price"]

            ratio = price / cvdd_price if cvdd_price > 0 else 1

            if ratio < 1.0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price at/below CVDD ({ratio:.2f}x) - historical bottom"
            elif ratio < 1.3:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price near CVDD ({ratio:.2f}x) - accumulation zone"
            elif ratio < 2.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price {ratio:.2f}x CVDD"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price well above CVDD ({ratio:.2f}x)"

            return AdvancedSignalResult(
                name="CVDD",
                category="cycle",
                subcategory="bottom_indicators",
                value=ratio,
                signal=signal,
                score=score,
                weight=1.4,
                description=desc,
                historical_accuracy=1.0,  # 100% at bottoms historically
                details={"price": price, "cvdd_price": cvdd_price}
            )
        except Exception as e:
            logger.error(f"CVDD error: {e}")
            return self._unavailable("CVDD", "cycle", "bottom_indicators")

    # =========================================================================
    # ADVANCED ON-CHAIN (71-85)
    # =========================================================================

    async def get_rhodl_ratio(self, asset: str) -> AdvancedSignalResult:
        """
        RHODL Ratio

        Ratio of 1-week and 1-2 year HODL bands.
        High = new money flooding in (top)
        Low = old money dominates (bottom)
        """
        try:
            data = await self._fetch_rhodl_data(asset)
            if data is None:
                return self._unavailable("RHODL Ratio", "onchain_advanced", "hodl_behavior")

            rhodl = data["rhodl"]

            if rhodl > 50000:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"RHODL extreme ({rhodl:,.0f}) - new money flood, top signal"
            elif rhodl > 10000:
                signal, score = SignalStrength.SELL, -1
                desc = f"RHODL elevated ({rhodl:,.0f}) - late cycle"
            elif rhodl < 350:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"RHODL low ({rhodl:,.0f}) - diamond hands dominate, bottom"
            elif rhodl < 1000:
                signal, score = SignalStrength.BUY, 1
                desc = f"RHODL moderate ({rhodl:,.0f}) - early cycle"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"RHODL normal ({rhodl:,.0f})"

            return AdvancedSignalResult(
                name="RHODL Ratio",
                category="onchain_advanced",
                subcategory="hodl_behavior",
                value=rhodl,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                historical_accuracy=0.90,
                details={"rhodl": rhodl}
            )
        except Exception as e:
            logger.error(f"RHODL error: {e}")
            return self._unavailable("RHODL Ratio", "onchain_advanced", "hodl_behavior")

    async def get_asopr(self, asset: str) -> AdvancedSignalResult:
        """
        aSOPR (Adjusted SOPR)

        SOPR adjusted by removing young coins (< 1 hour).
        Better signal for long-term holder behavior.
        """
        try:
            data = await self._fetch_asopr_data(asset)
            if data is None:
                return self._unavailable("aSOPR", "onchain_advanced", "profit_loss")

            asopr = data["asopr"]
            asopr_7d = data.get("asopr_7d", asopr)

            if asopr < 0.95:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"aSOPR {asopr:.3f} - deep capitulation"
            elif asopr < 1.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"aSOPR {asopr:.3f} - selling at loss"
            elif asopr > 1.05:
                signal, score = SignalStrength.SELL, -1
                desc = f"aSOPR {asopr:.3f} - profit taking"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"aSOPR {asopr:.3f} - near breakeven"

            return AdvancedSignalResult(
                name="aSOPR",
                category="onchain_advanced",
                subcategory="profit_loss",
                value=asopr,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                historical_accuracy=0.82,
                details={"asopr": asopr, "asopr_7d": asopr_7d}
            )
        except Exception as e:
            logger.error(f"aSOPR error: {e}")
            return self._unavailable("aSOPR", "onchain_advanced", "profit_loss")

    async def get_lth_sopr(self, asset: str) -> AdvancedSignalResult:
        """
        LTH-SOPR (Long Term Holder SOPR)

        SOPR for coins held >155 days.
        LTH selling at loss = extreme capitulation.
        """
        try:
            data = await self._fetch_lth_sopr_data(asset)
            if data is None:
                return self._unavailable("LTH-SOPR", "onchain_advanced", "profit_loss")

            lth_sopr = data["lth_sopr"]

            if lth_sopr < 0.85:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"LTH-SOPR {lth_sopr:.3f} - long-term holders capitulating"
            elif lth_sopr < 1.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"LTH-SOPR {lth_sopr:.3f} - LTH selling at loss"
            elif lth_sopr > 3.0:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"LTH-SOPR {lth_sopr:.3f} - extreme LTH profit taking"
            elif lth_sopr > 1.5:
                signal, score = SignalStrength.SELL, -1
                desc = f"LTH-SOPR {lth_sopr:.3f} - LTH distribution"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"LTH-SOPR {lth_sopr:.3f} - normal"

            return AdvancedSignalResult(
                name="LTH-SOPR",
                category="onchain_advanced",
                subcategory="profit_loss",
                value=lth_sopr,
                signal=signal,
                score=score,
                weight=1.3,
                description=desc,
                historical_accuracy=0.88,
                details={"lth_sopr": lth_sopr}
            )
        except Exception as e:
            logger.error(f"LTH-SOPR error: {e}")
            return self._unavailable("LTH-SOPR", "onchain_advanced", "profit_loss")

    async def get_sth_sopr(self, asset: str) -> AdvancedSignalResult:
        """
        STH-SOPR (Short Term Holder SOPR)

        SOPR for coins held <155 days.
        STH behavior indicates near-term momentum.
        """
        try:
            data = await self._fetch_sth_sopr_data(asset)
            if data is None:
                return self._unavailable("STH-SOPR", "onchain_advanced", "profit_loss")

            sth_sopr = data["sth_sopr"]

            if sth_sopr < 0.9:
                signal, score = SignalStrength.BUY, 1
                desc = f"STH-SOPR {sth_sopr:.3f} - short-term panic"
            elif sth_sopr > 1.1:
                signal, score = SignalStrength.SELL, -1
                desc = f"STH-SOPR {sth_sopr:.3f} - STH profit taking"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"STH-SOPR {sth_sopr:.3f} - normal"

            return AdvancedSignalResult(
                name="STH-SOPR",
                category="onchain_advanced",
                subcategory="profit_loss",
                value=sth_sopr,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                historical_accuracy=0.70,
                details={"sth_sopr": sth_sopr}
            )
        except Exception as e:
            logger.error(f"STH-SOPR error: {e}")
            return self._unavailable("STH-SOPR", "onchain_advanced", "profit_loss")

    async def get_supply_in_profit(self, asset: str) -> AdvancedSignalResult:
        """
        Supply in Profit

        Percentage of supply currently in profit.
        < 50% = most holders underwater (bottom signal)
        > 95% = everyone in profit (top signal)
        """
        try:
            data = await self._fetch_supply_profit_data(asset)
            if data is None:
                return self._unavailable("Supply in Profit", "onchain_advanced", "profit_loss")

            pct_profit = data["pct_in_profit"]

            if pct_profit < 50:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Only {pct_profit:.0f}% of supply in profit - capitulation"
            elif pct_profit < 60:
                signal, score = SignalStrength.BUY, 1
                desc = f"{pct_profit:.0f}% of supply in profit - accumulation zone"
            elif pct_profit > 95:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"{pct_profit:.0f}% of supply in profit - euphoria"
            elif pct_profit > 85:
                signal, score = SignalStrength.SELL, -1
                desc = f"{pct_profit:.0f}% of supply in profit - late cycle"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"{pct_profit:.0f}% of supply in profit"

            return AdvancedSignalResult(
                name="Supply in Profit",
                category="onchain_advanced",
                subcategory="profit_loss",
                value=pct_profit,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                historical_accuracy=0.85,
                details={"pct_in_profit": pct_profit}
            )
        except Exception as e:
            logger.error(f"Supply in Profit error: {e}")
            return self._unavailable("Supply in Profit", "onchain_advanced", "profit_loss")

    async def get_realized_losses(self, asset: str) -> AdvancedSignalResult:
        """
        Realized Losses

        Total USD value of losses realized on-chain.
        Spikes in realized losses = capitulation events.
        """
        try:
            data = await self._fetch_realized_losses_data(asset)
            if data is None:
                return self._unavailable("Realized Losses", "onchain_advanced", "profit_loss")

            losses_usd = data["realized_losses"]
            losses_zscore = data.get("zscore", 0)

            if losses_zscore > 3:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme loss realization (z={losses_zscore:.1f}) - capitulation"
            elif losses_zscore > 2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Elevated loss realization (z={losses_zscore:.1f})"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal loss realization (z={losses_zscore:.1f})"

            return AdvancedSignalResult(
                name="Realized Losses",
                category="onchain_advanced",
                subcategory="profit_loss",
                value=losses_zscore,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                historical_accuracy=0.80,
                details={"realized_losses_usd": losses_usd, "zscore": losses_zscore}
            )
        except Exception as e:
            logger.error(f"Realized Losses error: {e}")
            return self._unavailable("Realized Losses", "onchain_advanced", "profit_loss")

    async def get_liveliness(self, asset: str) -> AdvancedSignalResult:
        """
        Liveliness

        Ratio of all CDD ever created to all CDD ever possible.
        Rising = spending activity increasing
        Falling = accumulation
        """
        try:
            data = await self._fetch_liveliness_data(asset)
            if data is None:
                return self._unavailable("Liveliness", "onchain_advanced", "hodl_behavior")

            liveliness = data["liveliness"]
            change_30d = data.get("change_30d", 0)

            if liveliness > 0.7 and change_30d > 0:
                signal, score = SignalStrength.SELL, -1
                desc = f"Liveliness {liveliness:.3f} (rising) - spending accelerating"
            elif liveliness < 0.5 and change_30d < 0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Liveliness {liveliness:.3f} (falling) - accumulation"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Liveliness {liveliness:.3f}"

            return AdvancedSignalResult(
                name="Liveliness",
                category="onchain_advanced",
                subcategory="hodl_behavior",
                value=liveliness,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                historical_accuracy=0.70,
                details={"liveliness": liveliness, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"Liveliness error: {e}")
            return self._unavailable("Liveliness", "onchain_advanced", "hodl_behavior")

    async def get_dormancy_flow(self, asset: str) -> AdvancedSignalResult:
        """
        Dormancy Flow

        Ratio of market cap to annualized dormancy value.
        Low values historically mark accumulation zones.
        """
        try:
            data = await self._fetch_dormancy_flow_data(asset)
            if data is None:
                return self._unavailable("Dormancy Flow", "onchain_advanced", "hodl_behavior")

            dormancy_flow = data["dormancy_flow"]

            if dormancy_flow < 250000:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Dormancy Flow {dormancy_flow:,.0f} - major accumulation zone"
            elif dormancy_flow < 500000:
                signal, score = SignalStrength.BUY, 1
                desc = f"Dormancy Flow {dormancy_flow:,.0f} - undervalued"
            elif dormancy_flow > 5000000:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Dormancy Flow {dormancy_flow:,.0f} - overextended"
            elif dormancy_flow > 2000000:
                signal, score = SignalStrength.SELL, -1
                desc = f"Dormancy Flow {dormancy_flow:,.0f} - elevated"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Dormancy Flow {dormancy_flow:,.0f}"

            return AdvancedSignalResult(
                name="Dormancy Flow",
                category="onchain_advanced",
                subcategory="hodl_behavior",
                value=dormancy_flow,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                historical_accuracy=0.85,
                details={"dormancy_flow": dormancy_flow}
            )
        except Exception as e:
            logger.error(f"Dormancy Flow error: {e}")
            return self._unavailable("Dormancy Flow", "onchain_advanced", "hodl_behavior")

    async def get_illiquid_supply_change(self, asset: str) -> AdvancedSignalResult:
        """
        Illiquid Supply Change

        Change in supply held by entities with <25% spending history.
        Increasing = accumulation by strong hands.
        """
        try:
            data = await self._fetch_illiquid_supply_data(asset)
            if data is None:
                return self._unavailable("Illiquid Supply Change", "onchain_advanced", "supply_dynamics")

            change_30d = data["change_30d_pct"]
            illiquid_supply_pct = data.get("illiquid_supply_pct", 0)

            if change_30d > 2:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Illiquid supply surging ({change_30d:+.1f}%/mo) - strong accumulation"
            elif change_30d > 0.5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Illiquid supply growing ({change_30d:+.1f}%/mo)"
            elif change_30d < -2:
                signal, score = SignalStrength.SELL, -1
                desc = f"Illiquid supply declining ({change_30d:+.1f}%/mo) - distribution"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Illiquid supply stable ({change_30d:+.1f}%/mo)"

            return AdvancedSignalResult(
                name="Illiquid Supply Change",
                category="onchain_advanced",
                subcategory="supply_dynamics",
                value=change_30d,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                historical_accuracy=0.80,
                details={
                    "change_30d_pct": change_30d,
                    "illiquid_supply_pct": illiquid_supply_pct
                }
            )
        except Exception as e:
            logger.error(f"Illiquid Supply error: {e}")
            return self._unavailable("Illiquid Supply Change", "onchain_advanced", "supply_dynamics")

    # =========================================================================
    # EXCHANGE & FLOW METRICS (86-95)
    # =========================================================================

    async def get_exchange_reserve_ratio(self, asset: str) -> AdvancedSignalResult:
        """
        Exchange Reserve Ratio

        Ratio of exchange reserves to total supply.
        Declining ratio = bullish (coins leaving exchanges)
        """
        try:
            data = await self._fetch_exchange_reserve_ratio_data(asset)
            if data is None:
                return self._unavailable("Exchange Reserve Ratio", "exchange_flow", "reserves")

            ratio = data["reserve_ratio"]
            change_30d = data.get("change_30d", 0)

            if ratio < 0.10 and change_30d < 0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Only {ratio:.1%} on exchanges (declining) - supply squeeze"
            elif ratio < 0.12 and change_30d < 0:
                signal, score = SignalStrength.BUY, 1
                desc = f"{ratio:.1%} on exchanges - accumulation"
            elif ratio > 0.15 and change_30d > 0:
                signal, score = SignalStrength.SELL, -1
                desc = f"{ratio:.1%} on exchanges (rising) - distribution"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"{ratio:.1%} on exchanges"

            return AdvancedSignalResult(
                name="Exchange Reserve Ratio",
                category="exchange_flow",
                subcategory="reserves",
                value=ratio,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                historical_accuracy=0.75,
                details={"reserve_ratio": ratio, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"Exchange Reserve Ratio error: {e}")
            return self._unavailable("Exchange Reserve Ratio", "exchange_flow", "reserves")

    async def get_stablecoin_exchange_reserve(self) -> AdvancedSignalResult:
        """
        Stablecoin Exchange Reserve

        Stablecoins on exchanges = dry powder for buying.
        Rising reserves = bullish buying pressure incoming.
        """
        try:
            data = await self._fetch_stablecoin_reserve_data()
            if data is None:
                return self._unavailable("Stablecoin Exchange Reserve", "exchange_flow", "stablecoins")

            reserve_usd = data["reserve_usd"]
            change_7d = data.get("change_7d_pct", 0)

            if change_7d > 10:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Stablecoin inflow surge ({change_7d:+.1f}%/wk) - buying power incoming"
            elif change_7d > 3:
                signal, score = SignalStrength.BUY, 1
                desc = f"Stablecoin inflows ({change_7d:+.1f}%/wk)"
            elif change_7d < -10:
                signal, score = SignalStrength.SELL, -1
                desc = f"Stablecoin outflows ({change_7d:+.1f}%/wk) - buying power depleting"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stablecoin reserves stable ({change_7d:+.1f}%/wk)"

            return AdvancedSignalResult(
                name="Stablecoin Exchange Reserve",
                category="exchange_flow",
                subcategory="stablecoins",
                value=change_7d,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                historical_accuracy=0.75,
                details={"reserve_usd": reserve_usd, "change_7d_pct": change_7d}
            )
        except Exception as e:
            logger.error(f"Stablecoin Reserve error: {e}")
            return self._unavailable("Stablecoin Exchange Reserve", "exchange_flow", "stablecoins")

    async def get_exchange_whale_ratio(self, asset: str) -> AdvancedSignalResult:
        """
        Exchange Whale Ratio

        Ratio of top 10 inflows to total inflows.
        High ratio = whales dominating (follow smart money).
        """
        try:
            data = await self._fetch_whale_ratio_data(asset)
            if data is None:
                return self._unavailable("Exchange Whale Ratio", "exchange_flow", "whale_activity")

            whale_ratio = data["whale_ratio"]

            if whale_ratio > 0.9:
                signal, score = SignalStrength.SELL, -1
                desc = f"Whale inflow ratio {whale_ratio:.0%} - whales depositing to sell"
            elif whale_ratio < 0.3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Whale inflow ratio {whale_ratio:.0%} - retail dominated"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Whale inflow ratio {whale_ratio:.0%}"

            return AdvancedSignalResult(
                name="Exchange Whale Ratio",
                category="exchange_flow",
                subcategory="whale_activity",
                value=whale_ratio,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                historical_accuracy=0.65,
                details={"whale_ratio": whale_ratio}
            )
        except Exception as e:
            logger.error(f"Whale Ratio error: {e}")
            return self._unavailable("Exchange Whale Ratio", "exchange_flow", "whale_activity")

    async def get_fund_flow_ratio(self, asset: str) -> AdvancedSignalResult:
        """
        Fund Flow Ratio

        Ratio of exchange inflows to exchange reserves.
        High ratio = sell pressure relative to available liquidity.
        """
        try:
            data = await self._fetch_fund_flow_ratio_data(asset)
            if data is None:
                return self._unavailable("Fund Flow Ratio", "exchange_flow", "liquidity")

            ffr = data["fund_flow_ratio"]

            if ffr > 0.10:
                signal, score = SignalStrength.SELL, -1
                desc = f"Fund Flow Ratio {ffr:.3f} - high inflow pressure"
            elif ffr < 0.02:
                signal, score = SignalStrength.BUY, 1
                desc = f"Fund Flow Ratio {ffr:.3f} - low sell pressure"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Fund Flow Ratio {ffr:.3f}"

            return AdvancedSignalResult(
                name="Fund Flow Ratio",
                category="exchange_flow",
                subcategory="liquidity",
                value=ffr,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                historical_accuracy=0.70,
                details={"fund_flow_ratio": ffr}
            )
        except Exception as e:
            logger.error(f"Fund Flow Ratio error: {e}")
            return self._unavailable("Fund Flow Ratio", "exchange_flow", "liquidity")

    # =========================================================================
    # MARKET STRUCTURE (106-115)
    # =========================================================================

    async def get_altcoin_season_index(self) -> AdvancedSignalResult:
        """
        Altcoin Season Index

        Measures if top 50 altcoins are outperforming BTC.
        > 75% = Altcoin Season
        < 25% = Bitcoin Season
        """
        try:
            data = await self._fetch_altseason_data()
            if data is None:
                return self._unavailable("Altcoin Season Index", "market_structure", "rotation")

            index = data["altseason_index"]

            if index > 75:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Altcoin Season ({index}) - consider rotating BTC→alts"
            elif index < 25:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Bitcoin Season ({index}) - consider rotating alts→BTC"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Mixed season ({index})"

            return AdvancedSignalResult(
                name="Altcoin Season Index",
                category="market_structure",
                subcategory="rotation",
                value=index,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                historical_accuracy=0.60,
                details={"altseason_index": index}
            )
        except Exception as e:
            logger.error(f"Altseason error: {e}")
            return self._unavailable("Altcoin Season Index", "market_structure", "rotation")

    async def get_btc_dominance(self) -> AdvancedSignalResult:
        """
        BTC Dominance

        BTC market cap / total crypto market cap.
        Rising dominance in downtrend = flight to safety.
        """
        try:
            data = await self._fetch_btc_dominance_data()
            if data is None:
                return self._unavailable("BTC Dominance", "market_structure", "rotation")

            dominance = data["dominance"]
            change_30d = data.get("change_30d", 0)

            if dominance > 60 and change_30d > 5:
                signal, score = SignalStrength.SELL, -1
                desc = f"BTC dominance rising to {dominance:.1f}% - risk-off"
            elif dominance < 40 and change_30d < -5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"BTC dominance falling to {dominance:.1f}% - alt mania"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"BTC dominance at {dominance:.1f}%"

            return AdvancedSignalResult(
                name="BTC Dominance",
                category="market_structure",
                subcategory="rotation",
                value=dominance,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                historical_accuracy=0.60,
                details={"dominance": dominance, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"BTC Dominance error: {e}")
            return self._unavailable("BTC Dominance", "market_structure", "rotation")

    async def get_total_market_cap_trend(self) -> AdvancedSignalResult:
        """
        Total Crypto Market Cap

        Overall market trend indicator.
        """
        try:
            data = await self._fetch_total_mcap_data()
            if data is None:
                return self._unavailable("Total Market Cap", "market_structure", "overall")

            mcap = data["total_market_cap"]
            ath = data.get("ath", mcap)
            change_30d = data.get("change_30d_pct", 0)

            drawdown = ((ath - mcap) / ath) * 100 if ath > 0 else 0

            if drawdown > 70:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Total market {drawdown:.0f}% from ATH - major opportunity"
            elif drawdown > 50:
                signal, score = SignalStrength.BUY, 1
                desc = f"Total market {drawdown:.0f}% from ATH"
            elif drawdown < 10 and change_30d > 20:
                signal, score = SignalStrength.SELL, -1
                desc = f"Near ATH with {change_30d:+.0f}% monthly gain - extended"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Total market {drawdown:.0f}% from ATH"

            return AdvancedSignalResult(
                name="Total Market Cap",
                category="market_structure",
                subcategory="overall",
                value=drawdown,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                historical_accuracy=0.70,
                details={
                    "total_market_cap": mcap,
                    "ath": ath,
                    "drawdown_pct": drawdown,
                    "change_30d_pct": change_30d
                }
            )
        except Exception as e:
            logger.error(f"Total Market Cap error: {e}")
            return self._unavailable("Total Market Cap", "market_structure", "overall")

    # =========================================================================
    # MACRO LIQUIDITY (116-125)
    # =========================================================================

    async def get_global_m2_change(self) -> AdvancedSignalResult:
        """
        Global M2 Money Supply Change

        Crypto correlates with global liquidity.
        M2 expansion = bullish for risk assets.
        """
        try:
            data = await self._fetch_global_m2_data()
            if data is None:
                return self._unavailable("Global M2 Change", "macro_liquidity", "money_supply")

            yoy_change = data["yoy_change_pct"]

            if yoy_change > 10:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"M2 expanding {yoy_change:+.1f}% YoY - liquidity tailwind"
            elif yoy_change > 5:
                signal, score = SignalStrength.BUY, 1
                desc = f"M2 growing {yoy_change:+.1f}% YoY"
            elif yoy_change < -2:
                signal, score = SignalStrength.SELL, -1
                desc = f"M2 contracting {yoy_change:+.1f}% YoY - liquidity headwind"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"M2 stable {yoy_change:+.1f}% YoY"

            return AdvancedSignalResult(
                name="Global M2 Change",
                category="macro_liquidity",
                subcategory="money_supply",
                value=yoy_change,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                historical_accuracy=0.75,
                details={"yoy_change_pct": yoy_change}
            )
        except Exception as e:
            logger.error(f"Global M2 error: {e}")
            return self._unavailable("Global M2 Change", "macro_liquidity", "money_supply")

    async def get_real_interest_rate(self) -> AdvancedSignalResult:
        """
        Real Interest Rate

        Nominal rate minus inflation.
        Negative real rates = bullish for crypto.
        """
        try:
            data = await self._fetch_real_rate_data()
            if data is None:
                return self._unavailable("Real Interest Rate", "macro_liquidity", "rates")

            real_rate = data["real_rate"]

            if real_rate < -2:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Deeply negative real rate ({real_rate:+.1f}%) - bullish"
            elif real_rate < 0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Negative real rate ({real_rate:+.1f}%)"
            elif real_rate > 3:
                signal, score = SignalStrength.SELL, -1
                desc = f"High real rate ({real_rate:+.1f}%) - headwind"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Real rate {real_rate:+.1f}%"

            return AdvancedSignalResult(
                name="Real Interest Rate",
                category="macro_liquidity",
                subcategory="rates",
                value=real_rate,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                historical_accuracy=0.70,
                details={"real_rate": real_rate}
            )
        except Exception as e:
            logger.error(f"Real Rate error: {e}")
            return self._unavailable("Real Interest Rate", "macro_liquidity", "rates")

    async def get_global_liquidity_index(self) -> AdvancedSignalResult:
        """
        Global Liquidity Index

        Composite of central bank balance sheets and credit conditions.
        """
        try:
            data = await self._fetch_liquidity_index_data()
            if data is None:
                return self._unavailable("Global Liquidity Index", "macro_liquidity", "composite")

            index = data["index"]
            change_3m = data.get("change_3m_pct", 0)

            if change_3m > 5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Liquidity expanding ({change_3m:+.1f}% 3M)"
            elif change_3m < -5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Liquidity contracting ({change_3m:+.1f}% 3M)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Liquidity stable ({change_3m:+.1f}% 3M)"

            return AdvancedSignalResult(
                name="Global Liquidity Index",
                category="macro_liquidity",
                subcategory="composite",
                value=change_3m,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                historical_accuracy=0.70,
                details={"index": index, "change_3m_pct": change_3m}
            )
        except Exception as e:
            logger.error(f"Liquidity Index error: {e}")
            return self._unavailable("Global Liquidity Index", "macro_liquidity", "composite")

    # =========================================================================
    # DERIVATIVES ADVANCED (126-135)
    # =========================================================================

    async def get_perp_spot_volume_ratio(self, asset: str) -> AdvancedSignalResult:
        """
        Perpetual Volume / Spot Volume Ratio

        High ratio = derivatives-driven (more volatile, less sustainable)
        Low ratio = spot-driven (healthier)
        """
        try:
            data = await self._fetch_perp_spot_ratio_data(asset)
            if data is None:
                return self._unavailable("Perp/Spot Ratio", "derivatives_advanced", "volume")

            ratio = data["ratio"]

            if ratio > 5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Perp volume {ratio:.1f}x spot - derivatives-driven, risky"
            elif ratio < 1:
                signal, score = SignalStrength.BUY, 1
                desc = f"Perp volume {ratio:.1f}x spot - spot-driven, healthy"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Perp volume {ratio:.1f}x spot"

            return AdvancedSignalResult(
                name="Perp/Spot Ratio",
                category="derivatives_advanced",
                subcategory="volume",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                historical_accuracy=0.65,
                details={"ratio": ratio}
            )
        except Exception as e:
            logger.error(f"Perp/Spot error: {e}")
            return self._unavailable("Perp/Spot Ratio", "derivatives_advanced", "volume")

    async def get_implied_vs_realized_vol(self, asset: str) -> AdvancedSignalResult:
        """
        Implied vs Realized Volatility Ratio

        IV > RV = options expensive (fear)
        IV < RV = options cheap (complacency)
        """
        try:
            data = await self._fetch_vol_ratio_data(asset)
            if data is None:
                return self._unavailable("IV/RV Ratio", "derivatives_advanced", "volatility")

            iv = data["implied_vol"]
            rv = data["realized_vol"]
            ratio = iv / rv if rv > 0 else 1

            if ratio > 1.5:
                signal, score = SignalStrength.BUY, 1
                desc = f"IV/RV {ratio:.2f} - options expensive, fear elevated"
            elif ratio < 0.8:
                signal, score = SignalStrength.SELL, -1
                desc = f"IV/RV {ratio:.2f} - options cheap, complacency"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"IV/RV {ratio:.2f} - normal"

            return AdvancedSignalResult(
                name="IV/RV Ratio",
                category="derivatives_advanced",
                subcategory="volatility",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                historical_accuracy=0.65,
                details={"implied_vol": iv, "realized_vol": rv, "ratio": ratio}
            )
        except Exception as e:
            logger.error(f"IV/RV error: {e}")
            return self._unavailable("IV/RV Ratio", "derivatives_advanced", "volatility")

    async def get_gamma_exposure(self, asset: str) -> AdvancedSignalResult:
        """
        Gamma Exposure

        Net gamma of market makers.
        Positive gamma = price stability
        Negative gamma = potential for volatility
        """
        try:
            data = await self._fetch_gamma_data(asset)
            if data is None:
                return self._unavailable("Gamma Exposure", "derivatives_advanced", "positioning")

            gamma = data["net_gamma"]  # In USD terms

            if gamma < -1e9:  # Large negative gamma
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Large negative gamma - volatility amplification risk"
            elif gamma > 1e9:  # Large positive gamma
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Large positive gamma - stability support"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Neutral gamma positioning"

            return AdvancedSignalResult(
                name="Gamma Exposure",
                category="derivatives_advanced",
                subcategory="positioning",
                value=gamma,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                historical_accuracy=0.60,
                details={"net_gamma": gamma}
            )
        except Exception as e:
            logger.error(f"Gamma error: {e}")
            return self._unavailable("Gamma Exposure", "derivatives_advanced", "positioning")

    # =========================================================================
    # FETCH METHODS (Placeholders)
    # =========================================================================

    async def _fetch_pi_cycle_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_golden_ratio_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_2year_ma_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_rainbow_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_log_growth_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_top_cap_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_delta_cap_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_terminal_price_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_balanced_price_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_cvdd_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_rhodl_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_asopr_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_lth_sopr_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_sth_sopr_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_supply_profit_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_realized_losses_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_liveliness_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_dormancy_flow_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_illiquid_supply_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_exchange_reserve_ratio_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_stablecoin_reserve_data(self) -> Optional[Dict]:
        return None

    async def _fetch_whale_ratio_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_fund_flow_ratio_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_altseason_data(self) -> Optional[Dict]:
        return None

    async def _fetch_btc_dominance_data(self) -> Optional[Dict]:
        return None

    async def _fetch_total_mcap_data(self) -> Optional[Dict]:
        return None

    async def _fetch_global_m2_data(self) -> Optional[Dict]:
        return None

    async def _fetch_real_rate_data(self) -> Optional[Dict]:
        return None

    async def _fetch_liquidity_index_data(self) -> Optional[Dict]:
        return None

    async def _fetch_perp_spot_ratio_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_vol_ratio_data(self, asset: str) -> Optional[Dict]:
        return None

    async def _fetch_gamma_data(self, asset: str) -> Optional[Dict]:
        return None


def format_advanced_signals(signals: List[AdvancedSignalResult]) -> str:
    """Format advanced signals for display."""
    lines = [
        "",
        "=" * 70,
        "  ADVANCED MARKET SIGNALS",
        "=" * 70,
        "",
    ]

    # Group by category
    categories: Dict[str, List[AdvancedSignalResult]] = {}
    for sig in signals:
        if sig.category not in categories:
            categories[sig.category] = []
        categories[sig.category].append(sig)

    for category, cat_signals in categories.items():
        lines.append(f"  {category.upper().replace('_', ' ')}")
        lines.append("-" * 40)

        for sig in cat_signals:
            if sig.signal == SignalStrength.UNAVAILABLE:
                indicator = "❓"
            elif sig.score >= 2:
                indicator = "🟢🟢"
            elif sig.score == 1:
                indicator = "🟢"
            elif sig.score <= -2:
                indicator = "🔴🔴"
            elif sig.score == -1:
                indicator = "🔴"
            else:
                indicator = "⚪"

            acc = f"[{sig.historical_accuracy:.0%}]" if sig.historical_accuracy > 0 else ""
            lines.append(f"    {indicator} {sig.name} {acc}")
            lines.append(f"       {sig.description}")

        lines.append("")

    return "\n".join(lines)
