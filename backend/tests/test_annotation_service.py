"""
Tests for Annotation Service - Unit tests with mock DB

Tests service logic, GeoJSON validation, and data transformation.
Does NOT require a running PostgreSQL instance.

Markers: @pytest.mark.annotation, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from schemas.annotation import AnnotationBatchCreate, AnnotationCreate, AnnotationUpdate
from schemas.detection import DetectionRequest, DetectionResponse
from schemas.geojson import GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONGeometry

# ============================================
# Schema Validation Tests
# ============================================


@pytest.mark.annotation
@pytest.mark.unit
class TestGeoJSONSchemas:
    def test_valid_polygon_geometry(self):
        geom = GeoJSONGeometry(
            type="Polygon",
            coordinates=[[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]],
        )
        assert geom.type == "Polygon"

    def test_valid_point_geometry(self):
        geom = GeoJSONGeometry(type="Point", coordinates=[500, 300])
        assert geom.type == "Point"

    def test_feature_with_properties(self):
        feature = GeoJSONFeature(
            geometry=GeoJSONGeometry(
                type="Polygon",
                coordinates=[[[0, 0], [10, 0], [10, 10], [0, 0]]],
            ),
            properties={"confidence": 0.95, "area_px": 1000},
            id="test_1",
        )
        assert feature.type == "Feature"
        assert feature.properties["confidence"] == 0.95

    def test_feature_collection(self):
        fc = GeoJSONFeatureCollection(
            features=[
                GeoJSONFeature(
                    geometry=GeoJSONGeometry(type="Point", coordinates=[0, 0]),
                    properties={},
                )
            ],
            metadata={"slide_id": "test"},
        )
        assert fc.type == "FeatureCollection"
        assert len(fc.features) == 1


@pytest.mark.annotation
@pytest.mark.unit
class TestAnnotationSchemas:
    def test_create_annotation_minimal(self):
        data = AnnotationCreate(
            geometry=GeoJSONGeometry(
                type="Polygon",
                coordinates=[[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]],
            ),
            geometry_type="rectangle",
        )
        assert data.annotation_type == "manual"
        assert data.confidence is None

    def test_create_annotation_full(self):
        data = AnnotationCreate(
            geometry=GeoJSONGeometry(
                type="Polygon",
                coordinates=[[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]],
            ),
            geometry_type="polygon",
            annotation_type="auto_confirmed",
            confidence=0.85,
            properties={"model": "resnet50"},
            created_by="ml_pipeline",
        )
        assert data.annotation_type == "auto_confirmed"
        assert data.confidence == 0.85

    def test_confidence_validation(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnnotationCreate(
                geometry=GeoJSONGeometry(type="Point", coordinates=[0, 0]),
                geometry_type="point",
                confidence=1.5,  # > 1.0, should fail
            )

    def test_batch_create(self):
        batch = AnnotationBatchCreate(
            annotations=[
                AnnotationCreate(
                    geometry=GeoJSONGeometry(type="Point", coordinates=[i, i]),
                    geometry_type="point",
                )
                for i in range(5)
            ]
        )
        assert len(batch.annotations) == 5

    def test_update_partial(self):
        data = AnnotationUpdate(annotation_type="auto_confirmed")
        dumped = data.model_dump(exclude_unset=True)
        assert "annotation_type" in dumped
        assert "geometry" not in dumped


@pytest.mark.annotation
@pytest.mark.unit
class TestDetectionSchemas:
    def test_default_detection_request(self):
        req = DetectionRequest()
        assert req.threshold == 0.5
        assert req.min_area == 100.0
        assert req.prediction_class == "tissue"

    def test_custom_detection_request(self):
        req = DetectionRequest(threshold=0.7, min_area=500, prediction_class="tumor")
        assert req.threshold == 0.7

    def test_detection_response(self):
        resp = DetectionResponse(
            slide_id="test_slide",
            geojson=GeoJSONFeatureCollection(features=[]),
            num_regions=0,
            parameters={"threshold": 0.5},
        )
        assert resp.num_regions == 0


@pytest.mark.annotation
@pytest.mark.unit
class TestLabelSchemas:
    def test_valid_hex_color(self):
        from schemas.annotation import LabelCreate

        label = LabelCreate(name="Tumor", color="#FF0000")
        assert label.color == "#FF0000"

    def test_invalid_hex_color(self):
        from pydantic import ValidationError

        from schemas.annotation import LabelCreate

        with pytest.raises(ValidationError):
            LabelCreate(name="Bad", color="red")  # Not a hex code

    def test_default_color(self):
        from schemas.annotation import LabelCreate

        label = LabelCreate(name="Default")
        assert label.color == "#FF0000"
