"""Integration tests for PACSWorkflowHook against a live Orthanc container.

SKIPPED automatically when no Orthanc DICOM endpoint is reachable. Run
after starting the dev compose stack:

    PACS_AET_LOCAL=VARUNA_DEV PACS_AET_REMOTE=ORTHANC \
      docker compose -f docker-compose.dev.yml up -d orthanc
    cd backend
    PACS_ENABLED=true \
      PACS_AET_LOCAL=VARUNA_DEV PACS_AET_REMOTE=ORTHANC \
      pytest tests/integration/test_pacs_workflow_hook.py -m requires_orthanc -v

Note: the dev Orthanc container's AE Title is configured from PACS_AET_REMOTE
at compose-up time; the AET in the running container must match what the
test sends.
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.interfaces.workflow import WorkflowEvent, WorkflowEventType
from services.workflow.pacs_config import PACSConfig
from services.workflow.pacs_hook import PACSWorkflowHook

pytestmark = pytest.mark.requires_orthanc


@pytest.fixture
def pacs_config() -> PACSConfig:
    return PACSConfig(
        enabled=True,
        host=os.getenv("PACS_HOST", "localhost"),
        dicom_port=int(os.getenv("PACS_DICOM_PORT", "4242")),
        http_url=os.getenv("PACS_HTTP_URL", "http://localhost:8042"),
        aet_local=os.getenv("PACS_AET_LOCAL", "VARUNA_TEST"),
        aet_remote=os.getenv("PACS_AET_REMOTE", "ORTHANC"),
        http_user=os.getenv("PACS_HTTP_USER", "varuna"),
        http_password=os.getenv("PACS_HTTP_PASSWORD", "varuna_dev"),
        timeout_seconds=10.0,
        retry_max_attempts=2,
        retry_backoff_seconds=1.0,
    )


@pytest.fixture
def hook(pacs_config: PACSConfig) -> PACSWorkflowHook:
    return PACSWorkflowHook(config=pacs_config)


@pytest.mark.asyncio
async def test_validate_configuration_against_live_orthanc(hook: PACSWorkflowHook):
    """C-ECHO must succeed against a healthy Orthanc container."""
    flags = await hook.validate_configuration()
    assert flags["connection"] is True, (
        "Expected C-ECHO to succeed — verify PACS_AET_LOCAL is in Orthanc's "
        "allow-list (DicomModalities config) and PACS_AET_REMOTE matches "
        "Orthanc's DicomAet."
    )
    assert flags["authentication"] is True
    assert flags["version_compatible"] is True


@pytest.mark.asyncio
async def test_get_patient_info_returns_none_for_unknown_id(hook: PACSWorkflowHook):
    """Patient never created → C-FIND returns no pending → None."""
    got = await hook.get_patient_info(f"never-exists-{uuid.uuid4().hex[:8]}")
    assert got is None


@pytest.mark.asyncio
async def test_send_result_c_stores_an_sr(hook: PACSWorkflowHook):
    """C-STORE a Comprehensive SR; expect 0x0000 status from Orthanc."""
    accession = f"VARUNA-IT-{uuid.uuid4().hex[:8]}"
    ok = await hook.send_result(
        accession,
        {
            "patient_id": f"p-{uuid.uuid4().hex[:8]}",
            "patient_name": "Integration Test Patient",
            "conclusion": "Test conclusion (integration test, do not interpret)",
        },
    )
    assert ok is True


@pytest.mark.asyncio
async def test_on_event_report_signed_round_trip(hook: PACSWorkflowHook):
    """REPORT_SIGNED → C-STORE SR. on_event returns True on success."""
    event = WorkflowEvent(
        event_type=WorkflowEventType.REPORT_SIGNED,
        slide_id=f"slide-{uuid.uuid4().hex[:8]}",
        user_id="dr.integration",
        metadata={
            "accession_number": f"A-{uuid.uuid4().hex[:8]}",
            "patient_id": f"p-{uuid.uuid4().hex[:8]}",
            "conclusion": "Round-trip integration check",
        },
    )
    assert await hook.on_event(event) is True
