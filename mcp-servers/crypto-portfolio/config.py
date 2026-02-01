"""
Trading Configuration and Safety Limits

IMPORTANT: Review and adjust these settings before enabling live trading!
These defaults are intentionally conservative to protect your funds.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class TradingMode(Enum):
    """Trading execution mode."""
    PAPER = "paper"      # Simulated trades - no real money
    CONFIRM = "confirm"  # Require manual confirmation for each trade
    LIVE = "live"        # Fully automated (use with caution!)


@dataclass
class SafetyLimits:
    """Safety guardrails to prevent catastrophic losses."""

    # Maximum single trade size in USD
    max_trade_usd: float = 100.0

    # Maximum total trades per day
    max_trades_per_day: int = 10

    # Maximum daily trading volume in USD
    max_daily_volume_usd: float = 500.0

    # Maximum percentage of any asset to sell in one trade
    max_sell_percent: float = 25.0

    # Minimum USD value to consider an asset for trading
    min_asset_value_usd: float = 10.0

    # Cooldown between trades for same asset (seconds)
    trade_cooldown_seconds: int = 300  # 5 minutes

    # Maximum slippage tolerance for market orders (percent)
    max_slippage_percent: float = 2.0

    # Blacklisted assets (never trade these)
    blacklist: List[str] = field(default_factory=list)

    # Whitelist (if set, ONLY trade these)
    whitelist: Optional[List[str]] = None


@dataclass
class RebalanceConfig:
    """Configuration for portfolio rebalancing."""

    # Target allocations (must sum to 100)
    # Example: {"BTC": 50, "ETH": 30, "SOL": 20}
    target_allocations: Dict[str, float] = field(default_factory=dict)

    # Minimum deviation to trigger rebalance (percent)
    rebalance_threshold: float = 5.0

    # Whether to sell overweight assets or just buy underweight
    allow_sells: bool = True

    # Minimum trade size for rebalancing (USD)
    min_rebalance_trade_usd: float = 25.0


@dataclass
class DCAConfig:
    """Configuration for Dollar Cost Averaging."""

    # Assets to DCA into with USD amounts
    # Example: {"BTC": 50, "ETH": 25} means $50 BTC and $25 ETH per interval
    dca_amounts: Dict[str, float] = field(default_factory=dict)

    # Interval between purchases
    # Options: "hourly", "daily", "weekly", "biweekly", "monthly"
    interval: str = "weekly"

    # Day of week for weekly (0=Monday, 6=Sunday)
    day_of_week: int = 0

    # Day of month for monthly (1-28 recommended)
    day_of_month: int = 1

    # Hour to execute (0-23, in local time)
    hour: int = 9

    # Skip if price is above X-day high (0 to disable)
    skip_if_near_high_days: int = 0


@dataclass
class AlertConfig:
    """Configuration for price alerts and automated responses."""

    # Stop-loss settings per asset
    # Example: {"BTC": -15, "ETH": -20} means sell if down 15% or 20%
    stop_loss_percent: Dict[str, float] = field(default_factory=dict)

    # Take-profit settings per asset
    # Example: {"BTC": 50, "ETH": 40} means sell portion if up 50% or 40%
    take_profit_percent: Dict[str, float] = field(default_factory=dict)

    # Percentage to sell when take-profit triggers
    take_profit_sell_percent: float = 25.0

    # Alert check interval (seconds)
    check_interval: int = 60

    # Reference price for calculating gains/losses
    # Options: "cost_basis", "24h", "7d", "30d"
    reference_price: str = "cost_basis"

    # Enable trailing stop-loss (adjusts stop as price rises)
    trailing_stop: bool = False
    trailing_stop_distance: float = 10.0  # Percent below peak


@dataclass
class TradingConfig:
    """Master configuration for the trading suite."""

    # Operating mode
    mode: TradingMode = TradingMode.CONFIRM

    # Safety limits
    safety: SafetyLimits = field(default_factory=SafetyLimits)

    # Rebalancing settings
    rebalance: RebalanceConfig = field(default_factory=RebalanceConfig)

    # DCA settings
    dca: DCAConfig = field(default_factory=DCAConfig)

    # Alert settings
    alerts: AlertConfig = field(default_factory=AlertConfig)

    # Logging
    log_file: str = "trading.log"
    verbose: bool = True

    @classmethod
    def load_example(cls) -> "TradingConfig":
        """Load an example configuration for testing."""
        return cls(
            mode=TradingMode.PAPER,  # Start in paper trading mode
            safety=SafetyLimits(
                max_trade_usd=50.0,
                max_trades_per_day=5,
                max_daily_volume_usd=200.0,
                blacklist=["SHIB", "DOGE"]  # Example: avoid meme coins
            ),
            rebalance=RebalanceConfig(
                target_allocations={
                    "BTC": 50.0,
                    "ETH": 30.0,
                    "SOL": 20.0
                },
                rebalance_threshold=5.0
            ),
            dca=DCAConfig(
                dca_amounts={
                    "BTC": 25.0,
                    "ETH": 15.0
                },
                interval="weekly",
                day_of_week=0,  # Monday
                hour=9
            ),
            alerts=AlertConfig(
                stop_loss_percent={
                    "BTC": -20.0,
                    "ETH": -25.0,
                    "SOL": -30.0
                },
                take_profit_percent={
                    "BTC": 100.0,
                    "ETH": 100.0,
                    "SOL": 150.0
                }
            )
        )


def load_config_from_env() -> TradingConfig:
    """Load configuration from environment variables."""
    config = TradingConfig()

    # Load mode
    mode_str = os.getenv("TRADING_MODE", "confirm").lower()
    if mode_str == "paper":
        config.mode = TradingMode.PAPER
    elif mode_str == "live":
        config.mode = TradingMode.LIVE
    else:
        config.mode = TradingMode.CONFIRM

    # Load safety limits
    if os.getenv("MAX_TRADE_USD"):
        config.safety.max_trade_usd = float(os.getenv("MAX_TRADE_USD"))
    if os.getenv("MAX_TRADES_PER_DAY"):
        config.safety.max_trades_per_day = int(os.getenv("MAX_TRADES_PER_DAY"))
    if os.getenv("MAX_DAILY_VOLUME_USD"):
        config.safety.max_daily_volume_usd = float(os.getenv("MAX_DAILY_VOLUME_USD"))

    return config


# Default configuration instance
DEFAULT_CONFIG = TradingConfig()
