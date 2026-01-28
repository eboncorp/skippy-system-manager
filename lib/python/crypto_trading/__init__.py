"""
Crypto Trading System
=====================

A comprehensive cryptocurrency trading and analysis system with:
- 130+ market signals across 16 categories
- 5 trading strategies (DCA, Swing, Mean Reversion, Grid, Rebalance)
- Full backtesting engine with Monte Carlo simulation
- Paper trading for safe testing
- Risk management with position limits and drawdown protection

Modules:
--------
- agents: Core trading agents and signal analyzers
- data: Data providers and market data fetching
- config: Configuration and settings

Usage:
------
    from crypto_trading.agents import UnifiedAnalyzer
    from crypto_trading.agents import TradingAgent
    from crypto_trading.data import providers

CLI Tools (in scripts/crypto/):
-------------------------------
    crypto_signals_cli.py  - Signal analysis
    trading_cli.py         - Paper/live trading
    backtest_cli.py        - Backtesting engine
    holdings_cli.py        - Portfolio holdings
    index_cli.py           - Index management

Version: 1.0.0
Created: 2026-01-28
"""

__version__ = "1.0.0"
__author__ = "Dave Biggers"

from .config import Config

__all__ = [
    "Config",
    "__version__",
]
