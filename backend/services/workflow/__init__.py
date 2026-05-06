"""
Workflow integration hooks — concrete implementers of the WorkflowHook
Protocol from core.interfaces.workflow.

Two implementations live here today:

- `NoOpWorkflowHook`: log-only, never reaches an external system. The
  default when FHIR_ENABLED=false; also useful in tests where you want
  the FastAPI app to behave normally without driving a real DPI.
- `FHIRWorkflowHook`: pushes events into a FHIR R4 server (HAPI FHIR in
  dev, the hospital's DPI in production). Implements `send_result`,
  `get_patient_info`, and `validate_configuration`.

PACS-style hooks (DICOM C-FIND / C-STORE) will land in a follow-up Tier 4
under the same namespace (services.workflow.pacs_hook), composed with the
FHIR hook via `CompositeWorkflowHook` from the Protocol module.
"""

from services.workflow.fhir_hook import FHIRWorkflowHook
from services.workflow.no_op_hook import NoOpWorkflowHook

__all__ = ["NoOpWorkflowHook", "FHIRWorkflowHook", "get_workflow_hook"]


def get_workflow_hook():
    """Return the singleton workflow hook for the current configuration.

    Selects between FHIRWorkflowHook (when FHIR is enabled and configured)
    and NoOpWorkflowHook (otherwise). Lazy import keeps fhir/config.py
    out of the module-level import graph until actually needed.
    """
    from fhir.config import get_fhir_config

    config = get_fhir_config()
    if config.is_configured:
        return FHIRWorkflowHook(config=config)
    return NoOpWorkflowHook()
