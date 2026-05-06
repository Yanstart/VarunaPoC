"""Integration tests for TwoLevelTileCache against a live Redis container.

These tests are SKIPPED automatically when no Redis is reachable.
Run them after starting the dev compose stack:

    docker compose -f docker-compose.dev.yml up -d redis
    cd backend
    pytest tests/integration/test_tile_cache_redis.py -m requires_redis -v

Mark `requires_redis` is registered in conftest.py:pytest_collection_modifyitems
and consumed by the same hook to skip when Redis is unreachable.
"""

from __future__ import annotations

import asyncio
import os

import pytest

from services.cache.redis_cache import RedisCache
from services.cache.two_level_tile_cache import TwoLevelTileCache


pytestmark = pytest.mark.requires_redis


@pytest.fixture
async def live_redis():
    """Open a RedisCache against the dev container; skip if unreachable."""
    cache = RedisCache(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6380")),
    )
    if not await cache.ping():
        pytest.skip("Redis not reachable on configured host/port")
    # Wipe DB before each test for isolation.
    await cache.flushdb()
    yield cache
    await cache.close()


@pytest.fixture
async def live_cache(live_redis):
    """A TwoLevelTileCache wired to the real Redis fixture."""
    cache = TwoLevelTileCache(redis_cache=live_redis)
    yield cache
    await cache.aclose()


@pytest.mark.asyncio
async def test_set_then_get_round_trip(live_cache):
    payload = b"\x89PNG\r\n\x1a\n" + b"x" * 100  # fake tile bytes
    await live_cache.set_tile("slide-1", level=2, col=10, row=5, tile_size=256, data=payload)
    got = await live_cache.get_tile("slide-1", level=2, col=10, row=5, tile_size=256)
    assert got == payload


@pytest.mark.asyncio
async def test_l1_eviction_falls_back_to_l2(live_redis):
    # L1 with maxsize=1 forces eviction of the first key on second insert.
    from services.cache.memory_cache import MemoryCache

    tiny_l1 = MemoryCache(maxsize=1, ttl=60)
    cache = TwoLevelTileCache(memory_cache=tiny_l1, redis_cache=live_redis)

    await cache.set_tile("a", 0, 0, 0, 256, b"first")
    await cache.set_tile("b", 0, 0, 0, 256, b"second")  # evicts "a" from L1

    # Subsequent get for "a" must come from L2 (the live Redis).
    got_a = await cache.get_tile("a", 0, 0, 0, 256)
    assert got_a == b"first"


@pytest.mark.asyncio
async def test_clear_pattern_removes_only_targeted_slide(live_cache):
    await live_cache.set_tile("keep-me", 0, 0, 0, 256, b"keep")
    await live_cache.set_tile("delete-me", 0, 0, 0, 256, b"a")
    await live_cache.set_tile("delete-me", 1, 5, 5, 256, b"b")

    await live_cache.delete_tile("delete-me")

    assert await live_cache.get_tile("delete-me", 0, 0, 0, 256) is None
    assert await live_cache.get_tile("delete-me", 1, 5, 5, 256) is None
    assert await live_cache.get_tile("keep-me", 0, 0, 0, 256) == b"keep"


@pytest.mark.asyncio
async def test_ttl_expires_in_l2(live_redis):
    """Set a 1s TTL and verify the key disappears after expiry.

    Uses a fresh TwoLevelTileCache without L1 wiring (we want to observe
    L2 expiry directly without L1 caching the value).
    """
    from services.cache.memory_cache import MemoryCache

    cache = TwoLevelTileCache(
        memory_cache=MemoryCache(maxsize=8, ttl=1),
        redis_cache=live_redis,
        default_ttl_seconds=1,
    )
    await cache.set_tile("ephemeral", 0, 0, 0, 256, b"will-expire")

    # Wait past TTL.
    await asyncio.sleep(1.5)

    # L1 is also TTL=1s so it expires too. Both layers miss, returns None.
    got = await cache.get_tile("ephemeral", 0, 0, 0, 256)
    assert got is None
