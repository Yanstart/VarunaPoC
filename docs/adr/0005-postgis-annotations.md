# ADR-0005: PostGIS for spatial annotations

**Status:** Accepted
**Date:** 2025-11-01
**Decision makers:** Project lead

## Context

Pathologists draw annotations (polygons, points, rectangles) on slides at specific coordinates. These annotations need spatial queries (e.g., "find all annotations within this viewport region") and must support concurrent multi-user editing.

## Decision

Use PostgreSQL + PostGIS with GeoAlchemy2 ORM. Annotations are stored as GeoJSON geometries with spatial indexes (GiST).

## Consequences

**Positive:**
- Native spatial queries: `ST_Intersects`, `ST_Within` for viewport-based filtering
- GiST indexing: fast spatial lookups even with thousands of annotations
- GeoJSON round-trip: frontend draws GeoJSON, backend stores GeoJSON, no conversion
- ACID transactions: concurrent annotation edits are safe
- SQLAlchemy ORM: typed models, migrations via Alembic

**Negative:**
- PostgreSQL + PostGIS is a mandatory dependency for annotations
- Spatial queries add complexity vs simple JSON storage
- GeoAlchemy2 has limited async support (workaround: run in threadpool)

**Alternatives rejected:**
- MongoDB + GeoJSON: good spatial support but adds a second database technology
- SQLite + SpatiaLite: no concurrent writes, single-file lock
- Flat JSON files: no spatial indexing, O(n) viewport queries
- Redis GEO: points only, no polygon support
