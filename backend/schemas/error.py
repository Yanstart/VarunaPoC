"""Unified error response schema.

All API error responses should use this format for consistency.
Registered exception handlers in core/exception_handlers.py convert
exceptions to this schema automatically.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response returned by all API endpoints."""

    status: int = Field(..., description="HTTP status code")
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    request_id: str | None = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Error timestamp (UTC)",
    )


class ErrorCodes:
    """Machine-readable error code constants for use in ErrorResponse."""

    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    CONFLICT = "CONFLICT"
    BAD_REQUEST = "BAD_REQUEST"
