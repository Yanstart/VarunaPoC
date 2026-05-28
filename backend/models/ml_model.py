"""ML model registry — ORM mapping for the `ml_models` table.

Every model that produces annotations (auto-detected regions, predictions,
embeddings) is registered here. Downstream tables — annotations.source_model_id,
corrections.model_id, dataset_snapshots.training_dataset_id — reference this
table by foreign key so the entire ML supply chain is traceable end-to-end.

Scope of this issue (#370) is the bare registry. Foundation-model adapters
(UNI, CONCH, Virchow, …) live in #346 and register entries into this table.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .annotation import Base


class MLModel(Base):
    """A registered ML model — versioned, traceable, with license metadata.

    Tenancy:
        * `tenant_id = "global"` for models that all tenants may reference
          (foundation models, public checkpoints).
        * `tenant_id = "<hospital_slug>"` for models trained locally on a
          tenant's private data.

    Lifecycle:
        registered_at → deployed_at (optional) → retired_at (soft delete).
        A retired model is never physically removed: existing annotations
        keep their `source_model_id` valid for audit.
    """

    __tablename__ = "ml_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        server_default=text("'default'"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    framework: Mapped[str | None] = mapped_column(String(50), nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(100), nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_shape: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    embedding_dim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checkpoint_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checkpoint_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mlflow_experiment_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mlflow_model_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    usage_constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    deployed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    retired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            "version",
            name="uq_mlmodel_tenant_name_version",
        ),
        # Defense in depth: Pydantic enforces these at the API boundary, but
        # raw SQL writes (DBA, migration scripts) must also be safe.
        CheckConstraint(
            "embedding_dim IS NULL OR embedding_dim >= 0",
            name="ck_mlmodel_embedding_dim_nonneg",
        ),
        CheckConstraint(
            "deployed_at IS NULL OR retired_at IS NULL OR deployed_at <= retired_at",
            name="ck_mlmodel_lifecycle_chronology",
        ),
        Index(
            "idx_mlmodel_task_active",
            "task_type",
            postgresql_where=text("retired_at IS NULL"),
        ),
    )

    def __repr__(self) -> str:
        retired = " (retired)" if self.retired_at else ""
        return (
            f"<MLModel(id='{self.id}', name='{self.name}', "
            f"version='{self.version}', task='{self.task_type}'{retired})>"
        )

    @property
    def is_active(self) -> bool:
        """True iff the model is registered and not yet retired."""
        return self.retired_at is None

    @property
    def is_deployed(self) -> bool:
        """True iff the model has been deployed and not yet retired."""
        return self.deployed_at is not None and self.retired_at is None
