"""
FHIR Routes - FHIR R4 resource endpoints.

Endpoints:
- GET /api/fhir/DiagnosticReport/{slide_id} - Generate DiagnosticReport for a slide
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from auth.dependencies import require_role
from auth.schemas import CurrentUser
from fhir.patient_context import get_patient_context
from fhir.resources import build_diagnostic_report
from services.slide_scanner import get_slide_path_by_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fhir", tags=["FHIR"])


@router.get("/DiagnosticReport/{slide_id}")
async def get_diagnostic_report(
    slide_id: str,
    patient_id: str | None = Query(None, description="Patient ID"),
    patient_name: str | None = Query(None, description="Patient name"),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),  # noqa: B008
):
    """
    Generate a FHIR R4 DiagnosticReport for a slide.

    Returns a FHIR R4 compliant JSON resource with:
    - Slide reference as Media
    - Patient reference (from query params)
    - Performer (current authenticated user)
    - Annotation count
    - Pathology category and LOINC coding
    """
    # Verify slide exists
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")

    # Get patient context
    patient = get_patient_context(patient_id, patient_name)

    # Get annotation count (best-effort)
    annotations_count = 0
    try:
        from sqlalchemy import func, select

        from core.database import get_db_context
        from models.annotation import Annotation

        async with get_db_context() as db:
            result = await db.execute(select(func.count()).where(Annotation.slide_id == slide_id))
            annotations_count = result.scalar_one()
    except Exception as e:
        logger.warning(f"Could not get annotation count: {e}")

    # Get slide name from path
    from pathlib import Path

    slide_name = Path(slide_path).name

    # Build FHIR resource
    return build_diagnostic_report(
        slide_id=slide_id,
        slide_name=slide_name,
        patient_id=patient.patient_id,
        patient_name=patient.patient_name,
        performer_name=current_user.username,
        performer_sub=current_user.sub,
        annotations_count=annotations_count,
    )
