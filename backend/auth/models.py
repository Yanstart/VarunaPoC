"""
Auth ORM Models - Users, Audit Events, Session State, Break-Glass Logs.

These tables store auth-related data. User identity comes from the IdP (Keycloak),
but we track local state: audit events, session roaming, break-glass activations.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class User(Base):
    """
    Local user record (synced from IdP on first login).

    We do NOT store passwords. Identity is managed by the IdP.
    This table stores local preferences and last-seen metadata.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_role: Mapped[str] = mapped_column(String(50), nullable=False, default="LECTURE_SEULE")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self):
        return f"<User(sub='{self.sub}', username='{self.username}', role='{self.primary_role}')>"


class AuditEvent(Base):
    """
    Audit trail for all significant actions.

    Retention: 6+ years for clinical compliance (HIPAA, GDPR).
    Levels: INFO, WARNING, CRITICAL (break-glass, admin actions).
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="INFO"
    )  # INFO, WARNING, CRITICAL
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # SLIDE_VIEWED, ANNOTATION_CREATED, etc.
    user_sub: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # slide, annotation, label, etc.
    resource_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self):
        return (
            f"<AuditEvent(type='{self.event_type}', user='{self.user_sub}', "
            f"action='{self.action}')>"
        )


class SessionState(Base):
    """
    Session roaming state - allows users to restore their viewer state
    when switching workstations (common in hospital environments).
    """

    __tablename__ = "session_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_sub: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    state_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def __repr__(self):
        return f"<SessionState(user='{self.user_sub}')>"


class BreakGlassLog(Base):
    """
    Break-glass emergency access log.

    Every activation is logged as CRITICAL audit event.
    Must be reviewed by ADMIN_TECHNIQUE.
    """

    __tablename__ = "break_glass_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_sub: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    def __repr__(self):
        return f"<BreakGlassLog(user='{self.user_sub}', reason='{self.reason[:30]}...')>"
