"""
Sharing Routes - Link sharing and annotation merge API.

Endpoints for creating, validating, revoking, and listing share links,
plus annotation merge for multi-user conflict resolution.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.annotation_merge import MergeStrategy, merge_service
from services.sharing import sharing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sharing", tags=["sharing"])


# ============================================
# Schemas
# ============================================


class CreateShareRequest(BaseModel):
    slide_id: str
    permission: str = Field("view", pattern="^(view|annotate)$")
    expires_hours: int = Field(24, ge=0, le=720)  # max 30 days


class ShareResponse(BaseModel):
    token: str
    url: str
    slide_id: str
    permission: str
    expires_at: Optional[datetime] = None


class MergeRequest(BaseModel):
    annotation_sets: list[list[dict]] = Field(
        ..., description="List of annotation lists (one per user/source)"
    )
    strategy: str = Field("union", pattern="^(union|last_write_wins|intersection)$")


class MergeConflictResponse(BaseModel):
    overlap_iou: float
    resolution: str


class MergeResponse(BaseModel):
    strategy: str
    total_input: int
    merged_count: int
    conflicts_found: int
    conflicts_resolved: int
    merged_annotations: list[dict]
    processing_time_ms: float


# ============================================
# Share Link Endpoints
# ============================================


@router.post("/", response_model=ShareResponse, status_code=201)
async def create_share(request: CreateShareRequest):
    """Create a share link for a slide."""
    link = sharing_service.create_share(
        slide_id=request.slide_id,
        permission=request.permission,
        expires_hours=request.expires_hours,
    )
    return ShareResponse(
        token=link.token,
        url=link.url,
        slide_id=link.slide_id,
        permission=link.permission,
        expires_at=link.expires_at,
    )


@router.get("/links", response_model=list[ShareResponse])
async def list_shares(slide_id: Optional[str] = None):
    """List active share links, optionally filtered by slide_id."""
    links = sharing_service.list_shares(slide_id=slide_id)
    return [
        ShareResponse(
            token=link.token,
            url=link.url,
            slide_id=link.slide_id,
            permission=link.permission,
            expires_at=link.expires_at,
        )
        for link in links
    ]


@router.get("/{token}", response_model=ShareResponse)
async def validate_share(token: str):
    """Validate a share token and return share info."""
    link = sharing_service.validate_share(token)
    if link is None:
        raise HTTPException(status_code=404, detail="Share link not found, expired, or revoked")
    return ShareResponse(
        token=link.token,
        url=link.url,
        slide_id=link.slide_id,
        permission=link.permission,
        expires_at=link.expires_at,
    )


@router.delete("/{token}", status_code=204)
async def revoke_share(token: str):
    """Revoke a share link."""
    revoked = sharing_service.revoke_share(token)
    if not revoked:
        raise HTTPException(status_code=404, detail="Share link not found")


# ============================================
# Annotation Merge Endpoint
# ============================================


@router.post("/merge", response_model=MergeResponse)
async def merge_annotations(request: MergeRequest):
    """Merge annotation sets with conflict resolution.

    Accepts multiple annotation lists and merges them using the
    specified strategy (union, last_write_wins, or intersection).
    """
    try:
        strategy = MergeStrategy(request.strategy)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {request.strategy}")

    result = merge_service.merge(
        annotation_sets=request.annotation_sets,
        strategy=strategy,
    )

    return MergeResponse(
        strategy=result.strategy,
        total_input=result.total_input,
        merged_count=result.merged_count,
        conflicts_found=result.conflicts_found,
        conflicts_resolved=result.conflicts_resolved,
        merged_annotations=result.merged_annotations,
        processing_time_ms=result.processing_time_ms,
    )
