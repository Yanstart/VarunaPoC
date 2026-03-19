"""Add rejection_reason to corrections table

Revision ID: 009
Revises: 008
Create Date: 2026-03-19

Structured rejection reason for ML retraining pipeline analysis.
Complements the free-text 'comment' field with a categorical value.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "corrections",
        sa.Column("rejection_reason", sa.String(50), nullable=True),
    )
    op.create_index(
        "idx_corrections_type_reason",
        "corrections",
        ["correction_type", "rejection_reason"],
    )


def downgrade() -> None:
    op.drop_index("idx_corrections_type_reason", table_name="corrections")
    op.drop_column("corrections", "rejection_reason")
