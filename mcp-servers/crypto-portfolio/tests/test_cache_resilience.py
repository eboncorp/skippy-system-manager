"""
Cache Resilience Tests
========================

Validates CacheManager behavior under failure conditions:
- Connection with bad Redis URL
- Operations after disconnect
- Serializer edge cases (Decimal, None, empty dicts)
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from cache import (
    CacheConfig,
    CacheManager,
    CacheSerializer,
    InMemoryCacheBackend,
    RedisCacheBackend,
)


@pytest.mark.stress
class TestCacheResilience:

    async def test_cache_connect_with_bad_url(self):
        """CacheManager with an unreachable Redis URL should fall back
        to the in-memory backend without raising."""
        config = CacheConfig(redis_url="redis://nonexistent-host:6379/0")
        cache = CacheManager(config)

        await cache.connect()

        # Should have fallen back to in-memory
        assert isinstance(cache.backend, InMemoryCacheBackend)

        # Basic operations should still work
        await cache.set_price("BTC", 97500.0)
        price = await cache.get_price("BTC")
        assert price == 97500.0

        stats = await cache.get_stats()
        assert stats["backend"] == "memory"
        assert stats["connected"] is True

        await cache.disconnect()

    async def test_cache_operations_after_disconnect(self):
        """After the Redis backend is disconnected, operations should
        return gracefully (None / False) instead of crashing."""
        config = CacheConfig(redis_url="redis://nonexistent-host:6379/0")

        # Create Redis backend directly to test its disconnected behavior
        backend = RedisCacheBackend(config)
        # Don't connect — redis attribute stays None

        # All operations should return gracefully
        assert await backend.get("any_key") is None
        assert await backend.set("key", "value") is False
        assert await backend.delete("key") is False
        assert await backend.exists("key") is False
        assert await backend.expire("key", 60) is False
        assert await backend.ttl("key") == -2
        assert await backend.keys("*") == []
        assert await backend.flush() is False

    @pytest.mark.parametrize("value,description", [
        (Decimal("0"), "zero decimal"),
        (Decimal("99999999.12345678"), "large decimal"),
        (None, "None value"),
        ({}, "empty dict"),
        ({"nested": {"key": Decimal("1.5"), "list": [1, 2, 3]}}, "nested structure"),
        (datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc), "datetime"),
        ("plain string", "string"),
        (42, "integer"),
        (3.14, "float"),
        ([Decimal("1"), Decimal("2"), Decimal("3")], "list of decimals"),
    ])
    async def test_cache_serializer_edge_cases(self, value, description):
        """Serialize and deserialize various edge-case values through
        CacheSerializer to verify round-trip integrity."""
        data = CacheSerializer.serialize(value)
        assert isinstance(data, bytes)

        restored = CacheSerializer.deserialize(data)

        # Type-specific checks
        if isinstance(value, Decimal):
            assert isinstance(restored, Decimal)
            assert restored == value
        elif isinstance(value, datetime):
            assert isinstance(restored, datetime)
            assert restored == value
        elif value is None:
            assert restored is None
        elif isinstance(value, dict):
            assert isinstance(restored, dict)
            # For nested dicts with Decimals, check key presence
            if "nested" in value:
                assert "nested" in restored
                assert restored["nested"]["key"] == Decimal("1.5")
                assert restored["nested"]["list"] == [1, 2, 3]
            else:
                assert restored == value
        elif isinstance(value, list):
            assert isinstance(restored, list)
            assert len(restored) == len(value)
            for orig, rest in zip(value, restored):
                if isinstance(orig, Decimal):
                    assert rest == orig
        else:
            assert restored == value
