"""
Core Interfaces for VarunaPoC

Protocol-based interfaces for dependency inversion and pluggable components.
Using typing.Protocol allows duck typing with static type checking (PEP 544).

Philosophy:
- Interfaces over inheritance (composition > inheritance)
- Dependency inversion (depend on abstractions, not concretions)
- Plugin architecture (swap implementations without code changes)

Modules:
- ml_provider:   MLProvider Protocol + result dataclasses (Slideflow, etc.)
- auth:          AuthProvider Protocol + User model
- storage:       StorageProvider Protocol (filesystem, S3, PACS)
- slide_loader:  SlideLoader Protocol (OpenSlide, DICOM, etc.)
- tile_cache:    TileCache Protocol (memory, Redis, filesystem)
- workflow:      WorkflowHook Protocol (Telemis, HL7, custom)
"""

# ML provider — concrete implementations used by routes/ml.py and services
# Modular architecture Protocols (pluggable backends)
from .auth import AuthProvider
from .ml_provider import (
    FeatureExtractionResult,
    HeatmapResult,
    MLProvider,
    PredictionResult,
    get_provider,
)
from .slide_loader import SlideLoader
from .storage import StorageProvider
from .tile_cache import TileCache
from .workflow import WorkflowHook

__all__ = [
    # Modular architecture Protocols
    "AuthProvider",
    # ML provider
    "FeatureExtractionResult",
    "HeatmapResult",
    "MLProvider",
    "PredictionResult",
    "SlideLoader",
    "StorageProvider",
    "TileCache",
    "WorkflowHook",
    "get_provider",
]
