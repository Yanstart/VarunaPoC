# ADR-0003: Stateless tile server with in-memory per-worker cache

**Status:** Accepted
**Date:** 2025-10-15
**Decision makers:** Project lead

## Context

WSI (Whole Slide Image) viewers request thousands of 256x256 JPEG tiles per session. OpenSlide file handles are expensive to open (~100ms for MRXS). The server must balance memory usage, concurrency, and response latency.

## Decision

Use a per-worker LRU cache of open OpenSlide handles (max 5 concurrent slides). Tiles are extracted on-demand and not stored server-side. Nginx handles tile caching (10 GB disk cache, 24h TTL).

## Consequences

**Positive:**
- Simple: no external cache service (Redis/Memcached) required for tiles
- Memory-bounded: LRU eviction keeps at most 5 slides open per worker
- Scales horizontally: each uvicorn worker is independent
- Nginx cache absorbs repeated requests (cache hit = no Python involved)

**Negative:**
- Cache is per-worker, not shared: N workers may each open the same slide
- Cold start per slide: first tile request pays the OpenSlide open cost
- No cross-request prefetching

**Alternatives rejected:**
- Redis tile cache: adds infrastructure, tiles are large binary blobs (poor fit)
- Shared file-handle pool across workers: requires multiprocessing.Manager (complex)
- Pre-generated tile pyramids (DZI on disk): doubles storage for multi-TB slide collections
