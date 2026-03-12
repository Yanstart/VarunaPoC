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

from starlette.requests import Request

# Rate limiting (requires slowapi)
try:
    from slowapi import Limiter

    RATE_LIMITING_ENABLED = True
except ImportError:
    RATE_LIMITING_ENABLED = False

# Read rate limit config from env (with defaults)
default_rate = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
tile_rate = os.getenv("RATE_LIMIT_TILES", "500/minute")
ml_rate = os.getenv("RATE_LIMIT_ML", "30/minute")
auth_rate = os.getenv("RATE_LIMIT_AUTH", "10/minute")
annotation_write_rate = os.getenv("RATE_LIMIT_ANNOTATION_WRITE", "60/minute")


def _get_real_client_ip(request: Request) -> str:
    """Extract client IP using X-Real-IP (set by nginx to $remote_addr).

    Nginx is the trust boundary: it sets X-Real-IP to the actual TCP peer
    address and overrides X-Forwarded-For with $remote_addr, preventing
    client-supplied header spoofing.  We prefer X-Real-IP because it is
    always a single address, then fall back to X-Forwarded-For (first
    entry) and finally to the ASGI transport peer.
    """
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


if RATE_LIMITING_ENABLED:
    limiter = Limiter(
        key_func=_get_real_client_ip,
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
