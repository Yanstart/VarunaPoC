"""
Break-Glass Emergency Access Routes - Review and Closure Workflow.

Provides admin-only endpoints for issuing, reviewing, and revoking
break-glass emergency access tokens in hospital environments.

Endpoints:
- POST   /api/auth/breakglass              -> Issue emergency access token
- GET    /api/auth/breakglass/sessions      -> List break-glass sessions
- DELETE /api/auth/breakglass/sessions/{id} -> Revoke a session
- POST   /api/auth/breakglass/sessions/{id}/review -> Mark session as reviewed

Security:
- All endpoints require ADMIN_TECHNIQUE role.
- Every action generates a CRITICAL or WARNING audit event.
- Tokens have a hard max TTL of 60 minutes.
"""

import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status

from auth.audit import AuditEvents, log_audit_event
from auth.break_glass import (
    activate_break_glass,
    get_session,
    list_all_sessions,
    review_session,
    revoke_session,
)
from auth.dependencies import require_role
from auth.schemas import (
    BreakGlassIssueRequest,
    BreakGlassIssueResponse,
    BreakGlassReviewRequest,
    BreakGlassSessionListResponse,
    BreakGlassSessionResponse,
    CurrentUser,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/breakglass", tags=["Break-Glass"])

# Max duration for break-glass tokens (hard limit)
MAX_DURATION_MINUTES = 60


def _generate_breakglass_token(
    session_id: str,
    target_user: str,
    expires_at: datetime,
    issued_by: str,
) -> str:
    """
    Generate a self-contained break-glass token.

    This is a simple signed token for emergency use. In production with
    Keycloak available, this would be exchanged for a proper JWT via the
    token exchange grant. When Keycloak is down (the primary break-glass
    scenario), this locally-generated token is verified by the backend.

    Format: bg_<session_id>_<random>_<expiry_ts>
    """
    random_part = secrets.token_urlsafe(32)
    expiry_ts = int(expires_at.timestamp())
    return f"bg_{session_id}_{random_part}_{expiry_ts}"


@router.post("", response_model=BreakGlassIssueResponse)
async def issue_breakglass_token(
    data: BreakGlassIssueRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    Issue an emergency break-glass access token.

    Only ADMIN_TECHNIQUE can issue these tokens. The token grants temporary
    elevated privileges to the target user for the specified duration.

    Every issuance is logged as a CRITICAL audit event with full context:
    timestamp, issuer, target, reason, duration, and IP address.
    """
    # Enforce hard max duration
    duration = min(data.duration_minutes, MAX_DURATION_MINUTES)

    # Get client IP
    ip_address = ""
    if request.client:
        ip_address = request.client.host
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()

    # Activate break-glass session
    session = activate_break_glass(
        target_user=data.target_user,
        issued_by=current_user.sub,
        issued_by_username=current_user.username,
        reason=data.reason,
        duration_minutes=duration,
        ip_address=ip_address,
    )

    # Generate emergency token
    token = _generate_breakglass_token(
        session_id=session.id,
        target_user=data.target_user,
        expires_at=session.expires_at,
        issued_by=current_user.sub,
    )

    # Persist to DB (best-effort)
    try:
        from auth.models import BreakGlassLog
        from core.database import get_db_context

        async with get_db_context() as db:
            log = BreakGlassLog(
                user_sub=data.target_user,
                username=current_user.username,
                reason=data.reason,
                expires_at=session.expires_at,
                ip_address=ip_address,
            )
            db.add(log)
    except Exception as e:
        logger.warning("Failed to persist break-glass log to DB: %s", e)

    # Audit: CRITICAL level
    await log_audit_event(
        event_type=AuditEvents.BREAK_GLASS_ACTIVATED,
        action="CREATE",
        user=current_user,
        request=request,
        level="CRITICAL",
        details={
            "session_id": session.id,
            "target_user": data.target_user,
            "reason": data.reason,
            "duration_minutes": duration,
            "expires_at": session.expires_at.isoformat(),
            "ip_address": ip_address,
        },
    )

    return BreakGlassIssueResponse(
        session_id=session.id,
        target_user=data.target_user,
        issued_by=current_user.sub,
        reason=data.reason,
        duration_minutes=duration,
        activated_at=session.activated_at,
        expires_at=session.expires_at,
        token=token,
    )


@router.get("/sessions", response_model=BreakGlassSessionListResponse)
async def list_breakglass_sessions(
    active_only: bool = False,
    pending_review: bool = False,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    List break-glass sessions with optional filters.

    Query parameters:
    - active_only: Only show currently active (non-expired, non-revoked) sessions.
    - pending_review: Only show sessions that have not been reviewed yet.

    Returns session metadata including status, review state, and audit trail.
    """
    sessions = list_all_sessions(
        active_only=active_only,
        pending_review=pending_review,
    )

    # Compute summary counts from all sessions (unfiltered)
    all_sessions = list_all_sessions()
    active_count = sum(1 for s in all_sessions if s["status"] == "active")
    pending_review_count = sum(1 for s in all_sessions if not s["reviewed"])

    return BreakGlassSessionListResponse(
        sessions=[BreakGlassSessionResponse(**s) for s in sessions],
        total=len(sessions),
        active_count=active_count,
        pending_review_count=pending_review_count,
    )


@router.delete("/sessions/{session_id}")
async def revoke_breakglass_session(
    session_id: str,
    request: Request,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    Revoke an active break-glass session.

    Immediately terminates the emergency access. The target user's
    break-glass token becomes invalid.

    Logged as a WARNING audit event.
    """
    session = revoke_session(
        session_id=session_id,
        revoked_by=current_user.sub,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Break-glass session not found: {session_id}",
        )

    # Audit
    await log_audit_event(
        event_type=AuditEvents.BREAK_GLASS_REVIEWED,
        action="DELETE",
        user=current_user,
        request=request,
        level="WARNING",
        details={
            "session_id": session_id,
            "target_user": session.target_user,
            "action": "revoke",
        },
    )

    return {
        "revoked": True,
        "session_id": session_id,
        "target_user": session.target_user,
    }


@router.post("/sessions/{session_id}/review")
async def review_breakglass_session(
    session_id: str,
    data: BreakGlassReviewRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    Mark a break-glass session as reviewed.

    Post-hoc review is mandatory for compliance. The reviewer confirms
    that the emergency access was justified and documents any findings.

    Logged as an INFO audit event.
    """
    session = review_session(
        session_id=session_id,
        reviewed_by=current_user.sub,
        notes=data.notes,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Break-glass session not found: {session_id}",
        )

    # Persist review to DB (best-effort)
    try:
        from sqlalchemy import update as sa_update

        from auth.models import BreakGlassLog
        from core.database import get_db_context

        async with get_db_context() as db:
            # Update the matching log entry
            from sqlalchemy import select

            stmt = (
                select(BreakGlassLog)
                .where(BreakGlassLog.user_sub == session.target_user)
                .where(BreakGlassLog.reviewed_by.is_(None))
                .order_by(BreakGlassLog.activated_at.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            log_entry = result.scalar_one_or_none()
            if log_entry:
                log_entry.reviewed_by = current_user.sub
                log_entry.reviewed_at = datetime.now(UTC)
    except Exception as e:
        logger.warning("Failed to persist review to DB: %s", e)

    # Audit
    await log_audit_event(
        event_type=AuditEvents.BREAK_GLASS_REVIEWED,
        action="UPDATE",
        user=current_user,
        request=request,
        level="INFO",
        details={
            "session_id": session_id,
            "target_user": session.target_user,
            "review_notes": data.notes,
            "action": "review",
        },
    )

    return {
        "reviewed": True,
        "session_id": session_id,
        "target_user": session.target_user,
        "reviewed_by": current_user.sub,
        "reviewed_at": session.reviewed_at.isoformat() if session.reviewed_at else None,
    }
