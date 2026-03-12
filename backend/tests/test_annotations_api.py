"""
Tests for Annotations API - Integration tests requiring PostgreSQL

Tests CRUD operations, batch create, spatial queries, GeoJSON export,
stats endpoint, error handling, and edge cases.
Requires a running PostgreSQL+PostGIS instance.

Run: pytest tests/test_annotations_api.py -m db
Skip: pytest -m "not db"

Markers: @pytest.mark.annotation, @pytest.mark.db
"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


def _check_db():
    """Check if PostgreSQL is reachable. Uses new_event_loop() for Windows compatibility."""
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

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_try_connect())
    finally:
        loop.close()


DB_AVAILABLE = _check_db()

pytestmark = [
    pytest.mark.annotation,
    pytest.mark.db,
    pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available on localhost:5433"),
]


# ============================================
# Fixtures
# ============================================


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


def _make_polygon(x=1000, y=1000, size=1000):
    """Helper: create a polygon dict at given position."""
    return {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [x, y],
                    [x + size, y],
                    [x + size, y + size],
                    [x, y + size],
                    [x, y],
                ]
            ],
        },
        "geometry_type": "polygon",
        "annotation_type": "manual",
    }


# ============================================
# Original CRUD Tests
# ============================================


class TestAnnotationsAPI:
    """
    Integration tests for the annotations REST API.

    These tests require a running PostgreSQL+PostGIS database.
    Skip with: pytest -m "not db"
    """

    def test_create_annotation(self, client, sample_polygon):
        response = client.post("/api/v1/annotations/test_slide_crud", json=sample_polygon)
        assert response.status_code == 201
        data = response.json()
        assert data["slide_id"] == "test_slide_crud"
        assert data["geometry_type"] == "rectangle"
        assert data["annotation_type"] == "manual"
        assert "id" in data

    def test_list_annotations(self, client, sample_polygon):
        client.post("/api/v1/annotations/test_slide_list", json=sample_polygon)
        response = client.get("/api/v1/annotations/test_slide_list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_annotation(self, client, sample_polygon):
        create_resp = client.post("/api/v1/annotations/test_slide_get", json=sample_polygon)
        anno_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/annotations/test_slide_get/{anno_id}")
        assert response.status_code == 200
        assert response.json()["id"] == anno_id

    def test_update_annotation(self, client, sample_polygon):
        create_resp = client.post("/api/v1/annotations/test_slide_upd", json=sample_polygon)
        anno_id = create_resp.json()["id"]

        update_data = {"annotation_type": "auto_confirmed", "confidence": 0.95}
        response = client.put(f"/api/v1/annotations/test_slide_upd/{anno_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["annotation_type"] == "auto_confirmed"

    def test_delete_annotation(self, client, sample_polygon):
        create_resp = client.post("/api/v1/annotations/test_slide_del", json=sample_polygon)
        anno_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/annotations/test_slide_del/{anno_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f"/api/v1/annotations/test_slide_del/{anno_id}")
        assert get_resp.status_code == 404

    def test_batch_create(self, client, sample_polygon, sample_auto_detection):
        batch = {"annotations": [sample_polygon, sample_auto_detection]}
        response = client.post("/api/v1/annotations/test_slide_batch/batch", json=batch)
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2

    def test_spatial_query(self, client, sample_polygon, sample_point):
        client.post("/api/v1/annotations/test_slide_spatial", json=sample_polygon)
        client.post("/api/v1/annotations/test_slide_spatial", json=sample_point)

        # Query bbox that includes the rectangle but not the point
        response = client.get(
            "/api/v1/annotations/test_slide_spatial",
            params={
                "bbox_x1": 500,
                "bbox_y1": 500,
                "bbox_x2": 2500,
                "bbox_y2": 2500,
            },
        )
        assert response.status_code == 200
        data = response.json()
        types = [d["geometry_type"] for d in data]
        assert "rectangle" in types

    def test_export_geojson(self, client, sample_polygon):
        client.post("/api/v1/annotations/test_slide_export", json=sample_polygon)

        response = client.get("/api/v1/annotations/test_slide_export/export")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) >= 1

    def test_filter_by_type(self, client, sample_polygon, sample_auto_detection):
        client.post("/api/v1/annotations/test_slide_filter", json=sample_polygon)
        client.post("/api/v1/annotations/test_slide_filter", json=sample_auto_detection)

        response = client.get(
            "/api/v1/annotations/test_slide_filter", params={"annotation_type": "manual"}
        )
        data = response.json()
        assert all(d["annotation_type"] == "manual" for d in data)


# ============================================
# Stats Endpoint Tests
# ============================================


class TestAnnotationStatsAPI:
    """Tests for the GET /api/annotations/{slide_id}/stats endpoint."""

    def test_stats_empty_slide(self, client):
        """Stats for a slide with no annotations should return zero counts."""
        response = client.get("/api/v1/annotations/test_slide_stats_empty/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_stats_counts(self, client):
        """Stats should reflect created annotations by type."""
        slide = "test_slide_stats_count"
        # Create 2 manual + 1 auto_confirmed
        client.post(f"/api/v1/annotations/{slide}", json=_make_polygon(100, 100))
        client.post(f"/api/v1/annotations/{slide}", json=_make_polygon(200, 200))
        auto = _make_polygon(300, 300)
        auto["annotation_type"] = "auto_confirmed"
        auto["confidence"] = 0.9
        client.post(f"/api/v1/annotations/{slide}", json=auto)

        response = client.get(f"/api/v1/annotations/{slide}/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        type_map = {t["type"]: t["count"] for t in data["by_type"]}
        assert type_map.get("manual", 0) == 2
        assert type_map.get("auto_confirmed", 0) == 1

    def test_stats_confidence_buckets(self, client):
        """Confidence distribution should bucket correctly (high/medium/low/unscored)."""
        slide = "test_slide_stats_conf"
        # High confidence (>= 0.8)
        high = _make_polygon(100, 100)
        high["annotation_type"] = "auto_confirmed"
        high["confidence"] = 0.95
        client.post(f"/api/v1/annotations/{slide}", json=high)
        # Medium confidence (0.5 <= x < 0.8)
        med = _make_polygon(200, 200)
        med["annotation_type"] = "auto_confirmed"
        med["confidence"] = 0.65
        client.post(f"/api/v1/annotations/{slide}", json=med)
        # Low confidence (< 0.5)
        low = _make_polygon(300, 300)
        low["annotation_type"] = "auto"
        low["confidence"] = 0.3
        client.post(f"/api/v1/annotations/{slide}", json=low)
        # Unscored (no confidence)
        client.post(f"/api/v1/annotations/{slide}", json=_make_polygon(400, 400))

        response = client.get(f"/api/v1/annotations/{slide}/stats")
        data = response.json()
        dist = data["confidence_distribution"]
        assert dist["high"] >= 1
        assert dist["medium"] >= 1
        assert dist["low"] >= 1
        assert dist["unscored"] >= 1


# ============================================
# Error Handling Tests
# ============================================


class TestAnnotationErrors:
    """Tests for error responses (404, 422)."""

    def test_get_nonexistent_annotation(self, client):
        """GET with a random UUID should return 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/annotations/test_slide_err/{fake_id}")
        assert response.status_code == 404

    def test_update_nonexistent_annotation(self, client):
        """PUT with a random UUID should return 404."""
        fake_id = str(uuid.uuid4())
        response = client.put(
            f"/api/v1/annotations/test_slide_err/{fake_id}",
            json={"annotation_type": "manual"},
        )
        assert response.status_code == 404

    def test_delete_nonexistent_annotation(self, client):
        """DELETE with a random UUID should return 404."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/annotations/test_slide_err/{fake_id}")
        assert response.status_code == 404

    def test_invalid_confidence_too_high(self, client):
        """Confidence > 1.0 should return 422."""
        anno = _make_polygon()
        anno["confidence"] = 1.5
        response = client.post("/api/v1/annotations/test_slide_err", json=anno)
        assert response.status_code == 422

    def test_invalid_confidence_negative(self, client):
        """Negative confidence should return 422."""
        anno = _make_polygon()
        anno["confidence"] = -0.1
        response = client.post("/api/v1/annotations/test_slide_err", json=anno)
        assert response.status_code == 422

    def test_missing_geometry(self, client):
        """Missing geometry field should return 422."""
        response = client.post(
            "/api/v1/annotations/test_slide_err",
            json={"geometry_type": "polygon", "annotation_type": "manual"},
        )
        assert response.status_code == 422

    def test_invalid_label_color(self, client):
        """Invalid hex color should return 422."""
        response = client.post(
            "/api/v1/labels/",
            json={"name": "test_bad_color", "color": "not-a-color"},
        )
        assert response.status_code == 422

    def test_empty_label_name(self, client):
        """Empty label name should return 422."""
        response = client.post("/api/v1/labels/", json={"name": ""})
        assert response.status_code == 422

    def test_invalid_annotation_id_format(self, client):
        """Non-UUID annotation_id should return 422."""
        response = client.get("/api/v1/annotations/test_slide_err/not-a-uuid")
        assert response.status_code == 422


# ============================================
# Edge Cases
# ============================================


class TestAnnotationEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_list_empty_slide(self, client):
        """Listing annotations for a slide with none should return empty list."""
        response = client.get("/api/v1/annotations/test_slide_empty_list")
        assert response.status_code == 200
        assert response.json() == []

    def test_export_empty_slide(self, client):
        """Exporting a slide with no annotations should return empty FeatureCollection."""
        response = client.get("/api/v1/annotations/test_slide_empty_export/export")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert data["features"] == []

    def test_batch_single_item(self, client):
        """Batch create with a single annotation should work."""
        batch = {"annotations": [_make_polygon(500, 500)]}
        response = client.post("/api/v1/annotations/test_slide_batch1/batch", json=batch)
        assert response.status_code == 201
        assert len(response.json()) == 1

    def test_point_annotation(self, client, sample_point):
        """Point geometry should round-trip correctly."""
        response = client.post("/api/v1/annotations/test_slide_point", json=sample_point)
        assert response.status_code == 201
        data = response.json()
        assert data["geometry_type"] == "point"
        assert data["geometry"]["type"] == "Point"

    def test_confidence_filter(self, client):
        """min_confidence filter should exclude low-confidence annotations."""
        slide = "test_slide_conf_filter"
        # Create low-confidence
        low = _make_polygon(100, 100)
        low["annotation_type"] = "auto"
        low["confidence"] = 0.3
        client.post(f"/api/v1/annotations/{slide}", json=low)
        # Create high-confidence
        high = _make_polygon(200, 200)
        high["annotation_type"] = "auto_confirmed"
        high["confidence"] = 0.9
        client.post(f"/api/v1/annotations/{slide}", json=high)

        response = client.get(f"/api/v1/annotations/{slide}", params={"min_confidence": 0.8})
        assert response.status_code == 200
        data = response.json()
        assert all(d.get("confidence", 0) >= 0.8 for d in data)
        assert len(data) >= 1


# ============================================
# Labels CRUD Tests (extended)
# ============================================


class TestLabelsAPI:
    """Integration tests for annotation labels."""

    def test_create_label(self, client):
        response = client.post(
            "/api/v1/labels/",
            json={
                "name": "Test Tumor",
                "color": "#FF0000",
                "category": "pathology",
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Test Tumor"

    def test_list_labels(self, client):
        client.post("/api/v1/labels/", json={"name": "Test Label List"})
        response = client.get("/api/v1/labels/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_label(self, client):
        """GET a label by ID should return the label."""
        create_resp = client.post(
            "/api/v1/labels/",
            json={"name": "Test Get Label", "color": "#00FF00"},
        )
        label_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/labels/{label_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Get Label"

    def test_update_label(self, client):
        """PUT should update label fields."""
        create_resp = client.post(
            "/api/v1/labels/",
            json={"name": "Test Update Label", "color": "#0000FF"},
        )
        label_id = create_resp.json()["id"]

        response = client.put(
            f"/api/v1/labels/{label_id}",
            json={"name": "Test Updated Label", "color": "#FF00FF"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test Updated Label"
        assert response.json()["color"] == "#FF00FF"

    def test_delete_label(self, client):
        """DELETE should remove the label."""
        create_resp = client.post(
            "/api/v1/labels/",
            json={"name": "Test Delete Label"},
        )
        label_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/labels/{label_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = client.get(f"/api/v1/labels/{label_id}")
        assert get_resp.status_code == 404

    def test_get_nonexistent_label(self, client):
        """GET with a random label UUID should return 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/labels/{fake_id}")
        assert response.status_code == 404

    def test_update_nonexistent_label(self, client):
        """PUT with a random label UUID should return 404."""
        fake_id = str(uuid.uuid4())
        response = client.put(f"/api/v1/labels/{fake_id}", json={"name": "test_nope"})
        assert response.status_code == 404

    def test_delete_nonexistent_label(self, client):
        """DELETE with a random label UUID should return 404."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/labels/{fake_id}")
        assert response.status_code == 404
