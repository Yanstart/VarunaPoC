"""
FHIR R4 Resource Builders - DiagnosticReport.

Builds FHIR R4 compatible JSON resources from slide and annotation data.
Reference: https://www.hl7.org/fhir/R4/diagnosticreport.html
"""

from datetime import UTC, datetime
from typing import Any


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

    Returns:
        FHIR R4 DiagnosticReport JSON dict
    """
    now = datetime.now(UTC).isoformat()

    report = {
        "resourceType": "DiagnosticReport",
        "id": f"slide-{slide_id}",
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/DiagnosticReport"],
            "lastUpdated": now,
        },
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
        "media": [
            {
                "comment": f"Whole Slide Image: {slide_name}",
                "link": {
                    "reference": f"Media/slide-{slide_id}",
                    "display": slide_name,
                },
            }
        ],
    }

    # Patient reference (stub - from URL param)
    if patient_id:
        report["subject"] = {
            "reference": f"Patient/{patient_id}",
        }
        if patient_name:
            report["subject"]["display"] = patient_name

    # Performer reference
    if performer_name:
        report["performer"] = [
            {
                "reference": f"Practitioner/{performer_sub or 'unknown'}",
                "display": performer_name,
            }
        ]

    # Conclusion
    if conclusion:
        report["conclusion"] = conclusion
    else:
        report["conclusion"] = (
            f"Digital pathology review. {annotations_count} annotation(s) recorded."
        )

    # Extensions for VarunaPoC specific data
    report["extension"] = [
        {
            "url": "http://varuna.local/fhir/StructureDefinition/slide-id",
            "valueString": slide_id,
        },
        {
            "url": "http://varuna.local/fhir/StructureDefinition/annotations-count",
            "valueInteger": annotations_count,
        },
    ]

    return report
