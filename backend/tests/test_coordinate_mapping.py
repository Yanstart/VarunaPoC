"""
Tests for Coordinate Mapping - Round-trip precision

Verifies that coordinates survive the transformation:
    slide_px → heatmap_px → scaled_back → slide_px

Precision requirement: < 1px error after round-trip.

Markers: @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest

from services.detection.postprocessing import scale_contours


@pytest.mark.unit
class TestCoordinateMapping:
    """Round-trip coordinate mapping precision tests."""

    def test_roundtrip_identity(self):
        """Scaling then inverse scaling should return original coords."""
        original = np.array([[500, 400], [1500, 1200], [2500, 2000]], dtype=float)
        heatmap_shape = (100, 100)
        slide_dims = (5000, 4000)

        # Forward: heatmap → slide
        scaled = scale_contours(original, heatmap_shape, slide_dims)

        # Inverse: slide → heatmap
        inverse_scale_x = heatmap_shape[1] / slide_dims[0]
        inverse_scale_y = heatmap_shape[0] / slide_dims[1]
        back = scaled.copy()
        back[:, 0] *= inverse_scale_x
        back[:, 1] *= inverse_scale_y

        np.testing.assert_allclose(back, original, atol=0.01)

    def test_scale_preserves_relative_positions(self):
        """Points that are left of others should remain left after scaling."""
        contour = np.array([[10, 20], [50, 20], [30, 60]], dtype=float)
        scaled = scale_contours(contour, (100, 100), (10000, 8000))

        # Relative ordering should be preserved
        assert scaled[0, 0] < scaled[1, 0]  # first point is left of second
        assert scaled[0, 1] < scaled[2, 1]  # first point is above third

    def test_precision_at_large_scale(self):
        """Test precision with typical WSI dimensions (100k x 80k)."""
        slide_dims = (100000, 80000)
        heatmap_shape = (200, 250)

        # Points at known positions in heatmap
        heatmap_point = np.array([[125, 100]], dtype=float)
        expected_slide = np.array(
            [
                [
                    125 * (slide_dims[0] / heatmap_shape[1]),
                    100 * (slide_dims[1] / heatmap_shape[0]),
                ],
            ]
        )

        scaled = scale_contours(heatmap_point, heatmap_shape, slide_dims)
        np.testing.assert_allclose(scaled, expected_slide, atol=0.5)

    def test_origin_maps_to_origin(self):
        """Point (0,0) in heatmap should map to (0,0) in slide."""
        point = np.array([[0, 0]], dtype=float)
        scaled = scale_contours(point, (100, 100), (50000, 40000))
        np.testing.assert_allclose(scaled, [[0, 0]])

    def test_corner_maps_to_corner(self):
        """Bottom-right corner of heatmap should map to bottom-right of slide."""
        heatmap_shape = (100, 100)
        slide_dims = (50000, 40000)
        point = np.array([[99.0, 99.0]], dtype=float)
        scaled = scale_contours(point, heatmap_shape, slide_dims)

        # Should be close to (49500, 39600) = 99 * (50000/100), 99 * (40000/100)
        expected = np.array([[49500.0, 39600.0]])
        np.testing.assert_allclose(scaled, expected, atol=1.0)

    def test_various_heatmap_resolutions(self):
        """Test with different heatmap resolutions (level 0, 1, 2, 3)."""
        slide_dims = (100000, 80000)

        for level, (h, w) in enumerate([(800, 1000), (400, 500), (200, 250), (100, 125)]):
            center = np.array([[w / 2, h / 2]], dtype=float)
            scaled = scale_contours(center, (h, w), slide_dims)

            # Center of heatmap should map to center of slide
            expected = np.array([[slide_dims[0] / 2, slide_dims[1] / 2]])
            np.testing.assert_allclose(
                scaled,
                expected,
                atol=slide_dims[0] / w,
                err_msg=f"Failed at level {level} (heatmap {w}x{h})",
            )

    def test_sub_pixel_precision(self):
        """Coordinates with fractional parts should be preserved."""
        point = np.array([[25.5, 33.7]], dtype=float)
        scaled = scale_contours(point, (100, 100), (10000, 8000))
        # 25.5 * 100 = 2550, 33.7 * 80 = 2696
        np.testing.assert_allclose(scaled, [[2550.0, 2696.0]], atol=0.01)
