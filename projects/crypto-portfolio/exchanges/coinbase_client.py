"""
Coinbase and Coinbase Prime API client.

Supports both personal Coinbase accounts and institutional Coinbase Prime accounts.
"""

import hmac
import hashlib
import logging
import time
import base64
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import aiohttp

from .base import ExchangeClient, Balance, StakingReward, Trade, OrderResult

logger = logging.getLogger(__name__)


class CoinbaseClient(ExchangeClient):
    """Client for Coinbase retail API."""
    
    name = "coinbase"
    BASE_URL = "https://api.coinbase.com"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self._session
    
    def _sign_request(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate signature for Coinbase API request."""
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
    ) -> dict:
        """Make authenticated request to Coinbase API."""
        session = await self._get_session()
        timestamp = str(int(time.time()))
        body_str = json.dumps(body) if body else ""
        
        signature = self._sign_request(timestamp, method, path, body_str)
        
        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
        }
        
        url = f"{self.BASE_URL}{path}"
        
        async with session.request(method, url, headers=headers, data=body_str or None) as resp:
            data = await resp.json()
            if resp.status >= 400:
                raise Exception(f"Coinbase API error: {data}")
            return data
    
    async def get_balances(self) -> Dict[str, Balance]:
        """Get all account balances."""
        balances = {}
        cursor = None
        
        while True:
            path = "/api/v3/brokerage/accounts"
            if cursor:
                path += f"?cursor={cursor}"
            
            data = await self._request("GET", path)
            
            for account in data.get("accounts", []):
                asset = account["currency"]
                total = Decimal(account["available_balance"]["value"])
                hold = Decimal(account.get("hold", {}).get("value", "0"))
                
                if total > 0:
                    balances[asset] = Balance(
                        asset=asset,
                        total=total,
                        available=total - hold,
                        staked=Decimal("0"),  # Coinbase doesn't separate staked in this endpoint
                    )
            
            cursor = data.get("cursor")
            if not cursor or not data.get("has_next"):
                break
        
        return balances
    
    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """Get staking rewards from transaction history."""
        rewards = []
        cursor = None
        
        # Coinbase returns rewards as transactions with type "staking_reward"
        while True:
            path = "/api/v3/brokerage/transaction_summary"
            if cursor:
                path += f"?cursor={cursor}"
            
            try:
                data = await self._request("GET", path)
                
                for tx in data.get("transactions", []):
                    if tx.get("type") == "staking_reward":
                        tx_time = datetime.fromisoformat(tx["created_at"].replace("Z", "+00:00"))
                        
                        if start_date and tx_time < start_date:
                            continue
                        if end_date and tx_time > end_date:
                            continue
                        
                        rewards.append(StakingReward(
                            asset=tx["amount"]["currency"],
                            amount=Decimal(tx["amount"]["value"]),
                            timestamp=tx_time,
                            usd_value=Decimal(tx.get("native_amount", {}).get("value", "0")),
                            source="coinbase",
                        ))
                
                cursor = data.get("cursor")
                if not cursor or not data.get("has_next"):
                    break
                    
            except Exception as e:
                # If endpoint not available, try alternative
                logger.warning("Could not fetch staking rewards: %s", e)
                break
        
        return rewards
    
    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Trade]:
        """Get trade/fill history."""
        trades = []
        
        # Use fills endpoint
        path = "/api/v3/brokerage/orders/historical/fills"
        params = []
        
        if start_date:
            params.append(f"start_sequence_timestamp={start_date.isoformat()}")
        if end_date:
            params.append(f"end_sequence_timestamp={end_date.isoformat()}")
        if asset:
            params.append(f"product_id={asset}-USD")
        
        if params:
            path += "?" + "&".join(params)
        
        try:
            data = await self._request("GET", path)
            
            for fill in data.get("fills", []):
                trades.append(Trade(
                    id=fill["trade_id"],
                    timestamp=datetime.fromisoformat(fill["trade_time"].replace("Z", "+00:00")),
                    asset=fill["product_id"].split("-")[0],
                    side=fill["side"].lower(),
                    amount=Decimal(fill["size"]),
                    price=Decimal(fill["price"]),
                    fee=Decimal(fill.get("commission", "0")),
                    fee_asset="USD",
                ))
        except Exception as e:
            logger.warning("Could not fetch trade history: %s", e)
        
        return trades
    
    async def place_market_order(
        self,
        asset: str,
        side: str,
        amount: Optional[Decimal] = None,
        quote_amount: Optional[Decimal] = None,
    ) -> OrderResult:
        """Place a market order."""
        order_config = {
            "market_market_ioc": {}
        }
        
        if side == "buy" and quote_amount:
            order_config["market_market_ioc"]["quote_size"] = str(quote_amount)
        elif amount:
            order_config["market_market_ioc"]["base_size"] = str(amount)
        else:
            return OrderResult(success=False, error="Must specify amount or quote_amount")
        
        body = {
            "client_order_id": f"pm_{int(time.time() * 1000)}",
            "product_id": f"{asset}-USD",
            "side": side.upper(),
            "order_configuration": order_config,
        }
        
        try:
            data = await self._request("POST", "/api/v3/brokerage/orders", body)
            
            return OrderResult(
                success=data.get("success", False),
                order_id=data.get("order_id"),
                filled_amount=Decimal(data.get("filled_size", "0")),
                filled_price=Decimal(data.get("average_filled_price", "0")),
                fee=Decimal(data.get("total_fees", "0")),
            )
        except Exception as e:
            return OrderResult(success=False, error=str(e))
    
    async def get_ticker_price(self, asset: str) -> Decimal:
        """Get current price for an asset."""
        path = f"/api/v3/brokerage/products/{asset}-USD"
        data = await self._request("GET", path)
        return Decimal(data["price"])
    
    async def stake(self, asset: str, amount: Decimal) -> bool:
        """Stake an asset (via Coinbase Earn)."""
        # Coinbase retail staking is done through a different flow
        # This would require the Coinbase Earn API
        raise NotImplementedError("Use Coinbase Prime for programmatic staking")
    
    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """Unstake an asset."""
        raise NotImplementedError("Use Coinbase Prime for programmatic staking")
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


class CoinbasePrimeClient(ExchangeClient):
    """Client for Coinbase Prime institutional API."""
    
    name = "coinbase_prime"
    BASE_URL = "https://api.prime.coinbase.com"
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str,
        portfolio_id: str,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.portfolio_id = portfolio_id
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self._session
    
    def _sign_request(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate signature for Coinbase Prime API request."""
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message.encode(),
            hashlib.sha256
        )
        return base64.b64encode(signature.digest()).decode()
    
    async def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
    ) -> dict:
        """Make authenticated request to Coinbase Prime API."""
        session = await self._get_session()
        timestamp = str(int(time.time()))
        body_str = json.dumps(body) if body else ""
        
        signature = self._sign_request(timestamp, method, path, body_str)
        
        headers = {
            "X-CB-ACCESS-KEY": self.api_key,
            "X-CB-ACCESS-SIGNATURE": signature,
            "X-CB-ACCESS-TIMESTAMP": timestamp,
            "X-CB-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }
        
        url = f"{self.BASE_URL}{path}"
        
        async with session.request(method, url, headers=headers, data=body_str or None) as resp:
            data = await resp.json()
            if resp.status >= 400:
                raise Exception(f"Coinbase Prime API error: {data}")
            return data
    
    async def get_balances(self) -> Dict[str, Balance]:
        """Get all portfolio balances."""
        path = f"/v1/portfolios/{self.portfolio_id}/balances"
        data = await self._request("GET", path)
        
        balances = {}
        for balance in data.get("balances", []):
            asset = balance["symbol"]
            total = Decimal(balance["amount"])
            holds = Decimal(balance.get("holds", "0"))
            staked = Decimal(balance.get("staked_balance", "0"))
            
            if total > 0:
                balances[asset] = Balance(
                    asset=asset,
                    total=total,
                    available=total - holds - staked,
                    staked=staked,
                )
        
        return balances
    
    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """Get staking rewards history."""
        rewards = []
        
        path = f"/v1/portfolios/{self.portfolio_id}/staking/rewards"
        params = []
        
        if start_date:
            params.append(f"start_time={start_date.isoformat()}")
        if end_date:
            params.append(f"end_time={end_date.isoformat()}")
        
        if params:
            path += "?" + "&".join(params)
        
        try:
            data = await self._request("GET", path)
            
            for reward in data.get("rewards", []):
                rewards.append(StakingReward(
                    asset=reward["symbol"],
                    amount=Decimal(reward["amount"]),
                    timestamp=datetime.fromisoformat(reward["created_at"].replace("Z", "+00:00")),
                    usd_value=Decimal(reward.get("usd_value", "0")),
                    source="coinbase_prime",
                ))
        except Exception as e:
            logger.warning("Could not fetch staking rewards: %s", e)
        
        return rewards
    
    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        asset: Optional[str] = None,
    ) -> List[Trade]:
        """Get trade history."""
        trades = []
        
        path = f"/v1/portfolios/{self.portfolio_id}/fills"
        params = []
        
        if start_date:
            params.append(f"start_time={start_date.isoformat()}")
        if end_date:
            params.append(f"end_time={end_date.isoformat()}")
        
        if params:
            path += "?" + "&".join(params)
        
        try:
            data = await self._request("GET", path)
            
            for fill in data.get("fills", []):
                fill_asset = fill["product_id"].split("-")[0]
                if asset and fill_asset != asset:
                    continue
                
                trades.append(Trade(
                    id=fill["fill_id"],
                    timestamp=datetime.fromisoformat(fill["time"].replace("Z", "+00:00")),
                    asset=fill_asset,
                    side=fill["side"].lower(),
                    amount=Decimal(fill["size"]),
                    price=Decimal(fill["price"]),
                    fee=Decimal(fill.get("commission", "0")),
                    fee_asset="USD",
                ))
        except Exception as e:
            logger.warning("Could not fetch trade history: %s", e)
        
        return trades
    
    async def place_market_order(
        self,
        asset: str,
        side: str,
        amount: Optional[Decimal] = None,
        quote_amount: Optional[Decimal] = None,
    ) -> OrderResult:
        """Place a market order."""
        body = {
            "portfolio_id": self.portfolio_id,
            "product_id": f"{asset}-USD",
            "side": side.upper(),
            "type": "MARKET",
            "client_order_id": f"pm_{int(time.time() * 1000)}",
        }
        
        if side == "buy" and quote_amount:
            body["quote_value"] = str(quote_amount)
        elif amount:
            body["base_quantity"] = str(amount)
        else:
            return OrderResult(success=False, error="Must specify amount or quote_amount")
        
        try:
            data = await self._request("POST", f"/v1/portfolios/{self.portfolio_id}/order", body)
            
            return OrderResult(
                success=True,
                order_id=data.get("order_id"),
                filled_amount=Decimal(data.get("filled_quantity", "0")),
                filled_price=Decimal(data.get("average_filled_price", "0")),
                fee=Decimal(data.get("fee", "0")),
            )
        except Exception as e:
            return OrderResult(success=False, error=str(e))
    
    async def get_ticker_price(self, asset: str) -> Decimal:
        """Get current price for an asset."""
        path = f"/v1/products/{asset}-USD"
        data = await self._request("GET", path)
        return Decimal(data["price"])
    
    async def stake(self, asset: str, amount: Decimal) -> bool:
        """Stake an asset via Prime staking."""
        body = {
            "symbol": asset,
            "amount": str(amount),
        }
        
        try:
            await self._request(
                "POST",
                f"/v1/portfolios/{self.portfolio_id}/staking/stake",
                body
            )
            return True
        except Exception as e:
            logger.warning("Staking failed: %s", e)
            return False
    
    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """Unstake an asset."""
        body = {
            "symbol": asset,
            "amount": str(amount),
        }
        
        try:
            await self._request(
                "POST",
                f"/v1/portfolios/{self.portfolio_id}/staking/unstake",
                body
            )
            return True
        except Exception as e:
            logger.warning("Unstaking failed: %s", e)
            return False
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
