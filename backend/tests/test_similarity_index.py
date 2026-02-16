"""
Tests for SimilarityIndex — FAISS vector index for slide similarity search.

4 tests using numpy random embeddings (mock faiss if not installed):
- test_add_and_search — add 5 slides, query one, verify results sorted by score
- test_exclude_self — query slide is excluded from results
- test_save_and_reload — save, create new instance from same dir, verify data persists
- test_empty_index — search returns empty list

Markers: @pytest.mark.similarity, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest

# Try importing faiss; if unavailable, skip all tests
faiss = pytest.importorskip("faiss", reason="faiss-cpu not installed")

from services.ml.similarity_index import SimilarityIndex, FAISS_AVAILABLE


@pytest.mark.similarity
@pytest.mark.unit
class TestSimilarityIndex:
    """Test FAISS-based similarity index."""

    @pytest.fixture
    def index_dir(self, tmp_path):
        """Temporary directory for test index."""
        return str(tmp_path / "test_index")

    @pytest.fixture
    def sample_embeddings(self):
        """Generate 5 slides with random embeddings (10 patches, 128 dim)."""
        rng = np.random.RandomState(42)
        return {
            f"slide-{i:03d}": rng.randn(10, 128).astype(np.float32)
            for i in range(5)
        }

    def test_add_and_search(self, index_dir, sample_embeddings):
        """Add 5 slides, search for most similar, verify results sorted by score."""
        idx = SimilarityIndex(index_dir=index_dir)

        # Add all slides
        for slide_id, emb in sample_embeddings.items():
            idx.add_slide(slide_id, emb)

        assert idx.size() == 5

        # Query with slide-000's embeddings
        query_emb = sample_embeddings["slide-000"]
        results = idx.search(query_emb, top_k=5)

        # Should return results
        assert len(results) > 0

        # Results should be sorted by descending score
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Each result should have slide_id and score
        for r in results:
            assert "slide_id" in r
            assert "score" in r
            # Cosine similarity via inner product ranges from -1 to 1
            assert -1.0 - 1e-6 <= r["score"] <= 1.0 + 1e-6

    def test_exclude_self(self, index_dir, sample_embeddings):
        """Query slide is excluded from results when exclude_id is set."""
        idx = SimilarityIndex(index_dir=index_dir)

        for slide_id, emb in sample_embeddings.items():
            idx.add_slide(slide_id, emb)

        query_emb = sample_embeddings["slide-000"]
        results = idx.search(query_emb, top_k=5, exclude_id="slide-000")

        # slide-000 should not be in results
        result_ids = [r["slide_id"] for r in results]
        assert "slide-000" not in result_ids

        # Should still have results (from the other 4 slides)
        assert len(results) > 0

    def test_save_and_reload(self, index_dir, sample_embeddings):
        """Save index, create new instance from same dir, verify data persists."""
        idx = SimilarityIndex(index_dir=index_dir)

        for slide_id, emb in sample_embeddings.items():
            idx.add_slide(slide_id, emb)

        idx.save()

        # Create new instance from same directory
        idx2 = SimilarityIndex(index_dir=index_dir)

        assert idx2.size() == 5
        assert set(idx2.slide_ids) == set(sample_embeddings.keys())

        # Search should still work
        query_emb = sample_embeddings["slide-000"]
        results = idx2.search(query_emb, top_k=3)
        assert len(results) > 0

    def test_empty_index(self, index_dir):
        """Search on empty index returns empty list."""
        idx = SimilarityIndex(index_dir=index_dir)

        assert idx.size() == 0

        # Search with random embeddings
        query = np.random.randn(5, 128).astype(np.float32)
        results = idx.search(query, top_k=5)

        assert results == []

    def test_deduplication(self, index_dir, sample_embeddings):
        """Adding the same slide_id twice should not create a duplicate."""
        idx = SimilarityIndex(index_dir=index_dir)

        emb = sample_embeddings["slide-000"]
        idx.add_slide("slide-000", emb)
        idx.add_slide("slide-000", emb)  # duplicate

        assert idx.size() == 1
        assert idx.slide_ids.count("slide-000") == 1
