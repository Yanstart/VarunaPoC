"""
Shared FastAPI helpers for routes that consume the StorageProvider.

Strangler Fig pattern: each route migrates from direct slide_scanner
imports to consuming the StorageProvider via Depends() / app.state.
This module centralises the boilerplate so each route just imports
`get_storage` (Depends) and `resolve_slide_path` (translation helper)
without duplicating the legacy-fallback logic.

Once every route has migrated, the legacy fallback can be removed in
one place rather than chased across each route file.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from fastapi import HTTPException, Request  # noqa: TC002 — Request needs runtime import for FastAPI to inject

from core.exceptions.storage import SlideNotFoundError
from monitoring import record_workflow_event
from services.slide_scanner import get_slide_path_by_id  # legacy fallback

if TYPE_CHECKING:
    from core.interfaces import StorageProvider
    from core.interfaces.workflow import WorkflowEvent

logger = logging.getLogger(__name__)


async def get_storage(request: Request) -> "Optional[StorageProvider]":
    """FastAPI dependency: return the StorageProvider attached at startup.

    None if the lifespan failed to wire it (degraded startup). Callers
    should pass the result into `resolve_slide_path` which falls back to
    the legacy slide_scanner in that case.
    """
    return getattr(request.app.state, "storage_provider", None)


async def resolve_slide_path(
    storage: "Optional[StorageProvider]", slide_id: str
) -> str:
    """Return the absolute slide path, raising HTTPException(404) if missing.

    Migration path:
    - When storage is set: calls `await storage.get_slide_path(slide_id)`
      and translates SlideNotFoundError → HTTPException(404).
    - When storage is None: falls back to the legacy slide_scanner so the
      route stays operational on a degraded backend.

    Once every route has migrated and the slide_scanner direct imports
    are removed, this helper becomes a thin wrapper around
    `provider.get_slide_path` and the legacy branch can be deleted.
    """
    if storage is not None:
        try:
            path = await storage.get_slide_path(slide_id)
            return str(path)
        except SlideNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
    # Legacy fallback (degraded startup / pre-migration tests).
    path = get_slide_path_by_id(slide_id)
    if not path:
        raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
    return path


__all__ = ["emit_workflow_event", "get_storage", "resolve_slide_path"]


# ---------------------------------------------------------------------------
# WorkflowHook event emission (sprint 5)
# ---------------------------------------------------------------------------


async def emit_workflow_event(request: Request, event: "WorkflowEvent") -> None:
    """Fire a WorkflowEvent through `request.app.state.workflow_hook`.

    Records the outcome via `monitoring.record_workflow_event`. NEVER
    raises — by Protocol contract the hook must not fail callers, and we
    add a defensive try/except in case a hook breaks the contract.

    Args:
        request: FastAPI request (used to read app.state.workflow_hook).
        event: A WorkflowEvent instance.
    """
    hook = getattr(request.app.state, "workflow_hook", None)
    if hook is None:
        return

    try:
        ok = await hook.on_event(event)
        record_workflow_event(
            event_type=event.event_type.value,
            hook_type=type(hook).__name__,
            status="success" if ok else "partial_failure",
        )
    except Exception as e:
        logger.warning("workflow_hook.on_event raised: %s", e)
        record_workflow_event(
            event_type=event.event_type.value,
            hook_type=type(hook).__name__,
            status="exception",
        )
