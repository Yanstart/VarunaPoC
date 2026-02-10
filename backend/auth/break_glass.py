"""
Break-Glass Emergency Access - Temporary elevated privileges.

In hospital environments, physicians may need emergency access to patient data
outside their normal scope. Break-glass provides time-limited ADMIN_TECHNIQUE
access with mandatory audit trail and post-hoc review requirement.

Sessions are stored in-memory (lost on restart, which is a safety feature).
Every activation is logged as CRITICAL audit event.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)

# In-memory break-glass sessions: {user_sub: expires_at}
_active_sessions: Dict[str, datetime] = {}


def activate_break_glass(
    user_sub: str,
    duration_minutes: int = 30,
) -> datetime:
    """
    Activate break-glass for a user.

    Returns the expiration datetime.
    """
    expires_at = datetime.now(UTC) + timedelta(minutes=duration_minutes)
    _active_sessions[user_sub] = expires_at
    logger.critical(
        f"BREAK-GLASS ACTIVATED: user={user_sub}, "
        f"expires={expires_at.isoformat()}, duration={duration_minutes}min"
    )
    return expires_at


def is_break_glass_active(user_sub: str) -> bool:
    """Check if a user has active break-glass access."""
    expires_at = _active_sessions.get(user_sub)
    if expires_at is None:
        return False

    now = datetime.now(UTC)
    if now >= expires_at:
        # Expired, clean up
        del _active_sessions[user_sub]
        logger.info(f"Break-glass expired for user={user_sub}")
        return False

    return True


def deactivate_break_glass(user_sub: str) -> bool:
    """Manually deactivate break-glass for a user."""
    if user_sub in _active_sessions:
        del _active_sessions[user_sub]
        logger.info(f"Break-glass deactivated for user={user_sub}")
        return True
    return False


def get_active_sessions() -> Dict[str, str]:
    """Get all active break-glass sessions (for admin review)."""
    now = datetime.now(UTC)
    active = {}
    expired_keys = []

    for user_sub, expires_at in _active_sessions.items():
        if now >= expires_at:
            expired_keys.append(user_sub)
        else:
            active[user_sub] = expires_at.isoformat()

    # Clean up expired
    for key in expired_keys:
        del _active_sessions[key]

    return active
