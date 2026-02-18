"""
SMART on FHIR App Launch Handler.

Implements the SMART on FHIR EHR launch sequence:
- GET /api/fhir/launch — accepts launch and iss parameters
- GET /api/fhir/.well-known/smart-configuration — SMART configuration JSON

Reference: https://hl7.org/fhir/smart-app-launch/
Mock mode: returns deterministic patient context without real EHR.
"""

import hashlib
import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SMARTConfiguration(BaseModel):
    """SMART on FHIR .well-known/smart-configuration response."""

    authorization_endpoint: str
    token_endpoint: str
    token_endpoint_auth_methods_supported: list[str] = Field(
        default_factory=lambda: ["client_secret_basic", "client_secret_post"],
    )
    registration_endpoint: str | None = None
    scopes_supported: list[str] = Field(
        default_factory=lambda: [
            "openid",
            "fhirUser",
            "launch",
            "launch/patient",
            "patient/Patient.read",
            "patient/DiagnosticReport.read",
            "patient/Observation.read",
            "patient/Condition.read",
            "user/Patient.read",
            "user/DiagnosticReport.read",
            "offline_access",
        ],
    )
    response_types_supported: list[str] = Field(
        default_factory=lambda: ["code"],
    )
    capabilities: list[str] = Field(
        default_factory=lambda: [
            "launch-ehr",
            "launch-standalone",
            "client-public",
            "client-confidential-symmetric",
            "context-ehr-patient",
            "sso-openid-connect",
            "permission-v2",
        ],
    )
    code_challenge_methods_supported: list[str] = Field(
        default_factory=lambda: ["S256"],
    )


class SMARTLaunchContext(BaseModel):
    """Contexte retourné après un lancement SMART on FHIR."""

    launch_id: str
    iss: str
    patient_id: str | None = None
    encounter_id: str | None = None
    need_patient_banner: bool = True
    smart_style_url: str | None = None
    intent: str = "pathology-review"
    mock_mode: bool = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deterministic_id(seed: str, prefix: str = "mock") -> str:
    """Génère un identifiant déterministe à partir d'un seed (pour le mode mock)."""
    digest = hashlib.sha256(seed.encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


def get_smart_configuration(
    base_url: str = "http://localhost:8000/api/fhir",
) -> dict[str, Any]:
    """
    Retourne la configuration SMART on FHIR (.well-known).

    Args:
        base_url: URL de base du serveur FHIR.

    Returns:
        Configuration SMART conforme au standard.
    """
    config = SMARTConfiguration(
        authorization_endpoint=f"{base_url}/authorize",
        token_endpoint=f"{base_url}/token",
        registration_endpoint=f"{base_url}/register",
    )
    return config.model_dump()


def handle_ehr_launch(
    launch: str,
    iss: str,
) -> dict[str, Any]:
    """
    Traite un lancement EHR SMART on FHIR.

    En mode mock (par défaut), retourne un contexte patient déterministe
    dérivé des paramètres launch et iss sans contacter de vrai EHR.

    Args:
        launch: Jeton opaque fourni par l'EHR.
        iss: URL du serveur FHIR de l'EHR.

    Returns:
        Contexte de lancement SMART.
    """
    # Mode mock: contexte déterministe
    patient_id = _deterministic_id(f"{launch}:{iss}", prefix="patient")
    encounter_id = _deterministic_id(f"{launch}:{iss}:encounter", prefix="encounter")
    launch_id = _deterministic_id(launch, prefix="launch")

    logger.info(
        "SMART EHR launch (mock): launch=%s iss=%s -> patient=%s",
        launch,
        iss,
        patient_id,
    )

    ctx = SMARTLaunchContext(
        launch_id=launch_id,
        iss=iss,
        patient_id=patient_id,
        encounter_id=encounter_id,
        need_patient_banner=True,
        smart_style_url=f"{iss}/.well-known/smart-style-url",
        intent="pathology-review",
        mock_mode=True,
    )
    return ctx.model_dump()
