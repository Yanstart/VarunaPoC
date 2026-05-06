"""
Export Routes - API Endpoints for Slide Export

Endpoints:
- POST /api/exports/dicom/{slide_id}        - Export slide to DICOM WSI
- GET  /api/exports/dicom/{slide_id}/status  - Get export job status

After a successful DICOM export, a `REPORT_SIGNED` WorkflowEvent is emitted
through `request.app.state.workflow_hook` (FHIR / PACS / Composite based on
runtime config). The emission is fire-and-forget — a hook outage cannot
fail the export response.

References:
- DICOM Supplement 145: Whole Slide Microscopic Image IOD
- FastAPI: https://fastapi.tiangolo.com/
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from core.interfaces.workflow import WorkflowEvent, WorkflowEventType
from monitoring import record_workflow_event
from services.dicom_export import DICOMExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exports", tags=["exports"])

# Singleton service instance
_export_service: Optional[DICOMExportService] = None


def get_export_service() -> DICOMExportService:
    """Get or create the singleton DICOMExportService."""
    global _export_service
    if _export_service is None:
        _export_service = DICOMExportService()
    return _export_service


@router.post("/dicom/{slide_id}")
async def export_dicom(
    request: Request,
    slide_id: str,
    anonymize: bool = True,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Export a slide to DICOM WSI format.

    Args:
        slide_id: Unique identifier for the slide.
        anonymize: Whether to anonymize patient data (default: True).

    Returns:
        Export result with DICOM UID and status.

    Side effects:
        Emits WorkflowEvent(REPORT_SIGNED) on success — fanned out to FHIR
        (DiagnosticReport) and / or PACS (C-STORE SR) depending on runtime
        config. Hook failures are logged but do not break the response.
    """
    service = get_export_service()

    try:
        result = service.export(
            slide_id=slide_id,
            anonymize=anonymize,
        )
    except Exception as e:
        logger.error("DICOM export failed for %s: %s", slide_id, e)
        raise HTTPException(status_code=500, detail=f"DICOM export failed: {e!s}")

    # Sprint 2 — emit REPORT_SIGNED after a successful export. The hook is
    # selected at startup (NoOp / FHIR / PACS / Composite) and attached to
    # app.state. None means startup wiring failed; we log and skip.
    hook = getattr(request.app.state, "workflow_hook", None)
    if hook is not None:
        event = WorkflowEvent(
            event_type=WorkflowEventType.REPORT_SIGNED,
            slide_id=slide_id,
            user_id=current_user.username,
            metadata={
                "accession_number": getattr(result, "accession_number", slide_id),
                "dicom_uid": result.dicom_uid,
                "anonymized": anonymize,
                "output_path": result.output_path,
                "frames_count": result.frames_count,
            },
        )
        try:
            ok = await hook.on_event(event)
            record_workflow_event(
                event_type=WorkflowEventType.REPORT_SIGNED.value,
                hook_type=type(hook).__name__,
                status="success" if ok else "partial_failure",
            )
        except Exception as e:
            logger.warning("workflow_hook.on_event raised: %s", e)
            record_workflow_event(
                event_type=WorkflowEventType.REPORT_SIGNED.value,
                hook_type=type(hook).__name__,
                status="exception",
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


@router.get("/dicom/{slide_id}/status")
async def export_status(slide_id: str, _current_user: CurrentUser = Depends(get_current_user)):
    """Get the status of a DICOM export job.

    Args:
        slide_id: Unique identifier for the slide.

    Returns:
        Export status information.
    """
    service = get_export_service()
    return service.get_export_status(slide_id)
