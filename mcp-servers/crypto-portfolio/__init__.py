"""
Crypto Portfolio Manager
========================

A comprehensive cryptocurrency portfolio management system with:
- Multi-exchange support (Coinbase, Kraken, Binance, Crypto.com, Gemini)
- Tax loss harvesting detection and optimization
- Portfolio optimization using Modern Portfolio Theory
- AI-powered analysis and predictions
- Advanced order types (TWAP, VWAP, Iceberg)
- Real-time PnL streaming
- Web dashboard interface

Usage:
    from exchanges import BinanceClient, CoinbaseClient
    from tax_loss_harvesting import TaxLossHarvester
    from portfolio_optimization import PortfolioOptimizer
    from advanced_orders import AdvancedOrderManager
    from web_dashboard import create_dashboard_app
"""

# Exchange clients (mock)
from exchanges.mock import (
    MockExchangeFactory,
    MockCoinbase,
    MockKraken,
    MockCryptoCom,
    MockGemini,
    BaseMockExchange,
    Order,
    Trade,
    OrderBook,
    StakingPosition,
    OrderStatus,
    OrderSide,
    OrderType,
    PriceSimulator,
    ErrorInjector,
    HistoricalDataReplayer,
    ExchangeError,
    RateLimitError,
    AuthenticationError,
    InsufficientFundsError,
    InvalidOrderError,
    NetworkError,
)

# Real exchange clients
from exchanges import (
    BinanceClient,
    BinanceUSClient,
    CoinbaseClient,
    CoinbasePrimeClient,
    KrakenClient,
)

__all__ = [
    # Mock exchanges
    "MockExchangeFactory",
    "MockCoinbase",
    "MockKraken",
    "MockCryptoCom",
    "MockGemini",
    "BaseMockExchange",
    "Order",
    "Trade",
    "OrderBook",
    "StakingPosition",
    "OrderStatus",
    "OrderSide",
    "OrderType",
    "PriceSimulator",
    "ErrorInjector",
    "HistoricalDataReplayer",
    "ExchangeError",
    "RateLimitError",
    "AuthenticationError",
    "InsufficientFundsError",
    "InvalidOrderError",
    "NetworkError",
    # Real exchanges
    "BinanceClient",
    "BinanceUSClient",
    "CoinbaseClient",
    "CoinbasePrimeClient",
    "KrakenClient",
]
