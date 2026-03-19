"""
Correction ORM Model

Tracks pathologist corrections to ML predictions.
Links to annotations table for provenance tracking.
Supports: confirmed, rejected, refined (geometry edit), relabeled.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Correction(Base):
    __tablename__ = "corrections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=text("'default'"), index=True
    )
    annotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("annotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    correction_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # confirmed, rejected, refined, relabeled
    original_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    corrected_label_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("annotation_labels.id", ondelete="SET NULL"),
        nullable=True,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # false_positive_artifact, false_positive_inflammation, imprecise_contour, wrong_label, other
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    annotation = relationship("Annotation", lazy="selectin")
    corrected_label = relationship("AnnotationLabel", lazy="selectin")

    __table_args__ = (Index("idx_corrections_tenant", "tenant_id"),)

    def __repr__(self):
        return (
            f"<Correction(id='{self.id}', type='{self.correction_type}', "
            f"annotation='{self.annotation_id}')>"
        )
