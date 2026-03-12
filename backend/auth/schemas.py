"""
Auth Pydantic Schemas - Request/Response models for auth endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CurrentUser(BaseModel):
    """Represents the authenticated (or anonymous) user."""

    sub: str = Field(..., description="Subject identifier (unique user ID from IdP)")
    username: str = Field(..., description="Display name / preferred_username")
    email: str | None = Field(None, description="User email")
    roles: list[str] = Field(default_factory=list, description="Assigned roles")
    is_anonymous: bool = Field(False, description="True when AUTH_ENABLED=false")
    break_glass_active: bool = Field(False, description="Emergency access activated")

    @property
    def primary_role(self) -> str:
        """Return highest-privilege role."""
        role_priority = {
            "ADMIN_TECHNIQUE": 4,
            "MEDECIN": 3,
            "INFIRMIER": 2,
            "LECTURE_SEULE": 1,
        }
        if not self.roles:
            return "LECTURE_SEULE"
        return max(self.roles, key=lambda r: role_priority.get(r, 0))

    def has_role(self, *roles: str) -> bool:
        """Check if user has any of the specified roles."""
        return any(r in self.roles for r in roles)


class BreakGlassRequest(BaseModel):
    """Request to activate emergency break-glass access."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Medical justification for emergency access",
    )
    duration_minutes: int = Field(
        30,
        ge=5,
        le=120,
        description="Duration of elevated access in minutes",
    )


class BreakGlassResponse(BaseModel):
    """Response after break-glass activation."""

    activated: bool
    expires_at: datetime
    user_sub: str
    reason: str
    audit_id: str | None = None


class BreakGlassIssueRequest(BaseModel):
    """Request to issue a break-glass emergency token for a target user (admin only)."""

    target_user: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Subject identifier of the user receiving emergency access",
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Medical/operational justification for emergency access",
    )
    duration_minutes: int = Field(
        30,
        ge=5,
        le=60,
        description="Duration of emergency access in minutes (max 60)",
    )


class BreakGlassIssueResponse(BaseModel):
    """Response after issuing a break-glass emergency token."""

    session_id: str
    target_user: str
    issued_by: str
    reason: str
    duration_minutes: int
    activated_at: datetime
    expires_at: datetime
    token: str = Field(..., description="Temporary JWT for emergency access")


class BreakGlassSessionResponse(BaseModel):
    """A break-glass session in list responses."""

    id: str
    target_user: str
    issued_by: str
    issued_by_username: str
    reason: str
    activated_at: datetime
    expires_at: datetime
    duration_minutes: int
    status: str
    revoked: bool
    revoked_by: str | None = None
    revoked_at: datetime | None = None
    reviewed: bool
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None


class BreakGlassSessionListResponse(BaseModel):
    """List of break-glass sessions."""

    sessions: list[BreakGlassSessionResponse]
    total: int
    active_count: int
    pending_review_count: int


class BreakGlassReviewRequest(BaseModel):
    """Request to mark a break-glass session as reviewed."""

    notes: str = Field(
        "",
        max_length=1000,
        description="Review notes or justification acceptance",
    )


class SessionStateData(BaseModel):
    """User session state for cross-workstation roaming."""

    slide_id: str | None = None
    viewport: dict[str, Any] | None = None
    active_tools: list[str] | None = None
    annotations_visible: bool = True
    heatmap_visible: bool = False
    zoom_level: float | None = None
    center_x: float | None = None
    center_y: float | None = None


class SessionStateResponse(BaseModel):
    """Response for session state operations."""

    user_sub: str
    state: SessionStateData
    saved_at: datetime


class AuthStatusResponse(BaseModel):
    """Response for /auth/me endpoint."""

    user: CurrentUser
    auth_enabled: bool
    break_glass_available: bool = False
    session_roaming_available: bool = False
