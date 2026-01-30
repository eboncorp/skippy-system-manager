"""
Binance Exchange API client.

Supports Binance spot trading, staking (Simple Earn), and account management.
Uses Binance API v3 for spot and Binance Simple Earn API for staking.
"""

import hmac
import hashlib
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from urllib.parse import urlencode
import logging
import aiohttp

from .base import ExchangeClient, Balance, StakingReward, Trade, OrderResult

logger = logging.getLogger(__name__)


class BinanceClient(ExchangeClient):
    """Client for Binance spot trading API."""

    name = "binance"
    BASE_URL = "https://api.binance.com"

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Initialize Binance client.

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet API (default False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self._session: Optional[aiohttp.ClientSession] = None

        if testnet:
            self.BASE_URL = "https://testnet.binance.vision"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def _sign_params(self, params: dict) -> dict:
        """Add timestamp and signature to request params."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        signed: bool = True,
    ) -> dict:
        """Make request to Binance API."""
        session = await self._get_session()

        if params is None:
            params = {}

        if signed:
            params = self._sign_params(params)

        headers = {
            "X-MBX-APIKEY": self.api_key,
        }

        url = f"{self.BASE_URL}{path}"

        if method == "GET":
            async with session.get(url, headers=headers, params=params) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    raise Exception(f"Binance API error: {data}")
                return data
        elif method == "DELETE":
            async with session.delete(url, headers=headers, params=params) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    raise Exception(f"Binance API error: {data}")
                return data
        else:
            async with session.post(url, headers=headers, data=params) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    raise Exception(f"Binance API error: {data}")
                return data

    async def get_balances(self) -> Dict[str, Balance]:
        """Get all non-zero balances."""
        data = await self._request("GET", "/api/v3/account")

        balances = {}
        for bal in data.get("balances", []):
            free = Decimal(bal["free"])
            locked = Decimal(bal["locked"])
            total = free + locked

            if total > 0:
                balances[bal["asset"]] = Balance(
                    asset=bal["asset"],
                    total=total,
                    available=free,
                    staked=Decimal("0"),  # Staking tracked separately
                )

        return balances

    async def get_staking_positions(self) -> Dict[str, Balance]:
        """Get Simple Earn flexible positions."""
        try:
            data = await self._request(
                "GET",
                "/sapi/v1/simple-earn/flexible/position",
                {"size": 100}
            )

            positions = {}
            for pos in data.get("rows", []):
                asset = pos["asset"]
                amount = Decimal(pos["totalAmount"])

                if amount > 0:
                    positions[asset] = Balance(
                        asset=asset,
                        total=amount,
                        available=Decimal("0"),
                        staked=amount,
                    )

            return positions
        except Exception as e:
            logger.warning(f"Could not fetch staking positions: {e}")
            return {}

    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """Get Simple Earn rewards history."""
        rewards = []

        params = {
            "type": "BONUS",  # Interest payments
            "size": 100,
        }

        if start_date:
            params["startTime"] = int(start_date.timestamp() * 1000)
        if end_date:
            params["endTime"] = int(end_date.timestamp() * 1000)

        try:
            data = await self._request(
                "GET",
                "/sapi/v1/simple-earn/flexible/history/rewardsRecord",
                params
            )

            for record in data.get("rows", []):
                rewards.append(StakingReward(
                    asset=record["asset"],
                    amount=Decimal(record["rewards"]),
                    timestamp=datetime.fromtimestamp(record["time"] / 1000),
                    source="binance_simple_earn",
                ))
        except Exception as e:
            logger.warning(f"Could not fetch staking rewards: {e}")

        return rewards

    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Trade]:
        """Get trade history for a symbol."""
        trades = []

        # If asset specified, query that pair. Otherwise get from common pairs
        symbols = [f"{asset}USDT"] if asset else ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

        for symbol in symbols:
            params = {"symbol": symbol, "limit": 1000}

            if start_date:
                params["startTime"] = int(start_date.timestamp() * 1000)
            if end_date:
                params["endTime"] = int(end_date.timestamp() * 1000)

            try:
                data = await self._request("GET", "/api/v3/myTrades", params)

                for trade in data:
                    base_asset = symbol.replace("USDT", "").replace("USD", "")

                    trades.append(Trade(
                        id=str(trade["id"]),
                        timestamp=datetime.fromtimestamp(trade["time"] / 1000),
                        asset=base_asset,
                        side="buy" if trade["isBuyer"] else "sell",
                        amount=Decimal(trade["qty"]),
                        price=Decimal(trade["price"]),
                        fee=Decimal(trade["commission"]),
                        fee_asset=trade["commissionAsset"],
                    ))
            except Exception as e:
                logger.warning(f"Could not fetch trades for {symbol}: {e}")

        # Sort by timestamp
        trades.sort(key=lambda t: t.timestamp, reverse=True)
        return trades

    async def place_market_order(
        self,
        asset: str,
        side: str,
        amount: Optional[Decimal] = None,
        quote_amount: Optional[Decimal] = None,
    ) -> OrderResult:
        """Place a market order."""
        symbol = f"{asset}USDT"

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
        }

        if side.lower() == "buy" and quote_amount:
            params["quoteOrderQty"] = str(quote_amount)
        elif amount:
            params["quantity"] = str(amount)
        else:
            return OrderResult(success=False, error="Must specify amount or quote_amount")

        try:
            data = await self._request("POST", "/api/v3/order", params)

            # Calculate average fill price
            total_qty = Decimal("0")
            total_quote = Decimal("0")
            total_fee = Decimal("0")

            for fill in data.get("fills", []):
                qty = Decimal(fill["qty"])
                total_qty += qty
                total_quote += qty * Decimal(fill["price"])
                total_fee += Decimal(fill["commission"])

            avg_price = total_quote / total_qty if total_qty > 0 else Decimal("0")

            return OrderResult(
                success=True,
                order_id=str(data["orderId"]),
                filled_amount=Decimal(data["executedQty"]),
                filled_price=avg_price,
                fee=total_fee,
            )
        except Exception as e:
            return OrderResult(success=False, error=str(e))

    async def place_limit_order(
        self,
        asset: str,
        side: str,
        amount: Decimal,
        price: Decimal,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        """Place a limit order."""
        symbol = f"{asset}USDT"

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "LIMIT",
            "timeInForce": time_in_force,
            "quantity": str(amount),
            "price": str(price),
        }

        try:
            data = await self._request("POST", "/api/v3/order", params)

            return OrderResult(
                success=True,
                order_id=str(data["orderId"]),
                filled_amount=Decimal(data.get("executedQty", "0")),
                filled_price=Decimal(data.get("price", "0")),
            )
        except Exception as e:
            return OrderResult(success=False, error=str(e))

    async def cancel_order(self, asset: str, order_id: str) -> bool:
        """Cancel an open order."""
        symbol = f"{asset}USDT"

        try:
            await self._request(
                "DELETE",
                "/api/v3/order",
                {"symbol": symbol, "orderId": order_id}
            )
            return True
        except Exception:
            return False

    async def get_open_orders(self, asset: Optional[str] = None) -> List[dict]:
        """Get all open orders."""
        params = {}
        if asset:
            params["symbol"] = f"{asset}USDT"

        data = await self._request("GET", "/api/v3/openOrders", params)
        return data

    async def get_ticker_price(self, asset: str) -> Decimal:
        """Get current price for an asset."""
        symbol = f"{asset}USDT"
        data = await self._request(
            "GET",
            "/api/v3/ticker/price",
            {"symbol": symbol},
            signed=False
        )
        return Decimal(data["price"])

    async def get_all_prices(self, assets: List[str]) -> Dict[str, Decimal]:
        """Get prices for multiple assets (batch)."""
        data = await self._request(
            "GET",
            "/api/v3/ticker/price",
            signed=False
        )

        prices = {}
        asset_set = set(assets)

        for ticker in data:
            symbol = ticker["symbol"]
            if symbol.endswith("USDT"):
                base = symbol.replace("USDT", "")
                if base in asset_set:
                    prices[base] = Decimal(ticker["price"])

        return prices

    async def get_orderbook(self, asset: str, limit: int = 100) -> dict:
        """Get order book for asset."""
        symbol = f"{asset}USDT"
        data = await self._request(
            "GET",
            "/api/v3/depth",
            {"symbol": symbol, "limit": limit},
            signed=False
        )
        return {
            "bids": [(Decimal(p), Decimal(q)) for p, q in data["bids"]],
            "asks": [(Decimal(p), Decimal(q)) for p, q in data["asks"]],
        }

    async def stake(self, asset: str, amount: Decimal) -> bool:
        """Subscribe to Simple Earn flexible product."""
        # First get product ID for asset
        try:
            products = await self._request(
                "GET",
                "/sapi/v1/simple-earn/flexible/list",
                {"asset": asset, "size": 10}
            )

            if not products.get("rows"):
                logger.warning(f"No Simple Earn product found for {asset}")
                return False

            product_id = products["rows"][0]["productId"]

            # Subscribe
            await self._request(
                "POST",
                "/sapi/v1/simple-earn/flexible/subscribe",
                {"productId": product_id, "amount": str(amount)}
            )
            return True
        except Exception as e:
            logger.error(f"Staking failed: {e}")
            return False

    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """Redeem from Simple Earn flexible product."""
        try:
            # Get position to find product ID
            positions = await self._request(
                "GET",
                "/sapi/v1/simple-earn/flexible/position",
                {"asset": asset}
            )

            if not positions.get("rows"):
                logger.warning(f"No staking position found for {asset}")
                return False

            product_id = positions["rows"][0]["productId"]

            # Redeem
            await self._request(
                "POST",
                "/sapi/v1/simple-earn/flexible/redeem",
                {"productId": product_id, "amount": str(amount)}
            )
            return True
        except Exception as e:
            logger.error(f"Unstaking failed: {e}")
            return False

    async def get_24h_stats(self, asset: str) -> dict:
        """Get 24h price statistics."""
        symbol = f"{asset}USDT"
        data = await self._request(
            "GET",
            "/api/v3/ticker/24hr",
            {"symbol": symbol},
            signed=False
        )
        return {
            "price_change": Decimal(data["priceChange"]),
            "price_change_percent": Decimal(data["priceChangePercent"]),
            "high": Decimal(data["highPrice"]),
            "low": Decimal(data["lowPrice"]),
            "volume": Decimal(data["volume"]),
            "quote_volume": Decimal(data["quoteVolume"]),
        }

    async def get_klines(
        self,
        asset: str,
        interval: str = "1h",
        limit: int = 100,
    ) -> List[dict]:
        """Get candlestick/kline data."""
        symbol = f"{asset}USDT"
        data = await self._request(
            "GET",
            "/api/v3/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
            signed=False
        )

        return [
            {
                "open_time": kline[0],
                "open": Decimal(kline[1]),
                "high": Decimal(kline[2]),
                "low": Decimal(kline[3]),
                "close": Decimal(kline[4]),
                "volume": Decimal(kline[5]),
                "close_time": kline[6],
                "quote_volume": Decimal(kline[7]),
                "trades": kline[8],
            }
            for kline in data
        ]

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


class BinanceUSClient(BinanceClient):
    """Client for Binance.US API (for US users)."""

    name = "binance_us"
    BASE_URL = "https://api.binance.us"

    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret, testnet=False)
        self.BASE_URL = "https://api.binance.us"
