"""Request context propagation using contextvars.

Provides X-Request-ID generation and propagation across async handlers,
background tasks, and log entries. The request ID is generated once per
request and available via get_request_id() anywhere in the call chain.
"""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get the current request ID from context."""
    return _request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that generates or propagates X-Request-ID header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        _request_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
