"""
ML Routes - API Endpoints for Machine Learning

Endpoints:
- POST /ml/predict/{slide_id} - Prédiction sur slide
- POST /ml/features/{slide_id} - Extraction features
- GET  /ml/heatmap/{slide_id} - Génération heatmap
- GET  /ml/focus/{slide_id} - Focus assist zones
- POST /ml/batch/predict - Batch inference
- GET  /ml/models - Liste modèles disponibles
- POST /ml/models/reload - Reload model configuration

References:
- FastAPI: https://fastapi.tiangolo.com/
- REST API Design: https://restfulapi.net/
"""

import base64
import logging
import os
from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from core.exceptions import MLProviderError
from core.interfaces import get_provider
from rate_limiting import limit, ml_rate
from services.ml import TagExtractor, TagRouter
from services.ml.worker import (
    MLWorkerBusyError,
    MLWorkerDownError,
    MLWorkerExecutionError,
    MLWorkerProxy,
    MLWorkerTimeoutError,
)
from services.slide_scanner import get_slide_path_by_id

# ---------------------------------------------------------------------------
# ML Worker: isolated process for heavy inference
# ---------------------------------------------------------------------------
_ml_worker: Optional[MLWorkerProxy] = None


def get_ml_worker() -> MLWorkerProxy:
    """Get or create the ML worker singleton."""
    global _ml_worker
    if _ml_worker is None:
        _ml_worker = MLWorkerProxy()
        _ml_worker.start()
    elif not _ml_worker.is_alive():
        _ml_worker.restart()
    return _ml_worker


# ---------------------------------------------------------------------------
# Error translation: technical errors -> readable French messages
# ---------------------------------------------------------------------------
ML_ERROR_MESSAGES = {
    "microns-per-pixel": "Cette lame n'a pas de metadonnees de resolution (MPP).",
    "missing_mpp": "Cette lame n'a pas de metadonnees de resolution (MPP).",
    "busy": "Le moteur d'inference est occupe. Reessayez dans quelques secondes.",
    "out of memory": "Memoire insuffisante pour analyser cette lame.",
    "oom": "Memoire insuffisante pour analyser cette lame.",
    "timeout": "L'analyse a pris trop de temps (>2 min).",
    "model not loaded": "Le modele IA n'est pas charge. Contactez l'administrateur.",
    "no model loaded": "Aucun modele IA n'est charge.",
    "not supported for ml": "Ce format de lame n'est pas supporte pour l'analyse IA.",
    "provider unavailable": "Le moteur d'analyse IA n'est pas disponible.",
}


def _translate_ml_error(error: Exception) -> HTTPException:
    """Translate an ML error into an HTTPException with a readable French message."""
    if isinstance(error, MLWorkerBusyError):
        return HTTPException(status_code=429, detail=str(error))

    if isinstance(error, MLWorkerTimeoutError):
        return HTTPException(status_code=504, detail=str(error))

    if isinstance(error, MLWorkerDownError):
        return HTTPException(
            status_code=503,
            detail="Le service d'analyse IA n'est pas disponible actuellement.",
        )

    # Check known patterns in the error message
    error_str = str(error).lower()
    for pattern, message in ML_ERROR_MESSAGES.items():
        if pattern in error_str:
            return HTTPException(status_code=500, detail=message)

    # Default: generic error
    return HTTPException(status_code=500, detail=str(error))


# Formats not supported by Slideflow/OpenSlide for ML analysis
# Note: DICOM (.dcm) supported since OpenSlide 4.0 (openslide-bin wheel)
_UNSUPPORTED_ML_FORMATS: set[str] = set()


def _check_slide_format(slide_path: str, slide_id: str):
    """Raise 400 if slide format is not supported for ML analysis."""
    from pathlib import Path

    ext = Path(slide_path).suffix.lower()
    if ext in _UNSUPPORTED_ML_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Slide format '{ext}' is not supported for ML analysis. "
            f"Supported formats: SVS, MRXS, NDPI, BIF, TIFF, SCN, DCM.",
        )


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


# ============================================================================
# CANCEL ENDPOINT
# ============================================================================


@router.post("/cancel", summary="Cancel the current ML job")
async def cancel_ml_job(
    _user: CurrentUser = Depends(get_current_user),
):
    """Cancel the running ML job by restarting the worker process."""
    worker = get_ml_worker()
    cancelled = worker.cancel_current()
    return {"status": "cancelled" if cancelled else "idle"}


# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================


class RegionRequest(BaseModel):
    """Région pour prédiction régionale."""

    x: int = Field(..., ge=0, description="X coordinate (pixels)")
    y: int = Field(..., ge=0, description="Y coordinate (pixels)")
    width: int = Field(..., gt=0, description="Width (pixels)")
    height: int = Field(..., gt=0, description="Height (pixels)")


class PredictionRequest(BaseModel):
    """Request pour prédiction."""

    region: Optional[RegionRequest] = Field(None, description="Region optionnelle")
    model_id: Optional[str] = Field(None, description="Force specific model")
    num_mc_samples: int = Field(10, ge=1, le=50, description="Monte Carlo samples for uncertainty")


class PredictionResponse(BaseModel):
    """Response pour prédiction."""

    slide_id: str
    prediction_class: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    uncertainty: Optional[float] = Field(None, ge=0.0, le=1.0)
    probabilities: Dict[str, float]
    execution_time_ms: float
    model_id: str
    model_name: Optional[str] = None
    tags: Optional[Dict] = None


class FeatureExtractionRequest(BaseModel):
    """Request pour extraction features."""

    tile_size: int = Field(224, ge=64, le=512, description="Tile size (pixels)")
    overlap: int = Field(0, ge=0, le=128, description="Tile overlap (pixels)")
    model_id: Optional[str] = None


class FeatureExtractionResponse(BaseModel):
    """Response pour extraction features."""

    slide_id: str
    num_patches: int
    embedding_dim: int
    embeddings_shape: List[int]
    model_id: str
    storage_path: Optional[str] = None  # S3/local path si stocké


class BatchPredictionRequest(BaseModel):
    """Request pour batch inference."""

    slide_ids: List[str] = Field(..., min_items=1, max_items=1000)
    model_id: Optional[str] = None


class BatchJobResponse(BaseModel):
    """Response pour batch job."""

    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    total_slides: int
    processed_slides: int = 0
    failed_slides: int = 0
    created_at: str
    estimated_time_minutes: Optional[int] = None


class ModelInfoResponse(BaseModel):
    """Response pour model info."""

    model_id: str
    model_name: str
    version: str
    task_type: str
    classes: List[str]
    device: str
    reference_metrics: Dict
    provider: str


class TagsResponse(BaseModel):
    """Response pour auto-tag endpoint."""

    slide_id: str
    tags: Dict[str, Optional[str]]
    source: str


class FocusZone(BaseModel):
    """A single zone of interest."""

    rank: int
    score: float = Field(..., ge=0.0, le=1.0)
    centroid: List[float]
    bbox: List[float]
    area_px: float


class FocusResponse(BaseModel):
    """Response for focus assist endpoint."""

    slide_id: str
    zones: List[FocusZone]
    model_id: str
    total_zones_above_threshold: int


class RegionMeasurement(BaseModel):
    region_id: int
    label: str
    feret_diameter_mm: float
    area_mm2: float
    perimeter_mm: float
    bbox_mm: List[float]
    confidence: float


class MeasurementResponse(BaseModel):
    slide_id: str
    measurements: List[RegionMeasurement]
    mpp: float
    unit: str = "mm"


class FeedbackRequest(BaseModel):
    """Pathologist feedback on an ML prediction."""

    original_annotation_id: str = Field(..., description="UUID of the original annotation")
    correction_type: str = Field(..., pattern="^(confirmed|rejected|refined|relabeled)$")
    corrected_class: Optional[str] = None
    corrected_geometry: Optional[Dict] = None
    notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    correction_id: str
    slide_id: str
    correction_type: str
    stats: Dict[str, int]


class SimilarSlideResult(BaseModel):
    """A single similar slide result."""

    slide_id: str
    score: float = Field(..., ge=0, le=1)
    name: Optional[str] = None
    overview_url: Optional[str] = None


class SimilarityResponse(BaseModel):
    """Response for similarity search endpoint."""

    query_slide_id: str
    results: List[SimilarSlideResult]
    index_size: int


class GeoJSONRegion(BaseModel):
    """GeoJSON polygon region for cell counting."""

    type: str = Field("Polygon")
    coordinates: List[List[List[float]]]


class CountRequest(BaseModel):
    """Request for cell counting endpoint."""

    region: Optional[GeoJSONRegion] = None
    stain: str = Field("Ki67")


class CountingResponse(BaseModel):
    """Response for cell counting endpoint."""

    total_cells: int
    positive: int
    negative: int
    ratio: float
    percentage: str
    processing_time_ms: float
    cells: Optional[List[Dict[str, Any]]] = None


class ClusterInfoModel(BaseModel):
    id: int
    color: str
    label: str
    tile_count: int
    centroid_embedding: List[float] = []


class TileAssignmentModel(BaseModel):
    x: int
    y: int
    cluster_id: int


class ClusteringResponse(BaseModel):
    clusters: List[ClusterInfoModel]
    tile_assignments: List[TileAssignmentModel]
    processing_time_ms: float


class ArtifactModel(BaseModel):
    type: str
    severity: str
    bbox: List[int]
    area_percent: float


class QualityResponse(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=1.0)
    quality_label: str
    artifacts: List[ArtifactModel]
    recommendation: str
    processing_time_ms: float


class DriftMetricModel(BaseModel):
    metric_name: str
    value: float
    threshold: float
    is_drifted: bool
    window_size: int


class DriftReportResponse(BaseModel):
    model_id: str
    report_date: str
    metrics: List[DriftMetricModel]
    overall_drifted: bool
    recommendation: str
    processing_time_ms: float


class AllDriftReportsResponse(BaseModel):
    reports: List[DriftReportResponse]


class RetrainingRequest(BaseModel):
    """Request pour retraining pipeline."""

    dataset_tag: str = Field("latest")
    config: Optional[Dict[str, Any]] = None


class RetrainingResponse(BaseModel):
    """Response pour retraining pipeline."""

    run_id: str
    status: str
    model_name: str
    dataset_version: str
    metrics: Dict[str, float]
    processing_time_ms: float
    artifact_uri: Optional[str] = None
    recommendation: str


# ============================================================================
# DEPENDENCIES
# ============================================================================


# Singleton cache: avoid reloading heavy ML models on every request
def get_ml_provider():
    """Dependency: lazily-initialized ML provider singleton.

    Delegates to core.container.ServiceContainer for centralized lifecycle.

    Configuration via environment variables:
        ML_ENABLED, ML_PROVIDER, ML_MODE, ML_EXTRACTOR, ML_MODEL_PATH, ML_CLASSES

    Raises:
        HTTPException 503: If ML features are disabled or provider unavailable.
    """
    from core.container import ServiceContainer

    return ServiceContainer.get_ml_provider()


def get_tag_extractor():
    """Dependency pour TagExtractor."""
    return TagExtractor()


def get_tag_router():
    """Dependency pour TagRouter."""
    import os

    config_path = os.getenv("ML_ROUTES_CONFIG", "config/ml_routes.yaml")
    return TagRouter(config_path)


def get_memory_cache():
    """Dependency: in-memory prediction cache singleton."""
    from core.container import ServiceContainer

    return ServiceContainer.get_memory_cache()


def get_disk_cache():
    """Dependency: disk-based prediction cache singleton."""
    from core.container import ServiceContainer

    return ServiceContainer.get_disk_cache()


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/predict/{slide_id}", response_model=PredictionResponse)
@limit(ml_rate)
async def predict_slide(
    request: Request,
    slide_id: str,
    body: PredictionRequest = PredictionRequest(),
    tag_extractor=Depends(get_tag_extractor),
    tag_router=Depends(get_tag_router),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Prédiction ML sur slide complète ou région.

    Process:
    1. Récupérer slide depuis DB/storage
    2. Extraire tags (organ, stain) via TagExtractor
    3. Router vers modèle approprié via TagRouter
    4. Inference via ML Worker (process isolé)
    5. Retourner résultat

    Args:
        slide_id: Identifiant lame
        request: Paramètres prédiction (région, model_id, etc.)

    Returns:
        PredictionResponse avec classe, confiance, incertitude

    Errors:
        404: Slide introuvable
        429: Worker occupe
        504: Timeout
        500: Erreur ML

    Examples:
        ```bash
        # Prédiction slide complète
        curl -X POST "http://localhost:8000/api/ml/predict/slide_abc123"

        # Prédiction sur région
        curl -X POST "http://localhost:8000/api/ml/predict/slide_abc123" \\
          -H "Content-Type: application/json" \\
          -d '{"region": {"x": 1000, "y": 1000, "width": 2000, "height": 2000}}'
        ```
    """
    try:
        # Get slide path from scanner
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        worker = get_ml_worker()
        region_tuple = (
            (body.region.x, body.region.y, body.region.width, body.region.height)
            if body.region
            else None
        )

        result = await worker.submit("predict", slide_path, region=region_tuple)

        # Model name from env config (model itself is in worker process)
        model_name = os.getenv("ML_EXTRACTOR", "feature_extractor")
        tags = result.metadata

        return PredictionResponse(
            slide_id=slide_id,
            prediction_class=result.prediction_class,
            confidence=result.confidence,
            uncertainty=result.uncertainty,
            probabilities=result.probabilities,
            execution_time_ms=result.execution_time_ms,
            model_id=result.model_id,
            model_name=model_name,
            tags=tags,
        )

    except HTTPException:
        raise
    except (MLWorkerBusyError, MLWorkerTimeoutError, MLWorkerDownError) as e:
        logger.warning(f"ML worker error: {e}")
        raise _translate_ml_error(e)
    except MLWorkerExecutionError as e:
        logger.error(f"ML prediction failed in worker: {e}")
        raise _translate_ml_error(e)
    except MLProviderError as e:
        logger.error(f"ML prediction failed: {e}")
        raise _translate_ml_error(e)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise _translate_ml_error(e)


@router.post("/features/{slide_id}", response_model=FeatureExtractionResponse)
@limit(ml_rate)
async def extract_features(
    request: Request,
    slide_id: str,
    body: FeatureExtractionRequest = FeatureExtractionRequest(),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Extraction de features (embeddings) pour MIL.

    Use cases:
    - Pre-compute embeddings pour active learning
    - Similarity search entre slides
    - Dataset clustering

    Args:
        slide_id: Identifiant lame
        request: Paramètres extraction (tile_size, overlap, etc.)

    Returns:
        FeatureExtractionResponse avec metadata features

    Examples:
        ```bash
        curl -X POST "http://localhost:8000/api/ml/features/slide_abc123" \\
          -H "Content-Type: application/json" \\
          -d '{"tile_size": 224, "overlap": 0}'
        ```
    """
    try:
        # Get slide path from scanner
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        # Extract features via ML worker (heavy — isolated process)
        worker = get_ml_worker()
        result = await worker.submit("extract_features", slide_path, body.tile_size, body.overlap)

        return FeatureExtractionResponse(
            slide_id=slide_id,
            num_patches=result.num_patches,
            embedding_dim=result.embedding_dim,
            embeddings_shape=list(result.embeddings.shape),
            model_id=result.model_id,
            storage_path=None,
        )

    except HTTPException:
        raise
    except (MLWorkerBusyError, MLWorkerTimeoutError, MLWorkerDownError) as e:
        logger.warning(f"ML worker error: {e}")
        raise _translate_ml_error(e)
    except (MLWorkerExecutionError, MLProviderError) as e:
        logger.error(f"Feature extraction failed: {e}")
        raise _translate_ml_error(e)


@router.get("/heatmap/{slide_id}")
@limit(ml_rate)
async def get_heatmap(
    request: Request,
    slide_id: str,
    prediction_class: str = Query(..., description="Target class for heatmap"),
    resolution_level: int = Query(2, ge=0, le=5, description="Resolution level (0=max)"),
    colormap: str = Query("jet", description="Matplotlib colormap (jet, hot, viridis, etc.)"),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Génère heatmap d'explainability (Grad-CAM ou feature attention).

    Returns JSON avec heatmap base64 et slide_dimensions pour overlay
    sur le viewer OpenSeadragon.

    Args:
        slide_id: Identifiant lame
        prediction_class: Classe pour laquelle générer heatmap
        resolution_level: Niveau résolution (0=max, 2=quart)
        colormap: Colormap matplotlib

    Returns:
        JSON avec heatmap_base64, slide_dimensions, metadata

    Examples:
        ```bash
        curl "http://localhost:8000/api/ml/heatmap/slide_abc123?prediction_class=tissue"
        ```
    """
    try:
        # Get slide path from scanner
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        # Generate heatmap via ML worker (heavy — isolated process)
        worker = get_ml_worker()
        result = await worker.submit(
            "generate_heatmap", slide_path, prediction_class, resolution_level
        )

        # Convert to RGB PNG
        rgb_heatmap = result.to_rgb(colormap=colormap)

        from PIL import Image

        img = Image.fromarray(rgb_heatmap)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Encode to base64 for frontend HeatmapOverlay
        heatmap_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "heatmap_base64": heatmap_b64,
            "slide_dimensions": list(result.slide_dimensions),
            "slide_id": slide_id,
            "prediction_class": prediction_class,
            "resolution_level": resolution_level,
            "method": result.method,
            "metadata": result.metadata,
        }

    except HTTPException:
        raise
    except (MLWorkerBusyError, MLWorkerTimeoutError, MLWorkerDownError) as e:
        logger.warning(f"ML worker error: {e}")
        raise _translate_ml_error(e)
    except (MLWorkerExecutionError, MLProviderError) as e:
        logger.error(f"Heatmap generation failed: {e}")
        raise _translate_ml_error(e)
    except Exception as e:
        logger.error(f"Unexpected heatmap error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Heatmap generation failed unexpectedly")


@router.post("/detect/{slide_id}")
@limit(ml_rate)
async def detect_regions_endpoint(
    request: Request,
    slide_id: str,
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Confidence threshold"),
    min_area: float = Query(100.0, ge=0.0, description="Minimum region area (px^2)"),
    simplify_tolerance: float = Query(2.0, ge=0.0, description="Douglas-Peucker tolerance"),
    resolution_level: int = Query(2, ge=0, le=5, description="Heatmap resolution level"),
    prediction_class: str = Query("tissue", description="Target class for heatmap"),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Auto-detection: generate heatmap then extract regions as GeoJSON.

    Pipeline:
    1. Generate heatmap via ML provider
    2. Threshold + morphological cleaning
    3. Extract contours, simplify, scale to slide coords
    4. Return GeoJSON FeatureCollection with confidence per region

    Used by frontend DetectionPanel for accept/reject workflow.
    """
    from schemas.detection import DetectionResponse
    from services.detection.pipeline import detect_regions as run_pipeline

    try:
        # Get slide path
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        # Generate heatmap via ML worker (heavy — isolated process)
        worker = get_ml_worker()
        heatmap_result = await worker.submit(
            "generate_heatmap",
            slide_path,
            prediction_class,
            resolution_level,
        )

        # Run detection pipeline (lightweight, runs in main process)
        geojson = run_pipeline(
            heatmap=heatmap_result.heatmap,
            slide_dimensions=heatmap_result.slide_dimensions,
            threshold=threshold,
            min_area=min_area,
            simplify_tolerance=simplify_tolerance,
        )

        return DetectionResponse(
            slide_id=slide_id,
            geojson=geojson,
            num_regions=len(geojson.features),
            parameters={
                "threshold": threshold,
                "min_area": min_area,
                "simplify_tolerance": simplify_tolerance,
                "resolution_level": resolution_level,
                "prediction_class": prediction_class,
            },
            metadata={
                "heatmap_shape": list(heatmap_result.heatmap.shape),
                "slide_dimensions": list(heatmap_result.slide_dimensions),
            },
        )

    except HTTPException:
        raise
    except (MLWorkerBusyError, MLWorkerTimeoutError, MLWorkerDownError) as e:
        logger.warning(f"ML worker error: {e}")
        raise _translate_ml_error(e)
    except (MLWorkerExecutionError, MLProviderError) as e:
        logger.error(f"Detection failed: {e}")
        raise _translate_ml_error(e)
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise _translate_ml_error(e)


def _compute_focus_zones(heatmap, slide_dimensions, threshold, top_n):
    """Extract and rank focus zones from a heatmap."""
    import numpy as np

    from services.detection.postprocessing import heatmap_to_contours

    contours_with_confidence = heatmap_to_contours(
        heatmap, threshold=threshold, min_area=50.0, closing_iterations=2
    )

    heatmap_h, heatmap_w = heatmap.shape[:2]
    scale_x = slide_dimensions[0] / heatmap_w
    scale_y = slide_dimensions[1] / heatmap_h

    zones = []
    for contour, confidence in contours_with_confidence:
        scaled = contour.copy().astype(float)
        scaled[:, 0] *= scale_x
        scaled[:, 1] *= scale_y

        xs, ys = scaled[:, 0], scaled[:, 1]
        centroid = [float(np.mean(xs)), float(np.mean(ys))]
        bbox = [float(np.min(xs)), float(np.min(ys)), float(np.max(xs)), float(np.max(ys))]

        n = len(scaled)
        if n >= 3:
            x, y = scaled[:, 0], scaled[:, 1]
            area = (
                abs(float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]) + x[-1] * y[0] - x[0] * y[-1]))
                / 2.0
            )
        else:
            area = 0.0

        zones.append(
            {
                "score": round(confidence, 4),
                "centroid": [round(c, 2) for c in centroid],
                "bbox": [round(v, 2) for v in bbox],
                "area_px": round(area, 2),
            }
        )

    zones.sort(key=lambda z: z["score"], reverse=True)
    total_above = len(zones)
    return zones[:top_n], total_above


@router.get("/focus/{slide_id}", response_model=FocusResponse)
async def get_focus_zones(
    slide_id: str,
    top_n: int = Query(10, ge=1, le=50, description="Number of top zones to return"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum attention score"),
    resolution_level: int = Query(2, ge=0, le=5, description="Heatmap resolution"),
    prediction_class: str = Query("tissue", description="Target class"),
    disk_cache=Depends(get_disk_cache),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Focus Assist — Retourne les N zones les plus intéressantes d'une lame.

    Utilise la heatmap ML pour identifier les régions d'attention élevée,
    les trie par score décroissant et retourne les top N zones avec
    coordonnées, bounding box et score.
    """
    try:
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        # Model ID from env config (model itself is in worker process)
        ml_mode = os.getenv("ML_MODE", "extractor")
        if ml_mode == "classifier":
            model_id = os.getenv("ML_MODEL_ID", "custom_classifier")
        else:
            extractor = os.getenv("ML_EXTRACTOR", "resnet50_imagenet")
            model_id = f"{extractor}_features"
        cached_heatmap = disk_cache.load_heatmap(slide_id, model_id)

        if cached_heatmap is not None:
            heatmap = cached_heatmap
            # We need slide dimensions - get from OpenSlide
            import openslide

            slide = openslide.OpenSlide(slide_path)
            slide_dimensions = slide.dimensions
            slide.close()
        else:
            # Generate heatmap via ML worker (heavy — isolated process)
            worker = get_ml_worker()
            heatmap_result = await worker.submit(
                "generate_heatmap", slide_path, prediction_class, resolution_level
            )
            heatmap = heatmap_result.heatmap
            slide_dimensions = heatmap_result.slide_dimensions
            # Cache for future use
            disk_cache.save_heatmap(slide_id, model_id, heatmap)

        # Find zones above threshold
        zones, total_above = _compute_focus_zones(
            heatmap,
            slide_dimensions,
            threshold,
            top_n,
        )

        focus_zones = [FocusZone(rank=i + 1, **z) for i, z in enumerate(zones)]

        return FocusResponse(
            slide_id=slide_id,
            zones=focus_zones,
            model_id=model_id,
            total_zones_above_threshold=total_above,
        )

    except HTTPException:
        raise
    except (MLWorkerBusyError, MLWorkerTimeoutError, MLWorkerDownError) as e:
        logger.warning(f"ML worker error: {e}")
        raise _translate_ml_error(e)
    except (MLWorkerExecutionError, MLProviderError) as e:
        logger.error(f"Focus assist failed: {e}")
        raise _translate_ml_error(e)
    except Exception as e:
        logger.error(f"Focus assist error: {e}", exc_info=True)
        raise _translate_ml_error(e)


@router.get("/measure/{slide_id}", response_model=MeasurementResponse)
async def measure_slide(
    slide_id: str,
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    prediction_class: str = Query("tissue"),
    resolution_level: int = Query(2, ge=0, le=5),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Auto-measure tumor dimensions in millimeters."""
    try:
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        # Get MPP from slide metadata
        import openslide

        slide = openslide.OpenSlide(slide_path)
        mpp = float(slide.properties.get("openslide.mpp-x", "0.25"))
        slide.close()

        # Generate heatmap via ML worker (heavy — isolated process)
        worker = get_ml_worker()
        heatmap_result = await worker.submit(
            "generate_heatmap", slide_path, prediction_class, resolution_level
        )

        # Extract contours
        from services.detection.postprocessing import heatmap_to_contours

        contours = heatmap_to_contours(heatmap_result.heatmap, threshold=threshold, min_area=100.0)

        # Measure regions
        from services.measurement import measure_regions

        measurements = measure_regions(
            contours,
            heatmap_result.slide_dimensions,
            heatmap_result.heatmap.shape[:2],
            mpp,
        )

        return MeasurementResponse(
            slide_id=slide_id,
            measurements=[RegionMeasurement(**m) for m in measurements],
            mpp=mpp,
        )

    except HTTPException:
        raise
    except (MLWorkerBusyError, MLWorkerTimeoutError, MLWorkerDownError) as e:
        logger.warning(f"ML worker error: {e}")
        raise _translate_ml_error(e)
    except (MLWorkerExecutionError, MLProviderError) as e:
        logger.error(f"Measurement failed: {e}")
        raise _translate_ml_error(e)
    except Exception as e:
        logger.error(f"Measurement error: {e}", exc_info=True)
        raise _translate_ml_error(e)


@router.post("/count/{slide_id}", response_model=CountingResponse)
async def count_cells(
    slide_id: str,
    request: CountRequest = CountRequest(),
    include_positions: bool = Query(False, description="Return cell centroid positions"),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Comptage cellulaire automatisé (Ki-67 / IHC).

    Compte les cellules positives et négatives dans une lame ou région.
    Retourne le ratio et le pourcentage pour l'index Ki-67.

    When include_positions=true, also returns cell centroid coordinates
    in slide pixel space (requires openslide for dimension lookup).

    Used by frontend CellCountingPanel (Wave 4).
    """
    try:
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        slide_dims = None
        if include_positions:
            try:
                import openslide

                with openslide.OpenSlide(str(slide_path)) as osr:
                    slide_dims = osr.dimensions
            except Exception as exc:
                logger.warning("Could not read slide dimensions for cell positions: %s", exc)

        worker = get_ml_worker()
        region_data = request.region.model_dump() if request.region else None
        result = await worker.submit(
            "count_cells",
            slide_path,
            stain=request.stain,
            region=region_data,
            include_positions=include_positions,
            slide_dimensions=slide_dims,
        )

        return CountingResponse(
            total_cells=result.total_cells,
            positive=result.positive,
            negative=result.negative,
            ratio=result.ratio,
            percentage=result.percentage,
            processing_time_ms=result.processing_time_ms,
            cells=result.cells,
        )

    except HTTPException:
        raise
    except MLProviderError as e:
        logger.error(f"Cell counting failed: {e}")
        raise _translate_ml_error(e)
    except Exception as e:
        logger.error(f"Cell counting error: {e}", exc_info=True)
        raise _translate_ml_error(e)


@router.post("/cluster/{slide_id}", response_model=ClusteringResponse)
async def cluster_slide(
    slide_id: str,
    n_clusters: int = Query(4, ge=2, le=8, description="Number of clusters"),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Clustering morphologique -- identifie les patterns dans une lame."""
    try:
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        worker = get_ml_worker()
        result = await worker.submit("cluster", slide_path, n_clusters=n_clusters)

        return ClusteringResponse(
            clusters=[
                ClusterInfoModel(
                    id=c.id,
                    color=c.color,
                    label=c.label,
                    tile_count=c.tile_count,
                    centroid_embedding=c.centroid_embedding,
                )
                for c in result.clusters
            ],
            tile_assignments=[
                TileAssignmentModel(x=t.x, y=t.y, cluster_id=t.cluster_id)
                for t in result.tile_assignments
            ],
            processing_time_ms=result.processing_time_ms,
        )

    except HTTPException:
        raise
    except MLProviderError as e:
        logger.error(f"Clustering failed: {e}")
        raise _translate_ml_error(e)
    except Exception as e:
        logger.error(f"Clustering error: {e}", exc_info=True)
        raise _translate_ml_error(e)


@router.get("/quality/{slide_id}", response_model=QualityResponse)
async def get_slide_quality(
    slide_id: str,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Controle qualite automatique -- evalue la qualite d'une lame.

    Retourne un score global, un label, une liste d'artefacts detectes
    et une recommandation.
    """
    try:
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        worker = get_ml_worker()
        result = await worker.submit("assess_quality", slide_path)

        return QualityResponse(
            overall_score=result.overall_score,
            quality_label=result.quality_label,
            artifacts=[
                ArtifactModel(
                    type=a.type,
                    severity=a.severity,
                    bbox=a.bbox,
                    area_percent=a.area_percent,
                )
                for a in result.artifacts
            ],
            recommendation=result.recommendation,
            processing_time_ms=result.processing_time_ms,
        )

    except HTTPException:
        raise
    except MLProviderError as e:
        logger.error(f"Quality assessment failed: {e}")
        raise _translate_ml_error(e)
    except Exception as e:
        logger.error(f"Quality assessment error: {e}", exc_info=True)
        raise _translate_ml_error(e)


@router.get("/drift/{model_id}", response_model=DriftReportResponse)
async def get_drift_report(
    model_id: str,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """Get drift report for a specific model."""
    from services.ml.drift import DriftDetectorService

    try:
        service = DriftDetectorService()
        result = service.detect_drift(model_id)

        return DriftReportResponse(
            model_id=result.model_id,
            report_date=result.report_date,
            metrics=[
                DriftMetricModel(
                    metric_name=m.metric_name,
                    value=m.value,
                    threshold=m.threshold,
                    is_drifted=m.is_drifted,
                    window_size=m.window_size,
                )
                for m in result.metrics
            ],
            overall_drifted=result.overall_drifted,
            recommendation=result.recommendation,
            processing_time_ms=result.processing_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Drift detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Drift detection error: {e!s}")


@router.get("/drift", response_model=AllDriftReportsResponse)
async def get_all_drift_reports(
    tag_router=Depends(get_tag_router),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """Get drift reports for all loaded models."""
    from services.ml.drift import DriftDetectorService

    try:
        service = DriftDetectorService()
        routes = tag_router.get_all_routes()

        reports = []
        for route in routes:
            result = service.detect_drift(route.model_id)
            reports.append(
                DriftReportResponse(
                    model_id=result.model_id,
                    report_date=result.report_date,
                    metrics=[
                        DriftMetricModel(
                            metric_name=m.metric_name,
                            value=m.value,
                            threshold=m.threshold,
                            is_drifted=m.is_drifted,
                            window_size=m.window_size,
                        )
                        for m in result.metrics
                    ],
                    overall_drifted=result.overall_drifted,
                    recommendation=result.recommendation,
                    processing_time_ms=result.processing_time_ms,
                )
            )

        return AllDriftReportsResponse(reports=reports)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Drift detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Drift detection error: {e!s}")


@router.post("/pipeline/retrain/{model_id}", response_model=RetrainingResponse)
async def retrain_model(
    model_id: str,
    request: RetrainingRequest = RetrainingRequest(),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    Trigger a model retraining pipeline run.

    Pipeline: DVC data versioning -> Slideflow MIL training -> MLflow tracking.

    Requires ADMIN_TECHNIQUE role.
    """
    from services.ml.retraining import RetrainingPipelineService

    try:
        service = RetrainingPipelineService()
        result = await service.trigger_retraining(
            model_id=model_id,
            dataset_tag=request.dataset_tag,
            config=request.config,
        )

        return RetrainingResponse(
            run_id=result.run_id,
            status=result.status,
            model_name=result.model_name,
            dataset_version=result.dataset_version,
            metrics=result.metrics,
            processing_time_ms=result.processing_time_ms,
            artifact_uri=result.artifact_uri,
            recommendation=result.recommendation,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retraining pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retraining error: {e!s}")


@router.post("/feedback/{slide_id}", response_model=FeedbackResponse)
async def submit_feedback(
    slide_id: str,
    request: FeedbackRequest,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Record pathologist correction on ML prediction."""
    import uuid as uuid_mod

    try:
        # Validate annotation ID format
        try:
            annotation_uuid = uuid_mod.UUID(request.original_annotation_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid annotation UUID format")

        # Create correction record
        from sqlalchemy import func, select

        from core.database import get_db_context
        from models.correction import Correction

        async with get_db_context() as session:
            correction = Correction(
                annotation_id=annotation_uuid,
                slide_id=slide_id,
                correction_type=request.correction_type,
                comment=request.notes,
                created_by=(
                    current_user.username if hasattr(current_user, "username") else "anonymous"
                ),
            )
            session.add(correction)
            await session.flush()

            # Get stats
            result = await session.execute(
                select(
                    Correction.correction_type,
                    func.count(Correction.id),
                )
                .where(Correction.slide_id == slide_id)
                .group_by(Correction.correction_type)
            )
            stats = {row[0]: row[1] for row in result.all()}

        return FeedbackResponse(
            correction_id=str(correction.id),
            slide_id=slide_id,
            correction_type=request.correction_type,
            stats=stats,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Feedback error: {e!s}")


@router.get("/feedback/stats")
async def get_feedback_stats(
    model_name: str = Query(None),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Get aggregated feedback statistics per model (7-day sliding window)."""
    from core.database import get_db_context
    from services.feedback_collector import FeedbackCollector

    collector = FeedbackCollector()
    async with get_db_context() as session:
        stats = await collector.get_stats(session, model_name=model_name)

    return {
        "stats": [
            {
                "model_name": s.model_name,
                "window_days": s.window_days,
                "total_corrections": s.total_corrections,
                "confirmed": s.confirmed,
                "rejected": s.rejected,
                "refined": s.refined,
                "relabeled": s.relabeled,
                "rejection_rate": s.rejection_rate,
                "needs_retrain": s.needs_retrain,
                "high_rejection": s.high_rejection,
            }
            for s in stats
        ],
    }


# ============================================================================
# SIMILARITY SEARCH
# ============================================================================

_similarity_index = None


def get_similarity_index():
    """Get or create the singleton SimilarityIndex."""
    global _similarity_index
    if _similarity_index is None:
        from services.ml.similarity_index import FAISS_AVAILABLE, SimilarityIndex

        if not FAISS_AVAILABLE:
            raise HTTPException(503, "Similarity search unavailable (faiss-cpu not installed)")
        _similarity_index = SimilarityIndex()
    return _similarity_index


@router.post("/similar/{slide_id}", response_model=SimilarityResponse)
async def search_similar(
    slide_id: str,
    top_k: int = Query(5, ge=1, le=20),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Find the K most similar slides to the given slide."""
    import os

    index = get_similarity_index()

    # Get query embeddings from disk cache
    disk_cache = get_disk_cache()
    model = os.getenv("ML_EXTRACTOR", "ctranspath")
    embeddings = disk_cache.load_embeddings(slide_id, model)

    if embeddings is None:
        raise HTTPException(404, f"No embeddings cached for slide {slide_id}")

    results = index.search(embeddings, top_k=top_k, exclude_id=slide_id)

    # Enrich with slide names and overview URLs
    for r in results:
        r["name"] = r["slide_id"].split("/")[-1] if "/" in r["slide_id"] else r["slide_id"]
        r["overview_url"] = f"/api/v1/slides/{r['slide_id']}/overview"

    return SimilarityResponse(
        query_slide_id=slide_id,
        results=[SimilarSlideResult(**r) for r in results],
        index_size=index.size(),
    )


@router.post("/batch/predict", response_model=BatchJobResponse)
@limit(ml_rate)
async def batch_predict(
    request: Request,
    body: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Batch inference asynchrone.

    Pour gros volumes (re-training, validation, etc.)

    Process:
    1. Créer job en DB
    2. Lancer processing en background
    3. Retourner job_id
    4. Client poll /batch/status/{job_id}

    Args:
        body: Liste slide_ids

    Returns:
        BatchJobResponse avec job_id

    Examples:
        ```bash
        curl -X POST "http://localhost:8000/api/ml/batch/predict" \\
          -H "Content-Type: application/json" \\
          -d '{"slide_ids": ["slide1", "slide2", "slide3"]}'
        ```
    """
    import uuid
    from datetime import datetime

    # Create job
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "queued",
        "total_slides": len(body.slide_ids),
        "processed_slides": 0,
        "failed_slides": 0,
        "created_at": datetime.utcnow().isoformat(),
        "estimated_time_minutes": len(body.slide_ids) * 2,  # 2 min per slide
    }

    # TODO: Store job in DB

    # Launch background task
    # background_tasks.add_task(process_batch_predictions, job_id, body.slide_ids)

    return BatchJobResponse(**job)


@router.get("/batch/status/{job_id}", response_model=BatchJobResponse)
async def get_batch_status(job_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """
    Récupère statut d'un batch job.

    Args:
        job_id: Job ID

    Returns:
        BatchJobResponse avec statut actuel

    Examples:
        ```bash
        curl "http://localhost:8000/api/ml/batch/status/{job_id}"
        ```
    """
    # TODO: Récupérer job depuis DB
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/models", response_model=List[ModelInfoResponse])
async def list_models(
    tag_router=Depends(get_tag_router), current_user: CurrentUser = Depends(get_current_user)
):
    """
    Liste tous les modèles disponibles.

    Returns:
        Liste de ModelInfoResponse

    Examples:
        ```bash
        curl "http://localhost:8000/api/ml/models"
        ```
    """
    routes = tag_router.get_all_routes()

    models = []
    for route in routes:
        model = ModelInfoResponse(
            model_id=route.model_id,
            model_name=route.model_name,
            version=route.model_version,
            task_type=route.task_type,
            classes=route.required_tags.get("classes", []),
            device="auto",  # TODO: from config
            reference_metrics=route.reference_metrics,
            provider="slideflow",  # TODO: from config
        )
        models.append(model)

    return models


@router.post("/models/reload")
async def reload_models(
    tag_router=Depends(get_tag_router),
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    Reload model configuration (hot reload).

    Utile si ml_routes.yaml modifié sans redémarrer service.

    Returns:
        {"status": "ok", "message": "Configuration reloaded"}

    Examples:
        ```bash
        curl -X POST "http://localhost:8000/api/ml/models/reload"
        ```
    """
    try:
        tag_router.reload_configuration()
        return {"status": "ok", "message": "Model configuration reloaded"}
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/{slide_id}", response_model=TagsResponse)
async def get_slide_tags(
    slide_id: str,
    tag_extractor=Depends(get_tag_extractor),
    memory_cache=Depends(get_memory_cache),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Auto-tag une lame — classification automatique (organe, coloration, pathologie).

    Utilise le TagExtractor existant pour extraire des tags depuis les métadonnées
    et le nom de fichier de la lame. Les résultats sont mis en cache mémoire.
    """
    # Check cache
    cache_key = f"tags:{slide_id}"
    cached = memory_cache.get(cache_key)
    if cached is not None:
        return TagsResponse(
            slide_id=slide_id,
            tags=cached["tags"],
            source=cached["source"],
        )

    # Get slide path
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")

    # Extract format from extension
    from pathlib import Path

    ext = Path(slide_path).suffix.upper().lstrip(".")
    slide_format = ext if ext else "UNKNOWN"

    # Extract tags
    try:
        raw_tags = tag_extractor.extract_tags(slide_path, slide_format)
    except Exception as e:
        logger.warning(f"Tag extraction failed for {slide_id}: {e}")
        raw_tags = {
            "organ": None,
            "stain": None,
            "marker": None,
            "confidence": 0.0,
            "source": "error",
        }

    tags_dict = {
        "organ": raw_tags.get("organ"),
        "stain": raw_tags.get("stain"),
        "marker": raw_tags.get("marker"),
        "pathology": None,  # Will be populated by ML in future
        "confidence": str(raw_tags.get("confidence", 0.0)),
    }
    source = raw_tags.get("source", "unknown")

    # Cache result
    memory_cache.set(cache_key, {"tags": tags_dict, "source": source})

    return TagsResponse(
        slide_id=slide_id,
        tags=tags_dict,
        source=source,
    )


@router.get("/health")
async def health_check(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Health check pour ML services.

    Returns:
        {"status": "ok", "provider": "slideflow", "device": "cpu"}

    Examples:
        ```bash
        curl "http://localhost:8000/api/ml/health"
        ```
    """
    provider_name = os.getenv("ML_PROVIDER", "slideflow")
    worker_alive = _ml_worker.is_alive() if _ml_worker else False
    return {
        "status": "ok",
        "provider": provider_name,
        "device": "cpu",
        "worker_alive": worker_alive,
    }
