"""
Slide Scanner Service
Détecte automatiquement les lames dans le dossier Slides/.

Formats supportés:
- .mrxs (3DHistech) - nécessite répertoire compagnon
- .bif (Roche/Ventana)
- .tif (Generic TIFF)

Documentation:
- pathlib: https://docs.python.org/3/library/pathlib.html
"""

from pathlib import Path
from typing import List, Dict
import hashlib


def scan_slides_directory(slides_dir: str = "../Slides") -> List[Dict]:
    """
    Scan récursif du dossier Slides/ pour détecter les lames.

    Args:
        slides_dir: Chemin relatif vers dossier Slides

    Returns:
        Liste de dicts:
        {
            "id": str (hash du path),
            "name": str (nom fichier),
            "path": str (chemin absolu),
            "format": str (extension),
            "has_companions": bool (True si .mrxs avec dossier compagnon)
        }

    Technical Notes:
        - Scan récursif pour supporter sous-dossiers (3Dhistec/, ROCHE/)
        - Hash MD5 du path pour ID unique et stable
        - Vérifie structure compagnon pour .mrxs (CRITICAL pour OpenSlide)
    """
    slides_path = Path(slides_dir).resolve()

    if not slides_path.exists():
        return []

    slides = []
    supported_extensions = ['.mrxs', '.bif', '.tif', '.tiff']

    # Scan récursif de tous les fichiers
    for slide_file in slides_path.rglob('*'):
        if slide_file.suffix.lower() in supported_extensions:

            # Vérifier compagnons pour .mrxs
            # Structure attendue: slide.mrxs + slide/ (contient Slidedat.ini, Data*.dat)
            has_companions = False
            if slide_file.suffix.lower() == '.mrxs':
                companion_dir = slide_file.parent / slide_file.stem
                has_companions = companion_dir.exists() and companion_dir.is_dir()

            # Générer ID unique (hash du path absolu)
            slide_id = hashlib.md5(str(slide_file).encode()).hexdigest()[:12]

            slides.append({
                "id": slide_id,
                "name": slide_file.name,
                "path": str(slide_file),
                "format": slide_file.suffix.lower().replace('.', ''),
                "has_companions": has_companions
            })

    return slides


# Cache simple pour ID->Path mapping (évite rescans répétés)
_slide_cache = {}


def get_slide_path_by_id(slide_id: str) -> str:
    """
    Trouve le path d'une lame depuis son ID.
    Utilise un cache simple pour éviter rescans répétés.

    Args:
        slide_id: ID de la lame (hash MD5)

    Returns:
        str: Chemin absolu vers la lame, ou None si introuvable

    Technical Notes:
        - Cache global rempli au premier appel
        - Reste en mémoire pendant session serveur
        - Redémarrer serveur pour forcer rescan
    """
    global _slide_cache

    if not _slide_cache:
        # Premier appel: remplir cache
        slides = scan_slides_directory()
        _slide_cache = {s['id']: s['path'] for s in slides}

    return _slide_cache.get(slide_id)
