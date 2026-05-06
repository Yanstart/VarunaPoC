"""
Two-Level Tile Cache — TileCache Protocol implementer.

Composes:
- L1: in-process MemoryCache (cachetools TTL, microseconds latency)
- L2: Redis (RedisCache, low-millisecond latency, shared across processes)

Behaviour
---------
- get_tile: L1 hit → return; L1 miss → L2 lookup, on hit warm L1 then return.
- set_tile: write-through both layers.
- delete_tile: clear matching entries in both layers.
- L2 outage: degrade to L1-only without raising; the RedisCache module owns
  the circuit-breaker state (see redis_cache.py).
- TILE_CACHE_L2_ENABLED=false at construction skips L2 entirely (useful when
  no Redis is available, e.g. minimal CI runs).

Cache key format
----------------
    {slide_id}:{level}:{col}_{row}:{tile_size}
    e.g. "abc123:2:10_5:256"

Source of truth for the format is the TileCache Protocol docstring at
core/interfaces/tile_cache.py.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from services.cache.memory_cache import MemoryCache
from services.cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)


def _make_key(slide_id: str, level: int, col: int, row: int, tile_size: int) -> str:
    return f"{slide_id}:{level}:{col}_{row}:{tile_size}"


def _key_pattern(
    slide_id: str,
    level: Optional[int] = None,
    col: Optional[int] = None,
    row: Optional[int] = None,
) -> str:
    """Build a glob pattern matching the requested granularity."""
    lvl = "*" if level is None else str(level)
    if col is None and row is None:
        return f"{slide_id}:{lvl}:*:*"
    cl = "*" if col is None else str(col)
    rw = "*" if row is None else str(row)
    return f"{slide_id}:{lvl}:{cl}_{rw}:*"


class TwoLevelTileCache:
    """TileCache Protocol implementer with L1 (memory) + L2 (Redis)."""

    def __init__(
        self,
        memory_cache: Optional[MemoryCache] = None,
        redis_cache: Optional[RedisCache] = None,
        l2_enabled: Optional[bool] = None,
        default_ttl_seconds: Optional[int] = None,
    ) -> None:
        self._l1 = memory_cache or MemoryCache(maxsize=2048, ttl=300)

        if l2_enabled is None:
            l2_enabled = os.getenv("TILE_CACHE_L2_ENABLED", "true").lower() in (
                "1",
                "true",
                "yes",
            )
        self._l2_enabled = bool(l2_enabled)
        self._l2 = redis_cache if self._l2_enabled else None
        if self._l2_enabled and self._l2 is None:
            self._l2 = RedisCache()

        if default_ttl_seconds is None:
            default_ttl_seconds = int(os.getenv("TILE_CACHE_L2_TTL_SECONDS", "3600"))
        self._default_ttl = default_ttl_seconds

        self._created_at = datetime.now(tz=UTC)
        self._total_requests = 0
        self._oldest_entry: Optional[datetime] = None
        self._newest_entry: Optional[datetime] = None

    # -- TileCache Protocol --------------------------------------------------

    async def get_tile(
        self,
        slide_id: str,
        level: int,
        col: int,
        row: int,
        tile_size: int = 256,
    ) -> Optional[bytes]:
        self._total_requests += 1
        key = _make_key(slide_id, level, col, row, tile_size)

        # L1 hot path
        cached = self._l1.get(key)
        if cached is not None:
            return cached

        # L2 lookup
        if self._l2 is None:
            return None
        l2_value = await self._l2.get(key)
        if l2_value is not None:
            # Warm L1 so subsequent hits skip the network round-trip.
            self._l1.set(key, l2_value)
            return l2_value
        return None

    async def set_tile(
        self,
        slide_id: str,
        level: int,
        col: int,
        row: int,
        tile_size: int,
        data: bytes,
        ttl: Optional[int] = None,
    ) -> bool:
        key = _make_key(slide_id, level, col, row, tile_size)

        # L1 write (sync, infallible).
        self._l1.set(key, data)

        now = datetime.now(tz=UTC)
        if self._oldest_entry is None:
            self._oldest_entry = now
        self._newest_entry = now

        # L2 write (async, may fail silently if Redis is down).
        if self._l2 is None:
            return True
        l2_ttl = ttl if ttl is not None else self._default_ttl
        await self._l2.set(key, data, ttl=l2_ttl)
        return True

    async def delete_tile(
        self,
        slide_id: str,
        level: Optional[int] = None,
        col: Optional[int] = None,
        row: Optional[int] = None,
    ) -> bool:
        # If a specific tile is targeted, surgical key delete in both layers.
        if level is not None and col is not None and row is not None:
            # We don't know tile_size here without the caller; clear all sizes
            # for that (slide, level, col, row) tuple.
            pattern = _key_pattern(slide_id, level, col, row)
            self._delete_l1_pattern(pattern)
            if self._l2 is not None:
                await self._l2.clear_pattern(pattern)
            return True

        pattern = _key_pattern(slide_id, level, col, row)
        self._delete_l1_pattern(pattern)
        if self._l2 is not None:
            await self._l2.clear_pattern(pattern)
        return True

    async def get_stats(self) -> Dict[str, Any]:
        l1_stats = self._l1.stats()
        l2_stats = self._l2.stats() if self._l2 is not None else {"backend": "disabled"}
        l1_hits = l1_stats.get("hits", 0)
        l1_misses = l1_stats.get("misses", 0)
        l2_hits = l2_stats.get("hits", 0) if self._l2 is not None else 0

        # Aggregate hit rate: consider a request a hit if EITHER layer served it.
        # Total lookups are L1 lookups (every request hits L1 first; L2 is only
        # consulted on L1 miss, so L1 lookups == total request count).
        total_hits = l1_hits + l2_hits
        total_lookups = l1_hits + l1_misses
        return {
            "hit_rate": (total_hits / total_lookups) if total_lookups else 0.0,
            "miss_rate": ((total_lookups - total_hits) / total_lookups) if total_lookups else 0.0,
            "total_requests": self._total_requests,
            "cache_entries": l1_stats.get("size", 0),
            "cache_size_bytes": -1,  # cachetools tracks count, not bytes
            "evictions": 0,  # not tracked by cachetools; placeholder
            "oldest_entry": self._oldest_entry,
            "newest_entry": self._newest_entry,
            "l1": l1_stats,
            "l2": l2_stats,
        }

    async def clear(self) -> bool:
        self._l1.clear()
        if self._l2 is not None:
            await self._l2.flushdb()
        self._oldest_entry = None
        self._newest_entry = None
        return True

    async def warm_up(
        self,
        slide_id: str,
        levels: Optional[list[int]] = None,
    ) -> bool:
        """Pre-populating tiles requires a slide reader + tile renderer hook
        that is owned by the TileServer, not this cache. Stubbed; intended
        to be wired when TileServer.warm_up calls back into the cache.
        """
        msg = (
            "TwoLevelTileCache.warm_up cannot render tiles on its own — it "
            "needs the TileServer to drive rendering. Wire the call from "
            "TileServer.warm_up_slide() once that lands."
        )
        raise NotImplementedError(msg)

    # -- maintenance --------------------------------------------------------

    async def aclose(self) -> None:
        """Release the L2 client. Safe to call repeatedly. Not on the Protocol."""
        if self._l2 is not None:
            await self._l2.close()

    # -- internals ----------------------------------------------------------

    def _delete_l1_pattern(self, pattern: str) -> None:
        """Linear scan over L1 keys to honor a glob pattern. L1 is a few KB
        of metadata; cost is trivial in practice (max 2048 keys by default).
        """
        # cachetools doesn't expose pattern matching, so iterate a snapshot.
        try:
            keys = list(self._l1._cache.keys())  # type: ignore[attr-defined]
        except AttributeError:
            return
        # Convert glob to a simple prefix/segment match: pattern segments are
        # either a literal or "*". We only care about correctness, not speed.
        from fnmatch import fnmatch

        for key in keys:
            if fnmatch(key, pattern):
                self._l1.invalidate(key)


# ---------------------------------------------------------------------------
# Singleton wiring
# ---------------------------------------------------------------------------

_singleton: Optional[TwoLevelTileCache] = None


def get_tile_cache() -> TwoLevelTileCache:
    """Return the process-wide TwoLevelTileCache instance.

    Lazy creation respects test isolation: tests that need a fresh cache
    can call ``reset_tile_cache`` between cases.
    """
    global _singleton
    if _singleton is None:
        _singleton = TwoLevelTileCache()
    return _singleton


def reset_tile_cache() -> None:
    """Clear the singleton. Used by tests; not exported on the Protocol."""
    global _singleton
    _singleton = None


__all__ = ["TwoLevelTileCache", "get_tile_cache", "reset_tile_cache"]
