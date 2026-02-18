"""
Patient Context - Extract patient info from URL parameters or SMART launch.

Sources de contexte patient (par priorité):
1. SMART on FHIR launch context (si disponible)
2. URL parameters (patient_id, patient_name)
3. Default (None)
"""

from __future__ import annotations

from pydantic import BaseModel


class PatientContext(BaseModel):
    """Patient context for FHIR resource generation."""

    patient_id: str | None = None
    patient_name: str | None = None
    encounter_id: str | None = None
    source: str = "url_params"


# In-memory SMART launch context cache (mock mode)
_smart_launch_contexts: dict[str, dict] = {}


def store_smart_context(launch_id: str, context: dict) -> None:
    """
    Stocke le contexte patient issu d'un lancement SMART on FHIR.

    Args:
        launch_id: Identifiant du lancement SMART.
        context: Contexte SMART (patient_id, encounter_id, etc.).
    """
    _smart_launch_contexts[launch_id] = context


def get_patient_context(
    patient_id: str | None = None,
    patient_name: str | None = None,
    smart_launch_id: str | None = None,
) -> PatientContext:
    """
    Construit le contexte patient à partir des paramètres disponibles.

    Priorité: SMART launch > URL params.

    Args:
        patient_id: ID patient (paramètre URL).
        patient_name: Nom du patient (paramètre URL).
        smart_launch_id: ID de lancement SMART (si applicable).

    Returns:
        PatientContext avec les données résolues.
    """
    # Try SMART launch context first
    if smart_launch_id and smart_launch_id in _smart_launch_contexts:
        ctx = _smart_launch_contexts[smart_launch_id]
        return PatientContext(
            patient_id=ctx.get("patient_id") or patient_id,
            patient_name=patient_name,
            encounter_id=ctx.get("encounter_id"),
            source="smart_launch",
        )

    return PatientContext(
        patient_id=patient_id,
        patient_name=patient_name,
        source="url_params",
    )
