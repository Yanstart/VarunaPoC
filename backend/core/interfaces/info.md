# interfaces

## But
Interfaces abstraites (Protocol PEP 544) definissant les contrats pour les providers ML.

## Pourquoi
L'inversion de dependances permet de changer de framework ML (Slideflow, TorchVision, mock) sans modifier le code appelant.

## Structure
- `__init__.py` -- Re-exporte MLProvider, PredictionResult, FeatureExtractionResult, HeatmapResult.
- `ml_provider.py` -- Interface Protocol MLProvider (predict, extract_features, generate_heatmap) et dataclasses de resultats.
