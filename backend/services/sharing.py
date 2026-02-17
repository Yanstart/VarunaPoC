"""
Sharing Service - Manage slide sharing via temporary secure links.

Provides create, validate, revoke, and list operations for share tokens.
Uses in-memory dict storage; the ShareToken model defines the schema
for future database migration.
"""

import logging
import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ShareLink:
    """Represents a share link with metadata."""

    token: str
    url: str
    slide_id: str
    permission: str
    expires_at: Optional[datetime]
    created_by: Optional[str]
    revoked: bool = False
    access_count: int = 0
    created_at: Optional[datetime] = None


class SharingService:
    """Manage slide sharing via temporary links.

    Thread-safe in-memory store for share tokens.
    """

    def __init__(self):
        self._store: dict[str, ShareLink] = {}
        self._lock = threading.Lock()

    def create_share(
        self,
        slide_id: str,
        permission: str = "view",
        expires_hours: int = 24,
        created_by: str = None,
    ) -> ShareLink:
        """Generate a secure share link.

        Args:
            slide_id: ID of the slide to share.
            permission: "view" or "annotate".
            expires_hours: Hours until expiration (0 = no expiration).
            created_by: User sub who created the share.

        Returns:
            ShareLink with token and URL.
        """
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=expires_hours) if expires_hours > 0 else None

        link = ShareLink(
            token=token,
            url=f"/share/{token}",
            slide_id=slide_id,
            permission=permission,
            expires_at=expires_at,
            created_by=created_by,
            revoked=False,
            access_count=0,
            created_at=now,
        )

        with self._lock:
            self._store[token] = link

        logger.info(
            "Share created: slide=%s, permission=%s, expires=%s, by=%s",
            slide_id,
            permission,
            expires_at,
            created_by,
        )
        return link

    def validate_share(self, token: str) -> Optional[ShareLink]:
        """Validate a share token.

        Returns None if token is invalid, expired, or revoked.
        Increments access_count on successful validation.
        """
        with self._lock:
            link = self._store.get(token)

        if link is None:
            return None

        if link.revoked:
            return None

        if link.expires_at is not None and datetime.now(UTC) > link.expires_at:
            return None

        with self._lock:
            link.access_count += 1

        return link

    def revoke_share(self, token: str) -> bool:
        """Revoke a share link.

        Returns True if the token was found and revoked, False otherwise.
        """
        with self._lock:
            link = self._store.get(token)
            if link is None:
                return False
            link.revoked = True

        logger.info("Share revoked: token=%s, slide=%s", token[:8] + "...", link.slide_id)
        return True

    def list_shares(
        self,
        slide_id: str = None,
        created_by: str = None,
    ) -> list[ShareLink]:
        """List active (non-revoked, non-expired) shares, optionally filtered.

        Args:
            slide_id: Filter by slide ID.
            created_by: Filter by creator's user sub.

        Returns:
            List of active ShareLink objects.
        """
        now = datetime.now(UTC)
        results = []

        with self._lock:
            for link in self._store.values():
                if link.revoked:
                    continue
                if link.expires_at is not None and now > link.expires_at:
                    continue
                if slide_id is not None and link.slide_id != slide_id:
                    continue
                if created_by is not None and link.created_by != created_by:
                    continue
                results.append(link)

        return results


# Module-level singleton
sharing_service = SharingService()
