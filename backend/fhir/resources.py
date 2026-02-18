"""
FHIR R4 Resource Builders - DiagnosticReport.

Builds FHIR R4 compatible JSON resources from slide and annotation data.
Reference: https://www.hl7.org/fhir/R4/diagnosticreport.html

Enhanced for #103:
- Contained Patient and Practitioner resources
- Specimen reference with type/collection info
- Result references to Observation resources
- presentedForm for PDF report attachment reference
- Search support (patient, status)
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from fhir.profiles import US_CORE_DIAGNOSTIC_REPORT_PROFILE


def _deterministic_id(seed: str) -> str:
    """Génère un identifiant déterministe à partir d'un seed."""
    return hashlib.sha256(seed.encode()).hexdigest()[:12]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _build_contained_resources(
    slide_id: str,
    patient_id: str | None,
    patient_name: str | None,
    performer_name: str | None,
    performer_sub: str | None,
    specimen_type: str | None,
    specimen_collection_method: str | None,
    now: str,
) -> tuple[list[dict[str, Any]], str, str, str]:
    """Build contained Patient, Practitioner, and Specimen resources.

    Returns:
        Tuple of (contained_list, patient_ref_id, practitioner_ref_id, specimen_ref_id).
    """
    contained: list[dict[str, Any]] = []
    patient_ref_id = f"patient-{_deterministic_id(patient_id or slide_id)}"
    practitioner_ref_id = f"practitioner-{_deterministic_id(performer_sub or 'unknown')}"
    specimen_ref_id = f"specimen-{_deterministic_id(slide_id)}"

    if patient_id:
        patient_names = [{"use": "official", "text": patient_name}] if patient_name else []
        contained.append(
            {
                "resourceType": "Patient",
                "id": patient_ref_id,
                "identifier": [
                    {"system": "http://hospital.example.org/patients", "value": patient_id}
                ],
                "name": patient_names,
            }
        )

    if performer_name:
        contained.append(
            {
                "resourceType": "Practitioner",
                "id": practitioner_ref_id,
                "identifier": [
                    {
                        "system": "http://hospital.example.org/practitioners",
                        "value": performer_sub or "unknown",
                    }
                ],
                "name": [{"use": "official", "text": performer_name}],
            }
        )

    specimen = {
        "resourceType": "Specimen",
        "id": specimen_ref_id,
        "type": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "119376003",
                    "display": specimen_type or "Tissue specimen",
                }
            ],
            "text": specimen_type or "Tissue specimen",
        },
        "collection": {"collectedDateTime": now},
    }
    if specimen_collection_method:
        specimen["collection"]["method"] = {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "86273004",
                    "display": specimen_collection_method,
                }
            ],
            "text": specimen_collection_method,
        }
    if patient_id:
        specimen["subject"] = {"reference": f"#{patient_ref_id}"}
    contained.append(specimen)

    return contained, patient_ref_id, practitioner_ref_id, specimen_ref_id


def _build_result_references(
    result_observations: list[dict[str, Any]] | None,
    ml_tags: dict[str, Any] | None,
    patient_id: str | None,
    slide_id: str,
) -> list[dict[str, str]] | None:
    """Build result references from explicit observations and ML tags."""
    refs: list[dict[str, str]] = []

    if result_observations:
        for obs in result_observations:
            refs.append(
                {
                    "reference": f"Observation/{obs.get('id', 'unknown')}",
                    "display": obs.get("code", {}).get("text", "Observation"),
                }
            )

    if ml_tags:
        from fhir.profiles import map_ml_tags_to_tumor_markers

        markers = map_ml_tags_to_tumor_markers(
            tags=ml_tags,
            patient_id=patient_id or "unknown",
            slide_id=slide_id,
        )
        for marker in markers:
            refs.append(
                {
                    "reference": f"Observation/{marker['id']}",
                    "display": marker.get("code", {}).get("text", "Tumor marker"),
                }
            )

    return refs or None


def build_diagnostic_report(
    slide_id: str,
    slide_name: str = "",
    patient_id: str | None = None,
    patient_name: str | None = None,
    performer_name: str | None = None,
    performer_sub: str | None = None,
    annotations_count: int = 0,
    conclusion: str | None = None,
    status: str = "preliminary",
    specimen_type: str | None = None,
    specimen_collection_method: str | None = None,
    result_observations: list[dict[str, Any]] | None = None,
    pdf_url: str | None = None,
    ml_tags: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a FHIR R4 DiagnosticReport resource.

    Args:
        slide_id: Internal slide identifier
        slide_name: Human-readable slide name
        patient_id: Patient identifier (from URL param or context)
        patient_name: Patient name
        performer_name: Pathologist name
        performer_sub: Pathologist IdP subject
        annotations_count: Number of annotations on the slide
        conclusion: Diagnostic conclusion text
        status: Report status (preliminary, final, etc.)
        specimen_type: Specimen type (e.g. "tissue", "biopsy")
        specimen_collection_method: Collection method description
        result_observations: List of Observation resource dicts to include as results
        pdf_url: URL for PDF report attachment
        ml_tags: ML auto-tags dict for tumor marker mapping

    Returns:
        FHIR R4 DiagnosticReport JSON dict
    """
    now = _now_iso()

    # Build contained resources
    contained, patient_ref_id, practitioner_ref_id, specimen_ref_id = _build_contained_resources(
        slide_id,
        patient_id,
        patient_name,
        performer_name,
        performer_sub,
        specimen_type,
        specimen_collection_method,
        now,
    )

    report: dict[str, Any] = {
        "resourceType": "DiagnosticReport",
        "id": f"slide-{slide_id}",
        "meta": {
            "profile": [US_CORE_DIAGNOSTIC_REPORT_PROFILE],
            "lastUpdated": now,
        },
        "contained": contained,
        "status": status,
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "SP",
                        "display": "Surgical Pathology",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "60568-3",
                    "display": "Pathology synoptic report",
                }
            ],
            "text": "Digital Pathology Slide Report",
        },
        "effectiveDateTime": now,
        "issued": now,
        "specimen": [
            {
                "reference": f"#{specimen_ref_id}",
                "display": specimen_type or "Tissue specimen",
            }
        ],
        "conclusion": conclusion
        or (f"Digital pathology review. {annotations_count} annotation(s) recorded."),
        "media": [
            {
                "comment": f"Whole Slide Image: {slide_name}",
                "link": {
                    "reference": f"Media/slide-{slide_id}",
                    "display": slide_name,
                },
            }
        ],
        "extension": [
            {
                "url": "http://varuna.local/fhir/StructureDefinition/slide-id",
                "valueString": slide_id,
            },
            {
                "url": "http://varuna.local/fhir/StructureDefinition/annotations-count",
                "valueInteger": annotations_count,
            },
        ],
    }

    # Subject (Patient) reference
    if patient_id:
        report["subject"] = {
            "reference": f"#{patient_ref_id}",
            "display": patient_name or patient_id,
        }

    # Performer reference
    if performer_name:
        report["performer"] = [{"reference": f"#{practitioner_ref_id}", "display": performer_name}]

    # Result observation references
    result_refs = _build_result_references(
        result_observations,
        ml_tags,
        patient_id,
        slide_id,
    )
    if result_refs:
        report["result"] = result_refs

    # PDF attachment
    if pdf_url:
        report["presentedForm"] = [
            {
                "contentType": "application/pdf",
                "url": pdf_url,
                "title": f"Pathology Report - {slide_name}",
            }
        ]

    return report


def search_diagnostic_reports(
    reports: list[dict[str, Any]],
    patient_id: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """
    Filtre une liste de DiagnosticReports selon les critères de recherche.

    Args:
        reports: Liste de DiagnosticReport FHIR.
        patient_id: Filtrer par ID patient.
        status: Filtrer par statut (preliminary, final, etc.).

    Returns:
        Bundle FHIR searchset avec les résultats filtrés.
    """
    filtered = reports

    if patient_id:
        filtered = [r for r in filtered if _report_matches_patient(r, patient_id)]

    if status:
        filtered = [r for r in filtered if r.get("status") == status]

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(filtered),
        "entry": [
            {
                "fullUrl": f"DiagnosticReport/{r.get('id', 'unknown')}",
                "resource": r,
            }
            for r in filtered
        ],
    }


def _report_matches_patient(report: dict[str, Any], patient_id: str) -> bool:
    """Vérifie si un DiagnosticReport correspond au patient donné."""
    subject = report.get("subject", {})
    ref = subject.get("reference", "")
    display = subject.get("display", "")

    if patient_id in ref or patient_id in display:
        return True

    # Check contained resources for patient ID match
    for contained in report.get("contained", []):
        if contained.get("resourceType") != "Patient":
            continue
        for ident in contained.get("identifier", []):
            if ident.get("value") == patient_id:
                return True

    return False
