# providers

## But
Implementations concretes de l'interface MLProvider pour differents frameworks d'inference.

## Pourquoi
Le pattern Strategy permet de basculer entre providers (Slideflow production, mock tests, OpenSlide integration) sans modifier le code appelant.

## Structure
- `__init__.py` -- Re-exporte SlideflowProvider, MockProvider, OpenSlideTestProvider.
- `slideflow_provider.py` -- Provider Slideflow : extraction de features (CTransPath, RetCCL, etc.), prediction, heatmap Grad-CAM.
- `mock_provider.py` -- Provider mock pour tests unitaires et developpement frontend sans dependances ML.
- `openslide_provider.py` -- Provider OpenSlide pour tests d'integration avec de vraies lames, sans modele ML entraine.
