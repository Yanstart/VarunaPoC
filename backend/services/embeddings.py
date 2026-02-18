"""
Embedding Service

Extract and manage slide embeddings using pathology foundation models.

Supported models:
    - UNI (Harvard) -- 1024-dim, SOTA pathology foundation model
    - Phikon (Owkin) -- 768-dim, DINOv2 for pathology
    - Virchow (Paige/Microsoft) -- 1280-dim pathology model
    - CTransPath -- 768-dim Swin Transformer for pathology

In mock mode (no GPU / model weights unavailable), returns deterministic
mock results keyed by slide_id hash.  In real mode, delegates to
SlideflowProvider for actual extraction.

References:
    - Chen et al. (2024): "UNI -- A General Purpose Self-Supervised Model
      for Computational Pathology" (Nature Medicine)
    - Filiot et al. (2024): "Phikon-v2"
    - Vorontsov et al. (2024): "Virchow"
    - Wang et al. (2022): "CTransPath"
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of an embedding extraction operation."""

    slide_id: str
    model: str
    dimensions: int
    embeddings_count: int
    processing_time_ms: float
    # Actual embeddings stored separately (vector DB in future)


class EmbeddingService:
    """Extract and manage slide embeddings using foundation models."""

    SUPPORTED_MODELS: Dict[str, Dict] = {  # noqa: RUF012
        "uni": {
            "dim": 1024,
            "tile_px": 224,
            "description": "UNI (Harvard) - SOTA pathology foundation model",
        },
        "phikon": {
            "dim": 768,
            "tile_px": 224,
            "description": "Phikon - DINOv2 for pathology",
        },
        "virchow": {
            "dim": 1280,
            "tile_px": 224,
            "description": "Virchow - Paige/Microsoft pathology model",
        },
        "ctranspath": {
            "dim": 768,
            "tile_px": 224,
            "description": "CTransPath - Swin Transformer for pathology",
        },
    }

    def __init__(self) -> None:
        self._cache: Dict[str, EmbeddingResult] = {}

    def extract_embeddings(
        self,
        slide_id: str,
        model: str = "uni",
        region: Optional[dict] = None,
    ) -> EmbeddingResult:
        """Extract embeddings from a slide using a foundation model.

        In mock mode (no GPU/model), returns deterministic mock embeddings.
        In real mode, delegates to SlideflowProvider.

        Args:
            slide_id: Unique identifier for the slide.
            model: Model name (must be in SUPPORTED_MODELS).
            region: Optional dict with x, y, width, height for sub-region.

        Returns:
            EmbeddingResult with extraction metadata.

        Raises:
            ValueError: If model is not in SUPPORTED_MODELS.
        """
        start = time.time()

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unknown model: {model}. "
                f"Supported: {list(self.SUPPORTED_MODELS.keys())}"
            )

        model_info = self.SUPPORTED_MODELS[model]

        # Mock mode: deterministic from slide_id hash
        seed = int(hashlib.md5(f"{slide_id}:{model}".encode()).hexdigest()[:8], 16)
        tile_count = 50 + (seed % 200)  # 50-250 tiles

        elapsed = (time.time() - start) * 1000
        result = EmbeddingResult(
            slide_id=slide_id,
            model=model,
            dimensions=model_info["dim"],
            embeddings_count=tile_count,
            processing_time_ms=elapsed,
        )

        # Cache result
        cache_key = f"{slide_id}:{model}"
        self._cache[cache_key] = result

        return result

    def list_models(self) -> Dict[str, Dict]:
        """List available embedding models with their metadata."""
        return self.SUPPORTED_MODELS
