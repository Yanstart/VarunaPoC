"""Centralized singleton service container.

Provides lazy-initialized singletons for ML provider, caches, and other
shared services. Centralizes the scattered module-level globals from routes
into a single registry that can be reset for testing.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Lazy singleton registry for shared services.

    Note: not thread-safe. Under ASGI with a single event loop this is fine;
    concurrent threads would need a ``threading.Lock`` around each getter.
    """

    _ml_provider: Any = None
    _ml_config_hash: str | None = None
    _memory_cache: Any = None
    _disk_cache: Any = None

    @classmethod
    def get_ml_provider(cls):
        """Get or create the ML provider singleton.

        Raises HTTPException 503 if ML is disabled or provider fails to init.
        """
        from fastapi import HTTPException

        ml_enabled = os.getenv("ML_ENABLED", "true").lower() == "true"
        if not ml_enabled:
            raise HTTPException(503, "ML features disabled in configuration")

        provider_name = os.getenv("ML_PROVIDER", "slideflow")
        ml_mode = os.getenv("ML_MODE", "extractor")
        extractor_name = os.getenv("ML_EXTRACTOR", "resnet50_imagenet")
        model_path = os.getenv("ML_MODEL_PATH", "")
        config_hash = f"{provider_name}:{ml_mode}:{extractor_name}:{model_path}"

        if cls._ml_provider is not None and cls._ml_config_hash == config_hash:
            return cls._ml_provider

        try:
            from services.ml.provider_factory import get_provider

            provider = get_provider(provider_name)

            if provider_name == "slideflow" and not provider.model_loaded:
                classes_str = os.getenv("ML_CLASSES", "tissue,background")
                classes = [c.strip() for c in classes_str.split(",") if c.strip()]

                if ml_mode == "classifier" and model_path:
                    provider.load_model(
                        model_path,
                        {
                            "model_id": os.getenv("ML_MODEL_ID", "custom_classifier"),
                            "mode": "classifier",
                            "classes": classes,
                            "tile_size": int(os.getenv("ML_TILE_SIZE", "224")),
                            "num_mc_samples": int(os.getenv("ML_MC_SAMPLES", "10")),
                        },
                    )
                else:
                    provider.load_model(
                        f"extractor://{extractor_name}",
                        {
                            "model_id": f"{extractor_name}_features",
                            "mode": "extractor",
                            "classes": classes,
                        },
                    )

            cls._ml_provider = provider
            cls._ml_config_hash = config_hash
            return provider

        except Exception as e:
            logger.error("Failed to initialize ML provider: %s", e)
            raise HTTPException(503, "ML provider unavailable") from e

    @classmethod
    def get_memory_cache(cls):
        """Get or create the in-memory prediction cache."""
        if cls._memory_cache is None:
            from services.cache.memory_cache import MemoryCache

            cls._memory_cache = MemoryCache(maxsize=512, ttl=300)
        return cls._memory_cache

    @classmethod
    def get_disk_cache(cls):
        """Get or create the disk-based prediction cache."""
        if cls._disk_cache is None:
            from services.cache.disk_cache import DiskCache

            cls._disk_cache = DiskCache()
        return cls._disk_cache

    @classmethod
    def reset(cls):
        """Reset all singletons (for testing)."""
        cls._ml_provider = None
        cls._ml_config_hash = None
        cls._memory_cache = None
        cls._disk_cache = None
