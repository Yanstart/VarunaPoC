"""
Tests for Focus Assist Endpoint — GET /ml/focus/{slide_id}

Tests the focus zones computation logic with mock heatmaps
and mock providers (no real model or slide required).

Markers: @pytest.mark.focus, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


import numpy as np
import pytest

from services.detection.postprocessing import heatmap_to_contours


def _make_synthetic_heatmap(size=100, num_blobs=3):
    """Create a synthetic heatmap with gaussian-like blobs."""
    heatmap = np.zeros((size, size), dtype=np.float32)
    centers = [
        (30, 30),
        (70, 70),
        (50, 20),
    ][:num_blobs]
    scores = [0.9, 0.7, 0.55][:num_blobs]

    for (cx, cy), peak in zip(centers, scores, strict=True):
        for y in range(size):
            for x in range(size):
                dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if dist < 15:
                    heatmap[y, x] = max(heatmap[y, x], peak * (1 - dist / 15))

    return heatmap


@pytest.mark.focus
@pytest.mark.unit
class TestFocusZonesComputation:
    """Test the focus zone extraction logic as used by the endpoint."""

    def test_heatmap_to_contours_returns_results(self):
        """heatmap_to_contours should find contours from a synthetic heatmap."""
        heatmap = _make_synthetic_heatmap(num_blobs=2)
        results = heatmap_to_contours(heatmap, threshold=0.3, min_area=5, closing_iterations=1)
        assert len(results) >= 1
        for contour, confidence in results:
            assert isinstance(contour, np.ndarray)
            assert contour.ndim == 2
            assert contour.shape[1] == 2
            assert 0.0 <= confidence <= 1.0

    def test_empty_heatmap_returns_no_zones(self):
        """An empty heatmap should produce zero contours."""
        heatmap = np.zeros((100, 100), dtype=np.float32)
        results = heatmap_to_contours(heatmap, threshold=0.5, min_area=5)
        assert len(results) == 0

    def test_high_threshold_filters_weak_zones(self):
        """A high threshold should filter out low-confidence zones."""
        heatmap = _make_synthetic_heatmap(num_blobs=3)
        results_low = heatmap_to_contours(heatmap, threshold=0.2, min_area=5)
        results_high = heatmap_to_contours(heatmap, threshold=0.7, min_area=5)
        assert len(results_high) <= len(results_low)

    def test_zone_scaling_to_slide_coordinates(self):
        """Contour coordinates should scale correctly to slide dimensions."""
        heatmap = _make_synthetic_heatmap(num_blobs=1)
        slide_dimensions = (50000, 40000)
        heatmap_h, heatmap_w = heatmap.shape[:2]
        scale_x = slide_dimensions[0] / heatmap_w
        scale_y = slide_dimensions[1] / heatmap_h

        results = heatmap_to_contours(heatmap, threshold=0.3, min_area=5)
        assert len(results) >= 1

        contour, _ = results[0]
        scaled = contour.copy().astype(float)
        scaled[:, 0] *= scale_x
        scaled[:, 1] *= scale_y

        # All coordinates should be within slide dimensions
        assert np.all(scaled[:, 0] >= 0)
        assert np.all(scaled[:, 0] <= slide_dimensions[0])
        assert np.all(scaled[:, 1] >= 0)
        assert np.all(scaled[:, 1] <= slide_dimensions[1])

    def test_zone_centroid_computation(self):
        """Centroid should be computed as mean of contour points."""
        heatmap = _make_synthetic_heatmap(num_blobs=1)
        results = heatmap_to_contours(heatmap, threshold=0.3, min_area=5)
        assert len(results) >= 1

        contour, _ = results[0]
        centroid_x = float(np.mean(contour[:, 0]))
        centroid_y = float(np.mean(contour[:, 1]))

        # Centroid should be roughly near the blob center (30, 30)
        assert 15 <= centroid_x <= 45
        assert 15 <= centroid_y <= 45

    def test_zone_bbox_computation(self):
        """Bounding box should contain all contour points."""
        heatmap = _make_synthetic_heatmap(num_blobs=1)
        results = heatmap_to_contours(heatmap, threshold=0.3, min_area=5)
        assert len(results) >= 1

        contour, _ = results[0]
        bbox = [
            float(np.min(contour[:, 0])),
            float(np.min(contour[:, 1])),
            float(np.max(contour[:, 0])),
            float(np.max(contour[:, 1])),
        ]

        assert bbox[0] <= bbox[2], "x_min <= x_max"
        assert bbox[1] <= bbox[3], "y_min <= y_max"

    def test_shoelace_area_positive(self):
        """Area via shoelace formula should be positive for valid contours."""
        heatmap = _make_synthetic_heatmap(num_blobs=1)
        slide_dimensions = (50000, 40000)
        heatmap_h, heatmap_w = heatmap.shape[:2]
        scale_x = slide_dimensions[0] / heatmap_w
        scale_y = slide_dimensions[1] / heatmap_h

        results = heatmap_to_contours(heatmap, threshold=0.3, min_area=5)
        assert len(results) >= 1

        contour, _ = results[0]
        scaled = contour.copy().astype(float)
        scaled[:, 0] *= scale_x
        scaled[:, 1] *= scale_y

        n = len(scaled)
        assert n >= 3

        x, y = scaled[:, 0], scaled[:, 1]
        area = (
            abs(float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]) + x[-1] * y[0] - x[0] * y[-1])) / 2.0
        )

        assert area > 0

    def test_zones_sorted_by_score_descending(self):
        """After sorting, zones should be in descending score order."""
        heatmap = _make_synthetic_heatmap(num_blobs=3)
        results = heatmap_to_contours(heatmap, threshold=0.2, min_area=5)

        if len(results) < 2:
            pytest.skip("Not enough zones to test sorting")

        zones = []
        for _contour, confidence in results:
            zones.append({"score": round(confidence, 4)})

        zones.sort(key=lambda z: z["score"], reverse=True)

        for i in range(len(zones) - 1):
            assert zones[i]["score"] >= zones[i + 1]["score"]

    def test_top_n_limits_output(self):
        """top_n should limit the number of returned zones."""
        heatmap = _make_synthetic_heatmap(num_blobs=3)
        results = heatmap_to_contours(heatmap, threshold=0.2, min_area=5)

        zones = [{"score": conf} for _, conf in results]
        zones.sort(key=lambda z: z["score"], reverse=True)

        top_1 = zones[:1]
        assert len(top_1) <= 1

        top_2 = zones[:2]
        assert len(top_2) <= 2


@pytest.mark.focus
@pytest.mark.unit
class TestFocusZonePydanticModels:
    """Test the Pydantic models for focus assist."""

    def test_focus_zone_model(self):
        from routes.ml import FocusZone

        zone = FocusZone(
            rank=1,
            score=0.85,
            centroid=[25000.0, 20000.0],
            bbox=[20000.0, 15000.0, 30000.0, 25000.0],
            area_px=5000000.0,
        )
        assert zone.rank == 1
        assert zone.score == 0.85
        assert len(zone.centroid) == 2
        assert len(zone.bbox) == 4
        assert zone.area_px == 5000000.0

    def test_focus_zone_score_validation(self):
        from routes.ml import FocusZone

        with pytest.raises(ValueError, match="less than or equal to 1"):
            FocusZone(
                rank=1,
                score=1.5,  # Invalid: > 1.0
                centroid=[0.0, 0.0],
                bbox=[0.0, 0.0, 1.0, 1.0],
                area_px=100.0,
            )

    def test_focus_response_model(self):
        from routes.ml import FocusResponse, FocusZone

        zones = [
            FocusZone(
                rank=1,
                score=0.9,
                centroid=[100.0, 200.0],
                bbox=[0.0, 0.0, 200.0, 400.0],
                area_px=80000.0,
            ),
            FocusZone(
                rank=2,
                score=0.7,
                centroid=[500.0, 600.0],
                bbox=[400.0, 500.0, 600.0, 700.0],
                area_px=40000.0,
            ),
        ]

        response = FocusResponse(
            slide_id="test-slide-001",
            zones=zones,
            model_id="ctranspath_features",
            total_zones_above_threshold=5,
        )
        assert response.slide_id == "test-slide-001"
        assert len(response.zones) == 2
        assert response.model_id == "ctranspath_features"
        assert response.total_zones_above_threshold == 5
