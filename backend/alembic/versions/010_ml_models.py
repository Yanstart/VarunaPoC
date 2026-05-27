"""Create ml_models registry table

Revision ID: 010
Revises: 009
Create Date: 2026-05-27

Foundation table for the ML supply chain. Every annotation produced by AI
(annotation_type IN ('auto', 'auto_confirmed')) will reference an entry in
this table via `source_model_id` (see issue #363). Corrections likewise
reference the model that produced the original prediction.

This migration is the schema-only foundation of #346 (foundation model
registry). The adapter implementations for UNI / CONCH / Virchow / GigaPath
live in #346 and register their entries into this table at startup.

Resolves audit gap G2 from
`docs/architecture/ANNOTATION_DATA_MODEL_AUDIT.md`.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ml_models",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            sa.String(100),
            nullable=False,
            server_default=sa.text("'default'"),
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("framework", sa.String(50), nullable=True),
        sa.Column("architecture", sa.String(100), nullable=True),
        # Free-form at the DB level, validated as a Literal at the Pydantic
        # boundary so adding a new task_type does not require a migration
        # (design decision D1 / B for issue #370).
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("input_shape", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding_dim", sa.Integer, nullable=True),
        sa.Column("checkpoint_hash", sa.String(128), nullable=True),
        sa.Column("checkpoint_uri", sa.Text, nullable=True),
        # MLflow lineage. Typed columns (not metadata_extra JSONB) so they can
        # be indexed and referenced as foreign keys virtuels by Wave 10 issues
        # (#339 drift, #341 CI/CD, #347 fine-tuning, #348 validation). Required
        # for AI Act art. 12 traceability of training runs.
        sa.Column("mlflow_run_id", sa.String(64), nullable=True),
        sa.Column("mlflow_experiment_id", sa.String(32), nullable=True),
        sa.Column("mlflow_model_uri", sa.Text, nullable=True),
        # Same rationale as task_type: free at DB level, validated by Pydantic.
        sa.Column("license", sa.String(100), nullable=True),
        sa.Column(
            "usage_constraints",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("registered_by", sa.String(200), nullable=True),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "metadata_extra",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "name",
            "version",
            name="uq_mlmodel_tenant_name_version",
        ),
        # Defense in depth: the API validates with Pydantic, but raw SQL
        # writes (DBA, migration scripts) must also be safe.
        sa.CheckConstraint(
            "embedding_dim IS NULL OR embedding_dim >= 0",
            name="ck_mlmodel_embedding_dim_nonneg",
        ),
        sa.CheckConstraint(
            "deployed_at IS NULL OR retired_at IS NULL OR deployed_at <= retired_at",
            name="ck_mlmodel_lifecycle_chronology",
        ),
    )

    op.create_index("idx_mlmodel_tenant_id", "ml_models", ["tenant_id"])

    # Partial index: only the currently active models are hit on the routing
    # paths (predict / detect / embed). Keeps the index lean as retired models
    # accumulate.
    op.create_index(
        "idx_mlmodel_task_active",
        "ml_models",
        ["task_type"],
        postgresql_where=sa.text("retired_at IS NULL"),
    )

    # Conditional index on mlflow_run_id — only registered models have one.
    # Used by Wave 10 issues to look up "which model came from MLflow run X?"
    # (drift detection, CI/CD champion/challenger, fine-tuning lineage).
    op.create_index(
        "idx_mlmodel_mlflow_run",
        "ml_models",
        ["mlflow_run_id"],
        postgresql_where=sa.text("mlflow_run_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_mlmodel_mlflow_run", table_name="ml_models")
    op.drop_index("idx_mlmodel_task_active", table_name="ml_models")
    op.drop_index("idx_mlmodel_tenant_id", table_name="ml_models")
    op.drop_table("ml_models")
