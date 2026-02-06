"""
Annotation Schemas - Pydantic models for annotation API

Request/Response models for the annotation CRUD endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .geojson import GeoJSONGeometry

# ============================================
# Label Schemas
# ============================================


class LabelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#FF0000", pattern=r"^#[0-9A-Fa-f]{6}$")
    category: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = Field(default=0, ge=0)


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    category: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)


class LabelResponse(BaseModel):
    id: UUID
    name: str
    color: str
    category: Optional[str]
    description: Optional[str]
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
    label_id: Optional[UUID] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    properties: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class AnnotationUpdate(BaseModel):
    geometry: Optional[GeoJSONGeometry] = None
    geometry_type: Optional[str] = None
    annotation_type: Optional[str] = None
    label_id: Optional[UUID] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    properties: Optional[Dict[str, Any]] = None


class AnnotationResponse(BaseModel):
    id: UUID
    slide_id: str
    geometry: GeoJSONGeometry
    geometry_type: str
    annotation_type: str
    label_id: Optional[UUID]
    label: Optional[LabelResponse] = None
    confidence: Optional[float]
    properties: Optional[Dict[str, Any]]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnotationBatchCreate(BaseModel):
    annotations: List[AnnotationCreate] = Field(..., min_length=1, max_length=10000)
