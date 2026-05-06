"""Unit tests for TwoLevelTileCache.

Redis is mocked at the RedisCache method level — no real redis-server is
spawned. The integration test that hits a live Redis instance lives at
tests/integration/test_tile_cache_redis.py (gated by `requires_redis`
marker).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.interfaces import TileCache
from services.cache.memory_cache import MemoryCache
from services.cache.two_level_tile_cache import (
    TwoLevelTileCache,
    _key_pattern,
    _make_key,
    get_tile_cache,
    reset_tile_cache,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_redis() -> AsyncMock:
    """A drop-in replacement for RedisCache used by the cache under test."""
    storage: dict[str, bytes] = {}
    fake = AsyncMock()
    fake.get = AsyncMock(side_effect=storage.get)

    async def _set(key: str, value: bytes, ttl: int | None = None):
        storage[key] = value
        return True

    fake.set = AsyncMock(side_effect=_set)

    async def _clear_pattern(pattern: str) -> int:
        from fnmatch import fnmatch

        keys = [k for k in storage if fnmatch(k, pattern)]
        for k in keys:
            storage.pop(k, None)
        return len(keys)

    fake.clear_pattern = AsyncMock(side_effect=_clear_pattern)
    fake.flushdb = AsyncMock(side_effect=lambda: (storage.clear() or True))
    fake.close = AsyncMock()
    fake.stats = lambda: {"backend": "redis", "hits": 0, "misses": 0}
    fake._storage = storage  # exposed for assertions
    return fake


# ---------------------------------------------------------------------------
# Key shape (regression guard for Protocol contract)
# ---------------------------------------------------------------------------


def test_make_key_format_matches_protocol():
    assert _make_key("abc123", 2, 10, 5, 256) == "abc123:2:10_5:256"


def test_key_pattern_full_slide():
    assert _key_pattern("abc") == "abc:*:*:*"


def test_key_pattern_specific_level():
    assert _key_pattern("abc", level=2) == "abc:2:*:*"


def test_key_pattern_specific_tile():
    assert _key_pattern("abc", level=2, col=10, row=5) == "abc:2:10_5:*"


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_satisfies_tilecache_protocol():
    cache = TwoLevelTileCache(redis_cache=_make_fake_redis())
    assert isinstance(cache, TileCache)


def test_singleton_returns_same_instance():
    reset_tile_cache()
    a = get_tile_cache()
    b = get_tile_cache()
    assert a is b
    reset_tile_cache()


# ---------------------------------------------------------------------------
# L1-only behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_l1_only_set_and_get():
    cache = TwoLevelTileCache(l2_enabled=False)
    await cache.set_tile("abc", 0, 1, 2, 256, b"tile-bytes")
    got = await cache.get_tile("abc", 0, 1, 2, 256)
    assert got == b"tile-bytes"


@pytest.mark.asyncio
async def test_l1_only_miss_returns_none():
    cache = TwoLevelTileCache(l2_enabled=False)
    assert await cache.get_tile("missing", 0, 0, 0, 256) is None


# ---------------------------------------------------------------------------
# L1 + L2 coordination
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_writes_through_to_both_layers():
    fake = _make_fake_redis()
    cache = TwoLevelTileCache(redis_cache=fake)
    await cache.set_tile("abc", 0, 1, 2, 256, b"payload")
    assert fake.set.call_args.args[0] == "abc:0:1_2:256"
    assert fake.set.call_args.args[1] == b"payload"


@pytest.mark.asyncio
async def test_l1_miss_l2_hit_warms_l1():
    fake = _make_fake_redis()
    fake._storage["abc:0:1_2:256"] = b"from-l2"
    cache = TwoLevelTileCache(memory_cache=MemoryCache(maxsize=8, ttl=60), redis_cache=fake)

    # First call: L1 miss → L2 hit → returns and warms L1.
    got = await cache.get_tile("abc", 0, 1, 2, 256)
    assert got == b"from-l2"

    # Second call: L1 hit; L2 should NOT be queried again.
    fake.get.reset_mock()
    got2 = await cache.get_tile("abc", 0, 1, 2, 256)
    assert got2 == b"from-l2"
    fake.get.assert_not_called()


@pytest.mark.asyncio
async def test_l1_hit_skips_l2_lookup():
    fake = _make_fake_redis()
    cache = TwoLevelTileCache(redis_cache=fake)
    await cache.set_tile("abc", 0, 1, 2, 256, b"payload")
    fake.get.reset_mock()

    got = await cache.get_tile("abc", 0, 1, 2, 256)
    assert got == b"payload"
    fake.get.assert_not_called()


# ---------------------------------------------------------------------------
# Delete pattern
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_tile_specific_clears_both_layers():
    fake = _make_fake_redis()
    cache = TwoLevelTileCache(redis_cache=fake)
    await cache.set_tile("abc", 2, 10, 5, 256, b"target")
    await cache.set_tile("abc", 2, 10, 5, 512, b"other-size")
    await cache.set_tile("abc", 2, 11, 5, 256, b"different-col")

    await cache.delete_tile("abc", level=2, col=10, row=5)

    # Both sizes for (level=2, col=10, row=5) gone in L1 and L2
    assert await cache.get_tile("abc", 2, 10, 5, 256) is None
    assert await cache.get_tile("abc", 2, 10, 5, 512) is None
    # Other tile untouched
    assert await cache.get_tile("abc", 2, 11, 5, 256) == b"different-col"


@pytest.mark.asyncio
async def test_delete_tile_full_slide_clears_all():
    fake = _make_fake_redis()
    cache = TwoLevelTileCache(redis_cache=fake)
    await cache.set_tile("abc", 0, 0, 0, 256, b"x")
    await cache.set_tile("abc", 1, 5, 7, 256, b"y")
    await cache.set_tile("def", 0, 0, 0, 256, b"keep")

    await cache.delete_tile("abc")

    assert await cache.get_tile("abc", 0, 0, 0, 256) is None
    assert await cache.get_tile("abc", 1, 5, 7, 256) is None
    assert await cache.get_tile("def", 0, 0, 0, 256) == b"keep"


# ---------------------------------------------------------------------------
# clear (full reset)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_wipes_both_layers():
    fake = _make_fake_redis()
    cache = TwoLevelTileCache(redis_cache=fake)
    await cache.set_tile("abc", 0, 0, 0, 256, b"x")
    assert await cache.clear() is True
    assert await cache.get_tile("abc", 0, 0, 0, 256) is None
    assert fake.flushdb.call_count == 1


# ---------------------------------------------------------------------------
# Stats aggregation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_stats_aggregates_layers():
    fake = _make_fake_redis()
    cache = TwoLevelTileCache(redis_cache=fake)
    await cache.set_tile("abc", 0, 0, 0, 256, b"x")
    await cache.get_tile("abc", 0, 0, 0, 256)  # L1 hit
    await cache.get_tile("abc", 0, 0, 0, 999)  # L1 miss + L2 miss

    stats = await cache.get_stats()
    assert stats["total_requests"] == 2
    assert "l1" in stats
    assert "l2" in stats
    assert stats["cache_entries"] >= 1


# ---------------------------------------------------------------------------
# L2 outage degrades to L1 only (no exception bubbles)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_l2_failure_does_not_break_get():
    """Simulate Redis down: get() returns None silently."""
    broken_redis = AsyncMock()
    broken_redis.get = AsyncMock(return_value=None)
    broken_redis.set = AsyncMock(return_value=False)
    broken_redis.clear_pattern = AsyncMock(return_value=0)
    broken_redis.flushdb = AsyncMock(return_value=False)
    broken_redis.close = AsyncMock()
    broken_redis.stats = lambda: {"backend": "redis", "circuit_open": True}

    cache = TwoLevelTileCache(redis_cache=broken_redis)

    # Set should still succeed (L1 always works).
    assert await cache.set_tile("abc", 0, 0, 0, 256, b"x") is True
    # Get reads L1.
    assert await cache.get_tile("abc", 0, 0, 0, 256) == b"x"
    # On a fresh slide, L2 returns None → cache miss, no crash.
    assert await cache.get_tile("zzz", 0, 0, 0, 256) is None


# ---------------------------------------------------------------------------
# warm_up explicit stub
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_warm_up_not_implemented():
    cache = TwoLevelTileCache(l2_enabled=False)
    with pytest.raises(NotImplementedError):
        await cache.warm_up("abc")
