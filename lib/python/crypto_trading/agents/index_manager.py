"""
Index Manager Module
====================
COIN50-style index management for 100+ crypto assets.
Handles eligibility screening, portfolio construction, personal/business allocation,
rebalancing, and importing holdings from files.
"""

import asyncio
import aiohttp
import csv
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set, Any
from pathlib import Path


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class AccountType(Enum):
    """Which account an asset should be held in"""
    PERSONAL = "personal"      # Coinbase One - 0% fees, higher staking
    BUSINESS = "business"      # Kraken - treasury, long-term
    SPLIT = "split"           # Both accounts
    EXCLUDED = "excluded"     # Didn't pass filters


class ExclusionReason(Enum):
    """Why an asset was excluded from the index"""
    MARKET_CAP_TOO_LOW = "Market cap below minimum"
    AGE_TOO_YOUNG = "Less than 360 days old"
    STABLECOIN = "Stablecoin excluded"
    WRAPPED_ASSET = "Wrapped/pegged asset"
    EXCHANGE_TOKEN = "Exchange token excluded"
    PRIVACY_COIN = "Privacy coin excluded"
    LOW_VOLUME = "Daily volume too low"
    NOT_ON_EXCHANGE = "Not listed on required exchange"
    SECURITY_CONCERN = "Known security issues"
    MANUAL_EXCLUDE = "Manually excluded"


@dataclass
class AssetData:
    """Raw data for a single asset"""
    symbol: str
    name: str
    market_cap: Decimal
    price: Decimal
    volume_24h: Decimal
    price_change_24h: float = 0.0
    price_change_7d: float = 0.0
    price_change_30d: float = 0.0
    circulating_supply: Decimal = Decimal("0")
    total_supply: Optional[Decimal] = None
    max_supply: Optional[Decimal] = None
    ath: Decimal = Decimal("0")
    ath_date: Optional[datetime] = None
    atl: Decimal = Decimal("0")
    atl_date: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    genesis_date: Optional[datetime] = None
    categories: List[str] = field(default_factory=list)
    on_coinbase: bool = True
    on_kraken: bool = True
    staking_apy_coinbase: Optional[float] = None
    staking_apy_kraken: Optional[float] = None


@dataclass 
class AssetScore:
    """Scoring for personal vs business allocation"""
    symbol: str
    
    # Raw scores (1-5)
    treasury_suitability: int = 3    # 1=speculative, 5=store of value
    regulatory_clarity: int = 3       # 1=uncertain, 5=clear
    institutional_adoption: int = 3   # 1=retail only, 5=institutions hold
    volatility: int = 3               # 1=stable, 5=highly volatile
    staking_advantage: int = 3        # 1=same/none, 5=much better personal
    trade_frequency: int = 3          # 1=hold forever, 5=trade often
    speculation_level: int = 3        # 1=blue chip, 5=moonshot
    
    @property
    def personal_score(self) -> float:
        """Higher = more suited for personal account"""
        return (
            self.volatility * 1.5 +
            self.staking_advantage * 2.0 +
            self.trade_frequency * 1.5 +
            self.speculation_level * 1.0
        ) / 6.0
    
    @property
    def business_score(self) -> float:
        """Higher = more suited for business account"""
        return (
            self.treasury_suitability * 2.0 +
            self.regulatory_clarity * 1.5 +
            self.institutional_adoption * 1.5 +
            (6 - self.volatility) * 1.0
        ) / 6.0
    
    @property
    def recommended_account(self) -> AccountType:
        """Determine which account based on scores"""
        diff = self.business_score - self.personal_score
        if diff > 0.5:
            return AccountType.BUSINESS
        elif diff < -0.5:
            return AccountType.PERSONAL
        else:
            return AccountType.SPLIT


@dataclass
class HoldingRecord:
    """A holding from imported file"""
    symbol: str
    quantity: Decimal = Decimal("0")
    current_value: Decimal = Decimal("0")
    cost_basis: Optional[Decimal] = None
    account: Optional[str] = None
    notes: str = ""


@dataclass
class IndexAsset:
    """An asset that's part of the index"""
    symbol: str
    name: str
    data: AssetData
    score: AssetScore
    
    rank: int = 0
    raw_weight: Decimal = Decimal("0")
    capped_weight: Decimal = Decimal("0")
    
    account: AccountType = AccountType.PERSONAL
    personal_weight: Decimal = Decimal("0")
    business_weight: Decimal = Decimal("0")
    
    current_quantity: Decimal = Decimal("0")
    current_value: Decimal = Decimal("0")
    target_value: Decimal = Decimal("0")
    target_quantity: Decimal = Decimal("0")
    
    @property
    def drift_pct(self) -> float:
        if self.target_value == 0:
            return float(self.current_value) * 100 if self.current_value > 0 else 0
        return float((self.current_value - self.target_value) / self.target_value * 100)
    
    @property
    def trade_needed(self) -> Decimal:
        return self.target_value - self.current_value


@dataclass
class ExcludedAsset:
    """An asset excluded from the index"""
    symbol: str
    name: str
    reason: ExclusionReason
    market_cap: Optional[Decimal] = None
    detail: str = ""
    current_value: Decimal = Decimal("0")


@dataclass
class IndexConfig:
    """Configuration for index construction"""
    target_count: int = 50
    auto_select_count: int = 40
    buffer_range: Tuple[int, int] = (41, 60)
    
    min_market_cap: Decimal = Decimal("100000000")
    min_age_days: int = 360
    min_daily_volume: Decimal = Decimal("1000000")
    
    max_weight_pct: Decimal = Decimal("40")
    min_weight_pct: Decimal = Decimal("0.5")
    
    personal_target_pct: Decimal = Decimal("40")
    business_target_pct: Decimal = Decimal("60")
    
    exclude_stablecoins: bool = True
    exclude_wrapped: bool = True
    exclude_exchange_tokens: bool = True
    exclude_privacy_coins: bool = True
    
    require_coinbase: bool = False
    require_kraken: bool = False
    
    manual_exclusions: Set[str] = field(default_factory=set)
    
    rebalance_threshold_pct: float = 5.0
    min_trade_value: Decimal = Decimal("25")


@dataclass
class IndexPortfolio:
    """Complete index portfolio"""
    name: str
    config: IndexConfig
    created_at: datetime
    
    assets: List[IndexAsset] = field(default_factory=list)
    excluded: List[ExcludedAsset] = field(default_factory=list)
    
    personal_assets: List[IndexAsset] = field(default_factory=list)
    business_assets: List[IndexAsset] = field(default_factory=list)
    
    total_value: Decimal = Decimal("0")
    personal_value: Decimal = Decimal("0")
    business_value: Decimal = Decimal("0")
    
    holdings_imported: int = 0
    holdings_matched: int = 0
    holdings_unmatched: List[str] = field(default_factory=list)
    
    @property
    def asset_count(self) -> int:
        return len(self.assets)
    
    @property
    def personal_count(self) -> int:
        return len(self.personal_assets)
    
    @property
    def business_count(self) -> int:
        return len(self.business_assets)


@dataclass
class RebalanceAction:
    """A single rebalancing trade"""
    symbol: str
    account: AccountType
    action: str
    quantity: Decimal
    value: Decimal
    current_value: Decimal
    target_value: Decimal
    reason: str
    priority: int = 0


@dataclass
class RebalancePlan:
    """Complete rebalancing plan"""
    generated_at: datetime
    personal_actions: List[RebalanceAction] = field(default_factory=list)
    business_actions: List[RebalanceAction] = field(default_factory=list)
    
    total_buys: Decimal = Decimal("0")
    total_sells: Decimal = Decimal("0")
    estimated_fees_personal: Decimal = Decimal("0")
    estimated_fees_business: Decimal = Decimal("0")
    
    assets_to_liquidate: List[str] = field(default_factory=list)
    
    @property
    def net_flow(self) -> Decimal:
        return self.total_buys - self.total_sells


# ============================================================================
# KNOWN ASSET CLASSIFICATIONS
# ============================================================================

STABLECOINS = {
    "USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "GUSD", "FRAX", 
    "LUSD", "USDD", "EURC", "PYUSD", "FDUSD", "USDE", "USDJ", "SUSD",
    "CRVUSD", "GHO", "CUSD", "RSV", "FEI", "MIM", "UST", "USTC"
}

WRAPPED_ASSETS = {
    "WBTC", "WETH", "STETH", "RETH", "CBETH", "WSTETH", "HBTC",
    "RENBTC", "TBTC", "BTCB", "WBNB", "WAVAX", "WMATIC", "WFTM",
    "WSOL", "WTRX", "WKAVA", "LIDO"
}

EXCHANGE_TOKENS = {
    "BNB", "CRO", "OKB", "KCS", "HT", "LEO", "FTT", "GT", "MX"
}

PRIVACY_COINS = {
    "XMR", "ZEC", "DASH", "SCRT", "FIRO", "ZEN", "ARRR", "XVG",
    "GRIN", "BEAM", "PIVX", "NAV", "PART"
}

SECURITY_CONCERNS = {
    "LUNA", "LUNC", "UST", "USTC", "FTT", "SRM", "MAPS", "OXY"
}

# Pre-scored assets (60+ common ones)
ASSET_SCORES = {
    # Blue chips
    "BTC": AssetScore("BTC", treasury_suitability=5, regulatory_clarity=5, institutional_adoption=5, 
                      volatility=2, staking_advantage=1, trade_frequency=2, speculation_level=1),
    "ETH": AssetScore("ETH", treasury_suitability=5, regulatory_clarity=4, institutional_adoption=5,
                      volatility=3, staking_advantage=4, trade_frequency=2, speculation_level=1),
    
    # Large caps
    "SOL": AssetScore("SOL", treasury_suitability=3, regulatory_clarity=3, institutional_adoption=4,
                      volatility=4, staking_advantage=5, trade_frequency=3, speculation_level=2),
    "XRP": AssetScore("XRP", treasury_suitability=3, regulatory_clarity=4, institutional_adoption=4,
                      volatility=3, staking_advantage=1, trade_frequency=2, speculation_level=2),
    "ADA": AssetScore("ADA", treasury_suitability=3, regulatory_clarity=4, institutional_adoption=3,
                      volatility=3, staking_advantage=4, trade_frequency=2, speculation_level=2),
    "DOGE": AssetScore("DOGE", treasury_suitability=1, regulatory_clarity=3, institutional_adoption=2,
                       volatility=5, staking_advantage=1, trade_frequency=4, speculation_level=5),
    "AVAX": AssetScore("AVAX", treasury_suitability=3, regulatory_clarity=3, institutional_adoption=3,
                       volatility=4, staking_advantage=5, trade_frequency=3, speculation_level=2),
    "DOT": AssetScore("DOT", treasury_suitability=3, regulatory_clarity=3, institutional_adoption=3,
                      volatility=4, staking_advantage=5, trade_frequency=2, speculation_level=2),
    "LINK": AssetScore("LINK", treasury_suitability=4, regulatory_clarity=4, institutional_adoption=4,
                       volatility=3, staking_advantage=3, trade_frequency=2, speculation_level=2),
    "MATIC": AssetScore("MATIC", treasury_suitability=3, regulatory_clarity=3, institutional_adoption=3,
                        volatility=4, staking_advantage=4, trade_frequency=3, speculation_level=2),
    "POL": AssetScore("POL", treasury_suitability=3, regulatory_clarity=3, institutional_adoption=3,
                      volatility=4, staking_advantage=4, trade_frequency=3, speculation_level=2),
    "ATOM": AssetScore("ATOM", treasury_suitability=3, regulatory_clarity=3, institutional_adoption=3,
                       volatility=4, staking_advantage=5, trade_frequency=2, speculation_level=2),
    "UNI": AssetScore("UNI", treasury_suitability=3, regulatory_clarity=2, institutional_adoption=3,
                      volatility=4, staking_advantage=2, trade_frequency=3, speculation_level=3),
    "LTC": AssetScore("LTC", treasury_suitability=4, regulatory_clarity=5, institutional_adoption=4,
                      volatility=3, staking_advantage=1, trade_frequency=2, speculation_level=1),
    "BCH": AssetScore("BCH", treasury_suitability=3, regulatory_clarity=4, institutional_adoption=3,
                      volatility=3, staking_advantage=1, trade_frequency=2, speculation_level=2),
    "XLM": AssetScore("XLM", treasury_suitability=3, regulatory_clarity=4, institutional_adoption=3,
                      volatility=3, staking_advantage=2, trade_frequency=2, speculation_level=2),
    "HBAR": AssetScore("HBAR", treasury_suitability=3, regulatory_clarity=4, institutional_adoption=3,
                       volatility=4, staking_advantage=3, trade_frequency=3, speculation_level=2),
    "SUI": AssetScore("SUI", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=5, staking_advantage=4, trade_frequency=4, speculation_level=3),
    "TRX": AssetScore("TRX", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=3, staking_advantage=3, trade_frequency=3, speculation_level=3),
    "TON": AssetScore("TON", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=4, staking_advantage=4, trade_frequency=3, speculation_level=3),
    
    # Mid caps
    "NEAR": AssetScore("NEAR", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                       volatility=4, staking_advantage=4, trade_frequency=3, speculation_level=3),
    "FIL": AssetScore("FIL", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=4, staking_advantage=3, trade_frequency=3, speculation_level=3),
    "APT": AssetScore("APT", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=5, staking_advantage=4, trade_frequency=3, speculation_level=3),
    "ARB": AssetScore("ARB", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=4, staking_advantage=3, trade_frequency=4, speculation_level=3),
    "OP": AssetScore("OP", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                     volatility=4, staking_advantage=3, trade_frequency=4, speculation_level=3),
    "INJ": AssetScore("INJ", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=5, staking_advantage=4, trade_frequency=4, speculation_level=4),
    "RENDER": AssetScore("RENDER", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                         volatility=5, staking_advantage=2, trade_frequency=4, speculation_level=4),
    "RNDR": AssetScore("RNDR", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                       volatility=5, staking_advantage=2, trade_frequency=4, speculation_level=4),
    "FET": AssetScore("FET", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=5, staking_advantage=3, trade_frequency=4, speculation_level=4),
    "GRT": AssetScore("GRT", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=4, staking_advantage=4, trade_frequency=3, speculation_level=3),
    "ALGO": AssetScore("ALGO", treasury_suitability=3, regulatory_clarity=4, institutional_adoption=3,
                       volatility=4, staking_advantage=4, trade_frequency=2, speculation_level=2),
    "VET": AssetScore("VET", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=4, staking_advantage=3, trade_frequency=3, speculation_level=3),
    "AAVE": AssetScore("AAVE", treasury_suitability=3, regulatory_clarity=2, institutional_adoption=3,
                       volatility=4, staking_advantage=3, trade_frequency=3, speculation_level=3),
    "MKR": AssetScore("MKR", treasury_suitability=3, regulatory_clarity=2, institutional_adoption=3,
                      volatility=4, staking_advantage=2, trade_frequency=2, speculation_level=2),
    "ETC": AssetScore("ETC", treasury_suitability=2, regulatory_clarity=4, institutional_adoption=2,
                      volatility=4, staking_advantage=1, trade_frequency=3, speculation_level=3),
    "ICP": AssetScore("ICP", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=5, staking_advantage=4, trade_frequency=3, speculation_level=3),
    "XMR": AssetScore("XMR", treasury_suitability=2, regulatory_clarity=1, institutional_adoption=1,
                      volatility=4, staking_advantage=1, trade_frequency=3, speculation_level=3),
    "XTZ": AssetScore("XTZ", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=4, staking_advantage=4, trade_frequency=3, speculation_level=3),
    "EOS": AssetScore("EOS", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=4, staking_advantage=3, trade_frequency=3, speculation_level=3),
    "THETA": AssetScore("THETA", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                        volatility=4, staking_advantage=3, trade_frequency=3, speculation_level=3),
    "SAND": AssetScore("SAND", treasury_suitability=1, regulatory_clarity=2, institutional_adoption=2,
                       volatility=5, staking_advantage=2, trade_frequency=4, speculation_level=4),
    "MANA": AssetScore("MANA", treasury_suitability=1, regulatory_clarity=2, institutional_adoption=2,
                       volatility=5, staking_advantage=2, trade_frequency=4, speculation_level=4),
    "AXS": AssetScore("AXS", treasury_suitability=1, regulatory_clarity=2, institutional_adoption=2,
                      volatility=5, staking_advantage=3, trade_frequency=4, speculation_level=4),
    "FLOW": AssetScore("FLOW", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                       volatility=4, staking_advantage=4, trade_frequency=3, speculation_level=3),
    "MINA": AssetScore("MINA", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                       volatility=5, staking_advantage=5, trade_frequency=3, speculation_level=3),
    "SNX": AssetScore("SNX", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=5, staking_advantage=4, trade_frequency=4, speculation_level=4),
    "CRV": AssetScore("CRV", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=5, staking_advantage=4, trade_frequency=4, speculation_level=4),
    "LDO": AssetScore("LDO", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=5, staking_advantage=3, trade_frequency=4, speculation_level=4),
    "IMX": AssetScore("IMX", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=5, staking_advantage=2, trade_frequency=4, speculation_level=4),
    "SEI": AssetScore("SEI", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=2,
                      volatility=5, staking_advantage=4, trade_frequency=4, speculation_level=4),
    "STX": AssetScore("STX", treasury_suitability=2, regulatory_clarity=3, institutional_adoption=2,
                      volatility=5, staking_advantage=4, trade_frequency=4, speculation_level=3),
    "OSMO": AssetScore("OSMO", treasury_suitability=2, regulatory_clarity=2, institutional_adoption=1,
                       volatility=5, staking_advantage=5, trade_frequency=3, speculation_level=4),
    
    # Meme/speculative
    "SHIB": AssetScore("SHIB", treasury_suitability=1, regulatory_clarity=2, institutional_adoption=1,
                       volatility=5, staking_advantage=2, trade_frequency=5, speculation_level=5),
    "PEPE": AssetScore("PEPE", treasury_suitability=1, regulatory_clarity=1, institutional_adoption=1,
                       volatility=5, staking_advantage=1, trade_frequency=5, speculation_level=5),
    "BONK": AssetScore("BONK", treasury_suitability=1, regulatory_clarity=1, institutional_adoption=1,
                       volatility=5, staking_advantage=1, trade_frequency=5, speculation_level=5),
    "WIF": AssetScore("WIF", treasury_suitability=1, regulatory_clarity=1, institutional_adoption=1,
                      volatility=5, staking_advantage=1, trade_frequency=5, speculation_level=5),
    "FLOKI": AssetScore("FLOKI", treasury_suitability=1, regulatory_clarity=1, institutional_adoption=1,
                        volatility=5, staking_advantage=1, trade_frequency=5, speculation_level=5),
    "TRUMP": AssetScore("TRUMP", treasury_suitability=1, regulatory_clarity=1, institutional_adoption=1,
                        volatility=5, staking_advantage=1, trade_frequency=5, speculation_level=5),
    "TURBO": AssetScore("TURBO", treasury_suitability=1, regulatory_clarity=1, institutional_adoption=1,
                        volatility=5, staking_advantage=1, trade_frequency=5, speculation_level=5),
}

STAKING_RATES = {
    "coinbase": {
        "ETH": 4.0, "SOL": 7.0, "ADA": 3.5, "AVAX": 8.0, "DOT": 11.0,
        "ATOM": 8.5, "MATIC": 4.5, "POL": 4.5, "NEAR": 6.0, "ALGO": 5.0, 
        "XTZ": 5.5, "OSMO": 10.0, "MINA": 12.0, "FLOW": 7.0, "SUI": 3.5,
        "GRT": 5.0, "SNX": 8.0, "CRV": 4.0
    },
    "kraken": {
        "ETH": 3.5, "SOL": 6.0, "ADA": 3.0, "AVAX": 7.0, "DOT": 10.0,
        "ATOM": 7.5, "MATIC": 4.0, "POL": 4.0, "NEAR": 5.0, "ALGO": 4.5, 
        "XTZ": 5.0, "FLOW": 6.0, "KAVA": 8.0, "GRT": 5.0, "MINA": 10.0
    }
}


# ============================================================================
# HOLDINGS IMPORTER
# ============================================================================

class HoldingsImporter:
    """Import holdings from various file formats"""
    
    SUPPORTED_FORMATS = ['.csv', '.txt', '.json']
    
    @staticmethod
    def detect_format(filepath: str) -> str:
        ext = Path(filepath).suffix.lower()
        return ext if ext in HoldingsImporter.SUPPORTED_FORMATS else '.txt'
    
    @staticmethod
    def import_file(filepath: str) -> List[HoldingRecord]:
        """Import holdings from file"""
        fmt = HoldingsImporter.detect_format(filepath)
        
        if fmt == '.csv':
            return HoldingsImporter._import_csv(filepath)
        elif fmt == '.json':
            return HoldingsImporter._import_json(filepath)
        else:
            return HoldingsImporter._import_text(filepath)
    
    @staticmethod
    def _import_csv(filepath: str) -> List[HoldingRecord]:
        """Import from CSV with flexible column detection"""
        holdings = []
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            sample = f.read(2048)
            f.seek(0)
            
            delimiter = '\t' if '\t' in sample else (';' if ';' in sample else ',')
            reader = csv.DictReader(f, delimiter=delimiter)
            
            col_map = {}
            if reader.fieldnames:
                for col in reader.fieldnames:
                    col_lower = col.lower().strip()
                    if col_lower in ['symbol', 'ticker', 'coin', 'asset', 'currency', 'name']:
                        col_map['symbol'] = col
                    elif col_lower in ['quantity', 'qty', 'amount', 'balance', 'holdings']:
                        col_map['quantity'] = col
                    elif col_lower in ['value', 'usd', 'usd_value', 'total', 'worth', 'market_value']:
                        col_map['value'] = col
                    elif col_lower in ['cost', 'cost_basis', 'costbasis', 'basis']:
                        col_map['cost'] = col
                    elif col_lower in ['account', 'exchange', 'wallet', 'location']:
                        col_map['account'] = col
            
            for row in reader:
                try:
                    symbol = row.get(col_map.get('symbol', ''), '').strip().upper()
                    if not symbol:
                        symbol = list(row.values())[0].strip().upper() if row else ''
                    
                    if not symbol or len(symbol) > 15:
                        continue
                    
                    qty_str = row.get(col_map.get('quantity', ''), '0')
                    try:
                        quantity = Decimal(str(qty_str).replace(',', '').strip() or '0')
                    except:
                        quantity = Decimal("0")
                    
                    val_str = row.get(col_map.get('value', ''), '0')
                    try:
                        value = Decimal(str(val_str).replace(',', '').replace('$', '').strip() or '0')
                    except:
                        value = Decimal("0")
                    
                    cost_str = row.get(col_map.get('cost', ''), '')
                    try:
                        cost = Decimal(str(cost_str).replace(',', '').replace('$', '').strip()) if cost_str else None
                    except:
                        cost = None
                    
                    account = row.get(col_map.get('account', ''), '').strip()
                    
                    holdings.append(HoldingRecord(
                        symbol=symbol, quantity=quantity, current_value=value,
                        cost_basis=cost, account=account
                    ))
                except Exception:
                    continue
        
        return holdings
    
    @staticmethod
    def _import_text(filepath: str) -> List[HoldingRecord]:
        """Import from text file (one symbol per line)"""
        holdings = []
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.replace(',', ' ').replace('\t', ' ').split()
                if parts:
                    symbol = parts[0].upper()
                    if len(symbol) <= 15 and symbol.isalnum():
                        quantity = Decimal("0")
                        value = Decimal("0")
                        
                        if len(parts) > 1:
                            try:
                                quantity = Decimal(parts[1].replace(',', ''))
                            except:
                                pass
                        
                        if len(parts) > 2:
                            try:
                                value = Decimal(parts[2].replace(',', '').replace('$', ''))
                            except:
                                pass
                        
                        holdings.append(HoldingRecord(symbol=symbol, quantity=quantity, current_value=value))
        
        return holdings
    
    @staticmethod
    def _import_json(filepath: str) -> List[HoldingRecord]:
        """Import from JSON file"""
        holdings = []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            data = data.get('assets', data.get('holdings', data.get('portfolio', [])))
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    holdings.append(HoldingRecord(symbol=item.upper()))
                elif isinstance(item, dict):
                    symbol = item.get('symbol', item.get('ticker', item.get('coin', ''))).upper()
                    if symbol:
                        holdings.append(HoldingRecord(
                            symbol=symbol,
                            quantity=Decimal(str(item.get('quantity', item.get('amount', 0)))),
                            current_value=Decimal(str(item.get('value', item.get('usd', 0)))),
                            cost_basis=Decimal(str(item['cost_basis'])) if 'cost_basis' in item else None,
                            account=item.get('account', '')
                        ))
        
        return holdings


# ============================================================================
# DATA PROVIDER
# ============================================================================

class IndexDataProvider:
    """Fetches market data"""
    
    # Symbol to CoinGecko ID mapping (100+ mappings)
    SYMBOL_TO_ID = {
        "BTC": "bitcoin", "ETH": "ethereum", "XRP": "ripple", "SOL": "solana",
        "DOGE": "dogecoin", "ADA": "cardano", "AVAX": "avalanche-2", "DOT": "polkadot",
        "LINK": "chainlink", "MATIC": "matic-network", "POL": "matic-network",
        "ATOM": "cosmos", "LTC": "litecoin", "UNI": "uniswap", "NEAR": "near",
        "APT": "aptos", "FIL": "filecoin", "ARB": "arbitrum", "OP": "optimism",
        "INJ": "injective-protocol", "SHIB": "shiba-inu", "PEPE": "pepe",
        "BONK": "bonk", "BCH": "bitcoin-cash", "XLM": "stellar", "HBAR": "hedera-hashgraph",
        "SUI": "sui", "ALGO": "algorand", "VET": "vechain", "AAVE": "aave",
        "MKR": "maker", "GRT": "the-graph", "RENDER": "render-token", "RNDR": "render-token",
        "FET": "fetch-ai", "SAND": "the-sandbox", "MANA": "decentraland",
        "AXS": "axie-infinity", "WIF": "dogwifcoin", "FLOKI": "floki", "ETC": "ethereum-classic",
        "ICP": "internet-computer", "XTZ": "tezos", "EOS": "eos", "THETA": "theta-token",
        "FLOW": "flow", "MINA": "mina-protocol", "SNX": "synthetix-network-token",
        "CRV": "curve-dao-token", "LDO": "lido-dao", "IMX": "immutable-x",
        "SEI": "sei-network", "STX": "blockstack", "OSMO": "osmosis", "TRX": "tron",
        "TON": "the-open-network", "XMR": "monero", "KAVA": "kava", "ENS": "ethereum-name-service",
        "COMP": "compound-governance-token", "1INCH": "1inch", "BAL": "balancer",
        "YFI": "yearn-finance", "SUSHI": "sushi", "CAKE": "pancakeswap-token",
        "TRUMP": "official-trump", "TURBO": "turbo",
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def ensure_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def fetch_prices(self, symbols: List[str]) -> Dict[str, AssetData]:
        """Fetch current prices from CoinGecko"""
        await self.ensure_session()
        results = {}
        
        ids_to_fetch = []
        for symbol in symbols:
            s = symbol.upper()
            if s in self.SYMBOL_TO_ID:
                ids_to_fetch.append((s, self.SYMBOL_TO_ID[s]))
        
        if not ids_to_fetch:
            return results
        
        ids_str = ','.join([id for _, id in ids_to_fetch[:250]])
        
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "ids": ids_str,
                "order": "market_cap_desc",
                "sparkline": "false"
            }
            
            async with self.session.get(url, params=params, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    id_to_symbol = {id: sym for sym, id in ids_to_fetch}
                    
                    for item in data:
                        cg_id = item.get('id', '')
                        if cg_id in id_to_symbol:
                            symbol = id_to_symbol[cg_id]
                            results[symbol] = AssetData(
                                symbol=symbol,
                                name=item.get('name', symbol),
                                market_cap=Decimal(str(item.get('market_cap', 0) or 0)),
                                price=Decimal(str(item.get('current_price', 0) or 0)),
                                volume_24h=Decimal(str(item.get('total_volume', 0) or 0)),
                                price_change_24h=float(item.get('price_change_percentage_24h', 0) or 0),
                                circulating_supply=Decimal(str(item.get('circulating_supply', 0) or 0)),
                                ath=Decimal(str(item.get('ath', 0) or 0)),
                                staking_apy_coinbase=STAKING_RATES['coinbase'].get(symbol),
                                staking_apy_kraken=STAKING_RATES['kraken'].get(symbol),
                            )
        except Exception as e:
            print(f"  Warning: Could not fetch live prices: {e}")
        
        return results


# ============================================================================
# INDEX BUILDER
# ============================================================================

class IndexBuilder:
    """Builds index portfolios"""
    
    def __init__(self, config: IndexConfig = None):
        self.config = config or IndexConfig()
        self.data_provider = IndexDataProvider()
    
    def _get_exclusion_reason(self, symbol: str) -> Optional[ExclusionReason]:
        if symbol in self.config.manual_exclusions:
            return ExclusionReason.MANUAL_EXCLUDE
        if self.config.exclude_stablecoins and symbol in STABLECOINS:
            return ExclusionReason.STABLECOIN
        if self.config.exclude_wrapped and symbol in WRAPPED_ASSETS:
            return ExclusionReason.WRAPPED_ASSET
        if self.config.exclude_exchange_tokens and symbol in EXCHANGE_TOKENS:
            return ExclusionReason.EXCHANGE_TOKEN
        if self.config.exclude_privacy_coins and symbol in PRIVACY_COINS:
            return ExclusionReason.PRIVACY_COIN
        if symbol in SECURITY_CONCERNS:
            return ExclusionReason.SECURITY_CONCERN
        return None
    
    def _get_score(self, symbol: str, data: Optional[AssetData] = None) -> AssetScore:
        if symbol in ASSET_SCORES:
            return ASSET_SCORES[symbol]
        
        score = AssetScore(symbol)
        
        if data and data.market_cap > 0:
            mcap = float(data.market_cap)
            if mcap > 100_000_000_000:
                score.treasury_suitability = 5
            elif mcap > 10_000_000_000:
                score.treasury_suitability = 4
            elif mcap > 1_000_000_000:
                score.treasury_suitability = 3
            else:
                score.treasury_suitability = 2
            
            if data.price_change_24h:
                vol = abs(data.price_change_24h)
                score.volatility = 2 if vol < 2 else (3 if vol < 5 else (4 if vol < 10 else 5))
        
        cb_stake = STAKING_RATES['coinbase'].get(symbol, 0)
        kr_stake = STAKING_RATES['kraken'].get(symbol, 0)
        if cb_stake > kr_stake + 2:
            score.staking_advantage = 5
        elif cb_stake > kr_stake:
            score.staking_advantage = 4
        elif cb_stake > 0:
            score.staking_advantage = 3
        else:
            score.staking_advantage = 1
        
        return score
    
    async def build_from_holdings(
        self,
        holdings: List[HoldingRecord],
        name: str = "My Portfolio",
        total_capital: Optional[Decimal] = None,
        fetch_prices: bool = True
    ) -> IndexPortfolio:
        """Build portfolio from imported holdings"""
        
        print(f"Processing {len(holdings)} holdings...")
        
        symbols = list(set(h.symbol for h in holdings))
        
        price_data: Dict[str, AssetData] = {}
        if fetch_prices:
            print("Fetching current prices...")
            async with self.data_provider as provider:
                price_data = await provider.fetch_prices(symbols)
            print(f"  Got prices for {len(price_data)} assets")
        
        assets: List[IndexAsset] = []
        excluded: List[ExcludedAsset] = []
        unmatched: List[str] = []
        
        holdings_by_symbol: Dict[str, HoldingRecord] = {}
        for h in holdings:
            if h.symbol in holdings_by_symbol:
                existing = holdings_by_symbol[h.symbol]
                existing.quantity += h.quantity
                existing.current_value += h.current_value
            else:
                holdings_by_symbol[h.symbol] = HoldingRecord(
                    symbol=h.symbol, quantity=h.quantity, current_value=h.current_value,
                    cost_basis=h.cost_basis, account=h.account
                )
        
        total_value = Decimal("0")
        
        for symbol, holding in holdings_by_symbol.items():
            exclusion = self._get_exclusion_reason(symbol)
            if exclusion:
                excluded.append(ExcludedAsset(
                    symbol=symbol, name=symbol, reason=exclusion,
                    current_value=holding.current_value
                ))
                continue
            
            data = price_data.get(symbol)
            
            if data:
                if holding.quantity > 0 and data.price > 0:
                    holding.current_value = holding.quantity * data.price
            else:
                data = AssetData(
                    symbol=symbol, name=symbol, market_cap=Decimal("0"),
                    price=holding.current_value / holding.quantity if holding.quantity > 0 else Decimal("0"),
                    volume_24h=Decimal("0"),
                )
                if holding.current_value == 0:
                    unmatched.append(symbol)
            
            score = self._get_score(symbol, data)
            
            asset = IndexAsset(
                symbol=symbol, name=data.name, data=data, score=score,
                account=score.recommended_account,
                current_quantity=holding.quantity, current_value=holding.current_value
            )
            
            assets.append(asset)
            total_value += holding.current_value
        
        print(f"  {len(assets)} eligible assets, {len(excluded)} excluded")
        
        if total_capital is None:
            total_capital = total_value
        
        assets.sort(key=lambda x: x.current_value, reverse=True)
        
        for i, asset in enumerate(assets):
            asset.rank = i + 1
            if total_value > 0:
                asset.raw_weight = asset.current_value / total_value * 100
                asset.capped_weight = min(asset.raw_weight, self.config.max_weight_pct)
        
        total_weight = sum(float(a.capped_weight) for a in assets)
        if total_weight > 0:
            for asset in assets:
                asset.capped_weight = asset.capped_weight / Decimal(str(total_weight)) * 100
        
        personal_target = total_capital * self.config.personal_target_pct / 100
        business_target = total_capital * self.config.business_target_pct / 100
        
        personal_assets = []
        business_assets = []
        
        for asset in assets:
            if asset.account == AccountType.BUSINESS:
                business_assets.append(asset)
            elif asset.account == AccountType.PERSONAL:
                personal_assets.append(asset)
            else:
                personal_assets.append(asset)
                business_assets.append(asset)
        
        personal_total = sum(float(a.capped_weight) for a in personal_assets)
        business_total = sum(float(a.capped_weight) for a in business_assets)
        
        for asset in personal_assets:
            if personal_total > 0:
                asset.personal_weight = asset.capped_weight / Decimal(str(personal_total)) * 100
                asset.target_value = personal_target * asset.personal_weight / 100
        
        for asset in business_assets:
            if business_total > 0:
                asset.business_weight = asset.capped_weight / Decimal(str(business_total)) * 100
                if asset.account == AccountType.BUSINESS:
                    asset.target_value = business_target * asset.business_weight / 100
        
        personal_assets.sort(key=lambda x: x.personal_weight, reverse=True)
        business_assets.sort(key=lambda x: x.business_weight, reverse=True)
        
        return IndexPortfolio(
            name=name, config=self.config, created_at=datetime.now(),
            assets=assets, excluded=excluded,
            personal_assets=personal_assets, business_assets=business_assets,
            total_value=total_capital, personal_value=personal_target, business_value=business_target,
            holdings_imported=len(holdings), holdings_matched=len(assets), holdings_unmatched=unmatched
        )


# ============================================================================
# REBALANCER
# ============================================================================

class IndexRebalancer:
    """Generates rebalancing plans"""
    
    def __init__(self, config: IndexConfig = None):
        self.config = config or IndexConfig()
    
    def generate_plan(self, portfolio: IndexPortfolio) -> RebalancePlan:
        plan = RebalancePlan(generated_at=datetime.now())
        
        for asset in portfolio.personal_assets:
            trade_value = asset.trade_needed
            
            if abs(trade_value) < self.config.min_trade_value:
                continue
            
            drift = abs(asset.drift_pct)
            if drift < self.config.rebalance_threshold_pct:
                continue
            
            action = RebalanceAction(
                symbol=asset.symbol, account=AccountType.PERSONAL,
                action="BUY" if trade_value > 0 else "SELL",
                quantity=abs(trade_value / asset.data.price) if asset.data.price > 0 else Decimal("0"),
                value=abs(trade_value), current_value=asset.current_value,
                target_value=asset.target_value, reason=f"Drift {drift:.1f}%",
                priority=1 if drift > 20 else 2
            )
            
            plan.personal_actions.append(action)
            if trade_value > 0:
                plan.total_buys += abs(trade_value)
            else:
                plan.total_sells += abs(trade_value)
        
        for asset in portfolio.business_assets:
            if asset.account != AccountType.BUSINESS:
                continue
            
            trade_value = asset.trade_needed
            
            if abs(trade_value) < self.config.min_trade_value:
                continue
            
            drift = abs(asset.drift_pct)
            if drift < self.config.rebalance_threshold_pct:
                continue
            
            action = RebalanceAction(
                symbol=asset.symbol, account=AccountType.BUSINESS,
                action="BUY" if trade_value > 0 else "SELL",
                quantity=abs(trade_value / asset.data.price) if asset.data.price > 0 else Decimal("0"),
                value=abs(trade_value), current_value=asset.current_value,
                target_value=asset.target_value, reason=f"Drift {drift:.1f}%",
                priority=1 if drift > 20 else 2
            )
            
            plan.business_actions.append(action)
            if trade_value > 0:
                plan.total_buys += abs(trade_value)
            else:
                plan.total_sells += abs(trade_value)
            
            plan.estimated_fees_business += abs(trade_value) * Decimal("0.0016")
        
        plan.personal_actions.sort(key=lambda x: (x.priority, -float(x.value)))
        plan.business_actions.sort(key=lambda x: (x.priority, -float(x.value)))
        
        for ex in portfolio.excluded:
            if ex.current_value > 0:
                plan.assets_to_liquidate.append(f"{ex.symbol}: ${ex.current_value:,.2f} ({ex.reason.value})")
        
        return plan


# ============================================================================
# REPORTER
# ============================================================================

class IndexReporter:
    """Generates reports"""
    
    @staticmethod
    def summary(portfolio: IndexPortfolio) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append(f"INDEX: {portfolio.name}")
        lines.append(f"Generated: {portfolio.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)
        lines.append("")
        
        if portfolio.holdings_imported > 0:
            lines.append(f"Holdings Imported: {portfolio.holdings_imported}")
            lines.append(f"  Matched: {portfolio.holdings_matched}")
            lines.append(f"  Excluded: {len(portfolio.excluded)}")
            if portfolio.holdings_unmatched:
                lines.append(f"  No Price Data: {len(portfolio.holdings_unmatched)}")
            lines.append("")
        
        lines.append(f"Total Assets: {portfolio.asset_count}")
        lines.append(f"  Personal: {portfolio.personal_count} assets")
        lines.append(f"  Business: {portfolio.business_count} assets")
        lines.append("")
        
        if portfolio.total_value > 0:
            lines.append(f"Total Value: ${portfolio.total_value:,.2f}")
            lines.append(f"  Personal Target: ${portfolio.personal_value:,.2f} ({float(portfolio.config.personal_target_pct):.0f}%)")
            lines.append(f"  Business Target: ${portfolio.business_value:,.2f} ({float(portfolio.config.business_target_pct):.0f}%)")
            lines.append("")
        
        lines.append("-" * 70)
        lines.append("BUSINESS PORTFOLIO (Kraken) - Treasury & Long-Term")
        lines.append("-" * 70)
        lines.append(f"{'Rank':<5} {'Symbol':<8} {'Weight':>8} {'Value':>12} {'Stake':>7} {'Treasury'}")
        lines.append("-" * 70)
        
        for asset in portfolio.business_assets[:25]:
            stake = f"{asset.data.staking_apy_kraken:.1f}%" if asset.data.staking_apy_kraken else "-"
            treasury = "★" * asset.score.treasury_suitability
            value = f"${float(asset.current_value):,.0f}" if asset.current_value > 0 else "-"
            lines.append(f"{asset.rank:<5} {asset.symbol:<8} {float(asset.business_weight):>7.2f}% {value:>12} {stake:>7} {treasury}")
        
        if len(portfolio.business_assets) > 25:
            lines.append(f"  ... and {len(portfolio.business_assets) - 25} more")
        
        lines.append("")
        
        lines.append("-" * 70)
        lines.append("PERSONAL PORTFOLIO (Coinbase One) - Staking & Active")
        lines.append("-" * 70)
        lines.append(f"{'Rank':<5} {'Symbol':<8} {'Weight':>8} {'Value':>12} {'Stake':>7} {'Spec'}")
        lines.append("-" * 70)
        
        for asset in portfolio.personal_assets[:25]:
            stake = f"{asset.data.staking_apy_coinbase:.1f}%" if asset.data.staking_apy_coinbase else "-"
            spec = "●" * asset.score.speculation_level
            value = f"${float(asset.current_value):,.0f}" if asset.current_value > 0 else "-"
            lines.append(f"{asset.rank:<5} {asset.symbol:<8} {float(asset.personal_weight):>7.2f}% {value:>12} {stake:>7} {spec}")
        
        if len(portfolio.personal_assets) > 25:
            lines.append(f"  ... and {len(portfolio.personal_assets) - 25} more")
        
        lines.append("")
        
        excluded_with_value = [e for e in portfolio.excluded if e.current_value > 0]
        if excluded_with_value:
            lines.append("-" * 70)
            lines.append("EXCLUDED (Consider Liquidating)")
            lines.append("-" * 70)
            for ex in sorted(excluded_with_value, key=lambda x: x.current_value, reverse=True)[:10]:
                lines.append(f"  {ex.symbol:<8} ${float(ex.current_value):>10,.2f}  {ex.reason.value}")
            lines.append("")
        
        other_excluded = [e for e in portfolio.excluded if e.current_value == 0]
        if other_excluded:
            lines.append("-" * 70)
            lines.append("OTHER EXCLUSIONS")
            lines.append("-" * 70)
            for ex in other_excluded[:15]:
                lines.append(f"  {ex.symbol:<8} {ex.reason.value}")
            if len(other_excluded) > 15:
                lines.append(f"  ... and {len(other_excluded) - 15} more")
        
        return "\n".join(lines)
    
    @staticmethod
    def rebalance_summary(plan: RebalancePlan) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("REBALANCING PLAN")
        lines.append(f"Generated: {plan.generated_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)
        lines.append("")
        
        lines.append(f"Total Buys:  ${plan.total_buys:>12,.2f}")
        lines.append(f"Total Sells: ${plan.total_sells:>12,.2f}")
        lines.append(f"Net Flow:    ${plan.net_flow:>12,.2f} {'(need cash)' if plan.net_flow > 0 else '(frees cash)'}")
        lines.append(f"Est. Fees:   ${plan.estimated_fees_personal + plan.estimated_fees_business:>12,.2f}")
        lines.append("")
        
        if plan.personal_actions:
            lines.append("-" * 70)
            lines.append("PERSONAL ACCOUNT (Coinbase One) - 0% Trading Fees")
            lines.append("-" * 70)
            lines.append(f"{'Action':<6} {'Symbol':<8} {'Value':>12} {'Current':>12} {'Target':>12}")
            lines.append("-" * 70)
            
            for action in plan.personal_actions:
                lines.append(f"{action.action:<6} {action.symbol:<8} ${float(action.value):>10,.2f} ${float(action.current_value):>10,.2f} ${float(action.target_value):>10,.2f}")
        
        lines.append("")
        
        if plan.business_actions:
            lines.append("-" * 70)
            lines.append(f"BUSINESS ACCOUNT (Kraken) - Est. Fees: ${plan.estimated_fees_business:,.2f}")
            lines.append("-" * 70)
            lines.append(f"{'Action':<6} {'Symbol':<8} {'Value':>12} {'Current':>12} {'Target':>12}")
            lines.append("-" * 70)
            
            for action in plan.business_actions:
                lines.append(f"{action.action:<6} {action.symbol:<8} ${float(action.value):>10,.2f} ${float(action.current_value):>10,.2f} ${float(action.target_value):>10,.2f}")
        
        if plan.assets_to_liquidate:
            lines.append("")
            lines.append("-" * 70)
            lines.append("CONSIDER LIQUIDATING (Excluded Assets with Value)")
            lines.append("-" * 70)
            for item in plan.assets_to_liquidate:
                lines.append(f"  {item}")
        
        if not plan.personal_actions and not plan.business_actions:
            lines.append("No rebalancing needed - all positions within threshold.")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_csv(portfolio: IndexPortfolio) -> str:
        lines = ["Symbol,Name,Account,Weight,CurrentValue,TargetValue,MarketCap,Price,StakingAPY,TreasuryScore,VolatilityScore,Action"]
        
        for asset in portfolio.assets:
            account = asset.account.value
            weight = float(asset.personal_weight if asset.account == AccountType.PERSONAL else asset.business_weight)
            stake = asset.data.staking_apy_coinbase or asset.data.staking_apy_kraken or 0
            trade = "BUY" if asset.trade_needed > 0 else "SELL" if asset.trade_needed < 0 else "HOLD"
            
            lines.append(
                f"{asset.symbol},{asset.name},{account},{weight:.4f},"
                f"{float(asset.current_value):.2f},{float(asset.target_value):.2f},"
                f"{float(asset.data.market_cap):.0f},{float(asset.data.price):.6f},"
                f"{stake:.2f},{asset.score.treasury_suitability},{asset.score.volatility},{trade}"
            )
        
        return "\n".join(lines)


# ============================================================================
# QUICK SORT
# ============================================================================

async def quick_sort(symbols: List[str]) -> Dict[str, AccountType]:
    result = {}
    
    for symbol in symbols:
        symbol = symbol.upper()
        
        if symbol in STABLECOINS:
            result[symbol] = AccountType.EXCLUDED
        elif symbol in WRAPPED_ASSETS:
            result[symbol] = AccountType.EXCLUDED
        elif symbol in EXCHANGE_TOKENS:
            result[symbol] = AccountType.EXCLUDED
        elif symbol in PRIVACY_COINS:
            result[symbol] = AccountType.EXCLUDED
        elif symbol in SECURITY_CONCERNS:
            result[symbol] = AccountType.EXCLUDED
        elif symbol in ASSET_SCORES:
            result[symbol] = ASSET_SCORES[symbol].recommended_account
        else:
            result[symbol] = AccountType.SPLIT
    
    return result
