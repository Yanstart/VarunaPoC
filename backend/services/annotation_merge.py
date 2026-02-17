"""
Annotation Merge Service - Automatic annotation conflict resolution.

Merges annotations from multiple users with configurable strategies:
- UNION: keep all annotations, mark overlapping pairs as conflicts
- LAST_WRITE_WINS: for conflicting pairs, keep the most recently created
- INTERSECTION: keep only annotations that overlap with at least one other

Conflict detection uses bounding-box IoU (Intersection over Union) on
GeoJSON geometries with a configurable threshold.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# Minimum IoU to consider two annotations as conflicting
DEFAULT_IOU_THRESHOLD = 0.3


class MergeStrategy(str, Enum):
    LAST_WRITE_WINS = "last_write_wins"
    UNION = "union"
    INTERSECTION = "intersection"


@dataclass
class MergeConflict:
    """A pair of overlapping annotations detected during merge."""

    annotation_a: dict
    annotation_b: dict
    overlap_iou: float
    resolution: str
    resolved_annotation: Optional[dict]


@dataclass
class MergeResult:
    """Result of an annotation merge operation."""

    strategy: str
    total_input: int
    merged_count: int
    conflicts_found: int
    conflicts_resolved: int
    conflicts: list = field(default_factory=list)
    merged_annotations: list = field(default_factory=list)
    processing_time_ms: float = 0.0


def _bbox_from_geometry(geom: dict) -> Optional[tuple]:
    """Extract (min_x, min_y, max_x, max_y) bounding box from a GeoJSON geometry.

    Supports Point, Polygon, and any geometry with a 'coordinates' field.
    Falls back to 'bbox' property if present on the annotation dict.
    """
    if not isinstance(geom, dict):
        return None

    # Direct bbox field
    if "bbox" in geom:
        b = geom["bbox"]
        if len(b) >= 4:
            return (b[0], b[1], b[2], b[3])

    coords = geom.get("coordinates")
    if coords is None:
        return None

    geo_type = geom.get("type", "")

    if geo_type == "Point" and len(coords) >= 2:
        return (coords[0], coords[1], coords[0], coords[1])

    # Flatten nested coordinate lists to find extent
    flat = _flatten_coords(coords)
    if not flat:
        return None

    xs = [p[0] for p in flat]
    ys = [p[1] for p in flat]
    return (min(xs), min(ys), max(xs), max(ys))


def _flatten_coords(coords) -> list:
    """Recursively flatten nested coordinate arrays into a list of [x, y] points."""
    if not coords:
        return []
    # If the first element is a number, this is a coordinate pair
    if isinstance(coords[0], (int, float)):
        return [coords]
    result = []
    for item in coords:
        result.extend(_flatten_coords(item))
    return result


class AnnotationMergeService:
    """Merge annotations from multiple users with conflict resolution."""

    def __init__(self, iou_threshold: float = DEFAULT_IOU_THRESHOLD):
        self.iou_threshold = iou_threshold

    def merge(
        self,
        annotation_sets: list[list[dict]],
        strategy: MergeStrategy = MergeStrategy.UNION,
    ) -> MergeResult:
        """Merge multiple sets of annotations.

        Args:
            annotation_sets: List of annotation lists (one per user/source).
            strategy: Conflict resolution strategy.

        Returns:
            MergeResult with merged annotations and conflict info.
        """
        start = time.time()

        all_annotations = [a for s in annotation_sets for a in s]
        total_input = len(all_annotations)
        conflicts = self._detect_conflicts(all_annotations)

        if strategy == MergeStrategy.LAST_WRITE_WINS:
            merged = self._last_write_wins(all_annotations, conflicts)
        elif strategy == MergeStrategy.UNION:
            merged = self._union(all_annotations, conflicts)
        elif strategy == MergeStrategy.INTERSECTION:
            merged = self._intersection(all_annotations, conflicts)
        else:
            merged = list(all_annotations)

        elapsed_ms = (time.time() - start) * 1000

        return MergeResult(
            strategy=strategy.value,
            total_input=total_input,
            merged_count=len(merged),
            conflicts_found=len(conflicts),
            conflicts_resolved=len(conflicts),
            conflicts=conflicts,
            merged_annotations=merged,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def _detect_conflicts(self, annotations: list[dict]) -> list[MergeConflict]:
        """Find overlapping annotations from different users.

        Compares bounding boxes pairwise; annotations with IoU above the
        threshold and different created_by values are considered conflicts.
        """
        conflicts = []
        n = len(annotations)

        for i in range(n):
            for j in range(i + 1, n):
                a = annotations[i]
                b = annotations[j]

                # Only consider conflicts between different users
                user_a = a.get("created_by", "")
                user_b = b.get("created_by", "")
                if user_a and user_b and user_a == user_b:
                    continue

                geom_a = a.get("geometry", {})
                geom_b = b.get("geometry", {})

                iou = self.compute_iou(geom_a, geom_b)
                if iou >= self.iou_threshold:
                    conflicts.append(
                        MergeConflict(
                            annotation_a=a,
                            annotation_b=b,
                            overlap_iou=round(iou, 4),
                            resolution="pending",
                            resolved_annotation=None,
                        )
                    )

        return conflicts

    def compute_iou(self, geom_a: dict, geom_b: dict) -> float:
        """Compute IoU from GeoJSON geometries using bounding box approximation.

        Returns 0.0 if either geometry lacks valid coordinates.
        """
        bbox_a = _bbox_from_geometry(geom_a)
        bbox_b = _bbox_from_geometry(geom_b)

        if bbox_a is None or bbox_b is None:
            return 0.0

        # Intersection
        x1 = max(bbox_a[0], bbox_b[0])
        y1 = max(bbox_a[1], bbox_b[1])
        x2 = min(bbox_a[2], bbox_b[2])
        y2 = min(bbox_a[3], bbox_b[3])

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)

        area_a = (bbox_a[2] - bbox_a[0]) * (bbox_a[3] - bbox_a[1])
        area_b = (bbox_b[2] - bbox_b[0]) * (bbox_b[3] - bbox_b[1])
        union = area_a + area_b - intersection

        if union <= 0:
            return 0.0

        return intersection / union

    def _last_write_wins(
        self, annotations: list[dict], conflicts: list[MergeConflict]
    ) -> list[dict]:
        """For each conflicting pair, keep the more recently created annotation."""
        # Collect IDs of annotations to drop
        drop_ids = set()

        for conflict in conflicts:
            a = conflict.annotation_a
            b = conflict.annotation_b

            time_a = a.get("created_at", "")
            time_b = b.get("created_at", "")

            # Keep the one with later created_at; if equal, keep b
            if time_a > time_b:
                winner = a
                loser = b
            else:
                winner = b
                loser = a

            loser_id = id(loser)
            drop_ids.add(loser_id)

            conflict.resolution = "last_write_wins"
            conflict.resolved_annotation = winner

        return [a for a in annotations if id(a) not in drop_ids]

    def _union(self, annotations: list[dict], conflicts: list[MergeConflict]) -> list[dict]:
        """Keep all annotations; mark conflicts as resolved with 'union' strategy."""
        for conflict in conflicts:
            conflict.resolution = "union_kept_both"
            conflict.resolved_annotation = None

        return list(annotations)

    def _intersection(
        self, annotations: list[dict], conflicts: list[MergeConflict]
    ) -> list[dict]:
        """Keep only annotations that are involved in at least one conflict."""
        if not conflicts:
            return []

        # Collect all annotations that participate in conflicts
        conflict_ids = set()
        for conflict in conflicts:
            conflict_ids.add(id(conflict.annotation_a))
            conflict_ids.add(id(conflict.annotation_b))
            conflict.resolution = "intersection"
            conflict.resolved_annotation = None

        return [a for a in annotations if id(a) in conflict_ids]


# Module-level singleton
merge_service = AnnotationMergeService()
