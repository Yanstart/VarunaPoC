"""
ML Provider Interface

Interface abstraite (Protocol) pour providers ML (Slideflow, TorchVision, Hugging Face, etc.).

Principles:
- Dependency Inversion: Code depends on abstractions, not concrete implementations
- Pluggability: Easy to swap providers without changing API
- Testability: Easy to mock for unit tests

References:
- PEP 544 (Structural Subtyping): https://peps.python.org/pep-0544/
- SOLID Principles: Dependency Inversion Principle
- Gang of Four: Strategy Pattern

Usage:
    from core.interfaces import MLProvider
    from services.ml.providers import SlideflowProvider

    provider: MLProvider = SlideflowProvider()
    result = provider.predict("path/to/slide.mrxs")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple

import numpy as np

# ============================================================================
# DATA CLASSES (Results)
# ============================================================================


@dataclass
class PredictionResult:
    """
    Résultat de prédiction ML.

    Attributes:
        prediction_class: Classe prédite (e.g., "gleason_4", "tumor", "benign")
        confidence: Confiance [0, 1] pour classe prédite
        probabilities: Distribution complète sur toutes classes
        uncertainty: Incertitude épistémique [0, 1] (optionnel, via MC Dropout)
        execution_time_ms: Temps d'exécution (optionnel)
        model_id: Identifiant du modèle utilisé
        slide_id: Identifiant de la lame

    References:
        - Gal & Ghahramani (2016): "Dropout as a Bayesian Approximation"
          (pour uncertainty quantification)
        - Guo et al. (2017): "On Calibration of Modern Neural Networks"
          (pour confidence calibration)

    Examples:
        >>> result = PredictionResult(
        ...     prediction_class="gleason_4",
        ...     confidence=0.92,
        ...     probabilities={"gleason_3": 0.05, "gleason_4": 0.92, "gleason_5": 0.03},
        ...     uncertainty=0.05,
        ...     execution_time_ms=2340,
        ...     model_id="gleason_grading_v2",
        ...     slide_id="slide_abc123"
        ... )
    """

    prediction_class: str
    confidence: float
    probabilities: Dict[str, float]
    uncertainty: Optional[float] = None
    execution_time_ms: Optional[float] = None
    model_id: str = ""
    slide_id: str = ""
    metadata: Dict = field(default_factory=dict)  # Extra info (device, batch_size, etc.)

    def __post_init__(self):
        """Validation des valeurs."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0, 1], got {self.confidence}")

        if self.uncertainty is not None and not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError(f"Uncertainty must be in [0, 1], got {self.uncertainty}")

        # Vérifier que probabilités somment à ~1.0
        prob_sum = sum(self.probabilities.values())
        if not 0.98 <= prob_sum <= 1.02:
            raise ValueError(f"Probabilities must sum to 1.0, got {prob_sum}")


@dataclass
class FeatureExtractionResult:
    """
    Résultat d'extraction de features (embeddings).

    Used for:
    - Multiple Instance Learning (MIL)
    - Active learning (uncertainty sampling)
    - Similarity search
    - Dataset clustering

    Attributes:
        embeddings: Features (N patches, D dimensions)
        coordinates: Coordonnées (x, y) pour chaque patch
        slide_id: Identifiant de la lame
        model_id: Identifiant du modèle (backbone)
        embedding_dim: Dimensionnalité features
        num_patches: Nombre de patches extraits
        tile_size: Taille des patches (px)

    References:
        - Ilse et al. (2018): "Attention-based Deep Multiple Instance Learning"
        - Lu et al. (2021): "Data-efficient Computational Pathology"
        - CLAM: https://github.com/mahmoodlab/CLAM

    Examples:
        >>> result = FeatureExtractionResult(
        ...     embeddings=np.random.randn(1000, 512),  # 1000 patches, 512-dim features
        ...     coordinates=[(0, 0), (224, 0), ...],
        ...     slide_id="slide_abc123",
        ...     model_id="resnet50_imagenet"
        ... )
    """

    embeddings: np.ndarray  # Shape: (N, D)
    coordinates: List[Tuple[int, int]]  # [(x1, y1), (x2, y2), ...]
    slide_id: str = ""
    model_id: str = ""
    embedding_dim: Optional[int] = None
    num_patches: Optional[int] = None
    tile_size: Optional[int] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Calcul automatique dimensions."""
        if self.embeddings.ndim != 2:
            raise ValueError(f"Embeddings must be 2D (N, D), got shape {self.embeddings.shape}")

        self.num_patches = self.embeddings.shape[0]
        self.embedding_dim = self.embeddings.shape[1]

        if len(self.coordinates) != self.num_patches:
            raise ValueError(
                f"Coordinates length ({len(self.coordinates)}) must match "
                f"num_patches ({self.num_patches})"
            )


@dataclass
class HeatmapResult:
    """
    Résultat de génération de heatmap (explainability).

    Methods supportées:
    - Grad-CAM (gradient-based)
    - Attention weights (MIL models)
    - Occlusion sensitivity
    - SHAP values

    Attributes:
        heatmap: Heatmap normalisée [0, 1], shape (H, W)
        slide_dimensions: Dimensions originales slide (width, height)
        resolution_level: Niveau de résolution (0=max, 1=half, etc.)
        slide_id: Identifiant lame
        method: Méthode génération ("gradcam", "attention", "occlusion", "shap")

    References:
        - Selvaraju et al. (2017): "Grad-CAM: Visual Explanations from Deep Networks"
        - Chattopadhay et al. (2018): "Grad-CAM++: Generalized Gradient-Based Explanations"
        - Lundberg & Lee (2017): "A Unified Approach to Interpreting Model Predictions" (SHAP)

    Examples:
        >>> result = HeatmapResult(
        ...     heatmap=np.random.rand(1000, 1000),
        ...     slide_dimensions=(20000, 20000),
        ...     resolution_level=2,
        ...     slide_id="slide_abc123",
        ...     method="gradcam"
        ... )
    """

    heatmap: np.ndarray  # Shape: (H, W), values [0, 1]
    slide_dimensions: Tuple[int, int]  # (width, height)
    resolution_level: int
    slide_id: str = ""
    method: str = "gradcam"
    target_class: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validation."""
        if self.heatmap.ndim != 2:
            raise ValueError(f"Heatmap must be 2D (H, W), got shape {self.heatmap.shape}")

        if not (self.heatmap.min() >= 0.0 and self.heatmap.max() <= 1.0):
            raise ValueError("Heatmap values must be normalized [0, 1]")

    def to_rgb(self, colormap: str = "jet") -> np.ndarray:
        """
        Convert heatmap to RGB image with colormap.

        Args:
            colormap: Matplotlib colormap name ("jet", "hot", "viridis", etc.)

        Returns:
            RGB image (H, W, 3) with values [0, 255]
        """
        import matplotlib.pyplot as plt

        cmap = plt.get_cmap(colormap)
        rgb = cmap(self.heatmap)[:, :, :3]  # Drop alpha channel
        rgb = (rgb * 255).astype(np.uint8)
        return rgb


# ============================================================================
# ML PROVIDER PROTOCOL
# ============================================================================


class MLProvider(Protocol):
    """
    Interface pour providers ML.

    Design pattern: Strategy Pattern
    - Permet de swapper l'implémentation ML sans changer l'API
    - Facilite tests (mocks) et extensibilité

    Implementations:
    - SlideflowProvider: Slideflow framework
    - TorchVisionProvider: PyTorch models
    - HuggingFaceProvider: Transformers models
    - MockProvider: Pour tests et développement

    References:
        - Gang of Four: Strategy Pattern
        - Martin Fowler: Dependency Injection
        - PEP 544: Protocol (Structural Subtyping)

    Examples:
        >>> provider: MLProvider = SlideflowProvider()
        >>> provider.load_model("models:/gleason_grading/production", {...})
        >>> result = provider.predict("path/to/slide.mrxs")
        >>> print(f"Prediction: {result.prediction_class} ({result.confidence:.2%})")
    """

    def load_model(self, model_path: str, model_config: Dict) -> None:
        """
        Charge un modèle ML depuis artefact.

        Args:
            model_path: Chemin vers modèle
                - Local: "models/gleason_v2.pt"
                - MLflow: "models:/gleason_grading/production"
                - Hugging Face: "hf://facebook/dino-vitb16"
                - S3: "s3://bucket/models/model.pt"

            model_config: Configuration
                {
                    "model_id": "gleason_grading_v2",
                    "device": "cuda",  # ou "cpu", "auto"
                    "batch_size": 32,
                    "tile_size": 224,
                    "num_classes": 3,
                    "classes": ["gleason_3", "gleason_4", "gleason_5"]
                }

        Raises:
            FileNotFoundError: Si modèle introuvable
            ValueError: Si configuration invalide
            MLProviderError: Si chargement échoue

        Examples:
            >>> provider.load_model(
            ...     "models:/gleason_grading/production",
            ...     {"device": "cuda", "batch_size": 32}
            ... )
        """
        ...

    def predict(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Prédiction sur slide complète ou région.

        Process:
        1. Load slide (avec OpenSlide)
        2. Tiling en patches (tile_size défini dans config)
        3. Inference sur chaque patch
        4. Aggregation (vote, moyenne, attention)
        5. Uncertainty quantification (Monte Carlo Dropout optionnel)

        Args:
            slide_path: Chemin vers lame histologique
            region: Région optionnelle (x, y, width, height) en pixels niveau 0

        Returns:
            PredictionResult avec classe, confiance, incertitude

        Raises:
            FileNotFoundError: Si slide introuvable
            MLProviderError: Si inference échoue

        Examples:
            >>> # Prédiction slide complète
            >>> result = provider.predict("path/to/slide.mrxs")

            >>> # Prédiction sur région
            >>> result = provider.predict(
            ...     "path/to/slide.mrxs",
            ...     region=(1000, 1000, 2000, 2000)
            ... )
            >>> print(f"Class: {result.prediction_class}, Confidence: {result.confidence:.2%}")
        """
        ...

    def extract_features(
        self, slide_path: str, tile_size: int = 224, overlap: int = 0
    ) -> FeatureExtractionResult:
        """
        Extraction de features (embeddings) pour Multiple Instance Learning.

        Process:
        1. Tiling slide en patches (tile_size × tile_size)
        2. Forward pass à travers backbone (sans classification head)
        3. Extraction features dernière couche (avant softmax)
        4. Retour embeddings + coordonnées

        Use cases:
        - MIL training (CLAM, DSMIL)
        - Active learning (uncertainty sampling)
        - Similarity search (nearest neighbors)
        - Dataset clustering (UMAP, t-SNE)

        Args:
            slide_path: Chemin vers lame
            tile_size: Taille patches (px), default 224
            overlap: Chevauchement patches (px), default 0

        Returns:
            FeatureExtractionResult avec embeddings (N, D) et coordonnées

        Raises:
            FileNotFoundError: Si slide introuvable
            MLProviderError: Si extraction échoue

        References:
            - Ilse et al. (2018): "Attention-based Deep MIL"
            - Lu et al. (2021): "Data-efficient Computational Pathology"

        Examples:
            >>> result = provider.extract_features(
            ...     "path/to/slide.mrxs",
            ...     tile_size=224,
            ...     overlap=0
            ... )
            >>> print(f"Extracted {result.num_patches} patches, {result.embedding_dim}-dim")
            >>> # Use embeddings for MIL training
            >>> attention_mil_model.train(result.embeddings, labels)
        """
        ...

    def generate_heatmap(
        self, slide_path: str, prediction_class: str, resolution_level: int = 2
    ) -> HeatmapResult:
        """
        Génère heatmap d'explainability (Grad-CAM, attention, etc.).

        Visualise les régions qui ont influencé la prédiction.

        Methods supportées:
        - Grad-CAM: Gradient-weighted Class Activation Mapping
        - Grad-CAM++: Improved Grad-CAM
        - Attention: Attention weights (si modèle MIL)
        - Occlusion: Sensitivity à l'occlusion
        - SHAP: SHapley Additive exPlanations

        Args:
            slide_path: Chemin vers lame
            prediction_class: Classe pour laquelle générer heatmap
            resolution_level: Niveau résolution (0=max, 1=demi, 2=quart, etc.)

        Returns:
            HeatmapResult avec heatmap normalisée [0, 1]

        Raises:
            FileNotFoundError: Si slide introuvable
            ValueError: Si classe invalide
            MLProviderError: Si génération échoue

        References:
            - Selvaraju et al. (2017): "Grad-CAM"
            - Chattopadhay et al. (2018): "Grad-CAM++"
            - Lundberg & Lee (2017): "SHAP"

        Examples:
            >>> result = provider.generate_heatmap(
            ...     "path/to/slide.mrxs",
            ...     prediction_class="gleason_4",
            ...     resolution_level=2
            ... )
            >>> # Save as RGB image
            >>> rgb = result.to_rgb(colormap="jet")
            >>> cv2.imwrite("heatmap.png", rgb)
        """
        ...

    def get_model_info(self) -> Dict:
        """
        Retourne metadata du modèle chargé.

        Returns:
            {
                "model_id": str,
                "model_name": str,
                "version": str,
                "task_type": str,  # "classification", "segmentation", "detection"
                "classes": List[str],
                "input_size": Tuple[int, int],
                "device": str,  # "cuda", "cpu"
                "reference_metrics": {
                    "accuracy": float,
                    "auc_roc": float,
                    "inference_time_ms": float
                }
            }

        Raises:
            MLProviderError: Si aucun modèle chargé

        Examples:
            >>> info = provider.get_model_info()
            >>> print(f"Model: {info['model_name']} v{info['version']}")
            >>> print(f"Classes: {info['classes']}")
            >>> print(f"Device: {info['device']}")
        """
        ...

    def unload_model(self) -> None:
        """
        Décharge le modèle de la mémoire.

        Libère ressources GPU/CPU. Utile si gestion dynamique de modèles multiples.

        Examples:
            >>> provider.load_model("models:/gleason_grading/v1", {...})
            >>> # ... inference ...
            >>> provider.unload_model()  # Free GPU memory
            >>> provider.load_model("models:/tumor_detection/v2", {...})
        """
        ...


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_provider(provider_name: str) -> MLProvider:
    """
    Factory pour instancier provider ML.

    Args:
        provider_name: "slideflow", "torchvision", "huggingface", "mock"

    Returns:
        Instance de MLProvider

    Raises:
        ValueError: Si provider inconnu

    Examples:
        >>> provider = get_provider("slideflow")
        >>> provider.load_model(...)
    """
    providers = {
        "slideflow": "services.ml.providers.slideflow_provider.SlideflowProvider",
        "mock": "services.ml.providers.mock_provider.MockProvider",
    }

    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")

    # Dynamic import
    module_path, class_name = providers[provider_name].rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])
    provider_class = getattr(module, class_name)

    return provider_class()
