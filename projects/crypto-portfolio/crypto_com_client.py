"""
Crypto.com Exchange API Client
Handles authentication and API requests to Crypto.com Exchange.

Uses HMAC-SHA256 digital signatures for authentication.
Docs: https://exchange-docs.crypto.com/exchange/v1/rest-ws/index.html
"""

import logging
import os
import json
import time
import hmac
import hashlib
from typing import Optional, List, Dict, Any
import requests

logger = logging.getLogger(__name__)


def load_crypto_com_credentials(filepath: str = None) -> Dict[str, str]:
    """Load Crypto.com API credentials from JSON file."""
    if filepath is None:
        filepath = os.getenv("CRYPTO_COM_API_KEY_FILE", "~/.config/crypto_com/api_key.json")

    with open(os.path.expanduser(filepath), 'r') as f:
        return json.load(f)


def create_crypto_com_client(
    api_key: str = None,
    api_secret: str = None,
    key_file: str = None
) -> "CryptoComClient":
    """Factory function to create a Crypto.com Exchange client.

    Args:
        api_key: API key
        api_secret: API secret
        key_file: Path to JSON file with credentials

    Returns:
        CryptoComClient instance
    """
    # Try loading from file first
    if key_file or os.getenv("CRYPTO_COM_API_KEY_FILE"):
        creds = load_crypto_com_credentials(key_file)
        api_key = creds.get("api_key")
        api_secret = creds.get("api_secret")

    # Fall back to environment variables
    if not api_key:
        api_key = os.getenv("CRYPTO_COM_API_KEY")
    if not api_secret:
        api_secret = os.getenv("CRYPTO_COM_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(
            "No Crypto.com credentials found. Provide either:\n"
            "  - CRYPTO_COM_API_KEY_FILE environment variable\n"
            "  - CRYPTO_COM_API_KEY and CRYPTO_COM_API_SECRET environment variables"
        )

    return CryptoComClient(api_key=api_key, api_secret=api_secret)


class CryptoComClient:
    """Client for Crypto.com Exchange API."""

    BASE_URL = "https://api.crypto.com/exchange/v1"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self._request_id = 0

    def _get_request_id(self) -> int:
        """Get unique request ID."""
        self._request_id += 1
        return self._request_id

    def _generate_signature(self, method: str, request_id: int, params: dict, nonce: int) -> str:
        """Generate HMAC-SHA256 signature for API request.

        Signature = HMAC-SHA256(method + id + api_key + param_string + nonce)
        where param_string is sorted alphabetically as key+value pairs
        """
        # Sort params and create param string
        param_string = ""
        if params:
            sorted_keys = sorted(params.keys())
            for key in sorted_keys:
                value = params[key]
                if isinstance(value, (dict, list)):
                    param_string += key + json.dumps(value, separators=(',', ':'))
                else:
                    param_string += key + str(value)

        # Create signature payload
        sig_payload = f"{method}{request_id}{self.api_key}{param_string}{nonce}"

        # Generate HMAC-SHA256
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            sig_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _make_request(self, method: str, params: dict = None) -> Optional[dict]:
        """Make authenticated request to Crypto.com Exchange API."""
        request_id = self._get_request_id()
        nonce = int(time.time() * 1000)  # Milliseconds

        if params is None:
            params = {}

        signature = self._generate_signature(method, request_id, params, nonce)

        payload = {
            "id": request_id,
            "method": method,
            "api_key": self.api_key,
            "params": params,
            "nonce": nonce,
            "sig": signature
        }

        try:
            response = self.session.post(
                f"{self.BASE_URL}/{method}",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                return result.get("result", {})
            else:
                logger.warning("API Error: %s - %s", result.get('code'), result.get('message'))
                return None

        except requests.exceptions.HTTPError as e:
            logger.warning("HTTP Error: %s", e)
            return None
        except requests.exceptions.RequestException as e:
            logger.warning("Request Error: %s", e)
            return None

    def get_user_balance(self) -> Optional[Dict[str, Any]]:
        """Get user wallet balance with collateral and position info."""
        return self._make_request("private/user-balance")

    def get_accounts(self) -> Optional[Dict[str, Any]]:
        """Get master and sub-account details."""
        return self._make_request("private/get-accounts")

    def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """Get all open positions with PnL data."""
        result = self._make_request("private/get-positions")
        if result:
            return result.get("data", [])
        return []

    def get_subaccount_balances(self) -> Optional[Dict[str, Any]]:
        """Get balances across all sub-accounts."""
        return self._make_request("private/get-subaccount-balances")

    def get_instruments(self) -> Optional[List[Dict[str, Any]]]:
        """Get available trading instruments (public endpoint)."""
        try:
            response = self.session.get(f"{self.BASE_URL}/public/get-instruments")
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 0:
                return result.get("result", {}).get("data", [])
        except Exception as e:
            logger.warning("Error getting instruments: %s", e)
        return []

    def get_ticker(self, instrument_name: str = None) -> Optional[Dict[str, Any]]:
        """Get ticker data for instrument(s)."""
        try:
            url = f"{self.BASE_URL}/public/get-tickers"
            if instrument_name:
                url += f"?instrument_name={instrument_name}"
            response = self.session.get(url)
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 0:
                return result.get("result", {}).get("data", [])
        except Exception as e:
            logger.warning("Error getting ticker: %s", e)
        return []

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        balance_data = self.get_user_balance()

        if not balance_data:
            return {
                "total_value_usd": 0,
                "holdings_count": 0,
                "holdings": [],
                "error": "Failed to fetch balance"
            }

        holdings = []
        total_value = 0

        # Parse position balances
        position_balances = balance_data.get("data", [])

        for pos in position_balances:
            instrument = pos.get("instrument_name", "")
            quantity = float(pos.get("quantity", 0))
            market_value = float(pos.get("market_value", 0))
            collateral_weight = float(pos.get("collateral_weight", 0))

            if quantity > 0 or market_value > 0:
                # Extract currency from instrument name (e.g., "BTC" from "BTC_USDT")
                currency = instrument.split("_")[0] if "_" in instrument else instrument

                holdings.append({
                    "currency": currency,
                    "instrument": instrument,
                    "balance": quantity,
                    "value_usd": market_value,
                    "collateral_weight": collateral_weight,
                })
                total_value += market_value

        # Sort by value
        holdings.sort(key=lambda x: x['value_usd'], reverse=True)

        return {
            "exchange": "Crypto.com",
            "total_value_usd": total_value,
            "holdings_count": len(holdings),
            "holdings": holdings,
            "raw_data": balance_data,
        }


# Test function
def test_connection():
    """Test Crypto.com API connection."""
    try:
        client = create_crypto_com_client()

        # Test public endpoint first
        print("Testing public endpoint...")
        tickers = client.get_ticker("BTC_USDT")
        if tickers:
            print(f"BTC/USDT ticker: {tickers[0] if tickers else 'N/A'}")

        # Test private endpoint
        print("\nTesting private endpoint (user balance)...")
        balance = client.get_user_balance()
        if balance:
            print(f"Balance data received: {json.dumps(balance, indent=2)[:500]}")
        else:
            print("Failed to get balance - check API credentials")

        return balance is not None

    except Exception as e:
        print(f"Connection test failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
