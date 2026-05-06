"""
Slides API Routes

Endpoints pour lister et charger les lames histologiques.

API Design:
- GET /api/slides → Liste toutes les lames (scan récursif complet)
- GET /api/browse?path={path} → Navigation hiérarchique dans /Slides
- GET /api/v1/slides/{id}/info → Métadonnées d'une lame
- GET /api/v1/slides/{id}/overview → Image overview (JPEG)
- GET /api/v1/slides/worklist → Liste de travail (mes cas assignés)
- GET /api/v1/slides/history → Historique des lames consultées

Worklist / History DB strategy:
    Primary:  PostgreSQL tables worklist_assignments + view_history (migration 006).
    Fallback: Deterministic mock derived from the slide filesystem scan.
              Used when the DB is unavailable (no DATABASE_URL, network down, etc.)
              so the endpoint stays functional in dev/offline environments.
"""

import hashlib
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, TYPE_CHECKING

import openslide
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from core.database import get_db
from core.error_helpers import internal_error, slide_not_found, slide_open_error
from models.view_history import ViewHistory
from models.worklist import WorklistAssignment
from rate_limiting import admin_rate, limit, tile_rate
from services.folder_browser import browse_directory
from services.slide_loader import get_slide_metadata, get_slide_overview_bytes
from services.slide_scanner import (
    get_last_scan_timestamp,
    get_slide_by_name,
    get_slide_path_by_id,
    rescan,
    scan_slides_directory,
)
from services.tile_audit import schedule_tile_audit
from services.tile_server import tile_server

# Tier 5 sprint 1 — TwoLevelTileCache wiring
import time

from monitoring import record_tile_cache_lookup
from routes._storage_helpers import get_storage, resolve_slide_path

if TYPE_CHECKING:
    from core.interfaces import StorageProvider

logger = logging.getLogger(__name__)

# ==========================================
# Worklist & History Schemas
# ==========================================


class WorklistItem(BaseModel):
    slide_id: str
    slide_name: str
    case_path: str
    status: str  # "pending", "in_progress", "completed"
    assigned_date: str  # ISO date
    is_new: bool  # True if never opened


class WorklistResponse(BaseModel):
    items: List[WorklistItem]
    counts: Dict[str, int]  # {"pending": 3, "in_progress": 1, "completed": 5}


class HistoryItem(BaseModel):
    slide_id: str
    slide_name: str
    viewed_at: str  # ISO datetime
    view_count: int


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int


# ==========================================
# MPP (Microns Per Pixel) Schema
# ==========================================


class MPPResponse(BaseModel):
    """Microns-per-pixel metadata for a slide."""

    mpp_x: float
    mpp_y: float
    objective: Optional[int] = None
    source: str = "openslide"


# ==========================================
# Slide List / Browse / Info Response Schemas (#306)
# ==========================================


class SlideEntry(BaseModel):
    id: str
    name: str
    path: str
    format: str
    has_companions: bool = False


class SlideListResponse(BaseModel):
    count: int
    last_scan_timestamp: Optional[str] = None
    slides: List[SlideEntry]


class RescanResponse(BaseModel):
    count: int
    last_scan_timestamp: Optional[str] = None


class BrowseFolderEntry(BaseModel):
    name: str
    path: str
    item_count: int = 0


class BrowseSlideEntry(BaseModel):
    name: str
    path: str
    id: Optional[str] = None
    format_string: str = ""
    structure_type: str = ""
    is_supported: bool = True
    notes: str = ""
    dependencies: List[str] = []


class BrowseFileEntry(BaseModel):
    name: str
    extension: Optional[str] = None
    is_supported: bool = False
    notes: str = ""


class BrowseResponse(BaseModel):
    current_path: str
    parent_path: Optional[str] = None
    breadcrumb: List[str] = []
    folders: List[BrowseFolderEntry] = []
    slides: List[BrowseSlideEntry] = []
    files: List[BrowseFileEntry] = []


class SlideInfoResponse(BaseModel):
    dimensions: List[int]
    level_count: int
    level_dimensions: List[List[int]]
    level_downsamples: List[float]
    vendor: Optional[str] = None
    format: Optional[str] = None


class DziMetadataResponse(BaseModel):
    width: int
    height: int
    tile_size: int
    overlap: int
    format: str = "jpeg"
    levels: int
    level_dimensions: List[List[int]]
    level_downsamples: List[float]


router = APIRouter(prefix="/slides")


@router.get("/", tags=["navigation"], response_model=SlideListResponse)
def list_slides(current_user: CurrentUser = Depends(get_current_user)):
    """
    Liste toutes les lames détectées dans /Slides (scan récursif complet).

    Returns:
        {
            "count": int,
            "last_scan_timestamp": str | null,  # ISO 8601 UTC, null si cache vide
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
        - last_scan_timestamp indique quand le cache a ete construit (UTC ISO 8601)
        - Pour forcer un nouveau scan, utiliser POST /api/slides/rescan (ADMIN_TECHNIQUE)
    """
    slides = scan_slides_directory()
    ts = get_last_scan_timestamp()
    return {
        "count": len(slides),
        "last_scan_timestamp": ts.isoformat() if ts else None,
        "slides": slides,
    }


@router.post("/rescan", tags=["navigation"], response_model=RescanResponse)
@limit(admin_rate)
def rescan_slides(
    request: Request,
    current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """
    Force un nouveau scan filesystem et invalide le cache de lames.

    Vide le cache en mémoire (ID->path et données complètes) puis relance
    immédiatement un scan recursif complet de /Slides.

    Returns:
        {
            "count": int,               # Nombre de lames detectees apres rescan
            "last_scan_timestamp": str  # ISO 8601 UTC du nouveau scan
        }

    Raises:
        403: Acces refuse - role ADMIN_TECHNIQUE requis

    Technical Notes:
        - Operation synchrone: le rescan est effectue avant de repondre
        - Invalide le cache de tile_server si present
        - Apres appel, GET /api/slides/ refletera le nouveau scan
        - Utile apres ajout/suppression de lames sur le filesystem
        - Acces restreint a ADMIN_TECHNIQUE (gestion technique du serveur)

    Security:
        - Requiert le role ADMIN_TECHNIQUE
        - Quand AUTH_ENABLED=false, tous les utilisateurs ont ce role (dev/PoC)
    """
    slides = rescan()
    ts = get_last_scan_timestamp()
    return {
        "count": len(slides),
        "last_scan_timestamp": ts.isoformat() if ts else None,
    }


@router.get("/browse", tags=["navigation"], response_model=BrowseResponse)
def browse_slides_directory(
    path: str = Query(
        "/",
        description="Chemin relatif depuis /Slides",
        max_length=1024,
        pattern=r"^[a-zA-Z0-9/_.àâäéèêëïîôùûüÿçæœÀÂÄÉÈÊËÏÎÔÙÛÜŸÇÆŒ -]*$",
    ),
    current_user: CurrentUser = Depends(get_current_user),
):
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
        raise internal_error("browse_directory", e)  # noqa: EM101


@router.get("/worklist", tags=["navigation"], response_model=WorklistResponse)
async def get_worklist(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Liste de travail : cas assignés au médecin connecté.

    Primary: queries the worklist_assignments table in PostgreSQL.
    Fallback: deterministic mock derived from the filesystem scan when the DB
              is unavailable (offline dev, missing DATABASE_URL, etc.).

    Args:
        db: Async DB session injected by FastAPI.
        current_user: Authenticated user (MEDECIN or ADMIN_TECHNIQUE role).

    Returns:
        WorklistResponse avec items et counts par statut.

    Technical Notes:
        - DB rows are filtered by user_sub = current_user.sub.
        - The slide_name shown in the response is resolved from the filesystem
          scan (slide metadata is not stored in the DB — it lives in the files).
        - On SQLAlchemyError (DB down, connection refused, etc.) the endpoint
          falls back silently to the mock implementation and logs a warning.
          See migration 006 for the worklist_assignments schema.
    """
    # --- Build a quick id -> name lookup from the filesystem scan ---
    slides = scan_slides_directory()
    slide_map: Dict[str, dict] = {s["id"]: s for s in slides}

    # --- Attempt DB query ---
    try:
        stmt = (
            select(WorklistAssignment)
            .where(WorklistAssignment.user_sub == current_user.sub)
            .order_by(WorklistAssignment.assigned_date.desc())
        )
        result = await db.execute(stmt)
        assignments = result.scalars().all()

        if assignments:
            statuses = ["pending", "in_progress", "completed"]
            items = []
            for row in assignments:
                slide_info = slide_map.get(row.slide_id, {})
                slide_name = slide_info.get("name", row.slide_id)
                slide_path = slide_info.get("path", "")
                case_path = "/".join(slide_path.replace("\\", "/").split("/")[:-1]) or "/"
                items.append(
                    WorklistItem(
                        slide_id=row.slide_id,
                        slide_name=slide_name,
                        case_path=case_path,
                        status=row.status,
                        assigned_date=row.assigned_date.isoformat(),
                        is_new=row.is_new,
                    )
                )
            counts = {s: sum(1 for item in items if item.status == s) for s in statuses}
            return WorklistResponse(items=items, counts=counts)

        # DB is reachable but no assignments for this user yet — return empty list
        # (do NOT fall back to mock so the UI correctly shows an empty worklist)
        return WorklistResponse(
            items=[],
            counts={"pending": 0, "in_progress": 0, "completed": 0},
        )

    except SQLAlchemyError as exc:
        logger.warning("Worklist DB query failed (%s), falling back to mock data", exc)

    # --- Mock fallback (DB unavailable) ---
    seed = int(hashlib.md5(current_user.sub.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    statuses = ["pending", "in_progress", "completed"]
    weights = [0.5, 0.3, 0.2]  # ~50% pending, ~30% in_progress, ~20% completed

    now = datetime.now(timezone.utc)
    items = []

    for slide in slides:
        status = rng.choices(statuses, weights=weights, k=1)[0]
        days_ago = rng.randint(0, 30)
        assigned_date = now - timedelta(days=days_ago)
        is_new = status == "pending" and rng.random() < 0.3
        slide_path = slide.get("path", "")
        case_path = "/".join(slide_path.replace("\\", "/").split("/")[:-1]) or "/"

        items.append(
            WorklistItem(
                slide_id=slide["id"],
                slide_name=slide["name"],
                case_path=case_path,
                status=status,
                assigned_date=assigned_date.isoformat(),
                is_new=is_new,
            )
        )

    items.sort(key=lambda x: x.assigned_date, reverse=True)
    counts = {s: sum(1 for item in items if item.status == s) for s in statuses}
    return WorklistResponse(items=items, counts=counts)


@router.get("/history", tags=["navigation"], response_model=HistoryResponse)
async def get_history(
    limit: int = Query(20, ge=1, le=100, description="Nombre max d'items à retourner"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Historique des lames récemment consultées.

    Primary: queries the view_history table in PostgreSQL, ordered by
             viewed_at descending (most recent first).
    Fallback: deterministic mock when the DB is unavailable.

    Args:
        limit: Maximum number of items to return (default 20, max 100).
        db: Async DB session injected by FastAPI.
        current_user: Authenticated user (MEDECIN or ADMIN_TECHNIQUE role).

    Returns:
        HistoryResponse avec items et total.

    Technical Notes:
        - One row per (slide_id, user_sub) in view_history; view_count reflects
          total opens, viewed_at reflects the most recent open.
        - slide_name is resolved from the filesystem scan at query time.
        - On SQLAlchemyError the endpoint falls back to the mock and logs a
          warning. See migration 006 for the view_history schema.
    """
    slides = scan_slides_directory()
    slide_map: Dict[str, dict] = {s["id"]: s for s in slides}

    # --- Attempt DB query ---
    try:
        stmt = (
            select(ViewHistory)
            .where(ViewHistory.user_sub == current_user.sub)
            .order_by(ViewHistory.viewed_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        # Count total rows for this user (without the LIMIT)
        from sqlalchemy import func

        count_stmt = (
            select(func.count())
            .select_from(ViewHistory)
            .where(ViewHistory.user_sub == current_user.sub)
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()

        items = []
        for row in rows:
            slide_info = slide_map.get(row.slide_id, {})
            slide_name = slide_info.get("name", row.slide_id)
            items.append(
                HistoryItem(
                    slide_id=row.slide_id,
                    slide_name=slide_name,
                    viewed_at=row.viewed_at.isoformat(),
                    view_count=row.view_count,
                )
            )
        return HistoryResponse(items=items, total=total)

    except SQLAlchemyError as exc:
        logger.warning("History DB query failed (%s), falling back to mock data", exc)

    # --- Mock fallback (DB unavailable) ---
    seed = int(hashlib.md5(current_user.sub.encode()).hexdigest()[:8], 16) + 42
    rng = random.Random(seed)

    now = datetime.now(timezone.utc)
    items = []

    for slide in slides:
        seconds_ago = rng.randint(0, 7 * 24 * 3600)
        viewed_at = now - timedelta(seconds=seconds_ago)
        view_count = rng.randint(1, 10)
        items.append(
            HistoryItem(
                slide_id=slide["id"],
                slide_name=slide["name"],
                viewed_at=viewed_at.isoformat(),
                view_count=view_count,
            )
        )

    items.sort(key=lambda x: x.viewed_at, reverse=True)
    total = len(items)
    items = items[:limit]
    return HistoryResponse(items=items, total=total)


@router.get("/by-name/{slide_name:path}", tags=["pacs-integration"])
def resolve_slide_by_name(
    slide_name: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Resolve slide by filename stem (Telemis PACS integration).

    Telemis substitutes {$study.examindex$} in its plugin URL, which
    corresponds to the slide filename without extension (e.g. 'AO.25B27859.2.1.3').
    This endpoint performs a case-insensitive match against all scanned slides.

    Args:
        slide_name: Filename stem (may contain dots)

    Returns:
        Full slide metadata dict (same shape as /api/slides list items)

    Raises:
        404: No slide matches the given name
        409: Multiple slides match (ambiguous)
    """
    try:
        slide = get_slide_by_name(slide_name)
    except ValueError as e:
        raise HTTPException(409, str(e))
    if not slide:
        raise HTTPException(404, f"No slide found matching '{slide_name}'")
    return slide


@router.get("/{slide_id}/mpp", tags=["visualization"], response_model=MPPResponse)
async def get_slide_mpp(
    slide_id: str = Path(
        ...,
        description="Identifiant unique de la lame (12 caracteres hexadecimaux, hash MD5 tronque)",
        min_length=12,
        max_length=12,
        pattern=r"^[0-9a-f]{12}$",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    storage: "StorageProvider | None" = Depends(get_storage),
):
    """
    Retrieve microns-per-pixel (MPP) calibration data for a slide.

    Args:
        slide_id: Unique slide identifier (MD5 hash).

    Returns:
        MPPResponse with mpp_x, mpp_y, objective power, and data source.

    Raises:
        404: Slide not found or MPP data unavailable.
        422: Slide detected but cannot be opened.

    Technical Notes:
        - Primary source: ``openslide.mpp-x`` / ``openslide.mpp-y`` properties.
        - Fallback: estimate MPP from ``openslide.objective-power`` using a
          standard lookup table (40x -> 0.25, 20x -> 0.50, etc.).
        - Returns 404 if neither MPP nor objective power is available.
        - Sprint 6: async + StorageProvider injected; OpenSlide call runs in
          a worker thread so the loop stays free.
    """
    import asyncio

    from services.slide_utils import resolve_slide_mpp

    slide_path = await resolve_slide_path(storage, slide_id)

    try:
        mpp_data = await asyncio.to_thread(resolve_slide_mpp, slide_path)
    except openslide.OpenSlideError as e:
        raise slide_open_error(slide_id, e)

    if not mpp_data:
        raise HTTPException(
            404,
            f"MPP data not available for slide {slide_id}. "
            "Neither openslide.mpp-x/y nor openslide.objective-power found in metadata.",
        )

    return MPPResponse(
        mpp_x=mpp_data.mpp_x,
        mpp_y=mpp_data.mpp_y,
        objective=mpp_data.objective,
        source=mpp_data.source,
    )


@router.get("/{slide_id}/info", tags=["visualization"], response_model=SlideInfoResponse)
async def get_slide_info(
    background_tasks: BackgroundTasks,
    slide_id: str = Path(
        ...,
        description="Identifiant unique de la lame (12 caracteres hexadecimaux, hash MD5 tronque)",
        min_length=12,
        max_length=12,
        pattern=r"^[0-9a-f]{12}$",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    storage: "StorageProvider | None" = Depends(get_storage),
):
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
        - Ouvre temporairement la lame avec OpenSlide (en thread pool)
        - Extrait métadonnées puis ferme immédiatement
    """
    import asyncio
    import os

    slide_path = await resolve_slide_path(storage, slide_id)

    try:
        metadata = await asyncio.to_thread(get_slide_metadata, slide_path)

        # Trigger background embedding pre-computation
        if os.getenv("ML_ENABLED", "true").lower() == "true":
            from services.background_tasks import precompute_embeddings

            background_tasks.add_task(precompute_embeddings, slide_id, slide_path)

        return metadata
    except openslide.OpenSlideError as e:
        raise slide_open_error(slide_id, e)
    except RuntimeError as e:
        raise internal_error("get_slide_info", e)  # noqa: EM101


@router.get("/{slide_id}/overview", tags=["visualization"])
async def get_overview(
    slide_id: str = Path(
        ...,
        description="Identifiant unique de la lame (12 caracteres hexadecimaux, hash MD5 tronque)",
        min_length=12,
        max_length=12,
        pattern=r"^[0-9a-f]{12}$",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    storage: "StorageProvider | None" = Depends(get_storage),
):
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
        - Sprint 6: async + StorageProvider injected; OpenSlide thumbnail
          runs in a worker thread.
    """
    import asyncio

    slide_path = await resolve_slide_path(storage, slide_id)

    try:
        img_bytes = await asyncio.to_thread(get_slide_overview_bytes, slide_path)
        return Response(content=img_bytes, media_type="image/jpeg")
    except openslide.OpenSlideError as e:
        raise slide_open_error(slide_id, e)
    except RuntimeError as e:
        raise internal_error("get_overview", e)  # noqa: EM101


@router.get("/{slide_id}/dzi.json", tags=["visualization"], response_model=DziMetadataResponse)
async def get_dzi_metadata(
    slide_id: str = Path(
        ...,
        description="Identifiant unique de la lame (12 caracteres hexadecimaux, hash MD5 tronque)",
        min_length=12,
        max_length=12,
        pattern=r"^[0-9a-f]{12}$",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    storage: "StorageProvider | None" = Depends(get_storage),
):
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
        - Sprint 6: async + StorageProvider injected; OpenSlide opening
          runs in a worker thread.
    """
    import asyncio

    slide_path = await resolve_slide_path(storage, slide_id)

    try:
        metadata = await asyncio.to_thread(tile_server.get_dzi_metadata, slide_path)
        return JSONResponse(content=metadata)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except openslide.OpenSlideError as e:
        raise slide_open_error(slide_id, e)
    except Exception as e:
        raise internal_error("get_dzi_metadata", e)  # noqa: EM101


@router.get("/{slide_id}/tiles/{level}/{col}_{row}.jpg", tags=["visualization"])
@limit(tile_rate)
async def get_tile(
    request: Request,
    slide_id: str = Path(
        ...,
        description="Identifiant unique de la lame (12 caracteres hexadecimaux, hash MD5 tronque)",
        min_length=12,
        max_length=12,
        pattern=r"^[0-9a-f]{12}$",
    ),
    level: int = Path(..., ge=0, description="Niveau pyramidal (0 = haute resolution)"),
    col: int = Path(..., ge=0, description="Colonne de la tuile"),
    row: int = Path(..., ge=0, description="Ligne de la tuile"),
    current_user: CurrentUser = Depends(get_current_user),
    storage: "StorageProvider | None" = Depends(get_storage),
):
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
        GET /api/v1/slides/a1b2c3d4e5f6/tiles/2/5_3.jpg
        → Tuile au niveau 2, colonne 5, ligne 3
    """
    slide_path = await resolve_slide_path(storage, slide_id)

    try:
        # Detect whether the slide is already in the open-slide cache before
        # extraction so we can include the cache_hit flag in the audit event.
        # NOTE: this is the open-slide handle cache, not the tile-bytes cache;
        # the latter is checked below via TwoLevelTileCache.
        slide_cache_hit = slide_path in tile_server._slide_cache

        # Tier 5 sprint 1 — TwoLevelTileCache lookup BEFORE OpenSlide extraction.
        # Cache key uses slide_id (stable identifier) so the same tile bytes
        # are reused across processes (L2 Redis is shared) and across slide
        # cache evictions in tile_server. tile_size hardcoded to 256 to match
        # tile_server.get_tile() default.
        tile_cache = getattr(request.app.state, "tile_cache", None)
        cache_lookup_t0 = time.monotonic()
        tile_bytes: bytes | None = None
        if tile_cache is not None:
            tile_bytes = await tile_cache.get_tile(slide_id, level, col, row, tile_size=256)
        cache_lookup_dt = time.monotonic() - cache_lookup_t0

        if tile_bytes is not None:
            # Cache hit — record metric and serve.
            record_tile_cache_lookup("hit", level, cache_lookup_dt)
        else:
            # Cache miss (or no cache configured) — render via tile_server,
            # then warm the cache for subsequent requests.
            record_tile_cache_lookup("miss", level, cache_lookup_dt)
            # tile_server.get_tile is sync (OpenSlide is C-bound). Run it in
            # a thread so the event loop stays free for other tile requests.
            import asyncio

            tile_bytes = await asyncio.to_thread(
                tile_server.get_tile, slide_path, level, col, row, 256
            )
            if tile_bytes is None:
                # Tuile hors limites (pas d'erreur, juste pas de contenu)
                raise HTTPException(404, "Tile out of bounds")
            # Write-through to L1 + L2. Best-effort: a Redis outage is logged
            # by RedisCache itself and degrades silently to L1-only.
            if tile_cache is not None:
                await tile_cache.set_tile(slide_id, level, col, row, 256, tile_bytes)

        # Emit SLIDE_VIEWED audit event (first access per user/slide/day only).
        # Fire-and-forget: must not block or fail tile serving.
        schedule_tile_audit(
            user_sub=current_user.sub,
            slide_id=slide_id,
            zoom_level=level,
            cache_hit=slide_cache_hit,
        )

        return Response(content=tile_bytes, media_type="image/jpeg")

    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except openslide.OpenSlideError as e:
        raise slide_open_error(slide_id, e)
    except Exception as e:
        raise internal_error("get_tile", e)  # noqa: EM101
