"""
Slide Loader Service
Extraction d'images depuis lames avec OpenSlide.

PRINCIPE SIMPLE - Phase 1:
On utilise OpenSlide.get_thumbnail() qui fait TOUT le travail automatiquement.
Pas de code complexe, pas de gestion manuelle des niveaux pyramidaux.

Documentation officielle:
- OpenSlide Python: https://openslide.org/api/python/
- get_thumbnail(): https://openslide.org/api/python/#openslide.OpenSlide.get_thumbnail
- Properties: https://openslide.org/api/python/#openslide.OpenSlide.properties
"""

import openslide
from openslide import OpenSlideError
from PIL import Image
from io import BytesIO
from typing import Dict


def get_slide_metadata(slide_path: str) -> Dict:
    """
    Extrait métadonnées d'une lame.

    Doc: https://openslide.org/api/python/#openslide.OpenSlide.properties

    Returns:
        {
            "dimensions": [width, height] (level 0),
            "level_count": int,
            "level_dimensions": [[w,h], ...],
            "level_downsamples": [1.0, 2.0, 4.0, ...],
            "vendor": str,
            "format": str
        }

    Technical Notes:
        - dimensions = niveau 0 (pleine résolution)
        - level_downsamples indique facteur réduction (ex: 2.0 = 50% taille)
        - vendor détecté via propriétés OpenSlide (ex: "3DHISTECH")
    """
    try:
        slide = openslide.OpenSlide(slide_path)

        metadata = {
            "dimensions": list(slide.dimensions),
            "level_count": slide.level_count,
            "level_dimensions": [list(d) for d in slide.level_dimensions],
            "level_downsamples": list(slide.level_downsamples),
            "vendor": slide.properties.get(openslide.PROPERTY_NAME_VENDOR, "Unknown"),
            "format": _detect_format(slide_path, slide)
        }

        slide.close()
        return metadata

    except OpenSlideError as e:
        raise RuntimeError(f"Cannot open slide: {e}")


def get_slide_overview_bytes(slide_path: str, max_size: int = 2000, quality: int = 85) -> bytes:
    """
    Extrait overview et retourne bytes JPEG.

    MÉTHODE SIMPLE - Phase 1:
    On utilise OpenSlide.get_thumbnail() qui fait TOUT automatiquement:
    - Choisit le meilleur niveau pyramidal
    - Extrait et redimensionne intelligemment
    - Gère TOUS les formats (.mrxs, .bif, .tif)

    Doc: https://openslide.org/api/python/#openslide.OpenSlide.get_thumbnail
    "Return a PIL.Image containing an RGB thumbnail of the slide."

    Args:
        slide_path: Chemin vers lame
        max_size: Dimension max (width ou height) en pixels
        quality: Qualité JPEG (1-100)

    Returns:
        bytes: Image JPEG encodée

    Technical Notes:
        - get_thumbnail() préserve aspect ratio
        - Retourne PIL.Image RGB (pas RGBA)
        - Optimisé automatiquement par OpenSlide (pas besoin cache Phase 1)
        - Pour .mrxs: OpenSlide gère fichiers compagnons automatiquement
    """
    try:
        # Ouvrir lame (OpenSlide détecte format et fichiers compagnons)
        slide = openslide.OpenSlide(slide_path)

        # SIMPLE: get_thumbnail() fait tout le boulot
        # Passe tuple (max_width, max_height), préserve aspect ratio
        overview = slide.get_thumbnail((max_size, max_size))

        # Fermer slide
        slide.close()

        # Convertir PIL.Image en JPEG bytes
        buffer = BytesIO()
        overview.save(buffer, format='JPEG', quality=quality, optimize=True)
        return buffer.getvalue()

    except OpenSlideError as e:
        raise RuntimeError(f"Cannot extract overview: {e}")


def _detect_format(slide_path: str, slide: openslide.OpenSlide) -> str:
    """
    Détecte format depuis vendor ou extension.

    Technical Notes:
        - Vendor provient des métadonnées embarquées dans la lame
        - Fallback sur extension si vendor inconnu
    """
    vendor = slide.properties.get(openslide.PROPERTY_NAME_VENDOR, "")

    if "3DHISTECH" in vendor.upper():
        return "3DHistech MRXS"
    elif "Ventana" in vendor or "Roche" in vendor:
        return "Roche/Ventana BIF"
    elif slide_path.endswith('.tif') or slide_path.endswith('.tiff'):
        return "Generic TIFF"
    else:
        return f"Unknown ({vendor})"
