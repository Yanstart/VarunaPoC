"""
Feature Flag Registry

Central registry tracking which optional features are enabled at runtime.
Populated during app startup based on try/except import results and env vars.

Usage:
    from core.feature_flags import feature_registry

    feature_registry.register("annotations", True)
    feature_registry.is_enabled("annotations")  # True
    feature_registry.get_all()  # {"annotations": True, ...}
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class FeatureRegistry:
    """Singleton registry of feature flags and their enabled/disabled status."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._features: Dict[str, bool] = {}
        return cls._instance

    def register(self, name: str, enabled: bool) -> None:
        """Register a feature flag with its enabled status."""
        self._features[name] = enabled
        logger.info("Feature '%s' registered as %s", name, "enabled" if enabled else "disabled")

    def is_enabled(self, name: str) -> bool:
        """Check if a feature is enabled. Returns False if not registered."""
        return self._features.get(name, False)

    def get_all(self) -> Dict[str, bool]:
        """Return a copy of all registered feature flags."""
        return dict(self._features)

    def reset(self) -> None:
        """Clear all registered features. Useful for testing."""
        self._features.clear()


# Module-level singleton instance
feature_registry = FeatureRegistry()
