"""
Gemini Exchange API client implementing ExchangeClient interface.

Provides async interface for Gemini Exchange operations including:
- Balance retrieval
- Trade history
- Market orders
- Gemini Earn (staking) operations
"""

import hmac
import hashlib
import base64
import json
import time
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import aiohttp

from .base import ExchangeClient, Balance, StakingReward, Trade, OrderResult


class GeminiClient(ExchangeClient):
    """Async client for Gemini REST API."""

    name = "gemini"
    BASE_URL = "https://api.gemini.com"

    def __init__(self, api_key: str, api_secret: str, sandbox: bool = False):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key
            api_secret: Gemini API secret
            sandbox: Use sandbox environment for testing
        """
        self.api_key = api_key
        self.api_secret = api_secret.encode() if isinstance(api_secret, str) else api_secret
        self._session: Optional[aiohttp.ClientSession] = None

        if sandbox:
            self.BASE_URL = "https://api.sandbox.gemini.com"

    @classmethod
    def from_env(cls, sandbox: bool = False) -> "GeminiClient":
        """Create client from environment variables."""
        api_key = os.getenv("GEMINI_API_KEY")
        api_secret = os.getenv("GEMINI_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError(
                "Gemini credentials not found. Set:\n"
                "  - GEMINI_API_KEY and GEMINI_API_SECRET environment variables"
            )

        return cls(api_key=api_key, api_secret=api_secret, sandbox=sandbox)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _generate_signature(self, payload: dict) -> tuple:
        """Generate signature for API authentication."""
        payload["nonce"] = str(int(time.time() * 1000))

        encoded_payload = base64.b64encode(
            json.dumps(payload).encode()
        )

        signature = hmac.new(
            self.api_secret,
            encoded_payload,
            hashlib.sha384
        ).hexdigest()

        return encoded_payload, signature

    async def _private_request(
        self, endpoint: str, params: Optional[dict] = None
    ) -> Optional[dict]:
        """Make authenticated private API request."""
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        payload = {"request": endpoint}
        if params:
            payload.update(params)

        encoded_payload, signature = self._generate_signature(payload)

        headers = {
            "Content-Type": "text/plain",
            "Content-Length": "0",
            "X-GEMINI-APIKEY": self.api_key,
            "X-GEMINI-PAYLOAD": encoded_payload.decode(),
            "X-GEMINI-SIGNATURE": signature,
            "Cache-Control": "no-cache"
        }

        async with session.post(url, headers=headers) as resp:
            if resp.status >= 400:
                error_text = await resp.text()
                print(f"Gemini API error ({resp.status}): {error_text}")
                return None
            return await resp.json()

    async def _public_request(self, endpoint: str) -> Optional[dict]:
        """Make public API request."""
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        async with session.get(url) as resp:
            if resp.status >= 400:
                return None
            return await resp.json()

    async def get_balances(self) -> Dict[str, Balance]:
        """Get all account balances including Earn positions."""
        balances = {}

        # Get spot balances
        data = await self._private_request("/v1/balances")
        if data:
            for balance in data:
                currency = balance.get("currency", "UNKNOWN")
                available = Decimal(str(balance.get("available", 0)))
                amount = Decimal(str(balance.get("amount", 0)))

                if amount > 0:
                    balances[currency] = Balance(
                        asset=currency,
                        total=amount,
                        available=available,
                        staked=Decimal("0"),
                    )

        # Get Earn balances
        earn_data = await self._private_request("/v1/earn/balances")
        if earn_data:
            for earn in earn_data:
                currency = earn.get("currency", "UNKNOWN")
                earn_balance = Decimal(str(earn.get("balance", 0)))

                if earn_balance > 0:
                    if currency in balances:
                        # Add to existing balance
                        existing = balances[currency]
                        balances[currency] = Balance(
                            asset=currency,
                            total=existing.total + earn_balance,
                            available=existing.available,
                            staked=earn_balance,
                        )
                    else:
                        balances[currency] = Balance(
                            asset=currency,
                            total=earn_balance,
                            available=Decimal("0"),
                            staked=earn_balance,
                        )

        return balances

    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """Get Gemini Earn interest payments."""
        rewards = []

        params = {"limit": 500}

        data = await self._private_request("/v1/earn/history", params)
        if data:
            for entry in data:
                if entry.get("type") == "Interest":
                    tx_time = datetime.fromtimestamp(entry.get("timestampms", 0) / 1000)

                    # Apply date filters
                    if start_date and tx_time < start_date:
                        continue
                    if end_date and tx_time > end_date:
                        continue

                    rewards.append(StakingReward(
                        asset=entry.get("currency", ""),
                        amount=Decimal(str(entry.get("amount", 0))),
                        timestamp=tx_time,
                        source="gemini_earn",
                    ))

        return rewards

    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Trade]:
        """Get trade history."""
        trades = []

        params = {"limit_trades": 500}
        if asset:
            params["symbol"] = f"{asset.lower()}usd"

        data = await self._private_request("/v1/mytrades", params)
        if data:
            for trade_data in data:
                tx_time = datetime.fromtimestamp(
                    trade_data.get("timestampms", 0) / 1000
                )

                # Apply date filters
                if start_date and tx_time < start_date:
                    continue
                if end_date and tx_time > end_date:
                    continue

                # Parse symbol to get asset
                symbol = trade_data.get("symbol", "")
                trade_asset = symbol[:-3].upper() if len(symbol) > 3 else symbol

                trades.append(Trade(
                    id=str(trade_data.get("tid", "")),
                    timestamp=tx_time,
                    asset=trade_asset,
                    side=trade_data.get("type", "").lower(),
                    amount=Decimal(str(trade_data.get("amount", 0))),
                    price=Decimal(str(trade_data.get("price", 0))),
                    fee=Decimal(str(trade_data.get("fee_amount", 0))),
                    fee_asset=trade_data.get("fee_currency", "USD"),
                ))

        return trades

    async def place_market_order(
        self,
        asset: str,
        side: str,
        amount: Optional[Decimal] = None,
        quote_amount: Optional[Decimal] = None,
    ) -> OrderResult:
        """
        Place a market order.

        Note: Gemini doesn't have true market orders, uses IOC limit orders.
        """
        symbol = f"{asset.lower()}usd"

        # Get current price for market simulation
        price_data = await self._public_request(f"/v1/pubticker/{symbol}")
        if not price_data or "last" not in price_data:
            return OrderResult(success=False, error=f"Could not get price for {asset}")

        current_price = Decimal(str(price_data["last"]))

        # Calculate execution price with slippage buffer
        if side.lower() == "buy":
            execution_price = current_price * Decimal("1.02")  # 2% above for buys
            if quote_amount:
                amount = quote_amount / execution_price
        else:
            execution_price = current_price * Decimal("0.98")  # 2% below for sells

        if not amount:
            return OrderResult(success=False, error="Must specify amount or quote_amount")

        params = {
            "symbol": symbol,
            "side": side.lower(),
            "type": "exchange limit",
            "amount": str(round(float(amount), 8)),
            "price": str(round(float(execution_price), 2)),
            "options": ["immediate-or-cancel"]
        }

        try:
            data = await self._private_request("/v1/order/new", params)

            if data:
                if data.get("is_cancelled"):
                    return OrderResult(
                        success=False,
                        error="Order was cancelled (likely insufficient liquidity)"
                    )

                return OrderResult(
                    success=True,
                    order_id=str(data.get("order_id", "")),
                    filled_amount=Decimal(str(data.get("executed_amount", 0))),
                    filled_price=Decimal(str(data.get("avg_execution_price", 0))),
                    fee=Decimal("0"),  # Gemini doesn't return fee in order response
                )

            return OrderResult(success=False, error="Order creation failed")

        except Exception as e:
            return OrderResult(success=False, error=str(e))

    async def get_ticker_price(self, asset: str) -> Decimal:
        """Get current price for an asset."""
        symbol = f"{asset.lower()}usd"

        data = await self._public_request(f"/v1/pubticker/{symbol}")

        if data and "last" in data:
            return Decimal(str(data["last"]))

        raise ValueError(f"Could not get price for {asset}")

    async def stake(self, asset: str, amount: Decimal) -> bool:
        """Deposit to Gemini Earn."""
        params = {
            "currency": asset.upper(),
            "amount": str(amount)
        }

        try:
            data = await self._private_request("/v1/earn/deposit", params)
            return data is not None
        except Exception as e:
            print(f"Gemini Earn deposit failed: {e}")
            return False

    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """Withdraw from Gemini Earn."""
        params = {
            "currency": asset.upper(),
            "amount": str(amount)
        }

        try:
            data = await self._private_request("/v1/earn/withdraw", params)
            return data is not None
        except Exception as e:
            print(f"Gemini Earn withdrawal failed: {e}")
            return False

    async def get_earn_rates(self) -> List[Dict]:
        """Get current Gemini Earn interest rates."""
        data = await self._private_request("/v1/earn/rates")
        if data:
            return [
                {
                    "currency": rate.get("currency"),
                    "apy": float(rate.get("rate", 0)) * 100,
                    "min_deposit": rate.get("minDepositAmount"),
                    "max_deposit": rate.get("maxDepositAmount"),
                }
                for rate in data
            ]
        return []

    async def get_open_orders(self) -> List[Dict]:
        """Get all open orders."""
        data = await self._private_request("/v1/orders")
        return data if data else []

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a specific order."""
        params = {"order_id": order_id}
        data = await self._private_request("/v1/order/cancel", params)
        return data is not None

    async def cancel_all_orders(self) -> bool:
        """Cancel all open orders."""
        data = await self._private_request("/v1/order/cancel/all")
        return data is not None

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
