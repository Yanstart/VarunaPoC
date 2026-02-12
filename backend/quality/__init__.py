"""
Quality Metrics Module - Inter-annotator agreement analysis.

Phase 4: Measures Cohen's/Fleiss' kappa, confusion matrices,
per-label F1/P/R, IoU distributions, and disagreement heatmaps
for multi-annotator histological slide annotations.

Requires annotations module to be enabled (PostGIS spatial queries).
"""

import os

QUALITY_ENABLED = os.getenv("QUALITY_ENABLED", "true").lower() == "true"

__all__ = ["QUALITY_ENABLED"]
