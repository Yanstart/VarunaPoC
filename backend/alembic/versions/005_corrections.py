"""Corrections table for ML feedback loop

Revision ID: 005
Revises: 004
Create Date: 2026-02-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "annotation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("annotations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slide_id", sa.String(500), nullable=False),
        sa.Column("correction_type", sa.String(20), nullable=False),
        sa.Column("original_confidence", sa.Float, nullable=True),
        sa.Column(
            "corrected_label_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("annotation_labels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("model_name", sa.String(200), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("metadata_extra", postgresql.JSONB, nullable=True),
        sa.Column("created_by", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_corrections_annotation_id", "corrections", ["annotation_id"])
    op.create_index("idx_corrections_slide_id", "corrections", ["slide_id"])
    op.create_index("idx_corrections_type", "corrections", ["correction_type"])


def downgrade() -> None:
    op.drop_index("idx_corrections_type")
    op.drop_index("idx_corrections_slide_id")
    op.drop_index("idx_corrections_annotation_id")
    op.drop_table("corrections")
