"""
CompositeWorkflowHook — fan-out adapter for multiple WorkflowHook implementers.

Use cases:
- Send the same event to FHIR (DPI integration) AND PACS (DICOM) in parallel.
- Add audit logging as a third hook without rewiring callers.
- Plug in a future MonitoringWorkflowHook to mirror events into Prometheus.

Behaviour
---------
- on_event:    runs every hook concurrently (asyncio.gather, return_exceptions=True),
               returns True iff every hook returned True. Failures are logged.
- query_worklist / get_patient_info: returns the FIRST non-empty result. Order
               follows registration order (the user picks the priority hook).
- send_result / update_worklist: dispatched to all hooks; True iff all True.
               (Either everything synced, or it didn't.)
- validate_configuration: per-flag AND across hooks (a flag is True iff every
               hook reports True).

This mirrors the `CompositeWorkflowHook` Protocol extension in
core/interfaces/workflow.py (lines 341-385) — `add_hook`, `remove_hook`, and
`get_hooks` are exposed for runtime composition.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from core.interfaces.workflow import WorkflowEvent, WorkflowHook

logger = logging.getLogger(__name__)


class CompositeWorkflowHook:
    """Fan-out WorkflowHook implementer over a list of registered hooks."""

    def __init__(self, hooks: Optional[List["WorkflowHook"]] = None) -> None:
        self._hooks: List["WorkflowHook"] = list(hooks) if hooks else []

    # -- Composite extension methods (CompositeWorkflowHook Protocol) -------

    def add_hook(self, hook: "WorkflowHook") -> None:
        if hook not in self._hooks:
            self._hooks.append(hook)

    def remove_hook(self, hook: "WorkflowHook") -> None:
        if hook in self._hooks:
            self._hooks.remove(hook)

    def get_hooks(self) -> List["WorkflowHook"]:
        return list(self._hooks)

    # -- WorkflowHook Protocol ----------------------------------------------

    async def on_event(self, event: "WorkflowEvent") -> bool:
        """Fan out concurrently. Logs failures, returns True iff all True."""
        if not self._hooks:
            return True
        results = await asyncio.gather(
            *(h.on_event(event) for h in self._hooks),
            return_exceptions=True,
        )
        all_ok = True
        for hook, result in zip(self._hooks, results, strict=False):
            if isinstance(result, Exception):
                logger.warning(
                    "[composite hook] %s.on_event raised: %s",
                    type(hook).__name__,
                    result,
                )
                all_ok = False
            elif not result:
                all_ok = False
        return all_ok

    async def query_worklist(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Return the first non-empty result. Hooks queried in registration order."""
        for hook in self._hooks:
            try:
                items = await hook.query_worklist(filters)
            except NotImplementedError:
                continue
            except Exception as e:
                logger.warning(
                    "[composite hook] %s.query_worklist raised: %s",
                    type(hook).__name__,
                    e,
                )
                continue
            if items:
                return items
        return []

    async def update_worklist(
        self,
        accession_number: str,
        status: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Dispatched to all hooks. NotImplementedError counts as 'skipped' (True)."""
        if not self._hooks:
            return True
        results = await asyncio.gather(
            *(
                _swallow_not_implemented(
                    h.update_worklist(accession_number, status, metadata)
                )
                for h in self._hooks
            ),
            return_exceptions=True,
        )
        all_ok = True
        for hook, result in zip(self._hooks, results, strict=False):
            if isinstance(result, Exception):
                logger.warning(
                    "[composite hook] %s.update_worklist raised: %s",
                    type(hook).__name__,
                    result,
                )
                all_ok = False
            elif result is False:
                all_ok = False
        return all_ok

    async def send_result(
        self, accession_number: str, result: Dict[str, Any]
    ) -> bool:
        """Dispatch to all. Each hook is responsible for its own retry policy."""
        if not self._hooks:
            return True
        results = await asyncio.gather(
            *(h.send_result(accession_number, result) for h in self._hooks),
            return_exceptions=True,
        )
        all_ok = True
        for hook, r in zip(self._hooks, results, strict=False):
            if isinstance(r, Exception):
                logger.warning(
                    "[composite hook] %s.send_result raised: %s",
                    type(hook).__name__,
                    r,
                )
                all_ok = False
            elif r is False:
                all_ok = False
        return all_ok

    async def get_patient_info(self, patient_id: str) -> Optional[Dict]:
        """Return the first non-None response. PACS first if registered first."""
        for hook in self._hooks:
            try:
                info = await hook.get_patient_info(patient_id)
            except NotImplementedError:
                continue
            except Exception as e:
                logger.warning(
                    "[composite hook] %s.get_patient_info raised: %s",
                    type(hook).__name__,
                    e,
                )
                continue
            if info is not None:
                return info
        return None

    async def validate_configuration(self) -> Dict[str, bool]:
        """AND aggregation: a flag is True iff every hook reports True."""
        if not self._hooks:
            # No hook: vacuously valid.
            return {
                "connection": True,
                "authentication": True,
                "permissions": True,
                "version_compatible": True,
            }
        per_hook: List[Dict[str, bool]] = []
        for hook in self._hooks:
            try:
                per_hook.append(await hook.validate_configuration())
            except Exception as e:
                logger.warning(
                    "[composite hook] %s.validate_configuration raised: %s",
                    type(hook).__name__,
                    e,
                )
                per_hook.append(
                    {
                        "connection": False,
                        "authentication": False,
                        "permissions": False,
                        "version_compatible": False,
                    }
                )
        keys = ("connection", "authentication", "permissions", "version_compatible")
        return {k: all(p.get(k, False) for p in per_hook) for k in keys}


async def _swallow_not_implemented(coro):
    """Treat NotImplementedError as 'skipped' rather than 'failed'.

    A hook that explicitly opts out of a method (e.g. PACSWorkflowHook
    when PACS_HTTP_URL is unset) should not pull the composite return
    value to False. We coerce NotImplementedError → True (skipped).
    """
    try:
        return await coro
    except NotImplementedError:
        return True


__all__ = ["CompositeWorkflowHook"]
