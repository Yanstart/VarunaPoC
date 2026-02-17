"""
Cell Counting Service — Ki-67 / IHC automated cell counting.

Two modes:
- Mock mode (default): Deterministic counts seeded from slide path hash.
- Real mode: Uses heatmap_to_contours() with small min_area for cell-level detection.

Reference: Issue #81 [W4-ML01]
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CellCountResult:
    total_cells: int
    positive: int
    negative: int
    ratio: float
    percentage: str
    processing_time_ms: float
    metadata: Optional[Dict] = field(default_factory=dict)


class CellCountingService:
    """Cell counting service with mock and real modes."""

    def count_cells(
        self,
        slide_path: str,
        provider=None,
        stain: str = "Ki67",
        region=None,
    ) -> CellCountResult:
        """
        Count cells in a slide.

        If provider has a loaded model capable of generating heatmaps,
        uses real contour-based counting. Otherwise falls back to
        deterministic mock mode.
        """
        start = time.time()

        # Try real mode if provider is available and loaded
        if provider and getattr(provider, "model_loaded", False):
            try:
                result = self._count_real(slide_path, provider, stain, region)
                result.processing_time_ms = (time.time() - start) * 1000
                return result
            except Exception as e:
                logger.warning("Real counting failed, falling back to mock: %s", e)

        # Mock mode
        result = self._count_mock(slide_path, stain)
        result.processing_time_ms = (time.time() - start) * 1000
        return result

    def _count_mock(self, slide_path: str, stain: str) -> CellCountResult:
        """Deterministic mock counts seeded from slide path hash."""
        seed = int(hashlib.md5(slide_path.encode()).hexdigest(), 16) % (2**32)
        import random

        rng = random.Random(seed)

        total = rng.randint(800, 2500)
        # Ki-67 ratio typically 5-40% in breast cancer
        ki67_pct = rng.uniform(0.05, 0.40)
        positive = int(total * ki67_pct)
        negative = total - positive
        ratio = round(positive / total, 4)
        percentage = f"{ratio * 100:.1f}%"

        return CellCountResult(
            total_cells=total,
            positive=positive,
            negative=negative,
            ratio=ratio,
            percentage=percentage,
            processing_time_ms=0,
            metadata={"mode": "mock", "stain": stain},
        )

    def _count_real(
        self,
        slide_path: str,
        provider,
        stain: str,
        region=None,
    ) -> CellCountResult:
        """Real counting via heatmap contour extraction."""
        import numpy as np

        from services.detection.postprocessing import heatmap_to_contours

        # Generate heatmap from provider
        heatmap_result = provider.generate_heatmap(slide_path, "tissue", 2)
        heatmap = heatmap_result.heatmap

        # Extract cell-level contours (min_area=10 for small cells)
        contours = heatmap_to_contours(
            heatmap,
            threshold=0.3,
            min_area=10,
            closing_iterations=1,
        )

        if not contours:
            return CellCountResult(
                total_cells=0,
                positive=0,
                negative=0,
                ratio=0.0,
                percentage="0.0%",
                processing_time_ms=0,
                metadata={"mode": "real", "stain": stain},
            )

        # Classify positive/negative via mean intensity in each contour
        total = len(contours)
        positive = 0
        intensity_threshold = 0.5

        for _contour, confidence in contours:
            if confidence >= intensity_threshold:
                positive += 1

        negative = total - positive
        ratio = round(positive / total, 4) if total > 0 else 0.0
        percentage = f"{ratio * 100:.1f}%"

        return CellCountResult(
            total_cells=total,
            positive=positive,
            negative=negative,
            ratio=ratio,
            percentage=percentage,
            processing_time_ms=0,
            metadata={"mode": "real", "stain": stain, "contours_found": total},
        )
