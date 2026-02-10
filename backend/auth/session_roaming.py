"""
Session Roaming - Save/load user viewer state across workstations.

In hospital environments, physicians move between workstations.
Session roaming allows them to resume exactly where they left off:
same slide, same viewport position, same tool configuration.

State is stored in PostgreSQL (session_states table).
"""

import logging
from datetime import UTC, datetime
from typing import Optional

from auth.schemas import SessionStateData

logger = logging.getLogger(__name__)


async def save_session_state(
    user_sub: str,
    state: SessionStateData,
) -> datetime:
    """
    Save or update session state for a user.

    Uses upsert (insert or update on conflict) since each user
    has at most one active session state.
    """
    from sqlalchemy import select

    from auth.models import SessionState
    from core.database import get_db_context

    saved_at = datetime.now(UTC)

    async with get_db_context() as db:
        # Check if session exists
        result = await db.execute(select(SessionState).where(SessionState.user_sub == user_sub))
        existing = result.scalar_one_or_none()

        if existing:
            existing.state_data = state.model_dump()
            existing.saved_at = saved_at
        else:
            session_state = SessionState(
                user_sub=user_sub,
                state_data=state.model_dump(),
                saved_at=saved_at,
            )
            db.add(session_state)

    logger.info(f"Session state saved for user={user_sub}")
    return saved_at


async def load_session_state(user_sub: str) -> Optional[SessionStateData]:
    """
    Load session state for a user.

    Returns None if no saved state exists.
    """
    from sqlalchemy import select

    from auth.models import SessionState
    from core.database import get_db_context

    async with get_db_context() as db:
        result = await db.execute(select(SessionState).where(SessionState.user_sub == user_sub))
        session = result.scalar_one_or_none()

        if session and session.state_data:
            logger.info(f"Session state loaded for user={user_sub}")
            return SessionStateData(**session.state_data)

    return None


async def delete_session_state(user_sub: str) -> bool:
    """Delete saved session state for a user."""
    from sqlalchemy import delete

    from auth.models import SessionState
    from core.database import get_db_context

    async with get_db_context() as db:
        result = await db.execute(delete(SessionState).where(SessionState.user_sub == user_sub))
        deleted = result.rowcount > 0

    if deleted:
        logger.info(f"Session state deleted for user={user_sub}")
    return deleted
