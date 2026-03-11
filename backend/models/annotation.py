"""
Annotation ORM Model

Stores spatial annotations on histological slides.
Supports manual annotations, auto-detected regions, and confirmed detections.

PostGIS geometry with SRID=0 (pixel coordinates, not geographic).
"""

import uuid
from datetime import UTC, datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=text("'default'"), index=True
    )
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=0), nullable=False
    )
    geometry_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # polygon, rectangle, point, circle, freehand
    annotation_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual", index=True
    )  # manual, auto, auto_confirmed
    label_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("annotation_labels.id", ondelete="SET NULL"),
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    properties: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationship
    label = relationship("AnnotationLabel", back_populates="annotations", lazy="selectin")

    __table_args__ = (
        Index("idx_annotations_geometry", "geometry", postgresql_using="gist"),
        Index("idx_annotations_tenant_slide", "tenant_id", "slide_id"),
    )

    def __repr__(self):
        return (
            f"<Annotation(id='{self.id}', slide='{self.slide_id}', "
            f"type='{self.annotation_type}')>"
        )
