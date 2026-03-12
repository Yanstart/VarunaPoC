"""
Auth Routes - Authentication, break-glass, and session roaming endpoints.

Endpoints:
- GET  /api/auth/me              → Current user info + capabilities
- POST /api/auth/break-glass     → Activate emergency access
- GET  /api/auth/break-glass     → List active break-glass sessions (admin)
- POST /api/auth/session         → Save session state
- GET  /api/auth/session         → Load session state
- DELETE /api/auth/session       → Delete session state
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request

from auth import AUTH_ENABLED
from auth.audit import AuditEvents, log_audit_event
from auth.break_glass import activate_break_glass, deactivate_break_glass, get_active_sessions
from auth.dependencies import get_current_user, require_role
from auth.schemas import (
    AuthStatusResponse,
    BreakGlassRequest,
    BreakGlassResponse,
    CurrentUser,
    SessionStateData,
    SessionStateResponse,
)
from rate_limiting import auth_rate, limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/me", response_model=AuthStatusResponse)
@limit(auth_rate)
async def get_me(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
):
    """Get current authenticated user info and capabilities."""
    # Log login event on first access
    await log_audit_event(
        event_type=AuditEvents.LOGIN,
        action="READ",
        user=current_user,
        request=request,
        level="INFO",
    )

    return AuthStatusResponse(
        user=current_user,
        auth_enabled=AUTH_ENABLED,
        break_glass_available=current_user.has_role("MEDECIN", "ADMIN_TECHNIQUE"),
        session_roaming_available=AUTH_ENABLED,
    )


@router.post("/break-glass", response_model=BreakGlassResponse)
@limit(auth_rate)
async def activate_break_glass_endpoint(
    data: BreakGlassRequest,
    request: Request,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),  # noqa: B008
):
    """
    Activate break-glass emergency access.

    Grants temporary ADMIN_TECHNIQUE privileges for the specified duration.
    Logged as CRITICAL audit event. Must be reviewed by admin.
    """
    session = activate_break_glass(
        target_user=current_user.sub,
        issued_by=current_user.sub,
        issued_by_username=current_user.username,
        reason=data.reason,
        duration_minutes=data.duration_minutes,
        ip_address=request.client.host if request.client else "",
    )
    expires_at = session.expires_at

    # Persist to DB
    try:
        from auth.models import BreakGlassLog
        from core.database import get_db_context

        async with get_db_context() as db:
            log = BreakGlassLog(
                user_sub=current_user.sub,
                username=current_user.username,
                reason=data.reason,
                expires_at=expires_at,
                ip_address=request.client.host if request.client else None,
            )
            db.add(log)
    except Exception as e:
        logger.warning(f"Failed to persist break-glass log to DB: {e}")

    # Audit: CRITICAL level
    await log_audit_event(
        event_type=AuditEvents.BREAK_GLASS_ACTIVATED,
        action="CREATE",
        user=current_user,
        request=request,
        level="CRITICAL",
        details={
            "reason": data.reason,
            "duration_minutes": data.duration_minutes,
            "expires_at": expires_at.isoformat(),
        },
    )

    return BreakGlassResponse(
        activated=True,
        expires_at=expires_at,
        user_sub=current_user.sub,
        reason=data.reason,
    )


@router.get("/break-glass")
async def list_break_glass_sessions(
    _current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),  # noqa: B008
):
    """List all active break-glass sessions (admin only)."""
    return {
        "active_sessions": get_active_sessions(),
    }


@router.delete("/break-glass/{user_sub}")
async def revoke_break_glass(
    user_sub: str,
    request: Request,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),  # noqa: B008
):
    """Revoke a user's break-glass access (admin only)."""
    deactivated = deactivate_break_glass(user_sub)

    if deactivated:
        await log_audit_event(
            event_type=AuditEvents.BREAK_GLASS_REVIEWED,
            action="DELETE",
            user=current_user,
            request=request,
            level="WARNING",
            details={"revoked_user": user_sub},
        )

    return {"revoked": deactivated, "user_sub": user_sub}


@router.post("/session", response_model=SessionStateResponse)
async def save_session(
    state: SessionStateData,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
):
    """Save current viewer state for session roaming."""
    from auth.session_roaming import save_session_state

    saved_at = await save_session_state(current_user.sub, state)

    await log_audit_event(
        event_type=AuditEvents.SESSION_SAVED,
        action="CREATE",
        user=current_user,
        request=request,
        details={"slide_id": state.slide_id},
    )

    return SessionStateResponse(
        user_sub=current_user.sub,
        state=state,
        saved_at=saved_at,
    )


@router.get("/session")
async def load_session(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
):
    """Load saved viewer state for session roaming."""
    from auth.session_roaming import load_session_state

    state = await load_session_state(current_user.sub)

    if state is None:
        return {"state": None, "message": "No saved session"}

    await log_audit_event(
        event_type=AuditEvents.SESSION_RESTORED,
        action="READ",
        user=current_user,
        request=request,
        details={"slide_id": state.slide_id},
    )

    return SessionStateResponse(
        user_sub=current_user.sub,
        state=state,
        saved_at=datetime.now(UTC),
    )


@router.delete("/session")
async def delete_session(
    current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
):
    """Delete saved session state."""
    from auth.session_roaming import delete_session_state

    deleted = await delete_session_state(current_user.sub)
    return {"deleted": deleted}
