"""
GTI Virtual ETF Configuration
==============================

Defines the 25+1 asset virtual ETF for GTI Inc, including:
- Asset allocations by category
- Exchange routing rules
- War chest deployment thresholds
- Rebalance parameters

Budget: $40/day total
  - GTI ETF (business accounts): $28/day (70%)
  - Personal day/swing trading: $12/day (30%)
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional


class AssetCategory(str, Enum):
    CORE = "core"
    INCOME = "income"
    LAND_RWA = "land_rwa"
    GROWTH_AI = "growth_ai"
    HIGH_RISK = "high_risk"
    WAR_CHEST = "war_chest"


class ExchangeRoute(str, Enum):
    KRAKEN_BUSINESS = "kraken_business"
    COINBASE_GTI = "coinbase_gti"
    DEX = "dex"


@dataclass(frozen=True)
class ETFAsset:
    """Single asset in the ETF."""
    symbol: str
    category: AssetCategory
    target_weight_pct: Decimal
    exchange: ExchangeRoute
    stakeable: bool = False
    expected_apy: Optional[Decimal] = None
    min_trade_usd: Decimal = Decimal("1.00")
    coingecko_id: Optional[str] = None


# ---------------------------------------------------------------------------
# ETF Asset Definitions (25 crypto + 1 stablecoin = 26 total)
# ---------------------------------------------------------------------------

ETF_ASSETS: Dict[str, ETFAsset] = {}

def _register(*assets: ETFAsset):
    for a in assets:
        ETF_ASSETS[a.symbol] = a

# --- Core (4 assets, 20%) ---
_register(
    ETFAsset("BTC",  AssetCategory.CORE, Decimal("10"), ExchangeRoute.COINBASE_GTI, coingecko_id="bitcoin"),
    ETFAsset("ETH",  AssetCategory.CORE, Decimal("5"),  ExchangeRoute.KRAKEN_BUSINESS, stakeable=True, expected_apy=Decimal("3.5"), coingecko_id="ethereum"),
    ETFAsset("SOL",  AssetCategory.CORE, Decimal("3"),  ExchangeRoute.COINBASE_GTI, coingecko_id="solana"),
    ETFAsset("AVAX", AssetCategory.CORE, Decimal("2"),  ExchangeRoute.COINBASE_GTI, coingecko_id="avalanche-2"),
)

# --- Income/Staking (6 assets, 25%) ---
_register(
    ETFAsset("TRX",  AssetCategory.INCOME, Decimal("5"), ExchangeRoute.KRAKEN_BUSINESS, stakeable=True, expected_apy=Decimal("4.5"), coingecko_id="tron"),
    ETFAsset("ATOM", AssetCategory.INCOME, Decimal("5"), ExchangeRoute.KRAKEN_BUSINESS, stakeable=True, expected_apy=Decimal("17"), coingecko_id="cosmos"),
    ETFAsset("DOT",  AssetCategory.INCOME, Decimal("4"), ExchangeRoute.KRAKEN_BUSINESS, stakeable=True, expected_apy=Decimal("12"), coingecko_id="polkadot"),
    ETFAsset("ADA",  AssetCategory.INCOME, Decimal("4"), ExchangeRoute.KRAKEN_BUSINESS, stakeable=True, expected_apy=Decimal("3.5"), coingecko_id="cardano"),
    ETFAsset("XRP",  AssetCategory.INCOME, Decimal("4"), ExchangeRoute.COINBASE_GTI, coingecko_id="ripple"),
    ETFAsset("HBAR", AssetCategory.INCOME, Decimal("3"), ExchangeRoute.COINBASE_GTI, coingecko_id="hedera-hashgraph"),
)

# --- Land/RWA (3 assets, 10%) ---
_register(
    ETFAsset("MANA", AssetCategory.LAND_RWA, Decimal("4"), ExchangeRoute.COINBASE_GTI, coingecko_id="decentraland"),
    ETFAsset("SAND", AssetCategory.LAND_RWA, Decimal("3"), ExchangeRoute.COINBASE_GTI, coingecko_id="the-sandbox"),
    ETFAsset("ONDO", AssetCategory.LAND_RWA, Decimal("3"), ExchangeRoute.COINBASE_GTI, coingecko_id="ondo-finance"),
)

# --- Growth/AI (5 assets, 15%) ---
_register(
    ETFAsset("LINK",   AssetCategory.GROWTH_AI, Decimal("3"), ExchangeRoute.COINBASE_GTI, coingecko_id="chainlink"),
    ETFAsset("NEAR",   AssetCategory.GROWTH_AI, Decimal("3"), ExchangeRoute.COINBASE_GTI, coingecko_id="near"),
    ETFAsset("SUI",    AssetCategory.GROWTH_AI, Decimal("3"), ExchangeRoute.COINBASE_GTI, coingecko_id="sui"),
    ETFAsset("RENDER", AssetCategory.GROWTH_AI, Decimal("3"), ExchangeRoute.COINBASE_GTI, coingecko_id="render-token"),
    ETFAsset("FET",    AssetCategory.GROWTH_AI, Decimal("3"), ExchangeRoute.COINBASE_GTI, coingecko_id="fetch-ai"),
)

# --- High Risk (6 assets, 15%) ---
_register(
    ETFAsset("XTZ",  AssetCategory.HIGH_RISK, Decimal("3"),   ExchangeRoute.COINBASE_GTI, coingecko_id="tezos"),
    ETFAsset("LTC",  AssetCategory.HIGH_RISK, Decimal("3"),   ExchangeRoute.COINBASE_GTI, coingecko_id="litecoin"),
    ETFAsset("ALGO", AssetCategory.HIGH_RISK, Decimal("2.5"), ExchangeRoute.COINBASE_GTI, coingecko_id="algorand"),
    ETFAsset("POL",  AssetCategory.HIGH_RISK, Decimal("2.5"), ExchangeRoute.COINBASE_GTI, coingecko_id="polygon-ecosystem-token"),
    ETFAsset("DOGE", AssetCategory.HIGH_RISK, Decimal("2"),   ExchangeRoute.COINBASE_GTI, coingecko_id="dogecoin"),
    ETFAsset("ARB",  AssetCategory.HIGH_RISK, Decimal("2"),   ExchangeRoute.COINBASE_GTI, coingecko_id="arbitrum"),
)

# --- War Chest (1 asset, 15%) ---
_register(
    ETFAsset("USDC", AssetCategory.WAR_CHEST, Decimal("15"), ExchangeRoute.COINBASE_GTI,
             coingecko_id="usd-coin"),
)


# ---------------------------------------------------------------------------
# Budget Configuration
# ---------------------------------------------------------------------------

DAILY_BUDGET_TOTAL = Decimal("40")
ETF_DAILY_BUDGET = Decimal("28")       # 70% for GTI ETF (business)
PERSONAL_DAILY_BUDGET = Decimal("12")   # 30% for personal day/swing trading

CATEGORY_DAILY_ALLOCATIONS: Dict[AssetCategory, Decimal] = {
    AssetCategory.CORE:      Decimal("5.60"),   # 20% of $28
    AssetCategory.INCOME:    Decimal("7.00"),   # 25% of $28
    AssetCategory.LAND_RWA:  Decimal("2.80"),   # 10% of $28
    AssetCategory.GROWTH_AI: Decimal("4.20"),   # 15% of $28
    AssetCategory.HIGH_RISK: Decimal("4.20"),   # 15% of $28
    AssetCategory.WAR_CHEST: Decimal("4.20"),   # 15% of $28
}


# ---------------------------------------------------------------------------
# War Chest Thresholds (Fear & Greed Index)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WarChestRule:
    """Defines behavior at a given Fear & Greed range."""
    fg_min: int
    fg_max: int
    target_usdc_pct: Decimal      # target USDC allocation
    deploy_pct: Decimal           # % of war chest to deploy
    dca_multiplier: Decimal       # multiplier on underweight asset DCA
    label: str

WAR_CHEST_RULES: List[WarChestRule] = [
    WarChestRule(0,  14, Decimal("15"), Decimal("75"), Decimal("3.0"), "extreme_fear"),
    WarChestRule(15, 34, Decimal("15"), Decimal("50"), Decimal("2.0"), "fear"),
    WarChestRule(35, 64, Decimal("15"), Decimal("0"),  Decimal("1.0"), "normal"),
    WarChestRule(65, 79, Decimal("22"), Decimal("0"),  Decimal("0.7"), "greed"),
    WarChestRule(80, 100, Decimal("28"), Decimal("0"), Decimal("0.5"), "extreme_greed"),
]


def get_war_chest_rule(fear_greed: int) -> WarChestRule:
    """Return the war chest rule for a given Fear & Greed index value."""
    for rule in WAR_CHEST_RULES:
        if rule.fg_min <= fear_greed <= rule.fg_max:
            return rule
    return WAR_CHEST_RULES[2]  # default to normal


# ---------------------------------------------------------------------------
# Rebalance Parameters
# ---------------------------------------------------------------------------

REBALANCE_BAND_PCT = Decimal("3")  # trigger rebalance when drift exceeds +/-3%
MIN_ORDER_USD = Decimal("0.50")    # minimum order size (Coinbase/Kraken support sub-$1)


# ---------------------------------------------------------------------------
# Locked Assets (counted in ETF but not rebalanced via new buys)
# ---------------------------------------------------------------------------

LOCKED_ASSETS = frozenset({
    "TRX",  # Already staked on Kraken, no rebalance
})


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_assets_by_category(category: AssetCategory) -> List[ETFAsset]:
    """Return all ETF assets in a given category."""
    return [a for a in ETF_ASSETS.values() if a.category == category]


def get_assets_by_exchange(exchange: ExchangeRoute) -> List[ETFAsset]:
    """Return all ETF assets routed to a given exchange."""
    return [a for a in ETF_ASSETS.values() if a.exchange == exchange]


def get_stakeable_assets() -> List[ETFAsset]:
    """Return all stakeable ETF assets."""
    return [a for a in ETF_ASSETS.values() if a.stakeable]


def validate_weights() -> bool:
    """Verify all weights sum to 100%."""
    total = sum(a.target_weight_pct for a in ETF_ASSETS.values())
    return total == Decimal("100")


def get_coingecko_ids() -> Dict[str, str]:
    """Return symbol -> CoinGecko ID mapping for all ETF assets."""
    return {
        a.symbol: a.coingecko_id
        for a in ETF_ASSETS.values()
        if a.coingecko_id
    }
