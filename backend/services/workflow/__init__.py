"""
Workflow integration hooks — concrete implementers of the WorkflowHook
Protocol from core.interfaces.workflow.

Three implementations live here today:

- `NoOpWorkflowHook`: log-only, never reaches an external system. The
  default when nothing is configured; also useful in tests where you want
  the FastAPI app to behave normally without driving real DPI/PACS.
- `FHIRWorkflowHook`: pushes events into a FHIR R4 server (HAPI FHIR in
  dev, the hospital's DPI in production). Implements `send_result`,
  `get_patient_info`, and `validate_configuration`.
- `PACSWorkflowHook`: talks DICOM (C-FIND/C-STORE/C-ECHO) via pynetdicom
  to a PACS (Orthanc in dev, the hospital PACS in production). Falls back
  to Orthanc HTTP REST for `update_worklist` (no native DIMSE-C op).

When both FHIR and PACS are configured, events are fanned out to both via
`CompositeWorkflowHook`. The composite returns the first non-empty
response for read methods (`query_worklist`, `get_patient_info`) and AND-
aggregates write success across hooks.

`get_workflow_hook()` is the single factory the rest of the app calls.
"""

from services.workflow.composite_hook import CompositeWorkflowHook
from services.workflow.fhir_hook import FHIRWorkflowHook
from services.workflow.no_op_hook import NoOpWorkflowHook
from services.workflow.pacs_hook import PACSWorkflowHook

__all__ = [
    "NoOpWorkflowHook",
    "FHIRWorkflowHook",
    "PACSWorkflowHook",
    "CompositeWorkflowHook",
    "get_workflow_hook",
]


def get_workflow_hook():
    """Return the singleton workflow hook for the current configuration.

    Selection rules (in order):
    - Both FHIR and PACS configured → CompositeWorkflowHook(FHIR, PACS)
    - Only FHIR configured          → FHIRWorkflowHook
    - Only PACS configured          → PACSWorkflowHook
    - Neither configured            → NoOpWorkflowHook

    Lazy imports keep fhir/config.py and pacs_config.py out of the module-
    level graph until actually needed.
    """
    from fhir.config import get_fhir_config
    from services.workflow.pacs_config import get_pacs_config

    fhir_config = get_fhir_config()
    pacs_config = get_pacs_config()

    hooks = []
    if fhir_config.is_configured:
        hooks.append(FHIRWorkflowHook(config=fhir_config))
    if pacs_config.is_configured:
        hooks.append(PACSWorkflowHook(config=pacs_config))

    if not hooks:
        return NoOpWorkflowHook()
    if len(hooks) == 1:
        return hooks[0]
    return CompositeWorkflowHook(hooks=hooks)
