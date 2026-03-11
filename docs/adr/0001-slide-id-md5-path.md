# ADR-0001: Slide ID based on MD5 of filesystem path

**Status:** Accepted
**Date:** 2025-10-15
**Decision makers:** Project lead

## Context

The viewer needs a stable, URL-safe identifier for each slide. Options:
- UUID v4 (random, requires DB)
- Auto-increment integer (requires DB)
- Hash of filesystem path (deterministic, no DB)

The system has no mandatory database — annotations use PostgreSQL but it's optional. Slides live on a mounted filesystem (`/Slides`).

## Decision

Use `hashlib.md5(path.encode()).hexdigest()[:12]` as the slide ID.

## Consequences

**Positive:**
- Deterministic: same path always produces same ID (idempotent scans)
- No database required for slide discovery
- URL-safe, short (12 hex chars)
- Cacheable: ID is stable across restarts

**Negative:**
- Renaming or moving a file changes its ID (breaks bookmarks)
- MD5 is not collision-resistant (acceptable at 12 chars for <100k slides)
- Path-dependent: same slide at different paths gets different IDs

**Alternatives rejected:**
- UUID v4: requires persistent storage to maintain identity
- Database serial: adds mandatory DB dependency for read-only viewing
- SHA-256 of file content: too slow for multi-GB WSI files
