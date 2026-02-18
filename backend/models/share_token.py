"""
ShareToken ORM Model

Stores share link tokens for slide sharing functionality.
Supports view-only and annotate permission levels with expiration.

Schema defined here for future DB migration; current implementation
uses in-memory storage in SharingService.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class SharePermission(enum.StrEnum):
    VIEW = "view"
    ANNOTATE = "annotate"


class ShareToken(Base):
    __tablename__ = "share_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    permission: Mapped[SharePermission] = mapped_column(
        Enum(SharePermission), default=SharePermission.VIEW
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    access_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return (
            f"<ShareToken(id='{self.id}', slide='{self.slide_id}', "
            f"permission='{self.permission}', revoked={self.revoked})>"
        )
