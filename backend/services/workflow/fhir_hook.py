"""
FHIRWorkflowHook — Strangler Fig adapter wiring REPORT_SIGNED events to a
FHIR R4 server via the existing fhir.resources.build_diagnostic_report().

Why this exists
---------------
- VarunaPoC integrates with hospital DPI (Dossier Patient Informatisé) via
  FHIR: a signed pathology report becomes a FHIR DiagnosticReport, posted
  into the DPI for clinicians to consult.
- Patient lookups (get_patient_info) read FHIR Patient resources from the
  DPI — the source of truth for demographics & MRN.
- query_worklist / update_worklist would map to FHIR Task resources but
  the project doesn't yet build Task resources (out of scope for Tier 3).
  Those methods raise NotImplementedError with a follow-up note.

Mapping of WorkflowEventType → FHIR action
------------------------------------------
- REPORT_SIGNED       → build DiagnosticReport (status=final), POST it.
- ANNOTATION_CREATED  → no FHIR action (logged only).
- SLIDE_OPENED, *     → no FHIR action (audit trail elsewhere).
- ML_INFERENCE_*      → no FHIR action (DPI consumes the signed report,
                        not raw ML telemetry).

Reliability
-----------
- All HTTP errors are caught; on_event NEVER raises so a DPI outage does
  not block slide signing in the viewer.
- send_result() bubbles WorkflowIntegrationError on persistent failure
  because the caller (a future REST endpoint) needs to know the report
  did not reach the DPI.
- Retries: simple capped-backoff loop driven by FHIR_RETRY_MAX_ATTEMPTS
  and FHIR_RETRY_BACKOFF_SECONDS.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import httpx

from core.exceptions.workflow import WorkflowIntegrationError
from core.interfaces.workflow import WorkflowEventType
from fhir.config import get_fhir_config
from fhir.resources import build_diagnostic_report

if TYPE_CHECKING:
    from core.interfaces.workflow import WorkflowEvent
    from fhir.config import FHIRConfig

logger = logging.getLogger(__name__)


# Event → DPI action. Anything not in the table is a no-op (logged only).
_EVENT_HANDLERS_REQUIRING_FHIR = frozenset({WorkflowEventType.REPORT_SIGNED})


class FHIRWorkflowHook:
    """WorkflowHook Protocol implementer talking to a FHIR R4 server."""

    def __init__(
        self,
        config: Optional[FHIRConfig] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._config = config or get_fhir_config()
        self._owns_client = client is None
        self._client = client  # injected for tests; lazily built otherwise

    # -- internal: HTTP plumbing --------------------------------------------

    async def _get_client(self) -> Optional[httpx.AsyncClient]:
        if not self._config.is_configured:
            return None
        if self._client is not None:
            return self._client
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }
        if self._config.auth_token:
            headers["Authorization"] = f"Bearer {self._config.auth_token}"
        self._client = httpx.AsyncClient(
            base_url=self._config.base_url,
            headers=headers,
            timeout=self._config.timeout_seconds,
        )
        return self._client

    async def aclose(self) -> None:
        """Release the HTTP client. Safe to call repeatedly."""
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def _request_with_retries(
        self,
        method: str,
        url: str,
        *,
        json: Optional[Dict] = None,
        ok_statuses: tuple = (200, 201),
    ) -> httpx.Response:
        """POST/GET/PUT against the FHIR server with capped exponential backoff.

        Raises WorkflowIntegrationError when all retries fail. Caller is
        responsible for catching it (or propagating, for endpoints that
        need to surface the failure).
        """
        client = await self._get_client()
        if client is None:
            raise WorkflowIntegrationError(
                "FHIR", "FHIR not configured (FHIR_ENABLED=false or FHIR_BASE_URL empty)"
            )

        last_error: Optional[Exception] = None
        backoff = self._config.retry_backoff_seconds
        for attempt in range(1, self._config.retry_max_attempts + 1):
            try:
                response = await client.request(method, url, json=json)
                if response.status_code in ok_statuses:
                    return response
                # 4xx is a permanent failure — no point retrying.
                if 400 <= response.status_code < 500:
                    raise WorkflowIntegrationError(
                        "FHIR",
                        f"{method} {url} returned {response.status_code}: "
                        f"{response.text[:300]}",
                    )
                last_error = WorkflowIntegrationError(
                    "FHIR",
                    f"{method} {url} returned {response.status_code}",
                )
            except httpx.HTTPError as e:
                last_error = e

            # Backoff before the next attempt (skip after the last attempt).
            if attempt < self._config.retry_max_attempts:
                await asyncio.sleep(backoff)
                backoff *= 2

        raise WorkflowIntegrationError(
            "FHIR",
            f"{method} {url} failed after {self._config.retry_max_attempts} "
            f"attempts: {last_error}",
        )

    # -- WorkflowHook Protocol ----------------------------------------------

    async def on_event(self, event: WorkflowEvent) -> bool:
        """Dispatch event to FHIR if mapped; otherwise log and return True.

        Never raises. A DPI outage must not block the viewer.
        """
        if not self._config.is_configured:
            logger.debug(
                "[fhir hook] not configured, dropping event=%s",
                event.event_type.value,
            )
            return True

        if event.event_type not in _EVENT_HANDLERS_REQUIRING_FHIR:
            logger.debug(
                "[fhir hook] event=%s not mapped to FHIR (logged only)",
                event.event_type.value,
            )
            return True

        # REPORT_SIGNED → build DiagnosticReport and POST it.
        try:
            report_payload = self._build_report_from_event(event)
            await self._request_with_retries(
                "POST", "/DiagnosticReport", json=report_payload, ok_statuses=(200, 201)
            )
            logger.info(
                "[fhir hook] DiagnosticReport posted for slide_id=%s patient_id=%s",
                event.slide_id,
                event.metadata.get("patient_id"),
            )
            return True
        except WorkflowIntegrationError as e:
            # Log but don't bubble — REPORT_SIGNED handler must not break
            # the signing flow on the viewer side.
            logger.warning(
                "[fhir hook] failed to post DiagnosticReport for slide_id=%s: %s",
                event.slide_id,
                e,
            )
            return False

    async def query_worklist(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        msg = (
            "FHIRWorkflowHook.query_worklist requires a Task resource builder "
            "in fhir/resources.py (FHIR R4 Task with status=requested). "
            "Track in a follow-up commit when the modality worklist flow is "
            "designed for this DPI vendor."
        )
        raise NotImplementedError(msg)

    async def update_worklist(
        self,
        accession_number: str,
        status: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        msg = (
            "FHIRWorkflowHook.update_worklist requires a Task resource builder. "
            "Track in a follow-up alongside query_worklist."
        )
        raise NotImplementedError(msg)

    async def send_result(
        self, accession_number: str, result: Dict[str, Any]
    ) -> bool:
        """Build a DiagnosticReport from `result` and POST it to the DPI.

        Unlike on_event, this propagates failures: callers are usually a
        REST endpoint that needs to surface "report did not reach DPI"
        as a 502 to the user.
        """
        report = build_diagnostic_report(
            slide_id=result.get("slide_id", accession_number),
            slide_name=result.get("slide_name", ""),
            patient_id=result.get("patient_id"),
            patient_name=result.get("patient_name"),
            performer_name=result.get("performer_name"),
            performer_sub=result.get("performer_sub"),
            annotations_count=int(result.get("annotations_count", 0)),
            conclusion=result.get("conclusion"),
            status=result.get("status", "final"),
            specimen_type=result.get("specimen_type"),
            specimen_collection_method=result.get("specimen_collection_method"),
            result_observations=result.get("result_observations"),
            pdf_url=result.get("pdf_url"),
            ml_tags=result.get("ml_tags"),
        )
        await self._request_with_retries(
            "POST", "/DiagnosticReport", json=report, ok_statuses=(200, 201)
        )
        logger.info(
            "[fhir hook] send_result accession=%s patient=%s",
            accession_number,
            result.get("patient_id"),
        )
        return True

    async def get_patient_info(self, patient_id: str) -> Optional[Dict]:
        """Read a Patient resource from the DPI.

        Returns the raw FHIR Patient resource (as a dict) on success, None
        when the patient is not found or the DPI is unreachable. The
        caller maps FHIR fields to the project's internal patient shape.
        """
        if not self._config.is_configured:
            return None
        try:
            response = await self._request_with_retries(
                "GET", f"/Patient/{patient_id}", ok_statuses=(200,)
            )
        except WorkflowIntegrationError as e:
            # 404 is signalled by the 4xx branch in _request_with_retries
            # which raises WorkflowIntegrationError. Treat that as "not
            # found" rather than propagating, matching the Protocol.
            logger.info(
                "[fhir hook] Patient/%s lookup failed: %s", patient_id, e
            )
            return None
        try:
            return response.json()
        except ValueError as e:
            logger.warning(
                "[fhir hook] Patient/%s returned non-JSON: %s", patient_id, e
            )
            return None

    async def validate_configuration(self) -> Dict[str, bool]:
        """Probe the FHIR server's CapabilityStatement.

        Returns the four flags expected by the Protocol. Never raises.
        """
        result = {
            "connection": False,
            "authentication": False,
            "permissions": False,
            "version_compatible": False,
        }
        if not self._config.is_configured:
            return result

        client = await self._get_client()
        if client is None:
            return result

        try:
            response = await client.get("/metadata")
        except httpx.HTTPError as e:
            logger.warning("[fhir hook] /metadata probe failed: %s", e)
            return result

        result["connection"] = True
        result["authentication"] = response.status_code != 401
        if response.status_code != 200:
            return result

        try:
            capability = response.json()
        except ValueError:
            return result

        # FHIR R4 capability statement: fhirVersion + rest.resource list.
        fhir_version = str(capability.get("fhirVersion", ""))
        result["version_compatible"] = fhir_version.startswith("4.")

        # Check that at least the expected resources are exposed by the server.
        rest = capability.get("rest", [])
        exposed = set()
        if rest:
            for resource in rest[0].get("resource", []) or []:
                t = resource.get("type")
                if t:
                    exposed.add(t)
        result["permissions"] = all(r in exposed for r in self._config.expected_resources)
        return result

    # -- helpers ------------------------------------------------------------

    def _build_report_from_event(self, event: WorkflowEvent) -> Dict[str, Any]:
        """Translate a REPORT_SIGNED event payload into a FHIR DiagnosticReport.

        Expects `event.metadata` to carry the report fields. Missing fields
        flow as None into build_diagnostic_report which already handles
        partial data gracefully.
        """
        meta = event.metadata or {}
        return build_diagnostic_report(
            slide_id=event.slide_id or meta.get("slide_id", "unknown"),
            slide_name=meta.get("slide_name", ""),
            patient_id=meta.get("patient_id"),
            patient_name=meta.get("patient_name"),
            performer_name=meta.get("performer_name") or event.user_id,
            performer_sub=meta.get("performer_sub") or event.user_id,
            annotations_count=int(meta.get("annotations_count", 0)),
            conclusion=meta.get("conclusion"),
            status=meta.get("status", "final"),
            specimen_type=meta.get("specimen_type"),
            specimen_collection_method=meta.get("specimen_collection_method"),
            result_observations=meta.get("result_observations"),
            pdf_url=meta.get("pdf_url"),
            ml_tags=meta.get("ml_tags"),
        )


__all__ = ["FHIRWorkflowHook"]
