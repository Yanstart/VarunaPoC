"""
Tests for Detection API Endpoint - Uses MockProvider

Tests the POST /api/ml/detect/{slide_id} endpoint
with a mock ML provider (no real model required).

Markers: @pytest.mark.detection, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock

import numpy as np
import pytest

from schemas.geojson import GeoJSONFeatureCollection
from services.detection.pipeline import detect_regions


@pytest.mark.detection
@pytest.mark.unit
class TestDetectionEndpoint:
    """Test the detection pipeline as called by the endpoint."""

    def _make_mock_heatmap_result(self):
        """Create a mock HeatmapResult like the ML provider returns."""
        result = MagicMock()
        # Create a synthetic heatmap with a blob
        heatmap = np.zeros((100, 100), dtype=np.float32)
        for y in range(30, 70):
            for x in range(30, 70):
                dist = np.sqrt((x - 50) ** 2 + (y - 50) ** 2)
                if dist < 20:
                    heatmap[y, x] = 0.8 * (1 - dist / 20)

        result.heatmap = heatmap
        result.slide_dimensions = (50000, 40000)
        result.resolution_level = 2
        result.method = "feature_attention"
        result.metadata = {}
        return result

    def test_detect_regions_from_mock_heatmap(self):
        mock_result = self._make_mock_heatmap_result()

        geojson = detect_regions(
            heatmap=mock_result.heatmap,
            slide_dimensions=mock_result.slide_dimensions,
            threshold=0.3,
            min_area=10,
        )

        assert isinstance(geojson, GeoJSONFeatureCollection)
        assert len(geojson.features) >= 1
        assert geojson.features[0].geometry.type == "Polygon"

    def test_detection_respects_threshold(self):
        mock_result = self._make_mock_heatmap_result()

        # Low threshold → more regions
        result_low = detect_regions(
            heatmap=mock_result.heatmap,
            slide_dimensions=mock_result.slide_dimensions,
            threshold=0.1,
            min_area=5,
        )

        # High threshold → fewer regions
        result_high = detect_regions(
            heatmap=mock_result.heatmap,
            slide_dimensions=mock_result.slide_dimensions,
            threshold=0.7,
            min_area=5,
        )

        assert len(result_high.features) <= len(result_low.features)

    def test_detection_output_format(self):
        mock_result = self._make_mock_heatmap_result()

        geojson = detect_regions(
            heatmap=mock_result.heatmap,
            slide_dimensions=mock_result.slide_dimensions,
            threshold=0.3,
            min_area=10,
        )

        for feature in geojson.features:
            # Required properties
            assert "confidence" in feature.properties
            assert "area_px" in feature.properties
            assert "centroid" in feature.properties
            assert "bbox" in feature.properties

            # Confidence range
            assert 0 <= feature.properties["confidence"] <= 1.0

            centroid = feature.properties["centroid"]
            assert len(centroid) == 2

            bbox = feature.properties["bbox"]
            assert len(bbox) == 4
            assert bbox[0] <= bbox[2]  # x1 <= x2
            assert bbox[1] <= bbox[3]  # y1 <= y2

    def test_detection_coordinates_in_slide_space(self):
        mock_result = self._make_mock_heatmap_result()
        slide_w, slide_h = mock_result.slide_dimensions

        geojson = detect_regions(
            heatmap=mock_result.heatmap,
            slide_dimensions=mock_result.slide_dimensions,
            threshold=0.3,
            min_area=10,
        )

        for feature in geojson.features:
            centroid = feature.properties["centroid"]
            # Centroid should be within slide dimensions
            assert 0 <= centroid[0] <= slide_w
            assert 0 <= centroid[1] <= slide_h

    def test_empty_heatmap_returns_zero_regions(self):
        heatmap = np.zeros((100, 100), dtype=np.float32)
        geojson = detect_regions(
            heatmap=heatmap,
            slide_dimensions=(10000, 8000),
        )
        assert len(geojson.features) == 0
