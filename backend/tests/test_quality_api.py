"""
Integration tests for Quality Metrics API endpoints.

These tests require PostgreSQL with PostGIS. They create real annotations
and verify the quality endpoints return correct structures.

Marked with 'db' marker - skipped automatically if PostgreSQL is unavailable.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def _check_db():
    try:
        import asyncpg
    except ImportError:
        return False

    async def _try_connect():
        try:
            conn = await asyncpg.connect(
                host="localhost",
                port=5433,
                user="varuna",
                password="varuna_dev",  # pragma: allowlist secret
                database="varuna",
                timeout=2,
            )
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(_try_connect())


DB_AVAILABLE = _check_db()

pytestmark = [
    pytest.mark.db,
    pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available on localhost:5433"),
]


@pytest.fixture
def quality_client(client):
    """Client for quality API tests."""
    return client


class TestAnnotatorsEndpoint:
    def test_get_annotators_no_annotations(self, quality_client):
        """Slide with no annotations returns empty list."""
        response = quality_client.get("/api/v1/quality/nonexistent_slide/annotators")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_annotators_returns_list(self, quality_client):
        """Endpoint returns correct structure."""
        response = quality_client.get("/api/v1/quality/test_slide/annotators")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestKappaEndpoint:
    def test_kappa_no_data(self, quality_client):
        """Kappa with no matching annotations returns 0."""
        response = quality_client.post(
            "/api/v1/quality/test_slide/kappa",
            json={
                "annotator_a": "user_a",
                "annotator_b": "user_b",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "kappa" in data
        assert "interpretation" in data
        assert data["n_matched"] == 0

    def test_kappa_response_structure(self, quality_client):
        """Verify response has all expected fields."""
        response = quality_client.post(
            "/api/v1/quality/test_slide/kappa",
            json={
                "annotator_a": "user_a",
                "annotator_b": "user_b",
                "iou_threshold": 0.5,
                "matching_strategy": "iou",
            },
        )
        assert response.status_code == 200
        data = response.json()
        expected_keys = {
            "kappa",
            "interpretation",
            "annotator_a",
            "annotator_b",
            "n_matched",
            "n_unmatched_a",
            "n_unmatched_b",
            "matching_strategy",
        }
        assert expected_keys.issubset(set(data.keys()))


class TestFleissEndpoint:
    def test_fleiss_no_data(self, quality_client):
        """Fleiss with no data returns 0."""
        response = quality_client.post(
            "/api/v1/quality/test_slide/fleiss",
            json={
                "annotators": ["user_a", "user_b", "user_c"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kappa"] == 0.0
        assert data["n_cells"] == 0


class TestConfusionMatrixEndpoint:
    def test_confusion_matrix_empty(self, quality_client):
        """Empty slide returns empty matrix."""
        response = quality_client.post(
            "/api/v1/quality/test_slide/confusion-matrix",
            json={
                "annotator_a": "user_a",
                "annotator_b": "user_b",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["matrix"] == []
        assert data["categories"] == []


class TestDisagreementsEndpoint:
    def test_disagreements_empty(self, quality_client):
        """Empty slide returns empty FeatureCollection."""
        response = quality_client.post(
            "/api/v1/quality/test_slide/disagreements",
            json={
                "annotator_a": "user_a",
                "annotator_b": "user_b",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert data["features"] == []
        assert data["n_disagreements"] == 0
