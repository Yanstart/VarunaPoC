"""
Tests for DICOM Standards Implementation

Tests cover:
- #105: DICOMweb WADO-RS Tile Serving
- #110: DICOM WSI Export Supplement 145
- #111: DICOM SR for AI Results
- #117: DICOM Microscopy Annotations Export
- #122: DICOMweb STOW-RS and QIDO-RS

All tests run in mock mode (no pydicom/highdicom required).
"""

import hashlib

import pytest

# =========================================================================
# Helper
# =========================================================================


def _seed_from_id(identifier: str) -> int:
    return int(hashlib.md5(identifier.encode()).hexdigest()[:8], 16)


# =========================================================================
# #110 — DICOMExportService (Supplement 145)
# =========================================================================


class TestDICOMExportService:
    """Tests for improved DICOM WSI Export with Supplement 145 metadata."""

    def test_export_returns_result(self):
        """Export produces a DICOMExportResult with all fields."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        result = svc.export("slide_001")

        assert result.slide_id == "slide_001"
        assert result.status == "mock"
        assert result.dicom_uid.startswith("2.25.")
        assert len(result.dicom_uid) <= 64
        assert result.frames_count > 0
        assert result.processing_time_ms >= 0

    def test_export_deterministic_uid(self):
        """Same slide_id always produces the same UID."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        r1 = svc.export("deterministic_test")
        r2 = svc.export("deterministic_test")
        assert r1.dicom_uid == r2.dicom_uid

    def test_export_different_uids_for_different_slides(self):
        """Different slide_ids produce different UIDs."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        r1 = svc.export("slide_A")
        r2 = svc.export("slide_B")
        assert r1.dicom_uid != r2.dicom_uid

    def test_export_has_supplement_145_metadata(self):
        """Export result includes full Supplement 145 metadata structure."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        result = svc.export("slide_145")

        assert result.metadata is not None
        meta = result.metadata

        # Check required modules are present
        assert "sop_common" in meta
        assert "patient" in meta
        assert "general_study" in meta
        assert "general_series" in meta
        assert "general_equipment" in meta
        assert "wsi_image" in meta
        assert "optical_path" in meta
        assert "specimen" in meta
        assert "frame_of_reference" in meta

    def test_sop_class_uid_is_wsi(self):
        """SOP Class UID is VL Whole Slide Microscopy Image."""
        from services.dicom_export import (
            VL_WHOLE_SLIDE_MICROSCOPY_IMAGE,
            DICOMExportService,
        )

        svc = DICOMExportService()
        result = svc.export("slide_sop")

        sop_uid = result.metadata["sop_common"]["sop_class_uid"]
        assert sop_uid == VL_WHOLE_SLIDE_MICROSCOPY_IMAGE
        assert sop_uid == "1.2.840.10008.5.1.4.1.1.77.1.6"

    def test_modality_is_sm(self):
        """Series modality is SM (Slide Microscopy)."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        result = svc.export("slide_mod")

        assert result.metadata["general_series"]["modality"] == "SM"

    def test_patient_anonymization(self):
        """Patient name is ANONYMOUS when anonymize=True."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        result = svc.export("slide_anon", patient_name="John Doe", anonymize=True)

        assert result.metadata["patient"]["patient_name"] == "ANONYMOUS"

    def test_patient_name_preserved_when_not_anonymized(self):
        """Patient name is preserved when anonymize=False."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        result = svc.export(
            "slide_named", patient_name="Jane Doe", anonymize=False
        )

        assert result.metadata["patient"]["patient_name"] == "Jane Doe"

    def test_equipment_module(self):
        """General Equipment module has VarunaPoC as manufacturer."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        result = svc.export("slide_eq")

        equip = result.metadata["general_equipment"]
        assert equip["manufacturer"] == "VarunaPoC"
        assert equip["institution_name"] == "CHU UCL Namur"

    def test_wsi_image_module(self):
        """WSI Image module has correct pixel parameters."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        result = svc.export("slide_wsi")

        wsi = result.metadata["wsi_image"]
        assert wsi["samples_per_pixel"] == 3
        assert wsi["bits_allocated"] == 8
        assert wsi["bits_stored"] == 8
        assert wsi["high_bit"] == 7
        assert wsi["total_pixel_matrix_columns"] > 0
        assert wsi["total_pixel_matrix_rows"] > 0
        assert wsi["number_of_frames"] > 0

    def test_uid_uses_2_25_prefix(self):
        """Generated UIDs use the 2.25. prefix standard."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        result = svc.export("slide_uid_prefix")

        assert result.dicom_uid.startswith("2.25.")
        meta = result.metadata
        assert meta["sop_common"]["sop_instance_uid"].startswith("2.25.")
        assert meta["general_study"]["study_instance_uid"].startswith("2.25.")
        assert meta["general_series"]["series_instance_uid"].startswith("2.25.")

    def test_get_export_status(self):
        """get_export_status returns expected structure."""
        from services.dicom_export import DICOMExportService

        svc = DICOMExportService()
        status = svc.get_export_status("slide_status")

        assert status["slide_id"] == "slide_status"
        assert status["status"] == "not_started"


# =========================================================================
# #105 — DICOMweb WADO-RS
# =========================================================================


class TestDICOMwebWADORS:
    """Tests for DICOMweb WADO-RS service (retrieve metadata and frames)."""

    def test_retrieve_instance_metadata(self):
        """Retrieve instance metadata returns DICOM JSON structure."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        metadata = svc.retrieve_instance_metadata(
            "1.2.3.4", "1.2.3.5", "1.2.3.6"
        )

        assert isinstance(metadata, list)
        assert len(metadata) == 1

        meta = metadata[0]
        # SOP Class UID
        assert "00080016" in meta
        assert meta["00080016"]["vr"] == "UI"
        assert meta["00080016"]["Value"][0] == "1.2.840.10008.5.1.4.1.1.77.1.6"

        # SOP Instance UID matches input
        assert meta["00080018"]["Value"][0] == "1.2.3.6"

        # Study and Series UIDs match input
        assert meta["0020000D"]["Value"][0] == "1.2.3.4"
        assert meta["0020000E"]["Value"][0] == "1.2.3.5"

        # Modality is SM
        assert meta["00080060"]["Value"][0] == "SM"

    def test_retrieve_instance_metadata_has_pixel_info(self):
        """Metadata includes pixel-related attributes."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        meta = svc.retrieve_instance_metadata("s", "se", "i")[0]

        # Rows and Columns
        assert meta["00280010"]["Value"][0] > 0  # Rows
        assert meta["00280011"]["Value"][0] > 0  # Columns

        # Total Pixel Matrix
        assert meta["00480006"]["Value"][0] > 0  # Total Columns
        assert meta["00480007"]["Value"][0] > 0  # Total Rows

    def test_retrieve_frame_returns_bytes(self):
        """Frame retrieval returns non-empty bytes."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        frame = svc.retrieve_frame("s", "se", "i", 1)

        assert isinstance(frame, bytes)
        assert len(frame) > 0

    def test_retrieve_frame_starts_with_jpeg_soi(self):
        """Frame data starts with JPEG SOI marker (0xFFD8)."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        frame = svc.retrieve_frame("s", "se", "i", 1)

        assert frame[0] == 0xFF
        assert frame[1] == 0xD8

    def test_retrieve_frame_deterministic(self):
        """Same parameters produce same frame data."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        f1 = svc.retrieve_frame("s", "se", "i", 1)
        f2 = svc.retrieve_frame("s", "se", "i", 1)
        assert f1 == f2

    def test_different_frames_differ(self):
        """Different frame numbers produce different data."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        f1 = svc.retrieve_frame("s", "se", "i", 1)
        f2 = svc.retrieve_frame("s", "se", "i", 2)
        assert f1 != f2


# =========================================================================
# #122 — DICOMweb STOW-RS and QIDO-RS
# =========================================================================


class TestDICOMwebSTOWRS:
    """Tests for DICOMweb STOW-RS (store instances)."""

    def test_store_no_instances(self):
        """Store with no instances creates a default instance."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        result = svc.store_instances()

        assert result["status"] == "success"
        assert result["stored_count"] == 1
        assert len(result["stored_instances"]) == 1
        assert "study_uid" in result

    def test_store_with_study_uid(self):
        """Store with explicit study UID uses that UID."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        result = svc.store_instances(study_uid="1.2.3.999")

        assert result["study_uid"] == "1.2.3.999"

    def test_store_multiple_instances(self):
        """Store multiple instances registers them all."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        instances = [
            {"series_uid": "1.2.3.10", "instance_uid": "1.2.3.100"},
            {"series_uid": "1.2.3.10", "instance_uid": "1.2.3.101"},
        ]
        result = svc.store_instances(
            study_uid="1.2.3.50", instances_data=instances
        )

        assert result["stored_count"] == 2
        assert result["stored_instances"][0]["instance_uid"] == "1.2.3.100"
        assert result["stored_instances"][1]["instance_uid"] == "1.2.3.101"

    def test_store_then_search(self):
        """Stored instances appear in QIDO-RS search results."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        svc.store_instances(
            study_uid="1.2.3.777",
            instances_data=[
                {"patient_name": "TESTPATIENT", "patient_id": "TP001"}
            ],
        )

        results = svc.search_studies(patient_id="TP001")
        assert len(results) >= 1

        # Check the study UID is in results
        study_uids = [
            r["0020000D"]["Value"][0] for r in results
        ]
        assert "1.2.3.777" in study_uids


class TestDICOMwebQIDORS:
    """Tests for DICOMweb QIDO-RS (search studies and series)."""

    def test_search_studies_empty_registry_returns_mock(self):
        """Empty registry returns mock study results."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        results = svc.search_studies()

        assert isinstance(results, list)
        assert len(results) > 0

        # Each result has Study Instance UID
        for r in results:
            assert "0020000D" in r
            assert r["0020000D"]["vr"] == "UI"

    def test_search_studies_with_modality_filter(self):
        """Modality filter is applied correctly."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        svc.store_instances(
            study_uid="1.2.3.800",
            instances_data=[{"patient_name": "MODTEST"}],
        )

        # SM should match
        results = svc.search_studies(modality="SM")
        assert len(results) >= 1

    def test_search_series_for_study(self):
        """Series search returns results for a study."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        results = svc.search_series("1.2.3.999")

        assert isinstance(results, list)
        assert len(results) > 0

        for r in results:
            assert "0020000E" in r  # Series Instance UID
            assert r["00080060"]["Value"][0] == "SM"

    def test_search_studies_pagination(self):
        """Pagination limit and offset work correctly."""
        from services.dicomweb import DICOMwebService

        svc = DICOMwebService()
        # Store multiple studies
        for i in range(5):
            svc.store_instances(
                study_uid=f"1.2.3.{900 + i}",
                instances_data=[{"patient_name": f"PAGE_{i}"}],
            )

        all_results = svc.search_studies(limit=100)
        page1 = svc.search_studies(limit=2, offset=0)
        page2 = svc.search_studies(limit=2, offset=2)

        assert len(page1) <= 2
        assert len(page2) <= 2
        # Pages should not overlap (unless mock results are mixed in)
        if len(all_results) >= 4:
            assert page1 != page2


# =========================================================================
# #111 — DICOM SR for AI Results
# =========================================================================


class TestDICOMSR:
    """Tests for DICOM Structured Reporting service."""

    def test_create_sr_returns_structure(self):
        """SR creation returns complete TID 1500 structure."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        result = svc.create_measurement_report("slide_sr_01")

        assert result["sr_uid"].startswith("2.25.")
        assert result["template_id"] == "TID_1500"
        assert result["modality"] == "SR"
        assert result["status"] == "mock"
        assert result["sop_class_uid"] == "1.2.840.10008.5.1.4.1.1.88.33"

    def test_sr_deterministic(self):
        """Same slide_id produces same SR UID."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        r1 = svc.create_measurement_report("slide_det_01")
        r2 = svc.create_measurement_report("slide_det_01")
        assert r1["sr_uid"] == r2["sr_uid"]

    def test_sr_has_content_items(self):
        """SR contains content items (TID 1500 tree)."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        result = svc.create_measurement_report("slide_content")

        items = result["content_items"]
        assert isinstance(items, list)
        assert len(items) > 0

    def test_sr_with_custom_detections(self):
        """SR encodes provided detection results."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        detections = [
            {
                "label": "mitosis",
                "confidence": 0.92,
                "bbox": [1000, 2000, 50, 50],
            },
            {
                "label": "tumor",
                "confidence": 0.87,
                "bbox": [3000, 4000, 200, 200],
            },
        ]
        result = svc.create_measurement_report(
            "slide_det",
            detections=detections,
            classifications=None,
        )

        assert result["detections_count"] == 2

        # Find measurement group items
        groups = [
            item
            for item in result["content_items"]
            if item.get("value_type") == "CONTAINER"
            and item.get("concept_name", {}).get("code_value") == "125007"
        ]
        assert len(groups) == 2

    def test_sr_with_custom_classifications(self):
        """SR encodes provided classification results."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        classifications = [
            {
                "diagnosis": "malignant",
                "probability": 0.95,
                "region": "whole slide",
            },
        ]
        result = svc.create_measurement_report(
            "slide_cls",
            detections=[],
            classifications=classifications,
        )

        assert result["classifications_count"] == 1

    def test_sr_detection_group_has_bbox(self):
        """Detection measurement group contains spatial coordinates."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        detections = [
            {
                "label": "tumor",
                "confidence": 0.9,
                "bbox": [100, 200, 50, 60],
            },
        ]
        result = svc.create_measurement_report(
            "slide_bbox",
            detections=detections,
            classifications=[],
        )

        groups = [
            item
            for item in result["content_items"]
            if item.get("value_type") == "CONTAINER"
            and item.get("concept_name", {}).get("code_value") == "125007"
        ]
        assert len(groups) == 1

        # Check for SCOORD in children
        scoord_items = [
            child
            for child in groups[0]["content_items"]
            if child.get("value_type") == "SCOORD"
        ]
        assert len(scoord_items) == 1
        assert scoord_items[0]["graphic_type"] == "POLYLINE"
        assert len(scoord_items[0]["graphic_data"]) == 5  # Closed polygon

    def test_sr_observer_type_device(self):
        """SR marks observer type as Device (AI algorithm)."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        result = svc.create_measurement_report("slide_obs")

        # Find observer type item
        observer_items = [
            item
            for item in result["content_items"]
            if item.get("concept_name", {}).get("code_value") == "121005"
        ]
        assert len(observer_items) == 1
        assert observer_items[0]["code"]["meaning"] == "Device"

    def test_sr_model_info(self):
        """SR includes model name and version."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        result = svc.create_measurement_report(
            "slide_model",
            model_name="TestModel",
            model_version="2.0",
        )

        assert result["model_info"]["name"] == "TestModel"
        assert result["model_info"]["version"] == "2.0"

    def test_sr_snomed_mapping(self):
        """Detection labels map to SNOMED-CT codes."""
        from services.dicom_sr import DICOMSRService

        svc = DICOMSRService()
        code = svc._map_label_to_snomed("mitosis")
        assert code["coding_scheme"] == "SCT"
        assert code["code_value"] == "19665009"

        code2 = svc._map_label_to_snomed("unknown_label")
        assert code2["coding_scheme"] == "SCT"
        assert "unknown_label" in code2["meaning"]


# =========================================================================
# #117 — DICOM Microscopy Annotations Export
# =========================================================================


class TestDICOMAnnotations:
    """Tests for GeoJSON to DICOM annotation conversion."""

    def _sample_geojson(self):
        """Create a sample GeoJSON FeatureCollection."""
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [100, 200],
                                [300, 200],
                                [300, 400],
                                [100, 400],
                                [100, 200],
                            ]
                        ],
                    },
                    "properties": {
                        "label": "tumor",
                        "confidence": 0.92,
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [500, 600],
                    },
                    "properties": {
                        "label": "mitosis",
                        "confidence": 0.88,
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [100, 100],
                            [200, 200],
                            [300, 150],
                        ],
                    },
                    "properties": {
                        "label": "tumor",
                        "confidence": 0.75,
                    },
                },
            ],
        }

    def test_convert_returns_structure(self):
        """Conversion returns complete DICOM annotation structure."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        result = svc.convert_geojson_to_dicom(
            "slide_ann_01", self._sample_geojson()
        )

        assert result["instance_uid"].startswith("2.25.")
        assert result["sop_class_uid"] == "1.2.840.10008.5.1.4.1.1.91.1"
        assert result["status"] == "mock"
        assert "annotation_groups" in result
        assert "conversion_stats" in result

    def test_features_grouped_by_label(self):
        """Features are grouped by label property."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        result = svc.convert_geojson_to_dicom(
            "slide_grp", self._sample_geojson()
        )

        groups = result["annotation_groups"]
        labels = {g["annotation_group_label"] for g in groups}
        assert "tumor" in labels
        assert "mitosis" in labels

    def test_polygon_conversion(self):
        """GeoJSON Polygon converts to DICOM POLYGON graphic type."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
                        ],
                    },
                    "properties": {"label": "region"},
                },
            ],
        }
        result = svc.convert_geojson_to_dicom("slide_poly", geojson)

        groups = result["annotation_groups"]
        assert len(groups) == 1
        annotations = groups[0]["annotations"]
        assert len(annotations) == 1
        assert annotations[0]["graphic_type"] == "POLYGON"
        assert len(annotations[0]["point_coordinates"]) == 5

    def test_point_conversion(self):
        """GeoJSON Point converts to DICOM POINT graphic type."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [500, 600],
                    },
                    "properties": {"label": "cell"},
                },
            ],
        }
        result = svc.convert_geojson_to_dicom("slide_pt", geojson)

        groups = result["annotation_groups"]
        annotations = groups[0]["annotations"]
        assert annotations[0]["graphic_type"] == "POINT"
        assert annotations[0]["point_coordinates"] == [[500, 600]]

    def test_polyline_conversion(self):
        """GeoJSON LineString converts to DICOM POLYLINE graphic type."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[0, 0], [10, 10], [20, 0]],
                    },
                    "properties": {"label": "boundary"},
                },
            ],
        }
        result = svc.convert_geojson_to_dicom("slide_line", geojson)

        annotations = result["annotation_groups"][0]["annotations"]
        assert annotations[0]["graphic_type"] == "POLYLINE"
        assert len(annotations[0]["point_coordinates"]) == 3

    def test_conversion_stats(self):
        """Conversion statistics are accurate."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        result = svc.convert_geojson_to_dicom(
            "slide_stats", self._sample_geojson()
        )

        stats = result["conversion_stats"]
        assert stats["total_features"] == 3
        assert stats["total_groups"] == 2  # tumor, mitosis
        assert stats["processing_time_ms"] >= 0

        # Graphic type counts
        counts = stats["graphic_type_counts"]
        assert "POLYGON" in counts
        assert "POINT" in counts

    def test_empty_geojson_uses_mock(self):
        """Empty GeoJSON features list generates mock features."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        result = svc.convert_geojson_to_dicom(
            "slide_empty", {"type": "FeatureCollection", "features": []}
        )

        # Should have generated mock features
        assert len(result["annotation_groups"]) > 0

    def test_annotation_property_type_mapping(self):
        """Labels map to SNOMED-CT annotation property types."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        prop = svc._map_label_to_property_type("tumor")
        assert prop["coding_scheme"] == "SCT"
        assert prop["code_value"] == "108369006"

    def test_measurements_extraction(self):
        """Measurements are extracted from feature properties."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [100, 200],
                    },
                    "properties": {
                        "label": "cell",
                        "area": 150.5,
                        "confidence": 0.95,
                    },
                },
            ],
        }
        result = svc.convert_geojson_to_dicom("slide_meas", geojson)

        annotations = result["annotation_groups"][0]["annotations"]
        measurements = annotations[0]["measurements"]
        names = [m["name"] for m in measurements]
        assert "Area" in names
        assert "Confidence Score" in names

    def test_deterministic_uids(self):
        """Same slide_id produces same annotation UIDs."""
        from services.dicom_annotations import DICOMAnnotationService

        svc = DICOMAnnotationService()
        r1 = svc.convert_geojson_to_dicom(
            "slide_det_uid", self._sample_geojson()
        )
        r2 = svc.convert_geojson_to_dicom(
            "slide_det_uid", self._sample_geojson()
        )
        assert r1["instance_uid"] == r2["instance_uid"]


# =========================================================================
# UID Generation
# =========================================================================


class TestUIDGeneration:
    """Tests for DICOM UID generation across all services."""

    def test_uid_max_length(self):
        """All generated UIDs are <= 64 characters."""
        from services.dicom_export import _generate_uid as gen_export
        from services.dicom_sr import _generate_uid as gen_sr
        from services.dicomweb import _generate_uid as gen_web

        for gen in [gen_export, gen_sr, gen_web]:
            for seed in ["short", "a" * 100, "x" * 1000, "1.2.3.4.5.6"]:
                uid = gen(seed)
                assert len(uid) <= 64, f"UID too long: {uid} ({len(uid)})"

    def test_uid_valid_characters(self):
        """UIDs contain only digits and dots."""
        from services.dicomweb import _generate_uid

        for seed in ["test", "slide_123", "a.b.c"]:
            uid = _generate_uid(seed)
            for char in uid:
                assert char in "0123456789.", (
                    f"Invalid character '{char}' in UID: {uid}"
                )

    def test_uid_starts_with_2_25(self):
        """UIDs use the 2.25. OID prefix."""
        from services.dicomweb import _generate_uid

        uid = _generate_uid("any_seed")
        assert uid.startswith("2.25.")


# =========================================================================
# API Route Integration (using TestClient)
# =========================================================================


class TestDICOMwebRoutes:
    """Integration tests for DICOMweb API routes."""

    @pytest.fixture(autouse=True)
    def _setup_client(self):
        """Set up test client for route tests."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from routes.dicomweb import router

        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def test_wado_rs_metadata(self):
        """GET instance metadata returns 200 with DICOM JSON."""
        resp = self.client.get(
            "/api/dicomweb/studies/1.2.3/series/1.2.4/instances/1.2.5"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_wado_rs_frame(self):
        """GET frame returns 200 with multipart content."""
        resp = self.client.get(
            "/api/dicomweb/studies/1.2.3/series/1.2.4"
            "/instances/1.2.5/frames/1"
        )
        assert resp.status_code == 200
        assert "multipart/related" in resp.headers["content-type"]

    def test_wado_rs_frame_invalid_number(self):
        """GET frame with number < 1 returns 400."""
        resp = self.client.get(
            "/api/dicomweb/studies/1.2.3/series/1.2.4"
            "/instances/1.2.5/frames/0"
        )
        assert resp.status_code == 400

    def test_stow_rs_store(self):
        """POST store instances returns 200."""
        resp = self.client.post(
            "/api/dicomweb/studies",
            json={
                "study_uid": "1.2.3.888",
                "instances": [{"patient_name": "ROUTETEST"}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["study_uid"] == "1.2.3.888"

    def test_qido_rs_search_studies(self):
        """GET search studies returns 200 with DICOM JSON."""
        resp = self.client.get("/api/dicomweb/studies")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_qido_rs_search_series(self):
        """GET search series returns 200."""
        resp = self.client.get(
            "/api/dicomweb/studies/1.2.3.999/series"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_sr_creation_route(self):
        """POST SR creation returns 200 with TID 1500 structure."""
        resp = self.client.post(
            "/api/dicomweb/sr/test_slide",
            json={
                "detections": [
                    {
                        "label": "tumor",
                        "confidence": 0.9,
                        "bbox": [100, 200, 50, 50],
                    }
                ],
                "classifications": [],
                "model_name": "TestModel",
                "model_version": "1.0",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["template_id"] == "TID_1500"
        assert data["detections_count"] == 1

    def test_annotation_conversion_route(self):
        """POST annotation conversion returns 200."""
        resp = self.client.post(
            "/api/dicomweb/annotations/test_slide",
            json={
                "geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [100, 200],
                            },
                            "properties": {"label": "cell"},
                        }
                    ],
                },
                "annotation_label": "test",
                "patient_name": "TEST",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "mock"
        assert len(data["annotation_groups"]) == 1
