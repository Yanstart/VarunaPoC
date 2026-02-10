"""
Audit Trail - Dual logging to DB + JSON file.

Every significant action is logged with:
- WHO: user_sub, username, role
- WHAT: event_type, action, resource
- WHEN: timestamp
- WHERE: IP address, user agent
- WHY: details (context-specific)

Levels:
- INFO: Normal operations (view slide, create annotation)
- WARNING: Unusual operations (failed auth, role denied)
- CRITICAL: Emergency actions (break-glass activation, admin override)

Dual persistence:
- PostgreSQL audit_events table (primary, queryable)
- JSON file fallback (if DB unavailable, for disaster recovery)
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import Request

from auth.schemas import CurrentUser

logger = logging.getLogger("audit")

# JSON fallback file path
_AUDIT_LOG_DIR = Path(__file__).parent.parent / "logs"
_AUDIT_LOG_FILE = _AUDIT_LOG_DIR / "audit.jsonl"


# Event type constants
class AuditEvents:
    # Auth events
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    AUTH_FAILED = "AUTH_FAILED"
    ROLE_DENIED = "ROLE_DENIED"

    # Slide events
    SLIDE_VIEWED = "SLIDE_VIEWED"
    SLIDE_LISTED = "SLIDE_LISTED"

    # Annotation events
    ANNOTATION_CREATED = "ANNOTATION_CREATED"
    ANNOTATION_UPDATED = "ANNOTATION_UPDATED"
    ANNOTATION_DELETED = "ANNOTATION_DELETED"
    ANNOTATION_BATCH_CREATED = "ANNOTATION_BATCH_CREATED"

    # ML events
    ML_PREDICTION = "ML_PREDICTION"
    ML_HEATMAP = "ML_HEATMAP"
    ML_DETECTION = "ML_DETECTION"

    # Break-glass events
    BREAK_GLASS_ACTIVATED = "BREAK_GLASS_ACTIVATED"
    BREAK_GLASS_EXPIRED = "BREAK_GLASS_EXPIRED"
    BREAK_GLASS_REVIEWED = "BREAK_GLASS_REVIEWED"

    # Admin events
    LABEL_CREATED = "LABEL_CREATED"
    LABEL_UPDATED = "LABEL_UPDATED"
    LABEL_DELETED = "LABEL_DELETED"

    # Session events
    SESSION_SAVED = "SESSION_SAVED"
    SESSION_RESTORED = "SESSION_RESTORED"


async def log_audit_event(
    event_type: str,
    action: str,
    user: CurrentUser | None = None,
    request: Request | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    level: str = "INFO",
    details: dict[str, Any] | None = None,
) -> None:
    """
    Log an audit event to both DB and JSON file.

    Args:
        event_type: Event category (from AuditEvents constants)
        action: CRUD action (CREATE, READ, UPDATE, DELETE, LOGIN, etc.)
        user: Current authenticated user (None for anonymous/failed auth)
        request: FastAPI request (for IP, user agent)
        resource_type: Type of resource affected (slide, annotation, etc.)
        resource_id: ID of the affected resource
        level: Severity (INFO, WARNING, CRITICAL)
        details: Additional context-specific data
    """
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level,
        "event_type": event_type,
        "user_sub": user.sub if user else None,
        "username": user.username if user else None,
        "user_role": user.primary_role if user else None,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
        "details": details,
        "ip_address": _get_client_ip(request) if request else None,
        "user_agent": request.headers.get("User-Agent", "")[:500] if request else None,
    }

    # Log to Python logger
    log_msg = (
        f"[AUDIT] {level} {event_type} | "
        f"user={event['username']} | action={action} | "
        f"resource={resource_type}:{resource_id}"
    )
    if level == "CRITICAL":
        logger.critical(log_msg)
    elif level == "WARNING":
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    # Persist to DB (best-effort, don't fail the request)
    await _persist_to_db(event)

    # Always write to JSON file (fallback)
    _persist_to_json(event)


async def _persist_to_db(event: dict) -> None:
    """Write audit event to PostgreSQL."""
    try:
        from core.database import get_db_context

        async with get_db_context() as db:
            from auth.models import AuditEvent

            audit = AuditEvent(
                id=uuid.UUID(event["id"]),
                level=event["level"],
                event_type=event["event_type"],
                user_sub=event["user_sub"],
                username=event["username"],
                user_role=event["user_role"],
                resource_type=event["resource_type"],
                resource_id=event["resource_id"],
                action=event["action"],
                details=event["details"],
                ip_address=event["ip_address"],
                user_agent=event["user_agent"],
            )
            db.add(audit)
    except Exception as e:
        logger.warning(f"Failed to persist audit event to DB: {e}")


def _persist_to_json(event: dict) -> None:
    """Append audit event to JSON Lines file (fallback)."""
    try:
        _AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _AUDIT_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception as e:
        logger.error(f"Failed to write audit event to JSON: {e}")


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For for proxied requests."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
