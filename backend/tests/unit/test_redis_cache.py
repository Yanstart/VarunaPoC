"""Unit tests for RedisCache.

The redis-server is mocked at the redis.asyncio module boundary so these
tests run anywhere without a live Redis. The integration test that hits a
real container lives in tests/integration/test_tile_cache_redis.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.cache import redis_cache as redis_cache_module
from services.cache.redis_cache import RedisCache


@pytest.fixture(autouse=True)
def reset_loaded_module():
    """Force redis module reload between tests to keep patches isolated."""
    redis_cache_module._redis_module = None
    yield
    redis_cache_module._redis_module = None


def _patch_redis_module(client_mock: AsyncMock):
    """Patch the lazily-loaded redis.asyncio module to return our mock client."""
    fake_module = MagicMock()
    fake_module.Redis = MagicMock(return_value=client_mock)
    return patch.object(redis_cache_module, "_redis_module", fake_module)


# ---------------------------------------------------------------------------
# Lazy connection + ping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_returns_none_on_connect_failure_and_opens_circuit():
    """If ping() raises at connect time, subsequent calls short-circuit."""
    bad_client = AsyncMock()
    bad_client.ping = AsyncMock(side_effect=ConnectionError("nope"))

    cache = RedisCache(host="unreachable", port=1)
    with _patch_redis_module(bad_client):
        first = await cache.get("any-key")
    assert first is None
    assert cache.stats()["circuit_open"] is True
    assert cache.stats()["errors"] == 1


@pytest.mark.asyncio
async def test_set_returns_false_when_circuit_is_open():
    bad_client = AsyncMock()
    bad_client.ping = AsyncMock(side_effect=TimeoutError("nope"))
    cache = RedisCache()
    with _patch_redis_module(bad_client):
        await cache.get("warm-up")  # opens the circuit
        assert await cache.set("k", b"v") is False


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_returns_value_and_increments_hits():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=b"payload")

    cache = RedisCache()
    with _patch_redis_module(client):
        value = await cache.get("k")
    assert value == b"payload"
    assert cache.stats()["hits"] == 1
    assert cache.stats()["misses"] == 0


@pytest.mark.asyncio
async def test_get_increments_misses_on_none():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)

    cache = RedisCache()
    with _patch_redis_module(client):
        value = await cache.get("missing")
    assert value is None
    assert cache.stats()["hits"] == 0
    assert cache.stats()["misses"] == 1


@pytest.mark.asyncio
async def test_set_with_ttl_uses_ex_argument():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.set = AsyncMock(return_value=True)

    cache = RedisCache()
    with _patch_redis_module(client):
        ok = await cache.set("k", b"v", ttl=60)
    assert ok is True
    client.set.assert_awaited_once_with("k", b"v", ex=60)


@pytest.mark.asyncio
async def test_set_without_ttl_does_not_pass_ex():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.set = AsyncMock(return_value=True)

    cache = RedisCache()
    with _patch_redis_module(client):
        await cache.set("k", b"v")
    client.set.assert_awaited_once_with("k", b"v")


@pytest.mark.asyncio
async def test_delete_returns_count():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=2)

    cache = RedisCache()
    with _patch_redis_module(client):
        count = await cache.delete("k1", "k2")
    assert count == 2


@pytest.mark.asyncio
async def test_clear_pattern_iterates_and_deletes():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)

    async def _scan(*, match: str, count: int):
        for k in [b"a:1:0_0:256", b"a:1:0_1:256", b"a:2:0_0:256"]:
            yield k

    client.scan_iter = _scan
    client.delete = AsyncMock(return_value=3)

    cache = RedisCache()
    with _patch_redis_module(client):
        deleted = await cache.clear_pattern("a:*:*:*")
    assert deleted == 3
    client.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# Operation-time failure (Redis up at connect, down at op time)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_failure_returns_none_and_increments_errors():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(side_effect=ConnectionError("dropped"))

    cache = RedisCache()
    with _patch_redis_module(client):
        value = await cache.get("k")
    assert value is None
    assert cache.stats()["errors"] == 1


@pytest.mark.asyncio
async def test_set_failure_returns_false():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.set = AsyncMock(side_effect=RuntimeError("oom"))

    cache = RedisCache()
    with _patch_redis_module(client):
        ok = await cache.set("k", b"v")
    assert ok is False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def test_constructor_reads_environment_variables(monkeypatch):
    monkeypatch.setenv("REDIS_HOST", "redis.internal")
    monkeypatch.setenv("REDIS_PORT", "16379")
    monkeypatch.setenv("REDIS_PASSWORD", "secret")  # pragma: allowlist secret
    monkeypatch.setenv("REDIS_DB", "3")
    cache = RedisCache()
    assert cache._host == "redis.internal"
    assert cache._port == 16379
    assert cache._password == "secret"  # pragma: allowlist secret
    assert cache._db == 3


def test_explicit_constructor_args_win_over_env(monkeypatch):
    monkeypatch.setenv("REDIS_HOST", "from-env")
    cache = RedisCache(host="explicit", port=9999)
    assert cache._host == "explicit"
    assert cache._port == 9999
