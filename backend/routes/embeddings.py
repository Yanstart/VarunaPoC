"""
Embedding Routes - API Endpoints for Slide Embeddings

Endpoints:
- POST /api/embeddings/{slide_id}  - Extract embeddings from a slide
- GET  /api/embeddings/models      - List available embedding models

References:
- FastAPI: https://fastapi.tiangolo.com/
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

# Singleton service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton EmbeddingService."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


@router.post("/{slide_id}")
async def extract_embeddings(slide_id: str, model: str = "uni"):
    """Extract embeddings from a slide using a foundation model.

    Args:
        slide_id: Unique identifier for the slide.
        model: Embedding model to use (default: "uni").

    Returns:
        Embedding extraction result with metadata.

    Raises:
        400: Invalid model name.
        500: Extraction failed.
    """
    service = get_embedding_service()

    try:
        result = service.extract_embeddings(slide_id=slide_id, model=model)
        return {
            "slide_id": result.slide_id,
            "model": result.model,
            "dimensions": result.dimensions,
            "embeddings_count": result.embeddings_count,
            "processing_time_ms": result.processing_time_ms,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Embedding extraction failed for %s: %s", slide_id, e)
        raise HTTPException(status_code=500, detail=f"Embedding extraction failed: {e!s}")


@router.get("/models")
async def list_models():
    """List available embedding models with their specifications.

    Returns:
        Dict of model name to model metadata (dimensions, tile size, description).
    """
    service = get_embedding_service()
    return {"models": service.list_models()}
