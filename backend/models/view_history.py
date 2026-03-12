"""
ViewHistory ORM Model

Tracks which slides a user has opened and how many times.
One row per (slide_id, user_sub) pair — upserted on every slide open event.

The `viewed_at` column records the most recent access timestamp.
The `view_count` column is incremented on each open.

This table is the authoritative source for the /api/slides/history endpoint
and also drives the `is_new` flag on WorklistAssignment rows.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ViewHistory(Base):
    """One row per (slide, user) pair tracking view frequency and recency."""

    __tablename__ = "view_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    user_sub: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        # Enforce uniqueness: one aggregate row per (slide, user)
        Index(
            "uq_view_history_slide_user",
            "slide_id",
            "user_sub",
            unique=True,
        ),
        Index("idx_view_history_user_viewed", "user_sub", "viewed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ViewHistory(slide='{self.slide_id}', "
            f"user='{self.user_sub}', count={self.view_count})>"
        )
