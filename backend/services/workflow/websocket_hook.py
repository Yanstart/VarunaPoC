"""
WebSocketWorkflowHook — WorkflowHook Protocol implementer that publishes
events to the in-process WorkflowEventBroadcaster, which then fans to
every connected WebSocket client.

Used to power live UI updates: a pathologist signs a report on backend
host A, and within ~10ms every connected viewer (host B, host C, …)
receives the REPORT_SIGNED event and refreshes the worklist / UI.

Composition
-----------
Combined with FHIRWorkflowHook + PACSWorkflowHook via the existing
CompositeWorkflowHook in `services/workflow/__init__.py`. Default
factory wiring includes WebSocketWorkflowHook unconditionally — it's
cheap, in-process, and useful even in single-process dev.

Behaviour
---------
- on_event: serialises the event to a JSON-friendly dict and publishes
  via the broadcaster. Returns True iff at least one subscriber was
  reachable (or there are zero subscribers — which is also fine).
  NEVER raises (Protocol contract).
- query_worklist / get_patient_info / send_result / update_worklist /
  validate_configuration: stub responses (a WS hook is event-only,
  not a queryable backend like FHIR).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from services.workflow.event_broadcaster import get_broadcaster

if TYPE_CHECKING:
    from core.interfaces.workflow import WorkflowEvent

logger = logging.getLogger(__name__)


def _event_to_dict(event: "WorkflowEvent") -> Dict[str, Any]:
    """Serialise a WorkflowEvent into a JSON-friendly payload.

    Datetime → ISO-8601 string; enum → its `.value`. Metadata is
    forwarded as-is (it's already a dict by the Protocol contract).
    """
    return {
        "event_type": event.event_type.value if event.event_type else None,
        "slide_id": event.slide_id,
        "user_id": event.user_id,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "metadata": event.metadata or {},
    }


class WebSocketWorkflowHook:
    """WorkflowHook Protocol implementer that fans events to WS subscribers."""

    def __init__(self) -> None:
        self._broadcaster = get_broadcaster()

    # -- WorkflowHook Protocol -----------------------------------------------

    async def on_event(self, event: "WorkflowEvent") -> bool:
        """Publish the event payload to every connected subscriber.

        Returns True even when zero subscribers are connected (no error,
        nothing to deliver). Returns False only on an unexpected
        broadcaster failure — kept defensive even though the Protocol
        contract says never raise.
        """
        try:
            payload = _event_to_dict(event)
            delivered = await self._broadcaster.publish(payload)
            logger.debug(
                "[ws hook] event=%s delivered to %d subscriber(s)",
                payload.get("event_type"),
                delivered,
            )
            return True
        except Exception as e:
            logger.warning("[ws hook] publish raised: %s", e)
            return False

    async def query_worklist(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Not a queryable hook — returns empty so Composite skips this hook."""
        return []

    async def update_worklist(
        self,
        accession_number: str,
        status: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Worklist updates flow through FHIR/PACS, not WS. No-op success."""
        return True

    async def send_result(self, accession_number: str, result: Dict[str, Any]) -> bool:
        """Final results go to FHIR/PACS — WS surfaces them via on_event."""
        return True

    async def get_patient_info(self, patient_id: str) -> Optional[Dict]:
        return None

    async def validate_configuration(self) -> Dict[str, bool]:
        """In-process broadcaster has no network state to validate."""
        return {
            "connection": True,
            "authentication": True,
            "permissions": True,
            "version_compatible": True,
        }


__all__ = ["WebSocketWorkflowHook"]
