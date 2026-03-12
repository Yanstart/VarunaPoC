"""Access logging middleware with request timing.

Logs method, path, status code, and duration for every request.
Health check endpoints are excluded to reduce log noise.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("access")

_SKIP_PATHS = frozenset({"/api/v1/health", "/health", "/metrics", "/nginx_status"})


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log every request with timing information."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
