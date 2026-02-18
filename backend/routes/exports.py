"""
Export Routes - API Endpoints for Slide Export

Endpoints:
- POST /api/exports/dicom/{slide_id}        - Export slide to DICOM WSI
- GET  /api/exports/dicom/{slide_id}/status  - Get export job status

References:
- DICOM Supplement 145: Whole Slide Microscopic Image IOD
- FastAPI: https://fastapi.tiangolo.com/
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from services.dicom_export import DICOMExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exports", tags=["exports"])

# Singleton service instance
_export_service: Optional[DICOMExportService] = None


def get_export_service() -> DICOMExportService:
    """Get or create the singleton DICOMExportService."""
    global _export_service
    if _export_service is None:
        _export_service = DICOMExportService()
    return _export_service


@router.post("/dicom/{slide_id}")
async def export_dicom(slide_id: str, anonymize: bool = True):
    """Export a slide to DICOM WSI format.

    Args:
        slide_id: Unique identifier for the slide.
        anonymize: Whether to anonymize patient data (default: True).

    Returns:
        Export result with DICOM UID and status.
    """
    service = get_export_service()

    try:
        result = service.export(
            slide_id=slide_id,
            anonymize=anonymize,
        )
        return {
            "slide_id": result.slide_id,
            "dicom_uid": result.dicom_uid,
            "status": result.status,
            "output_path": result.output_path,
            "file_size_bytes": result.file_size_bytes,
            "frames_count": result.frames_count,
            "processing_time_ms": result.processing_time_ms,
        }
    except Exception as e:
        logger.error("DICOM export failed for %s: %s", slide_id, e)
        raise HTTPException(status_code=500, detail=f"DICOM export failed: {e!s}")


@router.get("/dicom/{slide_id}/status")
async def export_status(slide_id: str):
    """Get the status of a DICOM export job.

    Args:
        slide_id: Unique identifier for the slide.

    Returns:
        Export status information.
    """
    service = get_export_service()
    return service.get_export_status(slide_id)
