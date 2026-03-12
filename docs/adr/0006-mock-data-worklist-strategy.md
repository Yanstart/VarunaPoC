# ADR-0006: Mock data strategy for worklist and history

**Status:** Accepted
**Date:** 2025-12-01
**Decision makers:** Project lead

## Context

The worklist (assigned slides) and history (recently viewed) features require integration with hospital LIS/LIMS systems that vary per deployment. The API contract needs to be stable before integration work begins.

## Decision

Ship worklist and history endpoints with deterministic mock data. The mocks return realistic structures (slide IDs, dates, statuses) seeded from the actual slide collection on disk. This allows frontend development and UX validation without LIS integration.

## Consequences

**Positive:**
- Frontend can be fully built and tested against stable API contracts
- Mock data uses real slide IDs (from filesystem scan), so navigation works end-to-end
- Easy to replace: mock functions have the same signature as future real implementations
- No external system dependencies for development or demos

**Negative:**
- Mock data can give false confidence ("it works" but isn't connected)
- Two code paths to maintain until real integration replaces mocks
- Status values (pending/in_progress/completed) are randomized, not meaningful

**Alternatives rejected:**
- No endpoint until real integration: blocks frontend development
- SQLite-backed worklist: adds state management without hospital system integration
- Stub returning empty arrays: insufficient for UX testing
