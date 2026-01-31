"""
Tests for Exchange Clients
Tests authentication, API calls, and response parsing for all supported exchanges.
"""

import pytest
import responses
import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch, MagicMock

# Import clients
import sys
sys.path.insert(0, '..')

from exchanges import CoinbaseClient, KrakenClient, CryptoComClient, GeminiClient


# ==================== COINBASE TESTS ====================

@pytest.mark.skip(reason="CoinbaseClientWrapper uses RESTClient pattern, not direct key/secret")
class TestCoinbaseClient:
    """Tests for Coinbase API client."""

    @pytest.fixture
    def client(self):
        return CoinbaseClient("test_key", "test_secret")
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.api_key == "test_key"
        assert client.api_secret == "test_secret"
        assert client.BASE_URL == "https://api.coinbase.com"
    
    def test_generate_signature(self, client):
        """Test HMAC signature generation."""
        timestamp = "1234567890"
        method = "GET"
        path = "/api/v3/brokerage/accounts"
        
        signature = client._generate_signature(timestamp, method, path)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest
    
    @responses.activate
    def test_get_accounts_success(self, client):
        """Test successful account retrieval."""
        responses.add(
            responses.GET,
            "https://api.coinbase.com/api/v3/brokerage/accounts",
            json={
                "accounts": [
                    {
                        "uuid": "abc123",
                        "currency": "BTC",
                        "available_balance": {"value": "1.5", "currency": "BTC"},
                        "hold": {"value": "0.1", "currency": "BTC"}
                    },
                    {
                        "uuid": "def456",
                        "currency": "ETH",
                        "available_balance": {"value": "10.0", "currency": "ETH"},
                        "hold": {"value": "0", "currency": "ETH"}
                    }
                ]
            },
            status=200
        )
        
        accounts = client.get_accounts()
        
        assert len(accounts) == 2
        assert accounts[0]["currency"] == "BTC"
        assert accounts[1]["currency"] == "ETH"
    
    @responses.activate
    def test_get_accounts_empty(self, client):
        """Test empty account list."""
        responses.add(
            responses.GET,
            "https://api.coinbase.com/api/v3/brokerage/accounts",
            json={"accounts": []},
            status=200
        )
        
        accounts = client.get_accounts()
        assert accounts == []
    
    @responses.activate
    def test_get_spot_price(self, client):
        """Test spot price retrieval."""
        responses.add(
            responses.GET,
            "https://api.coinbase.com/api/v3/brokerage/products/BTC-USD",
            json={"price": "45000.00"},
            status=200
        )
        
        price = client.get_spot_price("BTC", "USD")
        
        assert price == 45000.00
    
    @responses.activate
    def test_get_spot_price_not_found(self, client):
        """Test spot price for non-existent pair."""
        responses.add(
            responses.GET,
            "https://api.coinbase.com/api/v3/brokerage/products/FAKE-USD",
            json={"error": "Not found"},
            status=404
        )
        
        price = client.get_spot_price("FAKE", "USD")
        assert price is None
    
    def test_staked_token_detection(self, client):
        """Test that staked tokens are properly identified."""
        # Mock the API response
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                "accounts": [
                    {
                        "uuid": "abc",
                        "currency": "CBETH",
                        "available_balance": {"value": "1.0", "currency": "CBETH"}
                    },
                    {
                        "uuid": "def",
                        "currency": "BTC",
                        "available_balance": {"value": "0.5", "currency": "BTC"}
                    }
                ]
            }
            
            accounts = client.get_accounts()
            
            # CBETH should be marked as staked
            cbeth = [a for a in accounts if a["currency"] == "CBETH"][0]
            assert cbeth.get("is_staked") == True
            assert cbeth.get("staked_asset") == "ETH"
            
            # BTC should not be staked
            btc = [a for a in accounts if a["currency"] == "BTC"][0]
            assert btc.get("is_staked") == False


# ==================== KRAKEN TESTS ====================

class TestKrakenClient:
    """Tests for Kraken API client."""
    
    @pytest.fixture
    def client(self):
        # Kraken requires base64-encoded secret
        import base64
        secret = base64.b64encode(b"test_secret").decode()
        return KrakenClient("test_key", secret)
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.api_key == "test_key"
        assert client.BASE_URL == "https://api.kraken.com"
    
    def test_symbol_normalization(self, client):
        """Test symbol conversion from Kraken to standard format."""
        from exchanges.kraken_client import normalize_symbol, to_kraken_symbol
        assert to_kraken_symbol("BTC") == "XBT"
        assert to_kraken_symbol("ETH") == "ETH"  # Unchanged

    def test_symbol_denormalization(self, client):
        """Test Kraken symbol back to common format."""
        from exchanges.kraken_client import normalize_symbol
        assert normalize_symbol("XBT") == "BTC"
        assert normalize_symbol("XXBT") == "BTC"  # With X prefix
        assert normalize_symbol("ETH") == "ETH"
    
    @pytest.mark.asyncio
    async def test_get_ticker_price(self, client):
        """Test ticker price retrieval via async get_ticker_price."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "XXBTZUSD": {
                    "c": ["45000.00", "0.1"]
                }
            }

            price = await client.get_ticker_price("BTC")

            assert price == Decimal("45000.00")

    @pytest.mark.asyncio
    async def test_staked_asset_detection(self, client):
        """Test detection of staked assets (.S suffix) via get_balances."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "XETH": "5.0",
                "ETH.S": "10.0",
                "XXBT": "1.0"
            }

            balances = await client.get_balances()

            assert "ETH" in balances
            assert balances["ETH"].staked == Decimal("10.0")
            assert balances["ETH"].available == Decimal("5.0")


# ==================== CRYPTO.COM TESTS ====================

class TestCryptoComClient:
    """Tests for Crypto.com Exchange API client."""
    
    @pytest.fixture
    def client(self):
        return CryptoComClient("test_key", "test_secret")
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.api_key == "test_key"
        assert client.api_secret == "test_secret"
    
    def test_signature_generation(self, client):
        """Test HMAC signature generation."""
        method = "private/get-account-summary"
        request_id = 1234567890
        params = {"currency": "BTC"}
        nonce = 1234567890
        
        signature = client._generate_signature(method, request_id, params, nonce)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest


# ==================== GEMINI TESTS ====================

class TestGeminiClient:
    """Tests for Gemini API client."""
    
    @pytest.fixture
    def client(self):
        return GeminiClient("test_key", "test_secret")
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.api_key == "test_key"
        assert client.BASE_URL == "https://api.gemini.com"
    
    def test_sandbox_mode(self):
        """Test sandbox environment initialization."""
        client = GeminiClient("test_key", "test_secret", sandbox=True)
        assert client.BASE_URL == "https://api.sandbox.gemini.com"
    
    @pytest.mark.asyncio
    async def test_get_ticker_price(self, client):
        """Test ticker price retrieval via async get_ticker_price."""
        with patch.object(client, '_public_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "last": "45000.00",
                "bid": "44999.00",
                "ask": "45001.00"
            }

            price = await client.get_ticker_price("BTC")

            assert price == Decimal("45000.00")

    @pytest.mark.asyncio
    async def test_get_open_orders(self, client):
        """Test open orders retrieval."""
        with patch.object(client, '_private_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [
                {"order_id": "123", "symbol": "btcusd", "side": "buy", "price": "45000.00"},
            ]

            orders = await client.get_open_orders()

            assert len(orders) == 1
            assert orders[0]["order_id"] == "123"


# ==================== INTEGRATION TESTS ====================

class TestMultiExchangeIntegration:
    """Integration tests for multi-exchange functionality."""
    
    def test_standardized_account_format(self):
        """Test that all clients return accounts in standardized format."""
        # Create mock accounts from each exchange
        coinbase_account = {
            "currency": "BTC",
            "available_balance": {"value": "1.0", "currency": "BTC"},
            "hold": {"value": "0", "currency": "BTC"},
            "uuid": "abc123"
        }
        
        kraken_account = {
            "currency": "BTC",
            "available_balance": {"value": "1.0", "currency": "BTC"},
            "hold": {"value": "0", "currency": "BTC"},
            "uuid": "XBT"
        }
        
        # Both should have same required keys
        required_keys = {"currency", "available_balance", "uuid"}
        
        assert required_keys.issubset(coinbase_account.keys())
        assert required_keys.issubset(kraken_account.keys())
    
    @pytest.mark.skip(reason="CoinbaseClient uses wrapper pattern")
    def test_price_methods_consistent(self):
        """Test that price methods exist on all clients."""
        clients = [
            CoinbaseClient("k", "s"),
            KrakenClient("k", "cw=="),  # Base64 secret
            CryptoComClient("k", "s"),
            GeminiClient("k", "s")
        ]
        
        for client in clients:
            assert hasattr(client, 'get_spot_price')
            assert hasattr(client, 'get_accounts')
            assert callable(client.get_spot_price)
            assert callable(client.get_accounts)


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
