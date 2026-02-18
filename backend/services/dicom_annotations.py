"""
DICOM Microscopy Annotations Export Service

Converts VarunaPoC GeoJSON annotations to DICOM Supplement 222/223
(Microscopy Bulk Simple Annotations) format.

Supports:
    - Polygon graphic type (from GeoJSON Polygon)
    - Point graphic type (from GeoJSON Point)
    - Polyline graphic type (from GeoJSON LineString)
    - Annotation group labeling mapped to DICOM annotation group types

References:
    - DICOM Supplement 222: Microscopy Bulk Simple Annotations
    - DICOM Supplement 223: Microscopy Annotations Storage
    - SOP Class: Microscopy Bulk Simple Annotations Storage
      UID: 1.2.840.10008.5.1.4.1.1.91.1
    - GeoJSON: https://geojson.org/
"""

import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import pydicom

    HAS_PYDICOM = True
except ImportError:
    HAS_PYDICOM = False

# SOP Class UID for Microscopy Bulk Simple Annotations
MICROSCOPY_ANNOTATION_SOP_CLASS = "1.2.840.10008.5.1.4.1.1.91.1"

# DICOM OID prefix
_OID_PREFIX = "1.2.826.0.1.3680043.8.498."

# GeoJSON type to DICOM Graphic Type mapping
_GEOJSON_TO_DICOM_GRAPHIC = {
    "Point": "POINT",
    "LineString": "POLYLINE",
    "Polygon": "POLYGON",
    "MultiPoint": "POINT",
    "MultiLineString": "POLYLINE",
    "MultiPolygon": "POLYGON",
}


def _generate_uid(seed_text: str) -> str:
    """Generate a deterministic DICOM UID from seed text using 2.25. prefix.

    Args:
        seed_text: Input text to derive UID from.

    Returns:
        A valid DICOM UID string (<= 64 characters).
    """
    digest = hashlib.md5(seed_text.encode()).hexdigest()
    decimal_val = str(int(digest, 16))
    uid = f"2.25.{decimal_val}"
    return uid[:64]


def _seed_from_id(identifier: str) -> int:
    """Derive a deterministic integer seed from an identifier string."""
    return int(hashlib.md5(identifier.encode()).hexdigest()[:8], 16)


class DICOMAnnotationService:
    """GeoJSON to DICOM Microscopy Annotations converter.

    Converts VarunaPoC GeoJSON annotation features into DICOM
    Supplement 222/223 Microscopy Bulk Simple Annotations format.

    In mock mode (default), produces deterministic conversion metadata
    without writing actual DICOM files.
    """

    def __init__(self) -> None:
        self._has_pydicom = HAS_PYDICOM
        logger.info(
            "DICOM Annotation service initialized (pydicom=%s)",
            self._has_pydicom,
        )

    def convert_geojson_to_dicom(
        self,
        slide_id: str,
        geojson: Dict[str, Any],
        annotation_label: str = "annotation",
        patient_name: str = "ANONYMOUS",
    ) -> Dict[str, Any]:
        """Convert a GeoJSON FeatureCollection to DICOM annotation format.

        Processes GeoJSON features and groups them by label into DICOM
        Annotation Groups (Supplement 222 structure).

        Args:
            slide_id: Source slide identifier.
            geojson: GeoJSON FeatureCollection dict with features.
            annotation_label: Default label for ungrouped annotations.
            patient_name: Patient name for DICOM metadata.

        Returns:
            Dict containing conversion result with:
                - instance_uid: SOP Instance UID
                - study_uid: Study Instance UID
                - series_uid: Series Instance UID
                - annotation_groups: List of DICOM annotation groups
                - conversion_stats: Conversion statistics
                - status: "mock" or "success"
        """
        seed = _seed_from_id(slide_id)
        start = time.time()

        instance_uid = _generate_uid(f"ann.{slide_id}")
        study_uid = _generate_uid(f"study.{slide_id}")
        series_uid = _generate_uid(f"ann_series.{slide_id}")

        # Parse GeoJSON features
        features = geojson.get("features", [])
        if not features:
            features = self._generate_mock_features(seed)

        # Group features by label
        groups = self._group_features_by_label(features, annotation_label)

        # Convert groups to DICOM annotation groups
        annotation_groups = []
        total_points = 0
        graphic_type_counts: Dict[str, int] = {}

        for group_label, group_features in groups.items():
            dicom_group = self._convert_annotation_group(group_label, group_features, slide_id)
            annotation_groups.append(dicom_group)

            for feat_info in dicom_group.get("annotations", []):
                graphic_type = feat_info.get("graphic_type", "UNKNOWN")
                graphic_type_counts[graphic_type] = graphic_type_counts.get(graphic_type, 0) + 1
                total_points += len(feat_info.get("point_coordinates", []))

        elapsed = (time.time() - start) * 1000

        return {
            "instance_uid": instance_uid,
            "study_uid": study_uid,
            "series_uid": series_uid,
            "sop_class_uid": MICROSCOPY_ANNOTATION_SOP_CLASS,
            "patient": {
                "patient_name": patient_name,
                "patient_id": f"PAT{seed % 100000:05d}",
            },
            "annotation_coordinate_type": "2D",
            "annotation_groups": annotation_groups,
            "conversion_stats": {
                "total_features": len(features),
                "total_groups": len(annotation_groups),
                "total_coordinate_points": total_points,
                "graphic_type_counts": graphic_type_counts,
                "processing_time_ms": elapsed,
            },
            "status": "mock",
        }

    def _group_features_by_label(
        self,
        features: List[Dict[str, Any]],
        default_label: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group GeoJSON features by their label property.

        Args:
            features: List of GeoJSON Feature dicts.
            default_label: Label for features without a label property.

        Returns:
            Dict mapping label -> list of features.
        """
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for feature in features:
            props = feature.get("properties", {}) or {}
            label = props.get("label", default_label)
            if label not in groups:
                groups[label] = []
            groups[label].append(feature)
        return groups

    def _convert_annotation_group(
        self,
        label: str,
        features: List[Dict[str, Any]],
        slide_id: str,
    ) -> Dict[str, Any]:
        """Convert a group of GeoJSON features to a DICOM Annotation Group.

        Each group corresponds to a single Annotation Group in the
        DICOM Microscopy Bulk Simple Annotations IOD.

        Args:
            label: Annotation group label.
            features: List of GeoJSON features in this group.
            slide_id: Source slide identifier.

        Returns:
            Dict representing a DICOM Annotation Group.
        """
        group_uid = _generate_uid(f"anngroup.{slide_id}.{label}")

        # Map label to DICOM annotation property type
        property_type = self._map_label_to_property_type(label)

        annotations = []
        for feature in features:
            converted = self._convert_feature(feature)
            if converted:
                annotations.append(converted)

        return {
            "annotation_group_uid": group_uid,
            "annotation_group_label": label,
            "annotation_group_description": f"Annotations labeled '{label}'",
            "annotation_property_type": property_type,
            "annotation_property_category": {
                "code_value": "91723000",
                "coding_scheme": "SCT",
                "meaning": "Anatomical structure",
            },
            "number_of_annotations": len(annotations),
            "graphic_type": (annotations[0]["graphic_type"] if annotations else "POLYGON"),
            "annotations": annotations,
        }

    def _convert_feature(self, feature: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a single GeoJSON Feature to DICOM annotation format.

        Extracts geometry coordinates and maps GeoJSON geometry type
        to DICOM graphic type.

        Args:
            feature: GeoJSON Feature dict.

        Returns:
            Dict with graphic_type and point_coordinates, or None if
            the geometry type is not supported.
        """
        geometry = feature.get("geometry", {})
        geom_type = geometry.get("type", "")
        coordinates = geometry.get("coordinates", [])

        graphic_type = _GEOJSON_TO_DICOM_GRAPHIC.get(geom_type)
        if graphic_type is None:
            logger.warning("Unsupported GeoJSON type: %s", geom_type)
            return None

        # Extract coordinate points based on geometry type
        points = self._extract_points(geom_type, coordinates)

        props = feature.get("properties", {}) or {}

        return {
            "graphic_type": graphic_type,
            "point_coordinates": points,
            "measurements": self._extract_measurements(props),
        }

    def _extract_points(
        self,
        geom_type: str,
        coordinates: Any,
    ) -> List[List[float]]:
        """Extract 2D coordinate points from GeoJSON coordinates.

        Handles the different nesting levels of GeoJSON coordinate arrays.

        Args:
            geom_type: GeoJSON geometry type.
            coordinates: GeoJSON coordinates array.

        Returns:
            Flat list of [x, y] coordinate pairs.
        """
        extractor = {
            "Point": self._extract_point,
            "LineString": self._extract_flat_coords,
            "MultiPoint": self._extract_flat_coords,
            "Polygon": self._extract_polygon,
            "MultiLineString": self._extract_multi_line,
            "MultiPolygon": self._extract_multi_polygon,
        }.get(geom_type)

        if extractor is None:
            return []
        return extractor(coordinates)

    def _extract_point(self, coordinates: Any) -> List[List[float]]:
        """Extract a single point: [x, y] -> [[x, y]]."""
        return [coordinates[:2]] if len(coordinates) >= 2 else []

    def _extract_flat_coords(self, coordinates: Any) -> List[List[float]]:
        """Extract flat coordinate list: [[x, y], ...] -> [[x, y], ...]."""
        return [c[:2] for c in coordinates if len(c) >= 2]

    def _extract_polygon(self, coordinates: Any) -> List[List[float]]:
        """Extract outer ring of polygon: [[[x, y], ...]] -> [[x, y], ...]."""
        if coordinates and len(coordinates) > 0:
            ring = coordinates[0]
            return [c[:2] for c in ring if len(c) >= 2]
        return []

    def _extract_multi_line(self, coordinates: Any) -> List[List[float]]:
        """Extract points from all lines in a MultiLineString."""
        points: List[List[float]] = []
        for line in coordinates:
            points.extend(c[:2] for c in line if len(c) >= 2)
        return points

    def _extract_multi_polygon(self, coordinates: Any) -> List[List[float]]:
        """Extract outer rings from all polygons in a MultiPolygon."""
        points: List[List[float]] = []
        for polygon in coordinates:
            if polygon:
                ring = polygon[0]
                points.extend(c[:2] for c in ring if len(c) >= 2)
        return points

    def _extract_measurements(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract measurement values from GeoJSON feature properties.

        Looks for common measurement properties like area, perimeter,
        confidence, etc.

        Args:
            properties: GeoJSON feature properties dict.

        Returns:
            List of measurement dicts with name, value, unit.
        """
        measurements = []
        measurement_keys = {
            "area": {"unit": "mm2", "meaning": "Area"},
            "perimeter": {"unit": "mm", "meaning": "Perimeter"},
            "confidence": {"unit": "1", "meaning": "Confidence Score"},
            "score": {"unit": "1", "meaning": "Algorithm Score"},
        }

        for key, meta in measurement_keys.items():
            if key in properties:
                measurements.append(
                    {
                        "name": meta["meaning"],
                        "value": float(properties[key]),
                        "unit": meta["unit"],
                    }
                )

        return measurements

    def _map_label_to_property_type(self, label: str) -> Dict[str, str]:
        """Map an annotation label to a DICOM Annotation Property Type code.

        Args:
            label: Annotation label string.

        Returns:
            Dict with code_value, coding_scheme, meaning.
        """
        mapping = {
            "tumor": {
                "code_value": "108369006",
                "coding_scheme": "SCT",
                "meaning": "Neoplasm",
            },
            "necrosis": {
                "code_value": "6574001",
                "coding_scheme": "SCT",
                "meaning": "Necrosis",
            },
            "stroma": {
                "code_value": "26036001",
                "coding_scheme": "SCT",
                "meaning": "Stroma",
            },
            "epithelium": {
                "code_value": "31610004",
                "coding_scheme": "SCT",
                "meaning": "Epithelium",
            },
            "lymphocyte": {
                "code_value": "56972008",
                "coding_scheme": "SCT",
                "meaning": "Lymphocyte",
            },
            "mitosis": {
                "code_value": "19665009",
                "coding_scheme": "SCT",
                "meaning": "Mitotic figure",
            },
        }
        return mapping.get(
            label.lower(),
            {
                "code_value": "404684003",
                "coding_scheme": "SCT",
                "meaning": f"Finding ({label})",
            },
        )

    # =========================================================================
    # Mock Data Generation
    # =========================================================================

    def _generate_mock_features(self, seed: int) -> List[Dict[str, Any]]:
        """Generate mock GeoJSON features from a seed.

        Creates a small set of deterministic features for testing.

        Args:
            seed: Integer seed for deterministic generation.

        Returns:
            List of GeoJSON Feature dicts.
        """
        labels = ["tumor", "stroma", "necrosis", "lymphocyte"]
        geom_types = ["Polygon", "Point", "LineString"]
        count = (seed % 5) + 3  # 3-7 features

        features = []
        for i in range(count):
            s = seed + i * 4219  # Prime step
            label = labels[i % len(labels)]
            geom_type = geom_types[i % len(geom_types)]

            cx = (s * 13) % 90000
            cy = (s * 17) % 70000

            if geom_type == "Point":
                geometry = {
                    "type": "Point",
                    "coordinates": [cx, cy],
                }
            elif geom_type == "LineString":
                geometry = {
                    "type": "LineString",
                    "coordinates": [
                        [cx, cy],
                        [cx + 200, cy + 100],
                        [cx + 400, cy],
                    ],
                }
            else:  # Polygon
                w = (s % 300) + 100
                h = (s % 300) + 100
                geometry = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [cx, cy],
                            [cx + w, cy],
                            [cx + w, cy + h],
                            [cx, cy + h],
                            [cx, cy],
                        ]
                    ],
                }

            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "label": label,
                        "confidence": round(0.5 + (s % 50) / 100.0, 3),
                    },
                }
            )

        return features
