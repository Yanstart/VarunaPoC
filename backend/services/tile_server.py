"""
Tile Server Service

Service de streaming de tuiles pour OpenSeadragon.

Fonctionnalités:
- Extraction de tuiles à la demande depuis OpenSlide
- Support multi-niveaux pyramidaux
- Conversion RGBA → RGB (OpenSlide retourne RGBA)
- Optimisation mémoire (pas de chargement complet)

Formats supportés (Phase 2):
- .bif (Ventana BIF)
- .tif/.tiff (Generic TIFF)
- .mrxs (3DHistech MIRAX)

Technical Notes:
- OpenSlide utilise coordonnées niveau 0 pour read_region()
- Tuiles retournées en JPEG (compression optimale)
- Taille tuile standard: 256x256 pixels

Voir: docs/CLAUDE.md section "Coordinate Mapping"
"""

import io
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import openslide
import logging

logger = logging.getLogger(__name__)


class TileServer:
    """
    Serveur de tuiles pour streaming OpenSeadragon.

    Gère l'ouverture des slides et l'extraction de tuiles à la demande.
    """

    def __init__(self):
        """Initialize tile server with slide cache."""
        self._slide_cache = {}  # Cache des slides ouverts {path: OpenSlide}
        self._max_cache_size = 5  # Max 5 slides en cache

    def get_slide(self, slide_path: str) -> openslide.OpenSlide:
        """
        Récupère ou ouvre un slide (avec cache).

        Args:
            slide_path: Chemin absolu vers le fichier slide

        Returns:
            Instance OpenSlide ouverte

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            openslide.OpenSlideError: Si impossible d'ouvrir le slide

        Technical Notes:
            - Cache les slides ouverts pour réutilisation
            - Limite à max_cache_size slides simultanés
            - Ferme le plus ancien si cache plein
        """
        if slide_path in self._slide_cache:
            logger.debug(f"Slide cache hit: {Path(slide_path).name}")
            return self._slide_cache[slide_path]

        # Vérifier que le fichier existe
        if not Path(slide_path).exists():
            raise FileNotFoundError(f"Slide not found: {slide_path}")

        # Ouvrir le slide
        logger.info(f"Opening slide: {Path(slide_path).name}")
        slide = openslide.OpenSlide(slide_path)

        # Ajouter au cache
        if len(self._slide_cache) >= self._max_cache_size:
            # Cache plein, supprimer le plus ancien
            oldest_path = next(iter(self._slide_cache))
            logger.info(f"Cache full, closing: {Path(oldest_path).name}")
            self._slide_cache[oldest_path].close()
            del self._slide_cache[oldest_path]

        self._slide_cache[slide_path] = slide
        return slide

    def get_tile(
        self,
        slide_path: str,
        level: int,
        col: int,
        row: int,
        tile_size: int = 256
    ) -> Optional[bytes]:
        """
        Extrait une tuile depuis un slide.

        Args:
            slide_path: Chemin absolu vers le fichier slide
            level: Niveau pyramidal (0 = haute résolution)
            col: Colonne de la tuile (x / tile_size)
            row: Ligne de la tuile (y / tile_size)
            tile_size: Taille de la tuile en pixels (défaut: 256)

        Returns:
            Bytes JPEG de la tuile, ou None si hors limites

        Technical Notes:
            - Coordonnées converties en coordonnées niveau 0 pour OpenSlide
            - RGBA converti en RGB (OpenSlide retourne RGBA)
            - Tuiles hors limites retournent None (pas d'erreur)
            - JPEG quality=85 pour compromis taille/qualité

        Examples:
            >>> get_tile("slide.mrxs", level=2, col=5, row=3)
            b'\xff\xd8\xff\xe0...'  # JPEG bytes
        """
        try:
            slide = self.get_slide(slide_path)

            # Vérifier que le niveau existe
            if level < 0 or level >= slide.level_count:
                logger.warning(f"Invalid level {level} (max: {slide.level_count-1})")
                return None

            # Calculer coordonnées niveau 0 (OpenSlide requirement)
            downsample = slide.level_downsamples[level]

            # Coordonnées tuile au niveau demandé
            x_tile = col * tile_size
            y_tile = row * tile_size

            # Convertir en coordonnées niveau 0
            x_level0 = int(x_tile * downsample)
            y_level0 = int(y_tile * downsample)

            # Dimensions du slide au niveau demandé
            level_width, level_height = slide.level_dimensions[level]

            # Vérifier si tuile hors limites
            if x_tile >= level_width or y_tile >= level_height:
                logger.debug(f"Tile out of bounds: level={level}, col={col}, row={row}")
                return None

            # Calculer taille réelle de la tuile (dernière tuile peut être plus petite)
            actual_width = min(tile_size, level_width - x_tile)
            actual_height = min(tile_size, level_height - y_tile)

            # Extraire la région depuis OpenSlide
            # read_region retourne RGBA PIL Image
            region = slide.read_region(
                location=(x_level0, y_level0),
                level=level,
                size=(actual_width, actual_height)
            )

            # Convertir RGBA → RGB (OpenSeadragon préfère RGB)
            rgb_region = region.convert('RGB')

            # Si tuile incomplète (bord), créer image complète avec fond noir
            if actual_width < tile_size or actual_height < tile_size:
                full_tile = Image.new('RGB', (tile_size, tile_size), (0, 0, 0))
                full_tile.paste(rgb_region, (0, 0))
                rgb_region = full_tile

            # Encoder en JPEG
            buffer = io.BytesIO()
            rgb_region.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)

            return buffer.getvalue()

        except openslide.OpenSlideError as e:
            logger.error(f"OpenSlide error extracting tile: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting tile: {e}")
            return None

    def get_dzi_metadata(self, slide_path: str) -> dict:
        """
        Génère métadonnées DZI pour OpenSeadragon.

        Args:
            slide_path: Chemin absolu vers le fichier slide

        Returns:
            Dictionnaire avec métadonnées DZI:
            {
                "width": int,           # Largeur niveau 0
                "height": int,          # Hauteur niveau 0
                "tile_size": int,       # Taille tuile (256)
                "overlap": int,         # Overlap (0 pour simplifier)
                "format": str,          # "jpeg"
                "levels": int,          # Nombre de niveaux
                "level_dimensions": [[w,h], ...]
            }

        Technical Notes:
            - Format compatible OpenSeadragon DziTileSource
            - Overlap=0 pour simplifier (pas de chevauchement tuiles)
            - tile_size=256 (standard OpenSeadragon)
        """
        slide = self.get_slide(slide_path)

        width, height = slide.dimensions  # Niveau 0

        return {
            "width": width,
            "height": height,
            "tile_size": 256,
            "overlap": 0,
            "format": "jpeg",
            "levels": slide.level_count,
            "level_dimensions": list(slide.level_dimensions),
            "level_downsamples": list(slide.level_downsamples)
        }

    def close_all(self):
        """Ferme tous les slides en cache."""
        for path, slide in self._slide_cache.items():
            logger.info(f"Closing cached slide: {Path(path).name}")
            slide.close()
        self._slide_cache.clear()

    def __del__(self):
        """Cleanup au garbage collection."""
        self.close_all()


# Instance globale (singleton)
tile_server = TileServer()
