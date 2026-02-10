"""
FHIR R4 Stub Module - DiagnosticReport generation.

Provides FHIR R4 compatible DiagnosticReport resources from slide data.
This is a stub for future FHIR integration with hospital EHR systems.
"""

import os

FHIR_ENABLED = os.getenv("FHIR_ENABLED", "false").lower() == "true"

__all__ = ["FHIR_ENABLED"]
