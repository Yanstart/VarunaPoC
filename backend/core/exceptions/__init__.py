"""
Custom Exceptions for VarunaPoC

Domain-specific exceptions for better error handling and debugging.
"""

from .ml_exceptions import (
    FeatureExtractionError,
    HeatmapGenerationError,
    MLModelNotLoadedError,
    MLProviderError,
    ModelLoadError,
    PredictionError,
)

__all__ = [
    "FeatureExtractionError",
    "HeatmapGenerationError",
    "MLModelNotLoadedError",
    "MLProviderError",
    "ModelLoadError",
    "PredictionError",
]
