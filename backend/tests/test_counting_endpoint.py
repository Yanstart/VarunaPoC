"""
Tests for Cell Counting Service and Endpoint

Tests the CellCountingService mock mode and verifies
response shape matches issue #81 spec.

Markers: @pytest.mark.counting, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from services.ml.counting import CellCountingService, CellCountResult


@pytest.mark.counting
@pytest.mark.unit
class TestCellCountingService:
    """Test CellCountingService in mock mode."""

    def setup_method(self):
        self.service = CellCountingService()

    def test_mock_returns_cell_count_result(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert isinstance(result, CellCountResult)

    def test_mock_response_shape(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert hasattr(result, "total_cells")
        assert hasattr(result, "positive")
        assert hasattr(result, "negative")
        assert hasattr(result, "ratio")
        assert hasattr(result, "percentage")
        assert hasattr(result, "processing_time_ms")

    def test_mock_total_equals_positive_plus_negative(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert result.total_cells == result.positive + result.negative

    def test_mock_ratio_in_valid_range(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert 0.0 <= result.ratio <= 1.0

    def test_mock_ratio_matches_counts(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        expected = round(result.positive / result.total_cells, 4)
        assert result.ratio == expected

    def test_mock_percentage_format(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert result.percentage.endswith("%")
        # Should be parseable as float
        float(result.percentage.rstrip("%"))

    def test_mock_total_cells_in_realistic_range(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert 800 <= result.total_cells <= 2500

    def test_mock_ki67_ratio_in_breast_cancer_range(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert 0.05 <= result.ratio <= 0.40

    def test_mock_is_deterministic(self):
        """Same slide path should always produce same counts."""
        r1 = self.service.count_cells("/slides/test_slide.svs")
        r2 = self.service.count_cells("/slides/test_slide.svs")
        assert r1.total_cells == r2.total_cells
        assert r1.positive == r2.positive
        assert r1.negative == r2.negative

    def test_mock_different_slides_produce_different_counts(self):
        r1 = self.service.count_cells("/slides/slide_A.svs")
        r2 = self.service.count_cells("/slides/slide_B.svs")
        # Very unlikely to be identical for different paths
        assert r1.total_cells != r2.total_cells or r1.positive != r2.positive

    def test_default_stain_is_ki67(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert result.metadata.get("stain") == "Ki67"

    def test_custom_stain(self):
        result = self.service.count_cells("/slides/test_slide.svs", stain="HER2")
        assert result.metadata.get("stain") == "HER2"

    def test_mock_mode_metadata(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert result.metadata.get("mode") == "mock"

    def test_processing_time_is_positive(self):
        result = self.service.count_cells("/slides/test_slide.svs")
        assert result.processing_time_ms >= 0
