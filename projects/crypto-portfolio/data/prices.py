"""
Price data service.

Fetches cryptocurrency prices from CoinGecko or other sources,
with caching to minimize API calls.
"""

import asyncio
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import aiohttp

from config import COINGECKO_IDS, settings

logger = logging.getLogger(__name__)


class PriceCache:
    """Simple in-memory cache for prices."""
    
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._cache: Dict[str, tuple[Decimal, float]] = {}
    
    def get(self, asset: str) -> Optional[Decimal]:
        """Get cached price if not expired."""
        if asset not in self._cache:
            return None
        
        price, timestamp = self._cache[asset]
        if time.time() - timestamp > self.ttl:
            del self._cache[asset]
            return None
        
        return price
    
    def set(self, asset: str, price: Decimal):
        """Cache a price."""
        self._cache[asset] = (price, time.time())
    
    def set_many(self, prices: Dict[str, Decimal]):
        """Cache multiple prices."""
        now = time.time()
        for asset, price in prices.items():
            self._cache[asset] = (price, now)
    
    def clear(self):
        """Clear all cached prices."""
        self._cache.clear()


class PriceService:
    """Service for fetching cryptocurrency prices."""
    
    COINGECKO_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, cache_ttl: int = None):
        self.cache = PriceCache(cache_ttl or settings.data.price_cache_duration)
        self._session: Optional[aiohttp.ClientSession] = None
        self.api_key = settings.market_data.coingecko_api_key
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def _get_coingecko_id(self, asset: str) -> Optional[str]:
        """Get CoinGecko ID for an asset symbol."""
        # Check explicit mapping first
        if asset in COINGECKO_IDS:
            return COINGECKO_IDS[asset]
        
        # Try lowercase as fallback
        return asset.lower()
    
    async def get_price(self, asset: str) -> Decimal:
        """Get price for a single asset."""
        # Check cache first
        cached = self.cache.get(asset)
        if cached is not None:
            return cached
        
        # Stablecoins are always ~$1
        if asset in ("USDC", "USDT", "DAI", "BUSD", "USD"):
            price = Decimal("1.0")
            self.cache.set(asset, price)
            return price
        
        # Fetch from CoinGecko
        coingecko_id = self._get_coingecko_id(asset)
        if not coingecko_id:
            raise ValueError(f"Unknown asset: {asset}")
        
        session = await self._get_session()
        
        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        
        url = f"{self.COINGECKO_URL}/simple/price"
        params = {
            "ids": coingecko_id,
            "vs_currencies": "usd",
        }
        
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status == 429:
                # Rate limited - wait and retry
                await asyncio.sleep(60)
                return await self.get_price(asset)
            
            data = await resp.json()
            
            if coingecko_id not in data:
                raise ValueError(f"No price data for {asset} ({coingecko_id})")
            
            price = Decimal(str(data[coingecko_id]["usd"]))
            self.cache.set(asset, price)
            return price
    
    async def get_prices(self, assets: List[str]) -> Dict[str, Decimal]:
        """Get prices for multiple assets efficiently."""
        prices = {}
        assets_to_fetch = []
        
        # Check cache first
        for asset in assets:
            cached = self.cache.get(asset)
            if cached is not None:
                prices[asset] = cached
            elif asset in ("USDC", "USDT", "DAI", "BUSD", "USD"):
                prices[asset] = Decimal("1.0")
            else:
                assets_to_fetch.append(asset)
        
        if not assets_to_fetch:
            return prices
        
        # Batch fetch from CoinGecko
        coingecko_ids = []
        asset_map = {}  # coingecko_id -> asset
        
        for asset in assets_to_fetch:
            cg_id = self._get_coingecko_id(asset)
            if cg_id:
                coingecko_ids.append(cg_id)
                asset_map[cg_id] = asset
        
        if not coingecko_ids:
            return prices
        
        session = await self._get_session()
        
        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        
        url = f"{self.COINGECKO_URL}/simple/price"
        params = {
            "ids": ",".join(coingecko_ids),
            "vs_currencies": "usd",
        }
        
        try:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 429:
                    # Rate limited - fall back to individual fetches with delay
                    for asset in assets_to_fetch:
                        try:
                            await asyncio.sleep(1)
                            prices[asset] = await self.get_price(asset)
                        except Exception as e:
                            logger.warning("Failed to fetch price for %s: %s", asset, e)
                    return prices
                
                data = await resp.json()
                
                fetched_prices = {}
                for cg_id, price_data in data.items():
                    asset = asset_map.get(cg_id)
                    if asset and "usd" in price_data:
                        price = Decimal(str(price_data["usd"]))
                        prices[asset] = price
                        fetched_prices[asset] = price
                
                # Cache all fetched prices
                self.cache.set_many(fetched_prices)
                
        except Exception as e:
            logger.warning("Failed to fetch prices: %s", e)
        
        return prices
    
    async def get_historical_price(
        self,
        asset: str,
        date: datetime,
    ) -> Optional[Decimal]:
        """Get historical price for a specific date."""
        coingecko_id = self._get_coingecko_id(asset)
        if not coingecko_id:
            return None
        
        session = await self._get_session()
        
        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        
        # CoinGecko expects dd-mm-yyyy format
        date_str = date.strftime("%d-%m-%Y")
        
        url = f"{self.COINGECKO_URL}/coins/{coingecko_id}/history"
        params = {
            "date": date_str,
        }
        
        try:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                
                if "market_data" in data and "current_price" in data["market_data"]:
                    return Decimal(str(data["market_data"]["current_price"]["usd"]))
                
                return None
        except Exception as e:
            logger.warning("Failed to fetch historical price for %s: %s", asset, e)
            return None
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()


# Convenience function for quick price lookups
async def get_current_prices(assets: List[str]) -> Dict[str, Decimal]:
    """Quick function to get current prices."""
    service = PriceService()
    try:
        return await service.get_prices(assets)
    finally:
        await service.close()
