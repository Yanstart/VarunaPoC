# ADR-0002: Optional modules via try/except import pattern

**Status:** Accepted
**Date:** 2025-10-15
**Decision makers:** Project lead

## Context

The backend has many optional features (annotations, auth, FHIR, monitoring, quality metrics). Not all deployments need all features. Installing all dependencies in a hospital environment can be complex.

## Decision

Use try/except ImportError at the top of `main.py` to conditionally load routers:

```python
try:
    from routes import annotations
    ANNOTATIONS_ENABLED = True
except ImportError:
    ANNOTATIONS_ENABLED = False
    print("[INFO] Annotations module disabled")
```

## Consequences

**Positive:**
- Zero-config: install only what you need, the app adapts
- Single binary/image: one Docker image serves all configurations
- Graceful degradation: missing module = disabled feature, not crash
- Easy to add new optional modules

**Negative:**
- Import errors in optional modules are silently swallowed (typos, missing transitive deps)
- No compile-time verification of feature combinations
- Feature flag state is only known at runtime

**Alternatives rejected:**
- Plugin architecture: over-engineered for current scale (~15 routers)
- Separate Docker images per feature: multiplies build/deploy complexity
- Environment variable feature flags without try/except: crashes if dep missing
