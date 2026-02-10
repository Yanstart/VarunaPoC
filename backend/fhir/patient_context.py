"""
Patient Context Stub - Extract patient info from URL parameters.

In a real hospital deployment, patient context would come from:
- SMART on FHIR launch context
- URL parameters from EHR integration
- FHIR Patient resource lookup

This stub accepts patient_id and patient_name as query parameters.
"""

from typing import Optional

from pydantic import BaseModel


class PatientContext(BaseModel):
    """Patient context for FHIR resource generation."""

    patient_id: Optional[str] = None
    patient_name: Optional[str] = None


def get_patient_context(
    patient_id: Optional[str] = None,
    patient_name: Optional[str] = None,
) -> PatientContext:
    """
    Build patient context from URL parameters.

    In production, this would use SMART on FHIR launch context
    or EHR integration to resolve patient identity.
    """
    return PatientContext(
        patient_id=patient_id,
        patient_name=patient_name,
    )
