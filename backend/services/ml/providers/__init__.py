"""
ML Providers Package

Implementations of MLProvider interface for different frameworks.

Available providers:
- SlideflowProvider: Slideflow framework (production)
- MockProvider: Mock for testing/development
"""

from .mock_provider import MockProvider
from .slideflow_provider import SlideflowProvider

__all__ = ["SlideflowProvider", "MockProvider"]
