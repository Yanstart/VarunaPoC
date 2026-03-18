"""
Annotations Routes - CRUD API for spatial annotations

Endpoints for managing annotations on histological slides,
including spatial queries, batch operations, and GeoJSON export.
"""

import logging
from datetime import UTC, datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from core.database import get_db
from core.tenant import get_current_tenant
from models.annotation import Annotation
from rate_limiting import annotation_write_rate, limit
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

router = APIRouter(prefix="/annotations", tags=["Annotations"])


# ============================================
# Annotation Endpoints
# ============================================


@router.post("/{slide_id}", response_model=AnnotationResponse, status_code=201)
@limit(annotation_write_rate)
async def create_annotation(
    request: Request,
    slide_id: str,
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
):
    """Create a single annotation on a slide."""
    try:
        # Populate created_by from authenticated user if not set
        if not data.created_by:
            data.created_by = current_user.username
        result = await annotation_service.create_annotation(db, slide_id, data, tenant_id=tenant_id)
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
    tenant_id: str = Depends(get_current_tenant),
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
        tenant_id=tenant_id,
    )
    return [AnnotationResponse(**r) for r in results]


@router.get("/{slide_id}/stats")
async def get_annotation_stats(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Get annotation statistics for a slide.

    Returns total count, counts by label, counts by type,
    and confidence distribution (high/medium/low/unscored).
    """
    return await annotation_service.get_annotation_stats(db, slide_id, tenant_id=tenant_id)


@router.get("/{slide_id}/report")
async def get_annotation_report(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Detailed annotation report: validation stats, contributor list, timeline.
    """
    result = await db.execute(
        select(Annotation).where(
            Annotation.slide_id == slide_id,
            Annotation.tenant_id == tenant_id,
        )
    )
    annotations = result.scalars().all()

    contributors = {}
    validation_stats = {"pending": 0, "validated": 0, "rejected": 0}
    ai_corrections = {"total_ai": 0, "validated": 0, "rejected": 0}
    timeline = []

    for a in annotations:
        author = a.created_by or "anonymous"
        if author not in contributors:
            contributors[author] = {"annotations": 0, "validations": 0, "rejections": 0}
        contributors[author]["annotations"] += 1

        status = getattr(a, "status", "pending")
        if status in validation_stats:
            validation_stats[status] += 1

        validator = getattr(a, "validated_by", None)
        if validator:
            if validator not in contributors:
                contributors[validator] = {"annotations": 0, "validations": 0, "rejections": 0}
            if status == "validated":
                contributors[validator]["validations"] += 1
            elif status == "rejected":
                contributors[validator]["rejections"] += 1

        if a.annotation_type in ("auto", "auto_confirmed"):
            ai_corrections["total_ai"] += 1
            if status == "validated":
                ai_corrections["validated"] += 1
            elif status == "rejected":
                ai_corrections["rejected"] += 1

        validated_at = getattr(a, "validated_at", None)
        timeline.append(
            {
                "id": str(a.id),
                "type": a.annotation_type,
                "status": status,
                "created_by": a.created_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "validated_by": validator,
                "validated_at": validated_at.isoformat() if validated_at else None,
                "label": a.label.name if a.label else None,
                "notes": getattr(a, "notes", None),
            }
        )

    timeline.sort(key=lambda x: x["created_at"] or "", reverse=True)

    return {
        "slide_id": slide_id,
        "total": len(annotations),
        "validation": validation_stats,
        "ai_corrections": ai_corrections,
        "contributors": contributors,
        "timeline": timeline[:50],
    }


@router.get("/{slide_id}/export", response_model=GeoJSONFeatureCollection)
async def export_annotations(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Export all annotations for a slide as GeoJSON FeatureCollection."""
    return await annotation_service.export_annotations_geojson(db, slide_id, tenant_id=tenant_id)


@router.get("/{slide_id}/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    slide_id: str,
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get a single annotation by ID."""
    result = await annotation_service.get_annotation(
        db, slide_id, annotation_id, tenant_id=tenant_id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return AnnotationResponse(**result)


@router.put("/{slide_id}/{annotation_id}", response_model=AnnotationResponse)
@limit(annotation_write_rate)
async def update_annotation(
    request: Request,
    slide_id: str,
    annotation_id: UUID,
    data: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
):
    """Update an annotation."""
    result = await annotation_service.update_annotation(
        db, slide_id, annotation_id, data, tenant_id=tenant_id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return AnnotationResponse(**result)


@router.patch("/{slide_id}/{annotation_id}/validate", response_model=AnnotationResponse)
async def validate_annotation(
    slide_id: str,
    annotation_id: UUID,
    notes: str | None = Query(None, max_length=2000),
    current_user: CurrentUser = Depends(require_role("MEDECIN")),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Mark an annotation as validated by the current pathologist."""
    result = await db.execute(
        select(Annotation).where(
            Annotation.id == annotation_id,
            Annotation.slide_id == slide_id,
            Annotation.tenant_id == tenant_id,
        )
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(404, "Annotation not found")

    annotation.status = "validated"
    annotation.validated_by = current_user.username
    annotation.validated_at = datetime.now(UTC)
    if notes is not None:
        annotation.notes = notes

    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.patch("/{slide_id}/{annotation_id}/reject", response_model=AnnotationResponse)
async def reject_annotation(
    slide_id: str,
    annotation_id: UUID,
    notes: str | None = Query(None, max_length=2000),
    current_user: CurrentUser = Depends(require_role("MEDECIN")),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Mark an annotation as rejected (false positive)."""
    result = await db.execute(
        select(Annotation).where(
            Annotation.id == annotation_id,
            Annotation.slide_id == slide_id,
            Annotation.tenant_id == tenant_id,
        )
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(404, "Annotation not found")

    annotation.status = "rejected"
    annotation.validated_by = current_user.username
    annotation.validated_at = datetime.now(UTC)
    if notes is not None:
        annotation.notes = notes

    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.delete("/{slide_id}/{annotation_id}", status_code=204)
@limit(annotation_write_rate)
async def delete_annotation(
    request: Request,
    slide_id: str,
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
):
    """Delete an annotation."""
    deleted = await annotation_service.delete_annotation(
        db, slide_id, annotation_id, tenant_id=tenant_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Annotation not found")


@router.post("/{slide_id}/batch", response_model=List[AnnotationResponse], status_code=201)
@limit(annotation_write_rate)
async def batch_create_annotations(
    request: Request,
    slide_id: str,
    data: AnnotationBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
):
    """Batch create annotations (used by auto-detection pipeline)."""
    try:
        results = await annotation_service.batch_create_annotations(
            db, slide_id, data.annotations, tenant_id=tenant_id
        )
        return [AnnotationResponse(**r) for r in results]
    except Exception as e:
        logger.error(f"Batch create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Label Endpoints
# ============================================

label_router = APIRouter(prefix="/labels", tags=["Labels"])


@label_router.get("/", response_model=List[LabelResponse])
async def list_labels(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """List all annotation labels."""
    labels = await annotation_service.get_labels(db, tenant_id=tenant_id)
    return [LabelResponse.model_validate(label) for label in labels]


@label_router.post("/", response_model=LabelResponse, status_code=201)
async def create_label(
    data: LabelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
):
    """Create a new annotation label."""
    try:
        label = await annotation_service.create_label(
            db,
            name=data.name,
            color=data.color,
            tenant_id=tenant_id,
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
    tenant_id: str = Depends(get_current_tenant),
):
    """Get a label by ID."""
    label = await annotation_service.get_label(db, label_id, tenant_id=tenant_id)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return LabelResponse.model_validate(label)


@label_router.put("/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: UUID,
    data: LabelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
):
    """Update a label."""
    update_data = data.model_dump(exclude_unset=True)
    label = await annotation_service.update_label(db, label_id, tenant_id=tenant_id, **update_data)
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    return LabelResponse.model_validate(label)


@label_router.delete("/{label_id}", status_code=204)
async def delete_label(
    label_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
    tenant_id: str = Depends(get_current_tenant),
):
    """Delete a label."""
    deleted = await annotation_service.delete_label(db, label_id, tenant_id=tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Label not found")
