"""
Annotations Routes - CRUD API for spatial annotations

Endpoints for managing annotations on histological slides,
including spatial queries, batch operations, and GeoJSON export.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from core.database import get_db
from schemas.annotation import (
    AnnotationBatchCreate,
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    LabelCreate,
    LabelResponse,
    LabelUpdate,
)
from schemas.geojson import GeoJSONFeatureCollection
from services import annotation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/annotations", tags=["Annotations"])


# ============================================
# Annotation Endpoints
# ============================================


@router.post("/{slide_id}", response_model=AnnotationResponse, status_code=201)
async def create_annotation(
    slide_id: str,
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Create a single annotation on a slide."""
    try:
        # Populate created_by from authenticated user if not set
        if not data.created_by:
            data.created_by = current_user.username
        result = await annotation_service.create_annotation(db, slide_id, data)
        return AnnotationResponse(**result)
    except Exception as e:
        logger.error(f"Failed to create annotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{slide_id}", response_model=List[AnnotationResponse])
async def list_annotations(
    slide_id: str,
    annotation_type: Optional[str] = Query(
        None, description="Filter: manual, auto, auto_confirmed"
    ),
    label_id: Optional[UUID] = Query(None, description="Filter by label ID"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    bbox_x1: Optional[float] = Query(None, description="Spatial filter: min X"),
    bbox_y1: Optional[float] = Query(None, description="Spatial filter: min Y"),
    bbox_x2: Optional[float] = Query(None, description="Spatial filter: max X"),
    bbox_y2: Optional[float] = Query(None, description="Spatial filter: max Y"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List annotations for a slide with optional filters.

    Spatial filter uses ST_Intersects with bounding box for viewport queries.
    """
    bbox = None
    if all(v is not None for v in [bbox_x1, bbox_y1, bbox_x2, bbox_y2]):
        bbox = [bbox_x1, bbox_y1, bbox_x2, bbox_y2]

    results = await annotation_service.get_annotations(
        db,
        slide_id,
        annotation_type=annotation_type,
        label_id=label_id,
        min_confidence=min_confidence,
        bbox=bbox,
    )
    return [AnnotationResponse(**r) for r in results]


@router.get("/{slide_id}/stats")
async def get_annotation_stats(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get annotation statistics for a slide.

    Returns total count, counts by label, counts by type,
    and confidence distribution (high/medium/low/unscored).
    """
    return await annotation_service.get_annotation_stats(db, slide_id)


@router.get("/{slide_id}/export", response_model=GeoJSONFeatureCollection)
async def export_annotations(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Export all annotations for a slide as GeoJSON FeatureCollection."""
    return await annotation_service.export_annotations_geojson(db, slide_id)


@router.get("/{slide_id}/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    slide_id: str,
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a single annotation by ID."""
    result = await annotation_service.get_annotation(db, slide_id, annotation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return AnnotationResponse(**result)


@router.put("/{slide_id}/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    slide_id: str,
    annotation_id: UUID,
    data: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Update an annotation."""
    result = await annotation_service.update_annotation(db, slide_id, annotation_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return AnnotationResponse(**result)


@router.delete("/{slide_id}/{annotation_id}", status_code=204)
async def delete_annotation(
    slide_id: str,
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Delete an annotation."""
    deleted = await annotation_service.delete_annotation(db, slide_id, annotation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Annotation not found")


@router.post("/{slide_id}/batch", response_model=List[AnnotationResponse], status_code=201)
async def batch_create_annotations(
    slide_id: str,
    data: AnnotationBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Batch create annotations (used by auto-detection pipeline)."""
    try:
        results = await annotation_service.batch_create_annotations(db, slide_id, data.annotations)
        return [AnnotationResponse(**r) for r in results]
    except Exception as e:
        logger.error(f"Batch create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Label Endpoints
# ============================================

label_router = APIRouter(prefix="/api/labels", tags=["Labels"])


@label_router.get("/", response_model=List[LabelResponse])
async def list_labels(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all annotation labels."""
    labels = await annotation_service.get_labels(db)
    return [LabelResponse.model_validate(label) for label in labels]


@label_router.post("/", response_model=LabelResponse, status_code=201)
async def create_label(
    data: LabelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Create a new annotation label."""
    try:
        label = await annotation_service.create_label(
            db,
            name=data.name,
            color=data.color,
            category=data.category,
            description=data.description,
            sort_order=data.sort_order,
        )
        return LabelResponse.model_validate(label)
    except Exception as e:
        logger.error(f"Failed to create label: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@label_router.get("/{label_id}", response_model=LabelResponse)
async def get_label(
    label_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a label by ID."""
    label = await annotation_service.get_label(db, label_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return LabelResponse.model_validate(label)


@label_router.put("/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: UUID,
    data: LabelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Update a label."""
    update_data = data.model_dump(exclude_unset=True)
    label = await annotation_service.update_label(db, label_id, **update_data)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return LabelResponse.model_validate(label)


@label_router.delete("/{label_id}", status_code=204)
async def delete_label(
    label_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """Delete a label."""
    deleted = await annotation_service.delete_label(db, label_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Label not found")
