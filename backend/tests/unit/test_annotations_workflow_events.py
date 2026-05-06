"""Sprint 5 — verifies that the emit_workflow_event helper increments
the right Prometheus counter labels for each WorkflowHook outcome.

The annotation routes themselves require a real PostgreSQL connection
to test end-to-end (annotation_service queries spatial geometry tables).
That's covered by the existing integration tests in test_annotations_api.py.
Here we just unit-test the emit_workflow_event helper which the new route
code relies on — every route uses the same code path, so testing the
helper covers all 3 mutations (create / validate / delete).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI

from core.interfaces.workflow import WorkflowEvent, WorkflowEventType
from routes._storage_helpers import emit_workflow_event


def _request_with_hook(hook):
    """Build a minimal Request stand-in exposing app.state.workflow_hook."""
    app = FastAPI()
    app.state.workflow_hook = hook

    request = MagicMock()
    request.app = app
    return request


@pytest.mark.asyncio
async def test_emit_records_success_when_hook_returns_true():
    hook = MagicMock()
    hook.on_event = AsyncMock(return_value=True)
    type(hook).__name__ = "FHIRWorkflowHook"

    event = WorkflowEvent(
        event_type=WorkflowEventType.ANNOTATION_CREATED,
        slide_id="slide-1",
        user_id="dr.test",
    )

    with patch("routes._storage_helpers.record_workflow_event") as mock_record:
        await emit_workflow_event(_request_with_hook(hook), event)

    hook.on_event.assert_awaited_once_with(event)
    mock_record.assert_called_once_with(
        event_type="annotation_created",
        hook_type="FHIRWorkflowHook",
        status="success",
    )


@pytest.mark.asyncio
async def test_emit_records_partial_failure_when_hook_returns_false():
    hook = MagicMock()
    hook.on_event = AsyncMock(return_value=False)
    type(hook).__name__ = "CompositeWorkflowHook"

    event = WorkflowEvent(
        event_type=WorkflowEventType.ANNOTATION_UPDATED,
        slide_id="slide-1",
    )

    with patch("routes._storage_helpers.record_workflow_event") as mock_record:
        await emit_workflow_event(_request_with_hook(hook), event)

    assert mock_record.call_args.kwargs["status"] == "partial_failure"


@pytest.mark.asyncio
async def test_emit_records_exception_when_hook_raises():
    """A broken hook (contract violation) doesn't break the calling route."""
    hook = MagicMock()
    hook.on_event = AsyncMock(side_effect=RuntimeError("hook went boom"))
    type(hook).__name__ = "BrokenHook"

    event = WorkflowEvent(
        event_type=WorkflowEventType.ANNOTATION_DELETED, slide_id="slide-1"
    )

    with patch("routes._storage_helpers.record_workflow_event") as mock_record:
        # MUST NOT raise.
        await emit_workflow_event(_request_with_hook(hook), event)

    assert mock_record.call_args.kwargs["status"] == "exception"


@pytest.mark.asyncio
async def test_emit_silently_skips_when_no_hook_attached():
    request = MagicMock()
    request.app.state.workflow_hook = None  # explicit None (degraded startup)

    event = WorkflowEvent(
        event_type=WorkflowEventType.ANNOTATION_CREATED, slide_id="slide-1"
    )

    with patch("routes._storage_helpers.record_workflow_event") as mock_record:
        await emit_workflow_event(request, event)

    mock_record.assert_not_called()


@pytest.mark.asyncio
async def test_emit_silently_skips_when_app_state_missing():
    """If app.state has no `workflow_hook` attribute at all (older test apps),
    the helper degrades gracefully rather than raising AttributeError.
    """

    class _BareState:
        pass

    request = MagicMock()
    request.app.state = _BareState()

    event = WorkflowEvent(
        event_type=WorkflowEventType.ANNOTATION_DELETED, slide_id="slide-1"
    )

    with patch("routes._storage_helpers.record_workflow_event") as mock_record:
        await emit_workflow_event(request, event)

    mock_record.assert_not_called()
