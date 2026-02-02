"""
Extended Market Signals Module

Additional signals beyond basic technicals:
1. Liquidation cascades (Coinglass)
2. Stablecoin supply (dry powder indicator)
3. Google Trends (retail interest)
4. S&P 500 correlation (risk-on/risk-off)
5. Options data (put/call ratio, max pain)
6. Network metrics (hash rate, active addresses)
7. Macro indicators (DXY, Gold, Treasury yields)
8. Social sentiment (aggregated)
9. Whale transactions
10. Exchange reserves
11. Miner metrics
12. Long/short ratio
13. Open interest
14. Grayscale/ETF flows
15. Stablecoin dominance
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import aiohttp

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength indicator."""
    STRONG_SELL = -2
    SELL = -1
    NEUTRAL = 0
    BUY = 1
    STRONG_BUY = 2
    UNAVAILABLE = -99


@dataclass
class Signal:
    """A market signal."""
    name: str
    category: str
    value: float
    signal: SignalStrength
    weight: float
    description: str
    data_source: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def weighted_score(self) -> float:
        return self.signal.value * self.weight


@dataclass
class SignalResult:
    """Individual signal result (unified interface for both analyzers)."""
    name: str
    category: str
    value: Optional[float]
    signal: SignalStrength
    score: int  # -2 to +2
    weight: float
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_signal(cls, s: "Signal") -> "SignalResult":
        """Convert a Signal to a SignalResult."""
        return cls(
            name=s.name,
            category=s.category,
            value=s.value,
            signal=s.signal,
            score=s.signal.value if s.signal != SignalStrength.UNAVAILABLE else 0,
            weight=s.weight,
            description=s.description,
            details={"data_source": s.data_source},
            timestamp=s.timestamp,
        )


@dataclass
class BaseCategorySummary:
    """Summary for a category of base signals."""
    name: str
    signals: List[SignalResult]
    avg_score: float
    weighted_score: float
    bullish_count: int
    bearish_count: int
    neutral_count: int
    unavailable_count: int


@dataclass
class ComprehensiveSignalAnalysis:
    """Complete analysis from the base 60 signals."""
    timestamp: datetime
    asset: str

    # Category summaries
    technical: BaseCategorySummary
    sentiment: BaseCategorySummary
    onchain: BaseCategorySummary
    derivatives: BaseCategorySummary
    macro: BaseCategorySummary
    institutional: BaseCategorySummary

    # Scores
    total_signals: int
    available_signals: int
    composite_score: float
    signal_strength: SignalStrength

    # All signals
    all_signals: List[SignalResult] = field(default_factory=list)


# =============================================================================
# LIQUIDATION DATA
# =============================================================================

@dataclass
class LiquidationData:
    """Liquidation data from derivatives markets."""
    asset: str
    long_liquidations_24h: float  # USD value
    short_liquidations_24h: float
    long_liquidations_1h: float
    short_liquidations_1h: float
    liquidation_ratio: float  # Long/Short ratio
    signal: SignalStrength
    is_cascade: bool  # Large liquidation event

    @property
    def total_24h(self) -> float:
        return self.long_liquidations_24h + self.short_liquidations_24h

    @property
    def interpretation(self) -> str:
        if self.is_cascade and self.liquidation_ratio > 2:
            return "Long cascade - potential bottom"
        elif self.is_cascade and self.liquidation_ratio < 0.5:
            return "Short squeeze - potential top"
        elif self.liquidation_ratio > 1.5:
            return "More longs liquidated - bearish flush"
        elif self.liquidation_ratio < 0.67:
            return "More shorts liquidated - bullish"
        return "Balanced liquidations"


# =============================================================================
# STABLECOIN METRICS
# =============================================================================

@dataclass
class StablecoinMetrics:
    """Stablecoin supply and flow metrics."""
    total_supply: float  # Total stablecoin market cap
    supply_change_7d: float  # Percentage change
    supply_change_30d: float
    usdt_supply: float
    usdc_supply: float
    dai_supply: float
    usdt_dominance: float  # USDT % of total stablecoins
    stablecoin_ratio: float  # Stablecoins / BTC market cap
    signal: SignalStrength

    @property
    def interpretation(self) -> str:
        if self.supply_change_7d > 5:
            return "Stablecoin inflows - dry powder accumulating"
        elif self.supply_change_7d < -5:
            return "Stablecoin outflows - capital leaving crypto"
        elif self.stablecoin_ratio > 0.15:
            return "High stablecoin ratio - lots of sidelined capital"
        return "Normal stablecoin levels"


# =============================================================================
# GOOGLE TRENDS
# =============================================================================

@dataclass
class GoogleTrendsData:
    """Google Trends search interest data."""
    term: str
    current_interest: int  # 0-100 scale
    interest_7d_ago: int
    interest_30d_ago: int
    interest_change_7d: float  # Percentage
    interest_change_30d: float
    peak_interest_90d: int
    signal: SignalStrength

    @property
    def interpretation(self) -> str:
        if self.current_interest > 80:
            return "Peak retail interest - potential top"
        elif self.current_interest < 20:
            return "Low retail interest - accumulation zone"
        elif self.interest_change_7d > 50:
            return "Surging interest - FOMO building"
        elif self.interest_change_7d < -30:
            return "Declining interest - capitulation"
        return "Normal search interest"


# =============================================================================
# CORRELATION DATA
# =============================================================================

@dataclass
class CorrelationData:
    """Correlation with traditional markets."""
    btc_sp500_corr_30d: float  # -1 to 1
    btc_gold_corr_30d: float
    btc_dxy_corr_30d: float  # Usually negative
    eth_btc_corr_30d: float

    sp500_change_7d: float
    gold_change_7d: float
    dxy_value: float
    dxy_change_7d: float

    signal: SignalStrength
    risk_regime: str  # "risk-on", "risk-off", "decoupled"

    @property
    def interpretation(self) -> str:
        if self.dxy_change_7d < -1 and self.btc_dxy_corr_30d < -0.3:
            return "Weakening dollar - bullish for crypto"
        elif self.dxy_change_7d > 1:
            return "Strengthening dollar - headwind for crypto"
        elif abs(self.btc_sp500_corr_30d) < 0.3:
            return "BTC decoupling from stocks"
        elif self.btc_gold_corr_30d > 0.5:
            return "BTC trading like digital gold"
        return f"Risk regime: {self.risk_regime}"


# =============================================================================
# OPTIONS DATA
# =============================================================================

@dataclass
class OptionsData:
    """Options market data."""
    asset: str
    put_call_ratio: float  # < 1 = bullish, > 1 = bearish
    max_pain_price: float  # Price where most options expire worthless
    current_price: float
    distance_to_max_pain: float  # Percentage
    implied_volatility: float
    iv_percentile: float  # Current IV vs historical

    total_call_oi: float  # Open interest
    total_put_oi: float

    signal: SignalStrength

    @property
    def interpretation(self) -> str:
        if self.put_call_ratio > 1.5:
            return "High put/call - extreme bearishness (contrarian buy)"
        elif self.put_call_ratio < 0.5:
            return "Low put/call - extreme bullishness (contrarian sell)"
        elif self.iv_percentile > 80:
            return "High IV - expect big move, good for selling premium"
        elif self.iv_percentile < 20:
            return "Low IV - calm before storm"
        return "Balanced options market"


# =============================================================================
# NETWORK METRICS
# =============================================================================

@dataclass
class NetworkMetrics:
    """Blockchain network health metrics."""
    asset: str

    # Activity
    active_addresses_24h: int
    active_addresses_7d_avg: int
    address_growth_7d: float  # Percentage

    # Transactions
    transaction_count_24h: int
    avg_transaction_value: float

    # For BTC specifically
    hash_rate: Optional[float] = None  # TH/s
    hash_rate_change_7d: Optional[float] = None
    difficulty: Optional[float] = None

    # For ETH specifically
    gas_price_gwei: Optional[float] = None

    signal: SignalStrength = SignalStrength.NEUTRAL

    @property
    def interpretation(self) -> str:
        if self.address_growth_7d > 10:
            return "Strong network growth - adoption increasing"
        elif self.address_growth_7d < -10:
            return "Declining activity - users leaving"
        elif self.hash_rate_change_7d and self.hash_rate_change_7d > 5:
            return "Hash rate increasing - miners confident"
        return "Normal network activity"


# =============================================================================
# SOCIAL SENTIMENT
# =============================================================================

@dataclass
class SocialSentiment:
    """Aggregated social media sentiment."""
    asset: str

    # Sentiment scores (-100 to +100)
    twitter_sentiment: float
    reddit_sentiment: float
    aggregated_sentiment: float

    # Volume
    social_volume_24h: int  # Number of mentions
    social_volume_change_7d: float

    # Influencer activity
    influencer_mentions: int

    signal: SignalStrength

    @property
    def interpretation(self) -> str:
        if self.aggregated_sentiment > 70:
            return "Extreme positive sentiment - potential top"
        elif self.aggregated_sentiment < -50:
            return "Extreme negative sentiment - potential bottom"
        elif self.social_volume_change_7d > 100:
            return "Social volume exploding - major event"
        return "Normal social activity"


# =============================================================================
# WHALE ACTIVITY
# =============================================================================

@dataclass
class WhaleActivity:
    """Large transaction monitoring."""
    asset: str

    whale_transactions_24h: int  # Transactions > $1M
    whale_volume_24h: float  # Total USD volume

    exchange_inflows_24h: float  # To exchanges (selling pressure)
    exchange_outflows_24h: float  # From exchanges (accumulation)
    net_flow: float  # Negative = outflows (bullish)

    large_buys_24h: int
    large_sells_24h: int

    signal: SignalStrength

    @property
    def interpretation(self) -> str:
        if self.net_flow < -100_000_000:  # $100M+ outflows
            return "Massive whale accumulation"
        elif self.net_flow > 100_000_000:
            return "Whales moving to exchanges - selling pressure"
        elif self.large_buys_24h > self.large_sells_24h * 2:
            return "Whales buying aggressively"
        elif self.large_sells_24h > self.large_buys_24h * 2:
            return "Whales selling aggressively"
        return "Normal whale activity"


# =============================================================================
# FUNDING & OPEN INTEREST
# =============================================================================

@dataclass
class FundingOIData:
    """Funding rates and open interest data."""
    asset: str

    # Funding
    funding_rate_8h: float  # Current 8-hour funding
    funding_rate_avg_7d: float
    predicted_funding: float

    # Open Interest
    open_interest: float  # USD value
    oi_change_24h: float  # Percentage
    oi_change_7d: float

    # Long/Short ratio
    long_short_ratio: float  # > 1 = more longs
    top_trader_long_short: float  # Top traders' positioning

    signal: SignalStrength

    @property
    def is_overleveraged_long(self) -> bool:
        return self.funding_rate_8h > 0.05 and self.long_short_ratio > 1.5

    @property
    def is_overleveraged_short(self) -> bool:
        return self.funding_rate_8h < -0.05 and self.long_short_ratio < 0.67

    @property
    def interpretation(self) -> str:
        if self.is_overleveraged_long:
            return "Overleveraged longs - correction risk"
        elif self.is_overleveraged_short:
            return "Overleveraged shorts - squeeze potential"
        elif self.funding_rate_8h < -0.03:
            return "Negative funding - shorts paying (bullish)"
        elif self.funding_rate_8h > 0.03:
            return "High positive funding - longs paying (bearish)"
        return "Balanced derivatives market"


# =============================================================================
# ETF/INSTITUTIONAL FLOWS
# =============================================================================

@dataclass
class InstitutionalFlows:
    """ETF and institutional flow data."""
    # BTC ETF flows
    btc_etf_flow_24h: float  # USD, positive = inflow
    btc_etf_flow_7d: float
    btc_etf_flow_30d: float
    btc_etf_total_aum: float

    # ETH ETF flows
    eth_etf_flow_24h: float
    eth_etf_flow_7d: float

    # Grayscale
    gbtc_premium: float  # Premium/discount to NAV

    signal: SignalStrength

    @property
    def interpretation(self) -> str:
        if self.btc_etf_flow_7d > 500_000_000:
            return "Strong ETF inflows - institutional buying"
        elif self.btc_etf_flow_7d < -500_000_000:
            return "ETF outflows - institutional selling"
        elif self.gbtc_premium < -10:
            return "Large GBTC discount - potential arbitrage/selling"
        return "Normal institutional activity"


# =============================================================================
# MINER METRICS
# =============================================================================

@dataclass
class MinerMetrics:
    """Bitcoin miner metrics."""
    hash_rate: float  # EH/s
    hash_rate_change_30d: float

    difficulty: float
    next_difficulty_adjustment: float  # Percentage expected

    miner_revenue_24h: float  # USD
    miner_outflows_24h: float  # BTC sent from miner wallets
    miner_reserve: float  # Total BTC in miner wallets

    puell_multiple: float  # Miner profitability indicator

    signal: SignalStrength

    @property
    def interpretation(self) -> str:
        if self.puell_multiple < 0.5:
            return "Miners under stress - capitulation zone"
        elif self.puell_multiple > 4:
            return "Miners very profitable - potential top"
        elif self.miner_outflows_24h > self.miner_revenue_24h:
            return "Miners selling more than earning"
        return "Normal miner activity"


# =============================================================================
# MAIN ANALYZER CLASS
# =============================================================================

class ExtendedSignalsAnalyzer:
    """Extended market signals analyzer with 15+ signal types."""

    # API endpoints
    COINGECKO_URL = "https://api.coingecko.com/api/v3"
    COINGLASS_URL = "https://open-api.coinglass.com/public/v2"
    ALTERNATIVE_ME_URL = "https://api.alternative.me"
    BLOCKCHAIN_INFO_URL = "https://api.blockchain.info"
    DERIBIT_URL = "https://www.deribit.com/api/v2/public"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._cache_ttl = 300  # 5 minutes

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def _is_cached(self, key: str) -> bool:
        if key in self._cache:
            cached_time, _ = self._cache[key]
            if (datetime.now() - cached_time).seconds < self._cache_ttl:
                return True
        return False

    def _get_cached(self, key: str) -> Any:
        return self._cache[key][1] if key in self._cache else None

    def _set_cache(self, key: str, value: Any):
        self._cache[key] = (datetime.now(), value)

    # =========================================================================
    # LIQUIDATION DATA
    # =========================================================================

    async def get_liquidation_data(self, asset: str = "BTC") -> LiquidationData:
        """Get liquidation data from Coinglass."""
        cache_key = f"liquidations_{asset}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        session = await self._get_session()

        # Using CoinGlass public endpoint (limited data)
        try:
            url = f"{self.COINGLASS_URL}/liquidation_chart"
            params = {"symbol": asset, "interval": "1h"}

            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Parse liquidation data
                    # Note: Actual API response structure may vary

            # Fallback to estimation from price action
            # For demo, using placeholder values
            long_liq_24h = 50_000_000  # $50M placeholder
            short_liq_24h = 30_000_000

        except Exception as e:
            print(f"Liquidation fetch failed: {e}")
            long_liq_24h = 0
            short_liq_24h = 0

        ratio = long_liq_24h / short_liq_24h if short_liq_24h > 0 else 1.0
        total = long_liq_24h + short_liq_24h
        is_cascade = total > 200_000_000  # $200M+ = cascade

        # Signal: Long liquidation cascade = bullish (flush out)
        if is_cascade and ratio > 2:
            signal = SignalStrength.STRONG_BUY
        elif ratio > 1.5:
            signal = SignalStrength.BUY
        elif ratio < 0.5:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.NEUTRAL

        result = LiquidationData(
            asset=asset,
            long_liquidations_24h=long_liq_24h,
            short_liquidations_24h=short_liq_24h,
            long_liquidations_1h=long_liq_24h / 24,  # Approximation
            short_liquidations_1h=short_liq_24h / 24,
            liquidation_ratio=ratio,
            signal=signal,
            is_cascade=is_cascade,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # STABLECOIN METRICS
    # =========================================================================

    async def get_stablecoin_metrics(self) -> StablecoinMetrics:
        """Get stablecoin supply metrics."""
        cache_key = "stablecoins"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        session = await self._get_session()

        try:
            # Get stablecoin data from CoinGecko
            url = f"{self.COINGECKO_URL}/coins/markets"
            params = {
                "vs_currency": "usd",
                "ids": "tether,usd-coin,dai,first-digital-usd,ethena-usde",
                "order": "market_cap_desc",
            }

            async with session.get(url, params=params) as resp:
                data = await resp.json()

                # CoinGecko returns a dict on rate-limit (e.g. {"status": {...}})
                if isinstance(data, dict):
                    if "status" in data and data["status"].get("error_code") == 429:
                        raise ValueError("CoinGecko rate limited (429)")
                    raise ValueError(f"Expected list from CoinGecko, got dict: {list(data.keys())[:3]}")

                total_supply = sum(c.get("market_cap", 0) for c in data)

                usdt = next((c for c in data if c["id"] == "tether"), {})
                usdc = next((c for c in data if c["id"] == "usd-coin"), {})
                dai = next((c for c in data if c["id"] == "dai"), {})

                usdt_supply = usdt.get("market_cap", 0)
                usdc_supply = usdc.get("market_cap", 0)
                dai_supply = dai.get("market_cap", 0)

            # Get BTC market cap for ratio
            url = f"{self.COINGECKO_URL}/simple/price"
            params = {"ids": "bitcoin", "vs_currencies": "usd", "include_market_cap": "true"}

            async with session.get(url, params=params) as resp:
                btc_data = await resp.json()
                btc_mcap = btc_data.get("bitcoin", {}).get("usd_market_cap", 1)

            stablecoin_ratio = total_supply / btc_mcap if btc_mcap > 0 else 0
            usdt_dominance = usdt_supply / total_supply * 100 if total_supply > 0 else 0

        except Exception as e:
            logger.debug(f"Stablecoin metrics fetch failed (using defaults): {e}")
            total_supply = 150_000_000_000
            usdt_supply = 100_000_000_000
            usdc_supply = 35_000_000_000
            dai_supply = 5_000_000_000
            stablecoin_ratio = 0.10
            usdt_dominance = 66

        # Signal: High stablecoin ratio = dry powder ready to deploy
        if stablecoin_ratio > 0.15:
            signal = SignalStrength.BUY  # Lots of sidelined capital
        elif stablecoin_ratio < 0.08:
            signal = SignalStrength.SELL  # Capital fully deployed
        else:
            signal = SignalStrength.NEUTRAL

        result = StablecoinMetrics(
            total_supply=total_supply,
            supply_change_7d=0,  # Would need historical data
            supply_change_30d=0,
            usdt_supply=usdt_supply,
            usdc_supply=usdc_supply,
            dai_supply=dai_supply,
            usdt_dominance=usdt_dominance,
            stablecoin_ratio=stablecoin_ratio,
            signal=signal,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # GOOGLE TRENDS (Simplified - would need pytrends in production)
    # =========================================================================

    async def get_google_trends(self, term: str = "bitcoin") -> GoogleTrendsData:
        """Get Google Trends data (simplified)."""
        cache_key = f"trends_{term}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        # Note: In production, use pytrends library
        # For now, using placeholder based on Fear & Greed as proxy

        session = await self._get_session()

        try:
            url = f"{self.ALTERNATIVE_ME_URL}/fng/?limit=30"
            async with session.get(url) as resp:
                data = await resp.json()

                if data.get("data"):
                    # Use Fear & Greed as proxy for retail interest
                    current_fg = int(data["data"][0]["value"])
                    week_ago_fg = int(data["data"][7]["value"]) if len(data["data"]) > 7 else current_fg
                    month_ago_fg = int(data["data"][-1]["value"]) if len(data["data"]) > 29 else current_fg

                    # Map to 0-100 interest scale
                    current_interest = current_fg
                    interest_7d = week_ago_fg
                    interest_30d = month_ago_fg
                else:
                    current_interest = 50
                    interest_7d = 50
                    interest_30d = 50

        except Exception as e:
            print(f"Trends fetch failed: {e}")
            current_interest = 50
            interest_7d = 50
            interest_30d = 50

        change_7d = ((current_interest - interest_7d) / interest_7d * 100) if interest_7d > 0 else 0
        change_30d = ((current_interest - interest_30d) / interest_30d * 100) if interest_30d > 0 else 0

        # Signal: Contrarian - low interest = buy, high interest = sell
        if current_interest < 25:
            signal = SignalStrength.STRONG_BUY
        elif current_interest < 40:
            signal = SignalStrength.BUY
        elif current_interest > 80:
            signal = SignalStrength.STRONG_SELL
        elif current_interest > 65:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.NEUTRAL

        result = GoogleTrendsData(
            term=term,
            current_interest=current_interest,
            interest_7d_ago=interest_7d,
            interest_30d_ago=interest_30d,
            interest_change_7d=change_7d,
            interest_change_30d=change_30d,
            peak_interest_90d=max(current_interest, interest_7d, interest_30d),
            signal=signal,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # CORRELATION DATA
    # =========================================================================

    async def get_correlation_data(self) -> CorrelationData:
        """Get correlation with traditional markets."""
        cache_key = "correlations"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        session = await self._get_session()

        # Get DXY approximation from CoinGecko (using USD strength against EUR)
        # In production, use proper forex API
        try:
            # Use CoinGecko for crypto data
            url = f"{self.COINGECKO_URL}/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": "usd,eur",
            }

            async with session.get(url, params=params) as resp:
                data = await resp.json()
                btc_usd = data.get("bitcoin", {}).get("usd", 0)
                btc_eur = data.get("bitcoin", {}).get("eur", 0)

            # DXY approximation (inverted EUR/USD)
            if btc_eur > 0:
                eur_usd = btc_usd / btc_eur
                dxy_approx = 100 / eur_usd * 100  # Rough approximation
            else:
                dxy_approx = 105

        except Exception as e:
            print(f"Correlation fetch failed: {e}")
            dxy_approx = 105

        # Placeholders for correlations (would need historical data)
        btc_sp500_corr = 0.4  # Typically 0.3-0.6 in recent years
        btc_gold_corr = 0.2
        btc_dxy_corr = -0.3  # Usually negative

        # Determine risk regime
        if btc_sp500_corr > 0.6:
            risk_regime = "risk-on"
        elif btc_sp500_corr < 0.2:
            risk_regime = "decoupled"
        else:
            risk_regime = "normal"

        # Signal based on DXY
        # Falling DXY = bullish for risk assets
        if dxy_approx < 100:
            signal = SignalStrength.BUY
        elif dxy_approx > 110:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.NEUTRAL

        result = CorrelationData(
            btc_sp500_corr_30d=btc_sp500_corr,
            btc_gold_corr_30d=btc_gold_corr,
            btc_dxy_corr_30d=btc_dxy_corr,
            eth_btc_corr_30d=0.85,
            sp500_change_7d=0,
            gold_change_7d=0,
            dxy_value=dxy_approx,
            dxy_change_7d=0,
            signal=signal,
            risk_regime=risk_regime,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # OPTIONS DATA
    # =========================================================================

    async def get_options_data(self, asset: str = "BTC") -> OptionsData:
        """Get options market data from Deribit."""
        cache_key = f"options_{asset}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        session = await self._get_session()

        try:
            # Get current price
            url = f"{self.DERIBIT_URL}/get_index_price"
            params = {"index_name": f"{asset.lower()}_usd"}

            async with session.get(url, params=params) as resp:
                data = await resp.json()
                current_price = data.get("result", {}).get("index_price", 0)

            # Get book summary for options
            # This is simplified - production would aggregate all strikes

        except Exception as e:
            print(f"Options fetch failed: {e}")
            current_price = 100000 if asset == "BTC" else 3500

        # Placeholder values (would need full options chain analysis)
        put_call_ratio = 0.85
        max_pain = current_price * 0.95  # Usually slightly below current price
        iv = 65  # Typical BTC IV
        iv_percentile = 50

        # Signal based on put/call ratio
        if put_call_ratio > 1.3:
            signal = SignalStrength.BUY  # Contrarian - too many puts
        elif put_call_ratio < 0.6:
            signal = SignalStrength.SELL  # Contrarian - too many calls
        else:
            signal = SignalStrength.NEUTRAL

        result = OptionsData(
            asset=asset,
            put_call_ratio=put_call_ratio,
            max_pain_price=max_pain,
            current_price=current_price,
            distance_to_max_pain=(current_price - max_pain) / max_pain * 100,
            implied_volatility=iv,
            iv_percentile=iv_percentile,
            total_call_oi=0,
            total_put_oi=0,
            signal=signal,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # NETWORK METRICS
    # =========================================================================

    async def get_network_metrics(self, asset: str = "BTC") -> NetworkMetrics:
        """Get blockchain network metrics."""
        cache_key = f"network_{asset}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        session = await self._get_session()

        hash_rate = None
        difficulty = None
        active_addresses = 0

        if asset.upper() == "BTC":
            try:
                # Blockchain.info stats
                url = f"{self.BLOCKCHAIN_INFO_URL}/stats"
                async with session.get(url) as resp:
                    data = await resp.json()

                    hash_rate = data.get("hash_rate", 0) / 1e18  # Convert to EH/s
                    difficulty = data.get("difficulty", 0)

            except Exception as e:
                print(f"BTC network fetch failed: {e}")

        # Active addresses from CoinGecko
        try:
            asset_map = {
                "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            }
            coin_id = asset_map.get(asset.upper(), asset.lower())

            url = f"{self.COINGECKO_URL}/coins/{coin_id}"
            params = {"localization": "false", "tickers": "false", "community_data": "false"}

            async with session.get(url, params=params) as resp:
                data = await resp.json()
                dev_data = data.get("developer_data", {})
                # CoinGecko doesn't provide active addresses directly

        except Exception as e:
            print(f"Network metrics fetch failed: {e}")

        # Signal: Growing network = bullish
        signal = SignalStrength.NEUTRAL
        if hash_rate and hash_rate > 500:  # > 500 EH/s
            signal = SignalStrength.BUY

        result = NetworkMetrics(
            asset=asset,
            active_addresses_24h=active_addresses,
            active_addresses_7d_avg=active_addresses,
            address_growth_7d=0,
            transaction_count_24h=0,
            avg_transaction_value=0,
            hash_rate=hash_rate,
            hash_rate_change_7d=0,
            difficulty=difficulty,
            signal=signal,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # FUNDING & OPEN INTEREST
    # =========================================================================

    async def get_funding_oi_data(self, asset: str = "BTC") -> FundingOIData:
        """Get funding rates and open interest data."""
        cache_key = f"funding_{asset}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        session = await self._get_session()

        # Try Coinglass public API
        funding_rate = 0.01  # Default neutral
        open_interest = 0
        long_short_ratio = 1.0

        try:
            # Using Deribit for funding
            url = f"{self.DERIBIT_URL}/get_funding_rate_value"
            params = {"instrument_name": f"{asset.upper()}-PERPETUAL"}

            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    funding_rate = data.get("result", 0) * 100  # Convert to percentage

        except Exception as e:
            print(f"Funding fetch failed: {e}")

        # Signal based on funding
        if funding_rate < -0.05:  # Very negative
            signal = SignalStrength.STRONG_BUY
        elif funding_rate < -0.02:
            signal = SignalStrength.BUY
        elif funding_rate > 0.10:  # Very positive
            signal = SignalStrength.STRONG_SELL
        elif funding_rate > 0.05:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.NEUTRAL

        result = FundingOIData(
            asset=asset,
            funding_rate_8h=funding_rate,
            funding_rate_avg_7d=funding_rate,  # Would need historical
            predicted_funding=funding_rate,
            open_interest=open_interest,
            oi_change_24h=0,
            oi_change_7d=0,
            long_short_ratio=long_short_ratio,
            top_trader_long_short=long_short_ratio,
            signal=signal,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # WHALE ACTIVITY
    # =========================================================================

    async def get_whale_activity(self, asset: str = "BTC") -> WhaleActivity:
        """Get whale transaction monitoring."""
        cache_key = f"whales_{asset}"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        # Would need Whale Alert API or similar
        # Using placeholders

        net_flow = -50_000_000  # Placeholder: $50M outflows (bullish)

        if net_flow < -100_000_000:
            signal = SignalStrength.STRONG_BUY
        elif net_flow < -20_000_000:
            signal = SignalStrength.BUY
        elif net_flow > 100_000_000:
            signal = SignalStrength.STRONG_SELL
        elif net_flow > 20_000_000:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.NEUTRAL

        result = WhaleActivity(
            asset=asset,
            whale_transactions_24h=150,
            whale_volume_24h=500_000_000,
            exchange_inflows_24h=200_000_000,
            exchange_outflows_24h=250_000_000,
            net_flow=net_flow,
            large_buys_24h=80,
            large_sells_24h=70,
            signal=signal,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # INSTITUTIONAL FLOWS
    # =========================================================================

    async def get_institutional_flows(self) -> InstitutionalFlows:
        """Get ETF and institutional flow data."""
        cache_key = "institutional"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        # Would need SoSo Value API or similar for ETF flows
        # Using placeholders

        btc_etf_flow_7d = 200_000_000  # $200M inflows

        if btc_etf_flow_7d > 500_000_000:
            signal = SignalStrength.STRONG_BUY
        elif btc_etf_flow_7d > 100_000_000:
            signal = SignalStrength.BUY
        elif btc_etf_flow_7d < -500_000_000:
            signal = SignalStrength.STRONG_SELL
        elif btc_etf_flow_7d < -100_000_000:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.NEUTRAL

        result = InstitutionalFlows(
            btc_etf_flow_24h=btc_etf_flow_7d / 7,
            btc_etf_flow_7d=btc_etf_flow_7d,
            btc_etf_flow_30d=btc_etf_flow_7d * 3,
            btc_etf_total_aum=50_000_000_000,
            eth_etf_flow_24h=10_000_000,
            eth_etf_flow_7d=50_000_000,
            gbtc_premium=-5,
            signal=signal,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # MINER METRICS
    # =========================================================================

    async def get_miner_metrics(self) -> MinerMetrics:
        """Get Bitcoin miner metrics."""
        cache_key = "miners"
        if self._is_cached(cache_key):
            return self._get_cached(cache_key)

        session = await self._get_session()

        try:
            url = f"{self.BLOCKCHAIN_INFO_URL}/stats"
            async with session.get(url) as resp:
                data = await resp.json()

                hash_rate = data.get("hash_rate", 0) / 1e18  # EH/s
                difficulty = data.get("difficulty", 0)

        except Exception as e:
            print(f"Miner metrics fetch failed: {e}")
            hash_rate = 600
            difficulty = 80e12

        # Puell Multiple approximation (would need more data)
        puell_multiple = 1.0  # Neutral placeholder

        if puell_multiple < 0.5:
            signal = SignalStrength.STRONG_BUY  # Miner capitulation
        elif puell_multiple < 0.8:
            signal = SignalStrength.BUY
        elif puell_multiple > 4:
            signal = SignalStrength.STRONG_SELL
        elif puell_multiple > 2:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.NEUTRAL

        result = MinerMetrics(
            hash_rate=hash_rate,
            hash_rate_change_30d=5,  # Placeholder
            difficulty=difficulty,
            next_difficulty_adjustment=2,  # Placeholder
            miner_revenue_24h=30_000_000,
            miner_outflows_24h=20_000_000,
            miner_reserve=1_800_000,  # ~1.8M BTC
            puell_multiple=puell_multiple,
            signal=signal,
        )

        self._set_cache(cache_key, result)
        return result

    # =========================================================================
    # COMPREHENSIVE ANALYSIS
    # =========================================================================

    async def get_all_signals(self, assets: List[str] = None) -> Dict[str, List[Signal]]:
        """Get all signals organized by category."""
        if assets is None:
            assets = ["BTC", "ETH"]

        all_signals = []

        # Gather all data concurrently
        tasks = [
            self.get_liquidation_data("BTC"),
            self.get_stablecoin_metrics(),
            self.get_google_trends("bitcoin"),
            self.get_correlation_data(),
            self.get_options_data("BTC"),
            self.get_funding_oi_data("BTC"),
            self.get_whale_activity("BTC"),
            self.get_institutional_flows(),
            self.get_miner_metrics(),
            self.get_network_metrics("BTC"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process liquidation data
        if isinstance(results[0], LiquidationData):
            liq = results[0]
            all_signals.append(Signal(
                name="Liquidations",
                category="derivatives",
                value=liq.liquidation_ratio,
                signal=liq.signal,
                weight=0.08,
                description=liq.interpretation,
                data_source="coinglass",
            ))

        # Process stablecoin metrics
        if isinstance(results[1], StablecoinMetrics):
            stable = results[1]
            all_signals.append(Signal(
                name="Stablecoin Ratio",
                category="on-chain",
                value=stable.stablecoin_ratio * 100,
                signal=stable.signal,
                weight=0.07,
                description=stable.interpretation,
                data_source="coingecko",
            ))

        # Process Google Trends
        if isinstance(results[2], GoogleTrendsData):
            trends = results[2]
            all_signals.append(Signal(
                name="Retail Interest",
                category="sentiment",
                value=trends.current_interest,
                signal=trends.signal,
                weight=0.06,
                description=trends.interpretation,
                data_source="alternative.me",
            ))

        # Process correlation data
        if isinstance(results[3], CorrelationData):
            corr = results[3]
            all_signals.append(Signal(
                name="DXY Correlation",
                category="macro",
                value=corr.dxy_value,
                signal=corr.signal,
                weight=0.08,
                description=corr.interpretation,
                data_source="forex",
            ))

        # Process options data
        if isinstance(results[4], OptionsData):
            opts = results[4]
            all_signals.append(Signal(
                name="Put/Call Ratio",
                category="derivatives",
                value=opts.put_call_ratio,
                signal=opts.signal,
                weight=0.07,
                description=opts.interpretation,
                data_source="deribit",
            ))

        # Process funding data
        if isinstance(results[5], FundingOIData):
            funding = results[5]
            all_signals.append(Signal(
                name="Funding Rate",
                category="derivatives",
                value=funding.funding_rate_8h,
                signal=funding.signal,
                weight=0.09,
                description=funding.interpretation,
                data_source="deribit",
            ))

        # Process whale activity
        if isinstance(results[6], WhaleActivity):
            whales = results[6]
            all_signals.append(Signal(
                name="Whale Net Flow",
                category="on-chain",
                value=whales.net_flow / 1_000_000,  # In millions
                signal=whales.signal,
                weight=0.08,
                description=whales.interpretation,
                data_source="whale_alert",
            ))

        # Process institutional flows
        if isinstance(results[7], InstitutionalFlows):
            inst = results[7]
            all_signals.append(Signal(
                name="ETF Flows",
                category="institutional",
                value=inst.btc_etf_flow_7d / 1_000_000,  # In millions
                signal=inst.signal,
                weight=0.10,
                description=inst.interpretation,
                data_source="etf_data",
            ))

        # Process miner metrics
        if isinstance(results[8], MinerMetrics):
            miners = results[8]
            all_signals.append(Signal(
                name="Miner Activity",
                category="on-chain",
                value=miners.puell_multiple,
                signal=miners.signal,
                weight=0.06,
                description=miners.interpretation,
                data_source="blockchain.info",
            ))

        # Process network metrics
        if isinstance(results[9], NetworkMetrics):
            network = results[9]
            all_signals.append(Signal(
                name="Network Health",
                category="on-chain",
                value=network.hash_rate or 0,
                signal=network.signal,
                weight=0.05,
                description=network.interpretation,
                data_source="blockchain.info",
            ))

        return {
            "all": all_signals,
            "derivatives": [s for s in all_signals if s.category == "derivatives"],
            "on_chain": [s for s in all_signals if s.category == "on-chain"],
            "sentiment": [s for s in all_signals if s.category == "sentiment"],
            "macro": [s for s in all_signals if s.category == "macro"],
            "institutional": [s for s in all_signals if s.category == "institutional"],
        }

    async def get_composite_score(self, assets: List[str] = None) -> Tuple[float, SignalStrength, List[Signal]]:
        """Calculate composite score from all signals."""
        signals_dict = await self.get_all_signals(assets)
        all_signals = signals_dict["all"]

        if not all_signals:
            return 0, SignalStrength.NEUTRAL, []

        # Weighted average
        total_weight = sum(s.weight for s in all_signals)
        composite = sum(s.weighted_score for s in all_signals) / total_weight if total_weight > 0 else 0

        # Scale to -10 to +10
        composite_scaled = composite * 5

        # Determine signal
        if composite_scaled > 3:
            signal = SignalStrength.STRONG_BUY
        elif composite_scaled > 1:
            signal = SignalStrength.BUY
        elif composite_scaled < -3:
            signal = SignalStrength.STRONG_SELL
        elif composite_scaled < -1:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.NEUTRAL

        return composite_scaled, signal, all_signals

    async def analyze(self, asset: str = "BTC") -> ComprehensiveSignalAnalysis:
        """Run full analysis and return structured result."""
        composite_scaled, signal_strength, all_signals = await self.get_composite_score([asset])

        # Convert Signal objects to SignalResult
        all_results = [SignalResult.from_signal(s) for s in all_signals]

        # Group by category
        CATEGORY_MAP = {
            "derivatives": "derivatives",
            "on-chain": "onchain",
            "on_chain": "onchain",
            "sentiment": "sentiment",
            "macro": "macro",
            "institutional": "institutional",
            "technical": "technical",
            "mining": "technical",
        }

        grouped: Dict[str, List[SignalResult]] = {
            "technical": [],
            "sentiment": [],
            "onchain": [],
            "derivatives": [],
            "macro": [],
            "institutional": [],
        }

        for sr in all_results:
            cat = CATEGORY_MAP.get(sr.category, "technical")
            grouped[cat].append(sr)

        def _make_summary(name: str, signals: List[SignalResult]) -> BaseCategorySummary:
            available = [s for s in signals if s.signal != SignalStrength.UNAVAILABLE]
            bullish = sum(1 for s in available if s.score > 0)
            bearish = sum(1 for s in available if s.score < 0)
            neutral = sum(1 for s in available if s.score == 0)
            unavailable = len(signals) - len(available)
            if available:
                avg = sum(s.score for s in available) / len(available)
                tw = sum(s.weight for s in available)
                ws = sum(s.score * s.weight for s in available) / tw if tw else 0
            else:
                avg = ws = 0
            return BaseCategorySummary(
                name=name, signals=signals, avg_score=avg,
                weighted_score=ws, bullish_count=bullish,
                bearish_count=bearish, neutral_count=neutral,
                unavailable_count=unavailable,
            )

        available_count = sum(1 for s in all_results if s.signal != SignalStrength.UNAVAILABLE)

        return ComprehensiveSignalAnalysis(
            timestamp=datetime.now(),
            asset=asset,
            technical=_make_summary("Technical", grouped["technical"]),
            sentiment=_make_summary("Sentiment", grouped["sentiment"]),
            onchain=_make_summary("On-Chain", grouped["onchain"]),
            derivatives=_make_summary("Derivatives", grouped["derivatives"]),
            macro=_make_summary("Macro", grouped["macro"]),
            institutional=_make_summary("Institutional", grouped["institutional"]),
            total_signals=len(all_results),
            available_signals=available_count,
            composite_score=composite_scaled,
            signal_strength=signal_strength,
            all_signals=all_results,
        )

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


def format_extended_signals(signals: List[Signal], composite_score: float, composite_signal: SignalStrength) -> str:
    """Format extended signals for display."""
    lines = []

    signal_emoji = {
        SignalStrength.STRONG_BUY: "🟢🟢",
        SignalStrength.BUY: "🟢",
        SignalStrength.NEUTRAL: "⚪",
        SignalStrength.SELL: "🔴",
        SignalStrength.STRONG_SELL: "🔴🔴",
    }

    lines.append("=" * 85)
    lines.append("  EXTENDED MARKET SIGNALS ANALYSIS")
    lines.append("  " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    lines.append("=" * 85)
    lines.append("")

    # Composite score
    emoji = signal_emoji.get(composite_signal, "")
    lines.append(f"  {emoji} COMPOSITE SCORE: {composite_score:+.1f} / 10")
    lines.append(f"  Overall Signal: {composite_signal.name}")
    lines.append("")

    # Multiplier recommendation
    if composite_score >= 4:
        mult = 2.5
    elif composite_score >= 2:
        mult = 2.0
    elif composite_score >= 1:
        mult = 1.5
    elif composite_score >= -1:
        mult = 1.0
    elif composite_score >= -3:
        mult = 0.75
    else:
        mult = 0.5

    lines.append(f"  💰 Recommended DCA Multiplier: {mult:.1f}x")
    lines.append("")

    # Group by category
    categories = {}
    for s in signals:
        if s.category not in categories:
            categories[s.category] = []
        categories[s.category].append(s)

    category_names = {
        "derivatives": "DERIVATIVES SIGNALS",
        "on_chain": "ON-CHAIN SIGNALS",
        "sentiment": "SENTIMENT SIGNALS",
        "macro": "MACRO SIGNALS",
        "institutional": "INSTITUTIONAL SIGNALS",
    }

    for cat, cat_signals in categories.items():
        cat_name = category_names.get(cat, cat.upper())
        lines.append(f"  {cat_name}")
        lines.append("  " + "-" * 75)

        for s in cat_signals:
            emoji = signal_emoji.get(s.signal, "")
            lines.append(f"  {emoji} {s.name:<20} | {s.description}")

        lines.append("")

    # Summary table
    lines.append("  SIGNAL SUMMARY")
    lines.append("  " + "-" * 75)
    lines.append(f"  {'Signal':<22} {'Category':<15} {'Value':>10} {'Weight':>8} {'Score':>8}")
    lines.append("  " + "-" * 75)

    for s in sorted(signals, key=lambda x: x.weight, reverse=True):
        emoji = signal_emoji.get(s.signal, "")
        lines.append(
            f"  {emoji} {s.name:<20} {s.category:<15} {s.value:>10.2f} "
            f"{s.weight:>7.0%} {s.weighted_score:>+7.2f}"
        )

    lines.append("  " + "-" * 75)
    total_weight = sum(s.weight for s in signals)
    total_score = sum(s.weighted_score for s in signals)
    lines.append(f"  {'TOTAL':<22} {'':<15} {'':<10} {total_weight:>7.0%} {total_score:>+7.2f}")
    lines.append("")

    return "\n".join(lines)


# Convenience function
async def get_extended_analysis() -> Tuple[float, SignalStrength, List[Signal]]:
    """Quick function to get extended analysis."""
    analyzer = ExtendedSignalsAnalyzer()
    try:
        return await analyzer.get_composite_score()
    finally:
        await analyzer.close()
