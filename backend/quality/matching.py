"""
Quality Matching - Spatial annotation matching strategies.

Two strategies for pairing annotations between annotators:
1. IoU matching: PostGIS spatial intersection, greedy best-match
2. Grid matching: Divide slide into cells, majority vote per cell

Both produce paired label lists suitable for kappa/F1 computation.
"""

import logging
from typing import Dict, List, Tuple

from sqlalchemy import case, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.annotation import Annotation
from models.annotation_label import AnnotationLabel
from quality.config import DEFAULT_POINT_BUFFER_RADIUS, UNLABELED_CATEGORY

logger = logging.getLogger(__name__)


def _buffered_geom(point_buffer_radius: float):
    """Build a CASE expression that buffers points, keeps other geometries."""
    return case(
        (
            Annotation.geometry_type == "point",
            func.ST_Buffer(Annotation.geometry, point_buffer_radius),
        ),
        else_=Annotation.geometry,
    )


async def iou_matching(
    db: AsyncSession,
    slide_id: str,
    annotator_a: str,
    annotator_b: str,
    iou_threshold: float = 0.5,
    point_buffer_radius: float = DEFAULT_POINT_BUFFER_RADIUS,
) -> Tuple[List[str], List[str], int, int, List[float]]:
    """
    Match annotations between two annotators using IoU (Intersection over Union).

    Uses PostGIS ST_Intersection/ST_Union/ST_Area for server-side computation.
    Points are buffered with ST_Buffer before IoU computation.
    Greedy best-match: each annotation matched at most once.

    Args:
        db: Async database session.
        slide_id: Slide identifier.
        annotator_a: Username of annotator A.
        annotator_b: Username of annotator B.
        iou_threshold: Minimum IoU to consider a match.
        point_buffer_radius: Buffer radius for point annotations.

    Returns:
        Tuple of (labels_a, labels_b, unmatched_a_count, unmatched_b_count, iou_values)
        where labels_a[i] and labels_b[i] are the matched pair labels.
    """
    # Aliases for the two annotator sets
    a_alias = (
        select(
            Annotation.id.label("id_a"),
            _buffered_geom(point_buffer_radius).label("geom_a"),
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
            _buffered_geom(point_buffer_radius).label("geom_b"),
            func.coalesce(AnnotationLabel.name, literal_column(f"'{UNLABELED_CATEGORY}'")).label(
                "label_b"
            ),
        )
        .join(AnnotationLabel, Annotation.label_id == AnnotationLabel.id, isouter=True)
        .where(Annotation.slide_id == slide_id)
        .where(Annotation.created_by == annotator_b)
        .subquery("b")
    )

    # Cross-join with ST_Intersects filter (uses GIST index)
    intersection_area = func.ST_Area(func.ST_Intersection(a_alias.c.geom_a, b_alias.c.geom_b))
    union_area = func.ST_Area(func.ST_Union(a_alias.c.geom_a, b_alias.c.geom_b))
    # IoU = intersection / union (avoid division by zero)
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

    # Greedy best-match (rows sorted by IoU descending)
    matched_a = set()
    matched_b = set()
    labels_a = []
    labels_b = []
    iou_values = []

    for row in rows:
        id_a, id_b, label_a, label_b, iou_val = row
        if id_a in matched_a or id_b in matched_b:
            continue
        matched_a.add(id_a)
        matched_b.add(id_b)
        labels_a.append(label_a)
        labels_b.append(label_b)
        iou_values.append(float(iou_val))

    # Count unmatched annotations
    total_a = await _count_annotations(db, slide_id, annotator_a)
    total_b = await _count_annotations(db, slide_id, annotator_b)
    unmatched_a = total_a - len(matched_a)
    unmatched_b = total_b - len(matched_b)

    return labels_a, labels_b, unmatched_a, unmatched_b, iou_values


async def grid_matching(
    db: AsyncSession,
    slide_id: str,
    annotators: List[str],
    grid_cell_size: int = 256,
    point_buffer_radius: float = DEFAULT_POINT_BUFFER_RADIUS,
) -> Tuple[List[List[int]], List[str]]:
    """
    Grid-based matching for multiple annotators (Fleiss' kappa).

    Divides the slide into grid cells. For each cell, each annotator's
    label is determined by majority vote of annotations intersecting that cell.
    Cells with no annotations from any rater are excluded.

    Args:
        db: Async database session.
        slide_id: Slide identifier.
        annotators: List of annotator usernames.
        grid_cell_size: Cell size in pixels.
        point_buffer_radius: Buffer radius for points.

    Returns:
        Tuple of (rating_matrix, categories) where rating_matrix[i][j] =
        number of raters who assigned category j to cell i.
    """
    # Get slide extent from annotations
    extent_query = select(
        func.ST_XMin(func.ST_Extent(Annotation.geometry)).label("xmin"),
        func.ST_YMin(func.ST_Extent(Annotation.geometry)).label("ymin"),
        func.ST_XMax(func.ST_Extent(Annotation.geometry)).label("xmax"),
        func.ST_YMax(func.ST_Extent(Annotation.geometry)).label("ymax"),
    ).where(Annotation.slide_id == slide_id)

    extent_result = await db.execute(extent_query)
    extent = extent_result.one_or_none()

    if extent is None or extent.xmin is None:
        return [], []

    xmin, ymin, xmax, ymax = extent.xmin, extent.ymin, extent.xmax, extent.ymax

    # Generate grid cells
    n_cols = max(1, int((xmax - xmin) / grid_cell_size) + 1)
    n_rows = max(1, int((ymax - ymin) / grid_cell_size) + 1)

    # For each annotator, get label per cell via majority vote
    cell_labels: Dict[str, Dict[str, str]] = {a: {} for a in annotators}
    all_categories = set()

    for annotator in annotators:
        anno_query = (
            select(
                _buffered_geom(point_buffer_radius).label("geom"),
                func.coalesce(
                    AnnotationLabel.name, literal_column(f"'{UNLABELED_CATEGORY}'")
                ).label("label"),
            )
            .join(AnnotationLabel, Annotation.label_id == AnnotationLabel.id, isouter=True)
            .where(Annotation.slide_id == slide_id)
            .where(Annotation.created_by == annotator)
        )

        anno_result = await db.execute(anno_query)
        annotations = anno_result.all()

        for anno_geom, anno_label in annotations:
            all_categories.add(anno_label)

            bbox_query = select(
                func.ST_XMin(anno_geom).label("axmin"),
                func.ST_YMin(anno_geom).label("aymin"),
                func.ST_XMax(anno_geom).label("axmax"),
                func.ST_YMax(anno_geom).label("aymax"),
            )
            bbox_result = await db.execute(bbox_query)
            bbox = bbox_result.one()

            col_start = max(0, int((bbox.axmin - xmin) / grid_cell_size))
            col_end = min(n_cols, int((bbox.axmax - xmin) / grid_cell_size) + 1)
            row_start = max(0, int((bbox.aymin - ymin) / grid_cell_size))
            row_end = min(n_rows, int((bbox.aymax - ymin) / grid_cell_size) + 1)

            for r in range(row_start, row_end):
                for c in range(col_start, col_end):
                    cell_key = f"{r}_{c}"
                    if cell_key not in cell_labels[annotator]:
                        cell_labels[annotator][cell_key] = anno_label

    # Find cells where at least one annotator has a label
    all_cells = set()
    for annotator in annotators:
        all_cells.update(cell_labels[annotator].keys())

    if not all_cells or not all_categories:
        return [], []

    categories = sorted(all_categories)
    cat_to_idx = {c: i for i, c in enumerate(categories)}

    # Build rating matrix - only cells rated by ALL annotators
    rating_matrix = []
    for cell_key in sorted(all_cells):
        row = [0] * len(categories)
        for annotator in annotators:
            label = cell_labels[annotator].get(cell_key)
            if label:
                row[cat_to_idx[label]] += 1
        rater_count = sum(row)
        if rater_count == len(annotators):
            rating_matrix.append(row)

    return rating_matrix, categories


async def _count_annotations(db: AsyncSession, slide_id: str, annotator: str) -> int:
    """Count annotations for a specific annotator on a slide."""
    result = await db.execute(
        select(func.count(Annotation.id))
        .where(Annotation.slide_id == slide_id)
        .where(Annotation.created_by == annotator)
    )
    return result.scalar_one()
