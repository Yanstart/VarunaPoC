"""
Tests for Annotations API - Integration tests requiring PostgreSQL

Tests CRUD operations, batch create, spatial queries, and GeoJSON export.
Requires a running PostgreSQL+PostGIS instance.

Run: pytest tests/test_annotations_api.py -m db

Markers: @pytest.mark.annotation, @pytest.mark.db
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Check DB availability by trying to connect
import asyncio

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
    pytest.mark.annotation,
    pytest.mark.db,
    pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available on localhost:5433"),
]


@pytest.fixture
def sample_polygon():
    """A simple polygon in slide pixel coordinates."""
    return {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[1000, 1000], [2000, 1000], [2000, 2000], [1000, 2000], [1000, 1000]]],
        },
        "geometry_type": "rectangle",
        "annotation_type": "manual",
    }


@pytest.fixture
def sample_point():
    """A point annotation."""
    return {
        "geometry": {"type": "Point", "coordinates": [5000, 3000]},
        "geometry_type": "point",
        "annotation_type": "manual",
    }


@pytest.fixture
def sample_auto_detection():
    """An auto-detected polygon."""
    return {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[3000, 3000], [4000, 3000], [4000, 4000], [3000, 4000], [3000, 3000]]],
        },
        "geometry_type": "polygon",
        "annotation_type": "auto_confirmed",
        "confidence": 0.87,
        "properties": {"model": "resnet50", "detection_index": 0},
    }


class TestAnnotationsAPI:
    """
    Integration tests for the annotations REST API.

    These tests require a running PostgreSQL+PostGIS database.
    Skip with: pytest -m "not db"
    """

    def test_create_annotation(self, client, sample_polygon):
        response = client.post("/api/annotations/test_slide", json=sample_polygon)
        assert response.status_code == 201
        data = response.json()
        assert data["slide_id"] == "test_slide"
        assert data["geometry_type"] == "rectangle"
        assert data["annotation_type"] == "manual"
        assert "id" in data

    def test_list_annotations(self, client, sample_polygon):
        # Create first
        client.post("/api/annotations/test_slide", json=sample_polygon)
        # List
        response = client.get("/api/annotations/test_slide")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_annotation(self, client, sample_polygon):
        create_resp = client.post("/api/annotations/test_slide", json=sample_polygon)
        anno_id = create_resp.json()["id"]

        response = client.get(f"/api/annotations/test_slide/{anno_id}")
        assert response.status_code == 200
        assert response.json()["id"] == anno_id

    def test_update_annotation(self, client, sample_polygon):
        create_resp = client.post("/api/annotations/test_slide", json=sample_polygon)
        anno_id = create_resp.json()["id"]

        update_data = {"annotation_type": "auto_confirmed", "confidence": 0.95}
        response = client.put(f"/api/annotations/test_slide/{anno_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["annotation_type"] == "auto_confirmed"

    def test_delete_annotation(self, client, sample_polygon):
        create_resp = client.post("/api/annotations/test_slide", json=sample_polygon)
        anno_id = create_resp.json()["id"]

        response = client.delete(f"/api/annotations/test_slide/{anno_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f"/api/annotations/test_slide/{anno_id}")
        assert get_resp.status_code == 404

    def test_batch_create(self, client, sample_polygon, sample_auto_detection):
        batch = {"annotations": [sample_polygon, sample_auto_detection]}
        response = client.post("/api/annotations/test_slide/batch", json=batch)
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2

    def test_spatial_query(self, client, sample_polygon, sample_point):
        # Create annotations at known positions
        client.post("/api/annotations/test_slide", json=sample_polygon)
        client.post("/api/annotations/test_slide", json=sample_point)

        # Query bbox that includes the rectangle but not the point
        response = client.get(
            "/api/annotations/test_slide",
            params={
                "bbox_x1": 500,
                "bbox_y1": 500,
                "bbox_x2": 2500,
                "bbox_y2": 2500,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should find the rectangle (1000-2000) but not the point (5000, 3000)
        types = [d["geometry_type"] for d in data]
        assert "rectangle" in types

    def test_export_geojson(self, client, sample_polygon):
        client.post("/api/annotations/test_slide", json=sample_polygon)

        response = client.get("/api/annotations/test_slide/export")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) >= 1

    def test_filter_by_type(self, client, sample_polygon, sample_auto_detection):
        client.post("/api/annotations/test_slide", json=sample_polygon)
        client.post("/api/annotations/test_slide", json=sample_auto_detection)

        # Filter manual only
        response = client.get("/api/annotations/test_slide", params={"annotation_type": "manual"})
        data = response.json()
        assert all(d["annotation_type"] == "manual" for d in data)


class TestLabelsAPI:
    """Integration tests for annotation labels."""

    def test_create_label(self, client):
        response = client.post(
            "/api/labels/",
            json={
                "name": "Tumor",
                "color": "#FF0000",
                "category": "pathology",
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Tumor"

    def test_list_labels(self, client):
        client.post("/api/labels/", json={"name": "Test Label"})
        response = client.get("/api/labels/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
