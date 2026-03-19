"""Add notes, status, validated_by, validated_at to annotations

Revision ID: 008
Revises: 006 (merges both 006 branches: tenant_id + worklist)
Create Date: 2026-03-18

Merge point for the two 006 revisions, then adds annotation workflow fields.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("annotations", sa.Column("notes", sa.String(2000), nullable=True))
    op.add_column(
        "annotations",
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
    )
    op.add_column("annotations", sa.Column("validated_by", sa.String(200), nullable=True))
    op.add_column(
        "annotations",
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_annotations_status", "annotations", ["status"])


def downgrade() -> None:
    op.drop_index("idx_annotations_status", table_name="annotations")
    op.drop_column("annotations", "validated_at")
    op.drop_column("annotations", "validated_by")
    op.drop_column("annotations", "status")
    op.drop_column("annotations", "notes")
