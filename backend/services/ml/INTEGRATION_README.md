# ML Integration - Slideflow

**Status:** Phase 2 - Core architecture implemented

---

## Structure

```
backend/
├── core/
│   ├── interfaces/
│   │   ├── ml_provider.py          # MLProvider Protocol (interface abstraite)
│   │   └── __init__.py
│   └── exceptions/
│       ├── ml_exceptions.py        # Exceptions ML custom
│       └── __init__.py
├── services/
│   └── ml/
│       ├── providers/
│       │   ├── slideflow_provider.py   # Implémentation Slideflow
│       │   ├── mock_provider.py        # Mock pour tests/dev
│       │   └── __init__.py
│       ├── tag_extractor.py        # Existant (Phase 3.1)
│       ├── tag_router.py           # Existant (Phase 3.2)
│       └── __init__.py
├── routes/
│   └── ml.py                       # API endpoints ML
├── config/
│   └── ml_routes.yaml.example      # Configuration model registry
└── tests/
    └── test_ml_integration.py      # Tests unitaires (19 tests)
```

---

## Quick Start

### 1. Installation

```bash
# Core dependencies (déjà installées)
pip install fastapi uvicorn pydantic numpy

# ML dependencies (optionnel - Slideflow)
pip install slideflow[tf]  # TensorFlow backend
# ou
pip install slideflow[torch]  # PyTorch backend

# MLOps tools (optionnel)
pip install mlflow dvc boto3
```

### 2. Configuration

Copier exemple configuration:

```bash
cp backend/config/ml_routes.yaml.example backend/config/ml_routes.yaml
```

Editer `.env`:

```bash
# ML Configuration
ML_ENABLED=true
ML_PROVIDER=slideflow  # ou "mock" pour dev sans Slideflow
ML_DEVICE=auto  # cuda, cpu, auto
ML_ROUTES_CONFIG=config/ml_routes.yaml
```

### 3. Tests

```bash
# Tests unitaires (MockProvider - pas besoin de Slideflow)
pytest backend/tests/test_ml_integration.py -v

# Tous 19 tests devraient passer
```

### 4. Lancer API

```bash
cd backend
uvicorn main:app --reload

# API docs: http://localhost:8000/docs
# ML endpoints: http://localhost:8000/api/ml/...
```

---

## API Endpoints

### Prediction

```bash
# Prédiction slide complète
curl -X POST "http://localhost:8000/api/ml/predict/slide_abc123"

# Prédiction sur région
curl -X POST "http://localhost:8000/api/ml/predict/slide_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "region": {"x": 1000, "y": 1000, "width": 2000, "height": 2000}
  }'

# Response
{
  "slide_id": "slide_abc123",
  "prediction_class": "gleason_4",
  "confidence": 0.92,
  "uncertainty": 0.05,
  "probabilities": {"gleason_3": 0.05, "gleason_4": 0.92, "gleason_5": 0.03},
  "execution_time_ms": 2340,
  "model_id": "gleason_grading_v2"
}
```

### Feature Extraction

```bash
curl -X POST "http://localhost:8000/api/ml/features/slide_abc123" \
  -H "Content-Type: application/json" \
  -d '{"tile_size": 224, "overlap": 0}'

# Response
{
  "slide_id": "slide_abc123",
  "num_patches": 1500,
  "embedding_dim": 512,
  "embeddings_shape": [1500, 512],
  "model_id": "resnet50_imagenet"
}
```

### Heatmap

```bash
# Télécharger heatmap PNG
curl "http://localhost:8000/api/ml/heatmap/slide_abc123?prediction_class=gleason_4" \
  -o heatmap.png
```

### Liste Modèles

```bash
curl "http://localhost:8000/api/ml/models"

# Response
[
  {
    "model_id": "gleason_grading_v2",
    "model_name": "Gleason Grading Model",
    "version": "2.1.0",
    "task_type": "classification",
    "classes": ["gleason_3", "gleason_4", "gleason_5"],
    "device": "cuda",
    "reference_metrics": {"accuracy": 0.94, "auc_roc": 0.97}
  }
]
```

---

## Développement

### Utiliser Mock Provider

En développement, utiliser le Mock Provider (pas besoin de Slideflow installé):

```python
# .env
ML_PROVIDER=mock

# Code
from services.ml.providers import MockProvider

provider = MockProvider()
provider.load_model("mock://test_model", {
    "model_id": "test",
    "classes": ["benign", "malignant"]
})

result = provider.predict("slide.mrxs")
print(result.prediction_class)  # "malignant" (mock)
```

### Ajouter nouveau provider

Créer un fichier `backend/services/ml/providers/my_provider.py`:

```python
from core.interfaces import MLProvider, PredictionResult, ...

class MyProvider:
    """Mon provider custom."""

    def load_model(self, model_path: str, model_config: Dict) -> None:
        # Implémentation
        pass

    def predict(self, slide_path: str, region=None) -> PredictionResult:
        # Implémentation
        pass

    # ... autres méthodes
```

Puis l'enregistrer dans `core/interfaces/ml_provider.py`:

```python
def get_provider(provider_name: str) -> MLProvider:
    providers = {
        "slideflow": "...",
        "my_provider": "services.ml.providers.my_provider.MyProvider"
    }
    # ...
```

---

## Tests

### Tests unitaires (19 tests)

```bash
pytest backend/tests/test_ml_integration.py -v

# Tests:
# - Model loading/unloading
# - Predictions (basic, region, reproducibility)
# - Feature extraction (MIL)
# - Heatmap generation (Grad-CAM)
# - Data validation (PredictionResult, etc.)
# - Complete workflow
```

### Tests d'intégration (à implémenter)

```bash
# Avec Slideflow installé
pytest backend/tests/integration/test_slideflow_integration.py

# Tests:
# - Chargement modèle réel
# - Inference sur vraie lame
# - Performance benchmarks
```

---

## Architecture Decisions

### Pourquoi Protocol au lieu d'ABC?

**Protocol (PEP 544)** permet structural subtyping (duck typing):

```python
# Pas besoin d'hériter explicitement
class MyProvider:
    def predict(...): ...  # OK, match Protocol

# vs ABC (nominal subtyping)
class MyProvider(ABC):  # Doit hériter
    pass
```

### Pourquoi Mock Provider?

- **Tests rapides**: Pas besoin d'installer Slideflow (dépendances lourdes)
- **Développement frontend**: API fonctionne sans ML backend
- **CI/CD**: Tests sans GPU

### Pourquoi lazy imports?

Éviter de charger OpenSlide au démarrage (problème DLL sur Windows):

```python
# Bad (charge OpenSlide immédiatement)
from services.ml import TagExtractor

# Good (lazy loading via __getattr__)
def __getattr__(name):
    if name == "TagExtractor":
        from .tag_extractor import TagExtractor
        return TagExtractor
```

---

## Roadmap

### Phase 2 (Actuel): Core Architecture ✅

- [x] MLProvider interface
- [x] SlideflowProvider implementation
- [x] MockProvider pour tests
- [x] API endpoints (predict, features, heatmap)
- [x] Tests unitaires (19 tests)
- [x] Documentation

### Phase 3: Production Features (Q1 2026)

- [ ] MLflow integration (model registry)
- [ ] DVC integration (dataset versioning)
- [ ] Batch processing (async jobs)
- [ ] Drift detection (Evidently AI)
- [ ] Active learning (uncertainty sampling)
- [ ] Feedback loop (corrections → retraining)

### Phase 4: Advanced ML (Q2 2026)

- [ ] Federated learning (Flower)
- [ ] Foundation models (UNI, Virchow)
- [ ] Multi-modal fusion (H&E + IHC)
- [ ] Real-time inference optimization
- [ ] Model monitoring dashboards

---

## Troubleshooting

### Slideflow not installed

**Symptôme:** `ImportError: No module named 'slideflow'`

**Solution:**

```bash
pip install slideflow[tf]  # TensorFlow
# ou
pip install slideflow[torch]  # PyTorch
```

Ou utiliser Mock Provider:

```bash
# .env
ML_PROVIDER=mock
```

### GPU not detected

**Symptôme:** `device: cpu` au lieu de `cuda`

**Solution:**

```bash
# Vérifier CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Vérifier TensorFlow
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

# Forcer GPU
# .env
ML_DEVICE=cuda
```

### Model loading fails

**Symptôme:** `ModelLoadError: Model file not found`

**Solution:**

Vérifier `ml_routes.yaml`:

```yaml
routes:
  - model_id: "my_model"
    model_path: "models:/my_model/production"  # MLflow
    # ou
    model_path: "/absolute/path/to/model.pt"   # Local
```

---

## Références

### Documentation

- **ML Integration Guide**: `docs/ML_INTEGRATION.md`
- **API Docs**: http://localhost:8000/docs
- **Slideflow Docs**: https://slideflow.dev/

### Papers

- Dolezal et al. (2023): "Slideflow: Deep Learning for Digital Histopathology"
- Gal & Ghahramani (2016): "Dropout as a Bayesian Approximation"
- Ilse et al. (2018): "Attention-based Deep MIL"

### Frameworks

- **Slideflow**: https://github.com/slideflow/slideflow
- **MLflow**: https://mlflow.org/
- **DVC**: https://dvc.org/

---

**Version**: 2.0
**Date**: 2026-02-05
**Contact**: ML Team VarunaPoC
