"""
Format Detector Service
Détecte et valide structures multi-fichiers OpenSlide.

Documentation officielle (SOURCE DE VÉRITÉ):
- Formats: https://openslide.org/formats/
- API: https://openslide.org/api/python/

TERMINOLOGIE CORRECTE:
- FICHIERS JOINTS: Fichiers additionnels requis (même niveau ou sous-dossiers)
- POINT D'ENTRÉE: Fichier à passer à OpenSlide() - trouve les autres automatiquement
- FICHIERS MÉTADONNÉES: Fichiers contenant métadonnées (souvent le point d'entrée)

Author: VarunaPoC Team
Version: 1.5.0
"""

import openslide
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SlideFormat:
    """
    Format de lame détecté avec structure complète.

    Attributes:
        name: Nom lisible du format (ex: "Hamamatsu VMS", "MIRAX")
        entry_point: Fichier à passer à OpenSlide()
        is_supported: True si OpenSlide peut l'ouvrir
        joint_files: Fichiers JOINTS requis
        companion_dirs: Dossiers compagnons
        metadata_files: Fichiers métadonnées
        format_string: Retour de detect_format() ("hamamatsu", "mirax", etc.)
        structure_type: Type de structure ("single-file", "multi-file", "with-companion-dir")
        detection_method: Méthode de détection (pour debug)
        notes: Informations additionnelles
    """
    name: str
    entry_point: Path
    is_supported: bool
    joint_files: List[Path] = field(default_factory=list)
    companion_dirs: List[Path] = field(default_factory=list)
    metadata_files: List[Path] = field(default_factory=list)
    format_string: Optional[str] = None
    structure_type: str = "unknown"
    detection_method: str = ""
    notes: str = ""


class FormatDetector:
    """
    Détecteur intelligent de formats OpenSlide.

    Basé sur documentation officielle OpenSlide.
    Utilise detect_format() comme validation FINALE.

    References:
        - https://openslide.org/formats/
        - https://openslide.org/api/python/#openslide.OpenSlide.detect_format
    """

    def __init__(self):
        self.detected_entries: Set[str] = set()  # Éviter duplicata
        self.scan_stats = {
            'scanned': 0,
            'detected': 0,
            'ignored': 0,
            'errors': 0
        }

    def detect_format(self, file_path: Path) -> Optional[SlideFormat]:
        """
        Détecte format d'une lame depuis un fichier.

        Process:
            1. Vérifie extension/structure
            2. Recherche fichiers joints/compagnons requis
            3. Valide avec OpenSlide.detect_format()
            4. Construit SlideFormat complet

        Args:
            file_path: Chemin vers fichier candidat

        Returns:
            SlideFormat si valide et supporté, None sinon

        Notes:
            - Incrémente scan_stats automatiquement
            - Évite détection multiple du même entry_point
        """
        self.scan_stats['scanned'] += 1

        if not file_path.exists() or not file_path.is_file():
            return None

        # Éviter duplicata
        if str(file_path.resolve()) in self.detected_entries:
            return None

        ext = file_path.suffix.lower()

        # Dispatch par extension
        detector_map = {
            '.vms': self._detect_hamamatsu_vms,
            '.vmu': self._detect_hamamatsu_vmu,
            '.ndpi': self._detect_hamamatsu_ndpi,
            '.mrxs': self._detect_mirax,
            '.svs': self._detect_aperio,
            '.scn': self._detect_leica,
            '.bif': self._detect_ventana_bif,
            '.svslide': self._detect_sakura,
            '.czi': self._detect_zeiss_czi,
            '.tif': self._detect_tiff_variant,
            '.tiff': self._detect_tiff_variant,
        }

        detector_func = detector_map.get(ext)
        if detector_func:
            result = detector_func(file_path)
            if result:
                self.scan_stats['detected'] += 1
                self.detected_entries.add(str(file_path.resolve()))
                if result.is_supported:
                    logger.info(f"[OK] Detected: {result.name} - {file_path.name}")
                else:
                    logger.warning(f"[UNSUPPORTED] Detected but cannot open: {result.name} - {file_path.name}")
            else:
                self.scan_stats['ignored'] += 1
                logger.debug(f"[X] Ignored: {file_path.name} (not a slide format)")
            return result

        # Extension inconnue - essayer détection par contenu
        self.scan_stats['ignored'] += 1
        logger.debug(f"✗ Unknown extension: {file_path.name}")
        return None

    # =========================================================================
    # HAMAMATSU FORMATS
    # Doc: https://openslide.org/formats/hamamatsu/
    # =========================================================================

    def _detect_hamamatsu_vms(self, vms_file: Path) -> Optional[SlideFormat]:
        """
        Hamamatsu VMS - Multi-file JPEG.

        Structure:
            - slide.vms (POINT D'ENTRÉE - fichier INI avec métadonnées)
            - slide(x,y).jpg (FICHIERS JOINTS - images pyramidales multiples)
            - slide.opt (FICHIER JOINT - optimisation JPEG offsets, optionnel)

        OpenSlide usage:
            OpenSlide("slide.vms") → trouve automatiquement les .jpg via clés INI

        Doc: https://openslide.org/formats/hamamatsu/
        """
        logger.debug(f"Checking Hamamatsu VMS: {vms_file.name}")

        # Vérifier que c'est un fichier INI VMS valide
        if not self._is_vms_ini_file(vms_file):
            return None

        # Chercher fichiers JOINTS .jpg dans même dossier
        jpg_pattern = f"{vms_file.stem}*.jpg"
        jpg_files = list(vms_file.parent.glob(jpg_pattern))

        # Exclure les fichiers macro/map (pas des tuiles)
        jpg_files = [f for f in jpg_files if '_macro' not in f.stem and '_map' not in f.stem]

        if len(jpg_files) == 0:
            logger.warning(f"VMS without JPEG joints: {vms_file.name}")
            return None

        # Chercher fichier .opt (optionnel)
        opt_file = vms_file.with_suffix('.opt')
        joint_files = jpg_files.copy()
        if opt_file.exists():
            joint_files.append(opt_file)

        # Validation FINALE avec OpenSlide
        format_str = self._validate_with_openslide(vms_file)
        if format_str is None:
            logger.warning(f"OpenSlide rejected VMS: {vms_file.name}")
            return None

        return SlideFormat(
            name="Hamamatsu VMS",
            entry_point=vms_file,
            is_supported=True,
            joint_files=joint_files,
            companion_dirs=[],
            metadata_files=[vms_file],
            format_string=format_str,
            structure_type="multi-file",
            detection_method="VMS INI validation + JPEG joints detection",
            notes=f"VMS index with {len(jpg_files)} JPEG tiles" + (", .opt file present" if opt_file.exists() else "")
        )

    def _detect_hamamatsu_vmu(self, vmu_file: Path) -> Optional[SlideFormat]:
        """
        Hamamatsu VMU - Multi-file NGR (uncompressed).
        Similar to VMS but with .ngr image files.

        Doc: https://openslide.org/formats/hamamatsu/
        """
        logger.debug(f"Checking Hamamatsu VMU: {vmu_file.name}")

        if not self._is_vmu_ini_file(vmu_file):
            return None

        # Chercher fichiers .ngr
        ngr_pattern = f"{vmu_file.stem}*.ngr"
        ngr_files = list(vmu_file.parent.glob(ngr_pattern))

        # Exclure macro/map
        ngr_files = [f for f in ngr_files if '_macro' not in f.stem and '_map' not in f.stem]

        if len(ngr_files) == 0:
            logger.warning(f"VMU without NGR joints: {vmu_file.name}")
            return None

        format_str = self._validate_with_openslide(vmu_file)
        if format_str is None:
            return None

        return SlideFormat(
            name="Hamamatsu VMU",
            entry_point=vmu_file,
            is_supported=True,
            joint_files=ngr_files,
            companion_dirs=[],
            metadata_files=[vmu_file],
            format_string=format_str,
            structure_type="multi-file",
            detection_method="VMU INI validation + NGR joints detection",
            notes=f"VMU index with {len(ngr_files)} NGR tiles (uncompressed)"
        )

    def _detect_hamamatsu_ndpi(self, ndpi_file: Path) -> Optional[SlideFormat]:
        """
        Hamamatsu NDPI - Single-file TIFF-like.
        Pas de fichiers joints requis.

        Doc: https://openslide.org/formats/hamamatsu/
        """
        format_str = self._validate_with_openslide(ndpi_file)
        if format_str is None:
            return None

        return SlideFormat(
            name="Hamamatsu NDPI",
            entry_point=ndpi_file,
            is_supported=True,
            joint_files=[],
            companion_dirs=[],
            metadata_files=[],
            format_string=format_str,
            structure_type="single-file",
            detection_method="OpenSlide detect_format validation",
            notes="Single TIFF-like file, no joints required"
        )

    # =========================================================================
    # MIRAX (3DHISTECH)
    # Doc: https://openslide.org/formats/mirax/
    # =========================================================================

    def _detect_mirax(self, mrxs_file: Path) -> Optional[SlideFormat]:
        """
        MIRAX (3DHistech) - Multi-file with companion directory.

        Structure CRITIQUE:
            - slide.mrxs (POINT D'ENTRÉE - petit index file)
            - slide/ (DOSSIER COMPAGNON - même nom sans extension)
                ├── Slidedat.ini (REQUIS - métadonnées)
                ├── Data0000.dat (REQUIS - tuiles images, multiples)
                ├── Data0001.dat
                └── Index.dat (index tuiles)

        OpenSlide usage:
            OpenSlide("slide.mrxs") → trouve automatiquement le dossier slide/

        Doc: https://openslide.org/formats/mirax/
        """
        logger.debug(f"Checking MIRAX: {mrxs_file.name}")

        # Vérifier dossier compagnon (même nom sans extension)
        companion_dir = mrxs_file.parent / mrxs_file.stem
        if not companion_dir.exists() or not companion_dir.is_dir():
            logger.warning(f"MIRAX missing companion dir: {mrxs_file.name} (expected: {companion_dir.name}/)")
            return None

        # Vérifier Slidedat.ini REQUIS
        slidedat = companion_dir / "Slidedat.ini"
        if not slidedat.exists():
            logger.warning(f"MIRAX companion dir missing Slidedat.ini: {companion_dir.name}/")
            return None

        # Vérifier fichiers Data*.dat REQUIS
        dat_files = list(companion_dir.glob("Data*.dat"))
        if len(dat_files) == 0:
            logger.warning(f"MIRAX companion dir missing Data*.dat files: {companion_dir.name}/")
            return None

        # Validation avec OpenSlide
        format_str = self._validate_with_openslide(mrxs_file)
        if format_str is None:
            logger.warning(f"OpenSlide rejected MIRAX: {mrxs_file.name}")
            return None

        # Tous les fichiers du companion dir sont "joints"
        all_companion_files = list(companion_dir.glob("*"))

        return SlideFormat(
            name="MIRAX",
            entry_point=mrxs_file,
            is_supported=True,
            joint_files=all_companion_files,
            companion_dirs=[companion_dir],
            metadata_files=[slidedat],
            format_string=format_str,
            structure_type="with-companion-dir",
            detection_method="MRXS index + companion dir validation + Slidedat.ini check",
            notes=f"MRXS index with companion dir '{companion_dir.name}/' containing {len(dat_files)} Data files"
        )

    # =========================================================================
    # SINGLE-FILE FORMATS
    # =========================================================================

    def _detect_aperio(self, svs_file: Path) -> Optional[SlideFormat]:
        """
        Aperio SVS - Single-file TIFF.
        Doc: https://openslide.org/formats/aperio/
        """
        format_str = self._validate_with_openslide(svs_file)
        if format_str is None:
            return None

        return SlideFormat(
            name="Aperio SVS",
            entry_point=svs_file,
            is_supported=True,
            joint_files=[],
            companion_dirs=[],
            metadata_files=[],
            format_string=format_str,
            structure_type="single-file",
            detection_method="OpenSlide detect_format validation",
            notes="Single-file TIFF format"
        )

    def _detect_leica(self, scn_file: Path) -> Optional[SlideFormat]:
        """
        Leica SCN - Single BigTIFF.
        Doc: https://openslide.org/formats/leica/
        """
        format_str = self._validate_with_openslide(scn_file)
        if format_str is None:
            return None

        return SlideFormat(
            name="Leica SCN",
            entry_point=scn_file,
            is_supported=True,
            joint_files=[],
            companion_dirs=[],
            metadata_files=[],
            format_string=format_str,
            structure_type="single-file",
            detection_method="OpenSlide detect_format validation",
            notes="Single BigTIFF file"
        )

    def _detect_ventana_bif(self, bif_file: Path) -> Optional[SlideFormat]:
        """
        Ventana BIF - Single-file.
        Doc: https://openslide.org/formats/ventana/
        """
        format_str = self._validate_with_openslide(bif_file)
        if format_str is None:
            return None

        return SlideFormat(
            name="Ventana BIF",
            entry_point=bif_file,
            is_supported=True,
            joint_files=[],
            companion_dirs=[],
            metadata_files=[],
            format_string=format_str,
            structure_type="single-file",
            detection_method="OpenSlide detect_format validation",
            notes="Single-file BIF format"
        )

    def _detect_sakura(self, svslide_file: Path) -> Optional[SlideFormat]:
        """
        Sakura - SQLite database.
        Doc: https://openslide.org/formats/sakura/
        """
        format_str = self._validate_with_openslide(svslide_file)
        if format_str is None:
            return None

        return SlideFormat(
            name="Sakura",
            entry_point=svslide_file,
            is_supported=True,
            joint_files=[],
            companion_dirs=[],
            metadata_files=[],
            format_string=format_str,
            structure_type="single-file",
            detection_method="OpenSlide detect_format validation",
            notes="SQLite database format"
        )

    # =========================================================================
    # ZEISS CZI
    # Doc: https://openslide.org/formats/zeiss/
    # =========================================================================

    def _detect_zeiss_czi(self, czi_file: Path) -> Optional[SlideFormat]:
        """
        Zeiss CZI - Single-file binary format with overlaps.

        Structure:
            - slide.czi (single file containing everything)
            - May use JPEG XR, Zstandard, or uncompressed data

        IMPORTANT NOTE:
            CZI support was added in OpenSlide 4.0.0, but some builds (notamment
            MSYS2) peuvent ne pas avoir les codecs requis (JPEG XR, zstd).
            On tente la détection quand même pour lister les fichiers CZI.

        Doc: https://openslide.org/formats/zeiss/
        """
        format_str = self._validate_with_openslide(czi_file)

        # Même si detect_format échoue, on peut détecter CZI par signature
        is_czi_by_signature = False
        if format_str is None:
            # Vérifier signature CZI: commence par "ZISRAWFILE"
            try:
                with open(czi_file, 'rb') as f:
                    signature = f.read(32)
                    if signature.startswith(b'ZISRAWFILE'):
                        is_czi_by_signature = True
                        logger.warning(f"CZI detected by signature but OpenSlide cannot open: {czi_file.name}")
            except:
                pass

        if format_str is None and not is_czi_by_signature:
            return None

        # Si détecté par signature mais pas par OpenSlide = pas supporté
        if is_czi_by_signature and format_str is None:
            return SlideFormat(
                name="Zeiss CZI",
                entry_point=czi_file,
                is_supported=False,  # Pas supporté par cette build OpenSlide
                joint_files=[],
                companion_dirs=[],
                metadata_files=[],
                format_string=None,
                structure_type="single-file",
                detection_method="CZI signature detection (ZISRAWFILE header)",
                notes="CZI detected but OpenSlide cannot open (missing JPEG XR/Zstandard codec or incompatible CZI variant)"
            )

        # Si OpenSlide le reconnait = supporté
        return SlideFormat(
            name="Zeiss CZI",
            entry_point=czi_file,
            is_supported=True,
            joint_files=[],
            companion_dirs=[],
            metadata_files=[],
            format_string=format_str,
            structure_type="single-file",
            detection_method="OpenSlide detect_format validation",
            notes="Single-file CZI with embedded image pyramid"
        )

    # =========================================================================
    # TIFF VARIANTS (Aperio, Ventana, Trestle, Generic)
    # =========================================================================

    def _detect_tiff_variant(self, tif_file: Path) -> Optional[SlideFormat]:
        """
        Détecte variants TIFF.
        OpenSlide.detect_format() discrimine automatiquement entre:
        - Aperio TIFF
        - Ventana TIFF
        - Trestle TIFF (avec fichiers overlap .tif-Nb adjacents - optionnels)
        - Generic Pyramidal TIFF

        Doc:
            - Aperio: https://openslide.org/formats/aperio/
            - Ventana: https://openslide.org/formats/ventana/
            - Trestle: https://openslide.org/formats/trestle/
            - Generic: https://openslide.org/formats/generic-tiff/
        """
        format_str = self._validate_with_openslide(tif_file)
        if format_str is None:
            return None

        # Vérifier fichiers adjacents Trestle (optionnels, OpenSlide ne les lit pas)
        adjacent_files = []
        if format_str == 'trestle':
            adjacent_pattern = f"{tif_file.stem}.tif-*b"
            adjacent_files = list(tif_file.parent.glob(adjacent_pattern))

        format_names = {
            'aperio': 'Aperio TIFF',
            'ventana': 'Ventana TIFF',
            'trestle': 'Trestle TIFF',
            'generic-tiff': 'Generic Pyramidal TIFF',
            'philips': 'Philips TIFF'
        }

        name = format_names.get(format_str, f'TIFF ({format_str})')
        notes = f"Detected as {format_str}"
        if adjacent_files:
            notes += f", {len(adjacent_files)} adjacent overlap files (not read by OpenSlide)"

        return SlideFormat(
            name=name,
            entry_point=tif_file,
            is_supported=True,
            joint_files=adjacent_files,
            companion_dirs=[],
            metadata_files=[],
            format_string=format_str,
            structure_type="single-file",
            detection_method="OpenSlide detect_format on TIFF",
            notes=notes
        )

    # =========================================================================
    # VALIDATION HELPERS
    # =========================================================================

    def _validate_with_openslide(self, file_path: Path) -> Optional[str]:
        """
        Validation FINALE avec OpenSlide.detect_format().

        C'EST LA MÉTHODE AUTHORITATIVE - si elle retourne None, on ignore.

        Doc: https://openslide.org/api/python/#openslide.OpenSlide.detect_format

        Returns:
            Format string ("aperio", "hamamatsu", "mirax", etc.) si supporté
            None si non supporté
        """
        try:
            format_str = openslide.OpenSlide.detect_format(str(file_path))
            if format_str:
                logger.debug(f"OpenSlide validated: {file_path.name} → {format_str}")
            return format_str
        except Exception as e:
            logger.debug(f"OpenSlide validation failed for {file_path.name}: {e}")
            self.scan_stats['errors'] += 1
            return None

    def _is_vms_ini_file(self, file_path: Path) -> bool:
        """
        Vérifie si fichier est un INI VMS valide.
        Section attendue: [Virtual Microscope Specimen]
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return '[Virtual Microscope Specimen]' in content
        except:
            return False

    def _is_vmu_ini_file(self, file_path: Path) -> bool:
        """
        Vérifie si fichier est un INI VMU valide.
        Section attendue: [Uncompressed Virtual Microscope Specimen]
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)
                return '[Uncompressed Virtual Microscope Specimen]' in content
        except:
            return False

    # =========================================================================
    # DIRECTORY SCANNING
    # =========================================================================

    def scan_directory(self, root_dir: Path, recursive: bool = True) -> List[SlideFormat]:
        """
        Scan complet d'un dossier.

        Process:
            1. Parcourt tous fichiers (récursif ou non)
            2. Tente detect_format() sur chaque
            3. Filtre seulement supportés (is_supported=True)
            4. Évite duplicata via detected_entries

        Args:
            root_dir: Dossier racine à scanner
            recursive: Si True, scan récursif (défaut)

        Returns:
            Liste de SlideFormat supportés et validés
        """
        detected_slides = []

        logger.info(f"{'='*60}")
        logger.info(f"Starting scan: {root_dir}")
        logger.info(f"Recursive: {recursive}")
        logger.info(f"{'='*60}")

        # Reset stats
        self.scan_stats = {'scanned': 0, 'detected': 0, 'ignored': 0, 'errors': 0}

        # Parcourir fichiers
        pattern = '**/*' if recursive else '*'
        for file_path in root_dir.glob(pattern):
            if file_path.is_file():
                slide_format = self.detect_format(file_path)

                # Retourner TOUTES les lames détectées (supportées ET non supportées)
                # Phase 1.5.1: Inclure CZI détectées par signature même si pas supportées
                if slide_format:
                    detected_slides.append(slide_format)

        # Logs finaux
        logger.info(f"{'='*60}")
        logger.info(f"Scan complete!")
        logger.info(f"  Files scanned: {self.scan_stats['scanned']}")
        logger.info(f"  Slides detected: {self.scan_stats['detected']}")
        logger.info(f"  Files ignored: {self.scan_stats['ignored']}")
        logger.info(f"  Errors: {self.scan_stats['errors']}")
        logger.info(f"{'='*60}")

        return detected_slides
