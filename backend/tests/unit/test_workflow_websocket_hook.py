"""Sprint 15 — verifies WebSocketWorkflowHook publishes events to the
in-process broadcaster, and that the broadcaster fans them to subscribers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.interfaces import WorkflowHook
from core.interfaces.workflow import WorkflowEvent, WorkflowEventType
from services.workflow.event_broadcaster import (
    WorkflowEventBroadcaster,
    get_broadcaster,
    reset_broadcaster,
)
from services.workflow.websocket_hook import WebSocketWorkflowHook, _event_to_dict


@pytest.fixture(autouse=True)
def _reset_broadcaster():
    reset_broadcaster()
    yield
    reset_broadcaster()


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_websocket_hook_satisfies_workflow_protocol():
    assert isinstance(WebSocketWorkflowHook(), WorkflowHook)


# ---------------------------------------------------------------------------
# Event serialisation
# ---------------------------------------------------------------------------


def test_event_to_dict_uses_enum_value_for_event_type():
    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED,
        slide_id="slide-1",
        user_id="dr.test",
        metadata={"foo": "bar"},
    )
    payload = _event_to_dict(event)
    assert payload["event_type"] == "report_signed"
    assert payload["slide_id"] == "slide-1"
    assert payload["user_id"] == "dr.test"
    assert payload["metadata"] == {"foo": "bar"}


def test_event_to_dict_serialises_timestamp_to_iso():
    ts = datetime(2026, 5, 6, 12, 0, 0, tzinfo=UTC)
    event = WorkflowEvent(
        event_type=WorkflowEventType.ANNOTATION_CREATED,
        slide_id="slide-1",
        timestamp=ts,
    )
    payload = _event_to_dict(event)
    assert payload["timestamp"] == "2026-05-06T12:00:00+00:00"


def test_event_to_dict_handles_missing_metadata():
    event = WorkflowEvent(
        event_type=WorkflowEventType.SLIDE_OPENED,
        slide_id="slide-1",
    )
    payload = _event_to_dict(event)
    assert payload["metadata"] == {}


# ---------------------------------------------------------------------------
# Broadcaster behaviour
# ---------------------------------------------------------------------------


def test_get_broadcaster_returns_singleton():
    a = get_broadcaster()
    b = get_broadcaster()
    assert a is b


@pytest.mark.asyncio
async def test_broadcaster_subscribe_publish_unsubscribe():
    bc = WorkflowEventBroadcaster()
    ws = MagicMock()
    ws.send_json = AsyncMock()

    await bc.subscribe(ws)
    assert bc.subscriber_count() == 1

    delivered = await bc.publish({"event_type": "test"})
    assert delivered == 1
    ws.send_json.assert_awaited_once_with({"event_type": "test"})

    await bc.unsubscribe(ws)
    assert bc.subscriber_count() == 0


@pytest.mark.asyncio
async def test_broadcaster_drops_failing_subscriber():
    """A subscriber that raises during send_json is silently removed."""
    bc = WorkflowEventBroadcaster()
    good = MagicMock()
    good.send_json = AsyncMock()
    bad = MagicMock()
    bad.send_json = AsyncMock(side_effect=ConnectionError("dead"))

    await bc.subscribe(good)
    await bc.subscribe(bad)

    delivered = await bc.publish({"event_type": "test"})
    assert delivered == 1  # only `good` got it

    # Bad subscriber must have been dropped after the publish.
    assert bc.subscriber_count() == 1


@pytest.mark.asyncio
async def test_broadcaster_publishes_to_zero_subscribers_silently():
    bc = WorkflowEventBroadcaster()
    delivered = await bc.publish({"event_type": "test"})
    assert delivered == 0


# ---------------------------------------------------------------------------
# WebSocketWorkflowHook end-to-end
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hook_on_event_publishes_via_broadcaster():
    hook = WebSocketWorkflowHook()
    ws = MagicMock()
    ws.send_json = AsyncMock()
    await get_broadcaster().subscribe(ws)

    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED,
        slide_id="slide-1",
        user_id="dr.test",
        metadata={"accession_number": "A-1"},
    )

    ok = await hook.on_event(event)
    assert ok is True

    ws.send_json.assert_awaited_once()
    payload = ws.send_json.await_args.args[0]
    assert payload["event_type"] == "report_signed"
    assert payload["slide_id"] == "slide-1"
    assert payload["metadata"]["accession_number"] == "A-1"


@pytest.mark.asyncio
async def test_hook_on_event_returns_true_with_zero_subscribers():
    """No subscribers connected → publish to nobody, but on_event still True."""
    hook = WebSocketWorkflowHook()
    event = WorkflowEvent(event_type=WorkflowEventType.SLIDE_OPENED, slide_id="slide-1")
    assert await hook.on_event(event) is True


@pytest.mark.asyncio
async def test_hook_on_event_swallows_publish_failure():
    """If the broadcaster.publish raises (unexpected), on_event returns False
    rather than propagating — Protocol contract says hooks don't raise."""
    hook = WebSocketWorkflowHook()
    hook._broadcaster = MagicMock()
    hook._broadcaster.publish = AsyncMock(side_effect=RuntimeError("boom"))

    event = WorkflowEvent(event_type=WorkflowEventType.ANNOTATION_DELETED, slide_id="slide-1")
    assert await hook.on_event(event) is False


@pytest.mark.asyncio
async def test_hook_other_protocol_methods_return_safe_defaults():
    """Read methods are no-ops (a WS hook is event-only); write methods
    succeed silently so Composite aggregation isn't poisoned."""
    hook = WebSocketWorkflowHook()
    assert await hook.query_worklist({}) == []
    assert await hook.update_worklist("A", "in_progress") is True
    assert await hook.send_result("A", {}) is True
    assert await hook.get_patient_info("p") is None
    flags = await hook.validate_configuration()
    assert all(flags.values())


# ---------------------------------------------------------------------------
# Factory inclusion
# ---------------------------------------------------------------------------


def test_factory_includes_websocket_hook_by_default(monkeypatch):
    monkeypatch.delenv("WORKFLOW_WS_BROADCAST_ENABLED", raising=False)
    monkeypatch.delenv("FHIR_ENABLED", raising=False)
    monkeypatch.delenv("PACS_ENABLED", raising=False)

    from services.workflow import get_workflow_hook

    hook = get_workflow_hook()
    # Only WS active → returns WebSocketWorkflowHook directly (not Composite).
    assert isinstance(hook, WebSocketWorkflowHook)


def test_factory_omits_websocket_hook_when_disabled(monkeypatch):
    """WORKFLOW_WS_BROADCAST_ENABLED=false opts out (e.g. headless workers)."""
    monkeypatch.setenv("WORKFLOW_WS_BROADCAST_ENABLED", "false")
    monkeypatch.delenv("FHIR_ENABLED", raising=False)
    monkeypatch.delenv("PACS_ENABLED", raising=False)

    from services.workflow import NoOpWorkflowHook, get_workflow_hook

    hook = get_workflow_hook()
    assert isinstance(hook, NoOpWorkflowHook)
