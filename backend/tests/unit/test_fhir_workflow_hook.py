"""Unit tests for FHIRWorkflowHook + NoOpWorkflowHook + fhir.config.

The HTTP layer is faked with httpx.MockTransport so these tests run
without spinning up HAPI FHIR. The integration test against the real
container lives at tests/integration/test_fhir_workflow_hook.py.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
import pytest

from core.exceptions.workflow import WorkflowIntegrationError
from core.interfaces import WorkflowHook
from core.interfaces.workflow import WorkflowEvent, WorkflowEventType
from fhir.config import FHIRConfig, get_fhir_config
from services.workflow import (
    FHIRWorkflowHook,
    NoOpWorkflowHook,
    get_workflow_hook,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config(**overrides) -> FHIRConfig:
    base = {
        "enabled": True,
        "base_url": "http://fhir-test.invalid/fhir",
        "auth_token": "",
        "timeout_seconds": 5.0,
        "retry_max_attempts": 1,  # tests should be fast — usually no retry
        "retry_backoff_seconds": 0.0,
    }
    base.update(overrides)
    return FHIRConfig(**base)


class _Recorder:
    """Capture every request that hits the MockTransport."""

    def __init__(self) -> None:
        self.requests: List[httpx.Request] = []

    def __call__(self, handler):
        def wrapped(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return handler(request)

        return wrapped


def _build_hook(handler, *, config: FHIRConfig | None = None) -> FHIRWorkflowHook:
    """Wire a FHIRWorkflowHook with an injected MockTransport client."""
    transport = httpx.MockTransport(handler)
    cfg = config or _config()
    headers = {
        "Accept": "application/fhir+json",
        "Content-Type": "application/fhir+json",
    }
    if cfg.auth_token:
        headers["Authorization"] = f"Bearer {cfg.auth_token}"
    client = httpx.AsyncClient(
        transport=transport, base_url=cfg.base_url, headers=headers, timeout=cfg.timeout_seconds
    )
    return FHIRWorkflowHook(config=cfg, client=client)


# ---------------------------------------------------------------------------
# FHIRConfig
# ---------------------------------------------------------------------------


def test_config_defaults_disabled():
    """get_fhir_config() with no env returns enabled=False, is_configured=False."""
    cfg = FHIRConfig()
    assert cfg.is_configured is False


def test_config_is_configured_requires_base_url():
    cfg = FHIRConfig(enabled=True, base_url="")
    assert cfg.is_configured is False


def test_config_is_configured_when_both_set():
    cfg = FHIRConfig(enabled=True, base_url="http://x/fhir")
    assert cfg.is_configured is True


def test_config_metadata_url_strips_trailing_slash():
    cfg = FHIRConfig(enabled=True, base_url="http://x/fhir/")
    assert cfg.metadata_url == "http://x/fhir/metadata"


def test_get_fhir_config_reads_environment(monkeypatch):
    monkeypatch.setenv("FHIR_ENABLED", "true")
    monkeypatch.setenv("FHIR_BASE_URL", "http://hapi/fhir/")
    monkeypatch.setenv("FHIR_TIMEOUT_SECONDS", "20")
    monkeypatch.setenv("FHIR_RETRY_MAX_ATTEMPTS", "5")
    cfg = get_fhir_config()
    assert cfg.enabled is True
    assert cfg.base_url == "http://hapi/fhir"  # trailing slash stripped
    assert cfg.timeout_seconds == 20.0
    assert cfg.retry_max_attempts == 5


def test_get_fhir_config_handles_invalid_numbers(monkeypatch):
    monkeypatch.setenv("FHIR_TIMEOUT_SECONDS", "not-a-number")
    cfg = get_fhir_config()
    assert cfg.timeout_seconds == 10.0  # default


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_fhir_hook_satisfies_workflow_protocol():
    assert isinstance(FHIRWorkflowHook(), WorkflowHook)


def test_no_op_hook_satisfies_workflow_protocol():
    assert isinstance(NoOpWorkflowHook(), WorkflowHook)


def test_get_workflow_hook_returns_no_op_when_nothing_configured(monkeypatch):
    monkeypatch.delenv("FHIR_ENABLED", raising=False)
    monkeypatch.delenv("PACS_ENABLED", raising=False)
    hook = get_workflow_hook()
    assert isinstance(hook, NoOpWorkflowHook)


def test_get_workflow_hook_returns_fhir_when_only_fhir_configured(monkeypatch):
    monkeypatch.setenv("FHIR_ENABLED", "true")
    monkeypatch.setenv("FHIR_BASE_URL", "http://hapi/fhir")
    monkeypatch.delenv("PACS_ENABLED", raising=False)
    hook = get_workflow_hook()
    assert isinstance(hook, FHIRWorkflowHook)


def test_get_workflow_hook_returns_pacs_when_only_pacs_configured(monkeypatch):
    from services.workflow import PACSWorkflowHook

    monkeypatch.delenv("FHIR_ENABLED", raising=False)
    monkeypatch.setenv("PACS_ENABLED", "true")
    monkeypatch.setenv("PACS_AET_LOCAL", "VARUNA")
    monkeypatch.setenv("PACS_AET_REMOTE", "ORTHANC")
    hook = get_workflow_hook()
    assert isinstance(hook, PACSWorkflowHook)


def test_get_workflow_hook_returns_composite_when_both_configured(monkeypatch):
    from services.workflow import CompositeWorkflowHook

    monkeypatch.setenv("FHIR_ENABLED", "true")
    monkeypatch.setenv("FHIR_BASE_URL", "http://hapi/fhir")
    monkeypatch.setenv("PACS_ENABLED", "true")
    monkeypatch.setenv("PACS_AET_LOCAL", "VARUNA")
    monkeypatch.setenv("PACS_AET_REMOTE", "ORTHANC")
    hook = get_workflow_hook()
    assert isinstance(hook, CompositeWorkflowHook)
    assert len(hook.get_hooks()) == 2


# ---------------------------------------------------------------------------
# NoOp hook
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_noop_on_event_returns_true():
    hook = NoOpWorkflowHook()
    event = WorkflowEvent(event_type=WorkflowEventType.SLIDE_OPENED, slide_id="abc")
    assert await hook.on_event(event) is True


@pytest.mark.asyncio
async def test_noop_get_patient_returns_none():
    hook = NoOpWorkflowHook()
    assert await hook.get_patient_info("123") is None


@pytest.mark.asyncio
async def test_noop_validate_configuration_all_true():
    hook = NoOpWorkflowHook()
    flags = await hook.validate_configuration()
    assert all(flags.values())


# ---------------------------------------------------------------------------
# on_event REPORT_SIGNED — happy path & failure path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_event_report_signed_posts_diagnostic_report():
    posted: Dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        posted["url"] = str(request.url)
        posted["body"] = json.loads(request.content)
        return httpx.Response(201, json={"resourceType": "DiagnosticReport", "id": "r1"})

    hook = _build_hook(handler)
    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED,
        slide_id="slide-1",
        user_id="dr.martin",
        metadata={
            "patient_id": "p-42",
            "patient_name": "Test Patient",
            "performer_name": "Dr Martin",
            "annotations_count": 3,
            "conclusion": "Benign tissue",
        },
    )
    ok = await hook.on_event(event)
    assert ok is True
    assert posted["url"].endswith("/DiagnosticReport")
    assert posted["body"]["resourceType"] == "DiagnosticReport"
    await hook.aclose()


@pytest.mark.asyncio
async def test_on_event_report_signed_swallows_server_5xx():
    """on_event must NOT raise when the FHIR server is down — it returns False."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    hook = _build_hook(handler)
    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED,
        slide_id="slide-1",
        user_id="dr.martin",
        metadata={"patient_id": "p-42"},
    )
    ok = await hook.on_event(event)
    assert ok is False
    await hook.aclose()


@pytest.mark.asyncio
async def test_on_event_other_types_skip_fhir_call():
    """SLIDE_OPENED, ML_INFERENCE_COMPLETED, etc. are logged only — no POST."""
    seen: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201)

    hook = _build_hook(handler)
    for evt_type in (
        WorkflowEventType.SLIDE_OPENED,
        WorkflowEventType.ANNOTATION_CREATED,
        WorkflowEventType.ML_INFERENCE_COMPLETED,
    ):
        ok = await hook.on_event(WorkflowEvent(event_type=evt_type, slide_id="x"))
        assert ok is True
    assert seen == []
    await hook.aclose()


@pytest.mark.asyncio
async def test_on_event_short_circuits_when_not_configured():
    """When FHIR_ENABLED=false, on_event returns True without trying any HTTP."""
    seen: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201)

    cfg = _config(enabled=False)
    hook = _build_hook(handler, config=cfg)
    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED, slide_id="x", metadata={"patient_id": "p"}
    )
    assert await hook.on_event(event) is True
    assert seen == []
    await hook.aclose()


# ---------------------------------------------------------------------------
# send_result — raises on failure (unlike on_event)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_result_returns_true_on_201():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"resourceType": "DiagnosticReport", "id": "r2"})

    hook = _build_hook(handler)
    ok = await hook.send_result(
        accession_number="A2025-001",
        result={
            "slide_id": "slide-1",
            "patient_id": "p-42",
            "performer_name": "Dr Martin",
            "annotations_count": 5,
            "conclusion": "Benign",
        },
    )
    assert ok is True
    await hook.aclose()


@pytest.mark.asyncio
async def test_send_result_raises_workflow_integration_error_on_4xx():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text='{"resourceType":"OperationOutcome"}')

    hook = _build_hook(handler)
    with pytest.raises(WorkflowIntegrationError):
        await hook.send_result(
            accession_number="A2025-001", result={"slide_id": "slide-1"}
        )
    await hook.aclose()


@pytest.mark.asyncio
async def test_send_result_raises_workflow_integration_error_on_repeated_5xx():
    """500/503 are retried; if they keep failing, the call raises."""
    seen: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(503, text="Service Unavailable")

    cfg = _config(retry_max_attempts=3, retry_backoff_seconds=0.0)
    hook = _build_hook(handler, config=cfg)
    with pytest.raises(WorkflowIntegrationError):
        await hook.send_result(accession_number="A", result={"slide_id": "s"})
    assert len(seen) == 3  # initial + 2 retries
    await hook.aclose()


# ---------------------------------------------------------------------------
# get_patient_info
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_patient_info_returns_resource_on_200():
    patient = {"resourceType": "Patient", "id": "p-42", "name": [{"text": "Test"}]}

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/Patient/p-42" in str(request.url)
        return httpx.Response(200, json=patient)

    hook = _build_hook(handler)
    got = await hook.get_patient_info("p-42")
    assert got == patient
    await hook.aclose()


@pytest.mark.asyncio
async def test_get_patient_info_returns_none_on_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    hook = _build_hook(handler)
    assert await hook.get_patient_info("missing") is None
    await hook.aclose()


@pytest.mark.asyncio
async def test_get_patient_info_returns_none_when_not_configured():
    cfg = _config(enabled=False)
    hook = _build_hook(lambda _r: httpx.Response(200), config=cfg)
    assert await hook.get_patient_info("p-1") is None
    await hook.aclose()


# ---------------------------------------------------------------------------
# validate_configuration — capability statement parsing
# ---------------------------------------------------------------------------


def _capability(fhir_version: str = "4.0.1", resources: List[str] | None = None) -> Dict:
    if resources is None:
        resources = ["DiagnosticReport", "Patient"]
    return {
        "resourceType": "CapabilityStatement",
        "fhirVersion": fhir_version,
        "rest": [{"mode": "server", "resource": [{"type": r} for r in resources]}],
    }


@pytest.mark.asyncio
async def test_validate_configuration_all_green_for_r4_capability():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_capability())

    hook = _build_hook(handler)
    flags = await hook.validate_configuration()
    assert flags == {
        "connection": True,
        "authentication": True,
        "permissions": True,
        "version_compatible": True,
    }
    await hook.aclose()


@pytest.mark.asyncio
async def test_validate_configuration_marks_permissions_false_when_resource_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        # Patient is missing from the capability statement.
        return httpx.Response(200, json=_capability(resources=["DiagnosticReport"]))

    hook = _build_hook(handler)
    flags = await hook.validate_configuration()
    assert flags["connection"] is True
    assert flags["version_compatible"] is True
    assert flags["permissions"] is False
    await hook.aclose()


@pytest.mark.asyncio
async def test_validate_configuration_marks_version_false_for_r3():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_capability(fhir_version="3.0.2"))

    hook = _build_hook(handler)
    flags = await hook.validate_configuration()
    assert flags["version_compatible"] is False
    await hook.aclose()


@pytest.mark.asyncio
async def test_validate_configuration_marks_authentication_false_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    hook = _build_hook(handler)
    flags = await hook.validate_configuration()
    assert flags["connection"] is True
    assert flags["authentication"] is False
    assert flags["permissions"] is False
    await hook.aclose()


@pytest.mark.asyncio
async def test_validate_configuration_returns_all_false_when_not_configured():
    cfg = _config(enabled=False)
    hook = _build_hook(lambda _r: httpx.Response(200), config=cfg)
    flags = await hook.validate_configuration()
    assert all(v is False for v in flags.values())
    await hook.aclose()


# ---------------------------------------------------------------------------
# Stub methods (Task / Worklist) — explicitly raise
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_worklist_raises_not_implemented():
    hook = FHIRWorkflowHook()
    with pytest.raises(NotImplementedError):
        await hook.query_worklist({})


@pytest.mark.asyncio
async def test_update_worklist_raises_not_implemented():
    hook = FHIRWorkflowHook()
    with pytest.raises(NotImplementedError):
        await hook.update_worklist("A", "IN_PROGRESS")
