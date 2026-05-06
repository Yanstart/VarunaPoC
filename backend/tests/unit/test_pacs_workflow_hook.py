"""Unit tests for PACSWorkflowHook.

`pynetdicom.AE.associate` is patched at the module boundary so these
tests run without a live Orthanc container. The integration test against
the real container lives at tests/integration/test_pacs_workflow_hook.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.exceptions.workflow import WorkflowIntegrationError
from core.interfaces import WorkflowHook
from core.interfaces.workflow import WorkflowEvent, WorkflowEventType
from services.workflow.pacs_config import PACSConfig, get_pacs_config
from services.workflow.pacs_hook import PACSWorkflowHook

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config(**overrides) -> PACSConfig:
    base = {
        "enabled": True,
        "host": "pacs.test.invalid",
        "dicom_port": 11112,
        "http_url": "http://orthanc.test.invalid:8042",
        "aet_local": "VARUNA_TEST",
        "aet_remote": "ORTHANC_TEST",
        "timeout_seconds": 1.0,
        "retry_max_attempts": 1,
        "retry_backoff_seconds": 0.0,
    }
    base.update(overrides)
    return PACSConfig(**base)


class _FakeStatus:
    """Minimal stand-in for a pydicom Dataset with .Status."""

    def __init__(self, status: int = 0x0000) -> None:
        self.Status = status


def _patch_associate(assoc_mock: MagicMock):
    """Patch the inner _associate_sync to return our fake (modules, assoc)."""
    fake_modules = {
        "Dataset": MagicMock,
        "AE": MagicMock(),
        "build_context": MagicMock(),
        "Verification": "1.2.840.10008.1.1",
        "ModalityWorklistInformationFind": "1.2.840.10008.5.1.4.31",
        "PatientRootQueryRetrieveInformationModelFind": "1.2.840.10008.5.1.4.1.2.1.1",
        "ComprehensiveSRStorage": "1.2.840.10008.5.1.4.1.1.88.33",
        "ExplicitVRLittleEndian": "1.2.840.10008.1.2.1",
        "ImplicitVRLittleEndian": "1.2.840.10008.1.2",
    }
    return patch.object(
        PACSWorkflowHook,
        "_associate_sync",
        return_value=(fake_modules, assoc_mock),
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_config_defaults_disabled():
    cfg = PACSConfig()
    assert cfg.is_configured is False


def test_config_requires_aet_local_and_remote():
    assert PACSConfig(enabled=True, aet_local="A").is_configured is False
    assert PACSConfig(enabled=True, aet_remote="B").is_configured is False
    assert PACSConfig(enabled=True, aet_local="A", aet_remote="B").is_configured is True


def test_config_has_http_fallback_only_when_url_set():
    assert PACSConfig(enabled=True).has_http_fallback is False
    assert (
        PACSConfig(enabled=True, http_url="http://x:8042").has_http_fallback is True
    )


def test_get_pacs_config_reads_environment(monkeypatch):
    monkeypatch.setenv("PACS_ENABLED", "true")
    monkeypatch.setenv("PACS_HOST", "pacs.example")
    monkeypatch.setenv("PACS_DICOM_PORT", "11112")
    monkeypatch.setenv("PACS_AET_LOCAL", "VARUNA")
    monkeypatch.setenv("PACS_AET_REMOTE", "ORTHANC")
    monkeypatch.setenv("PACS_HTTP_URL", "http://orthanc.example/")
    cfg = get_pacs_config()
    assert cfg.enabled is True
    assert cfg.host == "pacs.example"
    assert cfg.dicom_port == 11112
    assert cfg.aet_local == "VARUNA"
    assert cfg.aet_remote == "ORTHANC"
    assert cfg.http_url == "http://orthanc.example"  # trailing slash stripped


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_satisfies_workflow_protocol():
    assert isinstance(PACSWorkflowHook(), WorkflowHook)


# ---------------------------------------------------------------------------
# validate_configuration — C-ECHO
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_configuration_returns_all_false_when_not_configured():
    hook = PACSWorkflowHook(config=_config(enabled=False))
    flags = await hook.validate_configuration()
    assert all(v is False for v in flags.values())


@pytest.mark.asyncio
async def test_validate_configuration_marks_connection_true_on_c_echo_success():
    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_echo.return_value = _FakeStatus(0x0000)
    hook = PACSWorkflowHook(config=_config())
    with _patch_associate(assoc):
        flags = await hook.validate_configuration()
    assert flags["connection"] is True
    assert flags["authentication"] is True
    assert flags["version_compatible"] is True
    # permissions stays False — DICOM doesn't expose per-SOP allow-list.
    assert flags["permissions"] is False


@pytest.mark.asyncio
async def test_validate_configuration_returns_false_on_c_echo_failure():
    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_echo.return_value = _FakeStatus(0x0122)  # SOP class not supported
    hook = PACSWorkflowHook(config=_config())
    with _patch_associate(assoc):
        flags = await hook.validate_configuration()
    assert flags["connection"] is False


@pytest.mark.asyncio
async def test_validate_configuration_handles_association_rejection():
    """When association fails (rejected), all flags stay False."""
    hook = PACSWorkflowHook(config=_config())
    with patch.object(
        PACSWorkflowHook,
        "_associate_sync",
        side_effect=WorkflowIntegrationError("PACS", "rejected"),
    ):
        flags = await hook.validate_configuration()
    assert all(v is False for v in flags.values())


# ---------------------------------------------------------------------------
# get_patient_info — C-FIND Patient Root
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_patient_info_returns_none_when_not_configured():
    hook = PACSWorkflowHook(config=_config(enabled=False))
    assert await hook.get_patient_info("p-42") is None


@pytest.mark.asyncio
async def test_get_patient_info_returns_dict_on_match():
    """Simulate a C-FIND response with one pending match."""
    # pynetdicom's send_c_find yields (status, identifier) tuples.
    identifier = MagicMock()
    # Make iter() over the dataset yield one element.
    elem = MagicMock()
    elem.VR = "PN"
    elem.keyword = "PatientName"
    elem.value = "Test^Patient"
    identifier.__iter__ = MagicMock(return_value=iter([elem]))

    pending = (_FakeStatus(0xFF00), identifier)
    final = (_FakeStatus(0x0000), None)

    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_find.return_value = iter([pending, final])

    hook = PACSWorkflowHook(config=_config())
    with _patch_associate(assoc):
        info = await hook.get_patient_info("p-42")
    assert info == {"PatientName": "Test^Patient"}


@pytest.mark.asyncio
async def test_get_patient_info_returns_none_on_no_match():
    """Only a final-status response, no pending matches → None."""
    final = (_FakeStatus(0x0000), None)
    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_find.return_value = iter([final])
    hook = PACSWorkflowHook(config=_config())
    with _patch_associate(assoc):
        assert await hook.get_patient_info("p-missing") is None


@pytest.mark.asyncio
async def test_get_patient_info_returns_none_on_association_failure():
    hook = PACSWorkflowHook(config=_config())
    with patch.object(
        PACSWorkflowHook,
        "_associate_sync",
        side_effect=WorkflowIntegrationError("PACS", "down"),
    ):
        assert await hook.get_patient_info("p-42") is None


# ---------------------------------------------------------------------------
# query_worklist — C-FIND MWL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_worklist_returns_empty_when_not_configured():
    hook = PACSWorkflowHook(config=_config(enabled=False))
    assert await hook.query_worklist({"patient_id": "p"}) == []


@pytest.mark.asyncio
async def test_query_worklist_collects_pending_results():
    elem1 = MagicMock(VR="LO", keyword="AccessionNumber", value="A-1")
    id1 = MagicMock()
    id1.__iter__ = MagicMock(return_value=iter([elem1]))

    elem2 = MagicMock(VR="LO", keyword="AccessionNumber", value="A-2")
    id2 = MagicMock()
    id2.__iter__ = MagicMock(return_value=iter([elem2]))

    responses = [
        (_FakeStatus(0xFF00), id1),
        (_FakeStatus(0xFF00), id2),
        (_FakeStatus(0x0000), None),
    ]

    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_find.return_value = iter(responses)

    hook = PACSWorkflowHook(config=_config())
    with _patch_associate(assoc):
        items = await hook.query_worklist({"modality": "SM"})
    assert items == [{"AccessionNumber": "A-1"}, {"AccessionNumber": "A-2"}]


# ---------------------------------------------------------------------------
# update_worklist — fallback / not-implemented
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_worklist_raises_not_implemented_without_http_url():
    hook = PACSWorkflowHook(config=_config(http_url=""))
    with pytest.raises(NotImplementedError):
        await hook.update_worklist("A-1", "IN_PROGRESS")


@pytest.mark.asyncio
async def test_update_worklist_returns_true_when_http_url_set():
    """The fallback is a stub today (logs and returns True)."""
    hook = PACSWorkflowHook(config=_config())
    assert await hook.update_worklist("A-1", "IN_PROGRESS") is True


# ---------------------------------------------------------------------------
# send_result — C-STORE SR
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_result_returns_true_on_c_store_success():
    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_store.return_value = _FakeStatus(0x0000)
    hook = PACSWorkflowHook(config=_config())
    with _patch_associate(assoc):
        ok = await hook.send_result(
            "A-1",
            {"patient_id": "p", "patient_name": "T", "conclusion": "Benign"},
        )
    assert ok is True


@pytest.mark.asyncio
async def test_send_result_raises_on_c_store_failure_status():
    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_store.return_value = _FakeStatus(0xA700)  # Refused: out of resources
    hook = PACSWorkflowHook(config=_config())
    with _patch_associate(assoc), pytest.raises(WorkflowIntegrationError):
        await hook.send_result("A-1", {"patient_id": "p"})


@pytest.mark.asyncio
async def test_send_result_raises_when_association_fails():
    hook = PACSWorkflowHook(config=_config())
    with patch.object(
        PACSWorkflowHook,
        "_associate_sync",
        side_effect=WorkflowIntegrationError("PACS", "rejected"),
    ), pytest.raises(WorkflowIntegrationError):
        await hook.send_result("A-1", {})


# ---------------------------------------------------------------------------
# on_event — REPORT_SIGNED delegates to send_result; others logged only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_event_report_signed_delegates_to_send_result():
    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_store.return_value = _FakeStatus(0x0000)
    hook = PACSWorkflowHook(config=_config())
    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED,
        slide_id="slide-1",
        metadata={
            "accession_number": "A-1",
            "patient_id": "p-42",
            "conclusion": "Benign",
        },
    )
    with _patch_associate(assoc):
        ok = await hook.on_event(event)
    assert ok is True
    assoc.send_c_store.assert_called_once()


@pytest.mark.asyncio
async def test_on_event_swallows_failure():
    """on_event NEVER raises; failures return False but don't propagate."""
    assoc = MagicMock()
    assoc.is_established = True
    assoc.send_c_store.return_value = _FakeStatus(0xA700)
    hook = PACSWorkflowHook(config=_config())
    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED,
        slide_id="slide-1",
        metadata={"accession_number": "A-1"},
    )
    with _patch_associate(assoc):
        ok = await hook.on_event(event)
    assert ok is False


@pytest.mark.asyncio
async def test_on_event_other_types_skip_dicom_call():
    hook = PACSWorkflowHook(config=_config())
    with patch.object(PACSWorkflowHook, "_associate_sync") as mock:
        for evt in (
            WorkflowEventType.SLIDE_OPENED,
            WorkflowEventType.ANNOTATION_CREATED,
            WorkflowEventType.ML_INFERENCE_COMPLETED,
        ):
            ok = await hook.on_event(WorkflowEvent(event_type=evt, slide_id="x"))
            assert ok is True
        mock.assert_not_called()


@pytest.mark.asyncio
async def test_on_event_short_circuits_when_not_configured():
    hook = PACSWorkflowHook(config=_config(enabled=False))
    with patch.object(PACSWorkflowHook, "_associate_sync") as mock:
        ok = await hook.on_event(
            WorkflowEvent(event_type=WorkflowEventType.REPORT_SIGNED, slide_id="x")
        )
    assert ok is True
    mock.assert_not_called()


# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_associate_retries_then_raises():
    """All retries fail → WorkflowIntegrationError. Counts attempts."""
    cfg = _config(retry_max_attempts=3, retry_backoff_seconds=0.0)
    hook = PACSWorkflowHook(config=cfg)
    with patch.object(
        PACSWorkflowHook,
        "_associate_sync",
        side_effect=WorkflowIntegrationError("PACS", "down"),
    ) as mock, pytest.raises(WorkflowIntegrationError):
        await hook.send_result("A", {})
    assert mock.call_count == 3
