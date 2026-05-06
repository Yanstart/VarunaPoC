"""
Tile Cache Interface

PURPOSE: Abstract caching strategy for tiles.
Phase 1 has no cache (stateless).
Phase 2+ will add caching for performance.

Caching Strategies:
- Memory cache (Redis, Memcached)
- Filesystem cache (pre-rendered tiles on disk)
- Hybrid (memory L1 + disk L2)
- CDN (edge caching for distributed access)

Pattern: Strategy Pattern
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class TileCache(Protocol):
    """
    Protocol for tile caching implementations.

    Implementations:
    - NoOpCache (Phase 1 - no caching)
    - RedisCache (Phase 2 - in-memory cache)
    - FilesystemCache (Phase 2 - disk cache)
    - HybridCache (Phase 3 - memory + disk)
    - CDNCache (Phase 3 - CloudFlare, Akamai, etc.)

    Cache Key Format:
        {slide_id}:{level}:{col}_{row}:{size}
        Example: "abc123:2:10_5:256"

    Why Cache Tiles?
    - Decoding tiles is expensive (JPEG2000, etc.)
    - Same tiles requested repeatedly (panning, zooming)
    - Reduces OpenSlide calls (OpenSlide not thread-safe)
    - Enables horizontal scaling (shared cache across instances)
    """

    async def get_tile(
        self,
        slide_id: str,
        level: int,
        col: int,
        row: int,
        tile_size: int = 256
    ) -> Optional[bytes]:
        """
        Get cached tile if available.

        Args:
            slide_id: Unique slide identifier
            level: Pyramid level
            col: Tile column
            row: Tile row
            tile_size: Tile size in pixels

        Returns:
            JPEG/PNG bytes if cached, None if cache miss

        Examples:
            >>> tile_bytes = await cache.get_tile(
            ...     slide_id="abc123",
            ...     level=2,
            ...     col=10,
            ...     row=5,
            ...     tile_size=256
            ... )
            >>> if tile_bytes:
            ...     # Cache hit
            ...     return Response(content=tile_bytes, media_type="image/jpeg")
            >>> else:
            ...     # Cache miss, extract from slide
            ...     tile_bytes = extract_tile_from_slide(...)
            ...     await cache.set_tile(..., tile_bytes)

        Notes:
            - MUST be fast (<1ms for memory cache)
            - SHOULD track hit/miss metrics
        """
        ...

    async def set_tile(
        self,
        slide_id: str,
        level: int,
        col: int,
        row: int,
        tile_size: int,
        data: bytes,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store tile in cache.

        Args:
            slide_id: Unique slide identifier
            level: Pyramid level
            col: Tile column
            row: Tile row
            tile_size: Tile size in pixels
            data: JPEG/PNG bytes
            ttl: Time to live in seconds (None = default TTL)

        Returns:
            True if stored successfully

        Examples:
            >>> await cache.set_tile(
            ...     slide_id="abc123",
            ...     level=2,
            ...     col=10,
            ...     row=5,
            ...     tile_size=256,
            ...     data=jpeg_bytes,
            ...     ttl=3600  # 1 hour
            ... )

        Notes:
            - SHOULD be non-blocking (fire-and-forget OK)
            - MUST handle cache full (LRU eviction)
            - TTL choice depends on use case:
              - High-res tiles: longer TTL (rarely change)
              - Overview tiles: shorter TTL (may be regenerated)
        """
        ...

    async def delete_tile(
        self,
        slide_id: str,
        level: Optional[int] = None,
        col: Optional[int] = None,
        row: Optional[int] = None
    ) -> bool:
        """
        Delete tile(s) from cache.

        Args:
            slide_id: Slide identifier
            level: Optional level (None = all levels)
            col: Optional column (None = all columns)
            row: Optional row (None = all rows)

        Returns:
            True if deleted

        Granularity:
            - delete_tile("abc123") → Delete ALL tiles for slide
            - delete_tile("abc123", level=2) → Delete all tiles at level 2
            - delete_tile("abc123", 2, 10) → Delete column 10 at level 2
            - delete_tile("abc123", 2, 10, 5) → Delete specific tile

        Use Cases:
            - Slide updated/replaced
            - Cache invalidation after processing
            - Manual cache clearing

        Examples:
            >>> # Delete all tiles for slide
            >>> await cache.delete_tile("abc123")

            >>> # Delete specific tile
            >>> await cache.delete_tile("abc123", level=2, col=10, row=5)
        """
        ...

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with keys:
            - hit_rate: float (0.0-1.0)
            - miss_rate: float (0.0-1.0)
            - total_requests: int
            - cache_size_bytes: int
            - cache_entries: int
            - evictions: int (LRU evictions)
            - oldest_entry: datetime
            - newest_entry: datetime

        Use Cases:
            - Monitoring dashboards
            - Cache tuning (adjust TTL, size limits)
            - Performance optimization

        Examples:
            >>> stats = await cache.get_stats()
            >>> print(f"Cache hit rate: {stats['hit_rate']:.2%}")
            >>> print(f"Cache size: {stats['cache_size_bytes'] / 1e9:.2f} GB")
        """
        ...

    async def clear(self) -> bool:
        """
        Clear entire cache.

        Returns:
            True if cleared successfully

        Use Cases:
            - Testing (reset cache between tests)
            - Emergency (cache corruption)
            - Maintenance (free memory)

        Examples:
            >>> await cache.clear()
        """
        ...

    async def warm_up(
        self,
        slide_id: str,
        levels: Optional[list[int]] = None
    ) -> bool:
        """
        Pre-populate cache with slide tiles.

        Args:
            slide_id: Slide to warm up
            levels: Pyramid levels to cache (None = all levels)

        Returns:
            True if warm-up successful

        Use Cases:
            - Slide uploaded (pre-render all tiles)
            - Scheduled task (warm cache during night)
            - High-priority slide (pathologist viewing soon)

        Strategy:
            - Low-res levels first (levels 3, 2, 1, 0)
            - Important regions first (tumor annotated regions)
            - Background task (don't block viewer)

        Examples:
            >>> # Warm up overview levels
            >>> await cache.warm_up("abc123", levels=[3, 2])

            >>> # Warm up all levels (slow!)
            >>> await cache.warm_up("abc123")

        Notes:
            - SHOULD be async/background task
            - MAY be interrupted (partial warm-up OK)
            - SHOULD track progress (for UI feedback)
        """
        ...


class DistributedTileCache(TileCache, Protocol):
    """
    Extension for distributed caching (multi-instance deployment).

    Use Cases:
    - Load-balanced backend (multiple FastAPI instances)
    - Multi-region deployment (edge caching)
    - Horizontal scaling (shared cache across nodes)

    Technologies:
    - Redis Cluster
    - Memcached with consistent hashing
    - Hazelcast (in-memory data grid)
    """

    async def invalidate_cluster(
        self,
        slide_id: str
    ) -> bool:
        """
        Invalidate cache across all cluster nodes.

        Args:
            slide_id: Slide to invalidate

        Returns:
            True if invalidated on all nodes

        Use Cases:
            - Slide updated on one node (propagate to all)
            - Cache consistency (avoid stale data)

        Examples:
            >>> # Slide updated on Node 1
            >>> await cache.invalidate_cluster("abc123")
            >>> # Cache cleared on Node 1, Node 2, Node 3
        """
        ...

    async def get_cluster_stats(self) -> Dict[str, Any]:
        """
        Get aggregated stats across cluster.

        Returns:
            Dict with keys:
            - nodes: int (number of cache nodes)
            - total_size_bytes: int (sum across all nodes)
            - avg_hit_rate: float (average hit rate)
            - nodes_stats: List[Dict] (per-node stats)

        Examples:
            >>> stats = await cache.get_cluster_stats()
            >>> print(f"Cluster nodes: {stats['nodes']}")
            >>> print(f"Avg hit rate: {stats['avg_hit_rate']:.2%}")
        """
        ...
