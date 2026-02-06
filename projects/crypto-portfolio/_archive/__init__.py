"""
Exchange Integrations
=====================

This package provides both real and mock exchange clients.

Mock clients (exchanges/mock.py):
- MockCoinbase, MockKraken, MockCryptoCom, MockGemini
- Full paper trading support
- Error injection for testing
- Historical data replay for backtesting

Usage:
    from exchanges.mock import MockExchangeFactory
    
    # Create single exchange
    coinbase = MockExchangeFactory.create("coinbase")
    
    # Create all exchanges
    exchanges = MockExchangeFactory.create_all()
"""

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

__all__ = [
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
]
