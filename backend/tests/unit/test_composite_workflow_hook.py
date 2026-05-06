"""Unit tests for CompositeWorkflowHook — verifies fan-out / aggregation.

Each registered hook is an AsyncMock so we can drive its return values
deterministically without spawning real FHIR / PACS dependencies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.interfaces import WorkflowHook
from core.interfaces.workflow import WorkflowEvent, WorkflowEventType
from services.workflow.composite_hook import CompositeWorkflowHook


def _hook(name: str = "h") -> AsyncMock:
    """Build a hook mock with sensible default returns for every Protocol method."""
    m = AsyncMock()
    m.on_event = AsyncMock(return_value=True)
    m.query_worklist = AsyncMock(return_value=[])
    m.update_worklist = AsyncMock(return_value=True)
    m.send_result = AsyncMock(return_value=True)
    m.get_patient_info = AsyncMock(return_value=None)
    m.validate_configuration = AsyncMock(
        return_value={
            "connection": True,
            "authentication": True,
            "permissions": True,
            "version_compatible": True,
        }
    )
    type(m).__name__ = name
    return m


def test_protocol_conformance():
    composite = CompositeWorkflowHook(hooks=[_hook("a"), _hook("b")])
    assert isinstance(composite, WorkflowHook)


def test_add_remove_get_hooks():
    composite = CompositeWorkflowHook()
    a = _hook("a")
    b = _hook("b")
    composite.add_hook(a)
    composite.add_hook(b)
    assert composite.get_hooks() == [a, b]
    composite.remove_hook(a)
    assert composite.get_hooks() == [b]


def test_add_hook_is_idempotent():
    composite = CompositeWorkflowHook()
    a = _hook("a")
    composite.add_hook(a)
    composite.add_hook(a)
    assert composite.get_hooks() == [a]


# ---------------------------------------------------------------------------
# on_event fan-out
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_event_fans_out_to_all_hooks():
    a, b = _hook("a"), _hook("b")
    composite = CompositeWorkflowHook(hooks=[a, b])
    event = WorkflowEvent(event_type=WorkflowEventType.REPORT_SIGNED, slide_id="s1")
    ok = await composite.on_event(event)
    assert ok is True
    a.on_event.assert_awaited_once_with(event)
    b.on_event.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_on_event_returns_false_when_any_hook_returns_false():
    a, b = _hook("a"), _hook("b")
    b.on_event.return_value = False
    composite = CompositeWorkflowHook(hooks=[a, b])
    event = WorkflowEvent(event_type=WorkflowEventType.REPORT_SIGNED, slide_id="s1")
    assert await composite.on_event(event) is False


@pytest.mark.asyncio
async def test_on_event_swallows_exceptions_and_logs():
    a, b = _hook("a"), _hook("b")
    a.on_event.side_effect = RuntimeError("FHIR exploded")
    composite = CompositeWorkflowHook(hooks=[a, b])
    event = WorkflowEvent(event_type=WorkflowEventType.REPORT_SIGNED, slide_id="s1")
    ok = await composite.on_event(event)
    # Exception in 'a' must NOT prevent 'b' from being called.
    assert b.on_event.await_count == 1
    # Aggregate result is False because one failed.
    assert ok is False


@pytest.mark.asyncio
async def test_on_event_with_no_hooks_returns_true():
    composite = CompositeWorkflowHook()
    event = WorkflowEvent(event_type=WorkflowEventType.SLIDE_OPENED, slide_id="s1")
    assert await composite.on_event(event) is True


# ---------------------------------------------------------------------------
# query_worklist — first non-empty wins
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_worklist_returns_first_non_empty_response():
    a, b = _hook("a"), _hook("b")
    a.query_worklist.return_value = []
    b.query_worklist.return_value = [{"accession_number": "A-1"}]
    composite = CompositeWorkflowHook(hooks=[a, b])
    items = await composite.query_worklist()
    assert items == [{"accession_number": "A-1"}]


@pytest.mark.asyncio
async def test_query_worklist_skips_not_implemented():
    a, b = _hook("a"), _hook("b")
    a.query_worklist.side_effect = NotImplementedError
    b.query_worklist.return_value = [{"accession_number": "A-2"}]
    composite = CompositeWorkflowHook(hooks=[a, b])
    items = await composite.query_worklist()
    assert items == [{"accession_number": "A-2"}]


@pytest.mark.asyncio
async def test_query_worklist_returns_empty_when_all_empty():
    composite = CompositeWorkflowHook(hooks=[_hook(), _hook()])
    assert await composite.query_worklist() == []


# ---------------------------------------------------------------------------
# get_patient_info — first non-None wins
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_patient_info_returns_first_non_none():
    a, b = _hook("a"), _hook("b")
    a.get_patient_info.return_value = None
    b.get_patient_info.return_value = {"PatientID": "p-42"}
    composite = CompositeWorkflowHook(hooks=[a, b])
    info = await composite.get_patient_info("p-42")
    assert info == {"PatientID": "p-42"}


# ---------------------------------------------------------------------------
# update_worklist — NotImplementedError counts as 'skipped' (does not fail)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_worklist_treats_not_implemented_as_skipped():
    a, b = _hook("a"), _hook("b")
    a.update_worklist.side_effect = NotImplementedError("PACS REST URL unset")
    b.update_worklist.return_value = True
    composite = CompositeWorkflowHook(hooks=[a, b])
    ok = await composite.update_worklist("A-1", "IN_PROGRESS")
    assert ok is True


@pytest.mark.asyncio
async def test_update_worklist_returns_false_on_real_failure():
    a, b = _hook("a"), _hook("b")
    a.update_worklist.return_value = True
    b.update_worklist.return_value = False
    composite = CompositeWorkflowHook(hooks=[a, b])
    assert await composite.update_worklist("A-1", "IN_PROGRESS") is False


# ---------------------------------------------------------------------------
# send_result — all hooks must succeed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_result_dispatches_to_all_hooks():
    a, b = _hook("a"), _hook("b")
    composite = CompositeWorkflowHook(hooks=[a, b])
    ok = await composite.send_result("A-1", {"slide_id": "s"})
    assert ok is True
    a.send_result.assert_awaited_once()
    b.send_result.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_result_returns_false_when_any_fails():
    a, b = _hook("a"), _hook("b")
    b.send_result.side_effect = RuntimeError("FHIR down")
    composite = CompositeWorkflowHook(hooks=[a, b])
    assert await composite.send_result("A-1", {}) is False


# ---------------------------------------------------------------------------
# validate_configuration — AND aggregation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_configuration_ands_each_flag_across_hooks():
    a, b = _hook("a"), _hook("b")
    a.validate_configuration.return_value = {
        "connection": True,
        "authentication": True,
        "permissions": False,
        "version_compatible": True,
    }
    b.validate_configuration.return_value = {
        "connection": True,
        "authentication": True,
        "permissions": True,
        "version_compatible": True,
    }
    composite = CompositeWorkflowHook(hooks=[a, b])
    flags = await composite.validate_configuration()
    assert flags == {
        "connection": True,
        "authentication": True,
        "permissions": False,  # AND of (False, True) = False
        "version_compatible": True,
    }


@pytest.mark.asyncio
async def test_validate_configuration_with_no_hooks_is_vacuously_true():
    flags = await CompositeWorkflowHook().validate_configuration()
    assert all(flags.values())
