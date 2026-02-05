"""
OpenSlide Test Provider

Provider ML utilisant OpenSlide pour tests d'intégration réels.

Ce provider:
- Lit de VRAIES lames avec OpenSlide
- Extrait de VRAIES tuiles
- Génère des features basées sur les données réelles (histogrammes, stats)
- Permet de tester le pipeline ML bout en bout sans Slideflow

Use cases:
- Tests d'intégration avec vraies lames
- Validation du pipeline de données
- Tests de performance sur fichiers réels

Note:
    Ce provider n'utilise PAS de modèle ML entraîné.
    Les "prédictions" sont basées sur des heuristiques simples.
    Pour de vraies prédictions, utiliser SlideflowProvider.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import openslide
from openslide import OpenSlideError

from core.exceptions import MLModelNotLoadedError, PredictionError
from core.interfaces import FeatureExtractionResult, HeatmapResult, PredictionResult

logger = logging.getLogger(__name__)


class OpenSlideTestProvider:
    """
    Provider ML utilisant OpenSlide pour tests réels.

    Features:
    - Lecture de vraies lames (.mrxs, .svs, .bif, .tiff, etc.)
    - Extraction de vraies tuiles
    - Features basées sur statistiques d'image (histogrammes, intensités)
    - Pas de dépendance à Slideflow ou modèle ML

    Usage:
        >>> provider = OpenSlideTestProvider()
        >>> provider.load_model("heuristic://color_analysis", {})
        >>> result = provider.predict("/path/to/slide.mrxs")
    """

    SUPPORTED_FORMATS = [".mrxs", ".svs", ".tif", ".tiff", ".bif", ".ndpi", ".scn", ".vsi"]

    def __init__(self, device: str = "cpu"):
        """Initialize OpenSlide test provider."""
        self.device = "cpu"
        self.model = None
        self.model_config = {}
        self.model_loaded = False
        self._slide_cache: Dict[str, openslide.OpenSlide] = {}

        logger.info("OpenSlideTestProvider initialized (real slides, heuristic predictions)")

    def load_model(self, model_path: str, model_config: Dict) -> None:
        """
        Load heuristic model configuration.

        Args:
            model_path: Identifiant (ex: "heuristic://color_analysis")
            model_config: Configuration avec classes, seuils, etc.
        """
        logger.info(f"[OPENSLIDE] Loading heuristic model: {model_path}")

        self.model = {
            "type": "heuristic",
            "path": model_path,
            "method": model_config.get("method", "intensity_analysis"),
        }
        self.model_config = model_config
        self.model_loaded = True

        logger.info(f"[OPENSLIDE] Model ready: {model_config.get('model_id', 'heuristic')}")

    def unload_model(self) -> None:
        """Unload model and clear slide cache."""
        self._close_all_slides()
        self.model = None
        self.model_loaded = False
        logger.info("[OPENSLIDE] Model unloaded, slide cache cleared")

    def _open_slide(self, slide_path: str) -> openslide.OpenSlide:
        """Open slide with caching."""
        if slide_path not in self._slide_cache:
            try:
                self._slide_cache[slide_path] = openslide.OpenSlide(slide_path)
            except OpenSlideError as e:
                raise PredictionError(
                    slide_path=slide_path,
                    model_id=self.model_config.get("model_id", ""),
                    message=f"Cannot open slide: {e}",
                    provider="openslide_test",
                )
        return self._slide_cache[slide_path]

    def _close_all_slides(self) -> None:
        """Close all cached slides."""
        for slide in self._slide_cache.values():
            try:
                slide.close()
            except Exception:
                pass
        self._slide_cache.clear()

    def predict(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Predict using real slide data with heuristic analysis.

        The prediction is based on color/intensity statistics from the slide.
        This is NOT a real ML prediction, but tests the full data pipeline.

        Args:
            slide_path: Path to real slide file
            region: Optional region (x, y, width, height)

        Returns:
            PredictionResult with heuristic-based prediction
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="openslide_test")

        start_time = time.time()
        slide_id = Path(slide_path).stem

        logger.info(f"[OPENSLIDE] Analyzing slide: {slide_id}")

        slide = self._open_slide(slide_path)

        if region:
            x, y, w, h = region
            tile = slide.read_region((x, y), 0, (min(w, 1024), min(h, 1024)))
        else:
            tile = slide.get_thumbnail((512, 512))

        tile_array = np.array(tile.convert("RGB"))

        features = self._extract_color_features(tile_array)
        prediction = self._heuristic_predict(features)

        classes = self.model_config.get("classes", ["tissue", "background"])
        probabilities = {cls: float(prediction["probs"].get(cls, 0.0)) for cls in classes}

        prob_sum = sum(probabilities.values())
        if prob_sum > 0:
            probabilities = {k: v / prob_sum for k, v in probabilities.items()}
        else:
            probabilities = {cls: 1.0 / len(classes) for cls in classes}

        execution_time_ms = (time.time() - start_time) * 1000

        result = PredictionResult(
            prediction_class=prediction["class"],
            confidence=prediction["confidence"],
            probabilities=probabilities,
            uncertainty=prediction["uncertainty"],
            execution_time_ms=execution_time_ms,
            model_id=self.model_config.get("model_id", "heuristic"),
            slide_id=slide_id,
            metadata={
                "provider": "openslide_test",
                "method": "color_heuristic",
                "region": region,
                "slide_dimensions": slide.dimensions,
                "features": features,
            },
        )

        logger.info(
            f"[OPENSLIDE] Prediction: {prediction['class']} "
            f"(conf: {prediction['confidence']:.2%}, time: {execution_time_ms:.0f}ms)"
        )

        return result

    def _extract_color_features(self, image: np.ndarray) -> Dict:
        """Extract color-based features from image."""
        r, g, b = image[:, :, 0], image[:, :, 1], image[:, :, 2]

        features = {
            "mean_r": float(np.mean(r)),
            "mean_g": float(np.mean(g)),
            "mean_b": float(np.mean(b)),
            "std_r": float(np.std(r)),
            "std_g": float(np.std(g)),
            "std_b": float(np.std(b)),
            "mean_intensity": float(np.mean(image)),
            "tissue_ratio": float(np.mean(image < 220) if image.size > 0 else 0),
        }

        return features

    def _heuristic_predict(self, features: Dict) -> Dict:
        """
        Heuristic prediction based on color features.

        Simple rules:
        - High pink/purple = likely tissue (H&E staining)
        - Low tissue ratio = likely background
        """
        classes = self.model_config.get("classes", ["tissue", "background"])

        tissue_ratio = features.get("tissue_ratio", 0.5)
        mean_intensity = features.get("mean_intensity", 128)

        if tissue_ratio > 0.3 and mean_intensity < 200:
            pred_class = classes[0] if len(classes) > 0 else "tissue"
            confidence = min(0.95, 0.5 + tissue_ratio * 0.5)
        else:
            pred_class = classes[-1] if len(classes) > 1 else "background"
            confidence = min(0.95, 0.5 + (1 - tissue_ratio) * 0.5)

        probs = {}
        for i, cls in enumerate(classes):
            if cls == pred_class:
                probs[cls] = confidence
            else:
                probs[cls] = (1 - confidence) / max(1, len(classes) - 1)

        uncertainty = 1.0 - confidence

        return {
            "class": pred_class,
            "confidence": confidence,
            "uncertainty": uncertainty,
            "probs": probs,
        }

    def extract_features(
        self, slide_path: str, tile_size: int = 224, overlap: int = 0
    ) -> FeatureExtractionResult:
        """
        Extract real features from slide tiles.

        Extracts tiles at regular intervals and computes color/texture features.

        Args:
            slide_path: Path to real slide
            tile_size: Tile size in pixels
            overlap: Overlap between tiles

        Returns:
            FeatureExtractionResult with real extracted features
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="openslide_test")

        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "heuristic")

        logger.info(f"[OPENSLIDE] Extracting features from: {slide_id}")

        slide = self._open_slide(slide_path)
        width, height = slide.dimensions

        best_level = self._find_best_level(slide, tile_size)
        level_dims = slide.level_dimensions[best_level]
        downsample = slide.level_downsamples[best_level]

        step = tile_size - overlap
        max_tiles = 500

        coordinates = []
        embeddings_list = []

        level_w, level_h = level_dims
        stride = max(1, int(tile_size / downsample))

        x_positions = list(range(0, level_w - stride, stride))[:50]
        y_positions = list(range(0, level_h - stride, stride))[:10]

        for y_level in y_positions:
            for x_level in x_positions:
                if len(coordinates) >= max_tiles:
                    break

                x_slide = int(x_level * downsample)
                y_slide = int(y_level * downsample)

                try:
                    tile = slide.read_region((x_slide, y_slide), best_level, (tile_size, tile_size))
                    tile_rgb = np.array(tile.convert("RGB"))

                    features = self._compute_tile_features(tile_rgb)
                    embeddings_list.append(features)
                    coordinates.append((x_slide, y_slide))
                except Exception as e:
                    logger.debug(f"Skipping tile at ({x_slide}, {y_slide}): {e}")
                    continue

            if len(coordinates) >= max_tiles:
                break

        if len(embeddings_list) == 0:
            embeddings_list.append(np.zeros(64))
            coordinates.append((0, 0))

        embeddings = np.array(embeddings_list, dtype=np.float32)

        result = FeatureExtractionResult(
            embeddings=embeddings,
            coordinates=coordinates,
            slide_id=slide_id,
            model_id=model_id,
            tile_size=tile_size,
            metadata={
                "provider": "openslide_test",
                "slide_dimensions": (width, height),
                "level_used": best_level,
                "downsample": downsample,
                "overlap": overlap,
            },
        )

        logger.info(
            f"[OPENSLIDE] Extracted {len(coordinates)} tiles, "
            f"embeddings shape: {embeddings.shape}"
        )

        return result

    def _find_best_level(self, slide: openslide.OpenSlide, target_tile_size: int) -> int:
        """Find best pyramid level for extraction."""
        for level in range(slide.level_count):
            dims = slide.level_dimensions[level]
            if dims[0] >= target_tile_size * 10 and dims[1] >= target_tile_size * 10:
                return level
        return slide.level_count - 1

    def _compute_tile_features(self, tile: np.ndarray) -> np.ndarray:
        """Compute feature vector from tile (64-dim)."""
        features = []

        for channel in range(3):
            ch = tile[:, :, channel]
            features.extend(
                [
                    np.mean(ch),
                    np.std(ch),
                    np.min(ch),
                    np.max(ch),
                    np.median(ch),
                    np.percentile(ch, 25),
                    np.percentile(ch, 75),
                ]
            )

        gray = np.mean(tile, axis=2)
        features.extend(
            [
                np.mean(gray),
                np.std(gray),
            ]
        )

        hist_r, _ = np.histogram(tile[:, :, 0], bins=8, range=(0, 256))
        hist_g, _ = np.histogram(tile[:, :, 1], bins=8, range=(0, 256))
        hist_b, _ = np.histogram(tile[:, :, 2], bins=8, range=(0, 256))

        hist_r = hist_r / (hist_r.sum() + 1e-8)
        hist_g = hist_g / (hist_g.sum() + 1e-8)
        hist_b = hist_b / (hist_b.sum() + 1e-8)

        features.extend(hist_r.tolist())
        features.extend(hist_g.tolist())
        features.extend(hist_b.tolist())

        features.append(np.mean(tile < 220))

        while len(features) < 64:
            features.append(0.0)

        return np.array(features[:64], dtype=np.float32)

    def generate_heatmap(
        self, slide_path: str, prediction_class: str, resolution_level: int = 2
    ) -> HeatmapResult:
        """
        Generate heatmap from real slide analysis.

        Creates attention map based on tissue intensity analysis.

        Args:
            slide_path: Path to real slide
            prediction_class: Target class
            resolution_level: Resolution level for heatmap

        Returns:
            HeatmapResult with real-data-based heatmap
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="openslide_test")

        slide_id = Path(slide_path).stem

        logger.info(f"[OPENSLIDE] Generating heatmap for: {slide_id}")

        slide = self._open_slide(slide_path)
        slide_dimensions = slide.dimensions

        target_size = 256 // (2**resolution_level)
        thumbnail = slide.get_thumbnail((target_size * 4, target_size * 4))
        thumb_array = np.array(thumbnail.convert("RGB"))

        heatmap = self._compute_attention_heatmap(thumb_array)

        from scipy.ndimage import zoom

        scale_h = target_size / heatmap.shape[0]
        scale_w = target_size / heatmap.shape[1]
        heatmap = zoom(heatmap, (scale_h, scale_w), order=1)

        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)

        result = HeatmapResult(
            heatmap=heatmap.astype(np.float32),
            slide_dimensions=slide_dimensions,
            resolution_level=resolution_level,
            slide_id=slide_id,
            method="intensity_attention",
            target_class=prediction_class,
            metadata={
                "provider": "openslide_test",
                "thumbnail_size": thumb_array.shape[:2],
            },
        )

        logger.info(f"[OPENSLIDE] Heatmap generated: {heatmap.shape}")

        return result

    def _compute_attention_heatmap(self, image: np.ndarray) -> np.ndarray:
        """
        Compute attention heatmap based on tissue presence.

        Highlights regions with tissue (darker, colored) vs background (white).
        """
        gray = np.mean(image, axis=2)

        attention = 1.0 - (gray / 255.0)

        r, g, b = image[:, :, 0], image[:, :, 1], image[:, :, 2]
        color_var = np.std([r, g, b], axis=0)
        color_attention = color_var / (color_var.max() + 1e-8)

        heatmap = 0.6 * attention + 0.4 * color_attention

        from scipy.ndimage import gaussian_filter

        heatmap = gaussian_filter(heatmap, sigma=2)

        return heatmap

    def get_model_info(self) -> Dict:
        """Get model information."""
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="openslide_test")

        return {
            "model_id": self.model_config.get("model_id", "heuristic"),
            "model_name": self.model_config.get("model_name", "OpenSlide Heuristic"),
            "version": "1.0.0",
            "task_type": "classification",
            "classes": self.model_config.get("classes", ["tissue", "background"]),
            "input_size": (224, 224),
            "device": "cpu",
            "provider": "openslide_test",
            "supported_formats": self.SUPPORTED_FORMATS,
            "method": "heuristic_color_analysis",
        }


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python openslide_provider.py <slide_path>")
        sys.exit(1)

    slide_path = sys.argv[1]

    provider = OpenSlideTestProvider()
    provider.load_model(
        "heuristic://test",
        {
            "model_id": "test",
            "classes": ["tissue", "background"],
        },
    )

    print("\n1. Prediction:")
    result = provider.predict(slide_path)
    print(f"   Class: {result.prediction_class}")
    print(f"   Confidence: {result.confidence:.2%}")

    print("\n2. Feature extraction:")
    features = provider.extract_features(slide_path)
    print(f"   Patches: {features.num_patches}")
    print(f"   Embedding dim: {features.embedding_dim}")

    print("\n3. Heatmap:")
    heatmap = provider.generate_heatmap(slide_path, result.prediction_class)
    print(f"   Shape: {heatmap.heatmap.shape}")

    provider.unload_model()
    print("\nDone!")
