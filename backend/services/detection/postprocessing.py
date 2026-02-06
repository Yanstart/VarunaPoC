"""
Detection Postprocessing - Heatmap to contours conversion

Converts a 2D float heatmap [0,1] into simplified polygon contours
using morphological operations and marching squares.

Pipeline:
    heatmap → threshold → binary_closing → label → find_contours
    → filter min_area → simplify Douglas-Peucker → scale to slide coords
"""

from typing import List, Tuple

import numpy as np


def heatmap_to_contours(
    heatmap: np.ndarray,
    threshold: float = 0.5,
    min_area: float = 100.0,
    closing_iterations: int = 2,
) -> List[Tuple[np.ndarray, float]]:
    """
    Convert a heatmap to polygon contours with confidence scores.

    Args:
        heatmap: 2D array of float values in [0, 1]
        threshold: Binary threshold for region detection
        min_area: Minimum region area in heatmap pixels
        closing_iterations: Morphological closing iterations

    Returns:
        List of (contour_points, mean_confidence) tuples.
        contour_points: Nx2 array of (x, y) coordinates in heatmap space.
    """
    from scipy import ndimage
    from skimage.measure import find_contours, label, regionprops

    # Threshold
    binary = (heatmap >= threshold).astype(np.uint8)

    # Morphological closing to fill small gaps
    if closing_iterations > 0:
        struct = ndimage.generate_binary_structure(2, 2)
        binary = ndimage.binary_closing(binary, structure=struct, iterations=closing_iterations)
        binary = binary.astype(np.uint8)

    # Label connected components
    labeled, num_features = label(binary, return_num=True)

    if num_features == 0:
        return []

    # Process each region
    results = []
    regions = regionprops(labeled, intensity_image=heatmap)

    for region in regions:
        # Filter by area
        if region.area < min_area:
            continue

        # Mean confidence within the region
        mean_confidence = float(region.mean_intensity)

        # Find contour for this specific label
        region_mask = (labeled == region.label).astype(float)
        contours = find_contours(region_mask, 0.5)

        if not contours:
            continue

        # Take the longest contour (outer boundary)
        contour = max(contours, key=len)

        # find_contours returns (row, col) → convert to (x, y) = (col, row)
        contour_xy = contour[:, ::-1].copy()

        results.append((contour_xy, mean_confidence))

    return results


def simplify_contour(contour: np.ndarray, tolerance: float = 2.0) -> np.ndarray:
    """
    Simplify a contour using Douglas-Peucker algorithm.

    Args:
        contour: Nx2 array of (x, y) points
        tolerance: Simplification tolerance in pixels

    Returns:
        Simplified Mx2 array (M <= N)
    """
    if tolerance <= 0 or len(contour) < 4:
        return contour

    from shapely.geometry import Polygon

    # Close the contour if not already closed
    if not np.array_equal(contour[0], contour[-1]):
        contour = np.vstack([contour, contour[0]])

    try:
        poly = Polygon(contour)
        simplified = poly.simplify(tolerance, preserve_topology=True)
        return np.array(simplified.exterior.coords)
    except Exception:
        return contour


def scale_contours(
    contour: np.ndarray,
    heatmap_shape: Tuple[int, int],
    slide_dimensions: Tuple[int, int],
) -> np.ndarray:
    """
    Scale contour coordinates from heatmap space to slide level-0 pixels.

    Args:
        contour: Nx2 array in heatmap pixel coordinates
        heatmap_shape: (height, width) of heatmap
        slide_dimensions: (width, height) of slide at level 0

    Returns:
        Nx2 array in slide pixel coordinates
    """
    h_h, h_w = heatmap_shape
    s_w, s_h = slide_dimensions

    scale_x = s_w / h_w
    scale_y = s_h / h_h

    scaled = contour.copy().astype(float)
    scaled[:, 0] *= scale_x
    scaled[:, 1] *= scale_y

    return scaled


def contour_to_geojson_coords(contour: np.ndarray) -> List[List[List[float]]]:
    """
    Convert an Nx2 contour to GeoJSON Polygon coordinates.

    GeoJSON Polygon: [[[x1,y1], [x2,y2], ..., [x1,y1]]]
    The outer ring must be closed (first point == last point).
    """
    points = contour.tolist()

    # Close the ring if needed
    if points[0] != points[-1]:
        points.append(points[0])

    # GeoJSON Polygon = array of rings, first is outer ring
    return [points]
