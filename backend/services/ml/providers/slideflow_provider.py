"""
Slideflow ML Provider

Implémentation de MLProvider interface avec Slideflow framework.

Slideflow: https://github.com/slideflow/slideflow
- Open-source framework pour deep learning sur whole slide images
- Développé par Mahmood Lab (Harvard Medical School)
- Support PyTorch & TensorFlow
- Features: MIL, SSL, normalisation coloration, explainability

References:
- Dolezal et al. (2023): "Slideflow: Deep Learning for Digital Histopathology"
  https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-024-05758-x
- Mahmood Lab: https://faisal.ai/
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from core.exceptions import (
    FeatureExtractionError,
    HeatmapGenerationError,
    MLModelNotLoadedError,
    ModelLoadError,
    PredictionError,
)
from core.interfaces import FeatureExtractionResult, HeatmapResult, PredictionResult

logger = logging.getLogger(__name__)


class SlideflowProvider:
    """
    ML Provider basé sur Slideflow.

    Features:
    - Model loading (local, MLflow, Hugging Face)
    - Inference avec uncertainty quantification (Monte Carlo Dropout)
    - Feature extraction pour MIL
    - Heatmap generation (Grad-CAM, attention)
    - GPU/CPU support avec fallback automatique
    - Lazy loading (ne charge que si Slideflow installé)

    Usage:
        >>> provider = SlideflowProvider(device="auto")
        >>> provider.load_model("models:/gleason_grading/production", config)
        >>> result = provider.predict("path/to/slide.mrxs")
        >>> print(f"Prediction: {result.prediction_class} ({result.confidence:.2%})")
    """

    def __init__(self, device: str = "auto"):
        """
        Initialize Slideflow provider.

        Args:
            device: "cuda", "cpu", or "auto" (détection automatique)
        """
        self.device = self._detect_device(device)
        self.model = None
        self.model_config = {}
        self.model_loaded = False

        # Check Slideflow availability
        self._slideflow_available = self._check_slideflow()

        if not self._slideflow_available:
            logger.warning(
                "Slideflow not installed. ML features disabled. "
                "Install with: pip install slideflow[tf] or slideflow[torch]"
            )
        else:
            logger.info(f"Slideflow provider initialized (device: {self.device})")

    # ========================================================================
    # INITIALIZATION & SETUP
    # ========================================================================

    def _check_slideflow(self) -> bool:
        """
        Vérifie disponibilité Slideflow.

        Returns:
            True si Slideflow disponible, False sinon
        """
        try:
            import slideflow as sf

            self.sf = sf
            logger.debug(f"Slideflow version: {sf.__version__}")
            return True
        except ImportError:
            logger.debug("Slideflow not installed")
            return False

    def _detect_device(self, device: str) -> str:
        """
        Détecte device disponible (GPU ou fallback CPU).

        Args:
            device: "cuda", "cpu", "auto"

        Returns:
            Device string ("cuda" ou "cpu")
        """
        if device == "auto":
            try:
                import torch

                if torch.cuda.is_available():
                    gpu_name = torch.cuda.get_device_name(0)
                    logger.info(f"GPU detected: {gpu_name}")
                    return "cuda"
                else:
                    logger.info("No GPU detected, using CPU")
                    return "cpu"
            except ImportError:
                # Try TensorFlow
                try:
                    import tensorflow as tf

                    gpus = tf.config.list_physical_devices("GPU")
                    if gpus:
                        logger.info(f"GPU detected: {gpus[0].name}")
                        return "cuda"  # Use "cuda" as generic GPU indicator
                    else:
                        logger.info("No GPU detected, using CPU")
                        return "cpu"
                except ImportError:
                    logger.warning("Neither PyTorch nor TensorFlow found, defaulting to CPU")
                    return "cpu"
        return device

    # ========================================================================
    # MODEL MANAGEMENT
    # ========================================================================

    def load_model(self, model_path: str, model_config: Dict) -> None:
        """
        Charge modèle Slideflow depuis artefact.

        Supports:
        - Local files (.pt, .h5, .zip)
        - MLflow URIs (models:/model_name/version)
        - Hugging Face Hub (hf://namespace/model)
        - S3/MinIO (s3://bucket/path)

        Args:
            model_path: Chemin vers modèle
            model_config: Configuration
                {
                    "model_id": "gleason_grading_v2",
                    "device": "cuda",
                    "batch_size": 32,
                    "tile_size": 224,
                    "classes": ["gleason_3", "gleason_4", "gleason_5"],
                    "num_mc_samples": 10  # Pour uncertainty
                }

        Raises:
            ModelLoadError: Si chargement échoue
        """
        if not self._slideflow_available:
            raise ModelLoadError(
                "Slideflow not installed. Install with: pip install slideflow[tf] or slideflow[torch]",
                model_path=model_path,
                provider="slideflow",
            )

        try:
            logger.info(f"Loading model: {model_path}")

            # Déterminer source
            if model_path.startswith("models:/"):
                # MLflow model
                model = self._load_from_mlflow(model_path)
            elif model_path.startswith("hf://"):
                # Hugging Face Hub
                model = self._load_from_huggingface(model_path)
            elif model_path.startswith("s3://"):
                # S3/MinIO
                model = self._load_from_s3(model_path)
            else:
                # Local file
                model = self._load_from_local(model_path)

            # Configure device
            if self.device == "cuda":
                model = self._move_to_gpu(model)

            self.model = model
            self.model_config = model_config
            self.model_loaded = True

            logger.info(
                f"Model loaded successfully: {model_config.get('model_id', 'unknown')} "
                f"(device: {self.device})"
            )

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise ModelLoadError(
                f"Failed to load model: {e!s}",
                model_path=model_path,
                model_id=model_config.get("model_id", ""),
                provider="slideflow",
                details={"error": str(e)},
            )

    def _load_from_local(self, model_path: str):
        """Charge modèle depuis fichier local."""
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Slideflow model loading
        model = self.sf.model.load(str(path))
        return model

    def _load_from_mlflow(self, model_uri: str):
        """
        Charge modèle depuis MLflow Model Registry.

        Format: models:/model_name/version
        Exemple: models:/gleason_grading/production
        """
        try:
            import mlflow

            # Parse URI: models:/gleason_grading/production
            model_name = model_uri.split("/")[1]
            stage_or_version = model_uri.split("/")[-1]

            logger.info(f"Loading from MLflow: {model_name} ({stage_or_version})")

            # Download model
            model_path = mlflow.artifacts.download_artifacts(model_uri)
            model = self.sf.model.load(model_path)

            return model

        except ImportError:
            raise ModelLoadError(
                "MLflow not installed. Install with: pip install mlflow",
                model_path=model_uri,
                provider="slideflow",
            )

    def _load_from_huggingface(self, model_uri: str):
        """
        Charge modèle depuis Hugging Face Hub.

        Format: hf://namespace/model
        Exemple: hf://facebook/dino-vitb16
        """
        try:
            from huggingface_hub import hf_hub_download

            # Parse URI: hf://facebook/dino-vitb16
            namespace, model_name = model_uri.replace("hf://", "").split("/")

            logger.info(f"Loading from Hugging Face: {namespace}/{model_name}")

            # Download model
            model_path = hf_hub_download(repo_id=f"{namespace}/{model_name}", filename="model.pt")
            model = self.sf.model.load(model_path)

            return model

        except ImportError:
            raise ModelLoadError(
                "huggingface_hub not installed. Install with: pip install huggingface_hub",
                model_path=model_uri,
                provider="slideflow",
            )

    def _load_from_s3(self, model_uri: str):
        """
        Charge modèle depuis S3/MinIO.

        Format: s3://bucket/path/to/model.pt
        """
        try:
            import boto3

            # Parse S3 URI
            bucket = model_uri.split("/")[2]
            key = "/".join(model_uri.split("/")[3:])

            logger.info(f"Loading from S3: {bucket}/{key}")

            # Download to temp location
            import tempfile

            temp_dir = tempfile.mkdtemp()
            local_path = Path(temp_dir) / "model.pt"

            s3 = boto3.client("s3")
            s3.download_file(bucket, key, str(local_path))

            model = self.sf.model.load(str(local_path))
            return model

        except ImportError:
            raise ModelLoadError(
                "boto3 not installed. Install with: pip install boto3",
                model_path=model_uri,
                provider="slideflow",
            )

    def _move_to_gpu(self, model):
        """Move model to GPU si disponible."""
        try:
            # PyTorch
            if hasattr(model, "cuda"):
                model = model.cuda()
                logger.debug("Model moved to GPU (PyTorch)")
            # TensorFlow
            elif hasattr(model, "to_device"):
                model.to_device("GPU:0")
                logger.debug("Model moved to GPU (TensorFlow)")
        except Exception as e:
            logger.warning(f"Failed to move model to GPU: {e}. Falling back to CPU.")
            self.device = "cpu"

        return model

    def unload_model(self) -> None:
        """Décharge modèle de la mémoire."""
        if self.model is not None:
            del self.model
            self.model = None
            self.model_loaded = False

            # Free GPU memory
            if self.device == "cuda":
                try:
                    import torch

                    torch.cuda.empty_cache()
                    logger.debug("GPU cache cleared")
                except ImportError:
                    try:
                        import tensorflow as tf

                        tf.keras.backend.clear_session()
                        logger.debug("TensorFlow session cleared")
                    except ImportError:
                        pass

            logger.info("Model unloaded")

    # ========================================================================
    # INFERENCE
    # ========================================================================

    def predict(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Prédiction avec uncertainty quantification (Monte Carlo Dropout).

        Process:
        1. Load WSI
        2. Extract tiles (avec region si spécifiée)
        3. Multiple forward passes avec dropout (Monte Carlo)
        4. Aggregation predictions
        5. Calcul uncertainty (variance)

        Args:
            slide_path: Chemin vers lame
            region: (x, y, width, height) optionnel

        Returns:
            PredictionResult avec classe, confidence, uncertainty

        References:
            - Gal & Ghahramani (2016): "Dropout as a Bayesian Approximation"
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "unknown")

        try:
            start_time = time.time()

            # Load WSI
            tile_size = self.model_config.get("tile_size", 224)
            wsi = self.sf.WSI(slide_path, tile_px=tile_size)

            # Build tile generator
            if region:
                x, y, w, h = region
                tiles = wsi.build_generator(region=(x, y, w, h))
                logger.debug(f"Extracting tiles from region: {region}")
            else:
                tiles = wsi.build_generator()
                logger.debug(f"Extracting tiles from full slide")

            # Monte Carlo Dropout for uncertainty
            num_mc_samples = self.model_config.get("num_mc_samples", 10)
            predictions_mc = []

            for i in range(num_mc_samples):
                # Enable dropout during inference
                pred = self.model.predict(tiles, training=True)
                predictions_mc.append(pred)

            # Aggregation
            predictions_mc = np.array(predictions_mc)  # Shape: (num_mc_samples, num_classes)
            mean_pred = predictions_mc.mean(axis=0)
            uncertainty = predictions_mc.var(axis=0).mean()  # Epistemic uncertainty

            # Predicted class
            classes = self.model_config.get("classes", [])
            pred_class_idx = np.argmax(mean_pred)
            pred_class = classes[pred_class_idx] if classes else f"class_{pred_class_idx}"
            confidence = float(mean_pred[pred_class_idx])

            # Probabilities dict
            if classes:
                probabilities = {cls: float(mean_pred[i]) for i, cls in enumerate(classes)}
            else:
                probabilities = {f"class_{i}": float(p) for i, p in enumerate(mean_pred)}

            execution_time_ms = (time.time() - start_time) * 1000

            result = PredictionResult(
                prediction_class=pred_class,
                confidence=confidence,
                probabilities=probabilities,
                uncertainty=float(uncertainty),
                execution_time_ms=execution_time_ms,
                model_id=model_id,
                slide_id=slide_id,
                metadata={
                    "device": self.device,
                    "num_mc_samples": num_mc_samples,
                    "region": region,
                },
            )

            logger.info(
                f"Prediction: {pred_class} (conf: {confidence:.2%}, "
                f"unc: {uncertainty:.3f}, time: {execution_time_ms:.0f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            raise PredictionError(
                f"Prediction failed: {e!s}",
                slide_path=slide_path,
                slide_id=slide_id,
                model_id=model_id,
                region=region,
                provider="slideflow",
                details={"error": str(e)},
            )

    # ========================================================================
    # FEATURE EXTRACTION (MIL)
    # ========================================================================

    def extract_features(
        self, slide_path: str, tile_size: int = 224, overlap: int = 0
    ) -> FeatureExtractionResult:
        """
        Extraction features pour Multiple Instance Learning.

        Process:
        1. Tiling slide
        2. Forward pass à travers backbone (sans classification head)
        3. Extraction features dernière couche
        4. Retour embeddings + coordonnées

        Args:
            slide_path: Chemin vers lame
            tile_size: Taille tiles (px)
            overlap: Chevauchement tiles (px)

        Returns:
            FeatureExtractionResult avec embeddings (N, D)

        References:
            - Ilse et al. (2018): "Attention-based Deep MIL"
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "unknown")

        try:
            logger.info(f"Extracting features: {slide_id}")

            # Load WSI
            wsi = self.sf.WSI(slide_path, tile_px=tile_size, overlap_px=overlap)

            # Get feature extractor (backbone without classification head)
            feature_extractor = self.model.get_feature_extractor()

            embeddings = []
            coordinates = []

            # Extract features for each tile
            for tile, (x, y) in wsi.build_generator(return_coords=True):
                # Forward pass through backbone
                features = feature_extractor(tile)

                # Convert to numpy
                if hasattr(features, "cpu"):
                    features = features.cpu().numpy()
                elif hasattr(features, "numpy"):
                    features = features.numpy()

                embeddings.append(features)
                coordinates.append((int(x), int(y)))

            # Stack embeddings
            embeddings = np.vstack(embeddings)  # Shape: (N, D)

            result = FeatureExtractionResult(
                embeddings=embeddings,
                coordinates=coordinates,
                slide_id=slide_id,
                model_id=model_id,
                tile_size=tile_size,
                metadata={"device": self.device, "overlap": overlap},
            )

            logger.info(
                f"Extracted {result.num_patches} patches, {result.embedding_dim}-dim features"
            )

            return result

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}", exc_info=True)
            raise FeatureExtractionError(
                f"Feature extraction failed: {e!s}",
                slide_path=slide_path,
                tile_size=tile_size,
                provider="slideflow",
                details={"error": str(e)},
            )

    # ========================================================================
    # EXPLAINABILITY (HEATMAPS)
    # ========================================================================

    def generate_heatmap(
        self, slide_path: str, prediction_class: str, resolution_level: int = 2
    ) -> HeatmapResult:
        """
        Génère heatmap d'explainability (Grad-CAM).

        Process:
        1. Forward pass pour obtenir prédiction
        2. Backward pass pour obtenir gradients
        3. Weight feature maps par gradients
        4. Generate heatmap overlay

        Args:
            slide_path: Chemin vers lame
            prediction_class: Classe pour heatmap
            resolution_level: Niveau résolution (0=max)

        Returns:
            HeatmapResult avec heatmap normalisée [0, 1]

        References:
            - Selvaraju et al. (2017): "Grad-CAM"
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        slide_id = Path(slide_path).stem

        try:
            logger.info(f"Generating heatmap: {slide_id}, class: {prediction_class}")

            # Validate class
            classes = self.model_config.get("classes", [])
            if classes and prediction_class not in classes:
                raise ValueError(f"Class '{prediction_class}' not in model classes: {classes}")

            # Load WSI
            wsi = self.sf.WSI(slide_path, tile_px=224)

            # Generate heatmap using Grad-CAM
            heatmap_generator = self.sf.grad.GradientHeatmap(
                model=self.model, target_class=prediction_class, method="gradcam"
            )

            heatmap = heatmap_generator.generate(
                wsi, level=resolution_level, batch_size=self.model_config.get("batch_size", 32)
            )

            # Normalize [0, 1]
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)

            result = HeatmapResult(
                heatmap=heatmap,
                slide_dimensions=wsi.dimensions,
                resolution_level=resolution_level,
                slide_id=slide_id,
                method="gradcam",
                target_class=prediction_class,
                metadata={"device": self.device},
            )

            logger.info(f"Heatmap generated: shape {heatmap.shape}")

            return result

        except Exception as e:
            logger.error(f"Heatmap generation failed: {e}", exc_info=True)
            raise HeatmapGenerationError(
                f"Heatmap generation failed: {e!s}",
                slide_path=slide_path,
                prediction_class=prediction_class,
                method="gradcam",
                provider="slideflow",
                details={"error": str(e)},
            )

    # ========================================================================
    # MODEL INFO
    # ========================================================================

    def get_model_info(self) -> Dict:
        """
        Retourne metadata du modèle chargé.

        Returns:
            Dict avec model_id, version, classes, metrics, etc.
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        info = {
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
            "reference_metrics": self.model_config.get("reference_metrics", {}),
            "provider": "slideflow",
            "slideflow_version": self.sf.__version__ if self._slideflow_available else "N/A",
        }

        return info
