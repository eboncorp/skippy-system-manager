"""
Data Providers Module

Real API integrations for fetching signal data.
Supports multiple data sources with fallbacks.

FREE APIs:
- CoinGecko (prices, basic data)
- Alternative.me (Fear & Greed)
- Blockchain.com (on-chain basics)
- Coinglass (derivatives data)
- Mempool.space (BTC mempool)

PAID/PREMIUM APIs (optional):
- Glassnode (comprehensive on-chain)
- CryptoQuant (on-chain + derivatives)
- Santiment (on-chain + social)
- IntoTheBlock (on-chain analytics)
- LunarCrush (social sentiment)
- The TIE (institutional data)
- Kaiko (market data)
- Skew (derivatives)
"""

import asyncio
import aiohttp
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """API configuration with optional keys."""
    coingecko_api_key: Optional[str] = None
    glassnode_api_key: Optional[str] = None
    cryptoquant_api_key: Optional[str] = None
    santiment_api_key: Optional[str] = None
    lunarcrush_api_key: Optional[str] = None
    coinglass_api_key: Optional[str] = None
    the_tie_api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load API keys from environment variables."""
        return cls(
            coingecko_api_key=os.getenv("COINGECKO_API_KEY"),
            glassnode_api_key=os.getenv("GLASSNODE_API_KEY"),
            cryptoquant_api_key=os.getenv("CRYPTOQUANT_API_KEY"),
            santiment_api_key=os.getenv("SANTIMENT_API_KEY"),
            lunarcrush_api_key=os.getenv("LUNARCRUSH_API_KEY"),
            coinglass_api_key=os.getenv("COINGLASS_API_KEY"),
            the_tie_api_key=os.getenv("THE_TIE_API_KEY"),
        )


class DataProviders:
    """
    Unified data provider that aggregates from multiple sources.
    Falls back to free APIs when premium APIs are unavailable.
    """
    
    ASSET_MAP = {
        "BTC": {"coingecko": "bitcoin", "symbol": "btcusd"},
        "ETH": {"coingecko": "ethereum", "symbol": "ethusd"},
        "SOL": {"coingecko": "solana", "symbol": "solusd"},
        "AVAX": {"coingecko": "avalanche-2", "symbol": "avaxusd"},
        "LINK": {"coingecko": "chainlink", "symbol": "linkusd"},
        "DOT": {"coingecko": "polkadot", "symbol": "dotusd"},
        "ATOM": {"coingecko": "cosmos", "symbol": "atomusd"},
        "NEAR": {"coingecko": "near", "symbol": "nearusd"},
        "ARB": {"coingecko": "arbitrum", "symbol": "arbusd"},
        "OP": {"coingecko": "optimism", "symbol": "opusd"},
    }
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig.from_env()
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                return data
        return None
    
    def _set_cache(self, key: str, data: Any):
        self._cache[key] = (data, datetime.utcnow())
    
    # =========================================================================
    # PRICE & MARKET DATA (CoinGecko)
    # =========================================================================
    
    async def get_price_data(self, asset: str) -> Optional[Dict]:
        """
        Get current price and market data from CoinGecko.
        
        Returns:
            {
                "price": float,
                "price_change_24h": float,
                "price_change_7d": float,
                "volume_24h": float,
                "market_cap": float,
                "ath": float,
                "ath_change_pct": float,
            }
        """
        cache_key = f"price_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            cg_id = self.ASSET_MAP.get(asset, {}).get("coingecko", asset.lower())
            
            url = f"https://api.coingecko.com/api/v3/coins/{cg_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
            }
            
            headers = {}
            if self.config.coingecko_api_key:
                headers["x-cg-pro-api-key"] = self.config.coingecko_api_key
            
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    market = data.get("market_data", {})
                    
                    result = {
                        "price": market.get("current_price", {}).get("usd", 0),
                        "price_change_24h": market.get("price_change_percentage_24h", 0),
                        "price_change_7d": market.get("price_change_percentage_7d", 0),
                        "volume_24h": market.get("total_volume", {}).get("usd", 0),
                        "market_cap": market.get("market_cap", {}).get("usd", 0),
                        "ath": market.get("ath", {}).get("usd", 0),
                        "ath_change_pct": market.get("ath_change_percentage", {}).get("usd", 0),
                        "high_24h": market.get("high_24h", {}).get("usd", 0),
                        "low_24h": market.get("low_24h", {}).get("usd", 0),
                    }
                    
                    self._set_cache(cache_key, result)
                    return result
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
        
        return None
    
    async def get_historical_prices(self, asset: str, days: int = 365) -> Optional[List[Dict]]:
        """
        Get historical OHLC data.
        
        Returns list of:
            {"timestamp": int, "open": float, "high": float, "low": float, "close": float}
        """
        cache_key = f"history_{asset}_{days}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            cg_id = self.ASSET_MAP.get(asset, {}).get("coingecko", asset.lower())
            
            url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/ohlc"
            params = {"vs_currency": "usd", "days": days}
            
            headers = {}
            if self.config.coingecko_api_key:
                headers["x-cg-pro-api-key"] = self.config.coingecko_api_key
            
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # CoinGecko returns [timestamp, open, high, low, close]
                    result = [
                        {
                            "timestamp": d[0],
                            "open": d[1],
                            "high": d[2],
                            "low": d[3],
                            "close": d[4],
                        }
                        for d in data
                    ]
                    self._set_cache(cache_key, result)
                    return result
        except Exception as e:
            logger.error(f"Error fetching historical prices: {e}")
        
        return None
    
    # =========================================================================
    # FEAR & GREED INDEX (Alternative.me - FREE)
    # =========================================================================
    
    async def get_fear_greed(self) -> Optional[Dict]:
        """
        Get Fear & Greed Index from Alternative.me.
        
        Returns:
            {"value": int (0-100), "classification": str}
        """
        cache_key = "fear_greed"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            url = "https://api.alternative.me/fng/?limit=1"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = {
                        "value": int(data["data"][0]["value"]),
                        "classification": data["data"][0]["value_classification"],
                    }
                    self._set_cache(cache_key, result)
                    return result
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")
        
        return None
    
    # =========================================================================
    # DERIVATIVES DATA (Coinglass - FREE tier available)
    # =========================================================================
    
    async def get_funding_rates(self, asset: str) -> Optional[Dict]:
        """
        Get funding rates from Coinglass.
        
        Returns:
            {"rate": float, "predicted_rate": float}
        """
        cache_key = f"funding_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            symbol = asset.upper()
            
            # Coinglass API
            url = f"https://open-api.coinglass.com/public/v2/funding"
            params = {"symbol": symbol}
            
            headers = {}
            if self.config.coinglass_api_key:
                headers["coinglassSecret"] = self.config.coinglass_api_key
            
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success") and data.get("data"):
                        # Average across exchanges
                        rates = [
                            float(ex.get("rate", 0))
                            for ex in data["data"]
                            if ex.get("rate")
                        ]
                        avg_rate = sum(rates) / len(rates) if rates else 0
                        
                        result = {
                            "rate": avg_rate,
                            "rate_pct": avg_rate * 100,
                        }
                        self._set_cache(cache_key, result)
                        return result
        except Exception as e:
            logger.error(f"Error fetching funding rates: {e}")
        
        return None
    
    async def get_open_interest(self, asset: str) -> Optional[Dict]:
        """
        Get open interest data from Coinglass.
        
        Returns:
            {"oi_usd": float, "change_24h_pct": float, "price_change_24h": float}
        """
        cache_key = f"oi_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            symbol = asset.upper()
            
            url = f"https://open-api.coinglass.com/public/v2/open_interest"
            params = {"symbol": symbol}
            
            headers = {}
            if self.config.coinglass_api_key:
                headers["coinglassSecret"] = self.config.coinglass_api_key
            
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success") and data.get("data"):
                        total_oi = sum(
                            float(ex.get("openInterest", 0))
                            for ex in data["data"]
                        )
                        
                        # Get price data for change
                        price_data = await self.get_price_data(asset)
                        price_change = price_data.get("price_change_24h", 0) if price_data else 0
                        
                        result = {
                            "oi_usd": total_oi,
                            "change_24h_pct": 0,  # Would need historical OI
                            "price_change_24h": price_change,
                        }
                        self._set_cache(cache_key, result)
                        return result
        except Exception as e:
            logger.error(f"Error fetching open interest: {e}")
        
        return None
    
    async def get_liquidations(self, asset: str) -> Optional[Dict]:
        """
        Get liquidation data from Coinglass.
        
        Returns:
            {"long_liquidations_usd": float, "short_liquidations_usd": float}
        """
        cache_key = f"liqs_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            symbol = asset.upper()
            
            url = f"https://open-api.coinglass.com/public/v2/liquidation"
            params = {"symbol": symbol, "time_type": 1}  # 24h
            
            headers = {}
            if self.config.coinglass_api_key:
                headers["coinglassSecret"] = self.config.coinglass_api_key
            
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success") and data.get("data"):
                        long_liqs = sum(
                            float(ex.get("longLiquidationUsd", 0))
                            for ex in data["data"]
                        )
                        short_liqs = sum(
                            float(ex.get("shortLiquidationUsd", 0))
                            for ex in data["data"]
                        )
                        
                        result = {
                            "long_liquidations_usd": long_liqs,
                            "short_liquidations_usd": short_liqs,
                            "total": long_liqs + short_liqs,
                        }
                        self._set_cache(cache_key, result)
                        return result
        except Exception as e:
            logger.error(f"Error fetching liquidations: {e}")
        
        return None
    
    async def get_long_short_ratio(self, asset: str) -> Optional[Dict]:
        """
        Get long/short ratio from Coinglass.
        
        Returns:
            {"ratio": float}  # >1 means more longs
        """
        cache_key = f"lsr_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            symbol = asset.upper()
            
            url = f"https://open-api.coinglass.com/public/v2/long_short"
            params = {"symbol": symbol, "time_type": 1}
            
            headers = {}
            if self.config.coinglass_api_key:
                headers["coinglassSecret"] = self.config.coinglass_api_key
            
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success") and data.get("data"):
                        # Average across exchanges
                        ratios = [
                            float(ex.get("longRate", 50)) / float(ex.get("shortRate", 50))
                            for ex in data["data"]
                            if ex.get("longRate") and ex.get("shortRate")
                        ]
                        avg_ratio = sum(ratios) / len(ratios) if ratios else 1.0
                        
                        result = {"ratio": avg_ratio}
                        self._set_cache(cache_key, result)
                        return result
        except Exception as e:
            logger.error(f"Error fetching long/short ratio: {e}")
        
        return None
    
    # =========================================================================
    # MEMPOOL DATA (Mempool.space - FREE)
    # =========================================================================
    
    async def get_mempool_data(self, asset: str = "BTC") -> Optional[Dict]:
        """
        Get mempool and fee data from mempool.space (BTC only).
        
        Returns:
            {"avg_fee_rate": float, "mempool_size_mb": float}
        """
        if asset.upper() != "BTC":
            return None
        
        cache_key = "mempool_btc"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            
            # Get recommended fees
            fees_url = "https://mempool.space/api/v1/fees/recommended"
            async with session.get(fees_url) as resp:
                if resp.status == 200:
                    fees = await resp.json()
                    avg_fee = (
                        fees.get("fastestFee", 0) +
                        fees.get("halfHourFee", 0) +
                        fees.get("hourFee", 0)
                    ) / 3
            
            # Get mempool stats
            mempool_url = "https://mempool.space/api/mempool"
            async with session.get(mempool_url) as resp:
                if resp.status == 200:
                    mempool = await resp.json()
                    mempool_size = mempool.get("vsize", 0) / 1e6  # Convert to MB
            
            result = {
                "avg_fee_rate": avg_fee,
                "mempool_size_mb": mempool_size,
            }
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Error fetching mempool data: {e}")
        
        return None
    
    # =========================================================================
    # ON-CHAIN DATA (Glassnode - PREMIUM, with fallbacks)
    # =========================================================================
    
    async def get_exchange_flows(self, asset: str) -> Optional[Dict]:
        """
        Get exchange flow data.
        Premium: Glassnode
        Fallback: CryptoQuant free tier
        
        Returns:
            {"net_flow": float, "flow_usd": float}
        """
        # Try Glassnode first
        if self.config.glassnode_api_key:
            result = await self._glassnode_exchange_flows(asset)
            if result:
                return result
        
        # Try CryptoQuant
        if self.config.cryptoquant_api_key:
            result = await self._cryptoquant_exchange_flows(asset)
            if result:
                return result
        
        return None
    
    async def _glassnode_exchange_flows(self, asset: str) -> Optional[Dict]:
        """Fetch exchange flows from Glassnode."""
        try:
            session = await self._get_session()
            symbol = asset.lower()
            
            url = "https://api.glassnode.com/v1/metrics/transactions/transfers_volume_exchanges_net"
            params = {
                "a": symbol,
                "api_key": self.config.glassnode_api_key,
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        latest = data[-1]
                        return {
                            "net_flow": latest.get("v", 0),
                            "flow_usd": 0,  # Would need price multiplication
                        }
        except Exception as e:
            logger.error(f"Glassnode exchange flows error: {e}")
        return None
    
    async def _cryptoquant_exchange_flows(self, asset: str) -> Optional[Dict]:
        """Fetch exchange flows from CryptoQuant."""
        # CryptoQuant API implementation
        # Similar structure to Glassnode
        return None
    
    async def get_mvrv_zscore(self, asset: str) -> Optional[Dict]:
        """
        Get MVRV Z-Score.
        Premium: Glassnode
        
        Returns:
            {"zscore": float, "mvrv": float}
        """
        if not self.config.glassnode_api_key:
            return None
        
        cache_key = f"mvrv_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            symbol = asset.lower()
            
            url = "https://api.glassnode.com/v1/metrics/market/mvrv_z_score"
            params = {
                "a": symbol,
                "api_key": self.config.glassnode_api_key,
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        latest = data[-1]
                        result = {
                            "zscore": latest.get("v", 0),
                            "mvrv": 0,  # Separate endpoint
                        }
                        self._set_cache(cache_key, result)
                        return result
        except Exception as e:
            logger.error(f"Error fetching MVRV: {e}")
        
        return None
    
    async def get_sopr(self, asset: str) -> Optional[Dict]:
        """
        Get SOPR (Spent Output Profit Ratio).
        Premium: Glassnode
        
        Returns:
            {"sopr": float, "sopr_7d_avg": float}
        """
        if not self.config.glassnode_api_key:
            return None
        
        cache_key = f"sopr_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            symbol = asset.lower()
            
            url = "https://api.glassnode.com/v1/metrics/indicators/sopr"
            params = {
                "a": symbol,
                "api_key": self.config.glassnode_api_key,
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and len(data) >= 7:
                        latest = data[-1].get("v", 1)
                        avg_7d = sum(d.get("v", 1) for d in data[-7:]) / 7
                        
                        result = {
                            "sopr": latest,
                            "sopr_7d_avg": avg_7d,
                        }
                        self._set_cache(cache_key, result)
                        return result
        except Exception as e:
            logger.error(f"Error fetching SOPR: {e}")
        
        return None
    
    async def get_nupl(self, asset: str) -> Optional[Dict]:
        """
        Get NUPL (Net Unrealized Profit/Loss).
        Premium: Glassnode
        
        Returns:
            {"nupl": float}
        """
        if not self.config.glassnode_api_key:
            return None
        
        cache_key = f"nupl_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            symbol = asset.lower()
            
            url = "https://api.glassnode.com/v1/metrics/indicators/net_unrealized_profit_loss"
            params = {
                "a": symbol,
                "api_key": self.config.glassnode_api_key,
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        result = {"nupl": data[-1].get("v", 0)}
                        self._set_cache(cache_key, result)
                        return result
        except Exception as e:
            logger.error(f"Error fetching NUPL: {e}")
        
        return None
    
    # =========================================================================
    # SOCIAL SENTIMENT (LunarCrush - PREMIUM)
    # =========================================================================
    
    async def get_social_sentiment(self, asset: str) -> Optional[Dict]:
        """
        Get social media sentiment.
        Premium: LunarCrush
        
        Returns:
            {"score": float (-100 to +100), "volume": str}
        """
        if not self.config.lunarcrush_api_key:
            return None
        
        cache_key = f"social_{asset}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            session = await self._get_session()
            symbol = asset.upper()
            
            url = f"https://lunarcrush.com/api4/public/coins/{symbol}/v1"
            headers = {"Authorization": f"Bearer {self.config.lunarcrush_api_key}"}
            
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("data"):
                        coin_data = data["data"]
                        # LunarCrush sentiment is 0-5, convert to -100 to +100
                        sentiment = coin_data.get("sentiment", 2.5)
                        normalized = (sentiment - 2.5) * 40  # Scale to -100 to +100
                        
                        result = {
                            "score": normalized,
                            "volume": "high" if coin_data.get("social_volume", 0) > 1000 else "normal",
                        }
                        self._set_cache(cache_key, result)
                        return result
        except Exception as e:
            logger.error(f"Error fetching social sentiment: {e}")
        
        return None
    
    # =========================================================================
    # ETF FLOWS (The TIE or scraping)
    # =========================================================================
    
    async def get_etf_flows(self, asset: str) -> Optional[Dict]:
        """
        Get ETF flow data.
        Premium: The TIE or custom scraping
        
        Returns:
            {"flow_1w_usd": float}
        """
        # ETF flow data typically requires premium sources or scraping
        # Could integrate with SoSoValue, Farside Investors, etc.
        return None
    
    # =========================================================================
    # MACRO DATA (Free sources)
    # =========================================================================
    
    async def get_dxy(self) -> Optional[Dict]:
        """
        Get DXY (Dollar Index) data.
        Free: Yahoo Finance or similar
        
        Returns:
            {"value": float, "change_1w": float}
        """
        # Implementation would use Yahoo Finance API or similar
        return None
    
    async def get_vix(self) -> Optional[Dict]:
        """
        Get VIX data.
        Free: Yahoo Finance or similar
        
        Returns:
            {"value": float}
        """
        # Implementation would use Yahoo Finance API or similar
        return None
    
    # =========================================================================
    # TECHNICAL INDICATORS (Calculated from price data)
    # =========================================================================
    
    async def calculate_rsi(self, asset: str, period: int = 14) -> Optional[float]:
        """
        Calculate RSI from historical price data.
        
        Returns:
            RSI value (0-100)
        """
        history = await self.get_historical_prices(asset, days=30)
        if not history or len(history) < period + 1:
            return None
        
        closes = [d["close"] for d in history]
        
        # Calculate price changes
        changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        # Separate gains and losses
        gains = [max(c, 0) for c in changes]
        losses = [abs(min(c, 0)) for c in changes]
        
        # Calculate average gain and loss
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def calculate_moving_averages(self, asset: str) -> Optional[Dict]:
        """
        Calculate 50, 100, 200 day moving averages.
        
        Returns:
            {"price": float, "ma_50": float, "ma_100": float, "ma_200": float}
        """
        history = await self.get_historical_prices(asset, days=365)
        if not history or len(history) < 200:
            return None
        
        closes = [d["close"] for d in history]
        current_price = closes[-1]
        
        ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
        ma_100 = sum(closes[-100:]) / 100 if len(closes) >= 100 else None
        ma_200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else None
        
        return {
            "price": current_price,
            "ma_50": ma_50,
            "ma_100": ma_100,
            "ma_200": ma_200,
        }
    
    async def calculate_bollinger_bands(self, asset: str, period: int = 20, std_dev: float = 2.0) -> Optional[Dict]:
        """
        Calculate Bollinger Bands.
        
        Returns:
            {"price": float, "upper": float, "middle": float, "lower": float}
        """
        history = await self.get_historical_prices(asset, days=60)
        if not history or len(history) < period:
            return None
        
        closes = [d["close"] for d in history[-period:]]
        current_price = history[-1]["close"]
        
        # Calculate middle band (SMA)
        middle = sum(closes) / period
        
        # Calculate standard deviation
        variance = sum((c - middle) ** 2 for c in closes) / period
        std = variance ** 0.5
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return {
            "price": current_price,
            "upper": upper,
            "middle": middle,
            "lower": lower,
        }


# Convenience function to create provider instance
def create_data_providers(config: Optional[APIConfig] = None) -> DataProviders:
    """Create a DataProviders instance with optional configuration."""
    return DataProviders(config)
