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
from io import BytesIO
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from core.exceptions import MLProviderError
from core.interfaces import get_provider
from services.ml import TagExtractor, TagRouter
from services.slide_scanner import get_slide_path_by_id

# Formats not supported by Slideflow/OpenSlide for ML analysis
_UNSUPPORTED_ML_FORMATS = {".dcm", ".dicom"}


def _check_slide_format(slide_path: str, slide_id: str):
    """Raise 400 if slide format is not supported for ML analysis."""
    from pathlib import Path

    ext = Path(slide_path).suffix.lower()
    if ext in _UNSUPPORTED_ML_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Slide format '{ext}' is not supported for ML analysis. "
            f"Supported formats: SVS, MRXS, NDPI, BIF, TIFF, SCN.",
        )


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


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


# ============================================================================
# DEPENDENCIES
# ============================================================================


# Singleton cache: avoid reloading heavy ML models on every request
_ml_provider_instance = None
_ml_provider_config_hash = None


def get_ml_provider():
    """
    Dependency pour récupérer ML provider (singleton).

    Le provider est initialisé une seule fois au premier appel,
    puis réutilisé. Le modèle/extractor n'est chargé qu'une fois.

    Configuration via variables d'environnement:
        ML_ENABLED=true              # Activer/désactiver ML
        ML_PROVIDER=slideflow        # "slideflow", "openslide", "mock"
        ML_MODE=extractor            # "extractor" (Phase 1-2) ou "classifier" (Phase 3)
        ML_EXTRACTOR=ctranspath      # Nom du feature extractor
        ML_MODEL_PATH=               # Chemin modèle entraîné (Phase 3)
        ML_CLASSES=tissue,background # Classes pour classification

    Returns:
        MLProvider instance configurée selon le mode

    Raises:
        HTTPException 503: Si ML features désactivées ou provider indisponible
    """
    global _ml_provider_instance, _ml_provider_config_hash
    import os

    ml_enabled = os.getenv("ML_ENABLED", "true").lower() == "true"
    if not ml_enabled:
        raise HTTPException(status_code=503, detail="ML features disabled in configuration")

    # Config hash to detect env changes (hot reload)
    provider_name = os.getenv("ML_PROVIDER", "slideflow")
    ml_mode = os.getenv("ML_MODE", "extractor")
    extractor_name = os.getenv("ML_EXTRACTOR", "resnet50_imagenet")
    model_path = os.getenv("ML_MODEL_PATH", "")
    config_hash = f"{provider_name}:{ml_mode}:{extractor_name}:{model_path}"

    # Return cached instance if config unchanged
    if _ml_provider_instance is not None and _ml_provider_config_hash == config_hash:
        return _ml_provider_instance

    try:
        provider = get_provider(provider_name)

        # Auto-configure slideflow provider from env
        if provider_name == "slideflow" and not provider.model_loaded:
            classes_str = os.getenv("ML_CLASSES", "tissue,background")
            classes = [c.strip() for c in classes_str.split(",") if c.strip()]

            if ml_mode == "classifier" and model_path:
                # Phase 3: trained model
                provider.load_model(
                    model_path,
                    {
                        "model_id": os.getenv("ML_MODEL_ID", "custom_classifier"),
                        "mode": "classifier",
                        "classes": classes,
                        "tile_size": int(os.getenv("ML_TILE_SIZE", "224")),
                        "num_mc_samples": int(os.getenv("ML_MC_SAMPLES", "10")),
                    },
                )
            else:
                # Phase 1-2: feature extractor
                provider.load_model(
                    f"extractor://{extractor_name}",
                    {
                        "model_id": f"{extractor_name}_features",
                        "mode": "extractor",
                        "classes": classes,
                    },
                )

        _ml_provider_instance = provider
        _ml_provider_config_hash = config_hash
        return provider

    except Exception as e:
        logger.error(f"Failed to initialize ML provider: {e}")
        raise HTTPException(status_code=503, detail=f"ML provider unavailable: {e!s}")


def get_tag_extractor():
    """Dependency pour TagExtractor."""
    return TagExtractor()


def get_tag_router():
    """Dependency pour TagRouter."""
    import os

    config_path = os.getenv("ML_ROUTES_CONFIG", "config/ml_routes.yaml")
    return TagRouter(config_path)


from services.cache.memory_cache import MemoryCache

_memory_cache = None


def get_memory_cache():
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache(maxsize=512, ttl=300)
    return _memory_cache


from services.cache.disk_cache import DiskCache

_disk_cache = None


def get_disk_cache():
    global _disk_cache
    if _disk_cache is None:
        _disk_cache = DiskCache()
    return _disk_cache


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/predict/{slide_id}", response_model=PredictionResponse)
async def predict_slide(
    slide_id: str,
    request: PredictionRequest = PredictionRequest(),
    provider=Depends(get_ml_provider),
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
    4. Inference via MLProvider
    5. Retourner résultat

    Args:
        slide_id: Identifiant lame
        request: Paramètres prédiction (région, model_id, etc.)

    Returns:
        PredictionResponse avec classe, confiance, incertitude

    Errors:
        404: Slide introuvable
        400: Paramètres invalides
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

        # Check if provider is already loaded in extractor mode
        # → skip tag routing (no trained models needed)
        if provider.model_loaded and getattr(provider, "mode", "") == "extractor":
            # Phase 1-2: Use pre-loaded feature extractor directly
            region_tuple = (
                (request.region.x, request.region.y, request.region.width, request.region.height)
                if request.region
                else None
            )

            result = provider.predict(slide_path, region=region_tuple)

            return PredictionResponse(
                slide_id=slide_id,
                prediction_class=result.prediction_class,
                confidence=result.confidence,
                uncertainty=result.uncertainty,
                probabilities=result.probabilities,
                execution_time_ms=result.execution_time_ms,
                model_id=result.model_id,
                model_name=provider.model_config.get("extractor_name", "feature_extractor"),
                tags=result.metadata,
            )

        # Phase 3: Full tag routing → specialized model
        from pathlib import Path

        ext = Path(slide_path).suffix.upper().lstrip(".")
        slide_format = ext if ext else "UNKNOWN"

        # Extract tags
        logger.info(f"Extracting tags for: {slide_id}")
        tags = tag_extractor.extract_tags(slide_path, slide_format)

        # Route to model
        if request.model_id:
            route = tag_router.get_route_by_model_id(request.model_id)
            if not route:
                raise HTTPException(status_code=404, detail=f"Model {request.model_id} not found")
        else:
            route = tag_router.route(tags)

        # Load model
        logger.info(f"Loading model: {route.model_id}")
        model_config = {
            "model_id": route.model_id,
            "model_name": route.model_name,
            "version": route.model_version,
            "classes": route.required_tags.get("classes", []),
            "tile_size": 224,
            "num_mc_samples": request.num_mc_samples,
        }
        provider.load_model(route.model_path, model_config)

        # Predict
        region_tuple = (
            (request.region.x, request.region.y, request.region.width, request.region.height)
            if request.region
            else None
        )

        result = provider.predict(slide_path, region=region_tuple)

        return PredictionResponse(
            slide_id=slide_id,
            prediction_class=result.prediction_class,
            confidence=result.confidence,
            uncertainty=result.uncertainty,
            probabilities=result.probabilities,
            execution_time_ms=result.execution_time_ms,
            model_id=result.model_id,
            model_name=route.model_name,
            tags=tags,
        )

    except HTTPException:
        raise
    except MLProviderError as e:
        logger.error(f"ML prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@router.post("/features/{slide_id}", response_model=FeatureExtractionResponse)
async def extract_features(
    slide_id: str,
    request: FeatureExtractionRequest = FeatureExtractionRequest(),
    provider=Depends(get_ml_provider),
    tag_router=Depends(get_tag_router),
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

        # In extractor mode, the provider is already loaded with the extractor
        # → use it directly without routing
        if not provider.model_loaded:
            # Fallback: try to load via routing if provider not pre-loaded
            route = tag_router.get_route_by_model_id(request.model_id or "feature_extractor")
            model_config = {
                "model_id": route.model_id if route else "feature_extractor",
                "embedding_dim": 512,
            }
            provider.load_model(
                route.model_path if route else "mock://feature_extractor", model_config
            )

        # Extract features
        result = provider.extract_features(slide_path, request.tile_size, request.overlap)

        response = FeatureExtractionResponse(
            slide_id=slide_id,
            num_patches=result.num_patches,
            embedding_dim=result.embedding_dim,
            embeddings_shape=list(result.embeddings.shape),
            model_id=result.model_id,
            storage_path=None,
        )

        return response

    except HTTPException:
        raise
    except MLProviderError as e:
        logger.error(f"Feature extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heatmap/{slide_id}")
async def get_heatmap(
    slide_id: str,
    prediction_class: str = Query(..., description="Target class for heatmap"),
    resolution_level: int = Query(2, ge=0, le=5, description="Resolution level (0=max)"),
    colormap: str = Query("jet", description="Matplotlib colormap (jet, hot, viridis, etc.)"),
    provider=Depends(get_ml_provider),
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

        # Generate heatmap
        result = provider.generate_heatmap(slide_path, prediction_class, resolution_level)

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
    except MLProviderError as e:
        logger.error(f"Heatmap generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/{slide_id}")
async def detect_regions_endpoint(
    slide_id: str,
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Confidence threshold"),
    min_area: float = Query(100.0, ge=0.0, description="Minimum region area (px^2)"),
    simplify_tolerance: float = Query(2.0, ge=0.0, description="Douglas-Peucker tolerance"),
    resolution_level: int = Query(2, ge=0, le=5, description="Heatmap resolution level"),
    prediction_class: str = Query("tissue", description="Target class for heatmap"),
    provider=Depends(get_ml_provider),
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

        # Generate heatmap via existing ML provider
        heatmap_result = provider.generate_heatmap(
            slide_path,
            prediction_class,
            resolution_level,
        )

        # Run detection pipeline
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
    except MLProviderError as e:
        logger.error(f"Detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection error: {e!s}")


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
    provider=Depends(get_ml_provider),
    disk_cache: DiskCache = Depends(get_disk_cache),
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

        # Check disk cache for heatmap
        model_id = (
            provider.model_config.get("model_id", "unknown") if provider.model_loaded else "unknown"
        )
        cached_heatmap = disk_cache.load_heatmap(slide_id, model_id)

        if cached_heatmap is not None:
            heatmap = cached_heatmap
            # We need slide dimensions - get from OpenSlide
            import openslide

            slide = openslide.OpenSlide(slide_path)
            slide_dimensions = slide.dimensions
            slide.close()
        else:
            # Generate heatmap
            heatmap_result = provider.generate_heatmap(
                slide_path, prediction_class, resolution_level
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
    except MLProviderError as e:
        logger.error(f"Focus assist failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Focus assist error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Focus assist error: {e!s}")


@router.get("/measure/{slide_id}", response_model=MeasurementResponse)
async def measure_slide(
    slide_id: str,
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    prediction_class: str = Query("tissue"),
    resolution_level: int = Query(2, ge=0, le=5),
    provider=Depends(get_ml_provider),
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

        # Generate heatmap
        heatmap_result = provider.generate_heatmap(slide_path, prediction_class, resolution_level)

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
    except MLProviderError as e:
        logger.error(f"Measurement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Measurement error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Measurement error: {e!s}")


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
        from core.database import get_db_context
        from models.correction import Correction
        from sqlalchemy import select, func

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
    from services.feedback_collector import FeedbackCollector
    from core.database import get_db_context

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
        from services.ml.similarity_index import SimilarityIndex, FAISS_AVAILABLE

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
    disk_cache = DiskCache()
    model = os.getenv("ML_EXTRACTOR", "ctranspath")
    embeddings = disk_cache.load_embeddings(slide_id, model)

    if embeddings is None:
        raise HTTPException(404, f"No embeddings cached for slide {slide_id}")

    results = index.search(embeddings, top_k=top_k, exclude_id=slide_id)

    # Enrich with slide names and overview URLs
    for r in results:
        r["name"] = r["slide_id"].split("/")[-1] if "/" in r["slide_id"] else r["slide_id"]
        r["overview_url"] = f"/api/slides/{r['slide_id']}/overview"

    return SimilarityResponse(
        query_slide_id=slide_id,
        results=[SimilarSlideResult(**r) for r in results],
        index_size=index.size(),
    )


@router.post("/batch/predict", response_model=BatchJobResponse)
async def batch_predict(
    request: BatchPredictionRequest,
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
        request: Liste slide_ids

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
        "total_slides": len(request.slide_ids),
        "processed_slides": 0,
        "failed_slides": 0,
        "created_at": datetime.utcnow().isoformat(),
        "estimated_time_minutes": len(request.slide_ids) * 2,  # 2 min per slide
    }

    # TODO: Store job in DB

    # Launch background task
    # background_tasks.add_task(process_batch_predictions, job_id, request.slide_ids)

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
    memory_cache: MemoryCache = Depends(get_memory_cache),
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
        "confidence": raw_tags.get("confidence", 0.0),
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
    provider=Depends(get_ml_provider), current_user: CurrentUser = Depends(get_current_user)
):
    """
    Health check pour ML services.

    Returns:
        {"status": "ok", "provider": "slideflow", "device": "cuda"}

    Examples:
        ```bash
        curl "http://localhost:8000/api/ml/health"
        ```
    """
    return {"status": "ok", "provider": "slideflow", "device": provider.device}
