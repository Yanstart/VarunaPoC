"""Domain-specific error helpers for consistent HTTP error responses.

Provides safe error translation that never leaks internal details like
file paths, stack traces, or library-specific messages to API callers.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def slide_open_error(slide_id: str, exc: Exception) -> HTTPException:
    """Translate an OpenSlide error to a safe 422 response."""
    logger.warning("Cannot open slide %s: %s", slide_id, exc)
    return HTTPException(
        422,
        "Slide detected but cannot be opened (corrupt or incompatible format).",
    )


def slide_not_found(slide_id: str) -> HTTPException:
    """Return a 404 for a missing slide."""
    return HTTPException(404, f"Slide {slide_id} not found")


def internal_error(context: str, exc: Exception) -> HTTPException:
    """Log the real error server-side, return a generic 500 to the caller."""
    logger.exception("Internal error in %s: %s", context, exc)
    msg = "Internal server error"
    return HTTPException(500, msg)
