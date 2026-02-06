"""
Tests for Detection Pipeline - Heatmap to GeoJSON conversion

Uses synthetic heatmaps (no ML or DB required).

Markers: @pytest.mark.detection, @pytest.mark.unit
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.detection.pipeline import detect_regions
from services.detection.postprocessing import (
    contour_to_geojson_coords,
    heatmap_to_contours,
    scale_contours,
    simplify_contour,
)


def _make_blob_heatmap(h=100, w=100, cx=50, cy=50, radius=15, value=0.8):
    """Create a heatmap with a single circular blob."""
    heatmap = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if dist < radius:
                heatmap[y, x] = value * (1 - dist / radius)
    return heatmap


def _make_multi_blob_heatmap():
    """Create a heatmap with multiple blobs."""
    heatmap = np.zeros((200, 200), dtype=np.float32)
    # Blob 1: top-left
    heatmap = _add_blob(heatmap, 40, 40, 20, 0.9)
    # Blob 2: bottom-right
    heatmap = _add_blob(heatmap, 160, 160, 15, 0.7)
    # Blob 3: small, below threshold
    return _add_blob(heatmap, 100, 100, 5, 0.3)


def _add_blob(heatmap, cx, cy, radius, value):
    h, w = heatmap.shape
    for y in range(max(0, cy - radius), min(h, cy + radius)):
        for x in range(max(0, cx - radius), min(w, cx + radius)):
            dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if dist < radius:
                heatmap[y, x] = max(heatmap[y, x], value * (1 - dist / radius))
    return heatmap


@pytest.mark.detection
@pytest.mark.unit
class TestHeatmapToContours:
    def test_single_blob_detected(self):
        heatmap = _make_blob_heatmap()
        contours = heatmap_to_contours(heatmap, threshold=0.3, min_area=10)
        assert len(contours) == 1
        points, confidence = contours[0]
        assert points.shape[1] == 2  # Nx2
        assert 0 < confidence <= 1.0

    def test_empty_heatmap_no_contours(self):
        heatmap = np.zeros((100, 100), dtype=np.float32)
        contours = heatmap_to_contours(heatmap, threshold=0.5)
        assert len(contours) == 0

    def test_full_heatmap_one_contour(self):
        heatmap = np.ones((50, 50), dtype=np.float32) * 0.8
        contours = heatmap_to_contours(heatmap, threshold=0.5, min_area=10)
        assert len(contours) >= 1

    def test_threshold_filters_low_values(self):
        heatmap = _make_blob_heatmap(value=0.4)
        contours_low = heatmap_to_contours(heatmap, threshold=0.1, min_area=5)
        contours_high = heatmap_to_contours(heatmap, threshold=0.35, min_area=5)
        # High threshold should find fewer/smaller regions
        assert len(contours_high) <= len(contours_low)

    def test_min_area_filters_small_regions(self):
        heatmap = _make_blob_heatmap(radius=3, value=0.9)
        contours_small = heatmap_to_contours(heatmap, threshold=0.3, min_area=1)
        contours_large = heatmap_to_contours(heatmap, threshold=0.3, min_area=500)
        assert len(contours_large) <= len(contours_small)

    def test_multi_blob_detection(self):
        heatmap = _make_multi_blob_heatmap()
        contours = heatmap_to_contours(heatmap, threshold=0.3, min_area=10)
        # Should detect at least the 2 large blobs (3rd is below threshold center)
        assert len(contours) >= 2


@pytest.mark.detection
@pytest.mark.unit
class TestSimplifyContour:
    def test_simplify_reduces_points(self):
        # Generate a circle with many points
        t = np.linspace(0, 2 * np.pi, 100)
        contour = np.column_stack([50 + 20 * np.cos(t), 50 + 20 * np.sin(t)])
        simplified = simplify_contour(contour, tolerance=2.0)
        assert len(simplified) < len(contour)
        assert len(simplified) >= 4  # At least a quad

    def test_no_simplification_at_zero_tolerance(self):
        contour = np.array([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]], dtype=float)
        simplified = simplify_contour(contour, tolerance=0)
        assert len(simplified) == len(contour)

    def test_short_contour_unchanged(self):
        contour = np.array([[0, 0], [10, 0], [5, 10]], dtype=float)
        simplified = simplify_contour(contour, tolerance=5.0)
        assert len(simplified) >= 3


@pytest.mark.detection
@pytest.mark.unit
class TestScaleContours:
    def test_scale_doubles_coordinates(self):
        contour = np.array([[10, 20], [30, 40]], dtype=float)
        scaled = scale_contours(contour, heatmap_shape=(100, 100), slide_dimensions=(200, 200))
        np.testing.assert_allclose(scaled, [[20, 40], [60, 80]])

    def test_scale_asymmetric(self):
        contour = np.array([[50, 50]], dtype=float)
        scaled = scale_contours(contour, heatmap_shape=(100, 200), slide_dimensions=(400, 300))
        # x scale: 400/200=2, y scale: 300/100=3
        np.testing.assert_allclose(scaled, [[100, 150]])


@pytest.mark.detection
@pytest.mark.unit
class TestContourToGeoJSON:
    def test_output_is_closed_ring(self):
        contour = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=float)
        coords = contour_to_geojson_coords(contour)
        # GeoJSON Polygon: [ring], ring is [[x,y], ...]
        assert len(coords) == 1
        ring = coords[0]
        assert ring[0] == ring[-1]  # closed

    def test_already_closed_not_duplicated(self):
        contour = np.array([[0, 0], [10, 0], [10, 10], [0, 0]], dtype=float)
        coords = contour_to_geojson_coords(contour)
        ring = coords[0]
        assert ring[0] == ring[-1]
        assert len(ring) == 4  # 3 unique + closing


@pytest.mark.detection
@pytest.mark.unit
class TestDetectRegions:
    def test_full_pipeline_returns_feature_collection(self):
        heatmap = _make_blob_heatmap()
        result = detect_regions(heatmap, slide_dimensions=(10000, 8000), threshold=0.3, min_area=10)
        assert result.type == "FeatureCollection"
        assert len(result.features) >= 1

    def test_features_have_required_properties(self):
        heatmap = _make_blob_heatmap()
        result = detect_regions(heatmap, slide_dimensions=(10000, 8000), threshold=0.3, min_area=10)
        for feature in result.features:
            assert feature.type == "Feature"
            assert feature.geometry.type == "Polygon"
            assert "confidence" in feature.properties
            assert "area_px" in feature.properties
            assert "centroid" in feature.properties
            assert "bbox" in feature.properties
            assert 0 <= feature.properties["confidence"] <= 1.0

    def test_empty_heatmap_returns_empty_collection(self):
        heatmap = np.zeros((100, 100), dtype=np.float32)
        result = detect_regions(heatmap, slide_dimensions=(10000, 8000))
        assert len(result.features) == 0

    def test_coordinates_scaled_to_slide(self):
        heatmap = _make_blob_heatmap(h=100, w=100, cx=50, cy=50, radius=20, value=0.9)
        result = detect_regions(heatmap, slide_dimensions=(10000, 8000), threshold=0.3, min_area=5)
        assert len(result.features) >= 1
        # Check that coordinates are in slide space (>> heatmap space)
        feature = result.features[0]
        centroid = feature.properties["centroid"]
        assert centroid[0] > 100  # Should be scaled from ~50 to ~5000
        assert centroid[1] > 100

    def test_metadata_included(self):
        heatmap = _make_blob_heatmap()
        result = detect_regions(heatmap, slide_dimensions=(10000, 8000))
        assert result.metadata is not None
        assert "num_regions" in result.metadata
