"""
Caching Layer
=============

Redis-based caching to reduce API calls and improve performance.

Features:
- Price caching with configurable TTL
- Balance caching
- Transaction history caching
- Rate limit tracking
- Distributed locking

Usage:
    from cache import CacheManager
    
    cache = CacheManager()
    await cache.connect()
    
    # Cache a price
    await cache.set_price("BTC", 45000.00)
    price = await cache.get_price("BTC")
    
    # Use decorator
    @cache.cached(ttl=60)
    async def get_portfolio():
        ...
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class CacheConfig:
    """Cache configuration."""
    
    # Redis connection
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Default TTLs (in seconds)
    price_ttl: int = 30
    balance_ttl: int = 60
    transaction_ttl: int = 300
    portfolio_ttl: int = 120
    orderbook_ttl: int = 5
    
    # Prefix for all keys
    key_prefix: str = "crypto:"
    
    # Max memory (for local cache)
    max_memory_items: int = 10000


class CacheKey(str, Enum):
    """Predefined cache key patterns."""
    PRICE = "price:{asset}"
    BALANCE = "balance:{exchange}:{asset}"
    PORTFOLIO = "portfolio:{snapshot_type}"
    ORDERBOOK = "orderbook:{exchange}:{symbol}"
    TRANSACTION = "transactions:{exchange}:{asset}"
    STAKING = "staking:{exchange}"
    DEFI = "defi:{protocol}:{wallet}"
    RATE_LIMIT = "ratelimit:{exchange}:{endpoint}"
    LOCK = "lock:{resource}"


# =============================================================================
# SERIALIZATION
# =============================================================================


class CacheSerializer:
    """Handles serialization/deserialization of cached values."""
    
    @staticmethod
    def serialize(value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps({"_type": "json", "_value": value}).encode()
        elif isinstance(value, Decimal):
            return json.dumps({"_type": "decimal", "_value": str(value)}).encode()
        elif isinstance(value, datetime):
            return json.dumps({"_type": "datetime", "_value": value.isoformat()}).encode()
        elif isinstance(value, dict):
            # Try JSON first, fall back to pickle
            try:
                return json.dumps({"_type": "json", "_value": value}).encode()
            except (TypeError, ValueError):
                return pickle.dumps({"_type": "pickle", "_value": value})
        else:
            return pickle.dumps({"_type": "pickle", "_value": value})
    
    @staticmethod
    def deserialize(data: bytes) -> Any:
        """Deserialize stored value."""
        try:
            obj = json.loads(data.decode())
            if isinstance(obj, dict) and "_type" in obj:
                if obj["_type"] == "json":
                    return obj["_value"]
                elif obj["_type"] == "decimal":
                    return Decimal(obj["_value"])
                elif obj["_type"] == "datetime":
                    return datetime.fromisoformat(obj["_value"])
            return obj
        except (json.JSONDecodeError, UnicodeDecodeError):
            obj = pickle.loads(data)
            if isinstance(obj, dict) and "_type" in obj:
                return obj["_value"]
            return obj


# =============================================================================
# BASE CACHE BACKEND
# =============================================================================


class BaseCacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key."""
        pass
    
    @abstractmethod
    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        pass
    
    @abstractmethod
    async def flush(self) -> bool:
        """Clear all keys."""
        pass


# =============================================================================
# IN-MEMORY CACHE BACKEND
# =============================================================================


class InMemoryCacheBackend(BaseCacheBackend):
    """Simple in-memory cache backend for testing/development."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if entry["expires_at"] and datetime.utcnow() > entry["expires_at"]:
                del self.cache[key]
                return None
            
            return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            expires_at = None
            if ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            self.cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.utcnow()
            }
            
            # Evict old entries if over limit
            if len(self.cache) > self.config.max_memory_items:
                self._evict_oldest()
            
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None
    
    async def expire(self, key: str, ttl: int) -> bool:
        async with self._lock:
            if key in self.cache:
                self.cache[key]["expires_at"] = datetime.utcnow() + timedelta(seconds=ttl)
                return True
            return False
    
    async def ttl(self, key: str) -> int:
        async with self._lock:
            if key not in self.cache:
                return -2
            
            entry = self.cache[key]
            if not entry["expires_at"]:
                return -1
            
            remaining = (entry["expires_at"] - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))
    
    async def keys(self, pattern: str) -> List[str]:
        import fnmatch
        async with self._lock:
            # Convert Redis pattern to fnmatch pattern
            fnmatch_pattern = pattern.replace("*", "*")
            return [k for k in self.cache.keys() if fnmatch.fnmatch(k, fnmatch_pattern)]
    
    async def flush(self) -> bool:
        async with self._lock:
            self.cache.clear()
            return True
    
    def _evict_oldest(self):
        """Evict oldest entries to stay under limit."""
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: self.cache[k]["created_at"]
        )
        to_remove = len(self.cache) - self.config.max_memory_items
        for key in sorted_keys[:to_remove]:
            del self.cache[key]


# =============================================================================
# REDIS CACHE BACKEND
# =============================================================================


class RedisCacheBackend(BaseCacheBackend):
    """Redis cache backend for production use."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis = None
        self.serializer = CacheSerializer()
    
    async def connect(self):
        """Connect to Redis."""
        try:
            import redis.asyncio as redis
            self.redis = await redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=False
            )
            # Test connection
            await self.redis.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        
        try:
            data = await self.redis.get(key)
            if data:
                return self.serializer.deserialize(data)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.redis:
            return False
        
        try:
            data = self.serializer.serialize(value)
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        if not self.redis:
            return False
        
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        if not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        if not self.redis:
            return False
        
        try:
            return await self.redis.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        if not self.redis:
            return -2
        
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -2
    
    async def keys(self, pattern: str) -> List[str]:
        if not self.redis:
            return []
        
        try:
            keys = await self.redis.keys(pattern)
            return [k.decode() if isinstance(k, bytes) else k for k in keys]
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []
    
    async def flush(self) -> bool:
        if not self.redis:
            return False
        
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis FLUSH error: {e}")
            return False
    
    # Additional Redis-specific methods
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        if not self.redis:
            return 0
        
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 0
    
    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field."""
        if not self.redis:
            return False
        
        try:
            data = self.serializer.serialize(value)
            await self.redis.hset(key, field, data)
            return True
        except Exception as e:
            logger.error(f"Redis HSET error: {e}")
            return False
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field."""
        if not self.redis:
            return None
        
        try:
            data = await self.redis.hget(key, field)
            if data:
                return self.serializer.deserialize(data)
            return None
        except Exception as e:
            logger.error(f"Redis HGET error: {e}")
            return None
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields."""
        if not self.redis:
            return {}
        
        try:
            data = await self.redis.hgetall(key)
            return {
                (k.decode() if isinstance(k, bytes) else k): 
                self.serializer.deserialize(v)
                for k, v in data.items()
            }
        except Exception as e:
            logger.error(f"Redis HGETALL error: {e}")
            return {}


# =============================================================================
# CACHE MANAGER
# =============================================================================


class CacheManager:
    """
    High-level cache manager with domain-specific methods.
    
    Usage:
        cache = CacheManager()
        await cache.connect()
        
        # Price caching
        await cache.set_price("BTC", 45000.00)
        price = await cache.get_price("BTC")
        
        # Use decorator for automatic caching
        @cache.cached(ttl=60)
        async def expensive_operation():
            ...
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.backend: Optional[BaseCacheBackend] = None
        self._fallback = InMemoryCacheBackend(self.config)
    
    async def connect(self):
        """Connect to cache backend."""
        # Try Redis first
        redis_backend = RedisCacheBackend(self.config)
        await redis_backend.connect()
        
        if redis_backend.redis:
            self.backend = redis_backend
        else:
            self.backend = self._fallback
            logger.info("Using in-memory cache backend")
    
    async def disconnect(self):
        """Disconnect from cache backend."""
        if isinstance(self.backend, RedisCacheBackend):
            await self.backend.disconnect()
    
    def _make_key(self, pattern: CacheKey, **kwargs) -> str:
        """Create cache key from pattern."""
        key = pattern.value.format(**kwargs)
        return f"{self.config.key_prefix}{key}"
    
    # -------------------------------------------------------------------------
    # Price Caching
    # -------------------------------------------------------------------------
    
    async def get_price(self, asset: str) -> Optional[float]:
        """Get cached price for asset."""
        key = self._make_key(CacheKey.PRICE, asset=asset.upper())
        value = await self.backend.get(key)
        return float(value) if value else None
    
    async def set_price(
        self,
        asset: str,
        price: float,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache price for asset."""
        key = self._make_key(CacheKey.PRICE, asset=asset.upper())
        return await self.backend.set(key, price, ttl or self.config.price_ttl)
    
    async def get_prices(self, assets: List[str]) -> Dict[str, Optional[float]]:
        """Get cached prices for multiple assets."""
        return {asset: await self.get_price(asset) for asset in assets}
    
    async def set_prices(self, prices: Dict[str, float]) -> bool:
        """Cache multiple prices."""
        results = await asyncio.gather(*[
            self.set_price(asset, price)
            for asset, price in prices.items()
        ])
        return all(results)
    
    # -------------------------------------------------------------------------
    # Balance Caching
    # -------------------------------------------------------------------------
    
    async def get_balance(
        self,
        exchange: str,
        asset: str
    ) -> Optional[Dict[str, float]]:
        """Get cached balance."""
        key = self._make_key(CacheKey.BALANCE, exchange=exchange, asset=asset.upper())
        return await self.backend.get(key)
    
    async def set_balance(
        self,
        exchange: str,
        asset: str,
        balance: Dict[str, float],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache balance."""
        key = self._make_key(CacheKey.BALANCE, exchange=exchange, asset=asset.upper())
        return await self.backend.set(key, balance, ttl or self.config.balance_ttl)
    
    async def invalidate_balances(self, exchange: str):
        """Invalidate all balances for an exchange."""
        pattern = self._make_key(CacheKey.BALANCE, exchange=exchange, asset="*")
        keys = await self.backend.keys(pattern)
        for key in keys:
            await self.backend.delete(key)
    
    # -------------------------------------------------------------------------
    # Portfolio Caching
    # -------------------------------------------------------------------------
    
    async def get_portfolio(
        self,
        snapshot_type: str = "full"
    ) -> Optional[Dict[str, Any]]:
        """Get cached portfolio snapshot."""
        key = self._make_key(CacheKey.PORTFOLIO, snapshot_type=snapshot_type)
        return await self.backend.get(key)
    
    async def set_portfolio(
        self,
        portfolio: Dict[str, Any],
        snapshot_type: str = "full",
        ttl: Optional[int] = None
    ) -> bool:
        """Cache portfolio snapshot."""
        key = self._make_key(CacheKey.PORTFOLIO, snapshot_type=snapshot_type)
        return await self.backend.set(key, portfolio, ttl or self.config.portfolio_ttl)
    
    # -------------------------------------------------------------------------
    # Rate Limiting
    # -------------------------------------------------------------------------
    
    async def check_rate_limit(
        self,
        exchange: str,
        endpoint: str,
        limit: int,
        window_seconds: int
    ) -> bool:
        """
        Check if rate limit is exceeded.
        
        Returns True if request is allowed, False if rate limited.
        """
        key = self._make_key(CacheKey.RATE_LIMIT, exchange=exchange, endpoint=endpoint)
        
        if isinstance(self.backend, RedisCacheBackend):
            count = await self.backend.incr(key)
            if count == 1:
                await self.backend.expire(key, window_seconds)
            return count <= limit
        else:
            # Fallback for in-memory
            data = await self.backend.get(key) or {"count": 0, "reset": datetime.utcnow()}
            if datetime.utcnow() > data["reset"] + timedelta(seconds=window_seconds):
                data = {"count": 0, "reset": datetime.utcnow()}
            data["count"] += 1
            await self.backend.set(key, data, window_seconds)
            return data["count"] <= limit
    
    # -------------------------------------------------------------------------
    # Distributed Locking
    # -------------------------------------------------------------------------
    
    async def acquire_lock(
        self,
        resource: str,
        timeout: int = 30
    ) -> bool:
        """
        Acquire a distributed lock.
        
        Returns True if lock acquired, False otherwise.
        """
        key = self._make_key(CacheKey.LOCK, resource=resource)
        
        if isinstance(self.backend, RedisCacheBackend) and self.backend.redis:
            # Use Redis SETNX
            result = await self.backend.redis.setnx(key, datetime.utcnow().isoformat())
            if result:
                await self.backend.expire(key, timeout)
            return result
        else:
            # Fallback - not truly distributed
            if await self.backend.exists(key):
                return False
            await self.backend.set(key, datetime.utcnow().isoformat(), timeout)
            return True
    
    async def release_lock(self, resource: str) -> bool:
        """Release a distributed lock."""
        key = self._make_key(CacheKey.LOCK, resource=resource)
        return await self.backend.delete(key)
    
    # -------------------------------------------------------------------------
    # Caching Decorator
    # -------------------------------------------------------------------------
    
    def cached(
        self,
        ttl: int = 60,
        key_builder: Optional[Callable[..., str]] = None
    ):
        """
        Decorator for caching function results.
        
        Usage:
            @cache.cached(ttl=300)
            async def get_portfolio_data():
                ...
            
            @cache.cached(ttl=60, key_builder=lambda asset: f"analysis:{asset}")
            async def analyze_asset(asset: str):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # Generate key from function name and arguments
                    key_parts = [func.__name__]
                    key_parts.extend(str(a) for a in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = ":".join(key_parts)
                
                cache_key = f"{self.config.key_prefix}cache:{cache_key}"
                
                # Try to get from cache
                cached_value = await self.backend.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Store in cache
                await self.backend.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    # -------------------------------------------------------------------------
    # Cache Statistics
    # -------------------------------------------------------------------------
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if isinstance(self.backend, RedisCacheBackend) and self.backend.redis:
            info = await self.backend.redis.info("memory")
            keys_count = await self.backend.redis.dbsize()
            return {
                "backend": "redis",
                "keys": keys_count,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected": True
            }
        else:
            return {
                "backend": "memory",
                "keys": len(self._fallback.cache),
                "connected": True
            }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def example_usage():
    """Demonstrate caching system."""
    cache = CacheManager()
    await cache.connect()
    
    # Get stats
    stats = await cache.get_stats()
    print(f"Cache stats: {stats}")
    
    # Cache prices
    await cache.set_price("BTC", 45000.00)
    await cache.set_price("ETH", 2750.00)
    
    price = await cache.get_price("BTC")
    print(f"BTC price: ${price:,.2f}")
    
    # Batch prices
    prices = await cache.get_prices(["BTC", "ETH", "SOL"])
    print(f"Prices: {prices}")
    
    # Rate limiting
    for i in range(5):
        allowed = await cache.check_rate_limit("coinbase", "get_accounts", limit=3, window_seconds=60)
        print(f"Request {i+1}: {'allowed' if allowed else 'rate limited'}")
    
    # Locking
    if await cache.acquire_lock("portfolio_update"):
        print("Lock acquired")
        # Do work...
        await cache.release_lock("portfolio_update")
        print("Lock released")
    
    # Using decorator
    @cache.cached(ttl=120)
    async def get_portfolio_summary():
        print("Computing portfolio (not cached)...")
        return {"total": 125000, "assets": ["BTC", "ETH"]}
    
    # First call - computes
    result = await get_portfolio_summary()
    print(f"Result 1: {result}")
    
    # Second call - cached
    result = await get_portfolio_summary()
    print(f"Result 2: {result}")
    
    await cache.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())
