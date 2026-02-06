"""
Annotation Schemas - Pydantic models for annotation API

Request/Response models for the annotation CRUD endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field

from .geojson import GeoJSONGeometry

# ============================================
# Label Schemas
# ============================================


class LabelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#FF0000", pattern=r"^#[0-9A-Fa-f]{6}$")
    category: str | None = None
    description: str | None = None
    sort_order: int = Field(default=0, ge=0)


class LabelUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    category: str | None = None
    description: str | None = None
    sort_order: int | None = Field(None, ge=0)


class LabelResponse(BaseModel):
    id: UUID
    name: str
    color: str
    category: str | None
    description: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# Annotation Schemas
# ============================================


class AnnotationCreate(BaseModel):
    geometry: GeoJSONGeometry
    geometry_type: str = Field(..., description="polygon, rectangle, point, circle, freehand")
    annotation_type: str = Field(default="manual", description="manual, auto, auto_confirmed")
    label_id: UUID | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    properties: Dict[str, Any] | None = None
    created_by: str | None = None


class AnnotationUpdate(BaseModel):
    geometry: GeoJSONGeometry | None = None
    geometry_type: str | None = None
    annotation_type: str | None = None
    label_id: UUID | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    properties: Dict[str, Any] | None = None


class AnnotationResponse(BaseModel):
    id: UUID
    slide_id: str
    geometry: GeoJSONGeometry
    geometry_type: str
    annotation_type: str
    label_id: UUID | None
    label: LabelResponse | None = None
    confidence: float | None
    properties: Dict[str, Any] | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnotationBatchCreate(BaseModel):
    annotations: List[AnnotationCreate] = Field(..., min_length=1, max_length=10000)
