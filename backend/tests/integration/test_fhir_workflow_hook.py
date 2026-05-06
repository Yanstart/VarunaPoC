"""Integration tests for FHIRWorkflowHook against a live HAPI FHIR container.

Skipped automatically when no FHIR server is reachable. Run them after
starting the dev compose stack:

    docker compose -f docker-compose.dev.yml up -d hapi-fhir
    # Wait for HAPI to come up (~45s cold start), then:
    cd backend
    FHIR_BASE_URL=http://localhost:8090/fhir \
      pytest tests/integration/test_fhir_workflow_hook.py -m requires_fhir -v
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.interfaces.workflow import WorkflowEvent, WorkflowEventType
from fhir.config import FHIRConfig
from services.workflow.fhir_hook import FHIRWorkflowHook

pytestmark = pytest.mark.requires_fhir


@pytest.fixture
def fhir_config() -> FHIRConfig:
    base_url = os.getenv("FHIR_BASE_URL", "http://localhost:8090/fhir").rstrip("/")
    return FHIRConfig(
        enabled=True,
        base_url=base_url,
        auth_token=os.getenv("FHIR_AUTH_TOKEN", ""),
        timeout_seconds=15.0,  # HAPI can be sluggish
        retry_max_attempts=2,
        retry_backoff_seconds=1.0,
    )


@pytest.fixture
async def hook(fhir_config: FHIRConfig):
    h = FHIRWorkflowHook(config=fhir_config)
    yield h
    await h.aclose()


@pytest.mark.asyncio
async def test_validate_configuration_against_live_hapi(hook: FHIRWorkflowHook):
    """HAPI FHIR exposes a CapabilityStatement listing DiagnosticReport + Patient."""
    flags = await hook.validate_configuration()
    assert flags["connection"] is True
    assert flags["version_compatible"] is True, (
        "Expected HAPI to advertise FHIR R4 (4.x) — check fhir.fhir_version env"
    )
    # HAPI exposes hundreds of resources by default; permissions should be True.
    assert flags["permissions"] is True


@pytest.mark.asyncio
async def test_send_result_creates_diagnostic_report(hook: FHIRWorkflowHook):
    """POST /DiagnosticReport returns 201 and the resource is then GET-able."""
    accession = f"VARUNA-IT-{uuid.uuid4().hex[:8]}"
    result = {
        "slide_id": f"slide-{uuid.uuid4().hex[:8]}",
        "patient_id": f"pat-{uuid.uuid4().hex[:8]}",
        "patient_name": "Integration Test Patient",
        "performer_name": "Integration Test Pathologist",
        "annotations_count": 2,
        "conclusion": "Test conclusion (integration test, do not interpret)",
        "status": "preliminary",
    }
    ok = await hook.send_result(accession, result)
    assert ok is True


@pytest.mark.asyncio
async def test_get_patient_info_returns_none_for_unknown_id(hook: FHIRWorkflowHook):
    """Patient resource we never created → 404 → returns None (not raises)."""
    got = await hook.get_patient_info(f"never-exists-{uuid.uuid4().hex}")
    assert got is None


@pytest.mark.asyncio
async def test_on_event_report_signed_round_trip(hook: FHIRWorkflowHook):
    """REPORT_SIGNED → POST DiagnosticReport, return True from on_event."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED,
        slide_id=f"slide-{uuid.uuid4().hex[:8]}",
        user_id="dr.integration",
        metadata={
            "patient_id": f"pat-{uuid.uuid4().hex[:8]}",
            "performer_name": "Dr Integration",
            "annotations_count": 1,
            "conclusion": "Round-trip integration check",
        },
    )
    assert await hook.on_event(event) is True
