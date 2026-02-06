"""
Detection Schemas - Request/Response for auto-detection pipeline

Parameters and results for the heatmap-to-regions detection pipeline.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .geojson import GeoJSONFeatureCollection


class DetectionRequest(BaseModel):
    """Parameters for auto-detection."""

    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence threshold")
    min_area: float = Field(default=100.0, ge=0.0, description="Minimum region area in pixels^2")
    merge_distance: float = Field(
        default=0.0, ge=0.0, description="Distance to merge nearby regions"
    )
    resolution_level: int = Field(default=2, ge=0, le=5, description="Heatmap resolution level")
    simplify_tolerance: float = Field(
        default=2.0, ge=0.0, description="Douglas-Peucker simplification tolerance"
    )
    prediction_class: str = Field(default="tissue", description="Target class for heatmap")


class DetectionRegion(BaseModel):
    """A single detected region with metadata."""

    confidence: float = Field(..., ge=0.0, le=1.0)
    area_px: float
    centroid: List[float] = Field(..., min_length=2, max_length=2)
    bbox: List[float] = Field(..., min_length=4, max_length=4)


class DetectionResponse(BaseModel):
    """Detection pipeline result."""

    slide_id: str
    geojson: GeoJSONFeatureCollection
    num_regions: int
    parameters: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
