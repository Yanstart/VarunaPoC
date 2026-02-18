"""
Annotation Outlier Detection Service

Detects outlier annotations based on statistical analysis of size,
position, shape, and timing characteristics.

Analysis categories:
- Size: Flags annotations with z-score > 3 for area.
- Position: Flags annotations whose centroid falls outside slide bounds.
- Shape: Flags extremely thin or irregular annotations (low area/perimeter ratio).
- Timing: Flags annotations created in under 1 second (suspiciously fast).
- Inconsistency: Flags annotations whose label differs from the majority
  in the same spatial region.

Reference: Issue #37
"""

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class OutlierScore:
    """A single annotation flagged as an outlier."""

    annotation_id: str
    score: float  # 0.0 (normal) to 1.0 (outlier)
    reasons: List[str]
    category: str  # "size", "position", "shape", "timing", "inconsistency"


@dataclass
class OutlierReport:
    """Summary of outlier detection for a set of annotations."""

    total_annotations: int
    outlier_count: int
    outliers: List[OutlierScore]
    processing_time_ms: float


class AnnotationOutlierService:
    """Detect outlier annotations based on statistical analysis."""

    SIZE_Z_THRESHOLD = 3.0  # z-score threshold for size outliers
    MIN_ANNOTATION_TIME_S = 1.0  # annotations faster than this are suspicious
    SHAPE_COMPACTNESS_THRESHOLD = 0.01  # area / perimeter^2, below = very irregular

    def detect_outliers(
        self,
        annotations: List[dict],
        slide_dimensions: Optional[Tuple[int, int]] = None,
    ) -> OutlierReport:
        """
        Analyze annotations and flag outliers.

        Args:
            annotations: List of annotation dicts. Expected fields:
                - id (str): annotation identifier
                - geometry (dict): GeoJSON geometry with "type" and "coordinates"
                - properties (dict, optional): may contain "label", "created_at", "updated_at"
            slide_dimensions: Optional (width, height) of the slide in pixels.

        Returns:
            OutlierReport with flagged outliers.
        """
        start = time.time()

        if not annotations:
            return OutlierReport(
                total_annotations=0,
                outlier_count=0,
                outliers=[],
                processing_time_ms=0.0,
            )

        # Collect all outlier flags per annotation
        outlier_map: Dict[str, OutlierScore] = {}

        # Run each detection pass
        self._size_outliers(annotations, outlier_map)
        self._position_outliers(annotations, slide_dimensions, outlier_map)
        self._shape_outliers(annotations, outlier_map)
        self._timing_outliers(annotations, outlier_map)
        self._inconsistency_outliers(annotations, outlier_map)

        outliers = list(outlier_map.values())
        elapsed_ms = (time.time() - start) * 1000

        return OutlierReport(
            total_annotations=len(annotations),
            outlier_count=len(outliers),
            outliers=outliers,
            processing_time_ms=round(elapsed_ms, 2),
        )

    # ------------------------------------------------------------------
    # Detection methods
    # ------------------------------------------------------------------

    def _size_outliers(
        self,
        annotations: List[dict],
        outlier_map: Dict[str, OutlierScore],
    ) -> None:
        """Flag annotations whose area z-score exceeds SIZE_Z_THRESHOLD."""
        areas = []
        for ann in annotations:
            area = self._compute_area(ann)
            areas.append(area)

        if len(areas) < 2:
            return

        mean_area = sum(areas) / len(areas)
        variance = sum((a - mean_area) ** 2 for a in areas) / len(areas)
        std_area = math.sqrt(variance) if variance > 0 else 0.0

        if std_area < 1e-10:
            return  # All annotations have the same area

        for ann, area in zip(annotations, areas, strict=True):
            z_score = abs(area - mean_area) / std_area
            if z_score > self.SIZE_Z_THRESHOLD:
                ann_id = self._get_id(ann)
                score = min(1.0, z_score / (self.SIZE_Z_THRESHOLD * 2))
                reason = f"Area z-score {z_score:.2f} exceeds threshold {self.SIZE_Z_THRESHOLD}"
                self._add_outlier(outlier_map, ann_id, score, reason, "size")

    def _position_outliers(
        self,
        annotations: List[dict],
        slide_dims: Optional[Tuple[int, int]],
        outlier_map: Dict[str, OutlierScore],
    ) -> None:
        """Flag annotations whose centroid is outside slide bounds."""
        if slide_dims is None:
            return

        width, height = slide_dims
        for ann in annotations:
            centroid = self._compute_centroid(ann)
            if centroid is None:
                continue

            cx, cy = centroid
            if cx < 0 or cy < 0 or cx > width or cy > height:
                ann_id = self._get_id(ann)
                reason = f"Centroid ({cx:.0f}, {cy:.0f}) outside slide bounds ({width}, {height})"
                self._add_outlier(outlier_map, ann_id, 0.9, reason, "position")

    def _shape_outliers(
        self,
        annotations: List[dict],
        outlier_map: Dict[str, OutlierScore],
    ) -> None:
        """Flag annotations with extremely irregular shapes (low compactness)."""
        for ann in annotations:
            area = self._compute_area(ann)
            perimeter = self._compute_perimeter(ann)

            if perimeter < 1e-6 or area < 1e-6:
                continue

            # Isoperimetric quotient: 1.0 for circle, near 0 for very thin shapes
            compactness = (4.0 * math.pi * area) / (perimeter * perimeter)

            if compactness < self.SHAPE_COMPACTNESS_THRESHOLD:
                ann_id = self._get_id(ann)
                reason = f"Shape compactness {compactness:.4f} below threshold {self.SHAPE_COMPACTNESS_THRESHOLD}"
                self._add_outlier(outlier_map, ann_id, 0.7, reason, "shape")

    def _timing_outliers(
        self,
        annotations: List[dict],
        outlier_map: Dict[str, OutlierScore],
    ) -> None:
        """Flag annotations created suspiciously fast (< MIN_ANNOTATION_TIME_S)."""
        for ann in annotations:
            props = ann.get("properties", {}) or {}
            created_at = props.get("created_at")
            updated_at = props.get("updated_at")

            if created_at is None or updated_at is None:
                continue

            try:
                from datetime import datetime

                if isinstance(created_at, str):
                    # Parse ISO format
                    ct = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    ut = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    elapsed = abs((ut - ct).total_seconds())
                elif isinstance(created_at, (int, float)):
                    elapsed = abs(updated_at - created_at)
                else:
                    continue
            except (ValueError, TypeError):
                continue

            if elapsed < self.MIN_ANNOTATION_TIME_S:
                ann_id = self._get_id(ann)
                reason = (
                    f"Annotation time {elapsed:.2f}s below minimum {self.MIN_ANNOTATION_TIME_S}s"
                )
                self._add_outlier(outlier_map, ann_id, 0.8, reason, "timing")

    def _inconsistency_outliers(
        self,
        annotations: List[dict],
        outlier_map: Dict[str, OutlierScore],
    ) -> None:
        """Flag annotations whose label differs from the majority in the same spatial region."""
        # Group annotations by spatial region (grid-based bucketing)
        grid_size = 1000  # pixels
        buckets: Dict[Tuple[int, int], List[Tuple[str, str]]] = {}

        for ann in annotations:
            props = ann.get("properties", {}) or {}
            label = props.get("label")
            if label is None:
                continue

            centroid = self._compute_centroid(ann)
            if centroid is None:
                continue

            cx, cy = centroid
            bucket_key = (int(cx // grid_size), int(cy // grid_size))
            ann_id = self._get_id(ann)
            buckets.setdefault(bucket_key, []).append((ann_id, label))

        # For each bucket, find the majority label and flag minority
        for _bucket_key, entries in buckets.items():
            if len(entries) < 3:
                continue  # Not enough to determine majority

            # Count labels
            label_counts: Dict[str, int] = {}
            for _, label in entries:
                label_counts[label] = label_counts.get(label, 0) + 1

            majority_label = max(label_counts, key=label_counts.get)
            majority_count = label_counts[majority_label]

            # Only flag if majority is clear (> 60% of the bucket)
            if majority_count / len(entries) < 0.6:
                continue

            for ann_id, label in entries:
                if label != majority_label:
                    reason = f"Label '{label}' differs from majority '{majority_label}' in region"
                    self._add_outlier(outlier_map, ann_id, 0.6, reason, "inconsistency")

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_id(ann: dict) -> str:
        """Extract annotation ID from dict."""
        return str(ann.get("id", ann.get("properties", {}).get("id", "unknown")))

    @staticmethod
    def _get_coordinates(ann: dict) -> Optional[List]:
        """Extract coordinate ring from GeoJSON annotation."""
        geometry = ann.get("geometry", {})
        if not geometry:
            return None

        geo_type = geometry.get("type", "")
        coords = geometry.get("coordinates")
        if not coords:
            return None

        if geo_type == "Polygon" and len(coords) > 0:
            return coords[0]  # Outer ring
        elif geo_type == "MultiPolygon" and len(coords) > 0 and len(coords[0]) > 0:
            return coords[0][0]  # First polygon outer ring
        elif geo_type == "LineString":
            return coords

        return None

    def _compute_area(self, ann: dict) -> float:
        """Compute polygon area using Shoelace formula."""
        # Check if area is provided in properties
        props = ann.get("properties", {}) or {}
        if "area" in props:
            return float(props["area"])

        coords = self._get_coordinates(ann)
        if not coords or len(coords) < 3:
            return 0.0

        # Shoelace formula
        n = len(coords)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += coords[i][0] * coords[j][1]
            area -= coords[j][0] * coords[i][1]
        return abs(area) / 2.0

    def _compute_perimeter(self, ann: dict) -> float:
        """Compute polygon perimeter."""
        coords = self._get_coordinates(ann)
        if not coords or len(coords) < 2:
            return 0.0

        perimeter = 0.0
        for i in range(len(coords)):
            j = (i + 1) % len(coords)
            dx = coords[j][0] - coords[i][0]
            dy = coords[j][1] - coords[i][1]
            perimeter += math.sqrt(dx * dx + dy * dy)
        return perimeter

    def _compute_centroid(self, ann: dict) -> Optional[Tuple[float, float]]:
        """Compute polygon centroid."""
        coords = self._get_coordinates(ann)
        if not coords or len(coords) < 1:
            return None

        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    def _add_outlier(
        outlier_map: Dict[str, OutlierScore],
        ann_id: str,
        score: float,
        reason: str,
        category: str,
    ) -> None:
        """Add or update an outlier entry in the map."""
        if ann_id in outlier_map:
            existing = outlier_map[ann_id]
            existing.reasons.append(reason)
            existing.score = max(existing.score, score)
            # Keep the highest-severity category
            if score > existing.score:
                existing.category = category
        else:
            outlier_map[ann_id] = OutlierScore(
                annotation_id=ann_id,
                score=score,
                reasons=[reason],
                category=category,
            )
