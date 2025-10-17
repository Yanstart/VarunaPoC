"""
Slide Scanner Service - Version 1.5
Utilise FormatDetector pour détection robuste multi-format.

NOUVEAUTÉ Phase 1.5:
- Détection intelligente basée sur documentation OpenSlide officielle
- Support complet des structures multi-fichiers (VMS, VMU, MIRAX, etc.)
- Validation avec OpenSlide.detect_format() comme autorité finale
- Métadonnées enrichies (structure_type, fichiers joints, etc.)

Author: VarunaPoC Team
Version: 1.5.0
"""

from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import logging
from services.format_detector import FormatDetector

logger = logging.getLogger(__name__)


def scan_slides_directory(slides_dir: str = "../Slides") -> List[Dict]:
    """
    Scan ROBUSTE avec détection de structure multi-format.

    RETOURNE SEULEMENT:
    - Lames supportées par OpenSlide
    - Lames validées par detect_format()
    - Avec structures complètes (fichiers joints, companions)

    Args:
        slides_dir: Chemin vers dossier Slides

    Returns:
        Liste de dicts avec métadonnées enrichies:
        {
            "id": str (hash MD5 unique),
            "name": str (nom fichier point d'entrée),
            "path": str (chemin absolu point d'entrée),
            "format": str (nom lisible - "Hamamatsu VMS", "MIRAX", etc.),
            "format_string": str (retour OpenSlide - "hamamatsu", "mirax", etc.),
            "structure_type": str ("single-file", "multi-file", "with-companion-dir"),
            "has_joint_files": bool,
            "joint_files_count": int,
            "has_companion_dirs": bool,
            "companion_dirs_count": int,
            "detection_method": str (méthode utilisée pour debug),
            "is_validated": bool (toujours True - filtre fait avant),
            "notes": str (infos additionnelles)
        }

    Technical Notes:
        - Utilise FormatDetector basé sur https://openslide.org/formats/
        - Seules les lames passant detect_format() sont retournées
        - Fichiers .jpg/.dat isolés (non liés à VMS/MIRAX) sont ignorés
        - Performance: O(n) avec n = nombre total de fichiers
    """
    slides_path = Path(slides_dir).resolve()

    if not slides_path.exists():
        logger.warning(f"Slides directory not found: {slides_path}")
        return []

    # Créer détecteur
    detector = FormatDetector()

    # Scan complet
    detected_formats = detector.scan_directory(slides_path, recursive=True)

    # Convertir en format API
    slides = []
    for slide_format in detected_formats:
        # Générer ID stable (hash du path point d'entrée)
        slide_id = hashlib.md5(str(slide_format.entry_point).encode()).hexdigest()[:12]

        slides.append({
            "id": slide_id,
            "name": slide_format.entry_point.name,
            "path": str(slide_format.entry_point),
            "format": slide_format.name,
            "format_string": slide_format.format_string if slide_format.format_string else "unknown",
            "structure_type": slide_format.structure_type,
            "has_joint_files": len(slide_format.joint_files) > 0,
            "joint_files_count": len(slide_format.joint_files),
            "has_companion_dirs": len(slide_format.companion_dirs) > 0,
            "companion_dirs_count": len(slide_format.companion_dirs),
            "detection_method": slide_format.detection_method,
            "is_supported": slide_format.is_supported,  # Phase 1.5.1: inclure supporté/non supporté
            "notes": slide_format.notes
        })

    logger.info(f"Scan complete: {len(slides)} validated slides ready for API")
    return slides


# Cache ID->Path (évite rescans répétés)
_slide_cache = {}


def get_slide_path_by_id(slide_id: str) -> Optional[str]:
    """
    Trouve path depuis ID.

    Args:
        slide_id: ID unique (hash MD5)

    Returns:
        Chemin absolu vers point d'entrée, ou None

    Technical Notes:
        - Cache rempli au premier appel
        - Redémarrer serveur pour forcer rescan
        - Retourne toujours le POINT D'ENTRÉE (pas fichiers joints)
    """
    global _slide_cache

    if not _slide_cache:
        # Premier appel: remplir cache
        slides = scan_slides_directory()
        _slide_cache = {s['id']: s['path'] for s in slides}

    return _slide_cache.get(slide_id)
