"""
OKX Exchange API client implementing ExchangeClient interface.

Provides async interface for OKX Exchange operations including:
- Balance retrieval (trading, funding, earn accounts)
- Trade history
- Market orders
- Staking operations (OKX Earn)

Uses OKX REST API v5: https://www.okx.com/docs-v5/
"""

import hmac
import hashlib
import base64
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
import logging
import aiohttp

from .base import ExchangeClient, Balance, StakingReward, Trade, OrderResult

logger = logging.getLogger(__name__)


class OKXClient(ExchangeClient):
    """Async client for OKX REST API v5."""

    name = "okx"
    BASE_URL = "https://www.okx.com"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str,
        demo: bool = False,
    ):
        """
        Initialize OKX client.

        Args:
            api_key: OKX API key
            api_secret: OKX API secret key
            passphrase: OKX API passphrase (set during key creation)
            demo: Use demo trading environment
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.demo = demo
        self._session: Optional[aiohttp.ClientSession] = None

    @classmethod
    def from_env(cls, demo: bool = False) -> "OKXClient":
        """Create client from environment variables."""
        api_key = os.getenv("OKX_API_KEY")
        api_secret = os.getenv("OKX_API_SECRET")
        passphrase = os.getenv("OKX_PASSPHRASE")

        if not api_key or not api_secret or not passphrase:
            raise ValueError(
                "OKX credentials not found. Set:\n"
                "  - OKX_API_KEY\n"
                "  - OKX_API_SECRET\n"
                "  - OKX_PASSPHRASE"
            )

        return cls(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            demo=demo,
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def _sign_request(
        self, timestamp: str, method: str, path: str, body: str = ""
    ) -> str:
        """Generate HMAC-SHA256 signature for OKX API authentication."""
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256,
        )
        return base64.b64encode(signature.digest()).decode()

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        body: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make authenticated request to OKX API v5."""
        session = await self._get_session()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Build query string for GET requests
        if method.upper() == "GET" and params:
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
            full_path = f"{path}?{query}" if query else path
        else:
            full_path = path

        body_str = json.dumps(body) if body else ""
        signature = self._sign_request(timestamp, method, full_path, body_str)

        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }

        if self.demo:
            headers["x-simulated-trading"] = "1"

        url = f"{self.BASE_URL}{full_path}"

        async with session.request(
            method, url, headers=headers, data=body_str or None
        ) as resp:
            data = await resp.json()

            if resp.status >= 400:
                logger.error(f"OKX API HTTP error ({resp.status}): {data}")
                return None

            # OKX returns code "0" for success
            if data.get("code") != "0":
                logger.error(
                    f"OKX API error (code {data.get('code')}): {data.get('msg')}"
                )
                return None

            return data

    async def _public_request(
        self, path: str, params: Optional[dict] = None
    ) -> Optional[dict]:
        """Make unauthenticated public API request."""
        session = await self._get_session()

        if params:
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
            url = f"{self.BASE_URL}{path}?{query}" if query else f"{self.BASE_URL}{path}"
        else:
            url = f"{self.BASE_URL}{path}"

        async with session.get(url) as resp:
            if resp.status >= 400:
                return None
            data = await resp.json()
            if data.get("code") != "0":
                return None
            return data

    async def get_balances(self) -> Dict[str, Balance]:
        """Get all account balances across trading and funding accounts."""
        balances: Dict[str, Balance] = {}

        # Trading account balances
        trading_data = await self._request("GET", "/api/v5/account/balance")
        if trading_data and trading_data.get("data"):
            for account in trading_data["data"]:
                for detail in account.get("details", []):
                    ccy = detail.get("ccy", "UNKNOWN")
                    total = Decimal(str(detail.get("eq", 0) or 0))
                    available = Decimal(str(detail.get("availEq", 0) or detail.get("availBal", 0) or 0))

                    if total > 0:
                        balances[ccy] = Balance(
                            asset=ccy,
                            total=total,
                            available=available,
                        )

        # Funding account balances
        funding_data = await self._request("GET", "/api/v5/asset/balances")
        if funding_data and funding_data.get("data"):
            for item in funding_data["data"]:
                ccy = item.get("ccy", "UNKNOWN")
                avail = Decimal(str(item.get("availBal", 0) or 0))
                frozen = Decimal(str(item.get("frozenBal", 0) or 0))
                total = avail + frozen

                if total > 0:
                    if ccy in balances:
                        existing = balances[ccy]
                        balances[ccy] = Balance(
                            asset=ccy,
                            total=existing.total + total,
                            available=existing.available + avail,
                            staked=existing.staked,
                        )
                    else:
                        balances[ccy] = Balance(
                            asset=ccy,
                            total=total,
                            available=avail,
                        )

        # Earn balances
        earn_data = await self._request("GET", "/api/v5/finance/savings/balance")
        if earn_data and earn_data.get("data"):
            for item in earn_data["data"]:
                ccy = item.get("ccy", "UNKNOWN")
                earn_amount = Decimal(str(item.get("amt", 0) or 0))

                if earn_amount > 0:
                    if ccy in balances:
                        existing = balances[ccy]
                        balances[ccy] = Balance(
                            asset=ccy,
                            total=existing.total + earn_amount,
                            available=existing.available,
                            staked=existing.staked + earn_amount,
                        )
                    else:
                        balances[ccy] = Balance(
                            asset=ccy,
                            total=earn_amount,
                            available=Decimal("0"),
                            staked=earn_amount,
                        )

        return balances

    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """Get OKX Earn reward history."""
        rewards = []

        params: dict = {"type": "1"}  # type 1 = earn rewards
        if start_date:
            params["begin"] = str(int(start_date.timestamp() * 1000))
        if end_date:
            params["end"] = str(int(end_date.timestamp() * 1000))

        data = await self._request(
            "GET", "/api/v5/finance/savings/lending-history", params=params
        )

        if data and data.get("data"):
            for entry in data["data"]:
                tx_time = datetime.fromtimestamp(
                    int(entry.get("ts", 0)) / 1000, tz=timezone.utc
                )

                rewards.append(
                    StakingReward(
                        asset=entry.get("ccy", ""),
                        amount=Decimal(str(entry.get("earnings", 0))),
                        timestamp=tx_time,
                        source="okx_earn",
                    )
                )

        return rewards

    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Trade]:
        """Get trade fill history."""
        trades = []

        params: dict = {"instType": "SPOT"}
        if asset:
            params["instId"] = f"{asset.upper()}-USDT"
        if start_date:
            params["begin"] = str(int(start_date.timestamp() * 1000))
        if end_date:
            params["end"] = str(int(end_date.timestamp() * 1000))

        data = await self._request(
            "GET", "/api/v5/trade/fills-history", params=params
        )

        if data and data.get("data"):
            for fill in data["data"]:
                tx_time = datetime.fromtimestamp(
                    int(fill.get("ts", 0)) / 1000, tz=timezone.utc
                )

                # Parse instrument ID to get asset (e.g., "BTC-USDT" -> "BTC")
                inst_id = fill.get("instId", "")
                trade_asset = inst_id.split("-")[0] if "-" in inst_id else inst_id

                trades.append(
                    Trade(
                        id=fill.get("tradeId", ""),
                        timestamp=tx_time,
                        asset=trade_asset,
                        side=fill.get("side", ""),
                        amount=Decimal(str(fill.get("fillSz", 0))),
                        price=Decimal(str(fill.get("fillPx", 0))),
                        fee=abs(Decimal(str(fill.get("fee", 0)))),
                        fee_asset=fill.get("feeCcy", "USDT"),
                    )
                )

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

        Args:
            asset: Asset to trade (e.g., "BTC")
            side: "buy" or "sell"
            amount: Amount of base asset
            quote_amount: USD/USDT amount for buys
        """
        inst_id = f"{asset.upper()}-USDT"

        body: dict = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": side.lower(),
            "ordType": "market",
        }

        if side.lower() == "buy" and quote_amount:
            # Buy by quote currency amount
            body["sz"] = str(quote_amount)
            body["tgtCcy"] = "quote_ccy"
        elif amount:
            body["sz"] = str(amount)
            body["tgtCcy"] = "base_ccy"
        else:
            return OrderResult(
                success=False, error="Must specify amount or quote_amount"
            )

        try:
            data = await self._request("POST", "/api/v5/trade/order", body=body)

            if data and data.get("data"):
                order_info = data["data"][0]
                order_id = order_info.get("ordId", "")

                if order_info.get("sCode") != "0":
                    return OrderResult(
                        success=False,
                        error=order_info.get("sMsg", "Order failed"),
                    )

                # Fetch fill details
                fill_data = await self._request(
                    "GET",
                    "/api/v5/trade/order",
                    params={"instId": inst_id, "ordId": order_id},
                )

                if fill_data and fill_data.get("data"):
                    order_detail = fill_data["data"][0]
                    return OrderResult(
                        success=True,
                        order_id=order_id,
                        filled_amount=Decimal(
                            str(order_detail.get("accFillSz", 0))
                        ),
                        filled_price=Decimal(
                            str(order_detail.get("avgPx", 0) or 0)
                        ),
                        fee=abs(
                            Decimal(str(order_detail.get("fee", 0) or 0))
                        ),
                    )

                return OrderResult(success=True, order_id=order_id)

            return OrderResult(success=False, error="Order creation failed")

        except Exception as e:
            return OrderResult(success=False, error=str(e))

    async def get_ticker_price(self, asset: str) -> Decimal:
        """Get current price for an asset."""
        inst_id = f"{asset.upper()}-USDT"

        data = await self._public_request(
            "/api/v5/market/ticker", params={"instId": inst_id}
        )

        if data and data.get("data"):
            last = data["data"][0].get("last")
            if last:
                return Decimal(str(last))

        raise ValueError(f"Could not get price for {asset}")

    async def get_all_prices(self, assets: List[str]) -> Dict[str, Decimal]:
        """Get prices for multiple assets using batch ticker endpoint."""
        prices = {}

        data = await self._public_request(
            "/api/v5/market/tickers", params={"instType": "SPOT"}
        )

        if data and data.get("data"):
            # Build lookup set for requested assets
            wanted = {f"{a.upper()}-USDT" for a in assets}
            for ticker in data["data"]:
                inst_id = ticker.get("instId", "")
                if inst_id in wanted:
                    asset_name = inst_id.split("-")[0]
                    last = ticker.get("last")
                    if last:
                        prices[asset_name] = Decimal(str(last))

        return prices

    async def stake(self, asset: str, amount: Decimal) -> bool:
        """Subscribe to OKX Earn (Simple Earn)."""
        body = {
            "ccy": asset.upper(),
            "amt": str(amount),
            "rate": "0.01",  # Minimum lending rate
        }

        try:
            data = await self._request(
                "POST", "/api/v5/finance/savings/purchase-redempt",
                body={**body, "side": "purchase"},
            )
            return data is not None
        except Exception as e:
            logger.error(f"OKX Earn purchase failed: {e}")
            return False

    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """Redeem from OKX Earn."""
        body = {
            "ccy": asset.upper(),
            "amt": str(amount),
        }

        try:
            data = await self._request(
                "POST", "/api/v5/finance/savings/purchase-redempt",
                body={**body, "side": "redempt"},
            )
            return data is not None
        except Exception as e:
            logger.error(f"OKX Earn redemption failed: {e}")
            return False

    async def get_open_orders(self) -> List[Dict]:
        """Get all open orders."""
        data = await self._request(
            "GET", "/api/v5/trade/orders-pending", params={"instType": "SPOT"}
        )

        if data and data.get("data"):
            return [
                {
                    "order_id": o.get("ordId"),
                    "instrument": o.get("instId"),
                    "side": o.get("side"),
                    "type": o.get("ordType"),
                    "size": o.get("sz"),
                    "price": o.get("px"),
                    "filled": o.get("accFillSz"),
                    "status": o.get("state"),
                    "created_at": o.get("cTime"),
                }
                for o in data["data"]
            ]
        return []

    async def cancel_order(self, order_id: str, inst_id: str = "") -> bool:
        """Cancel a specific order."""
        if not inst_id:
            # Try to find the instrument from the order
            order_data = await self._request(
                "GET",
                "/api/v5/trade/order",
                params={"ordId": order_id, "instId": "BTC-USDT"},
            )
            if order_data and order_data.get("data"):
                inst_id = order_data["data"][0].get("instId", "")

        if not inst_id:
            return False

        data = await self._request(
            "POST",
            "/api/v5/trade/cancel-order",
            body={"instId": inst_id, "ordId": order_id},
        )
        return data is not None

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
