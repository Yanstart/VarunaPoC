"""
FHIR Routes - FHIR R4 resource endpoints.

Endpoints:
- GET /api/fhir/metadata               — CapabilityStatement (#103)
- GET /api/fhir/DiagnosticReport/{id}   — DiagnosticReport for a slide (#103)
- GET /api/fhir/DiagnosticReport        — Search DiagnosticReports (#103)
- GET /api/fhir/launch                  — SMART on FHIR EHR launch (#104)
- GET /api/fhir/.well-known/smart-configuration — SMART config (#104)
- GET /api/fhir/Patient/{id}/us-core    — US Core Patient (#112)
- GET /api/fhir/Patient/{id}/ca-core    — CA Core Patient (#112)
- GET /api/fhir/Condition/{id}/mcode    — mCODE CancerCondition (#114)
- GET /api/fhir/Observation/tnm/{id}    — mCODE TNMStageGroup (#114)
- GET /api/fhir/Observation/marker/{id} — mCODE TumorMarkerTest (#114)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from auth.dependencies import require_role
from auth.schemas import CurrentUser
from fhir.capability import build_capability_statement
from fhir.patient_context import get_patient_context, store_smart_context
from fhir.profiles import (
    build_ca_core_patient,
    build_cancer_condition,
    build_tnm_stage_group,
    build_tumor_marker_test,
    build_us_core_patient,
    validate_ca_core_patient,
    validate_mcode_cancer_condition,
    validate_mcode_tumor_marker,
    validate_us_core_patient,
)
from fhir.resources import build_diagnostic_report, search_diagnostic_reports
from fhir.smart import get_smart_configuration, handle_ehr_launch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fhir", tags=["FHIR"])


# ---------------------------------------------------------------------------
# #103 — CapabilityStatement
# ---------------------------------------------------------------------------


@router.get("/metadata")
async def get_capability_statement(request: Request):
    """
    FHIR R4 CapabilityStatement — describes server capabilities.

    Returns the server's conformance statement including supported
    resources, search parameters, and security information.
    """
    base_url = str(request.base_url).rstrip("/") + "/api/fhir"
    return build_capability_statement(base_url=base_url)


# ---------------------------------------------------------------------------
# #104 — SMART on FHIR
# ---------------------------------------------------------------------------


@router.get("/.well-known/smart-configuration")
async def smart_configuration(request: Request):
    """
    SMART on FHIR .well-known/smart-configuration endpoint.

    Returns the SMART configuration JSON describing authorization
    endpoints, supported scopes, and capabilities.
    """
    base_url = str(request.base_url).rstrip("/") + "/api/fhir"
    return get_smart_configuration(base_url=base_url)


@router.get("/launch")
async def smart_launch(
    launch: str = Query(..., description="Opaque launch token from EHR"),
    iss: str = Query(..., description="FHIR server base URL from EHR"),
):
    """
    SMART on FHIR EHR launch endpoint.

    Accepts launch and iss parameters from the EHR, resolves
    patient context, and returns a launch context (mock mode by default).
    """
    context = handle_ehr_launch(launch=launch, iss=iss)

    # Store context for later retrieval by patient_context
    launch_id = context.get("launch_id", "")
    if launch_id:
        store_smart_context(launch_id, context)

    return context


# ---------------------------------------------------------------------------
# #103 — DiagnosticReport (existing + search)
# ---------------------------------------------------------------------------


@router.get("/DiagnosticReport/{slide_id}")
async def get_diagnostic_report(
    slide_id: str,
    patient_id: str | None = Query(None, description="Patient ID"),
    patient_name: str | None = Query(None, description="Patient name"),
    smart_launch_id: str | None = Query(None, description="SMART launch ID"),
    specimen_type: str | None = Query(None, description="Specimen type"),
    pdf_url: str | None = Query(None, description="PDF report URL"),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),  # noqa: B008
):
    """
    Generate a FHIR R4 DiagnosticReport for a slide.

    Returns a FHIR R4 compliant JSON resource with:
    - Contained Patient and Practitioner resources
    - Specimen with type and collection info
    - Slide reference as Media
    - Result references to Observation resources
    - presentedForm for PDF attachment
    - Pathology category and LOINC coding
    """
    # Verify slide exists
    try:
        from services.slide_scanner import get_slide_path_by_id

        slide_path = get_slide_path_by_id(slide_id)
    except ImportError:
        slide_path = None

    if not slide_path:
        raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")

    # Get patient context (SMART or URL params)
    patient = get_patient_context(patient_id, patient_name, smart_launch_id)

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
        logger.warning("Could not get annotation count: %s", e)

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
        specimen_type=specimen_type,
        pdf_url=pdf_url,
    )


@router.get("/DiagnosticReport")
async def search_diagnostic_reports_endpoint(
    patient: str | None = Query(None, description="Patient ID filter"),
    status: str | None = Query(None, description="Report status filter"),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),  # noqa: B008
):
    """
    Search DiagnosticReports by patient and/or status.

    Returns a FHIR Bundle of matching DiagnosticReports.
    In mock mode, returns a sample set of reports for demonstration.
    """
    # Mock mode: generate sample reports for search demonstration
    sample_reports = []
    mock_slides = [
        ("slide-001", "sample_slide_1.svs", "P001", "Jane Doe"),
        ("slide-002", "sample_slide_2.svs", "P002", "John Smith"),
        ("slide-003", "sample_slide_3.svs", "P001", "Jane Doe"),
    ]

    for sid, sname, pid, pname in mock_slides:
        report = build_diagnostic_report(
            slide_id=sid,
            slide_name=sname,
            patient_id=pid,
            patient_name=pname,
            performer_name=current_user.username,
            performer_sub=current_user.sub,
            status="preliminary" if sid != "slide-002" else "final",
        )
        sample_reports.append(report)

    return search_diagnostic_reports(
        reports=sample_reports,
        patient_id=patient,
        status=status,
    )


# ---------------------------------------------------------------------------
# #112 — US Core / CA Core Patient profiles
# ---------------------------------------------------------------------------


@router.get("/Patient/{patient_id}/us-core")
async def get_us_core_patient(
    patient_id: str,
    family_name: str = Query("Unknown", description="Family name"),
    given_name: str = Query("Unknown", description="Given name"),
    gender: str = Query("unknown", description="Administrative gender"),
    birth_date: str | None = Query(None, description="Birth date (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends(
        require_role("MEDECIN", "ADMIN_TECHNIQUE")
    ),  # noqa: ARG001, B008
):
    """
    Return a US Core Patient resource (USCDI v3 required elements).

    Includes identifier, name, gender, and optional race/ethnicity extensions.
    """
    patient = build_us_core_patient(
        patient_id=patient_id,
        family_name=family_name,
        given_name=given_name,
        gender=gender,
        birth_date=birth_date,
    )
    errors = validate_us_core_patient(patient)
    if errors:
        logger.warning("US Core validation issues: %s", errors)
    return patient


@router.get("/Patient/{patient_id}/ca-core")
async def get_ca_core_patient(
    patient_id: str,
    family_name: str = Query("Unknown", description="Family name"),
    given_name: str = Query("Unknown", description="Given name"),
    gender: str = Query("unknown", description="Administrative gender"),
    birth_date: str | None = Query(None, description="Birth date (YYYY-MM-DD)"),
    health_number: str | None = Query(None, description="Provincial health number"),
    jurisdiction: str = Query("ON", description="Province code (ON, QC, BC, AB)"),
    current_user: CurrentUser = Depends(
        require_role("MEDECIN", "ADMIN_TECHNIQUE")
    ),  # noqa: ARG001, B008
):
    """
    Return a CA Core Patient resource (pan-Canadian required elements).

    Includes provincial health number identifier when provided.
    """
    patient = build_ca_core_patient(
        patient_id=patient_id,
        family_name=family_name,
        given_name=given_name,
        gender=gender,
        birth_date=birth_date,
        health_number=health_number,
        health_number_jurisdiction=jurisdiction,
    )
    errors = validate_ca_core_patient(patient)
    if errors:
        logger.warning("CA Core validation issues: %s", errors)
    return patient


# ---------------------------------------------------------------------------
# #114 — mCODE Oncology resources
# ---------------------------------------------------------------------------


@router.get("/Condition/{condition_id}/mcode")
async def get_mcode_cancer_condition(
    condition_id: str,
    patient_id: str = Query(..., description="Patient reference"),
    histology_code: str = Query("8140/3", description="ICD-O-3 histology code"),
    histology_display: str = Query("Adenocarcinoma, NOS", description="Histology display"),
    body_site_code: str = Query("80248005", description="SNOMED CT body site code"),
    body_site_display: str = Query("Left breast structure", description="Body site display"),
    current_user: CurrentUser = Depends(
        require_role("MEDECIN", "ADMIN_TECHNIQUE")
    ),  # noqa: ARG001, B008
):
    """
    Return an mCODE PrimaryCancerCondition resource.

    Includes TNM staging reference, histology coding, and body site.
    """
    condition = build_cancer_condition(
        condition_id=condition_id,
        patient_id=patient_id,
        histology_code=histology_code,
        histology_display=histology_display,
        body_site_code=body_site_code,
        body_site_display=body_site_display,
    )
    errors = validate_mcode_cancer_condition(condition)
    if errors:
        logger.warning("mCODE CancerCondition validation issues: %s", errors)
    return condition


@router.get("/Observation/tnm/{observation_id}")
async def get_mcode_tnm_stage(
    observation_id: str,
    patient_id: str = Query(..., description="Patient reference"),
    stage: str = Query("II", description="Stage group (I, II, III, IV)"),
    t_category: str = Query("T2", description="T category"),
    n_category: str = Query("N0", description="N category"),
    m_category: str = Query("M0", description="M category"),
    current_user: CurrentUser = Depends(
        require_role("MEDECIN", "ADMIN_TECHNIQUE")
    ),  # noqa: ARG001, B008
):
    """
    Return an mCODE TNMStageGroup observation.

    Includes clinical T, N, and M component observations.
    """
    # Map stage display to SNOMED codes (simplified)
    stage_snomed = {
        "I": ("258215001", "Stage I"),
        "II": ("261638004", "Stage II"),
        "III": ("261639007", "Stage III"),
        "IV": ("261640009", "Stage IV"),
    }
    code, display = stage_snomed.get(stage, ("261638004", f"Stage {stage}"))

    return build_tnm_stage_group(
        observation_id=observation_id,
        patient_id=patient_id,
        stage_group_code=code,
        stage_group_display=display,
        t_display=t_category,
        n_display=n_category,
        m_display=m_category,
    )


@router.get("/Observation/marker/{observation_id}")
async def get_mcode_tumor_marker(
    observation_id: str,
    patient_id: str = Query(..., description="Patient reference"),
    marker: str = Query(..., description="Marker name (ki67, her2, er, pr)"),
    value: str | None = Query(None, description="Result value"),
    current_user: CurrentUser = Depends(
        require_role("MEDECIN", "ADMIN_TECHNIQUE")
    ),  # noqa: ARG001, B008
):
    """
    Return an mCODE TumorMarkerTest observation.

    Maps VarunaPoC ML auto-tags to mCODE LOINC-coded tumor marker observations.
    """
    # Try to parse numeric value
    numeric_val: float | str | None = None
    if value is not None:
        try:
            numeric_val = float(value)
        except ValueError:
            numeric_val = value

    obs = build_tumor_marker_test(
        observation_id=observation_id,
        patient_id=patient_id,
        marker_name=marker,
        value=numeric_val,
    )
    errors = validate_mcode_tumor_marker(obs)
    if errors:
        logger.warning("mCODE TumorMarkerTest validation issues: %s", errors)
    return obs
