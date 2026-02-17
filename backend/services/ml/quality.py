"""
Quality Control Service — Automatic slide quality assessment.

Two modes:
- Mock mode (default): Deterministic quality score seeded from slide path hash.
- Real mode: Feature norm analysis on cached embeddings (sklearn std deviation).

Reference: Issue #93 [W4-ML]
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

ARTIFACT_TYPES = ["fold", "blur", "bubble", "discoloration"]
SEVERITY_LEVELS = ["minor", "moderate", "severe"]


@dataclass
class ArtifactInfo:
    type: str  # fold, blur, bubble, discoloration
    severity: str  # minor, moderate, severe
    bbox: List[int]  # [x1, y1, x2, y2]
    area_percent: float


@dataclass
class QualityResult:
    overall_score: float
    quality_label: str
    artifacts: List[ArtifactInfo]
    recommendation: str
    processing_time_ms: float
    metadata: Optional[Dict] = field(default_factory=dict)


def _score_to_label(score: float) -> str:
    """Map quality score to a French label."""
    if score > 0.8:
        return "Bonne"
    elif score >= 0.6:
        return "Acceptable"
    else:
        return "À refaire"


def _score_to_recommendation(score: float) -> str:
    """Generate a recommendation string based on quality score."""
    if score > 0.8:
        return "Qualité suffisante pour diagnostic"
    elif score >= 0.6:
        return "Qualité acceptable — vérifier les zones artéfactées avant diagnostic"
    else:
        return "Qualité insuffisante — rescanner la lame recommandé"


class QualityService:
    """Quality assessment service with mock and real modes."""

    def assess_quality(
        self,
        slide_path: str,
        disk_cache=None,
        model_id: str = "unknown",
    ) -> QualityResult:
        """
        Assess quality of a slide.

        If disk_cache has cached embeddings and sklearn is available,
        uses real feature norm analysis. Otherwise falls back to
        deterministic mock mode.
        """
        start = time.time()

        # Try real mode if disk_cache is available
        if disk_cache is not None:
            try:
                result = self._assess_real(slide_path, disk_cache, model_id)
                result.processing_time_ms = (time.time() - start) * 1000
                return result
            except Exception as e:
                logger.warning("Real quality assessment failed, falling back to mock: %s", e)

        # Mock mode
        result = self._assess_mock(slide_path)
        result.processing_time_ms = (time.time() - start) * 1000
        return result

    def _assess_mock(self, slide_path: str) -> QualityResult:
        """Deterministic mock quality assessment seeded from slide path hash."""
        seed = int(hashlib.md5(slide_path.encode()).hexdigest(), 16) % (2**32)
        import random

        rng = random.Random(seed)

        # Generate overall score (0.0 - 1.0)
        overall_score = round(rng.uniform(0.0, 1.0), 4)

        quality_label = _score_to_label(overall_score)
        recommendation = _score_to_recommendation(overall_score)

        # Generate 0-3 mock artifacts
        num_artifacts = rng.randint(0, 3)
        artifacts = []
        for _ in range(num_artifacts):
            art_type = rng.choice(ARTIFACT_TYPES)
            severity = rng.choice(SEVERITY_LEVELS)
            x1 = rng.randint(0, 40000)
            y1 = rng.randint(0, 30000)
            x2 = x1 + rng.randint(500, 3000)
            y2 = y1 + rng.randint(500, 3000)
            area_percent = round(rng.uniform(0.5, 10.0), 1)
            artifacts.append(
                ArtifactInfo(
                    type=art_type,
                    severity=severity,
                    bbox=[x1, y1, x2, y2],
                    area_percent=area_percent,
                )
            )

        return QualityResult(
            overall_score=overall_score,
            quality_label=quality_label,
            artifacts=artifacts,
            recommendation=recommendation,
            processing_time_ms=0,
            metadata={"mode": "mock"},
        )

    def _assess_real(
        self,
        slide_path: str,
        disk_cache,
        model_id: str,
    ) -> QualityResult:
        """Real quality assessment via feature norm analysis on cached embeddings."""
        # Extract slide_id from path for cache lookup
        from pathlib import Path

        import numpy as np

        slide_id = Path(slide_path).stem

        # Load embeddings from disk cache
        embeddings = disk_cache.load_embeddings(slide_id, model_id)
        if embeddings is None:
            raise ValueError(f"No cached embeddings for slide {slide_id} / model {model_id}")

        # Compute feature norms
        norms = np.linalg.norm(embeddings, axis=1)
        mean_norm = float(np.mean(norms))
        std_norm = float(np.std(norms))

        # Score based on norm consistency (lower std = higher quality)
        # Normalize std relative to mean to get coefficient of variation
        cv = std_norm / mean_norm if mean_norm > 0 else 1.0
        # Map CV to score: CV < 0.1 -> ~1.0, CV > 0.5 -> ~0.0
        overall_score = round(max(0.0, min(1.0, 1.0 - (cv * 2.0))), 4)

        quality_label = _score_to_label(overall_score)
        recommendation = _score_to_recommendation(overall_score)

        # Detect potential artifact regions (tiles with outlier norms)
        threshold_low = mean_norm - 2 * std_norm
        threshold_high = mean_norm + 2 * std_norm
        outlier_mask = (norms < threshold_low) | (norms > threshold_high)
        n_outliers = int(np.sum(outlier_mask))

        artifacts = []
        if n_outliers > 0:
            artifacts.append(
                ArtifactInfo(
                    type="blur",
                    severity="moderate" if n_outliers > 5 else "minor",
                    bbox=[0, 0, 1000, 1000],
                    area_percent=round(100.0 * n_outliers / len(norms), 1),
                )
            )

        return QualityResult(
            overall_score=overall_score,
            quality_label=quality_label,
            artifacts=artifacts,
            recommendation=recommendation,
            processing_time_ms=0,
            metadata={
                "mode": "real",
                "model_id": model_id,
                "mean_norm": round(mean_norm, 4),
                "std_norm": round(std_norm, 4),
                "n_outlier_tiles": n_outliers,
            },
        )
