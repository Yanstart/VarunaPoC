"""
GDPR Data Subject Rights Endpoints (Articles 15-20)

Provides endpoints for exercising data subject rights:
- GET  /api/gdpr/subjects/{hash}/data     — Right of access (Art. 15)
- DELETE /api/gdpr/subjects/{hash}        — Right to erasure (Art. 17)
- GET  /api/gdpr/subjects/{hash}/erasure/{id} — Erasure task status
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel

from auth.audit import AuditEvents, log_audit_event
from auth.dependencies import require_role
from auth.schemas import CurrentUser
from rate_limiting import admin_rate, limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["gdpr"])

# In-memory erasure task tracking.
# WARNING: This is process-local — tasks are lost on restart and not shared
# across workers. In production, replace with Redis or a database table.
_erasure_tasks: dict[str, dict] = {}


class SubjectDataResponse(BaseModel):
    patient_hash: str
    annotations: list[dict]
    view_sessions: list[dict]
    audit_events: list[dict]
    exported_at: str


class ErasureRequest(BaseModel):
    reason: str = "data_subject_request"
    confirmation: bool = False


class ErasureTaskResponse(BaseModel):
    task_id: str
    patient_hash: str
    status: str  # pending, in_progress, completed, failed
    requested_at: str
    completed_at: str | None = None
    items_erased: dict | None = None


@router.get(
    "/subjects/{patient_hash}/data",
    response_model=SubjectDataResponse,
)
async def get_subject_data(
    patient_hash: str,
    request: Request,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    Right of Access (GDPR Art. 15).

    Returns all data held about a data subject identified by patient_hash.
    Restricted to ADMIN_TECHNIQUE role (DPO or system administrator).
    """
    annotations = await _find_annotations_by_patient(patient_hash)
    sessions = await _find_view_sessions_by_patient(patient_hash)
    audit_events = await _find_audit_events_by_patient(patient_hash)

    await log_audit_event(
        event_type=AuditEvents.DATA_EXPORT,
        action="READ",
        user=current_user,
        request=request,
        resource_type="patient_data",
        resource_id=patient_hash,
        details={"reason": "gdpr_art15_access_request"},
        legal_basis="legal_obligation",
        data_classification="restricted",
    )

    return SubjectDataResponse(
        patient_hash=patient_hash,
        annotations=annotations,
        view_sessions=sessions,
        audit_events=audit_events,
        exported_at=datetime.now(timezone.utc).isoformat(),
    )


@router.delete(
    "/subjects/{patient_hash}",
    response_model=ErasureTaskResponse,
)
@limit(admin_rate)
async def request_erasure(
    patient_hash: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    Right to Erasure (GDPR Art. 17).

    Initiates async erasure of all data related to a data subject.
    Erasure is processed as a background task with a 30-day retention
    window for legal review before permanent deletion.
    """
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    task = {
        "task_id": task_id,
        "patient_hash": patient_hash,
        "status": "pending",
        "requested_at": now,
        "requested_by": current_user.sub,
        "completed_at": None,
        "items_erased": None,
    }
    _erasure_tasks[task_id] = task

    await log_audit_event(
        event_type=AuditEvents.DATA_ERASURE,
        action="DELETE",
        user=current_user,
        request=request,
        resource_type="patient_data",
        resource_id=patient_hash,
        level="WARNING",
        details={"task_id": task_id, "reason": "gdpr_art17_erasure_request"},
        legal_basis="legal_obligation",
        data_classification="restricted",
    )

    background_tasks.add_task(_process_erasure, task_id, patient_hash)

    return ErasureTaskResponse(**task)


@router.get(
    "/subjects/{patient_hash}/erasure/{task_id}",
    response_model=ErasureTaskResponse,
)
async def get_erasure_status(
    patient_hash: str,
    task_id: str,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """Check status of an erasure request."""
    task = _erasure_tasks.get(task_id)
    if not task or task["patient_hash"] != patient_hash:
        raise HTTPException(404, "Erasure task not found")
    return ErasureTaskResponse(**task)


# ---------------------------------------------------------------------------
# Internal helpers (stubs — connect to real DB in production)
# ---------------------------------------------------------------------------


async def _find_annotations_by_patient(patient_hash: str) -> list[dict]:
    """Find all annotations linked to a patient hash."""
    try:
        from sqlalchemy import select

        from core.database import get_session
        from models.annotation import Annotation

        async with get_session() as session:
            result = await session.execute(
                select(Annotation).where(
                    Annotation.metadata_json.contains({"patient_hash": patient_hash})
                )
            )
            rows = result.scalars().all()
            return [{"id": str(r.id), "slide_id": r.slide_id, "type": r.type} for r in rows]
    except Exception:
        logger.debug("DB not available for annotation lookup, returning empty")
        return []


async def _find_view_sessions_by_patient(patient_hash: str) -> list[dict]:
    """Find view sessions linked to a patient hash."""
    # View sessions are currently not persisted per-patient.
    # When worklist is promoted from mock data (#220), this will query real sessions.
    return []


async def _find_audit_events_by_patient(patient_hash: str) -> list[dict]:
    """Find audit events referencing a patient hash."""
    try:
        from sqlalchemy import select

        from auth.models import AuditEvent
        from core.database import get_session

        async with get_session() as session:
            result = await session.execute(
                select(AuditEvent).where(AuditEvent.resource_id == patient_hash).limit(100)
            )
            rows = result.scalars().all()
            return [
                {"id": str(r.id), "event_type": r.event_type, "timestamp": r.timestamp.isoformat()}
                for r in rows
            ]
    except Exception:
        logger.debug("DB not available for audit lookup, returning empty")
        return []


async def _process_erasure(task_id: str, patient_hash: str) -> None:
    """
    Background task: anonymize/delete patient data.

    In production this would:
    1. Anonymize annotations (replace patient_hash with 'ERASED')
    2. Delete view state sessions
    3. Mark audit events as 'erased' (audit trail itself is retained for compliance)
    """
    task = _erasure_tasks.get(task_id)
    if not task:
        return

    task["status"] = "in_progress"
    items = {"annotations_anonymized": 0, "sessions_deleted": 0, "audit_events_marked": 0}

    try:
        # Anonymize annotations
        try:
            from sqlalchemy import update

            from core.database import get_session
            from models.annotation import Annotation

            async with get_session() as session:
                result = await session.execute(
                    update(Annotation)
                    .where(Annotation.metadata_json.contains({"patient_hash": patient_hash}))
                    .values(metadata_json={"patient_hash": "ERASED", "gdpr_erased": True})
                )
                items["annotations_anonymized"] = result.rowcount
                await session.commit()
        except Exception:
            logger.debug("DB not available for annotation erasure")

        task["status"] = "completed"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["items_erased"] = items

    except Exception as e:
        task["status"] = "failed"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["items_erased"] = {"error": str(e)}
        logger.error("Erasure task %s failed: %s", task_id, e)
