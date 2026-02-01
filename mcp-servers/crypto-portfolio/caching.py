"""
Caching Layer (Compatibility Shim)
===================================

This module re-exports from ``cache.py``, which provides the primary cache
implementation with JSON-only serialization, rate limiting, and distributed
locking.

All public names that previously lived here are available through this shim
so that existing ``from caching import ...`` statements continue to work.

Usage (unchanged)::

    from caching import CacheManager, get_cache_manager, init_cache

    cache = CacheManager()
    await cache.connect()
    await cache.set_price("BTC", 45000.50)

NOTE: New code should import directly from ``cache`` instead of ``caching``.
"""

import asyncio
import logging
from enum import IntEnum
from typing import Optional

# Re-export the primary implementation from cache.py
from cache import (  # noqa: F401
    CacheConfig,
    CacheKey,
    CacheManager,
    CacheSerializer,
    BaseCacheBackend,
    InMemoryCacheBackend,
    RedisCacheBackend,
)

logger = logging.getLogger(__name__)


class CacheTTL(IntEnum):
    """Default TTL values in seconds (kept for backward compat)."""

    PRICE = 10
    BALANCE = 30
    TRANSACTION = 300
    STAKING_RATE = 3600
    MARKET_DATA = 60
    PORTFOLIO = 60
    DEFI = 120
    DEFAULT = 60


# ---------------------------------------------------------------------------
# Convenience functions (match the old caching.py public API)
# ---------------------------------------------------------------------------

_default_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create the default CacheManager singleton."""
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = CacheManager()
    return _default_cache_manager


async def init_cache() -> CacheManager:
    """Initialize and connect the default CacheManager."""
    manager = get_cache_manager()
    await manager.connect()
    return manager


if __name__ == "__main__":

    async def _demo():
        cache = await init_cache()
        print(f"Backend: {type(cache.backend).__name__}")
        print(f"CacheTTL.PRICE = {CacheTTL.PRICE}")
        await cache.disconnect()

    asyncio.run(_demo())
