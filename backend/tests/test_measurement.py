"""Tests for measurement service."""

import numpy as np

from services.measurement import compute_feret_diameter, measure_regions, pixels_to_mm


class TestFeretDiameter:
    def test_square(self):
        points = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=float)
        feret = compute_feret_diameter(points)
        expected = np.sqrt(200)  # diagonal
        assert abs(feret - expected) < 0.01

    def test_single_point(self):
        assert compute_feret_diameter(np.array([[5, 5]])) == 0.0

    def test_two_points(self):
        points = np.array([[0, 0], [3, 4]], dtype=float)
        assert abs(compute_feret_diameter(points) - 5.0) < 0.01


class TestPixelsToMm:
    def test_basic(self):
        assert abs(pixels_to_mm(1000, 0.25) - 0.25) < 0.001

    def test_zero(self):
        assert pixels_to_mm(0, 0.25) == 0.0


class TestMeasureRegions:
    def test_basic(self):
        contour = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=float)
        result = measure_regions(
            [(contour, 0.9)],
            slide_dimensions=(1000, 1000),
            heatmap_shape=(100, 100),
            mpp=0.25,
        )
        assert len(result) == 1
        assert result[0]["region_id"] == 0
        assert result[0]["feret_diameter_mm"] > 0
        assert result[0]["confidence"] == 0.9
