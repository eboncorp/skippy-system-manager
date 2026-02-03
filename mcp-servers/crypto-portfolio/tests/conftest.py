"""
Shared fixtures for crypto-portfolio stress tests.
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Add project root to path so imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Realistic mock prices for all ETF + day-trade assets
# ---------------------------------------------------------------------------

MOCK_PRICES = {
    "BTC": Decimal("97500"),
    "ETH": Decimal("3200"),
    "SOL": Decimal("195"),
    "AVAX": Decimal("38"),
    "TRX": Decimal("0.24"),
    "ATOM": Decimal("9.50"),
    "DOT": Decimal("7.20"),
    "ADA": Decimal("0.98"),
    "XRP": Decimal("2.40"),
    "HBAR": Decimal("0.32"),
    "MANA": Decimal("0.55"),
    "SAND": Decimal("0.62"),
    "ONDO": Decimal("1.45"),
    "LINK": Decimal("22"),
    "NEAR": Decimal("5.80"),
    "SUI": Decimal("4.20"),
    "RENDER": Decimal("7.50"),
    "FET": Decimal("2.10"),
    "XTZ": Decimal("1.30"),
    "LTC": Decimal("125"),
    "ALGO": Decimal("0.38"),
    "POL": Decimal("0.50"),
    "DOGE": Decimal("0.34"),
    "ARB": Decimal("1.10"),
    "USDC": Decimal("1"),
    "TON": Decimal("5.40"),
}


@pytest.fixture
def mock_coingecko_prices():
    """Dict of realistic prices for all ETF assets."""
    return dict(MOCK_PRICES)


# ---------------------------------------------------------------------------
# DCA Agent fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def paper_dca_agent(tmp_path, monkeypatch):
    """PaperDCAAgent with $5000 cash, seeded prices, and temp log dir.

    Patches DCA_LOG_PATH and NAV_HISTORY_PATH to use tmp_path so tests
    never touch real files.
    """
    # Patch DCA log path before import
    dca_log = tmp_path / "dca_paper_log.json"
    monkeypatch.setattr("dca_agent.DCA_LOG_PATH", dca_log)

    # Patch NAV history path
    nav_log = tmp_path / "nav_history.json"
    monkeypatch.setattr("etf_manager.NAV_HISTORY_PATH", nav_log)

    from dca_agent import PaperDCAAgent

    agent = PaperDCAAgent(initial_cash=Decimal("5000"))

    # Seed prices
    for symbol, price in MOCK_PRICES.items():
        agent.exchange._prices[symbol] = price

    return agent


# ---------------------------------------------------------------------------
# Day Trader fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def paper_day_trader(tmp_path, monkeypatch):
    """PaperDayTrader with $1000 cash and seeded prices."""
    from day_trading_agent import PaperDayTrader

    trader = PaperDayTrader(initial_cash=Decimal("1000"))

    # Seed prices on the paper exchange
    for symbol, price in MOCK_PRICES.items():
        trader.exchange._prices[symbol] = price

    return trader


# ---------------------------------------------------------------------------
# Agent Runner fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def agent_runner(tmp_path, monkeypatch):
    """AgentRunner in paper mode with temp log dir.

    Patches DCA_LOG_PATH and NAV_HISTORY_PATH and mocks CoinGecko
    price fetching so no network calls are made.
    """
    dca_log = tmp_path / "dca_paper_log.json"
    monkeypatch.setattr("dca_agent.DCA_LOG_PATH", dca_log)

    nav_log = tmp_path / "nav_history.json"
    monkeypatch.setattr("etf_manager.NAV_HISTORY_PATH", nav_log)

    from agent_runner import AgentRunner

    runner = AgentRunner(
        mode="paper",
        run_business=True,
        run_personal=True,
        log_dir=tmp_path / "agent_logs",
    )
    return runner


# ---------------------------------------------------------------------------
# Aiohttp mock helpers
# ---------------------------------------------------------------------------


class MockAiohttpResponse:
    """Factory for mocking aiohttp.ClientSession.get() responses."""

    def __init__(self, json_data=None, status=200, raise_error=None):
        self._json_data = json_data
        self.status = status
        self._raise_error = raise_error

    async def json(self):
        if self._raise_error:
            raise self._raise_error
        return self._json_data

    async def __aenter__(self):
        if self._raise_error:
            raise self._raise_error
        return self

    async def __aexit__(self, *args):
        pass


class MockAiohttpSession:
    """Mock aiohttp.ClientSession that returns preconfigured responses."""

    def __init__(self, responses=None, default_response=None):
        self._responses = responses or {}
        self._default = default_response or MockAiohttpResponse(json_data={})

    def get(self, url, **kwargs):
        for pattern, resp in self._responses.items():
            if pattern in url:
                return resp
        return self._default

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_aiohttp_response():
    """Factory fixture for creating MockAiohttpResponse objects."""
    return MockAiohttpResponse


@pytest.fixture
def tmp_log_dir(tmp_path):
    """Temp directory for trade logs."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir
