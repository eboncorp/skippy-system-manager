"""
Crypto.com Exchange API client implementing ExchangeClient interface.

Provides async interface for Crypto.com Exchange operations including:
- Balance retrieval
- Trade history
- Market orders
- Staking operations
"""

import hmac
import hashlib
import time
import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import aiohttp

from .base import ExchangeClient, Balance, StakingReward, Trade, OrderResult


class CryptoComClient(ExchangeClient):
    """Async client for Crypto.com Exchange API."""

    name = "crypto_com"
    BASE_URL = "https://api.crypto.com/exchange/v1"

    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Crypto.com client.

        Args:
            api_key: Crypto.com API key
            api_secret: Crypto.com API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_id = 0

    @classmethod
    def from_env(cls) -> "CryptoComClient":
        """Create client from environment variables."""
        # Try file-based credentials first
        key_file = os.getenv("CRYPTO_COM_API_KEY_FILE", "~/.config/crypto_com/api_key.json")
        expanded_path = os.path.expanduser(key_file)

        if os.path.exists(expanded_path):
            with open(expanded_path, 'r') as f:
                creds = json.load(f)
                return cls(
                    api_key=creds.get("api_key"),
                    api_secret=creds.get("api_secret")
                )

        # Fall back to environment variables
        api_key = os.getenv("CRYPTO_COM_API_KEY")
        api_secret = os.getenv("CRYPTO_COM_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError(
                "Crypto.com credentials not found. Set either:\n"
                "  - CRYPTO_COM_API_KEY_FILE environment variable\n"
                "  - CRYPTO_COM_API_KEY and CRYPTO_COM_API_SECRET environment variables"
            )

        return cls(api_key=api_key, api_secret=api_secret)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _get_request_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _generate_signature(
        self, method: str, request_id: int, params: dict, nonce: int
    ) -> str:
        """Generate HMAC-SHA256 signature for API request."""
        param_string = ""
        if params:
            sorted_keys = sorted(params.keys())
            for key in sorted_keys:
                value = params[key]
                if isinstance(value, (dict, list)):
                    param_string += key + json.dumps(value, separators=(',', ':'))
                else:
                    param_string += key + str(value)

        sig_payload = f"{method}{request_id}{self.api_key}{param_string}{nonce}"

        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            sig_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def _request(
        self,
        method: str,
        params: Optional[dict] = None,
        public: bool = False,
    ) -> Optional[dict]:
        """Make request to Crypto.com API."""
        session = await self._get_session()

        if public:
            # Public endpoint
            url = f"{self.BASE_URL}/{method}"
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("code") == 0:
                    return data.get("result", {})
                return None

        # Private endpoint
        request_id = self._get_request_id()
        nonce = int(time.time() * 1000)

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

        url = f"{self.BASE_URL}/{method}"

        async with session.post(url, json=payload) as resp:
            data = await resp.json()

            if data.get("code") == 0:
                return data.get("result", {})
            else:
                print(f"Crypto.com API error: {data.get('code')} - {data.get('message')}")
                return None

    async def get_balances(self) -> Dict[str, Balance]:
        """Get all account balances."""
        balances = {}

        data = await self._request("private/user-balance")
        if not data:
            return balances

        position_balances = data.get("data", [])

        for pos in position_balances:
            instrument = pos.get("instrument_name", "")
            quantity = Decimal(str(pos.get("quantity", 0)))
            market_value = Decimal(str(pos.get("market_value", 0)))

            if quantity > 0:
                # Extract currency from instrument name
                currency = instrument.split("_")[0] if "_" in instrument else instrument

                balances[currency] = Balance(
                    asset=currency,
                    total=quantity,
                    available=quantity,  # Crypto.com doesn't separate in this endpoint
                    staked=Decimal("0"),
                )

        return balances

    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """Get staking rewards (Crypto.com Earn)."""
        rewards = []

        # Crypto.com Earn rewards come through account history
        params = {}
        if start_date:
            params["start_ts"] = int(start_date.timestamp() * 1000)
        if end_date:
            params["end_ts"] = int(end_date.timestamp() * 1000)

        try:
            data = await self._request("private/get-account-summary", params)
            if data:
                # Parse earn rewards from account summary
                for account in data.get("accounts", []):
                    if account.get("type") == "EARN":
                        currency = account.get("currency", "")
                        interest = Decimal(str(account.get("interest", 0)))

                        if interest > 0:
                            rewards.append(StakingReward(
                                asset=currency,
                                amount=interest,
                                timestamp=datetime.now(),
                                source="crypto_com",
                            ))
        except Exception as e:
            print(f"Error fetching Crypto.com staking rewards: {e}")

        return rewards

    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Trade]:
        """Get trade history."""
        trades = []

        params = {}
        if start_date:
            params["start_ts"] = int(start_date.timestamp() * 1000)
        if end_date:
            params["end_ts"] = int(end_date.timestamp() * 1000)
        if asset:
            params["instrument_name"] = f"{asset}_USDT"

        try:
            data = await self._request("private/get-trades", params)
            if data:
                for trade_data in data.get("trade_list", []):
                    instrument = trade_data.get("instrument_name", "")
                    trade_asset = instrument.split("_")[0] if "_" in instrument else instrument

                    trades.append(Trade(
                        id=str(trade_data.get("trade_id", "")),
                        timestamp=datetime.fromtimestamp(
                            trade_data.get("create_time", 0) / 1000
                        ),
                        asset=trade_asset,
                        side=trade_data.get("side", "").lower(),
                        amount=Decimal(str(trade_data.get("traded_quantity", 0))),
                        price=Decimal(str(trade_data.get("traded_price", 0))),
                        fee=Decimal(str(trade_data.get("fee", 0))),
                        fee_asset=trade_data.get("fee_currency", "USDT"),
                    ))
        except Exception as e:
            print(f"Error fetching Crypto.com trade history: {e}")

        return trades

    async def place_market_order(
        self,
        asset: str,
        side: str,
        amount: Optional[Decimal] = None,
        quote_amount: Optional[Decimal] = None,
    ) -> OrderResult:
        """Place a market order."""
        instrument = f"{asset}_USDT"

        params = {
            "instrument_name": instrument,
            "side": side.upper(),
            "type": "MARKET",
        }

        if side.lower() == "buy" and quote_amount:
            params["notional"] = str(quote_amount)
        elif amount:
            params["quantity"] = str(amount)
        else:
            return OrderResult(success=False, error="Must specify amount or quote_amount")

        try:
            data = await self._request("private/create-order", params)

            if data:
                return OrderResult(
                    success=True,
                    order_id=str(data.get("order_id", "")),
                    filled_amount=Decimal(str(data.get("cumulative_quantity", 0))),
                    filled_price=Decimal(str(data.get("avg_price", 0))),
                    fee=Decimal(str(data.get("fee", 0))),
                )
            return OrderResult(success=False, error="Order creation failed")

        except Exception as e:
            return OrderResult(success=False, error=str(e))

    async def get_ticker_price(self, asset: str) -> Decimal:
        """Get current price for an asset."""
        instrument = f"{asset}_USDT"

        data = await self._request(f"public/get-tickers?instrument_name={instrument}", public=True)

        if data and data.get("data"):
            tickers = data["data"]
            if tickers and len(tickers) > 0:
                return Decimal(str(tickers[0].get("a", 0)))  # Ask price

        raise ValueError(f"Could not get price for {asset}")

    async def stake(self, asset: str, amount: Decimal) -> bool:
        """
        Stake assets via Crypto.com Earn.

        Note: Crypto.com Earn is managed through the app primarily.
        This provides programmatic access where available.
        """
        params = {
            "currency": asset,
            "amount": str(amount),
        }

        try:
            data = await self._request("private/earn/subscribe", params)
            return data is not None
        except Exception as e:
            print(f"Staking failed: {e}")
            return False

    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """Unstake assets from Crypto.com Earn."""
        params = {
            "currency": asset,
            "amount": str(amount),
        }

        try:
            data = await self._request("private/earn/unsubscribe", params)
            return data is not None
        except Exception as e:
            print(f"Unstaking failed: {e}")
            return False

    async def get_earn_positions(self) -> List[Dict]:
        """Get all Crypto.com Earn positions."""
        try:
            data = await self._request("private/earn/get-subscriptions")
            if data:
                return data.get("subscriptions", [])
        except Exception as e:
            print(f"Error fetching earn positions: {e}")
        return []

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
