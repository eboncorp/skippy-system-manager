"""
Expanded Market Signals Module - 40+ Additional Indicators

Extends the 60 base signals with advanced analytics:

CATEGORY 9: SMART MONEY / BEHAVIORAL (61-72)
61. Entity-Adjusted SOPR
62. Long-term Holder SOPR (LTH-SOPR)
63. Short-term Holder SOPR (STH-SOPR)
64. Realized Losses (absolute)
65. Exchange Whale Ratio
66. Accumulation Trend Score
67. Dormancy Flow
68. Supply in Profit %
69. Liveliness
70. ASOL (Average Spent Output Lifespan)
71. Binary CDD (Coin Days Destroyed > median)
72. Long-term Holder Supply

CATEGORY 10: DEFI / ALTCOIN SPECIFIC (73-84)
73. ETH Gas (Gwei)
74. ETH Burn Rate (post-EIP1559)
75. ETH Staking Ratio
76. L2 TVL (Arbitrum, Optimism, Base)
77. DEX vs CEX Volume Ratio
78. Altcoin Season Index
79. BTC Dominance
80. ETH/BTC Ratio
81. Total Stablecoin Market Cap
82. USDT Dominance
83. Real Yield (DeFi)
84. Lending Utilization Rate

CATEGORY 11: ORDER FLOW / MICROSTRUCTURE (85-92)
85. Bid-Ask Spread (top exchanges)
86. Order Book Depth (2% depth)
87. Whale Order Flow (>$100k trades)
88. Spot vs Derivatives Volume
89. Aggregated CVD (Cumulative Volume Delta)
90. Taker Buy/Sell Ratio
91. Large Trade Intensity
92. Slippage Estimate (for $1M order)

CATEGORY 12: ECONOMIC CALENDAR (93-100)
93. FOMC Days (meeting/announcement)
94. CPI Release Proximity
95. NFP Day Impact
96. Options Expiry (weekly/monthly/quarterly)
97. CME Gap (weekend gap analysis)
98. Quarter End Rebalancing
99. Tax Season (US April)
100. Halving Countdown

CATEGORY 13: CROSS-CHAIN / MULTI-ASSET (101-108)
101. Cross-Exchange Arbitrage Spread
102. Bridge Volume (major bridges)
103. Wrapped BTC Supply (WBTC, etc.)
104. Stablecoin Depeg Risk Score
105. Total Crypto Market Cap
106. BTC vs Gold Market Cap Ratio
107. Crypto vs M2 Money Supply
108. Relative Strength vs S&P (30d)

CATEGORY 14: CYCLE POSITION INDICATORS (109-116)
109. Pi Cycle Top/Bottom Indicator
110. 200-Week MA Heatmap Position
111. Bitcoin Rainbow Price Band
112. Halving Cycle Position (0-100%)
113. 4-Year Cycle Phase
114. Mayer Multiple
115. Investor Tool (2Y MA x5)
116. Golden Ratio Multiplier

CATEGORY 15: ADVANCED ON-CHAIN (117-124)
117. Realized Cap HODL Waves
118. Value Days Destroyed (VDD)
119. Transfer Volume (adjusted)
120. Velocity (NVT inverse)
121. Young Supply Profit/Loss
122. Old Supply Movement
123. Revived Supply (dormant coins moving)
124. Stablecoin Exchange Ratio

CATEGORY 16: SENTIMENT ADVANCED (125-130)
125. Weighted Social Volume
126. Development Activity (GitHub commits)
127. Whale Alert Frequency
128. Exchange Maintenance Events
129. Regulatory News Sentiment
130. AI/LLM Mention Trend
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import aiohttp
import json
import logging
import math

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
class ExpandedCategorySummary:
    """Summary for a category of signals."""
    name: str
    signals: List[SignalResult]
    avg_score: float
    weighted_score: float
    bullish_count: int
    bearish_count: int
    neutral_count: int
    unavailable_count: int


@dataclass
class ExpandedSignalAnalysis:
    """Analysis with all 70 additional signals."""
    timestamp: datetime
    asset: str
    
    # New category summaries (9-16)
    smart_money: ExpandedCategorySummary
    defi_altcoin: ExpandedCategorySummary
    order_flow: ExpandedCategorySummary
    economic_calendar: ExpandedCategorySummary
    cross_chain: ExpandedCategorySummary
    cycle_position: ExpandedCategorySummary
    advanced_onchain: ExpandedCategorySummary
    advanced_sentiment: ExpandedCategorySummary
    
    # Scores
    total_signals: int
    available_signals: int
    composite_score: float  # -100 to +100
    confidence: float
    
    # All signals for reference
    all_signals: List[SignalResult] = field(default_factory=list)


class ExpandedSignalsAnalyzer:
    """
    Analyzes 70 additional market signals beyond the base 60.
    
    These signals provide deeper insight into:
    - Smart money behavior
    - DeFi ecosystem health
    - Order flow dynamics
    - Macro calendar events
    - Cross-chain flows
    - Cycle positioning
    """
    
    CATEGORY_WEIGHTS = {
        "smart_money": 1.3,        # Very reliable
        "defi_altcoin": 0.9,
        "order_flow": 1.1,
        "economic_calendar": 0.8,
        "cross_chain": 0.7,
        "cycle_position": 1.0,
        "advanced_onchain": 1.2,
        "advanced_sentiment": 0.7,
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
            data, ts = self._cache[key]
            if datetime.utcnow() - ts < self._cache_ttl:
                return data
        return None
    
    def _set_cached(self, key: str, data: Any):
        self._cache[key] = (data, datetime.utcnow())
    
    def _unavailable_signal(self, name: str, category: str) -> SignalResult:
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
    # CATEGORY 9: SMART MONEY / BEHAVIORAL
    # =========================================================================
    
    async def _get_entity_adjusted_sopr(self, asset: str) -> SignalResult:
        """
        Entity-Adjusted SOPR - filters out internal exchange movements.
        < 0.95: Strong capitulation (Strong Buy)
        0.95-1.0: Selling at loss (Buy)
        1.0-1.05: Break-even zone (Neutral)
        > 1.05: Profit taking (Sell/Strong Sell)
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "sopr_entity_adjusted")
            if data is None:
                return self._unavailable_signal("Entity-Adjusted SOPR", "smart_money")
            
            sopr = data.get("value", 1.0)
            
            if sopr < 0.90:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme capitulation (aSOPR: {sopr:.3f})"
            elif sopr < 0.97:
                signal, score = SignalStrength.BUY, 1
                desc = f"Selling at loss (aSOPR: {sopr:.3f})"
            elif sopr < 1.03:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Break-even zone (aSOPR: {sopr:.3f})"
            elif sopr < 1.10:
                signal, score = SignalStrength.SELL, -1
                desc = f"Profit taking (aSOPR: {sopr:.3f})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Heavy profit taking (aSOPR: {sopr:.3f})"
            
            return SignalResult(
                name="Entity-Adjusted SOPR",
                category="smart_money",
                value=sopr,
                signal=signal,
                score=score,
                weight=1.3,
                description=desc,
                details={"sopr": sopr}
            )
        except Exception as e:
            logger.error(f"Error fetching Entity-Adjusted SOPR: {e}")
            return self._unavailable_signal("Entity-Adjusted SOPR", "smart_money")
    
    async def _get_lth_sopr(self, asset: str) -> SignalResult:
        """
        Long-Term Holder SOPR (>155 days).
        LTH selling at loss is extremely rare and signals major bottoms.
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "sopr_lth")
            if data is None:
                return self._unavailable_signal("LTH-SOPR", "smart_money")
            
            sopr = data.get("value", 1.0)
            
            if sopr < 0.85:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"LTH capitulation - rare bottom signal (LTH-SOPR: {sopr:.3f})"
            elif sopr < 1.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"LTH selling at loss (LTH-SOPR: {sopr:.3f})"
            elif sopr < 1.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"LTH in profit (LTH-SOPR: {sopr:.3f})"
            elif sopr < 2.5:
                signal, score = SignalStrength.SELL, -1
                desc = f"LTH profit taking (LTH-SOPR: {sopr:.3f})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"LTH heavy distribution (LTH-SOPR: {sopr:.3f})"
            
            return SignalResult(
                name="LTH-SOPR",
                category="smart_money",
                value=sopr,
                signal=signal,
                score=score,
                weight=1.5,  # High weight - very reliable
                description=desc,
                details={"lth_sopr": sopr}
            )
        except Exception as e:
            logger.error(f"Error fetching LTH-SOPR: {e}")
            return self._unavailable_signal("LTH-SOPR", "smart_money")
    
    async def _get_sth_sopr(self, asset: str) -> SignalResult:
        """
        Short-Term Holder SOPR (<155 days).
        STH behavior indicates retail sentiment and near-term momentum.
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "sopr_sth")
            if data is None:
                return self._unavailable_signal("STH-SOPR", "smart_money")
            
            sopr = data.get("value", 1.0)
            
            if sopr < 0.90:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"STH panic selling (STH-SOPR: {sopr:.3f})"
            elif sopr < 0.98:
                signal, score = SignalStrength.BUY, 1
                desc = f"STH underwater (STH-SOPR: {sopr:.3f})"
            elif sopr < 1.02:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"STH break-even (STH-SOPR: {sopr:.3f})"
            elif sopr < 1.15:
                signal, score = SignalStrength.SELL, -1
                desc = f"STH taking profit (STH-SOPR: {sopr:.3f})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"STH euphoria (STH-SOPR: {sopr:.3f})"
            
            return SignalResult(
                name="STH-SOPR",
                category="smart_money",
                value=sopr,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"sth_sopr": sopr}
            )
        except Exception as e:
            logger.error(f"Error fetching STH-SOPR: {e}")
            return self._unavailable_signal("STH-SOPR", "smart_money")
    
    async def _get_realized_losses(self, asset: str) -> SignalResult:
        """
        Net Realized Losses - absolute USD value of losses being realized.
        Spikes in losses often mark local/macro bottoms.
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "realized_loss")
            if data is None:
                return self._unavailable_signal("Realized Losses", "smart_money")
            
            loss = data.get("value", 0)
            loss_30d_avg = data.get("avg_30d", 0) or 1  # Avoid division by zero
            
            ratio = loss / loss_30d_avg
            
            if ratio > 5.0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Extreme loss realization ({ratio:.1f}x avg) - capitulation"
            elif ratio > 2.0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Elevated losses ({ratio:.1f}x avg)"
            elif ratio > 0.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal loss levels ({ratio:.1f}x avg)"
            elif ratio > 0.2:
                signal, score = SignalStrength.SELL, -1
                desc = f"Low losses - complacency ({ratio:.1f}x avg)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very low losses - potential top ({ratio:.1f}x avg)"
            
            return SignalResult(
                name="Realized Losses",
                category="smart_money",
                value=ratio,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={"loss_usd": loss, "ratio_to_avg": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching Realized Losses: {e}")
            return self._unavailable_signal("Realized Losses", "smart_money")
    
    async def _get_exchange_whale_ratio(self, asset: str) -> SignalResult:
        """
        Exchange Whale Ratio - ratio of top 10 inflows to total inflows.
        High ratio = whales depositing to sell.
        """
        try:
            data = await self._fetch_cryptoquant_metric(asset, "exchange_whale_ratio")
            if data is None:
                return self._unavailable_signal("Exchange Whale Ratio", "smart_money")
            
            ratio = data.get("value", 0.5)
            
            if ratio < 0.30:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Low whale selling pressure ({ratio:.1%})"
            elif ratio < 0.45:
                signal, score = SignalStrength.BUY, 1
                desc = f"Below average whale activity ({ratio:.1%})"
            elif ratio < 0.60:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal whale activity ({ratio:.1%})"
            elif ratio < 0.75:
                signal, score = SignalStrength.SELL, -1
                desc = f"Elevated whale deposits ({ratio:.1%})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"High whale selling pressure ({ratio:.1%})"
            
            return SignalResult(
                name="Exchange Whale Ratio",
                category="smart_money",
                value=ratio,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={"whale_ratio": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching Exchange Whale Ratio: {e}")
            return self._unavailable_signal("Exchange Whale Ratio", "smart_money")
    
    async def _get_accumulation_trend_score(self, asset: str) -> SignalResult:
        """
        Accumulation Trend Score (0-1).
        Measures net accumulation/distribution across all cohorts.
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "accumulation_trend_score")
            if data is None:
                return self._unavailable_signal("Accumulation Trend", "smart_money")
            
            score_val = data.get("value", 0.5)
            
            if score_val > 0.9:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Strong accumulation across all cohorts ({score_val:.2f})"
            elif score_val > 0.7:
                signal, score = SignalStrength.BUY, 1
                desc = f"Accumulation trend ({score_val:.2f})"
            elif score_val > 0.3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Mixed accumulation/distribution ({score_val:.2f})"
            elif score_val > 0.1:
                signal, score = SignalStrength.SELL, -1
                desc = f"Distribution trend ({score_val:.2f})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Strong distribution ({score_val:.2f})"
            
            return SignalResult(
                name="Accumulation Trend",
                category="smart_money",
                value=score_val,
                signal=signal,
                score=score,
                weight=1.4,
                description=desc,
                details={"accumulation_score": score_val}
            )
        except Exception as e:
            logger.error(f"Error fetching Accumulation Trend: {e}")
            return self._unavailable_signal("Accumulation Trend", "smart_money")
    
    async def _get_dormancy_flow(self, asset: str) -> SignalResult:
        """
        Dormancy Flow - ratio of market cap to annualized dormancy.
        Low values indicate old coins not moving (accumulation).
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "dormancy_flow")
            if data is None:
                return self._unavailable_signal("Dormancy Flow", "smart_money")
            
            dormancy = data.get("value", 1000000)
            
            if dormancy < 200000:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Very low dormancy - strong accumulation zone"
            elif dormancy < 500000:
                signal, score = SignalStrength.BUY, 1
                desc = f"Low dormancy - accumulation"
            elif dormancy < 1500000:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal dormancy levels"
            elif dormancy < 3000000:
                signal, score = SignalStrength.SELL, -1
                desc = f"Elevated dormancy - old coins moving"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"High dormancy - significant distribution"
            
            return SignalResult(
                name="Dormancy Flow",
                category="smart_money",
                value=dormancy,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                details={"dormancy_flow": dormancy}
            )
        except Exception as e:
            logger.error(f"Error fetching Dormancy Flow: {e}")
            return self._unavailable_signal("Dormancy Flow", "smart_money")
    
    async def _get_supply_in_profit(self, asset: str) -> SignalResult:
        """
        Percentage of circulating supply in profit.
        < 50%: Strong buy zone (most holders underwater)
        > 95%: Euphoria / potential top
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "supply_profit_percent")
            if data is None:
                return self._unavailable_signal("Supply in Profit", "smart_money")
            
            pct = data.get("value", 0.5) * 100  # Convert to percentage
            
            if pct < 40:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Only {pct:.1f}% in profit - deep value zone"
            elif pct < 55:
                signal, score = SignalStrength.BUY, 1
                desc = f"{pct:.1f}% in profit - accumulation zone"
            elif pct < 80:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"{pct:.1f}% in profit - healthy range"
            elif pct < 95:
                signal, score = SignalStrength.SELL, -1
                desc = f"{pct:.1f}% in profit - elevated"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"{pct:.1f}% in profit - euphoria zone"
            
            return SignalResult(
                name="Supply in Profit",
                category="smart_money",
                value=pct,
                signal=signal,
                score=score,
                weight=1.3,
                description=desc,
                details={"percent_in_profit": pct}
            )
        except Exception as e:
            logger.error(f"Error fetching Supply in Profit: {e}")
            return self._unavailable_signal("Supply in Profit", "smart_money")
    
    async def _get_liveliness(self, asset: str) -> SignalResult:
        """
        Liveliness - ratio of Coin Days Destroyed to Coin Days Created.
        Low = HODLing (accumulation), High = spending (distribution).
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "liveliness")
            if data is None:
                return self._unavailable_signal("Liveliness", "smart_money")
            
            liveliness = data.get("value", 0.5)
            
            if liveliness < 0.55:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Low liveliness ({liveliness:.3f}) - strong HODLing"
            elif liveliness < 0.60:
                signal, score = SignalStrength.BUY, 1
                desc = f"Below avg liveliness ({liveliness:.3f}) - accumulation"
            elif liveliness < 0.65:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal liveliness ({liveliness:.3f})"
            elif liveliness < 0.70:
                signal, score = SignalStrength.SELL, -1
                desc = f"Elevated liveliness ({liveliness:.3f}) - spending"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"High liveliness ({liveliness:.3f}) - heavy spending"
            
            return SignalResult(
                name="Liveliness",
                category="smart_money",
                value=liveliness,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"liveliness": liveliness}
            )
        except Exception as e:
            logger.error(f"Error fetching Liveliness: {e}")
            return self._unavailable_signal("Liveliness", "smart_money")
    
    async def _get_asol(self, asset: str) -> SignalResult:
        """
        Average Spent Output Lifespan - avg age of coins being spent.
        High = old coins moving (distribution), Low = recent coins moving.
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "asol")
            if data is None:
                return self._unavailable_signal("ASOL", "smart_money")
            
            asol_days = data.get("value", 100)
            
            if asol_days < 30:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Very young coins moving ({asol_days:.0f} days) - accumulation"
            elif asol_days < 60:
                signal, score = SignalStrength.BUY, 1
                desc = f"Young coins moving ({asol_days:.0f} days)"
            elif asol_days < 120:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal ASOL ({asol_days:.0f} days)"
            elif asol_days < 200:
                signal, score = SignalStrength.SELL, -1
                desc = f"Older coins moving ({asol_days:.0f} days)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very old coins moving ({asol_days:.0f} days) - distribution"
            
            return SignalResult(
                name="ASOL",
                category="smart_money",
                value=asol_days,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"asol_days": asol_days}
            )
        except Exception as e:
            logger.error(f"Error fetching ASOL: {e}")
            return self._unavailable_signal("ASOL", "smart_money")
    
    async def _get_binary_cdd(self, asset: str) -> SignalResult:
        """
        Binary CDD - number of days in past 7 where CDD exceeded median.
        High = distribution period, Low = accumulation.
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "cdd_binary")
            if data is None:
                return self._unavailable_signal("Binary CDD", "smart_money")
            
            days_above = data.get("value", 3.5)  # 0-7
            
            if days_above < 1:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Very low CDD ({days_above:.0f}/7 days) - accumulation"
            elif days_above < 2.5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Low CDD ({days_above:.0f}/7 days)"
            elif days_above < 4.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal CDD ({days_above:.0f}/7 days)"
            elif days_above < 6:
                signal, score = SignalStrength.SELL, -1
                desc = f"High CDD ({days_above:.0f}/7 days) - distribution"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very high CDD ({days_above:.0f}/7 days) - heavy distribution"
            
            return SignalResult(
                name="Binary CDD",
                category="smart_money",
                value=days_above,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"days_above_median": days_above}
            )
        except Exception as e:
            logger.error(f"Error fetching Binary CDD: {e}")
            return self._unavailable_signal("Binary CDD", "smart_money")
    
    async def _get_lth_supply(self, asset: str) -> SignalResult:
        """
        Long-Term Holder Supply - % held by addresses >155 days.
        Rising LTH supply = accumulation phase.
        """
        try:
            data = await self._fetch_glassnode_metric(asset, "lth_supply_percent")
            if data is None:
                return self._unavailable_signal("LTH Supply", "smart_money")
            
            pct = data.get("value", 0.6) * 100
            change_30d = data.get("change_30d", 0) * 100
            
            # Both absolute level and trend matter
            if pct > 75 and change_30d > 1:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"LTH supply {pct:.1f}% and rising (+{change_30d:.1f}%)"
            elif pct > 70 or change_30d > 0.5:
                signal, score = SignalStrength.BUY, 1
                desc = f"LTH supply {pct:.1f}% (30d: {change_30d:+.1f}%)"
            elif pct > 60:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"LTH supply {pct:.1f}% (30d: {change_30d:+.1f}%)"
            elif change_30d < -1:
                signal, score = SignalStrength.SELL, -1
                desc = f"LTH supply declining ({pct:.1f}%, 30d: {change_30d:.1f}%)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Low/declining LTH supply ({pct:.1f}%) - distribution"
            
            return SignalResult(
                name="LTH Supply",
                category="smart_money",
                value=pct,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={"lth_percent": pct, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching LTH Supply: {e}")
            return self._unavailable_signal("LTH Supply", "smart_money")
    
    # =========================================================================
    # CATEGORY 10: DEFI / ALTCOIN SPECIFIC
    # =========================================================================
    
    async def _get_eth_gas(self) -> SignalResult:
        """
        ETH Gas (Gwei) - network congestion indicator.
        Very high gas = heavy usage (often peaks at tops).
        Very low gas = low activity (accumulation periods).
        """
        try:
            session = await self._get_session()
            async with session.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle") as resp:
                if resp.status != 200:
                    return self._unavailable_signal("ETH Gas", "defi_altcoin")
                data = await resp.json()
            
            if data.get("status") != "1":
                return self._unavailable_signal("ETH Gas", "defi_altcoin")
            
            result = data.get("result", {})
            gas = float(result.get("ProposeGasPrice", 30))
            
            if gas < 10:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Very low gas ({gas:.0f} gwei) - quiet accumulation"
            elif gas < 25:
                signal, score = SignalStrength.BUY, 1
                desc = f"Low gas ({gas:.0f} gwei)"
            elif gas < 60:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal gas ({gas:.0f} gwei)"
            elif gas < 150:
                signal, score = SignalStrength.SELL, -1
                desc = f"High gas ({gas:.0f} gwei) - heavy activity"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very high gas ({gas:.0f} gwei) - euphoria/panic"
            
            return SignalResult(
                name="ETH Gas",
                category="defi_altcoin",
                value=gas,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"gas_gwei": gas}
            )
        except Exception as e:
            logger.error(f"Error fetching ETH Gas: {e}")
            return self._unavailable_signal("ETH Gas", "defi_altcoin")
    
    async def _get_eth_burn_rate(self) -> SignalResult:
        """
        ETH Burn Rate (post-EIP1559).
        High burn = high usage/demand, low burn = quiet period.
        """
        try:
            data = await self._fetch_ultrasound_money_data()
            if data is None:
                return self._unavailable_signal("ETH Burn Rate", "defi_altcoin")
            
            burn_24h = data.get("burn_24h", 0)
            avg_burn = data.get("avg_30d_burn", 1) or 1
            
            ratio = burn_24h / avg_burn
            
            if ratio < 0.4:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Very low burn ({ratio:.2f}x avg) - quiet accumulation"
            elif ratio < 0.7:
                signal, score = SignalStrength.BUY, 1
                desc = f"Below avg burn ({ratio:.2f}x avg)"
            elif ratio < 1.3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal burn ({ratio:.2f}x avg)"
            elif ratio < 2.0:
                signal, score = SignalStrength.SELL, -1
                desc = f"High burn ({ratio:.2f}x avg) - elevated activity"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very high burn ({ratio:.2f}x avg) - peak activity"
            
            return SignalResult(
                name="ETH Burn Rate",
                category="defi_altcoin",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"burn_24h_eth": burn_24h, "ratio_to_avg": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching ETH Burn Rate: {e}")
            return self._unavailable_signal("ETH Burn Rate", "defi_altcoin")
    
    async def _get_eth_staking_ratio(self) -> SignalResult:
        """
        ETH Staking Ratio - % of supply staked.
        Rising staking = bullish long-term sentiment.
        """
        try:
            data = await self._fetch_beaconchain_data()
            if data is None:
                return self._unavailable_signal("ETH Staking Ratio", "defi_altcoin")
            
            staking_pct = data.get("staking_percent", 25)
            change_30d = data.get("change_30d", 0)
            
            if staking_pct > 30 and change_30d > 0.5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"{staking_pct:.1f}% staked, rising - strong conviction"
            elif staking_pct > 25 or change_30d > 0:
                signal, score = SignalStrength.BUY, 1
                desc = f"{staking_pct:.1f}% staked (30d: {change_30d:+.1f}%)"
            elif staking_pct > 20:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"{staking_pct:.1f}% staked (30d: {change_30d:+.1f}%)"
            elif change_30d < -0.5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Staking declining ({staking_pct:.1f}%, 30d: {change_30d:.1f}%)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Low staking ({staking_pct:.1f}%) - weak conviction"
            
            return SignalResult(
                name="ETH Staking Ratio",
                category="defi_altcoin",
                value=staking_pct,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"staking_percent": staking_pct, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching ETH Staking Ratio: {e}")
            return self._unavailable_signal("ETH Staking Ratio", "defi_altcoin")
    
    async def _get_l2_tvl(self) -> SignalResult:
        """
        L2 TVL (Arbitrum, Optimism, Base, etc.).
        Growing L2 TVL = ecosystem health, declining = risk-off.
        """
        try:
            data = await self._fetch_l2beat_data()
            if data is None:
                return self._unavailable_signal("L2 TVL", "defi_altcoin")
            
            tvl_usd = data.get("total_tvl_usd", 0)
            change_7d = data.get("change_7d_percent", 0)
            change_30d = data.get("change_30d_percent", 0)
            
            if change_30d > 20:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"L2 TVL surging +{change_30d:.1f}% (30d) - strong adoption"
            elif change_30d > 5:
                signal, score = SignalStrength.BUY, 1
                desc = f"L2 TVL growing +{change_30d:.1f}% (30d)"
            elif change_30d > -5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"L2 TVL stable ({change_30d:+.1f}% 30d)"
            elif change_30d > -15:
                signal, score = SignalStrength.SELL, -1
                desc = f"L2 TVL declining {change_30d:.1f}% (30d)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"L2 TVL dropping {change_30d:.1f}% (30d) - risk-off"
            
            return SignalResult(
                name="L2 TVL",
                category="defi_altcoin",
                value=tvl_usd,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"tvl_usd": tvl_usd, "change_7d": change_7d, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching L2 TVL: {e}")
            return self._unavailable_signal("L2 TVL", "defi_altcoin")
    
    async def _get_dex_cex_ratio(self) -> SignalResult:
        """
        DEX vs CEX Volume Ratio.
        Rising DEX share = decentralization trend, often bullish.
        """
        try:
            data = await self._fetch_the_block_data("dex_cex_ratio")
            if data is None:
                return self._unavailable_signal("DEX/CEX Ratio", "defi_altcoin")
            
            ratio = data.get("value", 0.15)  # Typically 10-20%
            change_30d = data.get("change_30d", 0)
            
            if ratio > 0.25 and change_30d > 0.02:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"DEX share {ratio:.1%}, rising - DeFi thriving"
            elif ratio > 0.18 or change_30d > 0.01:
                signal, score = SignalStrength.BUY, 1
                desc = f"DEX share {ratio:.1%} (30d: {change_30d:+.1%})"
            elif ratio > 0.10:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"DEX share {ratio:.1%} - normal range"
            elif change_30d < -0.02:
                signal, score = SignalStrength.SELL, -1
                desc = f"DEX share falling ({ratio:.1%}, 30d: {change_30d:.1%})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Low DEX activity ({ratio:.1%}) - DeFi quiet"
            
            return SignalResult(
                name="DEX/CEX Ratio",
                category="defi_altcoin",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"dex_cex_ratio": ratio, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching DEX/CEX Ratio: {e}")
            return self._unavailable_signal("DEX/CEX Ratio", "defi_altcoin")
    
    async def _get_altcoin_season_index(self) -> SignalResult:
        """
        Altcoin Season Index (0-100).
        > 75 = Altcoin season, < 25 = Bitcoin season.
        """
        try:
            session = await self._get_session()
            async with session.get("https://api.blockchaincenter.net/api/altcoin-season-index") as resp:
                if resp.status != 200:
                    return self._unavailable_signal("Altcoin Season", "defi_altcoin")
                data = await resp.json()
            
            index = data.get("index", 50)
            
            # For BTC-focused portfolio, altcoin season is actually a caution sign
            if index < 20:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Bitcoin season ({index}) - BTC outperforming"
            elif index < 40:
                signal, score = SignalStrength.BUY, 1
                desc = f"BTC-leaning ({index})"
            elif index < 60:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Neutral ({index})"
            elif index < 80:
                signal, score = SignalStrength.SELL, -1
                desc = f"Altcoin-leaning ({index}) - rotation from BTC"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Altcoin season ({index}) - late cycle euphoria"
            
            return SignalResult(
                name="Altcoin Season",
                category="defi_altcoin",
                value=index,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"altcoin_index": index}
            )
        except Exception as e:
            logger.error(f"Error fetching Altcoin Season Index: {e}")
            return self._unavailable_signal("Altcoin Season", "defi_altcoin")
    
    async def _get_btc_dominance(self) -> SignalResult:
        """
        BTC Dominance %.
        Rising dominance in downtrends = flight to quality (bullish for BTC).
        """
        try:
            session = await self._get_session()
            async with session.get("https://api.coingecko.com/api/v3/global") as resp:
                if resp.status != 200:
                    return self._unavailable_signal("BTC Dominance", "defi_altcoin")
                data = await resp.json()
            
            dom = data.get("data", {}).get("market_cap_percentage", {}).get("btc", 50)
            
            # Historical context: 40-70% range
            if dom > 60:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"High BTC dominance ({dom:.1f}%) - safety preference"
            elif dom > 52:
                signal, score = SignalStrength.BUY, 1
                desc = f"Above-avg BTC dominance ({dom:.1f}%)"
            elif dom > 42:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal BTC dominance ({dom:.1f}%)"
            elif dom > 35:
                signal, score = SignalStrength.SELL, -1
                desc = f"Low BTC dominance ({dom:.1f}%) - alt rotation"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very low BTC dominance ({dom:.1f}%) - alt mania"
            
            return SignalResult(
                name="BTC Dominance",
                category="defi_altcoin",
                value=dom,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"btc_dominance": dom}
            )
        except Exception as e:
            logger.error(f"Error fetching BTC Dominance: {e}")
            return self._unavailable_signal("BTC Dominance", "defi_altcoin")
    
    async def _get_eth_btc_ratio(self) -> SignalResult:
        """
        ETH/BTC Ratio.
        Trend indicates relative strength and cycle positioning.
        """
        try:
            session = await self._get_session()
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=btc"
            ) as resp:
                if resp.status != 200:
                    return self._unavailable_signal("ETH/BTC", "defi_altcoin")
                data = await resp.json()
            
            ratio = data.get("ethereum", {}).get("btc", 0.05)
            
            # Historical range: 0.02 - 0.08
            if ratio < 0.03:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"ETH/BTC very low ({ratio:.4f}) - ETH value zone"
            elif ratio < 0.045:
                signal, score = SignalStrength.BUY, 1
                desc = f"ETH/BTC below avg ({ratio:.4f})"
            elif ratio < 0.065:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"ETH/BTC normal ({ratio:.4f})"
            elif ratio < 0.08:
                signal, score = SignalStrength.SELL, -1
                desc = f"ETH/BTC elevated ({ratio:.4f})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"ETH/BTC very high ({ratio:.4f}) - ETH extended"
            
            return SignalResult(
                name="ETH/BTC",
                category="defi_altcoin",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"eth_btc_ratio": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching ETH/BTC: {e}")
            return self._unavailable_signal("ETH/BTC", "defi_altcoin")
    
    async def _get_stablecoin_mcap(self) -> SignalResult:
        """
        Total Stablecoin Market Cap.
        Growing = dry powder entering, shrinking = capital exiting.
        """
        try:
            data = await self._fetch_defi_llama_stablecoins()
            if data is None:
                return self._unavailable_signal("Stablecoin MCap", "defi_altcoin")
            
            mcap = data.get("total_mcap_usd", 0) / 1e9  # In billions
            change_30d = data.get("change_30d_percent", 0)
            
            if change_30d > 5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Stablecoin supply surging +{change_30d:.1f}% - capital entering"
            elif change_30d > 1:
                signal, score = SignalStrength.BUY, 1
                desc = f"Stablecoin supply growing +{change_30d:.1f}%"
            elif change_30d > -1:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Stablecoin supply stable ({change_30d:+.1f}%)"
            elif change_30d > -5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Stablecoin supply declining {change_30d:.1f}%"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Stablecoin supply dropping {change_30d:.1f}% - capital exiting"
            
            return SignalResult(
                name="Stablecoin MCap",
                category="defi_altcoin",
                value=mcap,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"mcap_billions": mcap, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching Stablecoin MCap: {e}")
            return self._unavailable_signal("Stablecoin MCap", "defi_altcoin")
    
    async def _get_usdt_dominance(self) -> SignalResult:
        """
        USDT Dominance among stablecoins.
        Flight to Tether during uncertainty vs diversified stables in calm.
        """
        try:
            data = await self._fetch_defi_llama_stablecoins()
            if data is None:
                return self._unavailable_signal("USDT Dominance", "defi_altcoin")
            
            dom = data.get("usdt_dominance", 0.65) * 100
            
            # High USDT dominance can indicate risk-off
            if dom > 75:
                signal, score = SignalStrength.BUY, 1
                desc = f"High USDT dominance ({dom:.1f}%) - flight to safety"
            elif dom > 65:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal USDT dominance ({dom:.1f}%)"
            elif dom > 55:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Diversified stables ({dom:.1f}%) - confidence"
            else:
                signal, score = SignalStrength.SELL, -1
                desc = f"Low USDT dominance ({dom:.1f}%) - could signal risk"
            
            return SignalResult(
                name="USDT Dominance",
                category="defi_altcoin",
                value=dom,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"usdt_dominance": dom}
            )
        except Exception as e:
            logger.error(f"Error fetching USDT Dominance: {e}")
            return self._unavailable_signal("USDT Dominance", "defi_altcoin")
    
    async def _get_real_yield(self) -> SignalResult:
        """
        DeFi Real Yield - sustainable yields from actual protocol revenue.
        """
        try:
            data = await self._fetch_defi_llama_yields()
            if data is None:
                return self._unavailable_signal("Real Yield", "defi_altcoin")
            
            avg_yield = data.get("median_real_yield", 5)
            
            if avg_yield > 10:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"High real yields ({avg_yield:.1f}%) - attractive DeFi"
            elif avg_yield > 6:
                signal, score = SignalStrength.BUY, 1
                desc = f"Good real yields ({avg_yield:.1f}%)"
            elif avg_yield > 3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal real yields ({avg_yield:.1f}%)"
            elif avg_yield > 1:
                signal, score = SignalStrength.SELL, -1
                desc = f"Low real yields ({avg_yield:.1f}%)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very low/negative yields ({avg_yield:.1f}%)"
            
            return SignalResult(
                name="Real Yield",
                category="defi_altcoin",
                value=avg_yield,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"median_yield": avg_yield}
            )
        except Exception as e:
            logger.error(f"Error fetching Real Yield: {e}")
            return self._unavailable_signal("Real Yield", "defi_altcoin")
    
    async def _get_lending_utilization(self) -> SignalResult:
        """
        Lending Protocol Utilization Rate (Aave, Compound).
        High utilization = high demand for leverage.
        """
        try:
            data = await self._fetch_aave_data()
            if data is None:
                return self._unavailable_signal("Lending Utilization", "defi_altcoin")
            
            util = data.get("avg_utilization", 0.5) * 100
            
            if util < 30:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Low lending utilization ({util:.1f}%) - delevering complete"
            elif util < 50:
                signal, score = SignalStrength.BUY, 1
                desc = f"Below-avg utilization ({util:.1f}%)"
            elif util < 70:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal utilization ({util:.1f}%)"
            elif util < 85:
                signal, score = SignalStrength.SELL, -1
                desc = f"High utilization ({util:.1f}%) - elevated leverage"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very high utilization ({util:.1f}%) - max leverage"
            
            return SignalResult(
                name="Lending Utilization",
                category="defi_altcoin",
                value=util,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"utilization_percent": util}
            )
        except Exception as e:
            logger.error(f"Error fetching Lending Utilization: {e}")
            return self._unavailable_signal("Lending Utilization", "defi_altcoin")
    
    # =========================================================================
    # CATEGORY 11: ORDER FLOW / MICROSTRUCTURE
    # =========================================================================
    
    async def _get_bid_ask_spread(self, asset: str) -> SignalResult:
        """
        Bid-Ask Spread on top exchanges.
        Wide spreads = uncertainty/thin liquidity.
        """
        try:
            data = await self._fetch_kaiko_data(asset, "spread")
            if data is None:
                return self._unavailable_signal("Bid-Ask Spread", "order_flow")
            
            spread_bps = data.get("spread_bps", 5)
            
            if spread_bps < 2:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Tight spreads ({spread_bps:.1f} bps) - healthy liquidity"
            elif spread_bps < 5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Normal spreads ({spread_bps:.1f} bps)"
            elif spread_bps < 10:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Slightly wide spreads ({spread_bps:.1f} bps)"
            elif spread_bps < 20:
                signal, score = SignalStrength.SELL, -1
                desc = f"Wide spreads ({spread_bps:.1f} bps) - thin liquidity"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very wide spreads ({spread_bps:.1f} bps) - low confidence"
            
            return SignalResult(
                name="Bid-Ask Spread",
                category="order_flow",
                value=spread_bps,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"spread_bps": spread_bps}
            )
        except Exception as e:
            logger.error(f"Error fetching Bid-Ask Spread: {e}")
            return self._unavailable_signal("Bid-Ask Spread", "order_flow")
    
    async def _get_order_book_depth(self, asset: str) -> SignalResult:
        """
        Order Book Depth (2% from mid price).
        Deep books = strong support, shallow = vulnerability.
        """
        try:
            data = await self._fetch_kaiko_data(asset, "depth")
            if data is None:
                return self._unavailable_signal("Order Depth", "order_flow")
            
            depth_usd = data.get("depth_2pct_usd", 0) / 1e6  # In millions
            avg_depth = data.get("avg_30d_depth", 0) / 1e6 or 1
            
            ratio = depth_usd / avg_depth
            
            if ratio > 1.5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Deep order books ({depth_usd:.1f}M, {ratio:.1f}x avg)"
            elif ratio > 1.1:
                signal, score = SignalStrength.BUY, 1
                desc = f"Above-avg depth ({depth_usd:.1f}M)"
            elif ratio > 0.8:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal depth ({depth_usd:.1f}M)"
            elif ratio > 0.5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Thin order books ({depth_usd:.1f}M, {ratio:.1f}x avg)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very thin books ({depth_usd:.1f}M) - vulnerable to moves"
            
            return SignalResult(
                name="Order Depth",
                category="order_flow",
                value=depth_usd,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"depth_millions": depth_usd, "ratio_to_avg": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching Order Depth: {e}")
            return self._unavailable_signal("Order Depth", "order_flow")
    
    async def _get_whale_order_flow(self, asset: str) -> SignalResult:
        """
        Whale Order Flow - net direction of >$100k trades.
        """
        try:
            data = await self._fetch_whale_alert_data(asset)
            if data is None:
                return self._unavailable_signal("Whale Order Flow", "order_flow")
            
            net_flow = data.get("net_flow_24h_usd", 0) / 1e6  # In millions
            buy_pct = data.get("buy_percent", 0.5)
            
            if buy_pct > 0.65:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Whales buying ({buy_pct:.0%}), net +${abs(net_flow):.1f}M"
            elif buy_pct > 0.55:
                signal, score = SignalStrength.BUY, 1
                desc = f"Slight whale buying ({buy_pct:.0%})"
            elif buy_pct > 0.45:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Balanced whale flow ({buy_pct:.0%})"
            elif buy_pct > 0.35:
                signal, score = SignalStrength.SELL, -1
                desc = f"Slight whale selling ({buy_pct:.0%})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Whales selling ({buy_pct:.0%}), net -${abs(net_flow):.1f}M"
            
            return SignalResult(
                name="Whale Order Flow",
                category="order_flow",
                value=buy_pct,
                signal=signal,
                score=score,
                weight=1.2,
                description=desc,
                details={"buy_percent": buy_pct, "net_flow_millions": net_flow}
            )
        except Exception as e:
            logger.error(f"Error fetching Whale Order Flow: {e}")
            return self._unavailable_signal("Whale Order Flow", "order_flow")
    
    async def _get_spot_deriv_volume(self, asset: str) -> SignalResult:
        """
        Spot vs Derivatives Volume Ratio.
        High deriv ratio = speculation, low = organic demand.
        """
        try:
            data = await self._fetch_coinglass_data(asset, "spot_deriv_ratio")
            if data is None:
                return self._unavailable_signal("Spot/Deriv Volume", "order_flow")
            
            spot_pct = data.get("spot_percent", 0.3) * 100
            
            if spot_pct > 50:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"High spot volume ({spot_pct:.0f}%) - organic demand"
            elif spot_pct > 35:
                signal, score = SignalStrength.BUY, 1
                desc = f"Above-avg spot ({spot_pct:.0f}%)"
            elif spot_pct > 20:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal spot ratio ({spot_pct:.0f}%)"
            elif spot_pct > 10:
                signal, score = SignalStrength.SELL, -1
                desc = f"Low spot ratio ({spot_pct:.0f}%) - speculative"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very low spot ({spot_pct:.0f}%) - pure speculation"
            
            return SignalResult(
                name="Spot/Deriv Volume",
                category="order_flow",
                value=spot_pct,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"spot_percent": spot_pct}
            )
        except Exception as e:
            logger.error(f"Error fetching Spot/Deriv Volume: {e}")
            return self._unavailable_signal("Spot/Deriv Volume", "order_flow")
    
    async def _get_cvd(self, asset: str) -> SignalResult:
        """
        Cumulative Volume Delta (CVD) - net buy vs sell pressure.
        Positive CVD = net buying, negative = net selling.
        """
        try:
            data = await self._fetch_coinglass_data(asset, "cvd")
            if data is None:
                return self._unavailable_signal("CVD", "order_flow")
            
            cvd_24h = data.get("cvd_24h", 0) / 1e6  # In millions
            cvd_trend = data.get("cvd_7d_trend", 0)  # Slope direction
            
            if cvd_24h > 50 and cvd_trend > 0:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Strong buying pressure (CVD: +${cvd_24h:.0f}M, rising)"
            elif cvd_24h > 10:
                signal, score = SignalStrength.BUY, 1
                desc = f"Net buying (CVD: +${cvd_24h:.0f}M)"
            elif cvd_24h > -10:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Balanced flow (CVD: ${cvd_24h:+.0f}M)"
            elif cvd_24h > -50:
                signal, score = SignalStrength.SELL, -1
                desc = f"Net selling (CVD: ${cvd_24h:.0f}M)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Heavy selling pressure (CVD: ${cvd_24h:.0f}M)"
            
            return SignalResult(
                name="CVD",
                category="order_flow",
                value=cvd_24h,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                details={"cvd_24h_millions": cvd_24h, "trend": cvd_trend}
            )
        except Exception as e:
            logger.error(f"Error fetching CVD: {e}")
            return self._unavailable_signal("CVD", "order_flow")
    
    async def _get_taker_ratio(self, asset: str) -> SignalResult:
        """
        Taker Buy/Sell Ratio.
        > 1 = aggressive buying, < 1 = aggressive selling.
        """
        try:
            data = await self._fetch_coinglass_data(asset, "taker_ratio")
            if data is None:
                return self._unavailable_signal("Taker Ratio", "order_flow")
            
            ratio = data.get("ratio", 1.0)
            
            if ratio > 1.3:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Strong taker buying ({ratio:.2f})"
            elif ratio > 1.1:
                signal, score = SignalStrength.BUY, 1
                desc = f"Taker buying ({ratio:.2f})"
            elif ratio > 0.9:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Balanced taker activity ({ratio:.2f})"
            elif ratio > 0.7:
                signal, score = SignalStrength.SELL, -1
                desc = f"Taker selling ({ratio:.2f})"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Strong taker selling ({ratio:.2f})"
            
            return SignalResult(
                name="Taker Ratio",
                category="order_flow",
                value=ratio,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"taker_buy_sell_ratio": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching Taker Ratio: {e}")
            return self._unavailable_signal("Taker Ratio", "order_flow")
    
    async def _get_large_trade_intensity(self, asset: str) -> SignalResult:
        """
        Large Trade Intensity - frequency of >$1M trades.
        """
        try:
            data = await self._fetch_kaiko_data(asset, "large_trades")
            if data is None:
                return self._unavailable_signal("Large Trade Intensity", "order_flow")
            
            count_24h = data.get("large_trade_count_24h", 0)
            avg_count = data.get("avg_30d_count", 1) or 1
            
            ratio = count_24h / avg_count
            
            if ratio > 2.0:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Very high large trade activity ({ratio:.1f}x avg) - volatility"
            elif ratio > 1.3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Elevated large trades ({ratio:.1f}x avg)"
            elif ratio > 0.7:
                signal, score = SignalStrength.BUY, 1
                desc = f"Normal institutional activity ({ratio:.1f}x avg)"
            elif ratio > 0.3:
                signal, score = SignalStrength.BUY, 1
                desc = f"Quiet institutional ({ratio:.1f}x avg) - accumulation?"
            else:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Very quiet ({ratio:.1f}x avg) - stealth accumulation"
            
            return SignalResult(
                name="Large Trade Intensity",
                category="order_flow",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"count_24h": count_24h, "ratio_to_avg": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching Large Trade Intensity: {e}")
            return self._unavailable_signal("Large Trade Intensity", "order_flow")
    
    async def _get_slippage_estimate(self, asset: str) -> SignalResult:
        """
        Slippage Estimate for $1M market order.
        """
        try:
            data = await self._fetch_kaiko_data(asset, "slippage")
            if data is None:
                return self._unavailable_signal("Slippage", "order_flow")
            
            slippage_bps = data.get("slippage_1m_bps", 20)
            
            if slippage_bps < 5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Excellent liquidity ({slippage_bps:.0f} bps slippage)"
            elif slippage_bps < 15:
                signal, score = SignalStrength.BUY, 1
                desc = f"Good liquidity ({slippage_bps:.0f} bps slippage)"
            elif slippage_bps < 30:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Normal liquidity ({slippage_bps:.0f} bps slippage)"
            elif slippage_bps < 50:
                signal, score = SignalStrength.SELL, -1
                desc = f"Thin liquidity ({slippage_bps:.0f} bps slippage)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Poor liquidity ({slippage_bps:.0f} bps slippage)"
            
            return SignalResult(
                name="Slippage",
                category="order_flow",
                value=slippage_bps,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"slippage_bps": slippage_bps}
            )
        except Exception as e:
            logger.error(f"Error fetching Slippage: {e}")
            return self._unavailable_signal("Slippage", "order_flow")
    
    # =========================================================================
    # CATEGORY 12: ECONOMIC CALENDAR
    # =========================================================================
    
    async def _get_fomc_signal(self) -> SignalResult:
        """
        FOMC Meeting proximity signal.
        Markets often volatile around FOMC - reduce position sizing.
        """
        try:
            # Known 2024-2025 FOMC meeting dates (update annually)
            fomc_dates = [
                date(2024, 1, 31), date(2024, 3, 20), date(2024, 5, 1),
                date(2024, 6, 12), date(2024, 7, 31), date(2024, 9, 18),
                date(2024, 11, 7), date(2024, 12, 18),
                date(2025, 1, 29), date(2025, 3, 19), date(2025, 5, 7),
                date(2025, 6, 18), date(2025, 7, 30), date(2025, 9, 17),
                date(2025, 11, 5), date(2025, 12, 17),
                date(2026, 1, 28), date(2026, 3, 18), date(2026, 5, 6),
            ]
            
            today = date.today()
            days_to_next = min((d - today).days for d in fomc_dates if d >= today)
            
            if days_to_next <= 1:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"FOMC today/tomorrow - expect volatility"
            elif days_to_next <= 3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"FOMC in {days_to_next} days - positioning period"
            elif days_to_next <= 7:
                signal, score = SignalStrength.BUY, 1
                desc = f"FOMC in {days_to_next} days - pre-positioning window"
            else:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"FOMC in {days_to_next} days - clear sailing"
            
            return SignalResult(
                name="FOMC Proximity",
                category="economic_calendar",
                value=days_to_next,
                signal=signal,
                score=score,
                weight=0.7,
                description=desc,
                details={"days_to_fomc": days_to_next}
            )
        except Exception as e:
            logger.error(f"Error calculating FOMC: {e}")
            return self._unavailable_signal("FOMC Proximity", "economic_calendar")
    
    async def _get_cpi_signal(self) -> SignalResult:
        """
        CPI Release proximity signal.
        """
        try:
            # CPI typically released 2nd week of month
            cpi_dates = [
                date(2024, 1, 11), date(2024, 2, 13), date(2024, 3, 12),
                date(2024, 4, 10), date(2024, 5, 15), date(2024, 6, 12),
                date(2024, 7, 11), date(2024, 8, 14), date(2024, 9, 11),
                date(2024, 10, 10), date(2024, 11, 13), date(2024, 12, 11),
                date(2025, 1, 15), date(2025, 2, 12), date(2025, 3, 12),
                date(2025, 4, 10), date(2025, 5, 13), date(2025, 6, 11),
                date(2025, 7, 10), date(2025, 8, 12), date(2025, 9, 10),
                date(2025, 10, 14), date(2025, 11, 12), date(2025, 12, 10),
                date(2026, 1, 13), date(2026, 2, 11), date(2026, 3, 11),
            ]
            
            today = date.today()
            future_dates = [d for d in cpi_dates if d >= today]
            if not future_dates:
                return self._unavailable_signal("CPI Proximity", "economic_calendar")
            
            days_to_next = (min(future_dates) - today).days
            
            if days_to_next <= 1:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"CPI release today/tomorrow"
            elif days_to_next <= 3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"CPI in {days_to_next} days"
            else:
                signal, score = SignalStrength.BUY, 1
                desc = f"CPI in {days_to_next} days - clear"
            
            return SignalResult(
                name="CPI Proximity",
                category="economic_calendar",
                value=days_to_next,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"days_to_cpi": days_to_next}
            )
        except Exception as e:
            logger.error(f"Error calculating CPI: {e}")
            return self._unavailable_signal("CPI Proximity", "economic_calendar")
    
    async def _get_nfp_signal(self) -> SignalResult:
        """
        Non-Farm Payrolls proximity signal (first Friday of month).
        """
        try:
            today = date.today()
            
            # Find first Friday of this month and next month
            def first_friday(year, month):
                first = date(year, month, 1)
                days_until_friday = (4 - first.weekday()) % 7
                return first + timedelta(days=days_until_friday)
            
            this_month_nfp = first_friday(today.year, today.month)
            if today.month == 12:
                next_month_nfp = first_friday(today.year + 1, 1)
            else:
                next_month_nfp = first_friday(today.year, today.month + 1)
            
            if today <= this_month_nfp:
                next_nfp = this_month_nfp
            else:
                next_nfp = next_month_nfp
            
            days_to_nfp = (next_nfp - today).days
            
            if days_to_nfp <= 1:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"NFP today/tomorrow"
            elif days_to_nfp <= 3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"NFP in {days_to_nfp} days"
            else:
                signal, score = SignalStrength.BUY, 1
                desc = f"NFP in {days_to_nfp} days - clear"
            
            return SignalResult(
                name="NFP Proximity",
                category="economic_calendar",
                value=days_to_nfp,
                signal=signal,
                score=score,
                weight=0.4,
                description=desc,
                details={"days_to_nfp": days_to_nfp}
            )
        except Exception as e:
            logger.error(f"Error calculating NFP: {e}")
            return self._unavailable_signal("NFP Proximity", "economic_calendar")
    
    async def _get_options_expiry_signal(self) -> SignalResult:
        """
        Options Expiry proximity signal.
        Monthly expiry (last Friday) and quarterly expiry dates.
        """
        try:
            today = date.today()
            
            # Find last Friday of month (monthly expiry)
            def last_friday(year, month):
                if month == 12:
                    next_month = date(year + 1, 1, 1)
                else:
                    next_month = date(year, month + 1, 1)
                last_day = next_month - timedelta(days=1)
                days_since_friday = (last_day.weekday() - 4) % 7
                return last_day - timedelta(days=days_since_friday)
            
            this_month_expiry = last_friday(today.year, today.month)
            if today > this_month_expiry:
                if today.month == 12:
                    next_expiry = last_friday(today.year + 1, 1)
                else:
                    next_expiry = last_friday(today.year, today.month + 1)
            else:
                next_expiry = this_month_expiry
            
            days_to_expiry = (next_expiry - today).days
            is_quarterly = next_expiry.month in [3, 6, 9, 12]
            
            if days_to_expiry <= 1:
                signal, score = SignalStrength.NEUTRAL, 0
                expiry_type = "QUARTERLY" if is_quarterly else "Monthly"
                desc = f"{expiry_type} options expiry today/tomorrow"
            elif days_to_expiry <= 3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Options expiry in {days_to_expiry} days"
            elif days_to_expiry <= 7 and is_quarterly:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Quarterly expiry in {days_to_expiry} days"
            else:
                signal, score = SignalStrength.BUY, 1
                desc = f"Options expiry in {days_to_expiry} days"
            
            return SignalResult(
                name="Options Expiry",
                category="economic_calendar",
                value=days_to_expiry,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"days_to_expiry": days_to_expiry, "is_quarterly": is_quarterly}
            )
        except Exception as e:
            logger.error(f"Error calculating Options Expiry: {e}")
            return self._unavailable_signal("Options Expiry", "economic_calendar")
    
    async def _get_cme_gap_signal(self, asset: str) -> SignalResult:
        """
        CME Gap analysis - weekend gaps often get filled.
        """
        try:
            data = await self._fetch_cme_data(asset)
            if data is None:
                return self._unavailable_signal("CME Gap", "economic_calendar")
            
            gap_pct = data.get("weekend_gap_percent", 0)
            gap_filled = data.get("gap_filled", True)
            
            if gap_filled or abs(gap_pct) < 0.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "No significant CME gap"
            elif gap_pct > 3:
                signal, score = SignalStrength.SELL, -1
                desc = f"Large upward CME gap ({gap_pct:.1f}%) - may fill"
            elif gap_pct > 1:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"CME gap up ({gap_pct:.1f}%)"
            elif gap_pct < -3:
                signal, score = SignalStrength.BUY, 1
                desc = f"Large downward CME gap ({gap_pct:.1f}%) - may fill up"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"CME gap down ({gap_pct:.1f}%)"
            
            return SignalResult(
                name="CME Gap",
                category="economic_calendar",
                value=gap_pct,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"gap_percent": gap_pct, "gap_filled": gap_filled}
            )
        except Exception as e:
            logger.error(f"Error fetching CME Gap: {e}")
            return self._unavailable_signal("CME Gap", "economic_calendar")
    
    async def _get_quarter_end_signal(self) -> SignalResult:
        """
        Quarter-end rebalancing signal.
        Institutional rebalancing at quarter end can cause volatility.
        """
        try:
            today = date.today()
            
            # Quarter end dates
            quarter_ends = [
                date(today.year, 3, 31),
                date(today.year, 6, 30),
                date(today.year, 9, 30),
                date(today.year, 12, 31),
            ]
            
            future_ends = [d for d in quarter_ends if d >= today]
            if not future_ends:
                future_ends = [date(today.year + 1, 3, 31)]
            
            days_to_qe = (min(future_ends) - today).days
            
            if days_to_qe <= 3:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Quarter-end in {days_to_qe} days - rebalancing period"
            elif days_to_qe <= 10:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Quarter-end approaching ({days_to_qe} days)"
            else:
                signal, score = SignalStrength.BUY, 1
                desc = f"Quarter-end in {days_to_qe} days"
            
            return SignalResult(
                name="Quarter End",
                category="economic_calendar",
                value=days_to_qe,
                signal=signal,
                score=score,
                weight=0.4,
                description=desc,
                details={"days_to_quarter_end": days_to_qe}
            )
        except Exception as e:
            logger.error(f"Error calculating Quarter End: {e}")
            return self._unavailable_signal("Quarter End", "economic_calendar")
    
    async def _get_tax_season_signal(self) -> SignalResult:
        """
        US Tax Season signal (January-April).
        Some selling pressure as people realize gains for taxes.
        """
        try:
            today = date.today()
            month = today.month
            day = today.day
            
            # Tax deadline April 15
            if month == 4 and day <= 15:
                signal, score = SignalStrength.SELL, -1
                desc = "Tax deadline approaching - potential selling"
            elif month == 4:
                signal, score = SignalStrength.BUY, 1
                desc = "Post-tax deadline - selling pressure eased"
            elif month in [1, 2, 3]:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = "Tax season - some selling pressure possible"
            else:
                signal, score = SignalStrength.BUY, 1
                desc = "Outside tax season"
            
            return SignalResult(
                name="Tax Season",
                category="economic_calendar",
                value=month,
                signal=signal,
                score=score,
                weight=0.3,
                description=desc,
                details={"month": month, "in_tax_season": month <= 4}
            )
        except Exception as e:
            logger.error(f"Error calculating Tax Season: {e}")
            return self._unavailable_signal("Tax Season", "economic_calendar")
    
    async def _get_halving_countdown(self, asset: str) -> SignalResult:
        """
        Bitcoin Halving countdown.
        Historically bullish 12-18 months after halving.
        """
        if asset.upper() != "BTC":
            return self._unavailable_signal("Halving Countdown", "economic_calendar")
        
        try:
            # April 2024 halving
            last_halving = date(2024, 4, 19)
            # Next halving ~2028
            next_halving = date(2028, 4, 15)  # Estimate
            
            today = date.today()
            days_since = (today - last_halving).days
            days_until = (next_halving - today).days
            
            months_since = days_since / 30
            
            if months_since < 6:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"{months_since:.0f}mo since halving - early bull phase"
            elif months_since < 18:
                signal, score = SignalStrength.BUY, 1
                desc = f"{months_since:.0f}mo since halving - bull phase"
            elif months_since < 30:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"{months_since:.0f}mo since halving - mid-cycle"
            elif months_since < 42:
                signal, score = SignalStrength.SELL, -1
                desc = f"{months_since:.0f}mo since halving - late cycle"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Approaching next halving ({days_until} days)"
            
            return SignalResult(
                name="Halving Countdown",
                category="economic_calendar",
                value=months_since,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"months_since_halving": months_since, "days_until_next": days_until}
            )
        except Exception as e:
            logger.error(f"Error calculating Halving Countdown: {e}")
            return self._unavailable_signal("Halving Countdown", "economic_calendar")
    
    # =========================================================================
    # CATEGORY 13: CROSS-CHAIN / MULTI-ASSET
    # =========================================================================
    
    async def _get_cross_exchange_arb(self, asset: str) -> SignalResult:
        """
        Cross-Exchange Arbitrage Spread.
        Large spreads = market inefficiency/stress.
        """
        try:
            data = await self._fetch_kaiko_data(asset, "exchange_spread")
            if data is None:
                return self._unavailable_signal("Cross-Exchange Arb", "cross_chain")
            
            spread_bps = data.get("max_spread_bps", 10)
            
            if spread_bps < 5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Tight cross-exchange spread ({spread_bps:.0f} bps) - efficient"
            elif spread_bps < 15:
                signal, score = SignalStrength.BUY, 1
                desc = f"Normal spread ({spread_bps:.0f} bps)"
            elif spread_bps < 30:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Elevated spread ({spread_bps:.0f} bps)"
            elif spread_bps < 50:
                signal, score = SignalStrength.SELL, -1
                desc = f"Wide spread ({spread_bps:.0f} bps) - stress"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Very wide spread ({spread_bps:.0f} bps) - market stress"
            
            return SignalResult(
                name="Cross-Exchange Arb",
                category="cross_chain",
                value=spread_bps,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"spread_bps": spread_bps}
            )
        except Exception as e:
            logger.error(f"Error fetching Cross-Exchange Arb: {e}")
            return self._unavailable_signal("Cross-Exchange Arb", "cross_chain")
    
    async def _get_bridge_volume(self) -> SignalResult:
        """
        Cross-chain Bridge Volume.
        Rising bridge volume = ecosystem activity.
        """
        try:
            data = await self._fetch_defi_llama_bridges()
            if data is None:
                return self._unavailable_signal("Bridge Volume", "cross_chain")
            
            volume_24h = data.get("volume_24h_usd", 0) / 1e9
            change_7d = data.get("change_7d_percent", 0)
            
            if change_7d > 50:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Bridge volume surging +{change_7d:.0f}% - activity spike"
            elif change_7d > 10:
                signal, score = SignalStrength.BUY, 1
                desc = f"Bridge volume rising +{change_7d:.0f}%"
            elif change_7d > -10:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Bridge volume stable ({change_7d:+.0f}%)"
            elif change_7d > -30:
                signal, score = SignalStrength.SELL, -1
                desc = f"Bridge volume declining {change_7d:.0f}%"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Bridge volume dropping {change_7d:.0f}%"
            
            return SignalResult(
                name="Bridge Volume",
                category="cross_chain",
                value=volume_24h,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"volume_24h_billions": volume_24h, "change_7d": change_7d}
            )
        except Exception as e:
            logger.error(f"Error fetching Bridge Volume: {e}")
            return self._unavailable_signal("Bridge Volume", "cross_chain")
    
    async def _get_wbtc_supply(self) -> SignalResult:
        """
        Wrapped BTC Supply (WBTC, etc.).
        Growing = DeFi demand for BTC exposure.
        """
        try:
            data = await self._fetch_defi_llama_data("wbtc")
            if data is None:
                return self._unavailable_signal("WBTC Supply", "cross_chain")
            
            supply_btc = data.get("total_supply_btc", 150000)
            change_30d = data.get("change_30d_percent", 0)
            
            if change_30d > 5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"WBTC supply growing +{change_30d:.1f}% - DeFi demand"
            elif change_30d > 1:
                signal, score = SignalStrength.BUY, 1
                desc = f"WBTC supply rising +{change_30d:.1f}%"
            elif change_30d > -1:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"WBTC supply stable ({change_30d:+.1f}%)"
            elif change_30d > -5:
                signal, score = SignalStrength.SELL, -1
                desc = f"WBTC supply declining {change_30d:.1f}%"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"WBTC supply dropping {change_30d:.1f}%"
            
            return SignalResult(
                name="WBTC Supply",
                category="cross_chain",
                value=supply_btc,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"supply_btc": supply_btc, "change_30d": change_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching WBTC Supply: {e}")
            return self._unavailable_signal("WBTC Supply", "cross_chain")
    
    async def _get_depeg_risk(self) -> SignalResult:
        """
        Stablecoin Depeg Risk Score.
        Based on current pegs of major stablecoins.
        """
        try:
            session = await self._get_session()
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=tether,usd-coin,dai&vs_currencies=usd"
            ) as resp:
                if resp.status != 200:
                    return self._unavailable_signal("Depeg Risk", "cross_chain")
                data = await resp.json()
            
            usdt = data.get("tether", {}).get("usd", 1.0)
            usdc = data.get("usd-coin", {}).get("usd", 1.0)
            dai = data.get("dai", {}).get("usd", 1.0)
            
            max_deviation = max(
                abs(usdt - 1.0),
                abs(usdc - 1.0),
                abs(dai - 1.0)
            ) * 100  # As percentage
            
            if max_deviation < 0.1:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Stablecoins well-pegged (max dev: {max_deviation:.2f}%)"
            elif max_deviation < 0.3:
                signal, score = SignalStrength.BUY, 1
                desc = f"Minor stablecoin deviation ({max_deviation:.2f}%)"
            elif max_deviation < 0.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Slight stablecoin stress ({max_deviation:.2f}%)"
            elif max_deviation < 1.0:
                signal, score = SignalStrength.SELL, -1
                desc = f"Stablecoin depeg risk ({max_deviation:.2f}%)"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Significant depeg ({max_deviation:.2f}%) - systemic risk"
            
            return SignalResult(
                name="Depeg Risk",
                category="cross_chain",
                value=max_deviation,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"usdt": usdt, "usdc": usdc, "dai": dai, "max_deviation": max_deviation}
            )
        except Exception as e:
            logger.error(f"Error fetching Depeg Risk: {e}")
            return self._unavailable_signal("Depeg Risk", "cross_chain")
    
    async def _get_total_mcap(self) -> SignalResult:
        """
        Total Crypto Market Cap trend.
        """
        try:
            session = await self._get_session()
            async with session.get("https://api.coingecko.com/api/v3/global") as resp:
                if resp.status != 200:
                    return self._unavailable_signal("Total MCap", "cross_chain")
                data = await resp.json()
            
            mcap = data.get("data", {}).get("total_market_cap", {}).get("usd", 0) / 1e12
            change_24h = data.get("data", {}).get("market_cap_change_percentage_24h_usd", 0)
            
            if change_24h > 5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Market surging +{change_24h:.1f}% - caution"
            elif change_24h > 2:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Market up +{change_24h:.1f}%"
            elif change_24h > -2:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Market stable ({change_24h:+.1f}%)"
            elif change_24h > -5:
                signal, score = SignalStrength.BUY, 1
                desc = f"Market dipping {change_24h:.1f}%"
            else:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Market down {change_24h:.1f}% - accumulation opportunity"
            
            return SignalResult(
                name="Total MCap",
                category="cross_chain",
                value=mcap,
                signal=signal,
                score=score,
                weight=0.8,
                description=desc,
                details={"mcap_trillions": mcap, "change_24h": change_24h}
            )
        except Exception as e:
            logger.error(f"Error fetching Total MCap: {e}")
            return self._unavailable_signal("Total MCap", "cross_chain")
    
    async def _get_btc_gold_ratio(self) -> SignalResult:
        """
        BTC vs Gold Market Cap ratio.
        """
        try:
            # Fetch BTC price and gold price
            session = await self._get_session()
            
            # BTC market cap
            async with session.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true"
            ) as resp:
                btc_data = await resp.json()
            
            btc_mcap = btc_data.get("bitcoin", {}).get("usd_market_cap", 0) / 1e12
            
            # Gold market cap ~$14T
            gold_mcap = 14.0
            
            ratio = btc_mcap / gold_mcap * 100  # As percentage
            
            if ratio < 5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"BTC is {ratio:.1f}% of gold mcap - undervalued"
            elif ratio < 10:
                signal, score = SignalStrength.BUY, 1
                desc = f"BTC is {ratio:.1f}% of gold mcap"
            elif ratio < 20:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"BTC is {ratio:.1f}% of gold mcap"
            elif ratio < 40:
                signal, score = SignalStrength.SELL, -1
                desc = f"BTC is {ratio:.1f}% of gold mcap - elevated"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"BTC is {ratio:.1f}% of gold mcap - very extended"
            
            return SignalResult(
                name="BTC/Gold Ratio",
                category="cross_chain",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.5,
                description=desc,
                details={"btc_mcap_trillions": btc_mcap, "gold_mcap_trillions": gold_mcap, "ratio": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching BTC/Gold Ratio: {e}")
            return self._unavailable_signal("BTC/Gold Ratio", "cross_chain")
    
    async def _get_crypto_m2_ratio(self) -> SignalResult:
        """
        Crypto Market Cap vs M2 Money Supply.
        """
        try:
            # Fetch total crypto mcap
            session = await self._get_session()
            async with session.get("https://api.coingecko.com/api/v3/global") as resp:
                data = await resp.json()
            
            crypto_mcap = data.get("data", {}).get("total_market_cap", {}).get("usd", 0) / 1e12
            
            # US M2 ~$21T (would need FRED API for live data)
            m2_supply = 21.0
            
            ratio = crypto_mcap / m2_supply * 100
            
            if ratio < 5:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Crypto is {ratio:.1f}% of M2 - early adoption"
            elif ratio < 10:
                signal, score = SignalStrength.BUY, 1
                desc = f"Crypto is {ratio:.1f}% of M2"
            elif ratio < 15:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Crypto is {ratio:.1f}% of M2"
            elif ratio < 25:
                signal, score = SignalStrength.SELL, -1
                desc = f"Crypto is {ratio:.1f}% of M2 - extended"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Crypto is {ratio:.1f}% of M2 - very extended"
            
            return SignalResult(
                name="Crypto/M2 Ratio",
                category="cross_chain",
                value=ratio,
                signal=signal,
                score=score,
                weight=0.4,
                description=desc,
                details={"crypto_mcap": crypto_mcap, "m2_trillions": m2_supply, "ratio": ratio}
            )
        except Exception as e:
            logger.error(f"Error fetching Crypto/M2 Ratio: {e}")
            return self._unavailable_signal("Crypto/M2 Ratio", "cross_chain")
    
    async def _get_relative_strength_sp500(self, asset: str) -> SignalResult:
        """
        30-day relative strength vs S&P 500.
        """
        try:
            data = await self._fetch_relative_strength_data(asset)
            if data is None:
                return self._unavailable_signal("RS vs S&P", "cross_chain")
            
            rs_30d = data.get("relative_strength_30d", 0)  # % outperformance
            
            if rs_30d > 20:
                signal, score = SignalStrength.SELL, -1
                desc = f"Crypto outperforming S&P by {rs_30d:.0f}% - extended"
            elif rs_30d > 5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Crypto outperforming S&P by {rs_30d:.0f}%"
            elif rs_30d > -5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Crypto tracking S&P ({rs_30d:+.0f}%)"
            elif rs_30d > -20:
                signal, score = SignalStrength.BUY, 1
                desc = f"Crypto underperforming S&P by {abs(rs_30d):.0f}%"
            else:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Crypto lagging S&P by {abs(rs_30d):.0f}% - catch-up potential"
            
            return SignalResult(
                name="RS vs S&P",
                category="cross_chain",
                value=rs_30d,
                signal=signal,
                score=score,
                weight=0.6,
                description=desc,
                details={"relative_strength_30d": rs_30d}
            )
        except Exception as e:
            logger.error(f"Error fetching RS vs S&P: {e}")
            return self._unavailable_signal("RS vs S&P", "cross_chain")
    
    # =========================================================================
    # CATEGORY 14: CYCLE POSITION INDICATORS
    # =========================================================================
    
    async def _get_pi_cycle(self, asset: str) -> SignalResult:
        """
        Pi Cycle Top Indicator.
        Cross of 111-day MA over 2x 350-day MA has historically marked tops.
        """
        try:
            data = await self._fetch_lookintobitcoin_data("pi_cycle")
            if data is None:
                return self._unavailable_signal("Pi Cycle", "cycle_position")
            
            distance_pct = data.get("distance_to_cross_percent", 10)
            crossed = data.get("crossed", False)
            
            if crossed:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = "Pi Cycle TOP SIGNAL - historically marks peaks"
            elif distance_pct < 5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Pi Cycle nearing cross ({distance_pct:.1f}% away)"
            elif distance_pct < 15:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Pi Cycle {distance_pct:.1f}% from cross"
            elif distance_pct < 30:
                signal, score = SignalStrength.BUY, 1
                desc = f"Pi Cycle {distance_pct:.1f}% from cross - healthy"
            else:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Pi Cycle {distance_pct:.1f}% from cross - early cycle"
            
            return SignalResult(
                name="Pi Cycle",
                category="cycle_position",
                value=distance_pct,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"distance_to_cross": distance_pct, "crossed": crossed}
            )
        except Exception as e:
            logger.error(f"Error fetching Pi Cycle: {e}")
            return self._unavailable_signal("Pi Cycle", "cycle_position")
    
    async def _get_200w_ma_heatmap(self, asset: str) -> SignalResult:
        """
        200-Week MA Heatmap Position.
        Price relative to 200W MA and rate of change.
        """
        try:
            data = await self._fetch_lookintobitcoin_data("200w_ma_heatmap")
            if data is None:
                return self._unavailable_signal("200W MA Heatmap", "cycle_position")
            
            pct_above = data.get("percent_above_200w_ma", 0)
            heatmap_color = data.get("heatmap_color", "orange")  # blue->green->yellow->orange->red
            
            if pct_above < -20:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price {abs(pct_above):.0f}% below 200W MA - deep value"
            elif pct_above < 0:
                signal, score = SignalStrength.BUY, 1
                desc = f"Price {abs(pct_above):.0f}% below 200W MA"
            elif pct_above < 100:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Price {pct_above:.0f}% above 200W MA"
            elif pct_above < 200:
                signal, score = SignalStrength.SELL, -1
                desc = f"Price {pct_above:.0f}% above 200W MA - elevated"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Price {pct_above:.0f}% above 200W MA - parabolic"
            
            return SignalResult(
                name="200W MA Heatmap",
                category="cycle_position",
                value=pct_above,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                details={"pct_above_200w": pct_above, "color": heatmap_color}
            )
        except Exception as e:
            logger.error(f"Error fetching 200W MA Heatmap: {e}")
            return self._unavailable_signal("200W MA Heatmap", "cycle_position")
    
    async def _get_rainbow_band(self, asset: str) -> SignalResult:
        """
        Bitcoin Rainbow Price Band position.
        """
        try:
            data = await self._fetch_lookintobitcoin_data("rainbow")
            if data is None:
                return self._unavailable_signal("Rainbow Band", "cycle_position")
            
            band = data.get("band", 5)  # 1-9
            band_name = data.get("band_name", "Hold")
            
            band_signals = {
                1: (SignalStrength.STRONG_BUY, 2, "Fire Sale"),
                2: (SignalStrength.STRONG_BUY, 2, "BUY!"),
                3: (SignalStrength.BUY, 1, "Accumulate"),
                4: (SignalStrength.BUY, 1, "Still Cheap"),
                5: (SignalStrength.NEUTRAL, 0, "Hold"),
                6: (SignalStrength.NEUTRAL, 0, "Is this a bubble?"),
                7: (SignalStrength.SELL, -1, "FOMO intensifies"),
                8: (SignalStrength.SELL, -1, "Sell. Seriously."),
                9: (SignalStrength.STRONG_SELL, -2, "Maximum bubble"),
            }
            
            signal, score, _ = band_signals.get(band, (SignalStrength.NEUTRAL, 0, "Unknown"))
            
            return SignalResult(
                name="Rainbow Band",
                category="cycle_position",
                value=band,
                signal=signal,
                score=score,
                weight=0.9,
                description=f"Rainbow Band: {band_name}",
                details={"band": band, "band_name": band_name}
            )
        except Exception as e:
            logger.error(f"Error fetching Rainbow Band: {e}")
            return self._unavailable_signal("Rainbow Band", "cycle_position")
    
    async def _get_halving_cycle_position(self, asset: str) -> SignalResult:
        """
        Position in halving cycle (0-100%).
        0% = just after halving, 100% = just before next halving.
        """
        if asset.upper() != "BTC":
            return self._unavailable_signal("Halving Cycle", "cycle_position")
        
        try:
            last_halving = date(2024, 4, 19)
            next_halving = date(2028, 4, 15)
            today = date.today()
            
            total_days = (next_halving - last_halving).days
            days_elapsed = (today - last_halving).days
            
            position = (days_elapsed / total_days) * 100
            
            if position < 25:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Early cycle ({position:.0f}%) - historically best accumulation"
            elif position < 50:
                signal, score = SignalStrength.BUY, 1
                desc = f"Mid-early cycle ({position:.0f}%)"
            elif position < 75:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Mid-cycle ({position:.0f}%)"
            elif position < 90:
                signal, score = SignalStrength.SELL, -1
                desc = f"Late cycle ({position:.0f}%)"
            else:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Pre-halving ({position:.0f}%) - anticipation building"
            
            return SignalResult(
                name="Halving Cycle",
                category="cycle_position",
                value=position,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"cycle_position_percent": position}
            )
        except Exception as e:
            logger.error(f"Error calculating Halving Cycle: {e}")
            return self._unavailable_signal("Halving Cycle", "cycle_position")
    
    async def _get_four_year_phase(self, asset: str) -> SignalResult:
        """
        4-Year Cycle Phase (Accumulation -> Markup -> Distribution -> Markdown).
        """
        try:
            data = await self._fetch_lookintobitcoin_data("four_year_cycle")
            if data is None:
                return self._unavailable_signal("4-Year Phase", "cycle_position")
            
            phase = data.get("phase", "markup")
            confidence = data.get("confidence", 0.5)
            
            phase_signals = {
                "accumulation": (SignalStrength.STRONG_BUY, 2),
                "early_markup": (SignalStrength.BUY, 1),
                "markup": (SignalStrength.NEUTRAL, 0),
                "late_markup": (SignalStrength.SELL, -1),
                "distribution": (SignalStrength.SELL, -1),
                "markdown": (SignalStrength.BUY, 1),  # End of markdown = accumulation
            }
            
            signal, score = phase_signals.get(phase, (SignalStrength.NEUTRAL, 0))
            
            return SignalResult(
                name="4-Year Phase",
                category="cycle_position",
                value=confidence,
                signal=signal,
                score=score,
                weight=1.0,
                description=f"4-Year Cycle: {phase.replace('_', ' ').title()} ({confidence:.0%} confidence)",
                details={"phase": phase, "confidence": confidence}
            )
        except Exception as e:
            logger.error(f"Error fetching 4-Year Phase: {e}")
            return self._unavailable_signal("4-Year Phase", "cycle_position")
    
    async def _get_mayer_multiple(self, asset: str) -> SignalResult:
        """
        Mayer Multiple - Price / 200-day MA.
        < 0.8: Historically good buy
        > 2.4: Historically overextended
        """
        try:
            data = await self._fetch_lookintobitcoin_data("mayer_multiple")
            if data is None:
                return self._unavailable_signal("Mayer Multiple", "cycle_position")
            
            mayer = data.get("value", 1.0)
            
            if mayer < 0.6:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Mayer Multiple {mayer:.2f} - extreme undervaluation"
            elif mayer < 0.8:
                signal, score = SignalStrength.BUY, 1
                desc = f"Mayer Multiple {mayer:.2f} - undervalued"
            elif mayer < 1.5:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Mayer Multiple {mayer:.2f} - fair value"
            elif mayer < 2.4:
                signal, score = SignalStrength.SELL, -1
                desc = f"Mayer Multiple {mayer:.2f} - elevated"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Mayer Multiple {mayer:.2f} - overextended"
            
            return SignalResult(
                name="Mayer Multiple",
                category="cycle_position",
                value=mayer,
                signal=signal,
                score=score,
                weight=1.1,
                description=desc,
                details={"mayer_multiple": mayer}
            )
        except Exception as e:
            logger.error(f"Error fetching Mayer Multiple: {e}")
            return self._unavailable_signal("Mayer Multiple", "cycle_position")
    
    async def _get_investor_tool(self, asset: str) -> SignalResult:
        """
        2-Year MA Multiplier (Investor Tool).
        Below 2Y MA = buy zone, Above 2Y MA x 5 = sell zone.
        """
        try:
            data = await self._fetch_lookintobitcoin_data("investor_tool")
            if data is None:
                return self._unavailable_signal("Investor Tool", "cycle_position")
            
            position = data.get("position", "middle")  # "below_2y", "middle", "above_5x"
            price = data.get("price", 0)
            ma_2y = data.get("ma_2y", 0)
            ma_2y_x5 = data.get("ma_2y_x5", 0)
            
            if position == "below_2y":
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Price below 2Y MA - historically best buy zone"
            elif position == "above_5x":
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Price above 2Y MA x5 - historically sell zone"
            else:
                # Calculate position within range
                range_size = ma_2y_x5 - ma_2y if ma_2y_x5 > ma_2y else 1
                pct_in_range = (price - ma_2y) / range_size * 100
                
                if pct_in_range < 25:
                    signal, score = SignalStrength.BUY, 1
                    desc = f"Lower part of range ({pct_in_range:.0f}%)"
                elif pct_in_range < 75:
                    signal, score = SignalStrength.NEUTRAL, 0
                    desc = f"Middle of range ({pct_in_range:.0f}%)"
                else:
                    signal, score = SignalStrength.SELL, -1
                    desc = f"Upper part of range ({pct_in_range:.0f}%)"
            
            return SignalResult(
                name="Investor Tool",
                category="cycle_position",
                value=price,
                signal=signal,
                score=score,
                weight=1.0,
                description=desc,
                details={"position": position, "price": price, "ma_2y": ma_2y}
            )
        except Exception as e:
            logger.error(f"Error fetching Investor Tool: {e}")
            return self._unavailable_signal("Investor Tool", "cycle_position")
    
    async def _get_golden_ratio(self, asset: str) -> SignalResult:
        """
        Golden Ratio Multiplier.
        Uses 350-day MA with golden ratio multipliers (1.6, 2, 3, 5, 8, 13, 21).
        """
        try:
            data = await self._fetch_lookintobitcoin_data("golden_ratio")
            if data is None:
                return self._unavailable_signal("Golden Ratio", "cycle_position")
            
            current_band = data.get("band", 3)  # 1-7 (which multiplier we're at)
            band_names = ["Below 350MA", "350MA-1.6x", "1.6x-2x", "2x-3x", "3x-5x", "5x-8x", "Above 8x"]
            
            if current_band <= 1:
                signal, score = SignalStrength.STRONG_BUY, 2
                desc = f"Golden Ratio: {band_names[current_band]} - deep value"
            elif current_band <= 2:
                signal, score = SignalStrength.BUY, 1
                desc = f"Golden Ratio: {band_names[current_band]}"
            elif current_band <= 4:
                signal, score = SignalStrength.NEUTRAL, 0
                desc = f"Golden Ratio: {band_names[current_band]}"
            elif current_band <= 5:
                signal, score = SignalStrength.SELL, -1
                desc = f"Golden Ratio: {band_names[current_band]} - elevated"
            else:
                signal, score = SignalStrength.STRONG_SELL, -2
                desc = f"Golden Ratio: {band_names[min(current_band, 6)]} - extreme"
            
            return SignalResult(
                name="Golden Ratio",
                category="cycle_position",
                value=current_band,
                signal=signal,
                score=score,
                weight=0.9,
                description=desc,
                details={"band": current_band}
            )
        except Exception as e:
            logger.error(f"Error fetching Golden Ratio: {e}")
            return self._unavailable_signal("Golden Ratio", "cycle_position")
    
    # =========================================================================
    # API FETCH HELPERS (Placeholders - implement with real APIs)
    # =========================================================================
    
    async def _fetch_glassnode_metric(self, asset: str, metric: str) -> Optional[Dict]:
        """Fetch from Glassnode API (requires API key)."""
        # Implementation would use actual Glassnode API
        # For now, return placeholder to show structure
        return None
    
    async def _fetch_cryptoquant_metric(self, asset: str, metric: str) -> Optional[Dict]:
        """Fetch from CryptoQuant API."""
        return None
    
    async def _fetch_ultrasound_money_data(self) -> Optional[Dict]:
        """Fetch ETH burn data from ultrasound.money."""
        return None
    
    async def _fetch_beaconchain_data(self) -> Optional[Dict]:
        """Fetch ETH staking data from beaconcha.in."""
        return None
    
    async def _fetch_l2beat_data(self) -> Optional[Dict]:
        """Fetch L2 TVL from L2Beat."""
        return None
    
    async def _fetch_the_block_data(self, metric: str) -> Optional[Dict]:
        """Fetch data from The Block."""
        return None
    
    async def _fetch_defi_llama_stablecoins(self) -> Optional[Dict]:
        """Fetch stablecoin data from DefiLlama."""
        try:
            session = await self._get_session()
            async with session.get("https://stablecoins.llama.fi/stablecoins") as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
            
            # Parse response
            total = sum(s.get("circulating", {}).get("peggedUSD", 0) for s in data.get("peggedAssets", []))
            usdt = next((s.get("circulating", {}).get("peggedUSD", 0) 
                        for s in data.get("peggedAssets", []) 
                        if s.get("symbol") == "USDT"), 0)
            
            return {
                "total_mcap_usd": total,
                "usdt_dominance": usdt / total if total > 0 else 0,
                "change_30d_percent": 0,  # Would need historical data
            }
        except:
            return None
    
    async def _fetch_defi_llama_yields(self) -> Optional[Dict]:
        """Fetch yield data from DefiLlama."""
        return None
    
    async def _fetch_aave_data(self) -> Optional[Dict]:
        """Fetch Aave lending data."""
        return None
    
    async def _fetch_kaiko_data(self, asset: str, metric: str) -> Optional[Dict]:
        """Fetch market microstructure data from Kaiko."""
        return None
    
    async def _fetch_whale_alert_data(self, asset: str) -> Optional[Dict]:
        """Fetch whale transaction data."""
        return None
    
    async def _fetch_coinglass_data(self, asset: str, metric: str) -> Optional[Dict]:
        """Fetch derivatives data from Coinglass."""
        return None
    
    async def _fetch_cme_data(self, asset: str) -> Optional[Dict]:
        """Fetch CME futures data."""
        return None
    
    async def _fetch_defi_llama_bridges(self) -> Optional[Dict]:
        """Fetch bridge volume from DefiLlama."""
        return None
    
    async def _fetch_defi_llama_data(self, protocol: str) -> Optional[Dict]:
        """Fetch protocol data from DefiLlama."""
        return None
    
    async def _fetch_relative_strength_data(self, asset: str) -> Optional[Dict]:
        """Calculate relative strength vs S&P 500."""
        return None
    
    async def _fetch_lookintobitcoin_data(self, metric: str) -> Optional[Dict]:
        """Fetch cycle indicators from LookIntoBitcoin."""
        return None
    
    # =========================================================================
    # CATEGORY 15: ADVANCED ON-CHAIN (Stubs - would be implemented similarly)
    # =========================================================================
    
    async def _get_realized_cap_hodl_waves(self, asset: str) -> SignalResult:
        """Realized Cap HODL Waves - distribution of supply by age."""
        return self._unavailable_signal("HODL Waves", "advanced_onchain")
    
    async def _get_vdd_multiple(self, asset: str) -> SignalResult:
        """Value Days Destroyed Multiple."""
        return self._unavailable_signal("VDD Multiple", "advanced_onchain")
    
    async def _get_adjusted_transfer_volume(self, asset: str) -> SignalResult:
        """Entity-adjusted transfer volume."""
        return self._unavailable_signal("Transfer Volume", "advanced_onchain")
    
    async def _get_velocity(self, asset: str) -> SignalResult:
        """Token velocity (inverse of NVT)."""
        return self._unavailable_signal("Velocity", "advanced_onchain")
    
    async def _get_young_supply_pnl(self, asset: str) -> SignalResult:
        """Young supply (<155d) profit/loss status."""
        return self._unavailable_signal("Young Supply P/L", "advanced_onchain")
    
    async def _get_old_supply_movement(self, asset: str) -> SignalResult:
        """Movement of old supply (>1yr)."""
        return self._unavailable_signal("Old Supply Movement", "advanced_onchain")
    
    async def _get_revived_supply(self, asset: str) -> SignalResult:
        """Amount of dormant supply being revived."""
        return self._unavailable_signal("Revived Supply", "advanced_onchain")
    
    async def _get_stablecoin_exchange_ratio(self) -> SignalResult:
        """Stablecoins on exchanges relative to BTC/ETH."""
        return self._unavailable_signal("Stablecoin Exchange Ratio", "advanced_onchain")
    
    # =========================================================================
    # CATEGORY 16: ADVANCED SENTIMENT (Stubs)
    # =========================================================================
    
    async def _get_weighted_social_volume(self, asset: str) -> SignalResult:
        """Weighted social media volume (quality-adjusted)."""
        return self._unavailable_signal("Social Volume", "advanced_sentiment")
    
    async def _get_dev_activity(self, asset: str) -> SignalResult:
        """GitHub development activity."""
        return self._unavailable_signal("Dev Activity", "advanced_sentiment")
    
    async def _get_whale_alert_frequency(self, asset: str) -> SignalResult:
        """Frequency of large transaction alerts."""
        return self._unavailable_signal("Whale Alert Freq", "advanced_sentiment")
    
    async def _get_exchange_maintenance(self) -> SignalResult:
        """Scheduled exchange maintenance events."""
        return self._unavailable_signal("Exchange Maintenance", "advanced_sentiment")
    
    async def _get_regulatory_sentiment(self) -> SignalResult:
        """Regulatory news sentiment score."""
        return self._unavailable_signal("Regulatory Sentiment", "advanced_sentiment")
    
    async def _get_ai_mention_trend(self) -> SignalResult:
        """AI/LLM crypto mention trend."""
        return self._unavailable_signal("AI Mention Trend", "advanced_sentiment")
    
    # =========================================================================
    # MAIN ANALYSIS METHOD
    # =========================================================================
    
    async def analyze(self, asset: str = "BTC") -> ExpandedSignalAnalysis:
        """
        Run expanded 70-signal analysis.
        """
        # Gather all signals by category
        smart_money_tasks = [
            self._get_entity_adjusted_sopr(asset),
            self._get_lth_sopr(asset),
            self._get_sth_sopr(asset),
            self._get_realized_losses(asset),
            self._get_exchange_whale_ratio(asset),
            self._get_accumulation_trend_score(asset),
            self._get_dormancy_flow(asset),
            self._get_supply_in_profit(asset),
            self._get_liveliness(asset),
            self._get_asol(asset),
            self._get_binary_cdd(asset),
            self._get_lth_supply(asset),
        ]
        
        defi_altcoin_tasks = [
            self._get_eth_gas(),
            self._get_eth_burn_rate(),
            self._get_eth_staking_ratio(),
            self._get_l2_tvl(),
            self._get_dex_cex_ratio(),
            self._get_altcoin_season_index(),
            self._get_btc_dominance(),
            self._get_eth_btc_ratio(),
            self._get_stablecoin_mcap(),
            self._get_usdt_dominance(),
            self._get_real_yield(),
            self._get_lending_utilization(),
        ]
        
        order_flow_tasks = [
            self._get_bid_ask_spread(asset),
            self._get_order_book_depth(asset),
            self._get_whale_order_flow(asset),
            self._get_spot_deriv_volume(asset),
            self._get_cvd(asset),
            self._get_taker_ratio(asset),
            self._get_large_trade_intensity(asset),
            self._get_slippage_estimate(asset),
        ]
        
        economic_calendar_tasks = [
            self._get_fomc_signal(),
            self._get_cpi_signal(),
            self._get_nfp_signal(),
            self._get_options_expiry_signal(),
            self._get_cme_gap_signal(asset),
            self._get_quarter_end_signal(),
            self._get_tax_season_signal(),
            self._get_halving_countdown(asset),
        ]
        
        cross_chain_tasks = [
            self._get_cross_exchange_arb(asset),
            self._get_bridge_volume(),
            self._get_wbtc_supply(),
            self._get_depeg_risk(),
            self._get_total_mcap(),
            self._get_btc_gold_ratio(),
            self._get_crypto_m2_ratio(),
            self._get_relative_strength_sp500(asset),
        ]
        
        cycle_position_tasks = [
            self._get_pi_cycle(asset),
            self._get_200w_ma_heatmap(asset),
            self._get_rainbow_band(asset),
            self._get_halving_cycle_position(asset),
            self._get_four_year_phase(asset),
            self._get_mayer_multiple(asset),
            self._get_investor_tool(asset),
            self._get_golden_ratio(asset),
        ]
        
        advanced_onchain_tasks = [
            self._get_realized_cap_hodl_waves(asset),
            self._get_vdd_multiple(asset),
            self._get_adjusted_transfer_volume(asset),
            self._get_velocity(asset),
            self._get_young_supply_pnl(asset),
            self._get_old_supply_movement(asset),
            self._get_revived_supply(asset),
            self._get_stablecoin_exchange_ratio(),
        ]
        
        advanced_sentiment_tasks = [
            self._get_weighted_social_volume(asset),
            self._get_dev_activity(asset),
            self._get_whale_alert_frequency(asset),
            self._get_exchange_maintenance(),
            self._get_regulatory_sentiment(),
            self._get_ai_mention_trend(),
        ]
        
        # Run all tasks
        all_results = await asyncio.gather(
            *smart_money_tasks,
            *defi_altcoin_tasks,
            *order_flow_tasks,
            *economic_calendar_tasks,
            *cross_chain_tasks,
            *cycle_position_tasks,
            *advanced_onchain_tasks,
            *advanced_sentiment_tasks,
            return_exceptions=True
        )
        
        # Split results
        idx = 0
        smart_money_signals = self._process_results(all_results[idx:idx+len(smart_money_tasks)])
        idx += len(smart_money_tasks)
        
        defi_signals = self._process_results(all_results[idx:idx+len(defi_altcoin_tasks)])
        idx += len(defi_altcoin_tasks)
        
        order_flow_signals = self._process_results(all_results[idx:idx+len(order_flow_tasks)])
        idx += len(order_flow_tasks)
        
        calendar_signals = self._process_results(all_results[idx:idx+len(economic_calendar_tasks)])
        idx += len(economic_calendar_tasks)
        
        cross_chain_signals = self._process_results(all_results[idx:idx+len(cross_chain_tasks)])
        idx += len(cross_chain_tasks)
        
        cycle_signals = self._process_results(all_results[idx:idx+len(cycle_position_tasks)])
        idx += len(cycle_position_tasks)
        
        adv_onchain_signals = self._process_results(all_results[idx:idx+len(advanced_onchain_tasks)])
        idx += len(advanced_onchain_tasks)
        
        adv_sentiment_signals = self._process_results(all_results[idx:idx+len(advanced_sentiment_tasks)])
        
        # Create category summaries
        categories = {
            "smart_money": ("Smart Money", smart_money_signals),
            "defi_altcoin": ("DeFi/Altcoin", defi_signals),
            "order_flow": ("Order Flow", order_flow_signals),
            "economic_calendar": ("Calendar", calendar_signals),
            "cross_chain": ("Cross-Chain", cross_chain_signals),
            "cycle_position": ("Cycle Position", cycle_signals),
            "advanced_onchain": ("Advanced On-Chain", adv_onchain_signals),
            "advanced_sentiment": ("Advanced Sentiment", adv_sentiment_signals),
        }
        
        summaries = {}
        all_signals = []
        total_weighted_score = 0
        total_weight = 0
        
        for key, (name, signals) in categories.items():
            summary = self._create_category_summary(name, signals, key)
            summaries[key] = summary
            all_signals.extend(signals)
            
            if summary.weighted_score != 0:
                total_weighted_score += summary.weighted_score * self.CATEGORY_WEIGHTS.get(key, 1.0)
                total_weight += self.CATEGORY_WEIGHTS.get(key, 1.0)
        
        # Calculate composite
        available = sum(1 for s in all_signals if s.signal != SignalStrength.UNAVAILABLE)
        total = len(all_signals)
        confidence = available / total if total > 0 else 0
        
        composite_score = (total_weighted_score / total_weight * 50) if total_weight > 0 else 0
        composite_score = max(-100, min(100, composite_score))
        
        return ExpandedSignalAnalysis(
            timestamp=datetime.utcnow(),
            asset=asset,
            smart_money=summaries["smart_money"],
            defi_altcoin=summaries["defi_altcoin"],
            order_flow=summaries["order_flow"],
            economic_calendar=summaries["economic_calendar"],
            cross_chain=summaries["cross_chain"],
            cycle_position=summaries["cycle_position"],
            advanced_onchain=summaries["advanced_onchain"],
            advanced_sentiment=summaries["advanced_sentiment"],
            total_signals=total,
            available_signals=available,
            composite_score=composite_score,
            confidence=confidence,
            all_signals=all_signals,
        )
    
    def _process_results(self, results: List) -> List[SignalResult]:
        """Process asyncio.gather results, handling exceptions."""
        processed = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                processed.append(self._unavailable_signal(f"Signal{i}", "unknown"))
            else:
                processed.append(r)
        return processed
    
    def _create_category_summary(self, name: str, signals: List[SignalResult], category: str) -> ExpandedCategorySummary:
        """Create summary for a category."""
        available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]
        
        bullish = sum(1 for s in available if s.score > 0)
        bearish = sum(1 for s in available if s.score < 0)
        neutral = sum(1 for s in available if s.score == 0)
        unavailable = len(signals) - len(available)
        
        if available:
            avg_score = sum(s.score for s in available) / len(available)
            weighted_score = sum(s.score * s.weight for s in available) / sum(s.weight for s in available)
        else:
            avg_score = 0
            weighted_score = 0
        
        return ExpandedCategorySummary(
            name=name,
            signals=signals,
            avg_score=avg_score,
            weighted_score=weighted_score,
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            unavailable_count=unavailable,
        )


def format_expanded_signals(analysis: ExpandedSignalAnalysis) -> str:
    """Format expanded signal analysis for display."""
    lines = [
        "",
        "=" * 75,
        f"  EXPANDED SIGNAL ANALYSIS (70 Additional Signals) - {analysis.asset}",
        f"  {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "=" * 75,
        "",
        f"  COMPOSITE SCORE: {analysis.composite_score:+.1f} / 100",
        f"  Signals: {analysis.available_signals}/{analysis.total_signals} available ({analysis.confidence:.0%})",
        "",
        "-" * 75,
    ]
    
    categories = [
        ("SMART MONEY", analysis.smart_money),
        ("DEFI/ALTCOIN", analysis.defi_altcoin),
        ("ORDER FLOW", analysis.order_flow),
        ("ECONOMIC CALENDAR", analysis.economic_calendar),
        ("CROSS-CHAIN", analysis.cross_chain),
        ("CYCLE POSITION", analysis.cycle_position),
        ("ADVANCED ON-CHAIN", analysis.advanced_onchain),
        ("ADVANCED SENTIMENT", analysis.advanced_sentiment),
    ]
    
    for name, summary in categories:
        lines.append(f"\n  {name} ({summary.bullish_count}🟢 {summary.bearish_count}🔴 "
                    f"{summary.neutral_count}⚪ {summary.unavailable_count}❓)")
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
    lines.append("=" * 75)
    
    return "\n".join(lines)
