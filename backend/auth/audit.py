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

    # FHIR access events (#109)
    FHIR_READ = "FHIR_READ"
    FHIR_SEARCH = "FHIR_SEARCH"
    FHIR_EXPORT = "FHIR_EXPORT"

    # DICOM events (#109)
    DICOM_EXPORT = "DICOM_EXPORT"
    DICOM_QUERY = "DICOM_QUERY"
    DICOM_RETRIEVE = "DICOM_RETRIEVE"

    # Data access events (#109)
    DATA_EXPORT = "DATA_EXPORT"
    DATA_DOWNLOAD = "DATA_DOWNLOAD"
    DATA_PRINT = "DATA_PRINT"
    DATA_ERASURE = "DATA_ERASURE"

    # Integration events (#109)
    EHEALTH_TOKEN_REQUEST = "EHEALTH_TOKEN_REQUEST"
    EHBOX_MESSAGE_SENT = "EHBOX_MESSAGE_SENT"
    HL7_MESSAGE_PARSED = "HL7_MESSAGE_PARSED"
    APSR_GENERATED = "APSR_GENERATED"
    TERMINOLOGY_LOOKUP = "TERMINOLOGY_LOOKUP"


async def log_audit_event(
    event_type: str,
    action: str,
    user: CurrentUser | None = None,
    request: Request | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    level: str = "INFO",
    details: dict[str, Any] | None = None,
    data_classification: str | None = None,
    legal_basis: str | None = None,
    retention_years: int | None = None,
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
        data_classification: Data sensitivity (public, internal, confidential, restricted)
        legal_basis: GDPR legal basis (consent, contract, legal_obligation, etc.)
        retention_years: Data retention period in years
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
        # Compliance fields (#109)
        "data_classification": data_classification,
        "legal_basis": legal_basis,
        "retention_years": retention_years,
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
            await db.commit()
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
    """Extract client IP using X-Real-IP (set by nginx to $remote_addr).

    Nginx overrides X-Forwarded-For with $remote_addr and sets X-Real-IP,
    preventing client-supplied header spoofing.  Prefer X-Real-IP (single
    address), fall back to X-Forwarded-For first entry, then ASGI peer.
    """
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# ---------------------------------------------------------------------------
# Audit search (reads from JSONL fallback file)
# ---------------------------------------------------------------------------


def search_audit_events(
    user_sub: str | None = None,
    event_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Search audit events from the JSONL fallback file.

    Provides a queryable interface to audit logs without requiring
    a PostgreSQL connection (uses the JSONL fallback file).

    Args:
        user_sub: Filter by user subject identifier
        event_type: Filter by event type (from AuditEvents constants)
        from_date: Filter events after this ISO date (inclusive)
        to_date: Filter events before this ISO date (inclusive)
        limit: Maximum number of results (default: 100)
        offset: Number of results to skip (default: 0)

    Returns:
        List of matching audit event dicts
    """
    results: list[dict[str, Any]] = []

    if not _AUDIT_LOG_FILE.exists():
        return results

    try:
        with _AUDIT_LOG_FILE.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Apply filters
                if user_sub and event.get("user_sub") != user_sub:
                    continue
                if event_type and event.get("event_type") != event_type:
                    continue
                if from_date:
                    ts = event.get("timestamp", "")
                    if ts < from_date:
                        continue
                if to_date:
                    ts = event.get("timestamp", "")
                    if ts > to_date:
                        continue

                results.append(event)
    except Exception as e:
        logger.warning(f"Failed to search audit events: {e}")

    # Sort by timestamp descending (most recent first)
    results.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    # Apply pagination
    return results[offset : offset + limit]


# ---------------------------------------------------------------------------
# GDPR Article 30 Register
# ---------------------------------------------------------------------------

# Processing activities register for GDPR compliance
GDPR_PROCESSING_REGISTER: list[dict[str, Any]] = [
    {
        "activity": "Digital Pathology Slide Viewing",
        "purpose": "Clinical diagnosis and treatment",
        "legal_basis": "legal_obligation",
        "data_categories": ["health_data", "patient_identifiers"],
        "data_subjects": ["patients"],
        "recipients": ["pathologists", "treating_physicians"],
        "retention_years": 30,
        "security_measures": ["encryption", "access_control", "audit_trail"],
    },
    {
        "activity": "ML-Assisted Analysis",
        "purpose": "Computer-aided diagnosis support",
        "legal_basis": "legitimate_interest",
        "data_categories": ["health_data", "slide_images"],
        "data_subjects": ["patients"],
        "recipients": ["pathologists"],
        "retention_years": 30,
        "security_measures": ["encryption", "access_control", "audit_trail", "anonymization"],
    },
    {
        "activity": "Annotation and Reporting",
        "purpose": "Pathology reporting and documentation",
        "legal_basis": "legal_obligation",
        "data_categories": ["health_data", "diagnostic_conclusions"],
        "data_subjects": ["patients"],
        "recipients": ["pathologists", "treating_physicians", "health_insurers"],
        "retention_years": 30,
        "security_measures": ["encryption", "access_control", "audit_trail"],
    },
    {
        "activity": "Audit Trail Logging",
        "purpose": "Security monitoring and regulatory compliance",
        "legal_basis": "legal_obligation",
        "data_categories": ["access_logs", "user_identifiers"],
        "data_subjects": ["system_users"],
        "recipients": ["system_administrators", "auditors"],
        "retention_years": 10,
        "security_measures": ["encryption", "integrity_protection", "access_control"],
    },
    {
        "activity": "eHealth Platform Communication",
        "purpose": "Secure messaging and identity verification",
        "legal_basis": "legal_obligation",
        "data_categories": ["practitioner_identifiers", "health_data"],
        "data_subjects": ["practitioners", "patients"],
        "recipients": ["ehealth_platform", "other_practitioners"],
        "retention_years": 10,
        "security_measures": ["encryption", "saml_authentication", "audit_trail"],
    },
]
