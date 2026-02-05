"""
Core Exceptions for VarunaPoC

Centralized exception hierarchy for clear error handling.

Philosophy:
- Specific exceptions over generic exceptions
- Include context (what failed, why, how to fix)
- Log appropriately (error vs warning vs info)
- User-friendly messages (not technical stacktraces)

Note: ML-specific exceptions (MLProviderError and subclasses) live in
ml_exceptions.py and inherit directly from Exception for now.
Migrating them to VarunaError is tracked as a follow-up refactoring task.
"""

from .auth import (
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    TokenExpiredError,
)
from .base import ConfigurationError, ValidationError, VarunaError
from .ml_exceptions import (
    FeatureExtractionError,
    HeatmapGenerationError,
    MLModelNotLoadedError,
    MLProviderError,
    ModelLoadError,
    PredictionError,
)
from .slide import (
    InvalidRegionError,
    SlideCorruptedError,
    SlideFormatError,
    UnsupportedFormatError,
)
from .storage import (
    SlideAccessDeniedError,
    SlideNotFoundError,
    StorageError,
    StorageQuotaExceededError,
)
from .workflow import (
    WorkflowError,
    WorkflowIntegrationError,
    WorklistNotFoundError,
)

__all__ = [
    # Auth
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "FeatureExtractionError",
    "HeatmapGenerationError",
    "InvalidCredentialsError",
    "InvalidRegionError",
    "MLModelNotLoadedError",
    # ML (own hierarchy, VarunaError migration pending)
    "MLProviderError",
    "ModelLoadError",
    "PredictionError",
    "SlideAccessDeniedError",
    "SlideCorruptedError",
    # Slide
    "SlideFormatError",
    "SlideNotFoundError",
    # Storage
    "StorageError",
    "StorageQuotaExceededError",
    "TokenExpiredError",
    "UnsupportedFormatError",
    "ValidationError",
    # Base
    "VarunaError",
    # Workflow
    "WorkflowError",
    "WorkflowIntegrationError",
    "WorklistNotFoundError",
]
