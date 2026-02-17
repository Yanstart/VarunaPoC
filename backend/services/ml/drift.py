"""
Drift Detector Service — Model drift monitoring via distribution comparison.

Two modes:
- Mock mode (default): Deterministic fake drift metrics seeded from model_id hash.
- Real mode: Would compare embedding distributions (not implemented yet).

Reference: Issue #95 [W4-ML03]
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DriftMetric:
    metric_name: str  # "mmd" or "ks_statistic"
    value: float
    threshold: float
    is_drifted: bool
    window_size: int


@dataclass
class ModelDriftReport:
    model_id: str
    report_date: str  # ISO datetime
    metrics: List[DriftMetric]
    overall_drifted: bool
    recommendation: str
    processing_time_ms: float
    metadata: Optional[Dict] = field(default_factory=dict)


class DriftDetectorService:
    """Drift detection service with mock and real modes."""

    def detect_drift(self, model_id: str) -> ModelDriftReport:
        """
        Detect drift for a given model.

        Currently only mock mode is implemented. Real mode would
        compare embedding distributions from recent inference
        against a reference distribution.
        """
        start = time.time()
        result = self._detect_mock(model_id)
        result.processing_time_ms = (time.time() - start) * 1000
        return result

    def _detect_mock(self, model_id: str) -> ModelDriftReport:
        """Deterministic mock drift metrics seeded from model_id hash."""
        seed = int(hashlib.md5(model_id.encode()).hexdigest(), 16) % (2**32)
        import random

        rng = random.Random(seed)

        # MMD value: 0.01-0.15, threshold 0.10
        mmd_value = round(rng.uniform(0.01, 0.15), 4)
        mmd_threshold = 0.10
        mmd_drifted = mmd_value > mmd_threshold

        # KS statistic: 0.05-0.25, threshold 0.15
        ks_value = round(rng.uniform(0.05, 0.25), 4)
        ks_threshold = 0.15
        ks_drifted = ks_value > ks_threshold

        metrics = [
            DriftMetric(
                metric_name="mmd",
                value=mmd_value,
                threshold=mmd_threshold,
                is_drifted=mmd_drifted,
                window_size=100,
            ),
            DriftMetric(
                metric_name="ks_statistic",
                value=ks_value,
                threshold=ks_threshold,
                is_drifted=ks_drifted,
                window_size=100,
            ),
        ]

        overall_drifted = any(m.is_drifted for m in metrics)
        recommendation = "Consider retraining" if overall_drifted else "No action needed"

        return ModelDriftReport(
            model_id=model_id,
            report_date=datetime.now(timezone.utc).isoformat(),
            metrics=metrics,
            overall_drifted=overall_drifted,
            recommendation=recommendation,
            processing_time_ms=0,
            metadata={"mode": "mock"},
        )
