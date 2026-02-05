"""
Core Interfaces for VarunaPoC Modular Architecture

This package defines Protocol-based interfaces for pluggable components.
Using typing.Protocol allows duck typing with type checking.

Philosophy:
- Interfaces over inheritance (composition > inheritance)
- Dependency inversion (depend on abstractions, not concretions)
- Plugin architecture (swap implementations without code changes)

Author: VarunaPoC Team (Lead Architecte)
Version: 2.0.0
"""

from .auth import AuthProvider
from .storage import StorageProvider
from .slide_loader import SlideLoader
from .tile_cache import TileCache
from .workflow import WorkflowHook

__all__ = [
    "AuthProvider",
    "StorageProvider",
    "SlideLoader",
    "TileCache",
    "WorkflowHook",
]
