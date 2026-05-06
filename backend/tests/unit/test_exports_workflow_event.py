"""Sprint 2 — verifies that exports.py emits WorkflowEvent(REPORT_SIGNED)
on successful DICOM export, and increments the workflow events counter
with the right labels.

The DICOMExportService.export() call is mocked since the export pipeline
needs OpenSlide + a real slide; we just need to verify the wiring.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import get_current_user
from auth.schemas import CurrentUser
from core.interfaces.workflow import WorkflowEventType


def _admin_user():
    return CurrentUser(
        sub="test-admin",
        username="admin",
        email=None,
        roles=["ADMIN_TECHNIQUE"],
        is_anonymous=False,
    )


@pytest.fixture
def app_with_workflow_hook():
    """Mount only the exports router with a stub workflow_hook in app.state."""
    from routes.exports import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = _admin_user
    return app


def _mock_export_result():
    """Build a mock DICOMExportResult-like object with the fields exports.py reads."""
    result = MagicMock()
    result.slide_id = "abc123"
    result.dicom_uid = "1.2.840.99999.1"
    result.status = "completed"
    result.output_path = "/exports/abc123.dcm"
    result.file_size_bytes = 1024
    result.frames_count = 10
    result.processing_time_ms = 250
    result.accession_number = "A-2026-001"
    return result


@pytest.mark.asyncio
async def test_export_dicom_emits_report_signed_event_on_success(app_with_workflow_hook):
    hook = MagicMock()
    hook.on_event = AsyncMock(return_value=True)
    type(hook).__name__ = "FHIRWorkflowHook"
    app_with_workflow_hook.state.workflow_hook = hook

    fake_export = _mock_export_result()

    with patch(
        "routes.exports.get_export_service",
        return_value=MagicMock(export=MagicMock(return_value=fake_export)),
    ), TestClient(app_with_workflow_hook) as client:
        response = client.post("/exports/dicom/abc123?anonymize=true")

    assert response.status_code == 200
    assert response.json()["dicom_uid"] == "1.2.840.99999.1"

    # Hook was called exactly once with a REPORT_SIGNED event.
    hook.on_event.assert_awaited_once()
    event = hook.on_event.await_args.args[0]
    assert event.event_type == WorkflowEventType.REPORT_SIGNED
    assert event.slide_id == "abc123"
    assert event.user_id == "admin"
    assert event.metadata["accession_number"] == "A-2026-001"
    assert event.metadata["dicom_uid"] == "1.2.840.99999.1"
    assert event.metadata["anonymized"] is True


@pytest.mark.asyncio
async def test_export_dicom_records_success_metric_when_hook_returns_true(
    app_with_workflow_hook,
):
    hook = MagicMock()
    hook.on_event = AsyncMock(return_value=True)
    type(hook).__name__ = "CompositeWorkflowHook"
    app_with_workflow_hook.state.workflow_hook = hook

    fake_export = _mock_export_result()

    with patch(
        "routes.exports.get_export_service",
        return_value=MagicMock(export=MagicMock(return_value=fake_export)),
    ), patch("routes.exports.record_workflow_event") as mock_record, TestClient(
        app_with_workflow_hook
    ) as client:
        response = client.post("/exports/dicom/abc123")

    assert response.status_code == 200
    mock_record.assert_called_once_with(
        event_type="report_signed",
        hook_type="CompositeWorkflowHook",
        status="success",
    )


@pytest.mark.asyncio
async def test_export_dicom_records_partial_failure_when_hook_returns_false(
    app_with_workflow_hook,
):
    """Composite returns False if any sub-hook failed → status='partial_failure'."""
    hook = MagicMock()
    hook.on_event = AsyncMock(return_value=False)
    type(hook).__name__ = "CompositeWorkflowHook"
    app_with_workflow_hook.state.workflow_hook = hook

    with patch(
        "routes.exports.get_export_service",
        return_value=MagicMock(export=MagicMock(return_value=_mock_export_result())),
    ), patch("routes.exports.record_workflow_event") as mock_record, TestClient(
        app_with_workflow_hook
    ) as client:
        response = client.post("/exports/dicom/abc123")

    assert response.status_code == 200
    mock_record.assert_called_once()
    assert mock_record.call_args.kwargs["status"] == "partial_failure"


@pytest.mark.asyncio
async def test_export_dicom_records_exception_when_hook_raises(app_with_workflow_hook):
    """Defensive: if the hook breaks its contract and raises, we log + record."""
    hook = MagicMock()
    hook.on_event = AsyncMock(side_effect=RuntimeError("hook exploded"))
    type(hook).__name__ = "BrokenHook"
    app_with_workflow_hook.state.workflow_hook = hook

    with patch(
        "routes.exports.get_export_service",
        return_value=MagicMock(export=MagicMock(return_value=_mock_export_result())),
    ), patch("routes.exports.record_workflow_event") as mock_record, TestClient(
        app_with_workflow_hook
    ) as client:
        response = client.post("/exports/dicom/abc123")

    # Export response itself is unaffected by the hook failure.
    assert response.status_code == 200
    mock_record.assert_called_once()
    assert mock_record.call_args.kwargs["status"] == "exception"


@pytest.mark.asyncio
async def test_export_dicom_skips_emission_when_no_hook_configured(app_with_workflow_hook):
    """app.state.workflow_hook = None → emission silently skipped, export still 200."""
    app_with_workflow_hook.state.workflow_hook = None

    with patch(
        "routes.exports.get_export_service",
        return_value=MagicMock(export=MagicMock(return_value=_mock_export_result())),
    ), patch("routes.exports.record_workflow_event") as mock_record, TestClient(
        app_with_workflow_hook
    ) as client:
        response = client.post("/exports/dicom/abc123")

    assert response.status_code == 200
    mock_record.assert_not_called()


@pytest.mark.asyncio
async def test_export_dicom_does_not_emit_event_when_export_fails(
    app_with_workflow_hook,
):
    """Export failure → 500, NO WorkflowEvent (the report wasn't actually signed)."""
    hook = MagicMock()
    hook.on_event = AsyncMock(return_value=True)
    app_with_workflow_hook.state.workflow_hook = hook

    failing_service = MagicMock()
    failing_service.export = MagicMock(side_effect=RuntimeError("boom"))

    with patch("routes.exports.get_export_service", return_value=failing_service), TestClient(
        app_with_workflow_hook
    ) as client:
        response = client.post("/exports/dicom/abc123")

    assert response.status_code == 500
    hook.on_event.assert_not_awaited()
