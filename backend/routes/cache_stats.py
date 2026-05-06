"""
Cache statistics endpoint — exposes the TwoLevelTileCache.get_stats() dict
so admins (and Grafana scrapers) can observe hit rate, layer breakdown,
and TTL distribution at runtime.

Route: GET /api/cache/stats
Access: ADMIN_TECHNIQUE only (cache state is operational telemetry).

The Prometheus counters in monitoring.py give the time-series picture
(hit/miss rates over time); this endpoint surfaces the current absolute
counters from each layer (L1 cachetools, L2 Redis) and the
process-wide request total tracked by TwoLevelTileCache.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Request  # noqa: TC002 — Request needs runtime import for FastAPI to inject

from auth.dependencies import require_role

router = APIRouter(prefix="/api/cache", tags=["admin"])


@router.get(
    "/stats",
    summary="Tile cache statistics (L1 memory + L2 Redis)",
    description=(
        "Returns the current snapshot from TwoLevelTileCache.get_stats(): "
        "aggregate hit/miss rate, per-layer counters, oldest/newest entry "
        "timestamps. ADMIN_TECHNIQUE only."
    ),
    response_model=Dict[str, Any],
)
async def cache_stats(
    request: Request,
    _user=Depends(require_role("ADMIN_TECHNIQUE")),
) -> Dict[str, Any]:
    cache = getattr(request.app.state, "tile_cache", None)
    if cache is None:
        return {"backend": "uninitialized", "hint": "tile_cache not attached to app.state"}
    return await cache.get_stats()
