"""
Slides API Routes

Endpoints pour lister et charger les lames histologiques.

API Design:
- GET /api/slides → Liste toutes les lames
- GET /api/slides/{id}/info → Métadonnées d'une lame
- GET /api/slides/{id}/overview → Image overview (JPEG)
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from services.slide_scanner import scan_slides_directory, get_slide_path_by_id
from services.slide_loader import get_slide_metadata, get_slide_overview_bytes

router = APIRouter(prefix="/api/slides", tags=["slides"])


@router.get("/")
async def list_slides():
    """
    Liste toutes les lames détectées dans /Slides.

    Returns:
        {
            "count": int,
            "slides": [
                {
                    "id": str,
                    "name": str,
                    "path": str,
                    "format": str,
                    "has_companions": bool
                },
                ...
            ]
        }

    Technical Notes:
        - Scan récursif de /Slides et sous-dossiers
        - has_companions indique si .mrxs a son dossier compagnon
    """
    slides = scan_slides_directory()
    return {"count": len(slides), "slides": slides}


@router.get("/{slide_id}/info")
async def get_slide_info(slide_id: str):
    """
    Récupère métadonnées d'une lame.

    Args:
        slide_id: ID unique de la lame (hash MD5)

    Returns:
        {
            "dimensions": [width, height],
            "level_count": int,
            "level_dimensions": [[w,h], ...],
            "level_downsamples": [1.0, 2.0, ...],
            "vendor": str,
            "format": str
        }

    Raises:
        404: Lame introuvable
        500: Erreur OpenSlide

    Technical Notes:
        - Ouvre temporairement la lame avec OpenSlide
        - Extrait métadonnées puis ferme immédiatement
    """
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(404, f"Slide {slide_id} not found")

    try:
        metadata = get_slide_metadata(slide_path)
        return metadata
    except RuntimeError as e:
        raise HTTPException(500, str(e))


@router.get("/{slide_id}/overview")
async def get_overview(slide_id: str):
    """
    Extrait image overview d'une lame.

    Args:
        slide_id: ID unique de la lame

    Returns:
        Image JPEG (max 2000px, quality 85)

    Raises:
        404: Lame introuvable
        500: Erreur extraction

    Technical Notes:
        - Utilise OpenSlide.get_thumbnail() (SIMPLE, efficace)
        - Retourne JPEG optimisé (~100-500KB typiquement)
        - Pas de cache Phase 1 (sera ajouté Phase 2)
    """
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(404, f"Slide {slide_id} not found")

    try:
        img_bytes = get_slide_overview_bytes(slide_path)
        return Response(content=img_bytes, media_type="image/jpeg")
    except RuntimeError as e:
        raise HTTPException(500, str(e))
