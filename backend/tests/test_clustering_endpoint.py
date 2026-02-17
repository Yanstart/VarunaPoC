"""
Tests for Clustering Service

Tests the ClusteringService mock mode and verifies
response shape matches the clustering plan spec.

Markers: @pytest.mark.clustering, @pytest.mark.unit
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from services.ml.clustering import ClusteringService, ClusterResult


@pytest.mark.clustering
@pytest.mark.unit
class TestClusteringService:
    """Test ClusteringService in mock mode."""

    def setup_method(self):
        self.service = ClusteringService()

    def test_returns_cluster_result(self):
        result = self.service.cluster("/slides/test_slide.svs")
        assert isinstance(result, ClusterResult)

    def test_default_4_clusters(self):
        result = self.service.cluster("/slides/test_slide.svs")
        assert len(result.clusters) == 4

    def test_custom_n_clusters(self):
        result = self.service.cluster("/slides/test_slide.svs", n_clusters=6)
        assert len(result.clusters) == 6

    def test_sequential_cluster_ids(self):
        result = self.service.cluster("/slides/test_slide.svs")
        ids = [c.id for c in result.clusters]
        assert ids == list(range(len(result.clusters)))

    def test_clusters_have_colors(self):
        result = self.service.cluster("/slides/test_slide.svs")
        hex_pattern = re.compile(r"^#[0-9a-fA-F]{6}$")
        for c in result.clusters:
            assert hex_pattern.match(c.color), f"Invalid color: {c.color}"

    def test_clusters_have_labels(self):
        result = self.service.cluster("/slides/test_slide.svs")
        expected_labels = [f"Cluster {chr(ord('A') + i)}" for i in range(len(result.clusters))]
        actual_labels = [c.label for c in result.clusters]
        assert actual_labels == expected_labels

    def test_tile_counts_sum_to_total_assignments(self):
        result = self.service.cluster("/slides/test_slide.svs")
        total_from_clusters = sum(c.tile_count for c in result.clusters)
        assert total_from_clusters == len(result.tile_assignments)

    def test_8x8_grid_64_tiles(self):
        result = self.service.cluster("/slides/test_slide.svs")
        assert len(result.tile_assignments) == 64

    def test_valid_cluster_ids_in_range(self):
        result = self.service.cluster("/slides/test_slide.svs", n_clusters=5)
        for t in result.tile_assignments:
            assert 0 <= t.cluster_id < 5

    def test_deterministic_same_path(self):
        """Same slide path should always produce same clustering."""
        r1 = self.service.cluster("/slides/test_slide.svs")
        r2 = self.service.cluster("/slides/test_slide.svs")
        ids1 = [(t.x, t.y, t.cluster_id) for t in r1.tile_assignments]
        ids2 = [(t.x, t.y, t.cluster_id) for t in r2.tile_assignments]
        assert ids1 == ids2

    def test_different_paths_different_results(self):
        r1 = self.service.cluster("/slides/slide_A.svs")
        r2 = self.service.cluster("/slides/slide_B.svs")
        ids1 = [t.cluster_id for t in r1.tile_assignments]
        ids2 = [t.cluster_id for t in r2.tile_assignments]
        assert ids1 != ids2

    def test_metadata_mode_mock(self):
        result = self.service.cluster("/slides/test_slide.svs")
        assert result.metadata.get("mode") == "mock"

    def test_processing_time_non_negative(self):
        result = self.service.cluster("/slides/test_slide.svs")
        assert result.processing_time_ms >= 0

    def test_n_clusters_capped_at_8(self):
        result = self.service.cluster("/slides/test_slide.svs", n_clusters=20)
        assert len(result.clusters) == 8
