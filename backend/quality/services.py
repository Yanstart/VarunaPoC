"""
Quality Services - Orchestration layer connecting matching + metrics.

Connects PostGIS spatial matching with pure metric functions.
Optional caching via quality_reports table.
"""

import json
import logging
from typing import Dict, List

from sqlalchemy import case, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.annotation import Annotation
from models.annotation_label import AnnotationLabel
from quality.config import UNLABELED_CATEGORY
from quality.matching import grid_matching, iou_matching
from quality.metrics import (
    cohens_kappa,
    confusion_matrix,
    fleiss_kappa,
    interpret_kappa,
    iou_distribution_stats,
    per_label_f1,
)

logger = logging.getLogger(__name__)

# Optional cache model
try:
    from models.quality_report import QualityReport  # noqa: F401

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


# ==========================================
# ANNOTATORS
# ==========================================


async def get_annotators(db: AsyncSession, slide_id: str) -> List[Dict]:
    """Get list of annotators who have annotated a slide."""
    query = (
        select(
            Annotation.created_by,
            func.count(Annotation.id).label("count"),
        )
        .where(Annotation.slide_id == slide_id)
        .where(Annotation.created_by.isnot(None))
        .group_by(Annotation.created_by)
        .order_by(func.count(Annotation.id).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    annotators = []
    for row in rows:
        # Get labels used by this annotator
        labels_query = (
            select(func.coalesce(AnnotationLabel.name, literal_column(f"'{UNLABELED_CATEGORY}'")))
            .join(AnnotationLabel, Annotation.label_id == AnnotationLabel.id, isouter=True)
            .where(Annotation.slide_id == slide_id)
            .where(Annotation.created_by == row.created_by)
            .distinct()
        )
        labels_result = await db.execute(labels_query)
        labels_used = [r[0] for r in labels_result.all()]

        annotators.append(
            {
                "username": row.created_by,
                "annotation_count": row.count,
                "labels_used": labels_used,
            }
        )

    return annotators


# ==========================================
# PAIRWISE KAPPA
# ==========================================


async def compute_pairwise_kappa(
    db: AsyncSession,
    slide_id: str,
    annotator_a: str,
    annotator_b: str,
    iou_threshold: float = 0.5,
    matching_strategy: str = "iou",
    grid_cell_size: int = 256,
    point_buffer_radius: float = 50.0,
) -> Dict:
    """Compute Cohen's kappa between two annotators."""
    if matching_strategy == "iou":
        labels_a, labels_b, unmatched_a, unmatched_b, _ = await iou_matching(
            db,
            slide_id,
            annotator_a,
            annotator_b,
            iou_threshold=iou_threshold,
            point_buffer_radius=point_buffer_radius,
        )
    else:
        # Grid-based for pairwise: use grid matching with 2 annotators
        matrix, categories = await grid_matching(
            db,
            slide_id,
            [annotator_a, annotator_b],
            grid_cell_size=grid_cell_size,
            point_buffer_radius=point_buffer_radius,
        )
        # Convert rating matrix to pairwise labels
        # Each row has [count_cat0, count_cat1, ...] with sum=2
        labels_a = []
        labels_b = []
        for row in matrix:
            cats_in_row = []
            for idx, count in enumerate(row):
                cats_in_row.extend([categories[idx]] * count)
            if len(cats_in_row) == 2:
                labels_a.append(cats_in_row[0])
                labels_b.append(cats_in_row[1])
        unmatched_a = 0
        unmatched_b = 0

    if not labels_a:
        return {
            "kappa": 0.0,
            "interpretation": "Poor",
            "annotator_a": annotator_a,
            "annotator_b": annotator_b,
            "n_matched": 0,
            "n_unmatched_a": unmatched_a,
            "n_unmatched_b": unmatched_b,
            "matching_strategy": matching_strategy,
        }

    kappa = cohens_kappa(labels_a, labels_b)

    return {
        "kappa": round(kappa, 4),
        "interpretation": interpret_kappa(kappa),
        "annotator_a": annotator_a,
        "annotator_b": annotator_b,
        "n_matched": len(labels_a),
        "n_unmatched_a": unmatched_a,
        "n_unmatched_b": unmatched_b,
        "matching_strategy": matching_strategy,
    }


# ==========================================
# FLEISS' KAPPA
# ==========================================


async def compute_fleiss_kappa(
    db: AsyncSession,
    slide_id: str,
    annotators: List[str],
    grid_cell_size: int = 256,
    point_buffer_radius: float = 50.0,
) -> Dict:
    """Compute Fleiss' kappa for multiple annotators using grid matching."""
    matrix, categories = await grid_matching(
        db,
        slide_id,
        annotators,
        grid_cell_size=grid_cell_size,
        point_buffer_radius=point_buffer_radius,
    )

    if not matrix:
        return {
            "kappa": 0.0,
            "interpretation": "Poor",
            "annotators": annotators,
            "n_cells": 0,
            "n_categories": 0,
            "categories": [],
        }

    kappa = fleiss_kappa(matrix)

    return {
        "kappa": round(kappa, 4),
        "interpretation": interpret_kappa(kappa),
        "annotators": annotators,
        "n_cells": len(matrix),
        "n_categories": len(categories),
        "categories": categories,
    }


# ==========================================
# CONFUSION MATRIX
# ==========================================


async def compute_confusion_matrix(
    db: AsyncSession,
    slide_id: str,
    annotator_a: str,
    annotator_b: str,
    iou_threshold: float = 0.5,
    matching_strategy: str = "iou",
    grid_cell_size: int = 256,
    point_buffer_radius: float = 50.0,
) -> Dict:
    """Compute confusion matrix between two annotators."""
    labels_a, labels_b = await _get_paired_labels(
        db,
        slide_id,
        annotator_a,
        annotator_b,
        iou_threshold,
        matching_strategy,
        grid_cell_size,
        point_buffer_radius,
    )

    if not labels_a:
        return {
            "matrix": [],
            "categories": [],
            "annotator_a": annotator_a,
            "annotator_b": annotator_b,
            "n_matched": 0,
        }

    matrix, categories = confusion_matrix(labels_a, labels_b)

    return {
        "matrix": matrix,
        "categories": categories,
        "annotator_a": annotator_a,
        "annotator_b": annotator_b,
        "n_matched": len(labels_a),
    }


# ==========================================
# PER-LABEL METRICS
# ==========================================


async def compute_per_label_metrics(
    db: AsyncSession,
    slide_id: str,
    annotator_a: str,
    annotator_b: str,
    iou_threshold: float = 0.5,
    matching_strategy: str = "iou",
    grid_cell_size: int = 256,
    point_buffer_radius: float = 50.0,
) -> Dict:
    """Compute F1/precision/recall per label."""
    labels_a, labels_b = await _get_paired_labels(
        db,
        slide_id,
        annotator_a,
        annotator_b,
        iou_threshold,
        matching_strategy,
        grid_cell_size,
        point_buffer_radius,
    )

    if not labels_a:
        return {
            "metrics": [],
            "annotator_a": annotator_a,
            "annotator_b": annotator_b,
            "n_matched": 0,
        }

    metrics = per_label_f1(labels_a, labels_b)

    return {
        "metrics": metrics,
        "annotator_a": annotator_a,
        "annotator_b": annotator_b,
        "n_matched": len(labels_a),
    }


# ==========================================
# IoU DISTRIBUTION
# ==========================================


async def compute_iou_distribution(
    db: AsyncSession,
    slide_id: str,
    annotator_a: str,
    annotator_b: str,
    iou_threshold: float = 0.0,  # Default 0 to capture all overlaps
    point_buffer_radius: float = 50.0,
) -> Dict:
    """Compute IoU distribution between two annotators."""
    _, _, _, _, iou_values = await iou_matching(
        db,
        slide_id,
        annotator_a,
        annotator_b,
        iou_threshold=iou_threshold,
        point_buffer_radius=point_buffer_radius,
    )

    stats = iou_distribution_stats(iou_values)
    stats["annotator_a"] = annotator_a
    stats["annotator_b"] = annotator_b

    return stats


# ==========================================
# DISAGREEMENT HEATMAP
# ==========================================


async def compute_disagreement_heatmap(
    db: AsyncSession,
    slide_id: str,
    annotator_a: str,
    annotator_b: str,
    iou_threshold: float = 0.5,
    point_buffer_radius: float = 50.0,
) -> Dict:
    """
    Find disagreement regions between two annotators.

    Returns matched annotations where labels differ as GeoJSON features.
    """
    # Get matched pairs with their geometries
    buffered_geom = case(
        (
            Annotation.geometry_type == "point",
            func.ST_Buffer(Annotation.geometry, point_buffer_radius),
        ),
        else_=Annotation.geometry,
    )

    a_alias = (
        select(
            Annotation.id.label("id_a"),
            buffered_geom.label("geom_a"),
            func.coalesce(AnnotationLabel.name, literal_column(f"'{UNLABELED_CATEGORY}'")).label(
                "label_a"
            ),
        )
        .join(AnnotationLabel, Annotation.label_id == AnnotationLabel.id, isouter=True)
        .where(Annotation.slide_id == slide_id)
        .where(Annotation.created_by == annotator_a)
        .subquery("a")
    )

    b_alias = (
        select(
            Annotation.id.label("id_b"),
            buffered_geom.label("geom_b"),
            func.coalesce(AnnotationLabel.name, literal_column(f"'{UNLABELED_CATEGORY}'")).label(
                "label_b"
            ),
        )
        .join(AnnotationLabel, Annotation.label_id == AnnotationLabel.id, isouter=True)
        .where(Annotation.slide_id == slide_id)
        .where(Annotation.created_by == annotator_b)
        .subquery("b")
    )

    intersection_area = func.ST_Area(func.ST_Intersection(a_alias.c.geom_a, b_alias.c.geom_b))
    union_area = func.ST_Area(func.ST_Union(a_alias.c.geom_a, b_alias.c.geom_b))
    iou_expr = case(
        (union_area > 0, intersection_area / union_area),
        else_=literal_column("0.0"),
    )

    query = (
        select(
            a_alias.c.id_a,
            b_alias.c.id_b,
            a_alias.c.label_a,
            b_alias.c.label_b,
            iou_expr.label("iou"),
            func.ST_AsGeoJSON(func.ST_Union(a_alias.c.geom_a, b_alias.c.geom_b)).label("geojson"),
        )
        .select_from(a_alias)
        .join(
            b_alias,
            func.ST_Intersects(a_alias.c.geom_a, b_alias.c.geom_b),
        )
        .where(iou_expr >= iou_threshold)
        .order_by(iou_expr.desc())
    )

    result = await db.execute(query)
    rows = result.all()

    # Greedy match + filter disagreements only
    matched_a = set()
    matched_b = set()
    features = []

    for row in rows:
        id_a, id_b, label_a, label_b, iou_val, geojson_str = row
        if id_a in matched_a or id_b in matched_b:
            continue
        matched_a.add(id_a)
        matched_b.add(id_b)

        # Only include disagreements
        if label_a != label_b:
            geom = json.loads(geojson_str)
            features.append(
                {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "label_a": label_a,
                        "label_b": label_b,
                        "annotator_a": annotator_a,
                        "annotator_b": annotator_b,
                        "iou": round(float(iou_val), 4),
                    },
                }
            )

    return {
        "type": "FeatureCollection",
        "features": features,
        "annotator_a": annotator_a,
        "annotator_b": annotator_b,
        "n_disagreements": len(features),
    }


# ==========================================
# HELPERS
# ==========================================


async def _get_paired_labels(
    db: AsyncSession,
    slide_id: str,
    annotator_a: str,
    annotator_b: str,
    iou_threshold: float,
    matching_strategy: str,
    grid_cell_size: int,
    point_buffer_radius: float,
) -> tuple:
    """Get paired label lists using the specified matching strategy."""
    if matching_strategy == "iou":
        labels_a, labels_b, _, _, _ = await iou_matching(
            db,
            slide_id,
            annotator_a,
            annotator_b,
            iou_threshold=iou_threshold,
            point_buffer_radius=point_buffer_radius,
        )
    else:
        matrix, categories = await grid_matching(
            db,
            slide_id,
            [annotator_a, annotator_b],
            grid_cell_size=grid_cell_size,
            point_buffer_radius=point_buffer_radius,
        )
        labels_a = []
        labels_b = []
        for row in matrix:
            cats_in_row = []
            for idx, count in enumerate(row):
                cats_in_row.extend([categories[idx]] * count)
            if len(cats_in_row) == 2:
                labels_a.append(cats_in_row[0])
                labels_b.append(cats_in_row[1])

    return labels_a, labels_b
