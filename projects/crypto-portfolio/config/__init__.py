"""Configuration module."""

from .settings import settings, Settings
from .targets import (
    TARGET_ALLOCATION,
    STAKING_CONFIG,
    DCA_ALLOCATION,
    REBALANCE_RULES,
    COINGECKO_IDS,
    EXCHANGE_SYMBOLS,
    get_net_staking_yield,
    calculate_blended_yield,
)
from .trading import (
    TradingMode,
    SafetyLimits,
    TradingConfig,
    RebalanceConfig,
    DCAConfig,
    AlertConfig,
    load_config_from_env,
    DEFAULT_CONFIG,
)

__all__ = [
    "settings",
    "Settings",
    "TARGET_ALLOCATION",
    "STAKING_CONFIG",
    "DCA_ALLOCATION",
    "REBALANCE_RULES",
    "COINGECKO_IDS",
    "EXCHANGE_SYMBOLS",
    "get_net_staking_yield",
    "calculate_blended_yield",
    "TradingMode",
    "SafetyLimits",
    "TradingConfig",
    "RebalanceConfig",
    "DCAConfig",
    "AlertConfig",
    "load_config_from_env",
    "DEFAULT_CONFIG",
]
