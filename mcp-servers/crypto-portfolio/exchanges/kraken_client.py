"""
Kraken API client.

Supports trading, staking, and account management.
"""

import json
import hmac
import hashlib
import base64
import os
import time
import urllib.parse
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import logging
import aiohttp

from .base import ExchangeClient, Balance, StakingReward, Trade, OrderResult

logger = logging.getLogger(__name__)


# Kraken uses different symbols than standard
KRAKEN_SYMBOL_MAP = {
    "XBT": "BTC",
    "XXBT": "BTC",
    "XETH": "ETH",
    "XXRP": "XRP",
    "XXLM": "XLM",
    "ZUSD": "USD",
    "ZEUR": "EUR",
}

STANDARD_TO_KRAKEN = {
    "BTC": "XBT",
    "ETH": "ETH",
}


STAKING_SUFFIXES = (".S", ".B", ".M", ".P")

# Numbered staking assets: Kraken appends 2-digit numbers (e.g. GRT28, FLOW14, KAVA21)
import re
_NUMBERED_STAKING_RE = re.compile(r'^([A-Z]+)\d{2,3}$')


def normalize_symbol(kraken_symbol: str) -> str:
    """Convert Kraken symbol to standard symbol."""
    if kraken_symbol in KRAKEN_SYMBOL_MAP:
        return KRAKEN_SYMBOL_MAP[kraken_symbol]

    # Handle staking suffixes: .S, .B, .M, .P
    for suffix in STAKING_SUFFIXES:
        if kraken_symbol.endswith(suffix):
            base = kraken_symbol[:-len(suffix)]
            return normalize_symbol(base)

    # Handle numbered staking assets (e.g. GRT28 -> GRT, FLOW14 -> FLOW)
    m = _NUMBERED_STAKING_RE.match(kraken_symbol)
    if m:
        return normalize_symbol(m.group(1))

    return kraken_symbol


def is_staked_symbol(kraken_symbol: str) -> bool:
    """Check if a Kraken symbol represents a staked asset."""
    for suffix in STAKING_SUFFIXES:
        if kraken_symbol.endswith(suffix):
            return True
    if _NUMBERED_STAKING_RE.match(kraken_symbol):
        return True
    return False


def to_kraken_symbol(standard_symbol: str) -> str:
    """Convert standard symbol to Kraken symbol."""
    return STANDARD_TO_KRAKEN.get(standard_symbol, standard_symbol)


class KrakenClient(ExchangeClient):
    """Client for Kraken API."""
    
    name = "kraken"
    BASE_URL = "https://api.kraken.com"
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self._session: Optional[aiohttp.ClientSession] = None

    @classmethod
    def from_key_file(cls, key_file: str) -> "KrakenClient":
        """Create client from a JSON key file.

        Args:
            key_file: Path to JSON file containing 'api_key' and 'api_secret'.
        """
        with open(os.path.expanduser(key_file)) as f:
            data = json.load(f)
        return cls(api_key=data["api_key"], api_secret=data["api_secret"])
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _sign_request(self, path: str, data: dict, nonce: str) -> str:
        """Generate signature for Kraken API request."""
        post_data = urllib.parse.urlencode(data)
        encoded = (nonce + post_data).encode()
        message = path.encode() + hashlib.sha256(encoded).digest()
        
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        )
        return base64.b64encode(signature.digest()).decode()
    
    async def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        private: bool = False,
    ) -> dict:
        """Make request to Kraken API."""
        session = await self._get_session()
        url = f"{self.BASE_URL}{path}"
        
        if data is None:
            data = {}
        
        headers = {}
        
        if private:
            nonce = str(int(time.time() * 1000))
            data["nonce"] = nonce
            
            signature = self._sign_request(path, data, nonce)
            headers = {
                "API-Key": self.api_key,
                "API-Sign": signature,
            }
        
        if method == "POST":
            async with session.post(url, data=data, headers=headers) as resp:
                result = await resp.json()
        else:
            async with session.get(url, params=data, headers=headers) as resp:
                result = await resp.json()
        
        if result.get("error"):
            raise Exception(f"Kraken API error: {result['error']}")
        
        return result.get("result", {})
    
    async def get_balances(self) -> Dict[str, Balance]:
        """Get all account balances including staked assets."""
        # Get regular balances
        data = await self._request("POST", "/0/private/Balance", private=True)
        
        balances = {}
        staked_balances = {}
        
        for kraken_symbol, amount in data.items():
            amount = Decimal(str(amount))
            if amount <= 0:
                continue

            # Check if this is a staked asset (.S, .B, .M, .P, or numbered like GRT28)
            if is_staked_symbol(kraken_symbol):
                base_symbol = normalize_symbol(kraken_symbol)
                staked_balances[base_symbol] = staked_balances.get(base_symbol, Decimal("0")) + amount
            else:
                symbol = normalize_symbol(kraken_symbol)
                if symbol not in balances:
                    balances[symbol] = Balance(
                        asset=symbol,
                        total=amount,
                        available=amount,
                        staked=Decimal("0"),
                    )
                else:
                    balances[symbol].total += amount
                    balances[symbol].available += amount
        
        # Merge staked balances
        for symbol, staked_amount in staked_balances.items():
            if symbol in balances:
                balances[symbol].staked = staked_amount
                balances[symbol].total += staked_amount
            else:
                balances[symbol] = Balance(
                    asset=symbol,
                    total=staked_amount,
                    available=Decimal("0"),
                    staked=staked_amount,
                )
        
        return balances
    
    async def get_staking_rewards(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StakingReward]:
        """Get staking rewards from ledger."""
        rewards = []
        
        params = {
            "type": "staking",
        }
        
        if start_date:
            params["start"] = int(start_date.timestamp())
        if end_date:
            params["end"] = int(end_date.timestamp())
        
        try:
            data = await self._request("POST", "/0/private/Ledgers", params, private=True)
            
            for ledger_id, entry in data.get("ledger", {}).items():
                if entry.get("type") == "staking":
                    symbol = normalize_symbol(entry["asset"])
                    
                    rewards.append(StakingReward(
                        asset=symbol,
                        amount=Decimal(str(entry["amount"])),
                        timestamp=datetime.fromtimestamp(entry["time"]),
                        tx_hash=ledger_id,
                        source="kraken",
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
        """Get trade history."""
        trades = []
        
        params = {}
        if start_date:
            params["start"] = int(start_date.timestamp())
        if end_date:
            params["end"] = int(end_date.timestamp())
        
        try:
            data = await self._request("POST", "/0/private/TradesHistory", params, private=True)
            
            for trade_id, trade_data in data.get("trades", {}).items():
                pair = trade_data["pair"]
                
                # Parse the trading pair to get the asset
                # Kraken pairs are like XXBTZUSD, ETHUSDT, etc.
                trade_asset = None
                for kraken_sym, std_sym in KRAKEN_SYMBOL_MAP.items():
                    if pair.startswith(kraken_sym):
                        trade_asset = std_sym
                        break
                
                if not trade_asset:
                    # Try to parse manually
                    if "USD" in pair:
                        trade_asset = normalize_symbol(pair.split("USD")[0])
                    else:
                        continue
                
                if asset and trade_asset != asset:
                    continue
                
                trades.append(Trade(
                    id=trade_id,
                    timestamp=datetime.fromtimestamp(trade_data["time"]),
                    asset=trade_asset,
                    side="buy" if trade_data["type"] == "buy" else "sell",
                    amount=Decimal(str(trade_data["vol"])),
                    price=Decimal(str(trade_data["price"])),
                    fee=Decimal(str(trade_data["fee"])),
                    fee_asset="USD",
                ))
        except Exception as e:
            logger.warning(f"Could not fetch trade history: {e}")
        
        return trades
    
    async def place_market_order(
        self,
        asset: str,
        side: str,
        amount: Optional[Decimal] = None,
        quote_amount: Optional[Decimal] = None,
    ) -> OrderResult:
        """Place a market order."""
        kraken_symbol = to_kraken_symbol(asset)
        pair = f"{kraken_symbol}USD"
        
        params = {
            "pair": pair,
            "type": side.lower(),
            "ordertype": "market",
        }
        
        if quote_amount and side == "buy":
            # Kraken doesn't directly support quote amounts for market orders
            # We need to get the price first and calculate
            price = await self.get_ticker_price(asset)
            params["volume"] = str(quote_amount / price)
        elif amount:
            params["volume"] = str(amount)
        else:
            return OrderResult(success=False, error="Must specify amount or quote_amount")
        
        try:
            data = await self._request("POST", "/0/private/AddOrder", params, private=True)
            
            order_ids = data.get("txid", [])
            
            return OrderResult(
                success=True,
                order_id=order_ids[0] if order_ids else None,
                filled_amount=Decimal(params["volume"]),
            )
        except Exception as e:
            return OrderResult(success=False, error=str(e))
    
    async def get_ticker_price(self, asset: str) -> Decimal:
        """Get current price for an asset."""
        kraken_symbol = to_kraken_symbol(asset)
        
        # Try different pair formats
        pairs_to_try = [
            f"{kraken_symbol}USD",
            f"X{kraken_symbol}ZUSD",
            f"{kraken_symbol}USDT",
        ]
        
        for pair in pairs_to_try:
            try:
                data = await self._request("GET", "/0/public/Ticker", {"pair": pair})
                if data:
                    # Get the first (and usually only) result
                    ticker = list(data.values())[0]
                    # 'c' is the last trade closed [price, lot volume]
                    return Decimal(str(ticker["c"][0]))
            except Exception:
                continue
        
        raise Exception(f"Could not get price for {asset}")
    
    async def stake(self, asset: str, amount: Decimal) -> bool:
        """Stake an asset on Kraken."""
        params = {
            "asset": to_kraken_symbol(asset),
            "amount": str(amount),
            "method": f"{asset}.S",  # Staking method
        }
        
        try:
            await self._request("POST", "/0/private/Stake", params, private=True)
            return True
        except Exception as e:
            logger.error(f"Staking failed: {e}")
            return False
    
    async def unstake(self, asset: str, amount: Decimal) -> bool:
        """Unstake an asset on Kraken."""
        params = {
            "asset": f"{to_kraken_symbol(asset)}.S",
            "amount": str(amount),
        }
        
        try:
            await self._request("POST", "/0/private/Unstake", params, private=True)
            return True
        except Exception as e:
            logger.error(f"Unstaking failed: {e}")
            return False
    
    async def get_stakeable_assets(self) -> Dict[str, dict]:
        """Get list of stakeable assets and their conditions."""
        try:
            data = await self._request("POST", "/0/private/Staking/Assets", private=True)
            return data
        except Exception as e:
            logger.error(f"Could not get stakeable assets: {e}")
            return {}
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
