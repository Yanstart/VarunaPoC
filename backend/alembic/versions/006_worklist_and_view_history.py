"""Worklist assignments and view history tables

Replaces the deterministic mock data in /api/slides/worklist and
/api/slides/history with real persistent DB rows.

Revision ID: 006
Revises: 005
Create Date: 2026-03-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # worklist_assignments table
    # ========================================
    op.create_table(
        "worklist_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slide_id", sa.String(500), nullable=False),
        sa.Column("user_sub", sa.String(500), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),  # pending | in_progress | completed
        sa.Column(
            "assigned_date",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("is_new", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("notes", sa.String(1000), nullable=True),
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
    op.create_index(
        "uq_worklist_slide_user",
        "worklist_assignments",
        ["slide_id", "user_sub"],
        unique=True,
    )
    op.create_index("idx_worklist_slide_id", "worklist_assignments", ["slide_id"])
    op.create_index("idx_worklist_user_sub", "worklist_assignments", ["user_sub"])
    op.create_index(
        "idx_worklist_user_status",
        "worklist_assignments",
        ["user_sub", "status"],
    )

    # ========================================
    # view_history table
    # ========================================
    op.create_table(
        "view_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slide_id", sa.String(500), nullable=False),
        sa.Column("user_sub", sa.String(500), nullable=False),
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "uq_view_history_slide_user",
        "view_history",
        ["slide_id", "user_sub"],
        unique=True,
    )
    op.create_index("idx_view_history_slide_id", "view_history", ["slide_id"])
    op.create_index("idx_view_history_user_sub", "view_history", ["user_sub"])
    op.create_index(
        "idx_view_history_user_viewed",
        "view_history",
        ["user_sub", "viewed_at"],
    )


def downgrade() -> None:
    # view_history
    op.drop_index("idx_view_history_user_viewed")
    op.drop_index("idx_view_history_user_sub")
    op.drop_index("idx_view_history_slide_id")
    op.drop_index("uq_view_history_slide_user")
    op.drop_table("view_history")

    # worklist_assignments
    op.drop_index("idx_worklist_user_status")
    op.drop_index("idx_worklist_user_sub")
    op.drop_index("idx_worklist_slide_id")
    op.drop_index("uq_worklist_slide_user")
    op.drop_table("worklist_assignments")
