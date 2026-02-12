"""
Quality Metrics Schemas - Pydantic models for request/response.

Defines the API contract for all quality metric endpoints.
"""

from typing import Dict, List

from pydantic import BaseModel, Field

# ==========================================
# REQUEST MODELS
# ==========================================


class PairwiseRequest(BaseModel):
    """Request for pairwise (2-annotator) comparison."""

    annotator_a: str = Field(..., description="Username or sub of annotator A")
    annotator_b: str = Field(..., description="Username or sub of annotator B")
    iou_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="IoU threshold for matching annotations",
    )
    matching_strategy: str = Field(
        default="iou",
        description="Matching strategy: 'iou' (spatial) or 'grid'",
    )
    grid_cell_size: int = Field(
        default=256,
        ge=32,
        le=2048,
        description="Grid cell size in pixels (for grid strategy)",
    )
    point_buffer_radius: float = Field(
        default=50.0,
        ge=1.0,
        description="Buffer radius in pixels for point annotations",
    )


class MultiRaterRequest(BaseModel):
    """Request for multi-rater (N annotators) comparison."""

    annotators: List[str] = Field(..., min_length=2, description="List of annotator usernames/subs")
    grid_cell_size: int = Field(
        default=256,
        ge=32,
        le=2048,
        description="Grid cell size in pixels",
    )
    point_buffer_radius: float = Field(
        default=50.0,
        ge=1.0,
        description="Buffer radius for point annotations",
    )


# ==========================================
# RESPONSE MODELS
# ==========================================


class AnnotatorInfo(BaseModel):
    """Information about an annotator on a slide."""

    username: str
    annotation_count: int
    labels_used: List[str]


class KappaResult(BaseModel):
    """Result of Cohen's kappa computation."""

    kappa: float = Field(..., description="Cohen's kappa coefficient [-1, 1]")
    interpretation: str = Field(..., description="Landis-Koch interpretation (e.g. 'Substantial')")
    annotator_a: str
    annotator_b: str
    n_matched: int = Field(..., description="Number of matched annotation pairs")
    n_unmatched_a: int = Field(..., description="Annotations from A without match in B")
    n_unmatched_b: int = Field(..., description="Annotations from B without match in A")
    matching_strategy: str


class FleissKappaResult(BaseModel):
    """Result of Fleiss' kappa computation."""

    kappa: float = Field(..., description="Fleiss' kappa coefficient [-1, 1]")
    interpretation: str
    annotators: List[str]
    n_cells: int = Field(..., description="Number of grid cells evaluated")
    n_categories: int = Field(..., description="Number of label categories")
    categories: List[str]


class ConfusionMatrixResult(BaseModel):
    """Confusion matrix between two annotators."""

    matrix: List[List[int]]
    categories: List[str] = Field(..., description="Label names in row/column order")
    annotator_a: str
    annotator_b: str
    n_matched: int


class LabelMetrics(BaseModel):
    """Per-label precision, recall, F1."""

    label: str
    precision: float
    recall: float
    f1: float
    support: int


class PerLabelMetricsResult(BaseModel):
    """F1/Precision/Recall per label."""

    metrics: List[LabelMetrics]
    annotator_a: str = Field(..., description="Ground truth annotator")
    annotator_b: str = Field(..., description="Predicted annotator")
    n_matched: int


class HistogramBin(BaseModel):
    """Single histogram bin."""

    bin_start: float
    bin_end: float
    count: int


class IoUDistributionResult(BaseModel):
    """IoU distribution statistics."""

    count: int
    mean: float
    median: float
    std: float
    min: float
    max: float
    histogram: List[HistogramBin]
    annotator_a: str
    annotator_b: str


class DisagreementFeature(BaseModel):
    """A single disagreement region as GeoJSON feature."""

    type: str = "Feature"
    geometry: Dict
    properties: Dict


class DisagreementHeatmapResult(BaseModel):
    """Disagreement regions as GeoJSON FeatureCollection."""

    type: str = "FeatureCollection"
    features: List[DisagreementFeature]
    annotator_a: str
    annotator_b: str
    n_disagreements: int
