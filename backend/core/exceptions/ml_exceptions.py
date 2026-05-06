"""
ML-specific Exceptions

Custom exceptions pour machine learning operations.

Design:
- Hiérarchie claire (MLProviderError → sous-exceptions spécifiques)
- Inherits from VarunaError so a single `except VarunaError` catches them
- Messages informatifs (pas juste "error")
- Attributs contextuels (model_id, slide_id, etc.)

References:
- PEP 8: Exception Naming Conventions
- Effective Python Item 87: Define exceptions hierarchically
"""

from .base import VarunaError


class MLProviderError(VarunaError):
    """
    Base exception pour ML provider errors.

    Tous les autres ML exceptions héritent de celle-ci.
    Inherits from VarunaError so generic `except VarunaError` handlers
    capture ML errors as well.

    Attributes:
        message: Message d'erreur (inherited from VarunaError)
        provider: Nom du provider ("slideflow", "torchvision", etc.)
        details: Détails additionnels (dict, inherited; includes provider key)

    Examples:
        >>> try:
        ...     provider.predict(...)
        ... except MLProviderError as e:
        ...     logger.error(f"ML error: {e.message}")
        ...     logger.debug(f"Provider: {e.provider}, Details: {e.details}")
    """

    def __init__(self, message: str, provider: str = "", details: dict = None):
        self.provider = provider
        # Provider also flows into details so generic VarunaError handlers
        # have full context. __str__ filters it out below to avoid display
        # duplication with the explicit "(provider: ...)" segment.
        merged_details = {"provider": provider} if provider else {}
        if details:
            merged_details.update(details)
        super().__init__(message, details=merged_details)

    def __str__(self):
        base = f"[ML Provider Error] {self.message}"
        if self.provider:
            base += f" (provider: {self.provider})"
        # Filter provider to avoid duplication: it is already shown above.
        extra = {k: v for k, v in self.details.items() if k != "provider"}
        if extra:
            base += f" - Details: {extra}"
        return base


class ModelLoadError(MLProviderError):
    """
    Erreur lors du chargement d'un modèle.

    Causes communes:
    - Fichier modèle introuvable
    - Format modèle incompatible
    - Mémoire insuffisante (GPU/CPU)
    - Version framework incompatible

    Attributes:
        model_path: Chemin vers modèle
        model_id: ID modèle (optionnel)

    Examples:
        >>> raise ModelLoadError(
        ...     "Model file not found",
        ...     model_path="models:/gleason_v2/production",
        ...     model_id="gleason_grading_v2",
        ...     provider="slideflow"
        ... )
    """

    def __init__(
        self,
        message: str,
        model_path: str = "",
        model_id: str = "",
        provider: str = "",
        details: dict = None,
    ):
        self.model_path = model_path
        self.model_id = model_id
        details = details or {}
        details.update({"model_path": model_path, "model_id": model_id})
        super().__init__(message, provider, details)

    def __str__(self):
        base = f"[Model Load Error] {self.message}"
        if self.model_path:
            base += f" (path: {self.model_path})"
        if self.model_id:
            base += f" (model_id: {self.model_id})"
        return base


class MLModelNotLoadedError(MLProviderError):
    """
    Erreur si tentative d'utiliser modèle non chargé.

    Raised quand predict() ou extract_features() appelé avant load_model().

    Examples:
        >>> provider = SlideflowProvider()
        >>> # Oubli de load_model()
        >>> provider.predict("slide.mrxs")  # Raises MLModelNotLoadedError
    """

    def __init__(
        self, message: str = "No model loaded. Call load_model() first.", provider: str = ""
    ):
        super().__init__(message, provider)


class PredictionError(MLProviderError):
    """
    Erreur lors de l'inférence ML.

    Causes communes:
    - Slide format non supporté
    - Tile extraction échoue
    - OOM (Out of Memory) GPU/CPU
    - Preprocessing échoue

    Attributes:
        slide_path: Chemin vers lame
        slide_id: ID lame (optionnel)
        model_id: ID modèle
        region: Région si prédiction régionale

    Examples:
        >>> raise PredictionError(
        ...     "Out of memory during inference",
        ...     slide_path="large_slide.svs",
        ...     model_id="gleason_v2",
        ...     provider="slideflow",
        ...     details={"gpu_memory_available": "512MB"}
        ... )
    """

    def __init__(
        self,
        message: str,
        slide_path: str = "",
        slide_id: str = "",
        model_id: str = "",
        region: tuple = None,
        provider: str = "",
        details: dict = None,
    ):
        self.slide_path = slide_path
        self.slide_id = slide_id
        self.model_id = model_id
        self.region = region
        details = details or {}
        details.update(
            {
                "slide_path": slide_path,
                "slide_id": slide_id,
                "model_id": model_id,
                "region": region,
            }
        )
        super().__init__(message, provider, details)

    def __str__(self):
        base = f"[Prediction Error] {self.message}"
        if self.slide_path:
            base += f" (slide: {self.slide_path})"
        if self.model_id:
            base += f" (model: {self.model_id})"
        if self.region:
            base += f" (region: {self.region})"
        return base


class FeatureExtractionError(MLProviderError):
    """
    Erreur lors de l'extraction de features.

    Causes communes:
    - Tile size incompatible avec modèle
    - Mémoire insuffisante
    - Slide trop large

    Attributes:
        slide_path: Chemin vers lame
        tile_size: Taille tiles
        num_patches: Nombre patches (si calculé)

    Examples:
        >>> raise FeatureExtractionError(
        ...     "Tile size 512 not supported, model expects 224",
        ...     slide_path="slide.mrxs",
        ...     tile_size=512,
        ...     provider="slideflow"
        ... )
    """

    def __init__(
        self,
        message: str,
        slide_path: str = "",
        tile_size: int = 0,
        num_patches: int = 0,
        provider: str = "",
        details: dict = None,
    ):
        self.slide_path = slide_path
        self.tile_size = tile_size
        self.num_patches = num_patches
        details = details or {}
        details.update(
            {"slide_path": slide_path, "tile_size": tile_size, "num_patches": num_patches}
        )
        super().__init__(message, provider, details)


class HeatmapGenerationError(MLProviderError):
    """
    Erreur lors de la génération de heatmap.

    Causes communes:
    - Classe invalide (pas dans classes modèle)
    - Méthode non supportée (e.g., Grad-CAM sur modèle sans Conv)
    - Résolution level invalide

    Attributes:
        slide_path: Chemin vers lame
        prediction_class: Classe pour heatmap
        method: Méthode génération ("gradcam", "attention", etc.)

    Examples:
        >>> raise HeatmapGenerationError(
        ...     "Class 'unknown_class' not in model classes",
        ...     slide_path="slide.mrxs",
        ...     prediction_class="unknown_class",
        ...     method="gradcam",
        ...     provider="slideflow"
        ... )
    """

    def __init__(
        self,
        message: str,
        slide_path: str = "",
        prediction_class: str = "",
        method: str = "",
        provider: str = "",
        details: dict = None,
    ):
        self.slide_path = slide_path
        self.prediction_class = prediction_class
        self.method = method
        details = details or {}
        details.update(
            {"slide_path": slide_path, "prediction_class": prediction_class, "method": method}
        )
        super().__init__(message, provider, details)


# ============================================================================
# UTILITIES
# ============================================================================


def handle_ml_error(func):
    """
    Decorator pour catch ML errors et logger proprement.

    Usage:
        @handle_ml_error
        def predict(self, slide_path: str):
            # ... code qui peut raise ML exceptions
    """
    import functools
    import logging

    logger = logging.getLogger(__name__)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MLProviderError as e:
            logger.error(f"ML Provider Error in {func.__name__}: {e}")
            logger.debug(f"Details: {e.details}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise MLProviderError(
                f"Unexpected error in {func.__name__}: {e!s}", details={"original_error": str(e)}
            )

    return wrapper
