"""
AnnotationLabel ORM Model

Labels used to categorize annotations (e.g. "Tumor", "Stroma", "Necrosis").
Each annotation references a label for consistent color and category display.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class AnnotationLabel(Base):
    __tablename__ = "annotation_labels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#FF0000")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationship
    annotations = relationship("Annotation", back_populates="label", lazy="selectin")

    def __repr__(self):
        return f"<AnnotationLabel(name='{self.name}', color='{self.color}')>"
