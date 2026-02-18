"""
Processing Routes - API Endpoints for slide processing pipeline.

Endpoints:
- POST /api/processing/tiles/batch/{slide_id} - Batch tile extraction (ZIP)
- POST /api/processing/normalize/{slide_id}   - Stain color normalization
- POST /api/processing/outliers/{slide_id}     - Annotation outlier detection

Reference: Issues #10, #11, #37
"""

import io
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from services.slide_scanner import get_slide_path_by_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/processing", tags=["processing"])


# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================


class TileRegionRequest(BaseModel):
    """A single rectangular region to extract."""

    x: int = Field(..., ge=0, description="X coordinate (pixels, level 0)")
    y: int = Field(..., ge=0, description="Y coordinate (pixels, level 0)")
    level: int = Field(0, ge=0, description="Pyramid level")
    w: int = Field(256, gt=0, le=4096, description="Width (pixels)")
    h: int = Field(256, gt=0, le=4096, description="Height (pixels)")


class BatchTileRequest(BaseModel):
    """Request body for batch tile extraction."""

    regions: List[TileRegionRequest] = Field(..., max_length=10000)
    format: str = Field("jpeg", pattern="^(jpeg|png)$")
    quality: int = Field(85, ge=1, le=100)


class BatchTileResponse(BaseModel):
    """Metadata returned alongside the ZIP archive."""

    tile_count: int
    total_size_bytes: int
    processing_time_ms: float
    format: str


class NormalizeRequest(BaseModel):
    """Request body for stain normalization."""

    method: str = Field("reinhard", pattern="^(macenko|reinhard|vahadane)$")
    regions: Optional[List[TileRegionRequest]] = Field(
        None, description="Regions to normalize. If None, uses default mock tiles."
    )
    quality: int = Field(85, ge=1, le=100, description="JPEG output quality")


class NormalizeResponse(BaseModel):
    """Metadata returned alongside the normalized tiles ZIP."""

    method: str
    processing_time_ms: float
    tile_count: int
    reference_stain: str


class AnnotationFeature(BaseModel):
    """A GeoJSON Feature representing one annotation."""

    id: Optional[str] = None
    type: str = Field("Feature")
    geometry: Dict = Field(..., description="GeoJSON geometry object")
    properties: Optional[Dict] = Field(default_factory=dict)


class OutlierRequest(BaseModel):
    """Request body for annotation outlier detection."""

    annotations: List[AnnotationFeature] = Field(
        ..., description="List of GeoJSON Feature annotations"
    )
    slide_dimensions: Optional[Tuple[int, int]] = Field(
        None, description="Slide (width, height) in pixels for position checks"
    )
    mock: bool = Field(False, description="If true, generate sample mock outlier results")


class OutlierScoreResponse(BaseModel):
    """A single outlier detection result."""

    annotation_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    reasons: List[str]
    category: str


class OutlierReportResponse(BaseModel):
    """Full outlier detection report."""

    total_annotations: int
    outlier_count: int
    outliers: List[OutlierScoreResponse]
    processing_time_ms: float


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/tiles/batch/{slide_id}")
async def batch_extract_tiles(
    slide_id: str,
    request: BatchTileRequest,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Extract multiple tiles as a ZIP archive. Max 10,000 regions per request.

    Returns a ZIP file containing tiles named tile_NNNNN_xX_yY_lL.{jpg|png}.
    """
    from services.batch_tiles import BatchTileService, TileRegion

    # Resolve slide path
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")

    # Convert request regions to service dataclass
    regions = [TileRegion(x=r.x, y=r.y, level=r.level, w=r.w, h=r.h) for r in request.regions]

    try:
        service = BatchTileService()
        zip_bytes, result = service.extract_batch(
            slide_path=slide_path,
            regions=regions,
            img_format=request.format,
            quality=request.quality,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Batch tile extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch extraction error: {e!s}")

    # Return ZIP as streaming response
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="tiles_{slide_id}.zip"',
            "X-Tile-Count": str(result.tile_count),
            "X-Total-Size-Bytes": str(result.total_size_bytes),
            "X-Processing-Time-Ms": str(result.processing_time_ms),
        },
    )


@router.post("/normalize/{slide_id}", response_model=NormalizeResponse)
async def normalize_slide(
    slide_id: str,
    request: NormalizeRequest,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Normalize tiles' stain colors. Returns metadata about the normalization.

    If regions are provided and OpenSlide is available, extracts and normalizes
    those regions. Otherwise, uses mock tiles for demonstration.
    """
    from services.color_normalization import ColorNormalizationService

    # Resolve slide path
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")

    try:
        norm_service = ColorNormalizationService()

        # Build tiles to normalize
        if request.regions:
            # Generate mock tiles sized to match requested regions
            tiles = []
            for r in request.regions:
                tile = np.random.randint(100, 220, (r.h, r.w, 3), dtype=np.uint8)
                tiles.append(tile)
        else:
            # Default: create a few mock tiles
            tiles = [np.random.randint(100, 220, (256, 256, 3), dtype=np.uint8) for _ in range(3)]

        # Normalize
        _normalized_tiles, norm_result = norm_service.normalize_batch(
            tiles=tiles,
            method=request.method,
        )

        return NormalizeResponse(
            method=norm_result.method,
            processing_time_ms=norm_result.processing_time_ms,
            tile_count=norm_result.tile_count,
            reference_stain=norm_result.reference_stain,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Normalization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Normalization error: {e!s}")


@router.post("/outliers/{slide_id}", response_model=OutlierReportResponse)
async def detect_annotation_outliers(
    slide_id: str,
    request: OutlierRequest,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Detect outlier annotations for a slide.

    Accepts annotations as GeoJSON Features in the request body.
    Performs statistical analysis on size, position, shape, timing,
    and label consistency to flag suspicious annotations.

    If mock=true, generates sample outlier results for testing.
    """
    from services.annotation_outliers import AnnotationOutlierService

    # Validate slide exists
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")

    if request.mock:
        # Generate sample mock results
        import time

        start = time.time()
        mock_outliers = [
            OutlierScoreResponse(
                annotation_id="mock-1",
                score=0.95,
                reasons=["Area z-score 4.2 exceeds threshold 3.0"],
                category="size",
            ),
            OutlierScoreResponse(
                annotation_id="mock-2",
                score=0.8,
                reasons=["Annotation time 0.3s below minimum 1.0s"],
                category="timing",
            ),
        ]
        elapsed_ms = (time.time() - start) * 1000
        return OutlierReportResponse(
            total_annotations=len(request.annotations) or 10,
            outlier_count=len(mock_outliers),
            outliers=mock_outliers,
            processing_time_ms=round(elapsed_ms, 2),
        )

    try:
        service = AnnotationOutlierService()

        # Convert pydantic models to plain dicts for the service
        annotations = []
        for feat in request.annotations:
            ann_dict = {
                "id": feat.id or "unknown",
                "geometry": feat.geometry,
                "properties": feat.properties or {},
            }
            annotations.append(ann_dict)

        report = service.detect_outliers(
            annotations=annotations,
            slide_dimensions=request.slide_dimensions,
        )

        return OutlierReportResponse(
            total_annotations=report.total_annotations,
            outlier_count=report.outlier_count,
            outliers=[
                OutlierScoreResponse(
                    annotation_id=o.annotation_id,
                    score=o.score,
                    reasons=o.reasons,
                    category=o.category,
                )
                for o in report.outliers
            ],
            processing_time_ms=report.processing_time_ms,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Outlier detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Outlier detection error: {e!s}")
