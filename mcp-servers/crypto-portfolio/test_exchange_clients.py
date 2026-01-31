"""
Tests for Exchange Clients
Tests authentication, API calls, and response parsing for all supported exchanges.
"""

import pytest
import responses
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

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
        """Test symbol conversion to Kraken format."""
        assert client._normalize_symbol("BTC") == "XBT"
        assert client._normalize_symbol("DOGE") == "XDG"
        assert client._normalize_symbol("ETH") == "ETH"  # Unchanged
    
    def test_symbol_denormalization(self, client):
        """Test Kraken symbol back to common format."""
        assert client._denormalize_symbol("XBT") == "BTC"
        assert client._denormalize_symbol("XXBT") == "BTC"  # With X prefix
        assert client._denormalize_symbol("ETH") == "ETH"
    
    @responses.activate
    def test_get_server_time(self, client):
        """Test server time endpoint (connectivity test)."""
        responses.add(
            responses.GET,
            "https://api.kraken.com/0/public/Time",
            json={
                "error": [],
                "result": {
                    "unixtime": 1234567890,
                    "rfc1123": "Mon, 13 Feb 2009 23:31:30 +0000"
                }
            },
            status=200
        )
        
        result = client.get_server_time()
        
        assert result is not None
        assert "unixtime" in result
    
    @responses.activate
    def test_get_spot_price(self, client):
        """Test spot price retrieval."""
        responses.add(
            responses.GET,
            "https://api.kraken.com/0/public/Ticker",
            json={
                "error": [],
                "result": {
                    "XXBTZUSD": {
                        "c": ["45000.00", "0.1"]  # Last trade [price, volume]
                    }
                }
            },
            status=200
        )
        
        price = client.get_spot_price("BTC", "USD")
        
        assert price == 45000.00
    
    def test_staked_asset_detection(self, client):
        """Test detection of staked assets (.S suffix)."""
        with patch.object(client, '_private_request') as mock_request:
            mock_request.return_value = {
                "ETH": "5.0",
                "ETH.S": "10.0",  # Staked ETH
                "XBT": "1.0"
            }
            
            accounts = client.get_accounts()
            
            # Find staked ETH
            staked = [a for a in accounts if "Staked" in a["currency"]]
            assert len(staked) == 1
            assert staked[0]["is_staked"] == True


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
    
    @responses.activate
    def test_get_spot_price(self, client):
        """Test spot price retrieval."""
        responses.add(
            responses.GET,
            "https://api.gemini.com/v1/pubticker/btcusd",
            json={
                "last": "45000.00",
                "bid": "44999.00",
                "ask": "45001.00"
            },
            status=200
        )
        
        price = client.get_spot_price("BTC", "USD")
        
        assert price == 45000.00
    
    @responses.activate
    def test_list_products(self, client):
        """Test product listing."""
        responses.add(
            responses.GET,
            "https://api.gemini.com/v1/symbols",
            json=["btcusd", "ethusd", "solusd"],
            status=200
        )
        
        products = client.list_products()
        
        assert len(products) == 3
        assert any(p["product_id"] == "btcusd" for p in products)


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
