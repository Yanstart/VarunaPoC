"""
Mock ML Provider

Provider mock pour tests et développement sans Slideflow.

Use cases:
- Tests unitaires (pas besoin d'installer Slideflow)
- Développement frontend (API fonctionne sans ML backend)
- CI/CD (tests rapides sans dépendances lourdes)

Usage:
    >>> provider = MockProvider()
    >>> provider.load_model("mock://model", {})
    >>> result = provider.predict("slide.mrxs")
    >>> print(result.prediction_class)  # "mock_class_1"
"""

import logging
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from core.exceptions import MLModelNotLoadedError, ModelLoadError
from core.interfaces import FeatureExtractionResult, HeatmapResult, PredictionResult

logger = logging.getLogger(__name__)


class MockProvider:
    """
    Mock ML Provider pour tests et développement.

    Simule comportement d'un vrai provider ML avec données aléatoires réalistes.

    Features:
    - Pas de dépendances externes
    - Latence configurable (simule temps inference)
    - Résultats reproductibles (seed)
    - Erreurs simulables (pour tester error handling)
    """

    def __init__(self, device: str = "cpu", seed: int = 42):
        """
        Initialize mock provider.

        Args:
            device: Ignoré (toujours "cpu")
            seed: Seed pour reproductibilité
        """
        self.device = "cpu"
        self.model = None
        self.model_config = {}
        self.model_loaded = False
        self.seed = seed

        np.random.seed(seed)
        random.seed(seed)

        logger.info("MockProvider initialized (development/testing mode)")

    # ========================================================================
    # MODEL MANAGEMENT
    # ========================================================================

    def load_model(self, model_path: str, model_config: Dict) -> None:
        """
        Mock model loading.

        Args:
            model_path: Path (ignoré, accepte tout)
            model_config: Configuration (stockée pour référence)
        """
        logger.info(f"[MOCK] Loading model: {model_path}")

        # Simulate loading delay
        time.sleep(0.1)

        self.model = {"mock": True, "path": model_path}
        self.model_config = model_config
        self.model_loaded = True

        logger.info(f"[MOCK] Model loaded: {model_config.get('model_id', 'unknown')} (device: cpu)")

    def unload_model(self) -> None:
        """Mock model unloading."""
        if self.model is not None:
            logger.info("[MOCK] Unloading model")
            self.model = None
            self.model_loaded = False

    # ========================================================================
    # INFERENCE
    # ========================================================================

    def predict(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Mock prediction avec résultats aléatoires réalistes.

        Args:
            slide_path: Chemin slide
            region: Région optionnelle

        Returns:
            PredictionResult avec données mockées
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="mock")

        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "mock_model")

        logger.info(f"[MOCK] Predicting: {slide_id}")

        # Reset seed for reproducibility (hash slide_id for determinism)
        seed_value = self.seed + hash(slide_id + model_id) % 1000
        np.random.seed(seed_value)
        random.seed(seed_value)

        # Simulate inference delay (50-200ms)
        delay = random.uniform(0.05, 0.2)
        time.sleep(delay)

        # Generate mock predictions
        classes = self.model_config.get("classes", ["class_0", "class_1", "class_2"])
        num_classes = len(classes)

        # Random probabilities (sum to 1)
        probs = np.random.dirichlet(np.ones(num_classes))

        # Predicted class
        pred_idx = np.argmax(probs)
        pred_class = classes[pred_idx]
        confidence = float(probs[pred_idx])

        # Mock uncertainty (higher for ambiguous cases)
        uncertainty = random.uniform(0.01, 0.15)

        # Probabilities dict
        probabilities = {cls: float(probs[i]) for i, cls in enumerate(classes)}

        execution_time_ms = delay * 1000

        result = PredictionResult(
            prediction_class=pred_class,
            confidence=confidence,
            probabilities=probabilities,
            uncertainty=uncertainty,
            execution_time_ms=execution_time_ms,
            model_id=model_id,
            slide_id=slide_id,
            metadata={"mock": True, "device": "cpu", "region": region},
        )

        logger.info(
            f"[MOCK] Prediction: {pred_class} (conf: {confidence:.2%}, unc: {uncertainty:.3f})"
        )

        return result

    # ========================================================================
    # FEATURE EXTRACTION
    # ========================================================================

    def extract_features(
        self, slide_path: str, tile_size: int = 224, overlap: int = 0
    ) -> FeatureExtractionResult:
        """
        Mock feature extraction.

        Args:
            slide_path: Chemin slide
            tile_size: Taille tiles
            overlap: Overlap tiles

        Returns:
            FeatureExtractionResult avec embeddings mockés
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="mock")

        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "mock_model")

        logger.info(f"[MOCK] Extracting features: {slide_id}")

        # Simulate extraction delay
        time.sleep(0.2)

        # Mock parameters
        num_patches = random.randint(500, 2000)  # Realistic range
        embedding_dim = self.model_config.get("embedding_dim", 512)

        # Generate random embeddings
        embeddings = np.random.randn(num_patches, embedding_dim).astype(np.float32)

        # Generate grid coordinates (ensure exact match with num_patches)
        grid_size = int(np.ceil(np.sqrt(num_patches)))
        coordinates = []
        for i in range(grid_size):
            for j in range(grid_size):
                if len(coordinates) < num_patches:
                    coordinates.append((i * tile_size, j * tile_size))
                else:
                    break
            if len(coordinates) >= num_patches:
                break

        result = FeatureExtractionResult(
            embeddings=embeddings,
            coordinates=coordinates,
            slide_id=slide_id,
            model_id=model_id,
            tile_size=tile_size,
            metadata={"mock": True, "device": "cpu", "overlap": overlap},
        )

        logger.info(f"[MOCK] Extracted {num_patches} patches, {embedding_dim}-dim features")

        return result

    # ========================================================================
    # HEATMAPS
    # ========================================================================

    def generate_heatmap(
        self, slide_path: str, prediction_class: str, resolution_level: int = 2
    ) -> HeatmapResult:
        """
        Mock heatmap generation.

        Args:
            slide_path: Chemin slide
            prediction_class: Classe pour heatmap
            resolution_level: Niveau résolution

        Returns:
            HeatmapResult avec heatmap mockée
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="mock")

        slide_id = Path(slide_path).stem

        logger.info(f"[MOCK] Generating heatmap: {slide_id}, class: {prediction_class}")

        # Simulate generation delay
        time.sleep(0.3)

        # Generate mock heatmap (Gaussian blobs)
        size = 256 // (2**resolution_level)  # Scale by resolution
        heatmap = self._generate_mock_heatmap(size, size)

        # Mock slide dimensions
        slide_dimensions = (20000, 15000)  # Typical WSI dimensions

        result = HeatmapResult(
            heatmap=heatmap,
            slide_dimensions=slide_dimensions,
            resolution_level=resolution_level,
            slide_id=slide_id,
            method="mock_gradcam",
            target_class=prediction_class,
            metadata={"mock": True, "device": "cpu"},
        )

        logger.info(f"[MOCK] Heatmap generated: shape {heatmap.shape}")

        return result

    def _generate_mock_heatmap(self, height: int, width: int) -> np.ndarray:
        """
        Génère heatmap mockée avec Gaussian blobs.

        Args:
            height: Hauteur
            width: Largeur

        Returns:
            Heatmap normalisée [0, 1]
        """
        heatmap = np.zeros((height, width), dtype=np.float32)

        # Add 3-5 Gaussian blobs (simule régions d'intérêt)
        num_blobs = random.randint(3, 5)

        for _ in range(num_blobs):
            # Random center
            cx = random.randint(0, width - 1)
            cy = random.randint(0, height - 1)

            # Random size
            sigma = random.uniform(width * 0.05, width * 0.15)

            # Generate Gaussian
            y, x = np.ogrid[:height, :width]
            gaussian = np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * sigma**2))

            # Add to heatmap
            heatmap += gaussian * random.uniform(0.5, 1.0)

        # Normalize [0, 1]
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)

        return heatmap

    # ========================================================================
    # MODEL INFO
    # ========================================================================

    def get_model_info(self) -> Dict:
        """
        Mock model info.

        Returns:
            Dict avec metadata mockée
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="mock")

        info = {
            "model_id": self.model_config.get("model_id", "mock_model"),
            "model_name": self.model_config.get("model_name", "Mock Model"),
            "version": self.model_config.get("version", "1.0.0-mock"),
            "task_type": self.model_config.get("task_type", "classification"),
            "classes": self.model_config.get("classes", ["class_0", "class_1", "class_2"]),
            "input_size": (224, 224),
            "device": "cpu",
            "reference_metrics": {
                "accuracy": 0.95,  # Mock metrics
                "auc_roc": 0.98,
                "inference_time_ms": 150,
            },
            "provider": "mock",
            "mock": True,
        }

        return info


# ============================================================================
# TESTING UTILITIES
# ============================================================================


def test_mock_provider():
    """
    Test rapide du mock provider.

    Usage:
        python -m services.ml.providers.mock_provider
    """
    print("\n" + "=" * 80)
    print("MOCK PROVIDER - TEST")
    print("=" * 80 + "\n")

    # Initialize
    provider = MockProvider()

    # Load model
    config = {
        "model_id": "test_model",
        "classes": ["benign", "malignant"],
        "embedding_dim": 512,
    }
    provider.load_model("mock://test_model", config)

    # Test prediction
    print("1. Testing prediction...")
    result = provider.predict("test_slide.mrxs")
    print(f"   Prediction: {result.prediction_class}")
    print(f"   Confidence: {result.confidence:.2%}")
    print(f"   Uncertainty: {result.uncertainty:.3f}")
    print(f"   Time: {result.execution_time_ms:.0f}ms")

    # Test feature extraction
    print("\n2. Testing feature extraction...")
    features = provider.extract_features("test_slide.mrxs")
    print(f"   Embeddings shape: {features.embeddings.shape}")
    print(f"   Num patches: {features.num_patches}")
    print(f"   Embedding dim: {features.embedding_dim}")

    # Test heatmap
    print("\n3. Testing heatmap generation...")
    heatmap = provider.generate_heatmap("test_slide.mrxs", "malignant")
    print(f"   Heatmap shape: {heatmap.heatmap.shape}")
    print(f"   Value range: [{heatmap.heatmap.min():.3f}, {heatmap.heatmap.max():.3f}]")

    # Test model info
    print("\n4. Testing model info...")
    info = provider.get_model_info()
    print(f"   Model ID: {info['model_id']}")
    print(f"   Classes: {info['classes']}")
    print(f"   Device: {info['device']}")

    # Unload
    provider.unload_model()
    print("\n✓ All tests passed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_mock_provider()
