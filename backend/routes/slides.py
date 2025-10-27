"""
Slides API Routes

Endpoints pour lister et charger les lames histologiques.

API Design:
- GET /api/slides → Liste toutes les lames (scan récursif complet)
- GET /api/browse?path={path} → Navigation hiérarchique dans /Slides
- GET /api/slides/{id}/info → Métadonnées d'une lame
- GET /api/slides/{id}/overview → Image overview (JPEG)
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from services.slide_scanner import scan_slides_directory, get_slide_path_by_id
from services.slide_loader import get_slide_metadata, get_slide_overview_bytes
from services.folder_browser import browse_directory
from services.tile_server import tile_server

router = APIRouter(prefix="/api/slides")


@router.get("/", tags=["navigation"])
async def list_slides():
    """
    Liste toutes les lames détectées dans /Slides (scan récursif complet).

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
        - Pour navigation hiérarchique, utiliser /api/browse
    """
    slides = scan_slides_directory()
    return {"count": len(slides), "slides": slides}


@router.get("/browse", tags=["navigation"])
async def browse_slides_directory(path: str = Query("/", description="Chemin relatif depuis /Slides")):
    """
    Navigation hiérarchique dans le répertoire /Slides.

    Args:
        path: Chemin relatif depuis la racine /Slides (ex: "/", "/3DHistech", "/projects/2024")

    Returns:
        {
            "current_path": str,           # Chemin actuel
            "parent_path": str | null,     # Chemin parent (null si racine)
            "breadcrumb": [str],           # Fil d'Ariane
            "folders": [                   # Sous-dossiers
                {
                    "name": str,
                    "path": str,
                    "item_count": int      # Nombre d'items dans le dossier
                }
            ],
            "slides": [                    # Lames détectées dans ce dossier
                {
                    "name": str,
                    "path": str,
                    "id": str,
                    "format_string": str,
                    "structure_type": str,
                    "is_supported": bool,
                    "notes": str,
                    "dependencies": [str]  # Fichiers/dossiers associés
                }
            ],
            "files": [                     # Fichiers non-slides (sans extension, etc.)
                {
                    "name": str,
                    "extension": str | null,
                    "is_supported": false,
                    "notes": str
                }
            ]
        }

    Raises:
        400: Chemin invalide ou tentative de path traversal
        404: Dossier introuvable

    Security:
        - Path traversal bloqué (../ interdit)
        - Accès limité à la racine /Slides uniquement

    Technical Notes:
        - Lecture NON récursive (un seul niveau de profondeur)
        - Détection des slides avec format_detector
        - Fichiers sans extension marqués non supportés
        - Voir docs/USER_GUIDE_SLIDE_STRUCTURE.md pour règles complètes
    """
    try:
        result = browse_directory(path)
        return result
    except PermissionError as e:
        raise HTTPException(400, f"Invalid path: {e}")
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error browsing directory: {e}")


@router.get("/{slide_id}/info", tags=["visualization"])
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


@router.get("/{slide_id}/overview", tags=["visualization"])
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


@router.get("/{slide_id}/dzi.json", tags=["visualization"])
async def get_dzi_metadata(slide_id: str):
    """
    Récupère métadonnées DZI pour OpenSeadragon (streaming de tuiles).

    Args:
        slide_id: ID unique de la lame

    Returns:
        {
            "width": int,               # Largeur niveau 0 (pixels)
            "height": int,              # Hauteur niveau 0 (pixels)
            "tile_size": int,           # Taille tuile (256px standard)
            "overlap": int,             # Chevauchement tuiles (0 pour simplicité)
            "format": "jpeg",
            "levels": int,              # Nombre de niveaux pyramidaux
            "level_dimensions": [[w,h], ...],   # Dimensions par niveau
            "level_downsamples": [1.0, 2.0, ...]  # Facteurs de réduction
        }

    Raises:
        404: Lame introuvable
        500: Erreur OpenSlide

    Technical Notes:
        - Format compatible OpenSeadragon DziTileSource
        - overlap=0 pour simplifier (pas de chevauchement)
        - tile_size=256 (standard DZI/OpenSeadragon)
        - Voir: docs/CLAUDE.md section "Coordinate Mapping"
    """
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(404, f"Slide {slide_id} not found")

    try:
        metadata = tile_server.get_dzi_metadata(slide_path)
        return JSONResponse(content=metadata)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error getting DZI metadata: {e}")


@router.get("/{slide_id}/tiles/{level}/{col}_{row}.jpg", tags=["visualization"])
async def get_tile(slide_id: str, level: int, col: int, row: int):
    """
    Extrait une tuile JPEG depuis une lame (streaming à la demande).

    Args:
        slide_id: ID unique de la lame
        level: Niveau pyramidal (0 = haute résolution, max = niveau le plus bas)
        col: Colonne de la tuile (x / tile_size)
        row: Ligne de la tuile (y / tile_size)

    Returns:
        Image JPEG de la tuile (256x256 pixels, quality 85)

    Raises:
        404: Lame introuvable ou tuile hors limites
        500: Erreur OpenSlide

    Technical Notes:
        - Coordonnées tuile converties en coordonnées niveau 0 pour OpenSlide
        - RGBA converti en RGB (OpenSlide retourne RGBA)
        - Tuiles hors limites retournent 404 (pas d'image noire)
        - Cache des slides ouverts (max 5 simultanés)
        - Voir: tile_server.py pour logique d'extraction

    Examples:
        GET /api/slides/a1b2c3d4e5f6/tiles/2/5_3.jpg
        → Tuile au niveau 2, colonne 5, ligne 3
    """
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(404, f"Slide {slide_id} not found")

    try:
        tile_bytes = tile_server.get_tile(slide_path, level, col, row, tile_size=256)

        if tile_bytes is None:
            # Tuile hors limites (pas d'erreur, juste pas de contenu)
            raise HTTPException(404, "Tile out of bounds")

        return Response(content=tile_bytes, media_type="image/jpeg")

    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error extracting tile: {e}")
