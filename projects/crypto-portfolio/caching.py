"""
Caching Layer
=============

Redis-based caching to reduce API calls and improve performance.

Features:
- Price caching with configurable TTL
- Balance caching
- Transaction history caching
- Staking rate caching
- Automatic cache invalidation
- Cache statistics

Usage:
    from caching import CacheManager
    
    cache = CacheManager()
    await cache.connect()
    
    # Cache price
    await cache.set_price("BTC", 45000.50)
    price = await cache.get_price("BTC")
    
    # Cache with custom TTL
    await cache.set("my_key", data, ttl=300)
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================


class CacheTTL(int, Enum):
    """Default TTL values in seconds."""
    PRICE = 10           # 10 seconds for prices
    BALANCE = 30         # 30 seconds for balances
    TRANSACTION = 300    # 5 minutes for transactions
    STAKING_RATE = 3600  # 1 hour for staking rates
    MARKET_DATA = 60     # 1 minute for market data
    PORTFOLIO = 60       # 1 minute for portfolio summary
    DEFI = 120           # 2 minutes for DeFi positions
    DEFAULT = 60         # 1 minute default


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": f"{self.hit_rate:.1%}",
        }


# =============================================================================
# CACHE BACKEND INTERFACE
# =============================================================================


class CacheBackend(ABC):
    """Abstract cache backend interface."""
    
    @abstractmethod
    async def connect(self):
        """Connect to cache backend."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from cache backend."""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        pass
    
    @abstractmethod
    async def clear(self):
        """Clear all cache."""
        pass
    
    @abstractmethod
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        pass


# =============================================================================
# REDIS BACKEND
# =============================================================================


class RedisBackend(CacheBackend):
    """Redis cache backend using aioredis."""
    
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        self.prefix = "crypto:"
    
    async def connect(self):
        """Connect to Redis."""
        try:
            import redis.asyncio as redis
            self.client = redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self.client.ping()
            logger.info(f"Connected to Redis: {self.url}")
        except ImportError:
            logger.error("redis package not installed. Run: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")
    
    def _key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        return await self.client.get(self._key(key))
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set value in Redis."""
        if ttl:
            await self.client.setex(self._key(key), ttl, value)
        else:
            await self.client.set(self._key(key))
    
    async def delete(self, key: str):
        """Delete value from Redis."""
        await self.client.delete(self._key(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(self._key(key)) > 0
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        full_pattern = self._key(pattern)
        keys = await self.client.keys(full_pattern)
        # Remove prefix from returned keys
        prefix_len = len(self.prefix)
        return [k[prefix_len:] for k in keys]
    
    async def clear(self):
        """Clear all cache keys with our prefix."""
        keys = await self.client.keys(f"{self.prefix}*")
        if keys:
            await self.client.delete(*keys)
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        return await self.client.ttl(self._key(key))
    
    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        """Get multiple values."""
        prefixed_keys = [self._key(k) for k in keys]
        return await self.client.mget(prefixed_keys)
    
    async def mset(self, mapping: Dict[str, str], ttl: Optional[int] = None):
        """Set multiple values."""
        prefixed_mapping = {self._key(k): v for k, v in mapping.items()}
        await self.client.mset(prefixed_mapping)
        
        if ttl:
            # Set TTL for each key
            pipe = self.client.pipeline()
            for key in prefixed_mapping:
                pipe.expire(key, ttl)
            await pipe.execute()


# =============================================================================
# IN-MEMORY BACKEND (FALLBACK)
# =============================================================================


class InMemoryBackend(CacheBackend):
    """In-memory cache backend for testing/fallback."""
    
    def __init__(self):
        self.data: Dict[str, tuple] = {}  # key -> (value, expires_at)
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def connect(self):
        """Start cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("In-memory cache initialized")
    
    async def disconnect(self):
        """Stop cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        self.data.clear()
    
    async def _cleanup_loop(self):
        """Periodically clean up expired keys."""
        while True:
            await asyncio.sleep(10)
            now = datetime.utcnow()
            expired = [
                key for key, (_, expires) in self.data.items()
                if expires and expires < now
            ]
            for key in expired:
                del self.data[key]
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from memory."""
        if key not in self.data:
            return None
        
        value, expires = self.data[key]
        if expires and expires < datetime.utcnow():
            del self.data[key]
            return None
        
        return value
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set value in memory."""
        expires = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
        self.data[key] = (value, expires)
    
    async def delete(self, key: str):
        """Delete value from memory."""
        self.data.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and not expired."""
        if key not in self.data:
            return False
        
        _, expires = self.data[key]
        if expires and expires < datetime.utcnow():
            del self.data[key]
            return False
        
        return True
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern (simple glob)."""
        import fnmatch
        now = datetime.utcnow()
        return [
            key for key, (_, expires) in self.data.items()
            if fnmatch.fnmatch(key, pattern) and (not expires or expires > now)
        ]
    
    async def clear(self):
        """Clear all cache."""
        self.data.clear()
    
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        if key not in self.data:
            return -2  # Key doesn't exist
        
        _, expires = self.data[key]
        if not expires:
            return -1  # No TTL set
        
        remaining = (expires - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))


# =============================================================================
# CACHE MANAGER
# =============================================================================


class CacheManager:
    """
    High-level cache manager with typed methods for crypto data.
    
    Usage:
        cache = CacheManager()
        await cache.connect()
        
        # Cache and retrieve price
        await cache.set_price("BTC", 45000.50)
        price = await cache.get_price("BTC")
        
        # Cache portfolio
        await cache.set_portfolio(portfolio_data)
        portfolio = await cache.get_portfolio()
    """
    
    def __init__(self, backend: Optional[CacheBackend] = None):
        self.backend = backend
        self.stats = CacheStats()
        self._initialized = False
    
    async def connect(self):
        """Connect to cache backend."""
        if self._initialized:
            return
        
        if not self.backend:
            # Try Redis first, fall back to in-memory
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                try:
                    self.backend = RedisBackend(redis_url)
                    await self.backend.connect()
                except Exception as e:
                    logger.warning(f"Redis unavailable, using in-memory cache: {e}")
                    self.backend = InMemoryBackend()
                    await self.backend.connect()
            else:
                self.backend = InMemoryBackend()
                await self.backend.connect()
        else:
            await self.backend.connect()
        
        self._initialized = True
    
    async def disconnect(self):
        """Disconnect from cache backend."""
        if self.backend:
            await self.backend.disconnect()
        self._initialized = False
    
    # -------------------------------------------------------------------------
    # Generic Operations
    # -------------------------------------------------------------------------
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache, deserializing JSON."""
        try:
            value = await self.backend.get(key)
            if value is None:
                self.stats.misses += 1
                return None
            
            self.stats.hits += 1
            return json.loads(value)
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = CacheTTL.DEFAULT
    ):
        """Set value in cache, serializing to JSON."""
        try:
            serialized = json.dumps(value, default=str)
            await self.backend.set(key, serialized, ttl)
            self.stats.sets += 1
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete value from cache."""
        try:
            await self.backend.delete(key)
            self.stats.deletes += 1
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache delete error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        try:
            keys = await self.backend.keys(pattern)
            for key in keys:
                await self.backend.delete(key)
                self.stats.deletes += 1
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Cache invalidate error: {e}")
    
    # -------------------------------------------------------------------------
    # Price Operations
    # -------------------------------------------------------------------------
    
    async def get_price(self, asset: str) -> Optional[float]:
        """Get cached price for asset."""
        return await self.get(f"price:{asset}")
    
    async def set_price(
        self,
        asset: str,
        price: float,
        ttl: int = CacheTTL.PRICE
    ):
        """Cache price for asset."""
        await self.set(f"price:{asset}", price, ttl)
    
    async def get_prices(self, assets: List[str]) -> Dict[str, Optional[float]]:
        """Get cached prices for multiple assets."""
        result = {}
        for asset in assets:
            result[asset] = await self.get_price(asset)
        return result
    
    async def set_prices(
        self,
        prices: Dict[str, float],
        ttl: int = CacheTTL.PRICE
    ):
        """Cache multiple prices."""
        for asset, price in prices.items():
            await self.set_price(asset, price, ttl)
    
    # -------------------------------------------------------------------------
    # Balance Operations
    # -------------------------------------------------------------------------
    
    async def get_balance(
        self,
        exchange: str,
        asset: Optional[str] = None
    ) -> Optional[Dict]:
        """Get cached balance."""
        if asset:
            return await self.get(f"balance:{exchange}:{asset}")
        return await self.get(f"balances:{exchange}")
    
    async def set_balance(
        self,
        exchange: str,
        balance: Dict,
        asset: Optional[str] = None,
        ttl: int = CacheTTL.BALANCE
    ):
        """Cache balance."""
        if asset:
            await self.set(f"balance:{exchange}:{asset}", balance, ttl)
        else:
            await self.set(f"balances:{exchange}", balance, ttl)
    
    async def invalidate_balances(self, exchange: Optional[str] = None):
        """Invalidate balance cache."""
        if exchange:
            await self.invalidate_pattern(f"balance*:{exchange}:*")
        else:
            await self.invalidate_pattern("balance*:*")
    
    # -------------------------------------------------------------------------
    # Portfolio Operations
    # -------------------------------------------------------------------------
    
    async def get_portfolio(self) -> Optional[Dict]:
        """Get cached portfolio summary."""
        return await self.get("portfolio:summary")
    
    async def set_portfolio(
        self,
        portfolio: Dict,
        ttl: int = CacheTTL.PORTFOLIO
    ):
        """Cache portfolio summary."""
        await self.set("portfolio:summary", portfolio, ttl)
    
    async def invalidate_portfolio(self):
        """Invalidate portfolio cache."""
        await self.invalidate_pattern("portfolio:*")
    
    # -------------------------------------------------------------------------
    # Transaction Operations
    # -------------------------------------------------------------------------
    
    async def get_transactions(
        self,
        exchange: str,
        asset: Optional[str] = None
    ) -> Optional[List]:
        """Get cached transactions."""
        key = f"transactions:{exchange}"
        if asset:
            key += f":{asset}"
        return await self.get(key)
    
    async def set_transactions(
        self,
        exchange: str,
        transactions: List,
        asset: Optional[str] = None,
        ttl: int = CacheTTL.TRANSACTION
    ):
        """Cache transactions."""
        key = f"transactions:{exchange}"
        if asset:
            key += f":{asset}"
        await self.set(key, transactions, ttl)
    
    # -------------------------------------------------------------------------
    # Staking Operations
    # -------------------------------------------------------------------------
    
    async def get_staking_rates(self) -> Optional[Dict]:
        """Get cached staking rates."""
        return await self.get("staking:rates")
    
    async def set_staking_rates(
        self,
        rates: Dict,
        ttl: int = CacheTTL.STAKING_RATE
    ):
        """Cache staking rates."""
        await self.set("staking:rates", rates, ttl)
    
    async def get_staking_positions(
        self,
        exchange: str
    ) -> Optional[List]:
        """Get cached staking positions."""
        return await self.get(f"staking:positions:{exchange}")
    
    async def set_staking_positions(
        self,
        exchange: str,
        positions: List,
        ttl: int = CacheTTL.BALANCE
    ):
        """Cache staking positions."""
        await self.set(f"staking:positions:{exchange}", positions, ttl)
    
    # -------------------------------------------------------------------------
    # DeFi Operations
    # -------------------------------------------------------------------------
    
    async def get_defi_positions(
        self,
        protocol: str,
        wallet: Optional[str] = None
    ) -> Optional[List]:
        """Get cached DeFi positions."""
        key = f"defi:{protocol}"
        if wallet:
            key += f":{wallet[:10]}"
        return await self.get(key)
    
    async def set_defi_positions(
        self,
        protocol: str,
        positions: List,
        wallet: Optional[str] = None,
        ttl: int = CacheTTL.DEFI
    ):
        """Cache DeFi positions."""
        key = f"defi:{protocol}"
        if wallet:
            key += f":{wallet[:10]}"
        await self.set(key, positions, ttl)
    
    # -------------------------------------------------------------------------
    # Market Data Operations
    # -------------------------------------------------------------------------
    
    async def get_market_data(self, asset: str) -> Optional[Dict]:
        """Get cached market data."""
        return await self.get(f"market:{asset}")
    
    async def set_market_data(
        self,
        asset: str,
        data: Dict,
        ttl: int = CacheTTL.MARKET_DATA
    ):
        """Cache market data."""
        await self.set(f"market:{asset}", data, ttl)
    
    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return self.stats.to_dict()
    
    def reset_stats(self):
        """Reset cache statistics."""
        self.stats = CacheStats()


# =============================================================================
# CACHE DECORATOR
# =============================================================================


def cached(
    key_pattern: str,
    ttl: int = CacheTTL.DEFAULT,
    cache_manager: Optional[CacheManager] = None
):
    """
    Decorator for caching function results.
    
    Usage:
        @cached("user:{user_id}", ttl=300)
        async def get_user(user_id: str):
            return await fetch_user_from_db(user_id)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Build cache key from pattern and arguments
            try:
                # Get argument names from function signature
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                
                # Build key mapping
                key_args = {}
                for i, arg in enumerate(args):
                    if i < len(params):
                        key_args[params[i]] = arg
                key_args.update(kwargs)
                
                cache_key = key_pattern.format(**key_args)
            except Exception:
                cache_key = key_pattern
            
            # Try to get from cache
            manager = cache_manager or _default_cache_manager
            if manager:
                cached_value = await manager.get(cache_key)
                if cached_value is not None:
                    return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            if manager and result is not None:
                await manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache manager instance
_default_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create default cache manager."""
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = CacheManager()
    return _default_cache_manager


async def init_cache():
    """Initialize default cache manager."""
    manager = get_cache_manager()
    await manager.connect()
    return manager


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def example_usage():
    """Demonstrate caching layer."""
    cache = CacheManager()
    await cache.connect()
    
    # Cache prices
    await cache.set_price("BTC", 45000.50)
    await cache.set_price("ETH", 2750.25)
    
    # Retrieve prices
    btc_price = await cache.get_price("BTC")
    print(f"BTC price: ${btc_price}")
    
    # Get multiple prices
    prices = await cache.get_prices(["BTC", "ETH", "SOL"])
    print(f"Prices: {prices}")
    
    # Cache portfolio
    portfolio = {
        "total_value": 127834.56,
        "holdings": {
            "BTC": {"amount": 1.5, "value": 67500},
            "ETH": {"amount": 12.5, "value": 34375}
        }
    }
    await cache.set_portfolio(portfolio)
    
    # Retrieve portfolio
    cached_portfolio = await cache.get_portfolio()
    print(f"Portfolio: {cached_portfolio}")
    
    # Get stats
    print(f"Cache stats: {cache.get_stats()}")
    
    await cache.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())
