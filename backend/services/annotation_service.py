"""
Annotation Service - CRUD operations for spatial annotations

Handles creation, retrieval, update, and deletion of annotations
with PostGIS spatial queries for viewport-based filtering.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

from geoalchemy2.functions import ST_AsGeoJSON, ST_GeomFromGeoJSON, ST_Intersects, ST_MakeEnvelope
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.annotation import Annotation
from models.annotation_label import AnnotationLabel
from schemas.annotation import AnnotationCreate, AnnotationUpdate
from schemas.geojson import GeoJSONFeature, GeoJSONFeatureCollection, GeoJSONGeometry


def _geojson_to_wkb(geojson_geom: GeoJSONGeometry) -> str:
    """Convert GeoJSON geometry dict to PostGIS-compatible GeoJSON string."""
    return json.dumps({"type": geojson_geom.type, "coordinates": geojson_geom.coordinates})


async def _row_to_response(row: Annotation, db: AsyncSession) -> Dict[str, Any]:
    """Convert an Annotation ORM row to a response dict with GeoJSON geometry."""
    # Get GeoJSON geometry from PostGIS
    result = await db.execute(
        select(ST_AsGeoJSON(Annotation.geometry)).where(Annotation.id == row.id)
    )
    geojson_str = result.scalar_one()
    geom = json.loads(geojson_str)

    label_data = None
    if row.label:
        label_data = {
            "id": row.label.id,
            "name": row.label.name,
            "color": row.label.color,
            "category": row.label.category,
            "description": row.label.description,
            "sort_order": row.label.sort_order,
            "created_at": row.label.created_at,
            "updated_at": row.label.updated_at,
        }

    return {
        "id": row.id,
        "slide_id": row.slide_id,
        "geometry": GeoJSONGeometry(type=geom["type"], coordinates=geom["coordinates"]),
        "geometry_type": row.geometry_type,
        "annotation_type": row.annotation_type,
        "label_id": row.label_id,
        "label": label_data,
        "confidence": row.confidence,
        "properties": row.properties,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


# ============================================
# Annotation CRUD
# ============================================


async def create_annotation(
    db: AsyncSession, slide_id: str, data: AnnotationCreate, tenant_id: str = "default"
) -> Dict[str, Any]:
    """Create a single annotation."""
    geojson_str = _geojson_to_wkb(data.geometry)

    annotation = Annotation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        slide_id=slide_id,
        geometry=ST_GeomFromGeoJSON(geojson_str),
        geometry_type=data.geometry_type,
        annotation_type=data.annotation_type,
        label_id=data.label_id,
        confidence=data.confidence,
        properties=data.properties,
        created_by=data.created_by,
    )
    db.add(annotation)
    await db.flush()

    # Refresh to get computed fields
    await db.refresh(annotation)
    return await _row_to_response(annotation, db)


async def batch_create_annotations(
    db: AsyncSession,
    slide_id: str,
    annotations_data: List[AnnotationCreate],
    tenant_id: str = "default",
) -> List[Dict[str, Any]]:
    """Create multiple annotations in a single transaction."""
    results = []
    for data in annotations_data:
        geojson_str = _geojson_to_wkb(data.geometry)
        annotation = Annotation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            slide_id=slide_id,
            geometry=ST_GeomFromGeoJSON(geojson_str),
            geometry_type=data.geometry_type,
            annotation_type=data.annotation_type,
            label_id=data.label_id,
            confidence=data.confidence,
            properties=data.properties,
            created_by=data.created_by,
        )
        db.add(annotation)
        results.append(annotation)

    await db.flush()

    responses = []
    for anno in results:
        await db.refresh(anno)
        responses.append(await _row_to_response(anno, db))
    return responses


async def get_annotations(
    db: AsyncSession,
    slide_id: str,
    annotation_type: Optional[str] = None,
    label_id: Optional[uuid.UUID] = None,
    min_confidence: Optional[float] = None,
    bbox: Optional[List[float]] = None,
    tenant_id: str = "default",
) -> List[Dict[str, Any]]:
    """
    List annotations for a slide with optional filters.

    Args:
        bbox: [x1, y1, x2, y2] spatial bounding box filter
        tenant_id: Tenant identifier for data isolation
    """
    stmt = select(Annotation).where(
        Annotation.tenant_id == tenant_id,
        Annotation.slide_id == slide_id,
    )

    if annotation_type:
        stmt = stmt.where(Annotation.annotation_type == annotation_type)
    if label_id:
        stmt = stmt.where(Annotation.label_id == label_id)
    if min_confidence is not None:
        stmt = stmt.where(Annotation.confidence >= min_confidence)
    if bbox and len(bbox) == 4:
        envelope = ST_MakeEnvelope(bbox[0], bbox[1], bbox[2], bbox[3], 4326)
        stmt = stmt.where(ST_Intersects(Annotation.geometry, envelope))

    stmt = stmt.order_by(Annotation.created_at)

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [await _row_to_response(row, db) for row in rows]


async def get_annotation(
    db: AsyncSession, slide_id: str, annotation_id: uuid.UUID, tenant_id: str = "default"
) -> Optional[Dict[str, Any]]:
    """Get a single annotation by ID."""
    stmt = select(Annotation).where(
        Annotation.tenant_id == tenant_id,
        Annotation.id == annotation_id,
        Annotation.slide_id == slide_id,
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if not row:
        return None
    return await _row_to_response(row, db)


async def update_annotation(
    db: AsyncSession,
    slide_id: str,
    annotation_id: uuid.UUID,
    data: AnnotationUpdate,
    tenant_id: str = "default",
) -> Optional[Dict[str, Any]]:
    """Update an annotation."""
    stmt = select(Annotation).where(
        Annotation.tenant_id == tenant_id,
        Annotation.id == annotation_id,
        Annotation.slide_id == slide_id,
    )
    result = await db.execute(stmt)
    annotation = result.scalar_one_or_none()
    if not annotation:
        return None

    update_data = data.model_dump(exclude_unset=True)

    if "geometry" in update_data and update_data["geometry"] is not None:
        geom = update_data.pop("geometry")
        geojson_str = json.dumps({"type": geom["type"], "coordinates": geom["coordinates"]})
        update_data["geometry"] = ST_GeomFromGeoJSON(geojson_str)

    if update_data:
        stmt = (
            update(Annotation)
            .where(Annotation.tenant_id == tenant_id, Annotation.id == annotation_id)
            .values(**update_data)
        )
        await db.execute(stmt)
        await db.flush()

    await db.refresh(annotation)
    return await _row_to_response(annotation, db)


async def delete_annotation(
    db: AsyncSession, slide_id: str, annotation_id: uuid.UUID, tenant_id: str = "default"
) -> bool:
    """Delete an annotation. Returns True if deleted."""
    stmt = delete(Annotation).where(
        Annotation.tenant_id == tenant_id,
        Annotation.id == annotation_id,
        Annotation.slide_id == slide_id,
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def export_annotations_geojson(
    db: AsyncSession, slide_id: str, tenant_id: str = "default"
) -> GeoJSONFeatureCollection:
    """Export all annotations for a slide as GeoJSON FeatureCollection."""
    annotations = await get_annotations(db, slide_id, tenant_id=tenant_id)

    features = []
    for anno in annotations:
        feature = GeoJSONFeature(
            type="Feature",
            id=str(anno["id"]),
            geometry=anno["geometry"],
            properties={
                "annotation_type": anno["annotation_type"],
                "geometry_type": anno["geometry_type"],
                "label_id": str(anno["label_id"]) if anno["label_id"] else None,
                "label_name": anno["label"]["name"] if anno["label"] else None,
                "label_color": anno["label"]["color"] if anno["label"] else None,
                "confidence": anno["confidence"],
                "created_by": anno["created_by"],
                "created_at": anno["created_at"].isoformat() if anno["created_at"] else None,
                **(anno["properties"] or {}),
            },
        )
        features.append(feature)

    return GeoJSONFeatureCollection(
        features=features,
        metadata={"slide_id": slide_id, "count": len(features)},
    )


# ============================================
# Statistics / Counting
# ============================================


async def get_annotation_stats(
    db: AsyncSession, slide_id: str, tenant_id: str = "default"
) -> Dict[str, Any]:
    """
    Get annotation statistics for a slide: total count, counts by label, counts by type,
    and confidence distribution.
    """
    # Total count
    total_result = await db.execute(
        select(func.count(Annotation.id)).where(
            Annotation.tenant_id == tenant_id, Annotation.slide_id == slide_id
        )
    )
    total = total_result.scalar_one()

    # Count by annotation_type
    type_result = await db.execute(
        select(Annotation.annotation_type, func.count(Annotation.id))
        .where(Annotation.tenant_id == tenant_id, Annotation.slide_id == slide_id)
        .group_by(Annotation.annotation_type)
    )
    by_type = [{"type": row[0], "count": row[1]} for row in type_result.all()]

    # Count by label (with label info)
    label_result = await db.execute(
        select(
            AnnotationLabel.id,
            AnnotationLabel.name,
            AnnotationLabel.color,
            func.count(Annotation.id),
        )
        .join(AnnotationLabel, Annotation.label_id == AnnotationLabel.id)
        .where(Annotation.tenant_id == tenant_id, Annotation.slide_id == slide_id)
        .group_by(AnnotationLabel.id, AnnotationLabel.name, AnnotationLabel.color)
    )
    by_label = [
        {"label_id": str(row[0]), "name": row[1], "color": row[2], "count": row[3]}
        for row in label_result.all()
    ]

    # Count unlabeled
    unlabeled_result = await db.execute(
        select(func.count(Annotation.id)).where(
            Annotation.tenant_id == tenant_id,
            Annotation.slide_id == slide_id,
            Annotation.label_id.is_(None),
        )
    )
    unlabeled = unlabeled_result.scalar_one()

    # Confidence distribution (buckets: high>=0.8, medium 0.5-0.8, low <0.5, unscored=null)
    conf_high = await db.execute(
        select(func.count(Annotation.id)).where(
            Annotation.tenant_id == tenant_id,
            Annotation.slide_id == slide_id,
            Annotation.confidence >= 0.8,
        )
    )
    conf_med = await db.execute(
        select(func.count(Annotation.id)).where(
            Annotation.tenant_id == tenant_id,
            Annotation.slide_id == slide_id,
            Annotation.confidence >= 0.5,
            Annotation.confidence < 0.8,
        )
    )
    conf_low = await db.execute(
        select(func.count(Annotation.id)).where(
            Annotation.tenant_id == tenant_id,
            Annotation.slide_id == slide_id,
            Annotation.confidence.isnot(None),
            Annotation.confidence < 0.5,
        )
    )
    conf_none = await db.execute(
        select(func.count(Annotation.id)).where(
            Annotation.tenant_id == tenant_id,
            Annotation.slide_id == slide_id,
            Annotation.confidence.is_(None),
        )
    )

    return {
        "slide_id": slide_id,
        "total": total,
        "by_type": by_type,
        "by_label": by_label,
        "unlabeled": unlabeled,
        "confidence_distribution": {
            "high": conf_high.scalar_one(),
            "medium": conf_med.scalar_one(),
            "low": conf_low.scalar_one(),
            "unscored": conf_none.scalar_one(),
        },
    }


# ============================================
# Label CRUD
# ============================================


async def create_label(
    db: AsyncSession, name: str, color: str = "#FF0000", tenant_id: str = "default", **kwargs
) -> AnnotationLabel:
    label = AnnotationLabel(id=uuid.uuid4(), tenant_id=tenant_id, name=name, color=color, **kwargs)
    db.add(label)
    await db.flush()
    await db.refresh(label)
    return label


async def get_labels(db: AsyncSession, tenant_id: str = "default") -> List[AnnotationLabel]:
    result = await db.execute(
        select(AnnotationLabel)
        .where(AnnotationLabel.tenant_id == tenant_id)
        .order_by(AnnotationLabel.sort_order, AnnotationLabel.name)
    )
    return list(result.scalars().all())


async def get_label(
    db: AsyncSession, label_id: uuid.UUID, tenant_id: str = "default"
) -> Optional[AnnotationLabel]:
    result = await db.execute(
        select(AnnotationLabel).where(
            AnnotationLabel.tenant_id == tenant_id,
            AnnotationLabel.id == label_id,
        )
    )
    return result.scalar_one_or_none()


async def update_label(
    db: AsyncSession, label_id: uuid.UUID, tenant_id: str = "default", **kwargs
) -> Optional[AnnotationLabel]:
    label = await get_label(db, label_id, tenant_id=tenant_id)
    if not label:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(label, key):
            setattr(label, key, value)
    await db.flush()
    await db.refresh(label)
    return label


async def delete_label(db: AsyncSession, label_id: uuid.UUID, tenant_id: str = "default") -> bool:
    result = await db.execute(
        delete(AnnotationLabel).where(
            AnnotationLabel.tenant_id == tenant_id,
            AnnotationLabel.id == label_id,
        )
    )
    return result.rowcount > 0
