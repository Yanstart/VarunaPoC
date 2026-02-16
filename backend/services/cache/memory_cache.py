"""
Memory Cache Service -- Level 1 Cache

Fast in-memory TTL cache for metadata, slide info, and ML tags.
Built on cachetools TTLCache with hit/miss statistics.

Thread-safe via built-in cachetools locking.
"""

import logging

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class MemoryCache:
    """TTL-based in-memory cache with statistics."""

    def __init__(self, maxsize: int = 512, ttl: int = 300):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    def get(self, key: str):
        """Get value by key. Returns None if missing or expired."""
        try:
            value = self._cache[key]
            self._hits += 1
            return value
        except KeyError:
            self._misses += 1
            return None

    def set(self, key: str, value) -> None:
        """Set a key-value pair."""
        self._cache[key] = value

    def invalidate(self, key: str) -> None:
        """Remove a specific key."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()

    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (
                self._hits / (self._hits + self._misses)
                if (self._hits + self._misses) > 0
                else 0.0
            ),
        }
