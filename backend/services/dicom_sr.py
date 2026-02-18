"""
DICOM Structured Reporting Service for AI Results

Encodes ML predictions (detections, classifications) into DICOM SR
following TID 1500 (Measurement Report) template structure.

References:
    - DICOM SR: PS3.16 (Content Mapping Resource)
    - TID 1500: Measurement Report
    - TID 1501: Measurement Group
    - CID 7021: Measurement Report Document Titles
    - SCT: SNOMED-CT concept codes
"""

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import pydicom

    HAS_PYDICOM = True
except ImportError:
    HAS_PYDICOM = False

# SOP Class UID for Comprehensive SR
COMPREHENSIVE_SR_SOP_CLASS = "1.2.840.10008.5.1.4.1.1.88.33"

# DICOM OID prefix
_OID_PREFIX = "1.2.826.0.1.3680043.8.498."


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


class DICOMSRService:
    """DICOM Structured Reporting service for ML predictions.

    Generates DICOM SR documents encoding AI detection and classification
    results following TID 1500 (Measurement Report) structure.

    In mock mode (default), produces deterministic SR JSON structures
    derived from slide_id hashes.
    """

    def __init__(self) -> None:
        self._has_pydicom = HAS_PYDICOM
        logger.info("DICOM SR service initialized (pydicom=%s)", self._has_pydicom)

    def create_measurement_report(
        self,
        slide_id: str,
        detections: Optional[List[Dict[str, Any]]] = None,
        classifications: Optional[List[Dict[str, Any]]] = None,
        model_name: str = "VarunaPoC-ML",
        model_version: str = "1.0",
    ) -> Dict[str, Any]:
        """Create a TID 1500 Measurement Report SR from ML predictions.

        Encodes detection bounding boxes and classification results as
        DICOM SR content items following the TID 1500 template.

        Args:
            slide_id: Source slide identifier.
            detections: List of detection results, each with keys:
                - label: str (e.g., "mitosis", "tumor")
                - confidence: float (0-1)
                - bbox: [x, y, width, height] in pixel coordinates
            classifications: List of classification results, each with:
                - diagnosis: str (e.g., "malignant", "benign")
                - probability: float (0-1)
                - region: optional str description
            model_name: Name of the ML model.
            model_version: Version of the ML model.

        Returns:
            Dict containing the SR document structure with:
                - sr_uid: SOP Instance UID
                - study_uid: Study Instance UID
                - series_uid: Series Instance UID
                - template: TID 1500 structure
                - content_items: Encoded measurement groups
                - status: "mock" or "success"
        """
        seed = _seed_from_id(slide_id)
        start = time.time()

        sr_uid = _generate_uid(f"sr.{slide_id}")
        study_uid = _generate_uid(f"study.{slide_id}")
        series_uid = _generate_uid(f"sr_series.{slide_id}")

        # Use provided data or generate mock detections/classifications
        if detections is None:
            detections = self._generate_mock_detections(seed)
        if classifications is None:
            classifications = self._generate_mock_classifications(seed)

        # Build TID 1500 content tree
        content_items = self._build_tid_1500(
            slide_id=slide_id,
            detections=detections,
            classifications=classifications,
            model_name=model_name,
            model_version=model_version,
            seed=seed,
        )

        elapsed = (time.time() - start) * 1000

        return {
            "sr_uid": sr_uid,
            "study_uid": study_uid,
            "series_uid": series_uid,
            "sop_class_uid": COMPREHENSIVE_SR_SOP_CLASS,
            "modality": "SR",
            "template_id": "TID_1500",
            "template_name": "Measurement Report",
            "document_title": {
                "code_value": "126000",
                "coding_scheme": "DCM",
                "meaning": "Imaging Measurement Report",
            },
            "patient": {
                "patient_name": "ANONYMOUS",
                "patient_id": f"PAT{seed % 100000:05d}",
            },
            "study_date": datetime.now(tz=timezone.utc).strftime("%Y%m%d"),
            "content_items": content_items,
            "detections_count": len(detections),
            "classifications_count": len(classifications),
            "model_info": {
                "name": model_name,
                "version": model_version,
                "algorithm_type": "AI_DETECTION_CLASSIFICATION",
            },
            "processing_time_ms": elapsed,
            "status": "mock",
        }

    def _build_tid_1500(
        self,
        slide_id: str,
        detections: List[Dict[str, Any]],
        classifications: List[Dict[str, Any]],
        model_name: str,
        model_version: str,
        seed: int,
    ) -> List[Dict[str, Any]]:
        """Build TID 1500 Measurement Report content tree.

        Structure:
            CONTAINER (Measurement Report) [TID 1500]
            +-- CODE (Language of Content)
            +-- CODE (Observation Context - Observer Type)
            +-- TEXT (Observation Context - Algorithm Name)
            +-- CONTAINER (Image Library) [TID 1600]
            +-- CONTAINER (Measurement Group) [TID 1501] (per detection)
            |   +-- CODE (Tracking Identifier)
            |   +-- UIDREF (Tracking UID)
            |   +-- SCOORD (Graphic Data - bounding box)
            |   +-- NUM (Confidence Score)
            +-- CONTAINER (Qualitative Evaluation) (per classification)
                +-- CODE (Finding)
                +-- NUM (Probability)
        """
        items = []

        # Language of Content Item and Value
        items.append(
            {
                "relationship_type": "HAS CONCEPT MOD",
                "value_type": "CODE",
                "concept_name": {
                    "code_value": "121049",
                    "coding_scheme": "DCM",
                    "meaning": "Language of Content Item and Value",
                },
                "code": {
                    "code_value": "eng",
                    "coding_scheme": "RFC5646",
                    "meaning": "English",
                },
            }
        )

        # Observer Type = Device (AI algorithm)
        items.append(
            {
                "relationship_type": "HAS OBS CONTEXT",
                "value_type": "CODE",
                "concept_name": {
                    "code_value": "121005",
                    "coding_scheme": "DCM",
                    "meaning": "Observer Type",
                },
                "code": {
                    "code_value": "121007",
                    "coding_scheme": "DCM",
                    "meaning": "Device",
                },
            }
        )

        # Algorithm Identification
        items.append(
            {
                "relationship_type": "HAS OBS CONTEXT",
                "value_type": "TEXT",
                "concept_name": {
                    "code_value": "111001",
                    "coding_scheme": "DCM",
                    "meaning": "Algorithm Name",
                },
                "text_value": f"{model_name} v{model_version}",
            }
        )

        # Measurement Groups (one per detection) - TID 1501
        for i, det in enumerate(detections):
            group = self._build_detection_group(det, i, slide_id)
            items.append(group)

        # Qualitative Evaluations (one per classification)
        for i, cls in enumerate(classifications):
            eval_item = self._build_classification_evaluation(cls, i)
            items.append(eval_item)

        return items

    def _build_detection_group(
        self,
        detection: Dict[str, Any],
        index: int,
        slide_id: str,
    ) -> Dict[str, Any]:
        """Build TID 1501 Measurement Group for a detection.

        Args:
            detection: Detection dict with label, confidence, bbox.
            index: Detection index.
            slide_id: Source slide ID.

        Returns:
            CONTAINER content item with measurement group.
        """
        label = detection.get("label", "finding")
        confidence = detection.get("confidence", 0.0)
        bbox = detection.get("bbox", [0, 0, 100, 100])
        tracking_uid = _generate_uid(f"tracking.{slide_id}.{index}")

        # Map label to SNOMED concept code
        finding_code = self._map_label_to_snomed(label)

        children = []

        # Tracking Identifier
        children.append(
            {
                "relationship_type": "HAS OBS CONTEXT",
                "value_type": "TEXT",
                "concept_name": {
                    "code_value": "112039",
                    "coding_scheme": "DCM",
                    "meaning": "Tracking Identifier",
                },
                "text_value": f"{label}_{index}",
            }
        )

        # Tracking UID
        children.append(
            {
                "relationship_type": "HAS OBS CONTEXT",
                "value_type": "UIDREF",
                "concept_name": {
                    "code_value": "112040",
                    "coding_scheme": "DCM",
                    "meaning": "Tracking Unique Identifier",
                },
                "uid_value": tracking_uid,
            }
        )

        # Finding (coded concept for what was detected)
        children.append(
            {
                "relationship_type": "CONTAINS",
                "value_type": "CODE",
                "concept_name": {
                    "code_value": "121071",
                    "coding_scheme": "DCM",
                    "meaning": "Finding",
                },
                "code": finding_code,
            }
        )

        # Spatial Coordinates (bounding box as POLYLINE)
        x, y, w, h = bbox
        children.append(
            {
                "relationship_type": "CONTAINS",
                "value_type": "SCOORD",
                "concept_name": {
                    "code_value": "111030",
                    "coding_scheme": "DCM",
                    "meaning": "Image Region",
                },
                "graphic_type": "POLYLINE",
                "graphic_data": [
                    [x, y],
                    [x + w, y],
                    [x + w, y + h],
                    [x, y + h],
                    [x, y],  # Close polygon
                ],
            }
        )

        # Confidence Score as NUM
        children.append(
            {
                "relationship_type": "CONTAINS",
                "value_type": "NUM",
                "concept_name": {
                    "code_value": "111001",
                    "coding_scheme": "DCM",
                    "meaning": "Algorithm Score",
                },
                "numeric_value": confidence,
                "unit": {
                    "code_value": "1",
                    "coding_scheme": "UCUM",
                    "meaning": "no units",
                },
            }
        )

        return {
            "relationship_type": "CONTAINS",
            "value_type": "CONTAINER",
            "concept_name": {
                "code_value": "125007",
                "coding_scheme": "DCM",
                "meaning": "Measurement Group",
            },
            "content_items": children,
        }

    def _build_classification_evaluation(
        self,
        classification: Dict[str, Any],
        index: int,
    ) -> Dict[str, Any]:
        """Build a qualitative evaluation content item for a classification.

        Args:
            classification: Classification dict with diagnosis, probability.
            index: Classification index.

        Returns:
            CONTAINER content item with evaluation.
        """
        diagnosis = classification.get("diagnosis", "unknown")
        probability = classification.get("probability", 0.0)
        region = classification.get("region", "whole slide")

        finding_code = self._map_diagnosis_to_snomed(diagnosis)

        children = []

        # Finding (diagnosis code)
        children.append(
            {
                "relationship_type": "CONTAINS",
                "value_type": "CODE",
                "concept_name": {
                    "code_value": "121071",
                    "coding_scheme": "DCM",
                    "meaning": "Finding",
                },
                "code": finding_code,
            }
        )

        # Probability as NUM
        children.append(
            {
                "relationship_type": "CONTAINS",
                "value_type": "NUM",
                "concept_name": {
                    "code_value": "111001",
                    "coding_scheme": "DCM",
                    "meaning": "Algorithm Score",
                },
                "numeric_value": probability,
                "unit": {
                    "code_value": "1",
                    "coding_scheme": "UCUM",
                    "meaning": "no units",
                },
            }
        )

        # Region description
        children.append(
            {
                "relationship_type": "HAS PROPERTIES",
                "value_type": "TEXT",
                "concept_name": {
                    "code_value": "121106",
                    "coding_scheme": "DCM",
                    "meaning": "Comment",
                },
                "text_value": f"Region: {region}",
            }
        )

        return {
            "relationship_type": "CONTAINS",
            "value_type": "CONTAINER",
            "concept_name": {
                "code_value": "C0034375",
                "coding_scheme": "UMLS",
                "meaning": "Qualitative Evaluation",
            },
            "content_items": children,
        }

    # =========================================================================
    # Mock Data Generation
    # =========================================================================

    def _generate_mock_detections(self, seed: int) -> List[Dict[str, Any]]:
        """Generate mock detection results from a seed."""
        labels = ["mitosis", "tumor", "necrosis", "lymphocyte"]
        count = (seed % 4) + 2  # 2-5 detections
        detections = []
        for i in range(count):
            s = seed + i * 7919  # Prime step for variety
            detections.append(
                {
                    "label": labels[i % len(labels)],
                    "confidence": round(0.5 + (s % 50) / 100.0, 3),
                    "bbox": [
                        (s * 13) % 90000,
                        (s * 17) % 70000,
                        (s % 500) + 100,
                        (s % 500) + 100,
                    ],
                }
            )
        return detections

    def _generate_mock_classifications(self, seed: int) -> List[Dict[str, Any]]:
        """Generate mock classification results from a seed."""
        diagnoses = ["malignant", "benign", "uncertain"]
        count = (seed % 2) + 1  # 1-2 classifications
        classifications = []
        for i in range(count):
            s = seed + i * 6271
            classifications.append(
                {
                    "diagnosis": diagnoses[s % len(diagnoses)],
                    "probability": round(0.4 + (s % 60) / 100.0, 3),
                    "region": f"region_{i}",
                }
            )
        return classifications

    # =========================================================================
    # Code Mapping
    # =========================================================================

    def _map_label_to_snomed(self, label: str) -> Dict[str, str]:
        """Map a detection label to a SNOMED-CT concept code.

        Args:
            label: Detection label string.

        Returns:
            Dict with code_value, coding_scheme, meaning.
        """
        mapping = {
            "mitosis": {
                "code_value": "19665009",
                "coding_scheme": "SCT",
                "meaning": "Mitotic figure",
            },
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
            "lymphocyte": {
                "code_value": "56972008",
                "coding_scheme": "SCT",
                "meaning": "Lymphocyte",
            },
        }
        return mapping.get(
            label,
            {
                "code_value": "404684003",
                "coding_scheme": "SCT",
                "meaning": f"Finding ({label})",
            },
        )

    def _map_diagnosis_to_snomed(self, diagnosis: str) -> Dict[str, str]:
        """Map a diagnosis label to a SNOMED-CT concept code.

        Args:
            diagnosis: Diagnosis string.

        Returns:
            Dict with code_value, coding_scheme, meaning.
        """
        mapping = {
            "malignant": {
                "code_value": "86049000",
                "coding_scheme": "SCT",
                "meaning": "Malignant neoplasm",
            },
            "benign": {
                "code_value": "20376005",
                "coding_scheme": "SCT",
                "meaning": "Benign neoplasm",
            },
            "uncertain": {
                "code_value": "64572001",
                "coding_scheme": "SCT",
                "meaning": "Uncertain behavior neoplasm",
            },
        }
        return mapping.get(
            diagnosis,
            {
                "code_value": "404684003",
                "coding_scheme": "SCT",
                "meaning": f"Finding ({diagnosis})",
            },
        )
