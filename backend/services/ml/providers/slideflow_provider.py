"""
Slideflow ML Provider

Implémentation de MLProvider interface avec Slideflow framework.
Supporte 3 modes progressifs:

Phase 1-2 (extractor): Feature extraction avec modèles pré-entraînés
  - CTransPath, RetCCL, Virchow, UNI, Phikon, GigaPath, ResNet50
  - extract_features() fonctionne immédiatement
  - predict() utilise analyse basée sur features (tissue/background)
  - generate_heatmap() utilise feature norms comme attention proxy

Phase 3 (classifier): Classification avec modèle entraîné
  - predict() fait de la vraie classification ML
  - generate_heatmap() utilise Grad-CAM
  - Feedback pathologiste pour amélioration continue

Configuration via variables d'environnement:
  ML_PROVIDER=slideflow
  ML_MODE=extractor          # "extractor" ou "classifier"
  ML_EXTRACTOR=ctranspath    # Nom du feature extractor
  ML_MODEL_PATH=             # Chemin modèle entraîné (Phase 3)

Slideflow: https://github.com/slideflow/slideflow
References:
- Dolezal et al. (2024): "Slideflow: Deep Learning for Digital Histopathology"
  https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-024-05758-x
"""

import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    import slideflow as sf

from core.exceptions import (
    FeatureExtractionError,
    HeatmapGenerationError,
    MLModelNotLoadedError,
    ModelLoadError,
    PredictionError,
)
from core.interfaces import FeatureExtractionResult, HeatmapResult, PredictionResult

logger = logging.getLogger(__name__)


# ============================================================================
# KNOWN FEATURE EXTRACTORS
# ============================================================================

KNOWN_EXTRACTORS = {
    # Core slideflow (Apache-2.0) - inclus dans pip install slideflow
    "resnet50_imagenet": {"dim": 2048, "tile_px": 224, "package": "slideflow"},
    "virchow": {"dim": 2560, "tile_px": 224, "package": "slideflow"},
    # slideflow-gpl (GPL-3.0) - pip install slideflow-gpl
    "ctranspath": {"dim": 768, "tile_px": 224, "package": "slideflow-gpl"},
    "retccl": {"dim": 2048, "tile_px": 224, "package": "slideflow-gpl"},
    # slideflow-noncommercial (CC BY-NC 4.0) - pip install slideflow-noncommercial
    "uni": {"dim": 1024, "tile_px": 224, "package": "slideflow-noncommercial"},
    "phikon": {"dim": 768, "tile_px": 224, "package": "slideflow-noncommercial"},
    "gigapath": {"dim": 1536, "tile_px": 256, "package": "slideflow-noncommercial"},
    "plip": {"dim": 512, "tile_px": 224, "package": "slideflow-noncommercial"},
    "histossl": {"dim": 2048, "tile_px": 224, "package": "slideflow-noncommercial"},
    # Direct HuggingFace (no slideflow plugin needed) - loaded via transformers
    "phikon-v2": {
        "dim": 1024,
        "tile_px": 224,
        "package": "transformers",
        "hf_id": "owkin/phikon-v2",
    },
}

# Extractors loaded directly via transformers (bypass slideflow's sf.build_feature_extractor)
CUSTOM_EXTRACTORS = {"phikon-v2"}


class _PhikonExtractor:
    """
    Wrapper Phikon-v2 compatible with Slideflow's extractor API.

    Phikon-v2 (Owkin) is a DINOv2-based pathology foundation model trained
    on large-scale histopathology data from TCGA. Produces 1024-dim embeddings
    that capture tissue morphology, cellular architecture, and staining patterns.

    Paper: Filiot et al. (2024) "Phikon-v2: A large-scale vision foundation
           model for digital pathology"
    HuggingFace: owkin/phikon-v2
    """

    def __init__(self, device="cpu"):
        import torch
        from transformers import AutoImageProcessor, AutoModel

        logger.info("Loading Phikon-v2 pathology foundation model...")
        self.phikon = AutoModel.from_pretrained("owkin/phikon-v2")
        self.image_processor = AutoImageProcessor.from_pretrained("owkin/phikon-v2")
        self.phikon.eval()

        # Slideflow-compatible attributes
        self.num_features = 1024
        self.num_classes = 0
        self.num_uncertainty = 0
        self.backend = "torch"
        self._device = device
        self.tag = "phikon-v2"
        self.include_preds = False
        self.img_format = "numpy"
        self.wsi_normalizer = None
        self.preprocess_kwargs = {}

        if device == "cuda":
            self.phikon = self.phikon.cuda()

        # Cache normalization tensors
        self._mean = torch.tensor(self.image_processor.image_mean).view(1, 3, 1, 1)
        self._std = torch.tensor(self.image_processor.image_std).view(1, 3, 1, 1)

        logger.info(f"Phikon-v2 loaded (1024-dim, device: {device})")

    @property
    def device(self):
        return self._device

    def is_torch(self):
        return True

    def is_tensorflow(self):
        return False

    def __call__(self, obj, **kwargs):
        import slideflow as sf
        import torch

        if isinstance(obj, sf.WSI):
            from slideflow.model.extractors._slide import features_from_slide

            return features_from_slide(self, obj, **kwargs)

        # obj is a tensor (B, 3, H, W) uint8 from Slideflow's tile pipeline
        images = obj.float() / 255.0
        mean = self._mean.to(images.device)
        std = self._std.to(images.device)
        images = (images - mean) / std

        with torch.no_grad():
            outputs = self.phikon(pixel_values=images)
            features = outputs.last_hidden_state[:, 0, :]  # CLS token

        return features


class SlideflowProvider:
    """
    ML Provider basé sur Slideflow - mode progressif.

    Modes:
    - "extractor": Feature extractors pré-entraînés (Phase 1-2)
    - "classifier": Modèle de classification entraîné (Phase 3)

    Le mode est déterminé par model_config["mode"] ou auto-détecté:
    - Si model_path est un nom d'extracteur connu → mode extractor
    - Si model_path est un chemin fichier → mode classifier
    - Si model_path commence par "extractor://" → mode extractor

    Usage Phase 1-2 (Feature Extraction):
        >>> provider = SlideflowProvider()
        >>> provider.load_model("extractor://ctranspath", {
        ...     "model_id": "ctranspath_features",
        ...     "mode": "extractor"
        ... })
        >>> features = provider.extract_features("slide.mrxs")

    Usage Phase 3 (Classification):
        >>> provider = SlideflowProvider()
        >>> provider.load_model("models/gleason_v1.pt", {
        ...     "model_id": "gleason_grading_v1",
        ...     "mode": "classifier",
        ...     "classes": ["gleason_3", "gleason_4", "gleason_5"]
        ... })
        >>> result = provider.predict("slide.mrxs")
    """

    def __init__(self, device: str = "auto"):
        self.device = self._detect_device(device)
        self.model = None
        self.extractor = None
        self.model_config: Dict = {}
        self.model_loaded = False
        self.mode = "extractor"  # "extractor" or "classifier"

        self._slideflow_available = self._check_slideflow()

        if not self._slideflow_available:
            logger.warning("Slideflow not installed. Install with: pip install slideflow[torch]")
        else:
            logger.info(
                f"SlideflowProvider initialized (device: {self.device}, "
                f"slideflow v{self.sf.__version__})"
            )

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def _check_slideflow(self) -> bool:
        try:
            import slideflow as sf

            self.sf = sf
            logger.debug(f"Slideflow version: {sf.__version__}")
            return True
        except ImportError:
            logger.debug("Slideflow not installed")
            return False

    def _detect_device(self, device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch

            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"GPU detected: {gpu_name}")
                return "cuda"
        except ImportError:
            pass
        logger.info("Using CPU (no GPU detected)")
        return "cpu"

    # ========================================================================
    # WSI HELPERS
    # ========================================================================

    def _open_wsi(self, slide_path: str, tile_size: int = 224) -> "sf.WSI":
        """
        Open a WSI with automatic magnification detection.

        Tries 10x first (good coverage/resolution tradeoff), then falls back
        to the closest available magnification if 10x is not available.
        """
        preferred_mags = ["10x", "20x", "5x", "40x"]

        for mag in preferred_mags:
            try:
                wsi = self.sf.WSI(slide_path, tile_px=tile_size, tile_um=mag)
                logger.debug(f"Opened WSI at {mag}: {slide_path}")
                return wsi
            except Exception as e:
                if "magnification" in str(e).lower() or "mpp" in str(e).lower():
                    continue
                raise

        # Last resort: use smallest available magnification from slide metadata
        try:
            import openslide

            slide = openslide.open_slide(slide_path)
            mpp = slide.properties.get("openslide.mpp-x")
            slide.close()
            if mpp:
                # Convert mpp to approximate magnification
                mpp_val = float(mpp)
                approx_mag = round(10.0 / mpp_val)
                mag_str = f"{approx_mag}x"
                logger.info(f"Using calculated magnification {mag_str} (mpp={mpp_val})")
                return self.sf.WSI(slide_path, tile_px=tile_size, tile_um=mag_str)
        except Exception:
            pass

        # No MPP metadata available - slide cannot be processed by Slideflow
        slide_name = Path(slide_path).name
        raise HeatmapGenerationError(
            f"Slide '{slide_name}' has no resolution metadata (microns-per-pixel). "
            f"Generic TIFF files often lack this information. "
            f"ML analysis requires slides with MPP data (SVS, MRXS, NDPI, SCN formats recommended).",
            slide_path=slide_path,
            prediction_class="",
            method="open_wsi",
            provider="slideflow",
            details={"reason": "missing_mpp", "slide": slide_name},
        )

    # ========================================================================
    # MODEL MANAGEMENT
    # ========================================================================

    def load_model(self, model_path: str, model_config: Dict) -> None:
        """
        Charge modèle ou feature extractor.

        Détection automatique du mode:
        - "extractor://ctranspath" → feature extractor CTransPath
        - "extractor://resnet50_imagenet" → ResNet50 ImageNet
        - "models/trained_model.pt" → classification model (Phase 3)

        Args:
            model_path: Chemin ou identifiant
                - "extractor://<name>" pour feature extractors
                - Chemin fichier pour modèles entraînés
            model_config: Configuration
                {
                    "model_id": str,
                    "mode": "extractor" | "classifier",  # auto-détecté si absent
                    "classes": [...],          # pour classifier
                    "tile_size": 224,
                    "batch_size": 32,
                    "num_mc_samples": 10,      # Monte Carlo pour classifier
                }
        """
        if not self._slideflow_available:
            raise ModelLoadError(
                "Slideflow not installed. Install: pip install slideflow[torch]",
                model_path=model_path,
                provider="slideflow",
            )

        try:
            # Determine mode
            explicit_mode = model_config.get("mode", "")
            extractor_name = self._parse_extractor_name(model_path)

            if explicit_mode == "extractor" or extractor_name:
                self._load_extractor(extractor_name or model_path, model_config)
            elif explicit_mode == "classifier" or Path(model_path).exists():
                self._load_classifier(model_path, model_config)
            # Default: try extractor first
            elif model_path.lower() in KNOWN_EXTRACTORS:
                self._load_extractor(model_path.lower(), model_config)
            else:
                self._load_classifier(model_path, model_config)

        except ModelLoadError:
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise ModelLoadError(
                f"Failed to load: {e!s}",
                model_path=model_path,
                model_id=model_config.get("model_id", ""),
                provider="slideflow",
                details={"error": str(e)},
            )

    def _parse_extractor_name(self, model_path: str) -> Optional[str]:
        """Parse extractor name from path like 'extractor://ctranspath'."""
        if model_path.startswith("extractor://"):
            return model_path.replace("extractor://", "").strip().lower()
        if model_path.lower() in KNOWN_EXTRACTORS:
            return model_path.lower()
        return None

    def _load_extractor(self, extractor_name: str, model_config: Dict) -> None:
        """
        Charge un feature extractor pré-entraîné.

        Les poids sont téléchargés automatiquement depuis Hugging Face
        lors de la première utilisation.

        Supports:
        - Slideflow built-in extractors (via sf.build_feature_extractor)
        - Custom extractors loaded directly via transformers (phikon-v2, etc.)
        """
        if extractor_name not in KNOWN_EXTRACTORS:
            available = ", ".join(sorted(KNOWN_EXTRACTORS.keys()))
            raise ModelLoadError(
                f"Unknown extractor '{extractor_name}'. Available: {available}",
                model_path=f"extractor://{extractor_name}",
                provider="slideflow",
            )

        info = KNOWN_EXTRACTORS[extractor_name]
        logger.info(
            f"Loading feature extractor: {extractor_name} "
            f"(dim={info['dim']}, tile_px={info['tile_px']}, "
            f"package={info['package']})"
        )

        if extractor_name in CUSTOM_EXTRACTORS:
            # Custom extractor loaded via transformers (bypass slideflow)
            self.extractor = _PhikonExtractor(device=self.device)
        else:
            try:
                self.extractor = self.sf.build_feature_extractor(
                    extractor_name,
                    tile_px=info["tile_px"],
                    device=self.device,
                )
            except TypeError:
                # Fallback: some extractors don't accept device param
                self.extractor = self.sf.build_feature_extractor(
                    extractor_name, tile_px=info["tile_px"]
                )
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower() or "import" in error_msg.lower():
                    raise ModelLoadError(
                        f"Extractor '{extractor_name}' requires package: {info['package']}. "
                        f"Install with: pip install {info['package']}",
                        model_path=f"extractor://{extractor_name}",
                        provider="slideflow",
                        details={"required_package": info["package"]},
                    )
                raise

        self.mode = "extractor"
        self.model_config = {
            "model_id": model_config.get("model_id", f"{extractor_name}_features"),
            "extractor_name": extractor_name,
            "embedding_dim": info["dim"],
            "tile_size": info["tile_px"],
            "mode": "extractor",
            **{k: v for k, v in model_config.items() if k not in ("mode",)},
        }
        self.model_loaded = True

        logger.info(
            f"Feature extractor loaded: {extractor_name} "
            f"({info['dim']}-dim, device: {self.device})"
        )

    def _load_classifier(self, model_path: str, model_config: Dict) -> None:
        """
        Charge un modèle de classification entraîné (Phase 3).

        Supports:
        - Local files (.pt, .h5, .zip)
        - MLflow URIs (models:/model_name/version)
        - Hugging Face Hub (hf://namespace/model)
        """
        logger.info(f"Loading classification model: {model_path}")

        if model_path.startswith("models:/"):
            model = self._load_from_mlflow(model_path)
        elif model_path.startswith("hf://"):
            model = self._load_from_huggingface(model_path)
        else:
            path = Path(model_path)
            if not path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            model = self.sf.model.load(str(path))

        if self.device == "cuda" and hasattr(model, "cuda"):
            model = model.cuda()

        self.model = model
        self.mode = "classifier"
        self.model_config = {
            "mode": "classifier",
            "tile_size": model_config.get("tile_size", 224),
            **model_config,
        }
        self.model_loaded = True

        logger.info(
            f"Classification model loaded: {model_config.get('model_id', 'unknown')} "
            f"(device: {self.device})"
        )

    def _load_from_mlflow(self, model_uri: str):
        """Charge modèle depuis MLflow Model Registry."""
        try:
            import mlflow

            model_path = mlflow.artifacts.download_artifacts(model_uri)
            return self.sf.model.load(model_path)
        except ImportError:
            raise ModelLoadError(
                "MLflow not installed. Install: pip install mlflow",
                model_path=model_uri,
                provider="slideflow",
            )

    def _load_from_huggingface(self, model_uri: str):
        """Charge modèle depuis Hugging Face Hub."""
        try:
            from huggingface_hub import hf_hub_download

            namespace, model_name = model_uri.replace("hf://", "").split("/", 1)
            model_path = hf_hub_download(repo_id=f"{namespace}/{model_name}", filename="model.pt")
            return self.sf.model.load(model_path)
        except ImportError:
            raise ModelLoadError(
                "huggingface_hub not installed. Install: pip install huggingface_hub",
                model_path=model_uri,
                provider="slideflow",
            )

    def unload_model(self) -> None:
        """Décharge modèle/extractor de la mémoire."""
        if self.model is not None:
            del self.model
            self.model = None

        if self.extractor is not None:
            del self.extractor
            self.extractor = None

        self.model_loaded = False

        if self.device == "cuda":
            try:
                import torch

                torch.cuda.empty_cache()
            except ImportError:
                pass

        logger.info(f"Model unloaded (was mode: {self.mode})")

    # ========================================================================
    # PREDICT
    # ========================================================================

    def predict(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Prédiction sur slide.

        Mode extractor (Phase 1-2):
            Analyse basée sur features extraites. Classifie tissue/background
            en utilisant les statistiques des embeddings. Pas de vrai modèle ML
            mais utilise les features d'un foundation model pré-entraîné.

        Mode classifier (Phase 3):
            Vraie classification ML avec uncertainty quantification
            (Monte Carlo Dropout).
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        if self.mode == "extractor":
            return self._predict_from_features(slide_path, region)
        else:
            return self._predict_from_classifier(slide_path, region)

    def _predict_from_features(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Prédiction basée sur feature extraction (Phase 1-2).

        Process:
        1. Extraire embeddings via foundation model
        2. Calculer statistiques des features (norms, variance)
        3. Classifier tissue/background via heuristique sur feature norms

        Note:
            Cette méthode ne remplace PAS un modèle entraîné (Phase 3).
            Elle fournit une analyse de base en attendant l'entraînement.
        """
        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "unknown")
        start_time = time.time()

        try:
            tile_size = self.model_config.get("tile_size", 224)
            wsi = self._open_wsi(slide_path, tile_size)

            # Extract features using foundation model
            features = self.extractor(wsi)

            # features shape: (num_tiles, embedding_dim) or (h, w, dim)
            if features.ndim == 3:
                _h, _w, d = features.shape
                features = features.reshape(-1, d)

            # Feature-based analysis - cast to float32 (GPU features may be float16)
            features = features.astype(np.float32) if features.dtype != np.float32 else features
            feature_norms = np.linalg.norm(features, axis=1)
            mean_norm = float(np.mean(feature_norms))
            std_norm = float(np.std(feature_norms))

            # Simple tissue/background classification based on feature activity
            # Higher feature norms = more "interesting" regions
            classes = self.model_config.get("classes", ["tissue", "background"])
            tissue_ratio = float(np.mean(feature_norms > np.median(feature_norms)))

            if tissue_ratio > 0.3:
                pred_class = classes[0] if classes else "tissue"
                confidence = min(0.95, 0.5 + tissue_ratio * 0.4)
            else:
                pred_class = classes[-1] if len(classes) > 1 else "background"
                confidence = min(0.95, 0.5 + (1 - tissue_ratio) * 0.4)

            probabilities = {}
            for cls in classes:
                if cls == pred_class:
                    probabilities[cls] = confidence
                else:
                    probabilities[cls] = (1 - confidence) / max(1, len(classes) - 1)

            execution_time_ms = (time.time() - start_time) * 1000

            result = PredictionResult(
                prediction_class=pred_class,
                confidence=confidence,
                probabilities=probabilities,
                uncertainty=1.0 - confidence,
                execution_time_ms=execution_time_ms,
                model_id=model_id,
                slide_id=slide_id,
                metadata={
                    "provider": "slideflow",
                    "mode": "extractor",
                    "extractor": self.model_config.get("extractor_name", ""),
                    "device": self.device,
                    "num_tiles": features.shape[0],
                    "embedding_dim": features.shape[1],
                    "mean_feature_norm": mean_norm,
                    "std_feature_norm": std_norm,
                    "region": region,
                    "note": "Feature-based analysis. Train a classifier (Phase 3) for real ML predictions.",
                },
            )

            logger.info(
                f"[EXTRACTOR] Prediction: {pred_class} (conf: {confidence:.2%}, "
                f"tiles: {features.shape[0]}, time: {execution_time_ms:.0f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Feature-based prediction failed: {e}", exc_info=True)
            raise PredictionError(
                f"Feature-based prediction failed: {e!s}",
                slide_path=slide_path,
                slide_id=slide_id,
                model_id=model_id,
                region=region,
                provider="slideflow",
                details={"mode": "extractor", "error": str(e)},
            )

    def _predict_from_classifier(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Vraie classification ML avec Monte Carlo Dropout (Phase 3).

        Process:
        1. Load WSI et tiling
        2. Multiple forward passes avec dropout (MC)
        3. Aggregation + uncertainty quantification
        """
        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "unknown")
        start_time = time.time()

        try:
            tile_size = self.model_config.get("tile_size", 224)
            wsi = self.sf.WSI(slide_path, tile_px=tile_size)

            if region:
                x, y, w, h = region
                tiles = wsi.build_generator(region=(x, y, w, h))
            else:
                tiles = wsi.build_generator()

            # Monte Carlo Dropout
            num_mc_samples = self.model_config.get("num_mc_samples", 10)
            predictions_mc = []

            for _ in range(num_mc_samples):
                pred = self.model.predict(tiles, training=True)
                predictions_mc.append(pred)

            predictions_mc = np.array(predictions_mc)
            mean_pred = predictions_mc.mean(axis=0)
            uncertainty = float(predictions_mc.var(axis=0).mean())

            classes = self.model_config.get("classes", [])
            pred_class_idx = np.argmax(mean_pred)
            pred_class = classes[pred_class_idx] if classes else f"class_{pred_class_idx}"
            confidence = float(mean_pred[pred_class_idx])

            if classes:
                probabilities = {cls: float(mean_pred[i]) for i, cls in enumerate(classes)}
            else:
                probabilities = {f"class_{i}": float(p) for i, p in enumerate(mean_pred)}

            execution_time_ms = (time.time() - start_time) * 1000

            result = PredictionResult(
                prediction_class=pred_class,
                confidence=confidence,
                probabilities=probabilities,
                uncertainty=uncertainty,
                execution_time_ms=execution_time_ms,
                model_id=model_id,
                slide_id=slide_id,
                metadata={
                    "provider": "slideflow",
                    "mode": "classifier",
                    "device": self.device,
                    "num_mc_samples": num_mc_samples,
                    "region": region,
                },
            )

            logger.info(
                f"[CLASSIFIER] Prediction: {pred_class} (conf: {confidence:.2%}, "
                f"unc: {uncertainty:.3f}, time: {execution_time_ms:.0f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Classification failed: {e}", exc_info=True)
            raise PredictionError(
                f"Classification failed: {e!s}",
                slide_path=slide_path,
                slide_id=slide_id,
                model_id=model_id,
                region=region,
                provider="slideflow",
                details={"mode": "classifier", "error": str(e)},
            )

    # ========================================================================
    # FEATURE EXTRACTION
    # ========================================================================

    def extract_features(
        self, slide_path: str, tile_size: int = 224, overlap: int = 0
    ) -> FeatureExtractionResult:
        """
        Extraction de features (embeddings).

        Mode extractor: Utilise le foundation model directement.
        Mode classifier: Utilise le backbone du modèle (sans classification head).
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "unknown")

        try:
            logger.info(f"Extracting features: {slide_id} (mode: {self.mode})")

            tile_px = self.model_config.get("tile_size", tile_size)
            wsi = self._open_wsi(slide_path, tile_px)

            if self.mode == "extractor":
                # Feature extractor mode - direct extraction
                raw_features = self.extractor(wsi)

                if raw_features.ndim == 3:
                    h, w, d = raw_features.shape
                    embeddings = raw_features.reshape(-1, d)
                    # Generate grid coordinates
                    coords = []
                    for yi in range(h):
                        for xi in range(w):
                            coords.append((xi * tile_px, yi * tile_px))
                    coordinates = coords
                else:
                    embeddings = raw_features
                    coordinates = [(i * tile_px, 0) for i in range(len(embeddings))]

            else:
                # Classifier mode - use backbone
                feature_extractor = self.model.get_feature_extractor()
                embeddings_list = []
                coordinates = []

                for tile, (x, y) in wsi.build_generator(return_coords=True):
                    feats = feature_extractor(tile)
                    if hasattr(feats, "cpu"):
                        feats = feats.cpu().numpy()
                    elif hasattr(feats, "numpy"):
                        feats = feats.numpy()
                    embeddings_list.append(feats)
                    coordinates.append((int(x), int(y)))

                embeddings = np.vstack(embeddings_list)

            # Ensure float32
            embeddings = embeddings.astype(np.float32)

            result = FeatureExtractionResult(
                embeddings=embeddings,
                coordinates=coordinates,
                slide_id=slide_id,
                model_id=model_id,
                tile_size=tile_px,
                metadata={
                    "provider": "slideflow",
                    "mode": self.mode,
                    "device": self.device,
                    "extractor": self.model_config.get("extractor_name", ""),
                    "overlap": overlap,
                },
            )

            logger.info(
                f"Extracted {result.num_patches} patches, "
                f"{result.embedding_dim}-dim features (mode: {self.mode})"
            )

            return result

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}", exc_info=True)
            raise FeatureExtractionError(
                f"Feature extraction failed: {e!s}",
                slide_path=slide_path,
                tile_size=tile_size,
                provider="slideflow",
                details={"mode": self.mode, "error": str(e)},
            )

    # ========================================================================
    # HEATMAP
    # ========================================================================

    def generate_heatmap(
        self, slide_path: str, prediction_class: str, resolution_level: int = 2
    ) -> HeatmapResult:
        """
        Génère heatmap d'explainability.

        Mode extractor: Attention map basée sur feature norms.
            Les régions avec des activations fortes sont mises en évidence.
        Mode classifier: Grad-CAM (gradient-based class activation).
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        if self.mode == "extractor":
            return self._heatmap_from_features(slide_path, prediction_class, resolution_level)
        else:
            return self._heatmap_from_gradcam(slide_path, prediction_class, resolution_level)

    def _heatmap_from_features(
        self, slide_path: str, prediction_class: str, resolution_level: int
    ) -> HeatmapResult:
        """
        Heatmap basée sur feature norms (Phase 1-2).

        Les feature norms du foundation model servent de proxy pour
        l'attention: les régions avec des features plus "actives"
        sont plus susceptibles de contenir du tissu intéressant.
        """
        slide_id = Path(slide_path).stem

        try:
            logger.info(f"[EXTRACTOR] Generating attention heatmap: {slide_id}")

            tile_size = self.model_config.get("tile_size", 224)
            wsi = self._open_wsi(slide_path, tile_size)

            raw_features = self.extractor(wsi)

            if raw_features.ndim == 3:
                # Shape (h, w, dim) → compute norm per spatial position
                feature_norms = np.linalg.norm(raw_features, axis=2)
            else:
                # Shape (n, dim) → need to reshape to 2D grid
                norms = np.linalg.norm(raw_features, axis=1)
                grid_size = int(np.ceil(np.sqrt(len(norms))))
                padded = np.zeros(grid_size * grid_size)
                padded[: len(norms)] = norms
                feature_norms = padded.reshape(grid_size, grid_size)

            # Normalize [0, 1] - cast to float32 (GPU features may be float16)
            feature_norms = feature_norms.astype(np.float32)
            heatmap = (feature_norms - feature_norms.min()) / (
                feature_norms.max() - feature_norms.min() + 1e-8
            )

            # Resize to target resolution
            target_size = max(64, 256 // (2**resolution_level))
            if heatmap.shape[0] != target_size or heatmap.shape[1] != target_size:
                try:
                    from scipy.ndimage import zoom

                    scale_h = target_size / heatmap.shape[0]
                    scale_w = target_size / heatmap.shape[1]
                    heatmap = zoom(heatmap, (scale_h, scale_w), order=1)
                except ImportError:
                    # Fallback: simple resize with numpy
                    from PIL import Image

                    img = Image.fromarray((heatmap * 255).astype(np.uint8))
                    img = img.resize((target_size, target_size), Image.BILINEAR)
                    heatmap = np.array(img).astype(np.float32) / 255.0

            # Re-normalize after resize
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
            heatmap = heatmap.astype(np.float32)

            slide_dimensions = wsi.dimensions if hasattr(wsi, "dimensions") else (20000, 15000)

            result = HeatmapResult(
                heatmap=heatmap,
                slide_dimensions=slide_dimensions,
                resolution_level=resolution_level,
                slide_id=slide_id,
                method="feature_attention",
                target_class=prediction_class,
                metadata={
                    "provider": "slideflow",
                    "mode": "extractor",
                    "extractor": self.model_config.get("extractor_name", ""),
                    "note": "Attention proxy from feature norms. Use trained model (Phase 3) for Grad-CAM.",
                },
            )

            logger.info(f"[EXTRACTOR] Attention heatmap generated: {heatmap.shape}")
            return result

        except Exception as e:
            logger.error(f"Feature heatmap failed: {e}", exc_info=True)
            raise HeatmapGenerationError(
                f"Feature-based heatmap failed: {e!s}",
                slide_path=slide_path,
                prediction_class=prediction_class,
                method="feature_attention",
                provider="slideflow",
                details={"mode": "extractor", "error": str(e)},
            )

    def _heatmap_from_gradcam(
        self, slide_path: str, prediction_class: str, resolution_level: int
    ) -> HeatmapResult:
        """Grad-CAM heatmap avec modèle de classification (Phase 3)."""
        slide_id = Path(slide_path).stem

        try:
            logger.info(f"[CLASSIFIER] Generating Grad-CAM heatmap: {slide_id}")

            classes = self.model_config.get("classes", [])
            if classes and prediction_class not in classes:
                raise ValueError(f"Class '{prediction_class}' not in model classes: {classes}")

            wsi = self.sf.WSI(slide_path, tile_px=224)

            heatmap_generator = self.sf.grad.GradientHeatmap(
                model=self.model,
                target_class=prediction_class,
                method="gradcam",
            )

            heatmap = heatmap_generator.generate(
                wsi,
                level=resolution_level,
                batch_size=self.model_config.get("batch_size", 32),
            )

            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)

            result = HeatmapResult(
                heatmap=heatmap,
                slide_dimensions=wsi.dimensions,
                resolution_level=resolution_level,
                slide_id=slide_id,
                method="gradcam",
                target_class=prediction_class,
                metadata={
                    "provider": "slideflow",
                    "mode": "classifier",
                    "device": self.device,
                },
            )

            logger.info(f"[CLASSIFIER] Grad-CAM heatmap: {heatmap.shape}")
            return result

        except Exception as e:
            logger.error(f"Grad-CAM heatmap failed: {e}", exc_info=True)
            raise HeatmapGenerationError(
                f"Grad-CAM heatmap failed: {e!s}",
                slide_path=slide_path,
                prediction_class=prediction_class,
                method="gradcam",
                provider="slideflow",
                details={"mode": "classifier", "error": str(e)},
            )

    # ========================================================================
    # MODEL INFO
    # ========================================================================

    def get_model_info(self) -> Dict:
        """Retourne metadata du modèle/extractor chargé."""
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        base_info = {
            "model_id": self.model_config.get("model_id", "unknown"),
            "model_name": self.model_config.get("model_name", ""),
            "version": self.model_config.get("version", ""),
            "task_type": self.model_config.get("task_type", "classification"),
            "classes": self.model_config.get("classes", []),
            "input_size": (
                self.model_config.get("tile_size", 224),
                self.model_config.get("tile_size", 224),
            ),
            "device": self.device,
            "provider": "slideflow",
            "mode": self.mode,
            "slideflow_version": self.sf.__version__ if self._slideflow_available else "N/A",
        }

        if self.mode == "extractor":
            extractor_name = self.model_config.get("extractor_name", "")
            base_info.update(
                {
                    "extractor_name": extractor_name,
                    "embedding_dim": self.model_config.get("embedding_dim", 0),
                    "task_type": "feature_extraction",
                    "reference_metrics": {},
                    "capabilities": [
                        "extract_features",
                        "predict (feature-based, approximate)",
                        "generate_heatmap (attention proxy)",
                    ],
                    "upgrade_path": "Train a classifier on extracted features for Phase 3",
                }
            )
        else:
            base_info.update(
                {
                    "reference_metrics": self.model_config.get("reference_metrics", {}),
                    "capabilities": [
                        "predict (ML classification)",
                        "extract_features",
                        "generate_heatmap (Grad-CAM)",
                    ],
                }
            )

        return base_info
