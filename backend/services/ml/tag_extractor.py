"""
Tag Extractor Service
Extraction automatique de tags (organ, stain, marker) depuis metadata slides.

Références:
- docs/MLOPS_ARCHITECTURE.md Section 2.4
- OpenSlide properties: https://openslide.org/api/python/#openslide.OpenSlide.properties
"""

import logging
import re
from pathlib import Path
from typing import Dict, Optional

import openslide

logger = logging.getLogger(__name__)


class TagExtractor:
    """
    Extracteur de tags depuis métadonnées slide.

    Sources (par ordre de priorité):
    1. DICOM metadata (si format DICOM)
    2. OpenSlide properties (vendor-specific)
    3. Filename parsing (patterns communs)
    4. ML inference (si modèle disponible)

    Usage:
        extractor = TagExtractor()
        tags = extractor.extract_tags("path/to/slide.mrxs", "MRXS")
        # tags = {"organ": "prostate", "stain": "H&E", "confidence": 0.85, ...}
    """

    def __init__(self, config_path: Optional[str] = None, tag_classifier_model=None):
        """
        Initialize tag extractor.

        Args:
            config_path: Path vers ml_routes.yaml (pour keywords)
            tag_classifier_model: Modèle ML pour inférence (optionnel)
        """
        self.tag_classifier = tag_classifier_model
        self.organ_keywords = self._load_organ_keywords()
        self.stain_keywords = self._load_stain_keywords()
        self.marker_keywords = self._load_marker_keywords()

    def extract_tags(self, slide_path: str, slide_format: str) -> Dict:
        """
        Extrait tags d'une lame.

        Args:
            slide_path: Chemin vers lame
            slide_format: Format détecté (DICOM, MRXS, BIF, etc.)

        Returns:
            {
                "organ": str | null,
                "stain": str | null,
                "marker": str | null,
                "task": str | null,
                "confidence": float,
                "source": str  # "dicom", "properties", "filename", "ml_inference", "manual_required"
            }

        Examples:
            >>> extractor = TagExtractor()
            >>> tags = extractor.extract_tags("prostate_HE_sample1.mrxs", "MRXS")
            >>> print(tags)
            {
                "organ": "prostate",
                "stain": "H&E",
                "marker": None,
                "task": None,
                "confidence": 0.7,
                "source": "filename_parsing"
            }
        """
        logger.info(f"Extracting tags for: {Path(slide_path).name} (format: {slide_format})")

        # 1. Essayer DICOM si applicable
        if slide_format.lower() == "dicom":
            tags = self._extract_from_dicom(slide_path)
            if tags and tags.get("confidence", 0) > 0.9:
                logger.info(f"Tags extracted from DICOM: {tags}")
                return tags

        # 2. Essayer OpenSlide properties
        tags = self._extract_from_openslide_properties(slide_path)
        if tags and tags.get("confidence", 0) > 0.8:
            logger.info(f"Tags extracted from OpenSlide properties: {tags}")
            return tags

        # 3. Parser filename (patterns communs)
        tags = self._extract_from_filename(slide_path)
        if tags and tags.get("confidence", 0) > 0.7:
            logger.info(f"Tags extracted from filename: {tags}")
            return tags

        # 4. ML inference (si modèle disponible)
        if self.tag_classifier:
            tags = self._extract_via_ml_inference(slide_path)
            if tags and tags.get("confidence", 0) > 0.75:
                logger.info(f"Tags extracted via ML inference: {tags}")
                return tags

        # 5. Fallback: demander assignation manuelle
        logger.warning(
            f"Could not auto-extract tags for {Path(slide_path).name} - manual assignment required"
        )
        return {
            "organ": None,
            "stain": None,
            "marker": None,
            "task": None,
            "confidence": 0.0,
            "source": "manual_required",
        }

    # ========================================================================
    # EXTRACTION METHODS
    # ========================================================================

    def _extract_from_dicom(self, slide_path: str) -> Optional[Dict]:
        """
        Extraction depuis tags DICOM.

        DICOM tags pour WSI:
        - (0008,0060) Modality = "SM" (Slide Microscopy)
        - (0040,0560) Specimen Description Sequence
        - (0048,0001) Imaging Subject Name

        Requires: pydicom library

        TODO: Implémenter avec pydicom quand support DICOM ajouté
        """
        try:
            import pydicom

            dcm = pydicom.dcmread(slide_path)

            # Extraction organ depuis Specimen Description
            organ = None
            stain = None

            if hasattr(dcm, "SpecimenDescriptionSequence"):
                for item in dcm.SpecimenDescriptionSequence:
                    desc_text = str(item.get("SpecimenDescription", "")).lower()
                    organ = self._find_organ_in_text(desc_text)
                    stain = self._find_stain_in_text(desc_text)

            if organ or stain:
                return {
                    "organ": organ,
                    "stain": stain,
                    "marker": None,  # Difficile à extraire de DICOM
                    "task": None,
                    "confidence": 0.95,
                    "source": "dicom_metadata",
                }

        except ImportError:
            logger.debug("pydicom not installed - skipping DICOM extraction")
        except Exception as e:
            logger.warning(f"Error extracting from DICOM: {e}")

        return None

    def _extract_from_openslide_properties(self, slide_path: str) -> Optional[Dict]:
        """
        Extraction depuis propriétés OpenSlide.

        OpenSlide expose metadata vendor-specific:
        - 3DHistech: Properties avec "3DHISTECH." prefix
        - Aperio: Properties avec "aperio." prefix
        - Ventana: Properties avec description texte

        Doc: https://openslide.org/api/python/#openslide.OpenSlide.properties
        """
        try:
            slide = openslide.OpenSlide(slide_path)
            properties = dict(slide.properties)
            slide.close()

            # Concaténer toutes les properties en texte
            all_text = " ".join(str(v) for v in properties.values()).lower()

            # Recherche par keywords dans properties
            organ = self._find_organ_in_text(all_text)
            stain = self._find_stain_in_text(all_text)
            marker = self._find_marker_in_text(all_text)

            if organ or stain or marker:
                logger.debug(
                    f"Found in OpenSlide properties: organ={organ}, stain={stain}, marker={marker}"
                )
                return {
                    "organ": organ,
                    "stain": stain,
                    "marker": marker,
                    "task": None,
                    "confidence": 0.8,
                    "source": "openslide_properties",
                }

        except openslide.OpenSlideError as e:
            logger.warning(f"Error opening slide for property extraction: {e}")
        except Exception as e:
            logger.error(f"Unexpected error extracting from OpenSlide properties: {e}")

        return None

    def _extract_from_filename(self, slide_path: str) -> Optional[Dict]:
        """
        Parsing patterns communs de noms de fichiers.

        Patterns fréquents:
        - "prostate_HE_patient123.mrxs"
        - "breast_Ki67_sample45.svs"
        - "colon_HER2_case789.bif"
        - "P12345_Lung_PDL1.ndpi"

        Returns:
            Tags extraits ou None si rien trouvé
        """
        filename = Path(slide_path).stem.lower()
        logger.debug(f"Parsing filename: {filename}")

        organ = self._find_organ_in_text(filename)
        stain = self._find_stain_in_text(filename)
        marker = self._find_marker_in_text(filename)

        if organ or stain or marker:
            logger.debug(f"Found in filename: organ={organ}, stain={stain}, marker={marker}")
            return {
                "organ": organ,
                "stain": stain,
                "marker": marker,
                "task": None,
                "confidence": 0.7,  # Filename parsing moins fiable
                "source": "filename_parsing",
            }

        return None

    def _extract_via_ml_inference(self, slide_path: str) -> Optional[Dict]:
        """
        Inférence ML pour détecter organ + stain.

        Utilise un modèle léger (EfficientNet-Lite) entraîné sur thumbnails.

        Model architecture:
        - Input: thumbnail 512x512 RGB
        - Backbone: EfficientNet-Lite0
        - Outputs: organ_logits (6 classes), stain_logits (3 classes)

        Returns:
            Tags prédits ou None si échec
        """
        if not self.tag_classifier:
            return None

        try:
            # Charger thumbnail (rapide, pas besoin full resolution)
            slide = openslide.OpenSlide(slide_path)
            thumbnail = slide.get_thumbnail((512, 512))
            slide.close()

            # Inférence
            predictions = self.tag_classifier.predict(thumbnail)

            if predictions["confidence"] > 0.75:
                return {
                    "organ": predictions.get("organ"),
                    "stain": predictions.get("stain"),
                    "marker": None,  # Pas prédit par ce modèle
                    "task": None,
                    "confidence": predictions["confidence"],
                    "source": "ml_inference",
                }

        except Exception as e:
            logger.error(f"ML inference failed: {e}")

        return None

    # ========================================================================
    # KEYWORD MATCHING HELPERS
    # ========================================================================

    def _find_organ_in_text(self, text: str) -> Optional[str]:
        """
        Recherche organ par keywords.

        Args:
            text: Texte à analyser (lowercase)

        Returns:
            Organ détecté ou None
        """
        text = text.lower()
        for organ, keywords in self.organ_keywords.items():
            if any(kw in text for kw in keywords):
                return organ
        return None

    def _find_stain_in_text(self, text: str) -> Optional[str]:
        """
        Recherche stain par keywords.

        Args:
            text: Texte à analyser (lowercase)

        Returns:
            Stain détecté ou None
        """
        text = text.lower()
        for stain, keywords in self.stain_keywords.items():
            if any(kw in text for kw in keywords):
                return stain
        return None

    def _find_marker_in_text(self, text: str) -> Optional[str]:
        """
        Recherche marker IHC par keywords.

        Args:
            text: Texte à analyser (lowercase)

        Returns:
            Marker détecté ou None
        """
        text = text.lower()
        for marker, keywords in self.marker_keywords.items():
            if any(kw in text for kw in keywords):
                return marker
        return None

    # ========================================================================
    # CONFIGURATION LOADERS
    # ========================================================================

    def _load_organ_keywords(self) -> Dict[str, list]:
        """
        Keywords pour détection organ.

        Basé sur anatomie standard + variations linguistiques.

        Returns:
            Dict mapping organ -> list of keywords
        """
        return {
            "prostate": ["prostate", "prostatic", "prost"],
            "sein": ["breast", "mammary", "sein", "mamm"],
            "côlon": ["colon", "colorectal", "rectal", "col"],
            "poumon": ["lung", "pulmonary", "poumon", "pulm"],
            "foie": ["liver", "hepatic", "foie", "hep"],
            "rein": ["kidney", "renal", "rein", "ren"],
            "peau": ["skin", "cutaneous", "peau", "derm"],
            "cerveau": ["brain", "cerebral", "cerveau", "neuro"],
            "estomac": ["stomach", "gastric", "estomac", "gastr"],
            "pancréas": ["pancreas", "pancreatic", "pancréas", "pancr"],
        }

    def _load_stain_keywords(self) -> Dict[str, list]:
        """
        Keywords pour détection stain.

        Returns:
            Dict mapping stain -> list of keywords
        """
        return {
            "H&E": ["h&e", "he", "hematoxylin", "eosin", "hem", "eos"],
            "IHC": ["ihc", "immunohistochemistry", "immunohistochimie", "immuno"],
            "IF": ["if", "immunofluorescence", "immfluor"],
            "PAS": ["pas", "periodic acid schiff"],
            "Masson": ["masson", "trichrome"],
        }

    def _load_marker_keywords(self) -> Dict[str, list]:
        """
        Keywords pour détection marker IHC.

        Returns:
            Dict mapping marker -> list of keywords
        """
        return {
            "Ki-67": ["ki-67", "ki67", "mib1", "mib-1"],
            "HER2": ["her2", "her-2", "erbb2", "c-erbb-2"],
            "PD-L1": ["pdl1", "pd-l1", "pdl-1", "programmed death ligand"],
            "ER": ["er", "estrogen", "oestrogen", "estrogenic"],
            "PR": ["pr", "progesterone", "progesteron"],
            "p53": ["p53", "tp53", "tumor protein 53"],
            "CD3": ["cd3"],
            "CD20": ["cd20"],
            "CD45": ["cd45"],
        }


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)

    # Test cases
    test_slides = [
        ("data/prostate_HE_sample1.mrxs", "MRXS"),
        ("data/breast_Ki67_case45.svs", "SVS"),
        ("data/lung_PDL1_patient789.bif", "BIF"),
        ("data/unknown_sample.ndpi", "NDPI"),
    ]

    extractor = TagExtractor()

    print("\n" + "=" * 80)
    print("TAG EXTRACTOR - TESTS")
    print("=" * 80 + "\n")

    for slide_path, slide_format in test_slides:
        print(f"Testing: {slide_path}")
        tags = extractor.extract_tags(slide_path, slide_format)

        print(f"  Organ: {tags['organ']}")
        print(f"  Stain: {tags['stain']}")
        print(f"  Marker: {tags['marker']}")
        print(f"  Confidence: {tags['confidence']:.2f}")
        print(f"  Source: {tags['source']}")
        print()
