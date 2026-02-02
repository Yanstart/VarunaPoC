"""
ML Services Package
Services pour MLOps et apprentissage continu.

Modules:
- tag_extractor: Extraction automatique tags (organ, stain, marker)
- tag_router: Routage intelligent vers modèles spécialisés
- model_inference: Inférence ML avec uncertainty quantification
- feedback_service: Capture feedback pathologistes
- dataset_builder: Construction datasets enrichis avec feedback
- retraining_monitor: Monitoring et déclenchement re-entraînement
- drift_detector: Détection drift données/prédictions

Référence: docs/MLOPS_ARCHITECTURE.md
"""

from .tag_extractor import TagExtractor
from .tag_router import TagRouter, ModelRoute

__all__ = [
    'TagExtractor',
    'TagRouter',
    'ModelRoute'
]
