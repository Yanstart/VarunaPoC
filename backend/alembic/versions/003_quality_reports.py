"""Quality reports cache table

Revision ID: 003
Revises: 002
Create Date: 2026-02-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quality_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slide_id", sa.String(500), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("annotators", postgresql.ARRAY(sa.String(200)), nullable=False),
        sa.Column("parameters", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("result", postgresql.JSONB, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_quality_reports_slide", "quality_reports", ["slide_id"])
    op.create_index(
        "idx_quality_reports_lookup",
        "quality_reports",
        ["slide_id", "report_type"],
    )
    op.create_index("idx_quality_reports_expires", "quality_reports", ["expires_at"])


def downgrade() -> None:
    op.drop_table("quality_reports")
