"""Pydantic Schemas for VarunaPoC Phase 2."""

from .annotation import (
    AnnotationBatchCreate,
    AnnotationCreate,
    AnnotationResponse,
    AnnotationUpdate,
    LabelCreate,
    LabelResponse,
    LabelUpdate,
)
from .detection import DetectionRequest, DetectionResponse
from .geojson import GeoJSONFeature, GeoJSONFeatureCollection

__all__ = [
    "AnnotationBatchCreate",
    "AnnotationCreate",
    "AnnotationResponse",
    "AnnotationUpdate",
    "DetectionRequest",
    "DetectionResponse",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "LabelCreate",
    "LabelResponse",
    "LabelUpdate",
]
