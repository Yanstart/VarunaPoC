"""
QualityReport ORM Model - Cache table for expensive quality computations.

Stores pre-computed quality metric results (kappa, confusion matrix, etc.)
with a TTL-based expiration. Optional - quality module works without it.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # kappa, fleiss, confusion_matrix, f1, iou_distribution, disagreements
    annotators: Mapped[list] = mapped_column(ARRAY(String(200)), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_quality_reports_lookup", "slide_id", "report_type"),
        Index("idx_quality_reports_expires", "expires_at"),
    )

    def __repr__(self):
        return (
            f"<QualityReport(slide='{self.slide_id}', "
            f"type='{self.report_type}', annotators={self.annotators})>"
        )
