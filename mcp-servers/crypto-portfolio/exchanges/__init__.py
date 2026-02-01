"""Exchange clients module."""

from .base import ExchangeClient, Balance, StakingReward, Trade, OrderResult
from .coinbase_client import CoinbaseClient, CoinbasePrimeClient
from .kraken_client import KrakenClient
from .binance_client import BinanceClient, BinanceUSClient
from .crypto_com_client import CryptoComClient
from .gemini_client import GeminiClient
from .okx_client import OKXClient

# CCXT fallback (optional - requires ccxt package)
try:
    from .ccxt_fallback import CCXTClient, CCXT_AVAILABLE, create_ccxt_client
except ImportError:
    CCXTClient = None
    CCXT_AVAILABLE = False
    create_ccxt_client = None

__all__ = [
    "ExchangeClient",
    "Balance",
    "StakingReward",
    "Trade",
    "OrderResult",
    "BinanceClient",
    "BinanceUSClient",
    "CCXTClient",
    "CCXT_AVAILABLE",
    "CoinbaseClient",
    "CoinbasePrimeClient",
    "CryptoComClient",
    "GeminiClient",
    "KrakenClient",
    "OKXClient",
    "create_ccxt_client",
]
