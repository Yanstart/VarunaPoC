"""Add tenant_id column to annotations, labels, corrections, quality_reports

Revision ID: 007
Revises: 006
Create Date: 2026-03-11

Multi-tenancy scaffolding: adds tenant_id to all annotation-related tables.
Existing rows default to 'default' tenant for backward compatibility.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- annotations table --
    op.add_column(
        "annotations",
        sa.Column(
            "tenant_id",
            sa.String(100),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index("idx_annotations_tenant_id", "annotations", ["tenant_id"])
    op.create_index("idx_annotations_tenant_slide", "annotations", ["tenant_id", "slide_id"])

    # -- annotation_labels table --
    op.add_column(
        "annotation_labels",
        sa.Column(
            "tenant_id",
            sa.String(100),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index("idx_labels_tenant", "annotation_labels", ["tenant_id"])
    # Replace unique(name) with unique(tenant_id, name) for per-tenant label names
    op.drop_constraint("annotation_labels_name_key", "annotation_labels", type_="unique")
    op.create_unique_constraint("uq_labels_tenant_name", "annotation_labels", ["tenant_id", "name"])

    # -- corrections table --
    op.add_column(
        "corrections",
        sa.Column(
            "tenant_id",
            sa.String(100),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index("idx_corrections_tenant", "corrections", ["tenant_id"])

    # -- quality_reports table --
    op.add_column(
        "quality_reports",
        sa.Column(
            "tenant_id",
            sa.String(100),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index("idx_quality_reports_tenant", "quality_reports", ["tenant_id"])


def downgrade() -> None:
    # -- quality_reports --
    op.drop_index("idx_quality_reports_tenant")
    op.drop_column("quality_reports", "tenant_id")

    # -- corrections --
    op.drop_index("idx_corrections_tenant")
    op.drop_column("corrections", "tenant_id")

    # -- annotation_labels --
    op.drop_constraint("uq_labels_tenant_name", "annotation_labels", type_="unique")
    op.create_unique_constraint("annotation_labels_name_key", "annotation_labels", ["name"])
    op.drop_index("idx_labels_tenant")
    op.drop_column("annotation_labels", "tenant_id")

    # -- annotations --
    op.drop_index("idx_annotations_tenant_slide")
    op.drop_index("idx_annotations_tenant_id")
    op.drop_column("annotations", "tenant_id")
