"""
DICOMweb Service - WADO-RS, STOW-RS, QIDO-RS

Implements DICOMweb RESTful services for whole-slide images:
- WADO-RS: Web Access to DICOM Objects (Retrieve)
- STOW-RS: Store Over the Web (Store)
- QIDO-RS: Query based on ID for DICOM Objects (Search)

All endpoints operate in mock mode by default, returning deterministic
responses derived from input identifiers.

References:
    - DICOMweb: https://www.dicomstandard.org/using/dicomweb
    - WADO-RS: PS3.18 Section 10.4
    - STOW-RS: PS3.18 Section 10.5
    - QIDO-RS: PS3.18 Section 10.6
    - VL Whole Slide Microscopy Image: 1.2.840.10008.5.1.4.1.1.77.1.6
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

# DICOM OID prefix for generated UIDs
_OID_PREFIX = "1.2.826.0.1.3680043.8.498."

# SOP Class UIDs
VL_WHOLE_SLIDE_MICROSCOPY_IMAGE = "1.2.840.10008.5.1.4.1.1.77.1.6"


def _generate_uid(seed_text: str) -> str:
    """Generate a deterministic DICOM UID from seed text using 2.25. prefix.

    Uses the MD5 hash converted to a decimal integer appended to 2.25.
    to produce a valid DICOM UID (max 64 characters).

    Args:
        seed_text: Input text to derive UID from.

    Returns:
        A valid DICOM UID string.
    """
    digest = hashlib.md5(seed_text.encode()).hexdigest()
    # Convert hex to decimal integer for 2.25. prefix standard
    decimal_val = str(int(digest, 16))
    uid = f"2.25.{decimal_val}"
    # DICOM UIDs must be <= 64 characters
    return uid[:64]


def _seed_from_id(identifier: str) -> int:
    """Derive a deterministic integer seed from an identifier string."""
    return int(hashlib.md5(identifier.encode()).hexdigest()[:8], 16)


def _generate_mock_jpeg_frame(seed: int) -> bytes:
    """Generate a small deterministic JPEG-like frame for mock mode.

    Creates a minimal valid JPEG file with a solid color derived from seed.

    Args:
        seed: Integer seed for deterministic color.

    Returns:
        Bytes of a minimal JPEG image.
    """
    # Generate a minimal 1x1 JPEG (smallest valid JPEG)
    # SOI + APP0 + DQT + SOF0 + DHT + SOS + image data + EOI
    # For simplicity, return a pre-built minimal JPEG with color from seed
    color_byte = (seed >> 16) & 0xFF

    # Minimal valid JPEG: SOI marker, then a trivially small image
    # This is a 1x1 pixel JPEG constructed from raw bytes
    jpeg_header = bytes(
        [
            0xFF,
            0xD8,  # SOI
            0xFF,
            0xE0,  # APP0
            0x00,
            0x10,  # Length
            0x4A,
            0x46,
            0x49,
            0x46,
            0x00,  # JFIF\0
            0x01,
            0x01,  # Version 1.1
            0x00,  # Aspect ratio units (0 = no units)
            0x00,
            0x01,  # X density
            0x00,
            0x01,  # Y density
            0x00,
            0x00,  # No thumbnail
            0xFF,
            0xDB,  # DQT
            0x00,
            0x43,  # Length 67
            0x00,  # Table 0, 8-bit
        ]
    )
    # Quantization table (all 1s for simplicity)
    qt = bytes([1] * 64)
    sof = bytes(
        [
            0xFF,
            0xC0,  # SOF0
            0x00,
            0x0B,  # Length 11
            0x08,  # 8 bits precision
            0x00,
            0x01,  # Height 1
            0x00,
            0x01,  # Width 1
            0x01,  # 1 component
            0x01,  # Component ID 1
            0x11,  # Sampling 1x1
            0x00,  # Quant table 0
        ]
    )
    # Minimal DHT (Huffman table for DC)
    dht = bytes(
        [
            0xFF,
            0xC4,  # DHT
            0x00,
            0x1F,  # Length 31
            0x00,  # DC table 0
            0x00,
            0x01,
            0x05,
            0x01,
            0x01,
            0x01,
            0x01,
            0x01,
            0x01,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
        ]
    )
    # SOS + minimal scan data + EOI
    sos = bytes(
        [
            0xFF,
            0xDA,  # SOS
            0x00,
            0x08,  # Length 8
            0x01,  # 1 component
            0x01,  # Component 1
            0x00,  # DC/AC table 0/0
            0x00,
            0x3F,
            0x00,  # Spectral selection
            color_byte & 0x7F,  # Scan data byte (seed-derived, avoid 0xFF)
            0xFF,
            0xD9,  # EOI
        ]
    )

    return jpeg_header + qt + sof + dht + sos


class DICOMwebService:
    """DICOMweb WADO-RS, STOW-RS, and QIDO-RS service.

    Operates in mock mode by default, providing deterministic responses
    for testing and development. When pydicom is available and real
    DICOM files are provided, can operate on actual DICOM data.
    """

    def __init__(self) -> None:
        self._has_pydicom = HAS_PYDICOM
        # In-memory study/series registry for STOW-RS mock mode
        self._studies: Dict[str, Dict[str, Any]] = {}
        self._series: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, Dict[str, Any]] = {}
        logger.info("DICOMweb service initialized (pydicom=%s)", self._has_pydicom)

    # =========================================================================
    # WADO-RS: Retrieve
    # =========================================================================

    def retrieve_instance_metadata(
        self,
        study_uid: str,
        series_uid: str,
        instance_uid: str,
    ) -> List[Dict[str, Any]]:
        """Retrieve DICOM JSON metadata for an instance (WADO-RS).

        Returns DICOM JSON Model (PS3.18 F.2) metadata for the
        requested instance.

        Args:
            study_uid: Study Instance UID.
            series_uid: Series Instance UID.
            instance_uid: SOP Instance UID.

        Returns:
            List with one DICOM JSON metadata object.
        """
        seed = _seed_from_id(instance_uid)

        # Generate deterministic metadata
        metadata = {
            # SOP Class UID - VL Whole Slide Microscopy Image
            "00080016": {
                "vr": "UI",
                "Value": [VL_WHOLE_SLIDE_MICROSCOPY_IMAGE],
            },
            # SOP Instance UID
            "00080018": {
                "vr": "UI",
                "Value": [instance_uid],
            },
            # Study Instance UID
            "0020000D": {
                "vr": "UI",
                "Value": [study_uid],
            },
            # Series Instance UID
            "0020000E": {
                "vr": "UI",
                "Value": [series_uid],
            },
            # Modality = SM (Slide Microscopy)
            "00080060": {
                "vr": "CS",
                "Value": ["SM"],
            },
            # Patient Name
            "00100010": {
                "vr": "PN",
                "Value": [{"Alphabetic": "ANONYMOUS"}],
            },
            # Patient ID
            "00100020": {
                "vr": "LO",
                "Value": [f"PAT{seed % 100000:05d}"],
            },
            # Study Date
            "00080020": {
                "vr": "DA",
                "Value": ["20250101"],
            },
            # Image Type
            "00080008": {
                "vr": "CS",
                "Value": ["ORIGINAL", "PRIMARY", "VOLUME", "NONE"],
            },
            # Rows
            "00280010": {
                "vr": "US",
                "Value": [256],
            },
            # Columns
            "00280011": {
                "vr": "US",
                "Value": [256],
            },
            # Bits Allocated
            "00280100": {
                "vr": "US",
                "Value": [8],
            },
            # Bits Stored
            "00280101": {
                "vr": "US",
                "Value": [8],
            },
            # High Bit
            "00280102": {
                "vr": "US",
                "Value": [7],
            },
            # Samples Per Pixel
            "00280002": {
                "vr": "US",
                "Value": [3],
            },
            # Photometric Interpretation
            "00280004": {
                "vr": "CS",
                "Value": ["YBR_FULL_422"],
            },
            # Total Pixel Matrix Columns
            "00480006": {
                "vr": "UL",
                "Value": [100000],
            },
            # Total Pixel Matrix Rows
            "00480007": {
                "vr": "UL",
                "Value": [80000],
            },
            # Number of Frames
            "00280008": {
                "vr": "IS",
                "Value": [str((seed % 50) + 10)],
            },
        }

        return [metadata]

    def retrieve_frame(
        self,
        study_uid: str,
        series_uid: str,
        instance_uid: str,
        frame_number: int,
    ) -> bytes:
        """Retrieve a single frame (tile) as JPEG bytes (WADO-RS).

        In mock mode, returns a small deterministic JPEG image.

        Args:
            study_uid: Study Instance UID.
            series_uid: Series Instance UID.
            instance_uid: SOP Instance UID.
            frame_number: 1-based frame number.

        Returns:
            JPEG bytes for the requested frame.
        """
        seed = _seed_from_id(f"{instance_uid}.{frame_number}")
        return _generate_mock_jpeg_frame(seed)

    # =========================================================================
    # STOW-RS: Store
    # =========================================================================

    def store_instances(
        self,
        study_uid: Optional[str] = None,
        instances_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Store DICOM instances (STOW-RS).

        In mock mode, registers instances in the in-memory registry
        and returns a success response.

        Args:
            study_uid: Optional Study Instance UID. If None, a new one
                is generated.
            instances_data: List of instance metadata dicts to store.

        Returns:
            STOW-RS response with stored instance references.
        """
        if study_uid is None:
            study_uid = _generate_uid(f"study.{time.time()}")

        stored_refs = []
        now = datetime.now(tz=timezone.utc)

        if instances_data:
            for inst in instances_data:
                series_uid = inst.get(
                    "series_uid",
                    _generate_uid(f"series.{study_uid}.{time.time()}"),
                )
                instance_uid = inst.get(
                    "instance_uid",
                    _generate_uid(f"instance.{study_uid}.{time.time()}"),
                )

                # Register in memory
                self._register_instance(study_uid, series_uid, instance_uid, inst, now)

                stored_refs.append(
                    {
                        "study_uid": study_uid,
                        "series_uid": series_uid,
                        "instance_uid": instance_uid,
                        "url": (
                            f"/api/dicomweb/studies/{study_uid}"
                            f"/series/{series_uid}"
                            f"/instances/{instance_uid}"
                        ),
                    }
                )
        else:
            # No instances provided, just register an empty study
            series_uid = _generate_uid(f"series.{study_uid}.default")
            instance_uid = _generate_uid(f"instance.{study_uid}.default")
            self._register_instance(study_uid, series_uid, instance_uid, {}, now)
            stored_refs.append(
                {
                    "study_uid": study_uid,
                    "series_uid": series_uid,
                    "instance_uid": instance_uid,
                    "url": (
                        f"/api/dicomweb/studies/{study_uid}"
                        f"/series/{series_uid}"
                        f"/instances/{instance_uid}"
                    ),
                }
            )

        return {
            "status": "success",
            "study_uid": study_uid,
            "stored_instances": stored_refs,
            "stored_count": len(stored_refs),
            "timestamp": now.isoformat(),
        }

    def _register_instance(
        self,
        study_uid: str,
        series_uid: str,
        instance_uid: str,
        metadata: Dict[str, Any],
        timestamp: datetime,
    ) -> None:
        """Register an instance in the in-memory registry."""
        ts_str = timestamp.isoformat()

        if study_uid not in self._studies:
            self._studies[study_uid] = {
                "study_uid": study_uid,
                "patient_name": metadata.get("patient_name", "ANONYMOUS"),
                "patient_id": metadata.get("patient_id", "UNKNOWN"),
                "study_date": metadata.get("study_date", timestamp.strftime("%Y%m%d")),
                "modality": "SM",
                "series_uids": [],
                "created_at": ts_str,
            }

        if series_uid not in self._studies[study_uid]["series_uids"]:
            self._studies[study_uid]["series_uids"].append(series_uid)

        if series_uid not in self._series:
            self._series[series_uid] = {
                "series_uid": series_uid,
                "study_uid": study_uid,
                "modality": "SM",
                "series_description": metadata.get("series_description", "WSI Series"),
                "instance_uids": [],
                "created_at": ts_str,
            }

        if instance_uid not in self._series[series_uid]["instance_uids"]:
            self._series[series_uid]["instance_uids"].append(instance_uid)

        self._instances[instance_uid] = {
            "instance_uid": instance_uid,
            "series_uid": series_uid,
            "study_uid": study_uid,
            "sop_class_uid": VL_WHOLE_SLIDE_MICROSCOPY_IMAGE,
            "metadata": metadata,
            "created_at": ts_str,
        }

    # =========================================================================
    # QIDO-RS: Search
    # =========================================================================

    def search_studies(
        self,
        patient_name: Optional[str] = None,
        patient_id: Optional[str] = None,
        study_date: Optional[str] = None,
        modality: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search for studies (QIDO-RS).

        Returns DICOM JSON formatted study-level results.

        Args:
            patient_name: Filter by patient name (substring match).
            patient_id: Filter by patient ID (exact match).
            study_date: Filter by study date (YYYYMMDD).
            modality: Filter by modality (e.g., "SM").
            limit: Maximum number of results.
            offset: Result offset for pagination.

        Returns:
            List of DICOM JSON study-level objects.
        """
        results = []

        for _study_uid, study in self._studies.items():
            # Apply filters
            if patient_name and patient_name.upper() not in study.get("patient_name", "").upper():
                continue
            if patient_id and study.get("patient_id") != patient_id:
                continue
            if study_date and study.get("study_date") != study_date:
                continue
            if modality and study.get("modality") != modality:
                continue

            results.append(self._study_to_dicom_json(study))

        # If no stored studies, return mock results
        if not results and not self._studies:
            results = self._generate_mock_studies()

        # Apply pagination
        return results[offset : offset + limit]

    def search_series(
        self,
        study_uid: str,
        modality: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search for series within a study (QIDO-RS).

        Args:
            study_uid: Study Instance UID to search within.
            modality: Filter by modality.
            limit: Maximum number of results.
            offset: Result offset for pagination.

        Returns:
            List of DICOM JSON series-level objects.
        """
        results = []

        study = self._studies.get(study_uid)
        if study:
            for series_uid in study.get("series_uids", []):
                series = self._series.get(series_uid)
                if series:
                    if modality and series.get("modality") != modality:
                        continue
                    results.append(self._series_to_dicom_json(series))

        # If no stored series, return mock results
        if not results:
            results = self._generate_mock_series(study_uid)

        return results[offset : offset + limit]

    # =========================================================================
    # DICOM JSON Helpers
    # =========================================================================

    def _study_to_dicom_json(self, study: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal study dict to DICOM JSON format."""
        return {
            # Study Instance UID
            "0020000D": {
                "vr": "UI",
                "Value": [study["study_uid"]],
            },
            # Patient Name
            "00100010": {
                "vr": "PN",
                "Value": [{"Alphabetic": study.get("patient_name", "ANONYMOUS")}],
            },
            # Patient ID
            "00100020": {
                "vr": "LO",
                "Value": [study.get("patient_id", "UNKNOWN")],
            },
            # Study Date
            "00080020": {
                "vr": "DA",
                "Value": [study.get("study_date", "20250101")],
            },
            # Modality
            "00080060": {
                "vr": "CS",
                "Value": [study.get("modality", "SM")],
            },
            # Number of Series
            "00201206": {
                "vr": "IS",
                "Value": [str(len(study.get("series_uids", [])))],
            },
        }

    def _series_to_dicom_json(self, series: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal series dict to DICOM JSON format."""
        return {
            # Series Instance UID
            "0020000E": {
                "vr": "UI",
                "Value": [series["series_uid"]],
            },
            # Study Instance UID
            "0020000D": {
                "vr": "UI",
                "Value": [series.get("study_uid", "")],
            },
            # Modality
            "00080060": {
                "vr": "CS",
                "Value": [series.get("modality", "SM")],
            },
            # Series Description
            "0008103E": {
                "vr": "LO",
                "Value": [series.get("series_description", "WSI Series")],
            },
            # Number of Instances
            "00201209": {
                "vr": "IS",
                "Value": [str(len(series.get("instance_uids", [])))],
            },
        }

    def _generate_mock_studies(self) -> List[Dict[str, Any]]:
        """Generate mock study results for empty registry."""
        mock_studies = []
        for i in range(3):
            seed_text = f"mock_study_{i}"
            study_uid = _generate_uid(seed_text)
            mock_studies.append(
                {
                    "0020000D": {
                        "vr": "UI",
                        "Value": [study_uid],
                    },
                    "00100010": {
                        "vr": "PN",
                        "Value": [{"Alphabetic": f"PATIENT^MOCK_{i}"}],
                    },
                    "00100020": {
                        "vr": "LO",
                        "Value": [f"PAT{i:05d}"],
                    },
                    "00080020": {
                        "vr": "DA",
                        "Value": ["20250101"],
                    },
                    "00080060": {
                        "vr": "CS",
                        "Value": ["SM"],
                    },
                    "00201206": {
                        "vr": "IS",
                        "Value": ["1"],
                    },
                }
            )
        return mock_studies

    def _generate_mock_series(self, study_uid: str) -> List[Dict[str, Any]]:
        """Generate mock series results for a study."""
        series_uid = _generate_uid(f"series.{study_uid}.0")
        return [
            {
                "0020000E": {
                    "vr": "UI",
                    "Value": [series_uid],
                },
                "0020000D": {
                    "vr": "UI",
                    "Value": [study_uid],
                },
                "00080060": {
                    "vr": "CS",
                    "Value": ["SM"],
                },
                "0008103E": {
                    "vr": "LO",
                    "Value": ["WSI Series (mock)"],
                },
                "00201209": {
                    "vr": "IS",
                    "Value": ["1"],
                },
            }
        ]
