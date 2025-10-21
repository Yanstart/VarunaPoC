"""
Folder Browser Service

Service de navigation hiérarchique dans le répertoire /Slides.

Fonctionnalités:
- Navigation dossier par dossier (non-récursive)
- Détection des slides avec format_detector
- Sécurité: path traversal bloqué
- Support fichiers sans extension (marqués non supportés)

Voir: docs/USER_GUIDE_SLIDE_STRUCTURE.md pour règles complètes
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from services.format_detector import FormatDetector

# Répertoire racine des slides (configurable)
SLIDES_ROOT = Path(__file__).parent.parent.parent / "Slides"


def is_safe_path(requested_path: str) -> bool:
    """
    Vérifie qu'un chemin est sûr (pas de path traversal).

    Args:
        requested_path: Chemin relatif demandé (ex: "/3DHistech")

    Returns:
        True si le chemin est sûr, False sinon

    Security:
        Bloque les tentatives de path traversal:
        - ../../../etc/passwd
        - /3DHistech/../../Windows/System32

    Examples:
        >>> is_safe_path("/3DHistech")
        True
        >>> is_safe_path("/../etc/passwd")
        False
    """
    try:
        # Normaliser le chemin (convertir backslashes en forward slashes)
        normalized_path = requested_path.replace('\\', '/')

        # Construire le chemin absolu résolu
        full_path = (SLIDES_ROOT / normalized_path.lstrip("/")).resolve()

        # Vérifier qu'il est bien sous SLIDES_ROOT
        return full_path.is_relative_to(SLIDES_ROOT.resolve())
    except (ValueError, OSError):
        return False


def get_breadcrumb(path: str) -> List[str]:
    """
    Génère le fil d'Ariane pour un chemin.

    Args:
        path: Chemin relatif (ex: "/projects/2024/lung")

    Returns:
        Liste des segments du chemin

    Examples:
        >>> get_breadcrumb("/projects/2024/lung")
        ["/", "/projects", "/projects/2024", "/projects/2024/lung"]
    """
    if path == "/":
        return ["/"]

    segments = ["/"]
    parts = path.strip("/").split("/")

    current = ""
    for part in parts:
        current += "/" + part
        segments.append(current)

    return segments


def count_items_in_folder(folder_path: Path) -> int:
    """
    Compte le nombre d'items (fichiers + dossiers) dans un dossier.

    Args:
        folder_path: Chemin absolu du dossier

    Returns:
        Nombre d'items (0 si erreur)
    """
    try:
        return len(list(folder_path.iterdir()))
    except (PermissionError, OSError):
        return 0


def generate_slide_id(file_path: Path) -> str:
    """
    Génère un ID unique pour une lame (hash MD5 du chemin).

    IMPORTANT: Doit utiliser la MÊME méthode que slide_scanner.py
    pour garantir cohérence des IDs entre browse et scan complet.

    Args:
        file_path: Chemin absolu du fichier

    Returns:
        Hash MD5 tronqué (12 premiers caractères hexadécimaux)

    Examples:
        >>> generate_slide_id(Path("/Slides/3DHistech/sample.mrxs"))
        "a1b2c3d4e5f6"
    """
    path_str = str(file_path)  # Utiliser le même que slide_scanner (pas .resolve())
    return hashlib.md5(path_str.encode()).hexdigest()[:12]  # Tronquer à 12 caractères


def browse_directory(relative_path: str = "/") -> Dict:
    """
    Navigue dans un dossier de /Slides et détecte son contenu.

    Args:
        relative_path: Chemin relatif depuis /Slides (ex: "/", "/3DHistech")

    Returns:
        Dictionnaire avec:
        - current_path: Chemin actuel
        - parent_path: Chemin parent (None si racine)
        - breadcrumb: Fil d'Ariane
        - folders: Liste des sous-dossiers
        - slides: Liste des lames détectées
        - files: Liste des fichiers non-slides

    Raises:
        PermissionError: Path traversal ou chemin invalide
        FileNotFoundError: Dossier introuvable

    Technical Notes:
        - Lecture NON récursive (un seul niveau)
        - Utilise format_detector pour identifier les slides
        - Fichiers sans extension marqués non supportés
        - Les dossiers companions (.mrxs/) sont détectés mais pas listés séparément

    Examples:
        >>> browse_directory("/")
        {
            "current_path": "/",
            "parent_path": None,
            "breadcrumb": ["/"],
            "folders": [{"name": "3DHistech", "path": "/3DHistech", "item_count": 5}],
            "slides": [...],
            "files": [...]
        }
    """
    # Normaliser le chemin (convertir backslashes en forward slashes)
    normalized_path = relative_path.replace('\\', '/')

    # Validation sécurité
    if not is_safe_path(normalized_path):
        raise PermissionError(f"Path traversal attempt detected: {relative_path}")

    # Construire le chemin absolu
    current_dir = SLIDES_ROOT / normalized_path.lstrip("/")

    if not current_dir.exists():
        raise FileNotFoundError(f"Directory not found: {normalized_path}")

    if not current_dir.is_dir():
        raise ValueError(f"Not a directory: {normalized_path}")

    # Calculer le chemin parent
    if normalized_path == "/":
        parent_path = None
    else:
        parent = str(Path(normalized_path).parent)
        parent_path = "/" if parent == "." else parent

    # Fil d'Ariane
    breadcrumb = get_breadcrumb(normalized_path)

    # Initialiser les listes de résultats
    folders = []
    slides = []
    files = []

    # Initialiser le détecteur de format
    detector = FormatDetector()

    # Ensemble des fichiers/dossiers déjà traités (pour éviter doublons)
    processed = set()

    # Scanner le contenu du dossier
    for item in sorted(current_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        item_name = item.name

        # Ignorer les fichiers cachés et système
        if item_name.startswith(".") or item_name.startswith("__"):
            continue

        # Chemin relatif de l'item (utiliser forward slashes)
        item_relative_path = str(Path(normalized_path) / item_name).replace('\\', '/')

        if item.is_dir():
            # Vérifier si c'est un dossier companion (ex: sample.mrxs/)
            # Si oui, ne pas le lister comme dossier normal
            parent_file = current_dir / f"{item_name}.mrxs"
            if parent_file.exists():
                # C'est un companion directory pour un fichier .mrxs
                # On ne le liste pas séparément
                processed.add(item_name)
                continue

            # Dossier normal
            folders.append({
                "name": item_name,
                "path": item_relative_path,
                "item_count": count_items_in_folder(item)
            })
            processed.add(item_name)

        elif item.is_file():
            # Ignorer si déjà traité (ex: fichier .vmu associé à .vms)
            if item_name in processed:
                continue

            # Tenter de détecter le format
            slide_format = detector.detect_format(item)

            if slide_format:
                # C'est une lame valide (ou potentiellement valide)
                slides.append({
                    "name": item_name,
                    "path": str(item.relative_to(SLIDES_ROOT)),
                    "id": generate_slide_id(item),
                    "format_string": slide_format.format_string or "Unknown",
                    "structure_type": slide_format.structure_type,
                    "is_supported": slide_format.is_supported,
                    "notes": slide_format.notes,
                    "dependencies": _get_dependency_paths(item, slide_format)
                })

                # Marquer les fichiers associés comme traités
                if slide_format.structure_type == "multi-file":
                    # Ex: .vms a un .vmu associé
                    vmu_file = current_dir / f"{item.stem}.vmu"
                    if vmu_file.exists():
                        processed.add(vmu_file.name)

                elif slide_format.structure_type == "with-companion-dir":
                    # Ex: .mrxs a un dossier companion
                    companion_dir = current_dir / item.stem
                    if companion_dir.exists():
                        processed.add(companion_dir.name)

                processed.add(item_name)

            else:
                # Fichier non reconnu
                extension = item.suffix if item.suffix else None

                files.append({
                    "name": item_name,
                    "extension": extension,
                    "is_supported": False,
                    "notes": "Unknown format - no extension or unsupported" if not extension else f"Extension {extension} not recognized"
                })
                processed.add(item_name)

    return {
        "current_path": normalized_path,
        "parent_path": parent_path,
        "breadcrumb": breadcrumb,
        "folders": folders,
        "slides": slides,
        "files": files
    }


def _get_dependency_paths(entry_point: Path, slide_format) -> List[str]:
    """
    Liste les chemins relatifs des dépendances d'une lame.

    Args:
        entry_point: Fichier principal de la lame
        slide_format: Objet SlideFormat retourné par le détecteur

    Returns:
        Liste des chemins relatifs des fichiers/dossiers associés

    Examples:
        Pour sample.mrxs:
        ["Slides/3DHistech/sample/"]

        Pour slide.vms:
        ["Slides/3DHistech/slide.vmu"]
    """
    dependencies = []

    if slide_format.structure_type == "multi-file":
        # Ex: .vms nécessite .vmu
        vmu_file = entry_point.parent / f"{entry_point.stem}.vmu"
        if vmu_file.exists():
            dependencies.append(str(vmu_file.relative_to(SLIDES_ROOT)))

    elif slide_format.structure_type == "with-companion-dir":
        # Ex: .mrxs nécessite dossier companion
        companion_dir = entry_point.parent / entry_point.stem
        if companion_dir.exists():
            dependencies.append(str(companion_dir.relative_to(SLIDES_ROOT)) + "/")

    return dependencies
