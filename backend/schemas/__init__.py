"""Pydantic Schemas for VarunaPoC."""

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
from .error import ErrorCodes, ErrorResponse
from .geojson import GeoJSONFeature, GeoJSONFeatureCollection
from .pagination import PaginatedResponse, PaginationParams

__all__ = [
    "AnnotationBatchCreate",
    "AnnotationCreate",
    "AnnotationResponse",
    "AnnotationUpdate",
    "DetectionRequest",
    "DetectionResponse",
    "ErrorCodes",
    "ErrorResponse",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "LabelCreate",
    "LabelResponse",
    "LabelUpdate",
    "PaginatedResponse",
    "PaginationParams",
]
