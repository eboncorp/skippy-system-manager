"""
Pytest Configuration
Fixtures and configuration for test suite.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("COINBASE_API_KEY", "test_coinbase_key")
    monkeypatch.setenv("COINBASE_API_SECRET", "test_coinbase_secret")
    monkeypatch.setenv("KRAKEN_API_KEY", "test_kraken_key")
    monkeypatch.setenv("KRAKEN_API_SECRET", "dGVzdF9rcmFrZW5fc2VjcmV0")  # base64
    monkeypatch.setenv("CRYPTOCOM_API_KEY", "test_cryptocom_key")
    monkeypatch.setenv("CRYPTOCOM_API_SECRET", "test_cryptocom_secret")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("GEMINI_API_SECRET", "test_gemini_secret")
    monkeypatch.setenv("TRADING_MODE", "paper")


@pytest.fixture
def mock_requests(mocker):
    """Mock requests library for API calls."""
    mock = mocker.patch("requests.Session")
    return mock


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data for testing."""
    return {
        "BTC": {
            "balance": 1.5,
            "price": 45000,
            "value_usd": 67500
        },
        "ETH": {
            "balance": 10.0,
            "price": 3000,
            "value_usd": 30000
        },
        "SOL": {
            "balance": 100.0,
            "price": 150,
            "value_usd": 15000
        }
    }


@pytest.fixture
def sample_transactions():
    """Sample transaction data for testing."""
    from datetime import datetime, timezone
    
    return [
        {
            "source": "coinbase",
            "type": "buy",
            "asset": "BTC",
            "amount": 0.5,
            "price_usd": 40000,
            "timestamp": datetime(2024, 1, 15, tzinfo=timezone.utc)
        },
        {
            "source": "coinbase",
            "type": "buy",
            "asset": "BTC",
            "amount": 1.0,
            "price_usd": 42000,
            "timestamp": datetime(2024, 3, 1, tzinfo=timezone.utc)
        },
        {
            "source": "coinbase",
            "type": "sell",
            "asset": "BTC",
            "amount": 0.3,
            "price_usd": 50000,
            "timestamp": datetime(2024, 6, 1, tzinfo=timezone.utc)
        }
    ]


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing."""
    db_path = tmp_path / "test_portfolio.db"
    return str(db_path)


class MockResponse:
    """Mock HTTP response object."""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            from requests.exceptions import HTTPError
            raise HTTPError(f"HTTP Error: {self.status_code}")


@pytest.fixture
def mock_response():
    """Factory for creating mock responses."""
    return MockResponse
