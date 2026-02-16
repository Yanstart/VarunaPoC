"""
Tests for Similarity Search Endpoint — POST /ml/similar/{slide_id}

3 tests with mocked DiskCache and SimilarityIndex:
- test_similar_returns_results
- test_similar_no_embeddings_404
- test_similar_empty_index

Markers: @pytest.mark.similarity, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.mark.similarity
@pytest.mark.unit
class TestSimilarityEndpoint:
    """Test POST /ml/similar/{slide_id} with mocked dependencies."""

    @pytest.fixture(autouse=True)
    def _reset_singleton(self):
        """Reset the module-level singleton between tests."""
        import routes.ml as ml_module

        ml_module._similarity_index = None
        yield
        ml_module._similarity_index = None

    @pytest.fixture
    def mock_auth(self):
        """Mock auth dependency to allow unauthenticated access."""
        with patch(
            "routes.ml.require_role",
            return_value=lambda: MagicMock(
                username="test_user", roles=["MEDECIN"]
            ),
        ):
            yield

    @pytest.fixture
    def mock_deps(self, mock_auth):
        """Patch DiskCache and SimilarityIndex for endpoint tests."""
        mock_disk_cache = MagicMock()
        mock_index = MagicMock()
        mock_index.size.return_value = 50

        with (
            patch("routes.ml.DiskCache", return_value=mock_disk_cache),
            patch(
                "routes.ml.get_similarity_index",
                return_value=mock_index,
            ),
        ):
            yield mock_disk_cache, mock_index

    def test_similar_returns_results(self, client, mock_deps):
        """POST /ml/similar/{slide_id} returns similarity results."""
        mock_disk_cache, mock_index = mock_deps

        # Mock embeddings exist in cache
        fake_embeddings = np.random.randn(10, 128).astype(np.float32)
        mock_disk_cache.load_embeddings.return_value = fake_embeddings

        # Mock index search returns results
        mock_index.search.return_value = [
            {"slide_id": "slide-002", "score": 0.94},
            {"slide_id": "slide-003", "score": 0.87},
        ]

        response = client.post("/api/ml/similar/slide-001?top_k=5")

        assert response.status_code == 200
        data = response.json()
        assert data["query_slide_id"] == "slide-001"
        assert len(data["results"]) == 2
        assert data["results"][0]["slide_id"] == "slide-002"
        assert data["results"][0]["score"] == 0.94
        assert data["results"][0]["overview_url"] == "/api/slides/slide-002/overview"
        assert data["index_size"] == 50

    def test_similar_no_embeddings_404(self, client, mock_deps):
        """POST /ml/similar/{slide_id} returns 404 when no embeddings cached."""
        mock_disk_cache, _mock_index = mock_deps

        # No embeddings in cache
        mock_disk_cache.load_embeddings.return_value = None

        response = client.post("/api/ml/similar/nonexistent-slide")

        assert response.status_code == 404
        data = response.json()
        assert "No embeddings cached" in data["detail"]

    def test_similar_empty_index(self, client, mock_deps):
        """POST /ml/similar/{slide_id} returns empty results for empty index."""
        mock_disk_cache, mock_index = mock_deps

        # Embeddings exist
        fake_embeddings = np.random.randn(10, 128).astype(np.float32)
        mock_disk_cache.load_embeddings.return_value = fake_embeddings

        # Empty index returns no results
        mock_index.search.return_value = []
        mock_index.size.return_value = 0

        response = client.post("/api/ml/similar/slide-001")

        assert response.status_code == 200
        data = response.json()
        assert data["query_slide_id"] == "slide-001"
        assert len(data["results"]) == 0
        assert data["index_size"] == 0
