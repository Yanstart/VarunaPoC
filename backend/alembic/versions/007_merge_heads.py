"""Merge two branches: 006 (worklist) + 006a (tenant_id)

Revision ID: 007
Revises: 006, 006a
Create Date: 2026-03-19

Both branches descended from 005. This merge point unifies the migration
chain so subsequent migrations have a single parent.

For existing databases that already applied both 006 migrations under the
old shared revision ID "006": run `alembic stamp 007` to update the
alembic_version table without re-running any DDL.
"""

from typing import Sequence, Union

revision: str = "007"
down_revision: tuple[str, str] = ("006", "006a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge point — no DDL changes.
    # Both branches (worklist tables + tenant_id columns) are already applied.
    pass


def downgrade() -> None:
    # Merge point — no DDL changes to reverse.
    pass
