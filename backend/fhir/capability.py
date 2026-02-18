"""
FHIR R4 CapabilityStatement - Describes server capabilities.

Endpoint: GET /api/fhir/metadata
Reference: https://www.hl7.org/fhir/R4/capabilitystatement.html
"""

from datetime import UTC, datetime
from typing import Any


def build_capability_statement(
    base_url: str = "http://localhost:8000/api/fhir",
) -> dict[str, Any]:
    """
    Construit un CapabilityStatement FHIR R4 décrivant les capacités du serveur.

    Args:
        base_url: URL de base du serveur FHIR.

    Returns:
        Ressource FHIR R4 CapabilityStatement.
    """
    now = datetime.now(UTC).isoformat()

    return {
        "resourceType": "CapabilityStatement",
        "id": "varuna-poc",
        "url": f"{base_url}/metadata",
        "version": "1.0.0",
        "name": "VarunaPoCCapabilityStatement",
        "title": "VarunaPoC Digital Pathology FHIR Server",
        "status": "active",
        "experimental": True,
        "date": now,
        "publisher": "VarunaPoC",
        "description": (
            "FHIR R4 capability statement for VarunaPoC digital pathology viewer. "
            "Provides DiagnosticReport resources for pathology slides with "
            "US Core, CA Core, and mCODE profile support."
        ),
        "kind": "instance",
        "software": {
            "name": "VarunaPoC",
            "version": "1.7.0",
        },
        "implementation": {
            "description": "VarunaPoC FHIR R4 API",
            "url": base_url,
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "documentation": (
                    "RESTful FHIR server for digital pathology diagnostic reports."
                ),
                "security": {
                    "cors": True,
                    "service": [
                        {
                            "coding": [
                                {
                                    "system": (
                                        "http://terminology.hl7.org/CodeSystem"
                                        "/restful-security-service"
                                    ),
                                    "code": "SMART-on-FHIR",
                                    "display": "SMART-on-FHIR",
                                }
                            ],
                            "text": "OAuth2 using SMART-on-FHIR profile",
                        }
                    ],
                    "description": (
                        "Supports SMART on FHIR EHR launch and standalone launch."
                    ),
                },
                "resource": [
                    {
                        "type": "DiagnosticReport",
                        "profile": (
                            "http://hl7.org/fhir/us/core/StructureDefinition"
                            "/us-core-diagnosticreport-note"
                        ),
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                        ],
                        "searchParam": [
                            {
                                "name": "patient",
                                "type": "reference",
                                "documentation": "Search by patient reference.",
                            },
                            {
                                "name": "status",
                                "type": "token",
                                "documentation": (
                                    "Search by report status "
                                    "(preliminary, final, amended, etc.)."
                                ),
                            },
                            {
                                "name": "category",
                                "type": "token",
                                "documentation": "Search by report category (e.g. SP).",
                            },
                            {
                                "name": "code",
                                "type": "token",
                                "documentation": "Search by LOINC code.",
                            },
                        ],
                    },
                    {
                        "type": "Patient",
                        "profile": (
                            "http://hl7.org/fhir/us/core/StructureDefinition"
                            "/us-core-patient"
                        ),
                        "supportedProfile": [
                            (
                                "http://hl7.org/fhir/ca/core/StructureDefinition"
                                "/profile-patient"
                            ),
                        ],
                        "interaction": [
                            {"code": "read"},
                        ],
                    },
                    {
                        "type": "Observation",
                        "profile": (
                            "http://hl7.org/fhir/us/mcode/StructureDefinition"
                            "/mcode-tumor-marker"
                        ),
                        "interaction": [
                            {"code": "read"},
                        ],
                    },
                    {
                        "type": "Condition",
                        "profile": (
                            "http://hl7.org/fhir/us/mcode/StructureDefinition"
                            "/mcode-primary-cancer-condition"
                        ),
                        "interaction": [
                            {"code": "read"},
                        ],
                    },
                ],
            }
        ],
    }
