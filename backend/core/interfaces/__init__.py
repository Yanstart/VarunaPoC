"""
Core Interfaces for VarunaPoC

Protocol-based interfaces for dependency inversion and modularity.

Modules:
- ml_provider: ML provider interface (Slideflow, etc.)
"""

from .ml_provider import (
    FeatureExtractionResult,
    HeatmapResult,
    MLProvider,
    PredictionResult,
    get_provider,
)

__all__ = [
    "FeatureExtractionResult",
    "HeatmapResult",
    "MLProvider",
    "PredictionResult",
    "get_provider",
]
