"""
Redis tile cache — L2 layer of the TwoLevelTileCache.

Async wrapper around `redis.asyncio` providing the get/set/delete/clear
primitives used by `TwoLevelTileCache`. Stays small on purpose: this is a
thin adapter, not a full Redis abstraction.

Configuration (read from env vars):
- REDIS_HOST              (default "localhost")
- REDIS_PORT              (default 6380 for dev compose; production uses 6379)
- REDIS_PASSWORD          (default "")
- REDIS_DB                (default 0)
- REDIS_CONNECT_TIMEOUT   (default 2.0 seconds)

Behaviour notes
---------------
- The connection is lazy: the first get/set creates the pool. This keeps
  process startup independent of Redis availability.
- All Redis errors are caught and logged at WARNING; the cache "degrades to
  miss" rather than propagating to callers. The TwoLevelTileCache uses this
  to fall back to L1 only when L2 is unhealthy.
- `_pool_unhealthy` is a process-wide circuit breaker: after one fatal
  connect failure, subsequent calls short-circuit for `_circuit_cooldown`
  seconds before retrying.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# redis.asyncio is imported lazily so that pytest collection does not fail
# when redis is not installed in the test environment.
_redis_module = None


def _load_redis():
    global _redis_module
    if _redis_module is None:
        import redis.asyncio as _r  # type: ignore[import-untyped]

        _redis_module = _r
    return _redis_module


class RedisCache:
    """L2 cache backed by Redis. Tile-data agnostic (stores arbitrary bytes)."""

    _circuit_cooldown = 30.0  # seconds before retrying after a connect failure

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: Optional[int] = None,
        connect_timeout: Optional[float] = None,
    ) -> None:
        self._host = host or os.getenv("REDIS_HOST", "localhost")
        self._port = int(port if port is not None else os.getenv("REDIS_PORT", "6380"))
        self._password = password if password is not None else os.getenv("REDIS_PASSWORD", "")
        self._db = int(db if db is not None else os.getenv("REDIS_DB", "0"))
        self._connect_timeout = (
            connect_timeout
            if connect_timeout is not None
            else float(os.getenv("REDIS_CONNECT_TIMEOUT", "2.0"))
        )
        self._client = None
        self._pool_unhealthy_until: float = 0.0
        self._hits = 0
        self._misses = 0
        self._errors = 0

    # -- connection ----------------------------------------------------------

    async def _get_client(self):
        """Lazily create / return the redis client. None if circuit is open."""
        if time.monotonic() < self._pool_unhealthy_until:
            return None
        if self._client is not None:
            return self._client
        try:
            redis = _load_redis()
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password or None,
                socket_connect_timeout=self._connect_timeout,
                socket_timeout=self._connect_timeout,
                decode_responses=False,  # we store raw tile bytes
            )
            # Cheap probe to fail fast if redis is unreachable.
            await self._client.ping()
            logger.info(
                "RedisCache connected to redis://%s:%d/%d",
                self._host,
                self._port,
                self._db,
            )
            return self._client
        except Exception as e:
            self._errors += 1
            self._client = None
            self._pool_unhealthy_until = time.monotonic() + self._circuit_cooldown
            logger.warning(
                "RedisCache unavailable (host=%s port=%d): %s. "
                "L2 cache will be skipped for %.0fs.",
                self._host,
                self._port,
                e,
                self._circuit_cooldown,
            )
            return None

    # -- primitives ---------------------------------------------------------

    async def get(self, key: str) -> Optional[bytes]:
        """Return cached bytes or None on miss / connection failure."""
        client = await self._get_client()
        if client is None:
            self._misses += 1
            return None
        try:
            value = await client.get(key)
        except Exception as e:
            self._errors += 1
            logger.warning("RedisCache.get(%r) failed: %s", key, e)
            return None
        if value is None:
            self._misses += 1
        else:
            self._hits += 1
        return value

    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        """Store bytes with optional TTL (seconds). Returns False on failure."""
        client = await self._get_client()
        if client is None:
            return False
        try:
            if ttl is not None and ttl > 0:
                await client.set(key, value, ex=ttl)
            else:
                await client.set(key, value)
            return True
        except Exception as e:
            self._errors += 1
            logger.warning("RedisCache.set(%r) failed: %s", key, e)
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys. Returns number of keys actually deleted."""
        if not keys:
            return 0
        client = await self._get_client()
        if client is None:
            return 0
        try:
            return int(await client.delete(*keys))
        except Exception as e:
            self._errors += 1
            logger.warning("RedisCache.delete(%r) failed: %s", keys, e)
            return 0

    async def scan_keys(self, pattern: str, count: int = 500):
        """Async-iterate keys matching a glob pattern (SCAN, not KEYS).

        Yields raw bytes keys as Redis returns them. Empty / on failure.
        """
        client = await self._get_client()
        if client is None:
            return
        try:
            async for key in client.scan_iter(match=pattern, count=count):
                yield key
        except Exception as e:
            self._errors += 1
            logger.warning("RedisCache.scan_keys(%r) failed: %s", pattern, e)
            return

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern. Returns count deleted."""
        client = await self._get_client()
        if client is None:
            return 0
        deleted = 0
        try:
            batch: list = []
            async for key in client.scan_iter(match=pattern, count=500):
                batch.append(key)
                if len(batch) >= 500:
                    deleted += int(await client.delete(*batch))
                    batch.clear()
            if batch:
                deleted += int(await client.delete(*batch))
        except Exception as e:
            self._errors += 1
            logger.warning("RedisCache.clear_pattern(%r) failed: %s", pattern, e)
        return deleted

    async def flushdb(self) -> bool:
        """Wipe the current Redis DB. Use with care — only for tests / clear()."""
        client = await self._get_client()
        if client is None:
            return False
        try:
            await client.flushdb()
            return True
        except Exception as e:
            self._errors += 1
            logger.warning("RedisCache.flushdb failed: %s", e)
            return False

    async def ping(self) -> bool:
        """Health probe. Returns True iff Redis is reachable right now."""
        client = await self._get_client()
        if client is None:
            return False
        try:
            return bool(await client.ping())
        except Exception as e:
            self._errors += 1
            logger.warning("RedisCache.ping failed: %s", e)
            return False

    async def close(self) -> None:
        """Release the underlying client. Safe to call repeatedly."""
        if self._client is not None:
            try:
                await self._client.aclose()  # redis>=5
            except AttributeError:
                # Older redis: .close() returns awaitable
                await self._client.close()
            except Exception as e:
                logger.warning("RedisCache.close failed: %s", e)
            finally:
                self._client = None

    # -- introspection ------------------------------------------------------

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "backend": "redis",
            "host": self._host,
            "port": self._port,
            "hits": self._hits,
            "misses": self._misses,
            "errors": self._errors,
            "hit_rate": (self._hits / total) if total else 0.0,
            "circuit_open": time.monotonic() < self._pool_unhealthy_until,
        }


__all__ = ["RedisCache"]
