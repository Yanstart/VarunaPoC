"""Auth and audit tables + user_sub column on annotations

Revision ID: 002
Revises: 001
Create Date: 2026-02-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # users table (local record, synced from IdP)
    # ========================================
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sub", sa.String(500), nullable=False, unique=True),
        sa.Column("username", sa.String(200), nullable=False),
        sa.Column("email", sa.String(500), nullable=True),
        sa.Column("primary_role", sa.String(50), nullable=False, server_default="LECTURE_SEULE"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preferences", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_users_sub", "users", ["sub"], unique=True)

    # ========================================
    # audit_events table
    # ========================================
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("level", sa.String(20), nullable=False, server_default="INFO"),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("user_sub", sa.String(500), nullable=True),
        sa.Column("username", sa.String(200), nullable=True),
        sa.Column("user_role", sa.String(50), nullable=True),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(500), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )
    op.create_index("idx_audit_timestamp", "audit_events", ["timestamp"])
    op.create_index("idx_audit_event_type", "audit_events", ["event_type"])
    op.create_index("idx_audit_user_sub", "audit_events", ["user_sub"])

    # ========================================
    # session_states table (session roaming)
    # ========================================
    op.create_table(
        "session_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_sub", sa.String(500), nullable=False, unique=True),
        sa.Column("state_data", postgresql.JSONB, nullable=True),
        sa.Column(
            "saved_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_session_user_sub", "session_states", ["user_sub"], unique=True)

    # ========================================
    # break_glass_logs table
    # ========================================
    op.create_table(
        "break_glass_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_sub", sa.String(500), nullable=False),
        sa.Column("username", sa.String(200), nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "activated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.String(500), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
    )
    op.create_index("idx_break_glass_user", "break_glass_logs", ["user_sub"])

    # ========================================
    # Add user_sub column to annotations table
    # ========================================
    op.add_column(
        "annotations",
        sa.Column("user_sub", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("annotations", "user_sub")
    op.drop_table("break_glass_logs")
    op.drop_table("session_states")
    op.drop_table("audit_events")
    op.drop_table("users")
