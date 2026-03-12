"""Centralized FastAPI exception handlers.

Converts common exceptions to the unified ErrorResponse schema so that
every error response from the API has a consistent structure.

Register with the FastAPI application:

    from core.exception_handlers import register_exception_handlers
    register_exception_handlers(app)
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.request_context import get_request_id
from schemas.error import ErrorCodes, ErrorResponse

logger = logging.getLogger(__name__)


def _make_response(status: int, code: str, message: str) -> JSONResponse:
    """Build a JSONResponse from ErrorResponse fields.

    Args:
        status: HTTP status code.
        code: Machine-readable error code from ErrorCodes.
        message: Human-readable error message.

    Returns:
        JSONResponse with serialized ErrorResponse body.
    """
    body = ErrorResponse(
        status=status,
        code=code,
        message=message,
        request_id=get_request_id() or None,
    )
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Convert Starlette/FastAPI HTTPException to ErrorResponse.

    Args:
        _request: Incoming request (unused but required by FastAPI handler protocol).
        exc: The raised HTTPException.

    Returns:
        JSONResponse with ErrorResponse body.
    """
    status = exc.status_code
    code_map = {
        400: ErrorCodes.BAD_REQUEST,
        401: ErrorCodes.UNAUTHORIZED,
        403: ErrorCodes.FORBIDDEN,
        404: ErrorCodes.NOT_FOUND,
        409: ErrorCodes.CONFLICT,
        429: ErrorCodes.RATE_LIMITED,
    }
    code = code_map.get(status, ErrorCodes.INTERNAL_ERROR)
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _make_response(status, code, message)


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic validation errors to ErrorResponse.

    Args:
        _request: Incoming request (unused but required by FastAPI handler protocol).
        exc: The raised RequestValidationError.

    Returns:
        JSONResponse (422) with ErrorResponse body summarising validation failures.
    """
    errors = exc.errors()
    # Summarise to a single human-readable message
    first = errors[0] if errors else {}
    loc = " -> ".join(str(p) for p in first.get("loc", []))
    msg = first.get("msg", "Validation error")
    message = f"Validation error at {loc}: {msg}" if loc else msg
    if len(errors) > 1:
        message += f" (and {len(errors) - 1} more)"
    return _make_response(422, ErrorCodes.VALIDATION_ERROR, message)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,  # noqa: ARG001 - required by handler protocol
) -> JSONResponse:
    """Catch-all handler for unexpected exceptions.

    Logs the full traceback and returns a generic 500 response so that
    internal details are never leaked to callers. The exc argument is
    required by the FastAPI handler protocol; exception info is captured
    automatically by logger.exception from the active exception context.

    Args:
        request: Incoming request.
        exc: The unhandled exception (required by handler protocol).

    Returns:
        JSONResponse (500) with ErrorResponse body.
    """
    logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
    return _make_response(500, ErrorCodes.INTERNAL_ERROR, "An unexpected error occurred")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    logger.info("Exception handlers registered (ErrorResponse schema)")
