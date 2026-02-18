"""
Measurement Service - Compute physical measurements from detected regions.
Converts pixel measurements to millimeters using slide MPP (microns per pixel).
Computes Feret diameter (max caliper diameter) for TNM staging.
"""

from typing import Dict, List, Tuple

import numpy as np
from scipy.spatial.distance import pdist


def compute_feret_diameter(contour_points: np.ndarray) -> float:
    """Compute Feret diameter (max distance between any two contour points)."""
    if len(contour_points) < 2:
        return 0.0
    distances = pdist(contour_points)
    return float(np.max(distances)) if len(distances) > 0 else 0.0


def pixels_to_mm(value_px: float, mpp: float) -> float:
    """Convert pixel measurement to millimeters. mpp = microns per pixel."""
    return value_px * mpp / 1000.0


def measure_regions(
    contours_with_confidence: List[Tuple[np.ndarray, float]],
    slide_dimensions: Tuple[int, int],
    heatmap_shape: Tuple[int, int],
    mpp: float,
) -> List[Dict]:
    """Measure all detected regions, converting to mm."""
    measurements = []
    scale_x = slide_dimensions[0] / heatmap_shape[1]
    scale_y = slide_dimensions[1] / heatmap_shape[0]

    for i, (contour, confidence) in enumerate(contours_with_confidence):
        scaled = contour.copy().astype(float)
        scaled[:, 0] *= scale_x
        scaled[:, 1] *= scale_y

        feret_px = compute_feret_diameter(scaled)
        area_px = _polygon_area(scaled)
        perimeter_px = _polygon_perimeter(scaled)

        xs, ys = scaled[:, 0], scaled[:, 1]
        bbox = [float(np.min(xs)), float(np.min(ys)), float(np.max(xs)), float(np.max(ys))]

        measurements.append(
            {
                "region_id": i,
                "label": "Tumor",
                "feret_diameter_mm": round(pixels_to_mm(feret_px, mpp), 2),
                "area_mm2": round(pixels_to_mm(area_px**0.5, mpp) ** 2, 2),
                "perimeter_mm": round(pixels_to_mm(perimeter_px, mpp), 2),
                "bbox_mm": [round(pixels_to_mm(v, mpp), 2) for v in bbox],
                "confidence": round(confidence, 4),
            }
        )

    return measurements


def _polygon_area(points: np.ndarray) -> float:
    n = len(points)
    if n < 3:
        return 0.0
    x, y = points[:, 0], points[:, 1]
    return abs(float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]) + x[-1] * y[0] - x[0] * y[-1])) / 2.0


def _polygon_perimeter(points: np.ndarray) -> float:
    if len(points) < 2:
        return 0.0
    diffs = np.diff(points, axis=0, append=points[:1])
    return float(np.sum(np.sqrt(np.sum(diffs**2, axis=1))))
