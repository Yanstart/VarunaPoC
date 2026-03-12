"""
Rate Limiting Configuration

Centralised rate-limiter setup so that both main.py (middleware) and
individual route modules can import without circular dependencies.

Environment variables:
    RATE_LIMIT_DEFAULT  - Default limit for all routes (default: 100/minute)
    RATE_LIMIT_TILES    - Tile streaming endpoints (default: 500/minute)
    RATE_LIMIT_ML       - ML inference endpoints (default: 30/minute)
    RATE_LIMIT_AUTH     - Authentication endpoints (default: 10/minute)
    RATE_LIMIT_ANNOTATION_WRITE - Annotation write endpoints (default: 60/minute)
"""

import os

# Rate limiting (requires slowapi)
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False

# Read rate limit config from env (with defaults)
default_rate = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
tile_rate = os.getenv("RATE_LIMIT_TILES", "500/minute")
ml_rate = os.getenv("RATE_LIMIT_ML", "30/minute")
auth_rate = os.getenv("RATE_LIMIT_AUTH", "10/minute")
annotation_write_rate = os.getenv("RATE_LIMIT_ANNOTATION_WRITE", "60/minute")

if RATE_LIMITING_ENABLED:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[default_rate],
        headers_enabled=True,  # Add X-RateLimit-* headers
    )
else:
    limiter = None


def limit(rate: str):
    """Return a rate-limit decorator, or a no-op when slowapi is not installed.

    Usage in routes::

        from rate_limiting import limit, ml_rate

        @router.post("/predict/{slide_id}")
        @limit(ml_rate)
        async def predict_slide(request: Request, ...):
            ...
    """
    if RATE_LIMITING_ENABLED and limiter is not None:
        return limiter.limit(rate)
    # No-op decorator when rate limiting is disabled
    return lambda func: func


# Re-export for main.py
__all__ = [
    "RATE_LIMITING_ENABLED",
    "annotation_write_rate",
    "auth_rate",
    "default_rate",
    "limit",
    "limiter",
    "ml_rate",
    "tile_rate",
]
