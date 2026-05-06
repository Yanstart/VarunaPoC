"""
Core Interfaces for VarunaPoC

Protocol-based interfaces for dependency inversion and pluggable components.
Using typing.Protocol allows duck typing with static type checking (PEP 544).

Philosophy:
- Interfaces over inheritance (composition > inheritance)
- Dependency inversion (depend on abstractions, not concretions)
- Plugin architecture (swap implementations without code changes)

Two flavours of Protocol coexist:

- **Service Protocols** (stateless): a singleton instance, methods take the
  resource id on each call. Suitable for infrastructure services where the
  per-call cost dominates over instance setup. Used by: AuthProvider,
  StorageProvider, TileCache, WorkflowHook, MLProvider.
- **Resource Protocols** (stateful): an instance represents an open resource
  with a clear lifecycle (open / use / close). Mandated by domains where
  opening is expensive and must be amortized. Used by: SlideReader.

Modules:
- ml_provider:   MLProvider Protocol + result dataclasses (Slideflow, etc.)
- auth:          AuthProvider Protocol + User model
- storage:       StorageProvider Protocol (filesystem, S3, PACS)
- slide_reader:  SlideReader Protocol (OpenSlide, BioFormats, OME-TIFF, OME-Zarr)
- tile_cache:    TileCache Protocol (memory, Redis, filesystem)
- workflow:      WorkflowHook Protocol (Telemis, HL7, custom)
"""

from .auth import AuthProvider
from .ml_provider import (
    FeatureExtractionResult,
    HeatmapResult,
    MLProvider,
    PredictionResult,
    get_provider,
)
from .slide_reader import SlideReader
from .storage import StorageProvider
from .tile_cache import TileCache
from .workflow import WorkflowHook

__all__ = [
    # Service Protocols (stateless)
    "AuthProvider",
    "MLProvider",
    "StorageProvider",
    "TileCache",
    "WorkflowHook",
    # ML provider helpers
    "FeatureExtractionResult",
    "HeatmapResult",
    "PredictionResult",
    "get_provider",
    # Resource Protocols (stateful)
    "SlideReader",
]
