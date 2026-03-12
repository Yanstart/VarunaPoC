"""
WorklistAssignment ORM Model

Stores slide assignments for pathologists (worklist / case queue).
Replaces the deterministic mock in routes/slides.py with a real persistent
DB record per (slide_id, user_sub) pair.

Statuses:
    pending     - assigned but not yet opened
    in_progress - opened at least once, not yet marked complete
    completed   - explicitly marked done by the user

The `is_new` flag is derived at query time (never opened = viewed_at IS NULL in
ViewHistory), but is stored here as a convenience column so the worklist
endpoint can return it without a join on every call.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class WorklistAssignment(Base):
    """One row per (slide, user) assignment in the pathologist worklist."""

    __tablename__ = "worklist_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    user_sub: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | in_progress | completed
    assigned_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    # Convenience flag: True until the user opens the slide at least once.
    # Updated by the view-history upsert logic.
    is_new: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Optional free-text note from the assigning admin
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        # Enforce uniqueness: each user can only be assigned a slide once
        Index(
            "uq_worklist_slide_user",
            "slide_id",
            "user_sub",
            unique=True,
        ),
        Index("idx_worklist_user_status", "user_sub", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<WorklistAssignment(slide='{self.slide_id}', "
            f"user='{self.user_sub}', status='{self.status}')>"
        )
