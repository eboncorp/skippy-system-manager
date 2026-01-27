"""
Configuration management for the crypto portfolio manager.
Loads settings from environment variables and .env file.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def get_env(key: str, default: str = None, required: bool = False) -> Optional[str]:
    """Get environment variable with optional default and required flag."""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def get_env_list(key: str, default: List[str] = None) -> List[str]:
    """Get environment variable as a list (comma-separated)."""
    value = os.getenv(key, "")
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get environment variable as float."""
    value = os.getenv(key)
    if value is None:
        return default
    return float(value)


def get_env_int(key: str, default: int = 0) -> int:
    """Get environment variable as int."""
    value = os.getenv(key)
    if value is None:
        return default
    return int(value)


@dataclass
class CoinbaseConfig:
    """Coinbase API configuration."""
    api_key: str = field(default_factory=lambda: get_env("COINBASE_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: get_env("COINBASE_API_SECRET", ""))
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)


@dataclass
class CoinbasePrimeConfig:
    """Coinbase Prime API configuration."""
    api_key: str = field(default_factory=lambda: get_env("COINBASE_PRIME_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: get_env("COINBASE_PRIME_API_SECRET", ""))
    passphrase: str = field(default_factory=lambda: get_env("COINBASE_PRIME_PASSPHRASE", ""))
    portfolio_id: str = field(default_factory=lambda: get_env("COINBASE_PRIME_PORTFOLIO_ID", ""))
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret and self.passphrase)


@dataclass
class KrakenConfig:
    """Kraken API configuration."""
    api_key: str = field(default_factory=lambda: get_env("KRAKEN_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: get_env("KRAKEN_API_SECRET", ""))
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)


@dataclass
class WalletConfig:
    """Wallet addresses configuration."""
    evm_addresses: List[str] = field(default_factory=lambda: get_env_list("EVM_WALLET_ADDRESSES"))
    solana_address: str = field(default_factory=lambda: get_env("SOLANA_WALLET_ADDRESS", ""))
    cosmos_address: str = field(default_factory=lambda: get_env("COSMOS_WALLET_ADDRESS", ""))


@dataclass
class RPCConfig:
    """Blockchain RPC endpoints."""
    eth_rpc_url: str = field(default_factory=lambda: get_env("ETH_RPC_URL", "https://eth.llamarpc.com"))
    solana_rpc_url: str = field(default_factory=lambda: get_env("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))


@dataclass
class NotificationConfig:
    """Notification settings."""
    method: str = field(default_factory=lambda: get_env("NOTIFICATION_METHOD", "none"))
    discord_webhook_url: str = field(default_factory=lambda: get_env("DISCORD_WEBHOOK_URL", ""))
    telegram_bot_token: str = field(default_factory=lambda: get_env("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: get_env("TELEGRAM_CHAT_ID", ""))
    smtp_host: str = field(default_factory=lambda: get_env("SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: get_env_int("SMTP_PORT", 587))
    smtp_user: str = field(default_factory=lambda: get_env("SMTP_USER", ""))
    smtp_password: str = field(default_factory=lambda: get_env("SMTP_PASSWORD", ""))
    email_to: str = field(default_factory=lambda: get_env("EMAIL_TO", ""))


@dataclass
class PortfolioConfig:
    """Portfolio management settings."""
    rebalance_threshold: float = field(default_factory=lambda: get_env_float("REBALANCE_THRESHOLD", 0.05))
    dca_daily_amount: float = field(default_factory=lambda: get_env_float("DCA_DAILY_AMOUNT", 40.0))
    min_trade_size: float = field(default_factory=lambda: get_env_float("MIN_TRADE_SIZE", 10.0))


@dataclass
class TaxConfig:
    """Tax tracking settings."""
    cost_basis_method: str = field(default_factory=lambda: get_env("COST_BASIS_METHOD", "FIFO"))
    tax_year: int = field(default_factory=lambda: get_env_int("TAX_YEAR", 2025))


@dataclass
class DataConfig:
    """Data storage settings."""
    database_path: str = field(default_factory=lambda: get_env("DATABASE_PATH", "./data/portfolio.db"))
    price_cache_duration: int = field(default_factory=lambda: get_env_int("PRICE_CACHE_DURATION", 60))


@dataclass
class MarketDataConfig:
    """Market data API settings."""
    coingecko_api_key: str = field(default_factory=lambda: get_env("COINGECKO_API_KEY", ""))
    glassnode_api_key: str = field(default_factory=lambda: get_env("GLASSNODE_API_KEY", ""))


@dataclass
class SchedulerConfig:
    """Scheduler settings."""
    sync_interval: int = field(default_factory=lambda: get_env_int("SYNC_INTERVAL", 15))
    dca_execution_time: str = field(default_factory=lambda: get_env("DCA_EXECUTION_TIME", "14:00"))
    alert_interval: int = field(default_factory=lambda: get_env_int("ALERT_INTERVAL", 5))


@dataclass
class Settings:
    """Main settings container."""
    coinbase: CoinbaseConfig = field(default_factory=CoinbaseConfig)
    coinbase_prime: CoinbasePrimeConfig = field(default_factory=CoinbasePrimeConfig)
    kraken: KrakenConfig = field(default_factory=KrakenConfig)
    wallets: WalletConfig = field(default_factory=WalletConfig)
    rpc: RPCConfig = field(default_factory=RPCConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    portfolio: PortfolioConfig = field(default_factory=PortfolioConfig)
    tax: TaxConfig = field(default_factory=TaxConfig)
    data: DataConfig = field(default_factory=DataConfig)
    market_data: MarketDataConfig = field(default_factory=MarketDataConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    
    def validate(self) -> List[str]:
        """Validate settings and return list of warnings."""
        warnings = []
        
        if not self.coinbase.is_configured and not self.coinbase_prime.is_configured:
            warnings.append("No Coinbase API configured")
        
        if not self.kraken.is_configured:
            warnings.append("Kraken API not configured")
        
        if not self.wallets.evm_addresses and not self.wallets.solana_address:
            warnings.append("No wallet addresses configured")
        
        return warnings


# Global settings instance
settings = Settings()


if __name__ == "__main__":
    # Print current configuration status
    print("Configuration Status:")
    print(f"  Coinbase configured: {settings.coinbase.is_configured}")
    print(f"  Coinbase Prime configured: {settings.coinbase_prime.is_configured}")
    print(f"  Kraken configured: {settings.kraken.is_configured}")
    print(f"  EVM wallets: {len(settings.wallets.evm_addresses)}")
    print(f"  Solana wallet: {'Yes' if settings.wallets.solana_address else 'No'}")
    print(f"  Notifications: {settings.notifications.method}")
    
    warnings = settings.validate()
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")
