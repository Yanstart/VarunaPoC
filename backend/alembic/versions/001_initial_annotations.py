"""Initial annotations and labels tables

Revision ID: 001
Revises:
Create Date: 2026-02-05
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # annotation_labels table
    op.create_table(
        "annotation_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("color", sa.String(7), nullable=False, server_default="#FF0000"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, server_default="0"),
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

    # annotations table
    op.create_table(
        "annotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slide_id", sa.String(500), nullable=False),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(geometry_type="GEOMETRY", srid=0),
            nullable=False,
        ),
        sa.Column("geometry_type", sa.String(20), nullable=False),
        sa.Column(
            "annotation_type",
            sa.String(20),
            nullable=False,
            server_default="manual",
        ),
        sa.Column(
            "label_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("annotation_labels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("properties", postgresql.JSONB, nullable=True),
        sa.Column("created_by", sa.String(200), nullable=True),
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

    # Indexes (geometry GIST index is auto-created by GeoAlchemy2)
    op.create_index("idx_annotations_slide_id", "annotations", ["slide_id"])
    op.create_index("idx_annotations_type", "annotations", ["annotation_type"])


def downgrade() -> None:
    op.drop_table("annotations")
    op.drop_table("annotation_labels")
