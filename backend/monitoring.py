"""
VarunaPoC - Prometheus Monitoring Instrumentation

This module provides comprehensive metrics collection for performance
benchmarking against competitor WSI solutions.

Key Metrics:
- Tile load time (P50, P95, P99) - CRITICAL for comparison
- Time to First Tile (TTFT)
- API endpoint latency
- Slides opened (by format)
- Network/storage performance

Official Resources:
- Prometheus Python Client: https://github.com/prometheus/client_python
- Prometheus Best Practices: https://prometheus.io/docs/practices/naming/
"""

import time
from functools import wraps
from typing import Callable

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, Info, generate_latest

# ============================================================================
# APPLICATION PERFORMANCE METRICS
# ============================================================================

REQUEST_COUNT = Counter(
    "varuna_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "varuna_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ============================================================================
# WSI-SPECIFIC METRICS (CRITICAL FOR BENCHMARKING)
# ============================================================================

TILE_LOAD_TIME = Histogram(
    "varuna_tile_load_seconds",
    "Tile loading time in seconds (KEY METRIC for comparison)",
    ["format", "level"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0),
)

TIME_TO_FIRST_TILE = Histogram(
    "varuna_time_to_first_tile_seconds",
    "Time from slide open to first tile displayed (TTFT)",
    ["format"],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0),
)

SLIDES_OPENED = Counter(
    "varuna_slides_opened_total", "Total number of slides opened", ["format", "vendor"]
)

# ============================================================================
# TILE CACHE METRICS (Tier 5 sprint 1 — TwoLevelTileCache wiring)
# ============================================================================
# These metrics live alongside TILE_LOAD_TIME so a Grafana dashboard can
# correlate cache hit rate with tile-render latency. The route-level layer
# attribution is approximate (we can't observe L1 vs L2 from the route side
# without an extra round-trip); finer breakdown is available via
# /api/cache/stats which calls into TwoLevelTileCache.get_stats().

TILE_CACHE_HITS = Counter(
    "varuna_tile_cache_hits_total",
    "Tile cache hits (route-level: any layer served the tile), by pyramid level",
    ["level"],
)

TILE_CACHE_MISSES = Counter(
    "varuna_tile_cache_misses_total",
    "Tile cache misses (both layers missed → fell through to OpenSlide), by level",
    ["level"],
)

TILE_CACHE_LOOKUP_TIME = Histogram(
    "varuna_tile_cache_lookup_seconds",
    "Time spent on tile cache lookup before deciding hit/miss",
    ["outcome"],  # "hit" | "miss"
    buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1),
)


def record_tile_load(format_name: str, level: int, duration: float):
    """Record tile load time."""
    TILE_LOAD_TIME.labels(format=format_name, level=str(level)).observe(duration)


def record_tile_cache_lookup(outcome: str, level: int, duration: float):
    """Record a cache lookup, by outcome ('hit' or 'miss') and pyramid level."""
    TILE_CACHE_LOOKUP_TIME.labels(outcome=outcome).observe(duration)
    if outcome == "hit":
        TILE_CACHE_HITS.labels(level=str(level)).inc()
    elif outcome == "miss":
        TILE_CACHE_MISSES.labels(level=str(level)).inc()


def record_slide_opened(format_name: str, vendor: str):
    """Record slide opened."""
    SLIDES_OPENED.labels(format=format_name, vendor=vendor).inc()


async def prometheus_middleware(request: Request, call_next):
    """FastAPI middleware to track all HTTP requests."""
    start_time = time.time()

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.url.path, status_code=response.status_code
        ).inc()

        REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)

        return response
    except Exception as e:
        raise


async def metrics_endpoint(request: Request):
    """Expose metrics for Prometheus scraping at /metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
