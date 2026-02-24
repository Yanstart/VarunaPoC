# exceptions

## But
Exceptions metier hierarchisees pour les operations ML et le traitement d'erreurs du backend.

## Pourquoi
Une hierarchie d'exceptions claire (MLProviderError -> sous-types) permet un traitement d'erreurs precis et des messages informatifs pour le debogage.

## Structure
- `__init__.py` -- Re-exporte toutes les exceptions ML pour un import simplifie.
- `ml_exceptions.py` -- Hierarchie d'exceptions ML : MLProviderError, ModelLoadError, PredictionError, FeatureExtractionError, HeatmapGenerationError, MLModelNotLoadedError.
