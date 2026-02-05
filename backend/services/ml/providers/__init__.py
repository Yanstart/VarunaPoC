"""
ML Providers Package

Implementations of MLProvider interface for different frameworks.

Available providers:
- SlideflowProvider: Slideflow framework (production)
- MockProvider: Mock for testing/development (no dependencies)
- OpenSlideTestProvider: Real slide testing (requires OpenSlide)
"""

from .mock_provider import MockProvider
from .slideflow_provider import SlideflowProvider

# OpenSlideTestProvider is optional (requires openslide)
try:
    from .openslide_provider import OpenSlideTestProvider
except ImportError:
    OpenSlideTestProvider = None

__all__ = ["SlideflowProvider", "MockProvider", "OpenSlideTestProvider"]
