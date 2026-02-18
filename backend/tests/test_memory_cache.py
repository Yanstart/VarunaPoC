"""Tests for memory cache service (TTL-based metadata cache)"""

import time

import pytest


@pytest.mark.unit
class TestMemoryCache:
    def test_get_set(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        cache.set("slide:info:abc", {"width": 1024, "height": 768})
        result = cache.get("slide:info:abc")
        assert result == {"width": 1024, "height": 768}

    def test_get_missing_returns_none(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_invalidate(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_maxsize_eviction(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=3, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)
        assert cache.get("d") == 4

    def test_stats(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("missing")  # miss

        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["maxsize"] == 100
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
