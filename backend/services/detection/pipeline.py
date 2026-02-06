"""
Detection Pipeline - Full heatmap-to-GeoJSON conversion

Orchestrates the full detection pipeline:
    Heatmap → threshold → contours → simplify → scale → GeoJSON

Returns a GeoJSON FeatureCollection with detected regions,
each annotated with confidence, area, centroid, and bbox.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from schemas.geojson import GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONGeometry

from .postprocessing import (
    contour_to_geojson_coords,
    heatmap_to_contours,
    scale_contours,
    simplify_contour,
)


def detect_regions(
    heatmap: np.ndarray,
    slide_dimensions: Tuple[int, int],
    threshold: float = 0.5,
    min_area: float = 100.0,
    simplify_tolerance: float = 2.0,
    closing_iterations: int = 2,
) -> GeoJSONFeatureCollection:
    """
    Full detection pipeline: heatmap → GeoJSON FeatureCollection.

    Args:
        heatmap: 2D float array [0, 1], shape (H, W)
        slide_dimensions: (width, height) of slide at level 0
        threshold: Confidence threshold for region detection
        min_area: Minimum area in heatmap pixels
        simplify_tolerance: Douglas-Peucker tolerance (in heatmap pixels)
        closing_iterations: Morphological closing passes

    Returns:
        GeoJSONFeatureCollection with detected polygon features
    """
    # Step 1: Heatmap → contours
    contours_with_confidence = heatmap_to_contours(
        heatmap,
        threshold=threshold,
        min_area=min_area,
        closing_iterations=closing_iterations,
    )

    if not contours_with_confidence:
        return GeoJSONFeatureCollection(features=[], metadata={"num_regions": 0})

    heatmap_shape = heatmap.shape

    features: List[GeoJSONFeature] = []

    for i, (contour, confidence) in enumerate(contours_with_confidence):
        # Step 2: Simplify in heatmap space
        simplified = simplify_contour(contour, tolerance=simplify_tolerance)

        if len(simplified) < 3:
            continue

        # Step 3: Scale to slide coordinates
        scaled = scale_contours(simplified, heatmap_shape, slide_dimensions)

        # Step 4: Compute region properties in slide space
        xs = scaled[:, 0]
        ys = scaled[:, 1]
        centroid_x = float(np.mean(xs))
        centroid_y = float(np.mean(ys))
        bbox = [float(np.min(xs)), float(np.min(ys)), float(np.max(xs)), float(np.max(ys))]

        # Area using shoelace formula
        area = _polygon_area(scaled)

        # Step 5: Convert to GeoJSON
        geojson_coords = contour_to_geojson_coords(scaled)

        feature = GeoJSONFeature(
            type="Feature",
            id=f"detection_{i}",
            geometry=GeoJSONGeometry(type="Polygon", coordinates=geojson_coords),
            properties={
                "confidence": round(confidence, 4),
                "area_px": round(area, 2),
                "centroid": [round(centroid_x, 2), round(centroid_y, 2)],
                "bbox": [round(v, 2) for v in bbox],
                "detection_index": i,
            },
        )
        features.append(feature)

    return GeoJSONFeatureCollection(
        features=features,
        metadata={"num_regions": len(features)},
    )


def _polygon_area(points: np.ndarray) -> float:
    """Compute polygon area using the shoelace formula."""
    n = len(points)
    if n < 3:
        return 0.0
    x = points[:, 0]
    y = points[:, 1]
    return abs(float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]) + x[-1] * y[0] - x[0] * y[-1])) / 2.0
