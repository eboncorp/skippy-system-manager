"""
Crypto Portfolio Manager Configuration

Edit these settings to customize the signal analysis and DCA behavior.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os


@dataclass
class DCAConfig:
    """DCA strategy configuration."""
    
    # Base DCA amount (daily)
    base_amount_usd: float = 75.0  # ~$2,250/month
    
    # Minimum and maximum multipliers
    min_multiplier: float = 0.25
    max_multiplier: float = 2.5
    
    # Target allocation percentages
    target_allocation: Dict[str, float] = field(default_factory=lambda: {
        "BTC": 0.45,   # 45%
        "ETH": 0.30,   # 30%
        "SOL": 0.10,   # 10%
        "LINK": 0.05,  # 5%
        "Other": 0.10, # 10%
    })


@dataclass
class BufferConfig:
    """Cash buffer configuration."""
    
    # Total cash buffer to maintain
    buffer_amount_usd: float = 10000.0
    
    # Deployment thresholds based on composite score
    deployment_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "extreme_buy": 0.75,    # Score < -60
        "strong_buy": 0.50,     # Score < -40
        "buy": 0.25,            # Score < -20
        "mild_buy": 0.10,       # Score < 0
    })


@dataclass
class SignalConfig:
    """Signal weighting configuration."""
    
    # Category weights (higher = more influence)
    category_weights: Dict[str, float] = field(default_factory=lambda: {
        "technical": 0.8,
        "sentiment": 0.7,
        "onchain": 1.2,
        "derivatives": 1.0,
        "macro": 0.6,
        "mining": 0.9,
        "institutional": 1.1,
        "additional": 0.5,
        "cycle": 1.3,
        "onchain_advanced": 1.2,
        "exchange_flow": 1.0,
        "market_structure": 0.6,
        "macro_liquidity": 0.7,
        "derivatives_advanced": 0.8,
    })
    
    # Individual signal overrides (signal_name: weight_multiplier)
    signal_overrides: Dict[str, float] = field(default_factory=lambda: {
        "Pi Cycle Top": 1.5,      # Very accurate at tops
        "CVDD": 1.5,              # Very accurate at bottoms
        "MVRV Z-Score": 1.3,      # Reliable valuation metric
        "Fear & Greed": 1.2,      # Good sentiment gauge
        "ETF Flows": 1.3,         # Institutional signal
    })


@dataclass
class AlertConfig:
    """Alert configuration."""
    
    # Email alerts
    email_enabled: bool = False
    email_address: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    
    # Alert thresholds
    score_alert_threshold: float = -40  # Alert when score drops below this
    dip_alert_threshold: float = 0.15   # Alert on 15%+ dip
    
    # Notification cooldown (hours)
    cooldown_hours: int = 24


@dataclass
class APIKeysConfig:
    """API keys configuration (loaded from environment)."""
    
    # Exchange APIs
    coinbase_api_key: str = field(default_factory=lambda: os.getenv("COINBASE_API_KEY", ""))
    coinbase_api_secret: str = field(default_factory=lambda: os.getenv("COINBASE_API_SECRET", ""))
    kraken_api_key: str = field(default_factory=lambda: os.getenv("KRAKEN_API_KEY", ""))
    kraken_api_secret: str = field(default_factory=lambda: os.getenv("KRAKEN_API_SECRET", ""))
    
    # Data provider APIs
    coingecko_api_key: str = field(default_factory=lambda: os.getenv("COINGECKO_API_KEY", ""))
    glassnode_api_key: str = field(default_factory=lambda: os.getenv("GLASSNODE_API_KEY", ""))
    cryptoquant_api_key: str = field(default_factory=lambda: os.getenv("CRYPTOQUANT_API_KEY", ""))
    santiment_api_key: str = field(default_factory=lambda: os.getenv("SANTIMENT_API_KEY", ""))
    lunarcrush_api_key: str = field(default_factory=lambda: os.getenv("LUNARCRUSH_API_KEY", ""))
    coinglass_api_key: str = field(default_factory=lambda: os.getenv("COINGLASS_API_KEY", ""))


@dataclass
class Config:
    """Main configuration."""
    
    dca: DCAConfig = field(default_factory=DCAConfig)
    buffer: BufferConfig = field(default_factory=BufferConfig)
    signals: SignalConfig = field(default_factory=SignalConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    api_keys: APIKeysConfig = field(default_factory=APIKeysConfig)
    
    # Supported assets
    supported_assets: List[str] = field(default_factory=lambda: [
        "BTC", "ETH", "SOL", "AVAX", "LINK", 
        "DOT", "ATOM", "NEAR", "ARB", "OP"
    ])
    
    # Analysis settings
    cache_ttl_minutes: int = 5
    max_concurrent_requests: int = 10


# Default configuration instance
config = Config()


# Score thresholds for recommendations
SCORE_THRESHOLDS = {
    "extreme_buy": -60,
    "strong_buy": -40,
    "buy": -20,
    "mild_buy": 0,
    "neutral": 20,
    "caution": 40,
    "greed": 60,
    "extreme_greed": 100,
}

# DCA multipliers for each threshold
DCA_MULTIPLIERS = {
    "extreme_buy": 2.5,
    "strong_buy": 2.0,
    "buy": 1.5,
    "mild_buy": 1.25,
    "neutral": 1.0,
    "caution": 0.75,
    "greed": 0.5,
    "extreme_greed": 0.25,
}

# Buffer deployment percentages
BUFFER_DEPLOYMENT = {
    "extreme_buy": 0.75,
    "strong_buy": 0.50,
    "buy": 0.25,
    "mild_buy": 0.10,
    "neutral": 0.0,
    "caution": 0.0,
    "greed": 0.0,
    "extreme_greed": 0.0,
}
