"""
Break-Glass Emergency Access - Temporary elevated privileges.

In hospital environments, physicians may need emergency access to patient data
outside their normal scope. Break-glass provides time-limited ADMIN_TECHNIQUE
access with mandatory audit trail and post-hoc review requirement.

Sessions are stored in-memory (lost on restart, which is a safety feature).
Every activation is logged as CRITICAL audit event.

Review workflow:
- All break-glass sessions must be reviewed by an ADMIN_TECHNIQUE user.
- Sessions can be revoked before expiry.
- Closed/reviewed sessions are tracked for compliance reporting.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class BreakGlassSession:
    """Represents a single break-glass session with full audit metadata."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_user: str = ""
    issued_by: str = ""
    issued_by_username: str = ""
    reason: str = ""
    activated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    duration_minutes: int = 30
    ip_address: str = ""
    revoked: bool = False
    revoked_by: str | None = None
    revoked_at: datetime | None = None
    reviewed: bool = False
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None

    @property
    def is_active(self) -> bool:
        """Check if this session is still active (not expired or revoked)."""
        if self.revoked:
            return False
        return datetime.now(UTC) < self.expires_at

    @property
    def status(self) -> str:
        """Return human-readable status."""
        if self.revoked:
            return "revoked"
        if datetime.now(UTC) >= self.expires_at:
            return "expired"
        return "active"

    def to_dict(self) -> dict:
        """Serialize session to dict for API responses."""
        return {
            "id": self.id,
            "target_user": self.target_user,
            "issued_by": self.issued_by,
            "issued_by_username": self.issued_by_username,
            "reason": self.reason,
            "activated_at": self.activated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "duration_minutes": self.duration_minutes,
            "status": self.status,
            "revoked": self.revoked,
            "revoked_by": self.revoked_by,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "reviewed": self.reviewed,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
        }


# In-memory break-glass sessions: {session_id: BreakGlassSession}
_sessions: Dict[str, BreakGlassSession] = {}

# Index by target user for quick lookup: {user_sub: [session_id, ...]}
_user_sessions: Dict[str, list] = {}


def activate_break_glass(
    target_user: str,
    issued_by: str,
    issued_by_username: str,
    reason: str,
    duration_minutes: int = 30,
    ip_address: str = "",
) -> BreakGlassSession:
    """
    Activate break-glass for a target user.

    Args:
        target_user: Subject identifier of the user receiving emergency access.
        issued_by: Subject identifier of the admin issuing the token.
        issued_by_username: Display name of the issuing admin.
        reason: Medical/operational justification (mandatory).
        duration_minutes: Duration in minutes (max 60).
        ip_address: IP address of the issuing admin.

    Returns:
        The created BreakGlassSession.
    """
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=duration_minutes)

    session = BreakGlassSession(
        target_user=target_user,
        issued_by=issued_by,
        issued_by_username=issued_by_username,
        reason=reason,
        activated_at=now,
        expires_at=expires_at,
        duration_minutes=duration_minutes,
        ip_address=ip_address,
    )

    _sessions[session.id] = session

    if target_user not in _user_sessions:
        _user_sessions[target_user] = []
    _user_sessions[target_user].append(session.id)

    logger.critical(
        "BREAK-GLASS ACTIVATED: session=%s, target=%s, issued_by=%s, "
        "reason=%s, expires=%s, duration=%dmin",
        session.id,
        target_user,
        issued_by,
        reason,
        expires_at.isoformat(),
        duration_minutes,
    )
    return session


def is_break_glass_active(user_sub: str) -> bool:
    """Check if a user has any active break-glass session."""
    session_ids = _user_sessions.get(user_sub, [])
    for sid in session_ids:
        session = _sessions.get(sid)
        if session and session.is_active:
            return True
    return False


def get_session(session_id: str) -> BreakGlassSession | None:
    """Get a specific break-glass session by ID."""
    return _sessions.get(session_id)


def revoke_session(
    session_id: str,
    revoked_by: str,
) -> BreakGlassSession | None:
    """
    Revoke a break-glass session before expiry.

    Returns the session if found and revoked, None otherwise.
    """
    session = _sessions.get(session_id)
    if session is None:
        return None

    if session.revoked:
        return session  # Already revoked

    session.revoked = True
    session.revoked_by = revoked_by
    session.revoked_at = datetime.now(UTC)

    logger.warning(
        "BREAK-GLASS REVOKED: session=%s, target=%s, revoked_by=%s",
        session_id,
        session.target_user,
        revoked_by,
    )
    return session


def review_session(
    session_id: str,
    reviewed_by: str,
    notes: str = "",
) -> BreakGlassSession | None:
    """
    Mark a break-glass session as reviewed (post-hoc audit).

    Returns the session if found, None otherwise.
    """
    session = _sessions.get(session_id)
    if session is None:
        return None

    session.reviewed = True
    session.reviewed_by = reviewed_by
    session.reviewed_at = datetime.now(UTC)
    session.review_notes = notes

    logger.info(
        "BREAK-GLASS REVIEWED: session=%s, target=%s, reviewed_by=%s",
        session_id,
        session.target_user,
        reviewed_by,
    )
    return session


def deactivate_break_glass(user_sub: str) -> bool:
    """Revoke all active break-glass sessions for a user."""
    session_ids = _user_sessions.get(user_sub, [])
    revoked_any = False
    for sid in session_ids:
        session = _sessions.get(sid)
        if session and session.is_active:
            session.revoked = True
            session.revoked_at = datetime.now(UTC)
            revoked_any = True

    if revoked_any:
        logger.info("Break-glass deactivated for user=%s", user_sub)

    return revoked_any


def get_active_sessions() -> Dict[str, str]:
    """Get all active break-glass sessions (legacy compat: user_sub -> expires_at)."""
    now = datetime.now(UTC)
    active = {}
    for session in _sessions.values():
        if not session.revoked and now < session.expires_at:
            active[session.target_user] = session.expires_at.isoformat()
    return active


def list_all_sessions(
    active_only: bool = False,
    pending_review: bool = False,
) -> list[dict]:
    """
    List break-glass sessions with optional filtering.

    Args:
        active_only: Only return currently active sessions.
        pending_review: Only return sessions not yet reviewed.

    Returns:
        List of session dicts.
    """
    results = []
    for session in _sessions.values():
        if active_only and not session.is_active:
            continue
        if pending_review and session.reviewed:
            continue
        results.append(session.to_dict())

    # Sort by activated_at descending (most recent first)
    results.sort(key=lambda s: s["activated_at"], reverse=True)
    return results
