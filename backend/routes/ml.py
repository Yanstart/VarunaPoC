"""
ML Routes - API Endpoints for Machine Learning

Endpoints:
- POST /ml/predict/{slide_id} - Prédiction sur slide
- POST /ml/features/{slide_id} - Extraction features
- GET  /ml/heatmap/{slide_id} - Génération heatmap
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


@router.post("/batch/predict", response_model=BatchJobResponse)
async def batch_predict(request: BatchPredictionRequest, background_tasks: BackgroundTasks):
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
async def get_batch_status(job_id: str):
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
async def list_models(tag_router=Depends(get_tag_router)):
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
async def reload_models(tag_router=Depends(get_tag_router)):
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


@router.get("/health")
async def health_check(provider=Depends(get_ml_provider)):
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
