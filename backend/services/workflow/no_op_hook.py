"""
NoOpWorkflowHook — the default WorkflowHook when no external system is
configured (FHIR_ENABLED=false, no PACS hook wired).

Behaviour: log every event at INFO, return success on writes, return
empty results on reads, never raise. Lets the FastAPI app run end-to-end
without depending on a hospital backbone — required for local dev,
tests, and demos.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from core.interfaces.workflow import WorkflowEvent

logger = logging.getLogger(__name__)


class NoOpWorkflowHook:
    """Logs events, performs no external integration."""

    async def on_event(self, event: WorkflowEvent) -> bool:
        logger.info(
            "[no-op workflow] event=%s slide_id=%s user_id=%s",
            event.event_type.value if event.event_type else "unknown",
            event.slide_id,
            event.user_id,
        )
        return True

    async def query_worklist(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        return []

    async def update_worklist(
        self,
        accession_number: str,
        status: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        logger.info(
            "[no-op workflow] update_worklist accession=%s status=%s",
            accession_number,
            status,
        )
        return True

    async def send_result(
        self, accession_number: str, result: Dict[str, Any]
    ) -> bool:
        logger.info("[no-op workflow] send_result accession=%s (skipped)", accession_number)
        return True

    async def get_patient_info(self, patient_id: str) -> Optional[Dict]:
        logger.debug("[no-op workflow] get_patient_info(%s) → None", patient_id)
        return None

    async def validate_configuration(self) -> Dict[str, bool]:
        return {
            "connection": True,  # no connection to make
            "authentication": True,
            "permissions": True,
            "version_compatible": True,
        }


__all__ = ["NoOpWorkflowHook"]
