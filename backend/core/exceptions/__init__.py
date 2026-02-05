"""
Core Exceptions for VarunaPoC

Centralized exception hierarchy for clear error handling.

Philosophy:
- Specific exceptions over generic exceptions
- Include context (what failed, why, how to fix)
- Log appropriately (error vs warning vs info)
- User-friendly messages (not technical stacktraces)

Author: VarunaPoC Team
Version: 2.0.0
"""

from .base import VarunaError, ConfigurationError, ValidationError
from .storage import (
    StorageError,
    SlideNotFoundError,
    SlideAccessDeniedError,
    StorageQuotaExceededError,
)
from .auth import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidCredentialsError,
)
from .slide import (
    SlideFormatError,
    SlideCorruptedError,
    UnsupportedFormatError,
    InvalidRegionError,
)
from .workflow import (
    WorkflowError,
    WorklistNotFoundError,
    WorkflowIntegrationError,
)

__all__ = [
    # Base
    "VarunaError",
    "ConfigurationError",
    "ValidationError",
    # Storage
    "StorageError",
    "SlideNotFoundError",
    "SlideAccessDeniedError",
    "StorageQuotaExceededError",
    # Auth
    "AuthenticationError",
    "AuthorizationError",
    "TokenExpiredError",
    "InvalidCredentialsError",
    # Slide
    "SlideFormatError",
    "SlideCorruptedError",
    "UnsupportedFormatError",
    "InvalidRegionError",
    # Workflow
    "WorkflowError",
    "WorklistNotFoundError",
    "WorkflowIntegrationError",
]
