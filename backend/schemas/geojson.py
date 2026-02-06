"""
GeoJSON Schemas

Standard GeoJSON types for annotation geometry exchange.
Coordinates are in slide pixel space (not geographic).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GeoJSONGeometry(BaseModel):
    """GeoJSON Geometry object."""

    type: str = Field(
        ...,
        description="Geometry type: Point, Polygon, MultiPolygon, LineString",
    )
    coordinates: Any = Field(..., description="Coordinate array per GeoJSON spec")


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature with annotation properties."""

    type: str = Field(default="Feature")
    geometry: GeoJSONGeometry
    properties: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection for batch annotation exchange."""

    type: str = Field(default="FeatureCollection")
    features: List[GeoJSONFeature] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
