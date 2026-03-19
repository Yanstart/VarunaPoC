"""
Background Tasks Service - Pre-computation of ML embeddings.

Triggered when a slide is opened via GET /slides/{id}/info.
Checks disk cache first, then runs extraction via MLProvider in background.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Track in-progress tasks to avoid duplicates
_active_tasks: set = set()


async def precompute_embeddings(slide_id: str, slide_path: str) -> None:
    """Pre-compute and cache embeddings for a slide.

    Called as a FastAPI BackgroundTask. Skips if already cached or in progress.
    """
    if slide_id in _active_tasks:
        logger.debug("Embeddings already being computed for %s", slide_id)
        return

    _active_tasks.add(slide_id)
    try:
        from services.cache.disk_cache import DiskCache

        cache = DiskCache()

        model_name = os.getenv("ML_EXTRACTOR", "resnet50_imagenet")
        if cache.exists(slide_id, model_name, "embeddings"):
            logger.debug("Embeddings already cached for %s", slide_id)
            return

        from core.interfaces import get_provider

        provider_name = os.getenv("ML_PROVIDER", "slideflow")
        ml_device = os.getenv("ML_DEVICE", "auto")
        provider = get_provider(provider_name, device=ml_device)

        if not provider.model_loaded:
            logger.warning("ML provider not loaded, skipping pre-computation for %s", slide_id)
            return

        result = provider.extract_features(slide_path, tile_size=224, overlap=0)
        cache.save_embeddings(slide_id, model_name, result.embeddings)
        logger.info("Pre-computed embeddings for %s: shape=%s", slide_id, result.embeddings.shape)

    except Exception as e:
        logger.error("Background embedding extraction failed for %s: %s", slide_id, e)
    finally:
        _active_tasks.discard(slide_id)
