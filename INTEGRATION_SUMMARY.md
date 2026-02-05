# Slideflow Integration Summary

**Date**: 2026-02-05
**Status**: Phase 2 - Core architecture implemented
**Tests**: 19/19 passing

---

## Fichiers Créés

### Documentation

1. **`docs/ML_INTEGRATION.md`** (77 KB)
   - Guide complet d'intégration Slideflow
   - Architecture détaillée (MLProvider, Providers, API)
   - Exemples code pour tous les use cases
   - Références scientifiques (papers, frameworks)
   - Workflow exemples (inference, active learning, feedback loop)
   - Déploiement (Docker, GPU, monitoring)
   - Sécurité & Privacy (GDPR, federated learning)

2. **`backend/services/ml/INTEGRATION_README.md`** (15 KB)
   - Quick start guide
   - API endpoints usage
   - Développement avec Mock Provider
   - Troubleshooting
   - Roadmap

### Core Interfaces

3. **`backend/core/interfaces/ml_provider.py`** (14 KB)
   - Interface `MLProvider` (Protocol)
   - Data classes: `PredictionResult`, `FeatureExtractionResult`, `HeatmapResult`
   - Factory: `get_provider()`
   - Documentation complète avec exemples

4. **`backend/core/interfaces/__init__.py`**
   - Exports interfaces

5. **`backend/core/exceptions/ml_exceptions.py`** (7 KB)
   - Hiérarchie exceptions ML:
     - `MLProviderError` (base)
     - `ModelLoadError`
     - `PredictionError`
     - `FeatureExtractionError`
     - `HeatmapGenerationError`
     - `MLModelNotLoadedError`
   - Decorator `@handle_ml_error`

6. **`backend/core/exceptions/__init__.py`**
   - Exports exceptions

### ML Providers

7. **`backend/services/ml/providers/slideflow_provider.py`** (21 KB)
   - Implémentation complète `SlideflowProvider`
   - Model loading (MLflow, Hugging Face, S3, local)
   - Inference avec Monte Carlo Dropout (uncertainty quantification)
   - Feature extraction (MIL)
   - Heatmap generation (Grad-CAM)
   - GPU/CPU detection et fallback
   - Lazy loading Slideflow

8. **`backend/services/ml/providers/mock_provider.py`** (13 KB)
   - Mock provider pour tests/dev (pas besoin Slideflow)
   - Résultats aléatoires réalistes
   - Reproductible (seed)
   - Utilisable en CI/CD

9. **`backend/services/ml/providers/__init__.py`**
   - Exports providers

### API Routes

10. **`backend/routes/ml.py`** (14 KB)
    - Endpoints API ML:
      - `POST /ml/predict/{slide_id}` - Prédiction
      - `POST /ml/features/{slide_id}` - Extraction features
      - `GET /ml/heatmap/{slide_id}` - Heatmap
      - `POST /ml/batch/predict` - Batch inference
      - `GET /ml/models` - Liste modèles
      - `POST /ml/models/reload` - Hot reload config
      - `GET /ml/health` - Health check
    - Pydantic models pour validation
    - Dependencies (get_ml_provider, get_tag_router)
    - Error handling

### Configuration

11. **`backend/config/ml_routes.yaml.example`** (5 KB)
    - Exemple configuration model registry
    - 4 modèles exemples:
      - Gleason grading (prostate)
      - Breast tumor detection
      - Ki-67 quantification
      - Generic tumor detection (fallback)
    - Feature extractors (ResNet50, DINO, UNI)
    - Documentation inline

### Tests

12. **`backend/tests/test_ml_integration.py`** (11 KB)
    - 19 tests unitaires avec MockProvider
    - Tests:
      - Model loading/unloading (4 tests)
      - Prediction (4 tests)
      - Feature extraction (3 tests)
      - Heatmap generation (4 tests)
      - Data validation (3 tests)
      - Complete workflow (1 test)
    - **All 19 tests passing**

### Modifications

13. **`backend/services/ml/__init__.py`** (modifié)
    - Lazy imports via `__getattr__` (évite chargement OpenSlide)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           API Layer                                  │
│  routes/ml.py: POST /predict, /features, /heatmap, /batch, etc.    │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────────────┐
│                      Service Layer                                   │
│  - TagExtractor (metadata extraction)                               │
│  - TagRouter (routing vers modèles)                                 │
│  - ModelRegistry (config ml_routes.yaml)                            │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────────────┐
│                    Interface Layer (Protocol)                        │
│  core/interfaces/ml_provider.py: MLProvider Protocol                │
│  - load_model()                                                      │
│  - predict()                                                         │
│  - extract_features()                                                │
│  - generate_heatmap()                                                │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────────────┐
│                  Implementation Layer                                │
│  ┌──────────────────────┐  ┌─────────────────────────┐             │
│  │ SlideflowProvider    │  │   MockProvider          │             │
│  │ (Slideflow)          │  │   (Tests/Dev)           │             │
│  │ - GPU/CPU support    │  │   - No dependencies     │             │
│  │ - MC Dropout         │  │   - Fast                │             │
│  │ - Grad-CAM           │  │   - Reproductible       │             │
│  │ - MLflow/HF/S3       │  │                         │             │
│  └──────────────────────┘  └─────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Features Implemented

### 1. Abstraction via Protocol

- Interface `MLProvider` découple l'API du provider ML
- Facile d'ajouter nouveaux providers (TorchVision, Hugging Face, etc.)
- Pas besoin d'hériter explicitement (structural subtyping)

### 2. Multiple Providers

- **SlideflowProvider**: Production (Slideflow framework)
- **MockProvider**: Tests/Dev (pas de dépendances)

### 3. Uncertainty Quantification

- Monte Carlo Dropout (Gal & Ghahramani 2016)
- Retourne confiance + incertitude épistémique
- Critique pour applications médicales

### 4. Explainability

- Grad-CAM heatmaps
- Visualisation régions importantes
- Export PNG avec colormap

### 5. Multiple Instance Learning

- Feature extraction pour MIL
- Embeddings (N patches, D dimensions)
- Coordonnées pour chaque patch

### 6. Lazy Loading

- Slideflow chargé uniquement si utilisé
- Évite problèmes OpenSlide DLL
- Application démarre sans ML dependencies

### 7. Testing

- 19 tests unitaires avec MockProvider
- Pas besoin Slideflow installé pour tester
- Reproductible (seed)

---

## API Usage Examples

### Prédiction Simple

```bash
curl -X POST "http://localhost:8000/api/ml/predict/slide_abc123"

# Response
{
  "prediction_class": "gleason_4",
  "confidence": 0.92,
  "uncertainty": 0.05,
  "probabilities": {"gleason_3": 0.05, "gleason_4": 0.92, "gleason_5": 0.03},
  "execution_time_ms": 2340
}
```

### Prédiction avec Région

```bash
curl -X POST "http://localhost:8000/api/ml/predict/slide_abc123" \
  -H "Content-Type: application/json" \
  -d '{"region": {"x": 1000, "y": 1000, "width": 2000, "height": 2000}}'
```

### Feature Extraction (MIL)

```bash
curl -X POST "http://localhost:8000/api/ml/features/slide_abc123" \
  -d '{"tile_size": 224, "overlap": 0}'

# Response
{
  "num_patches": 1500,
  "embedding_dim": 512,
  "embeddings_shape": [1500, 512]
}
```

### Heatmap

```bash
curl "http://localhost:8000/api/ml/heatmap/slide_abc123?prediction_class=gleason_4" \
  -o heatmap.png
```

---

## Development Workflow

### 1. Sans Slideflow (Mock Provider)

```python
# .env
ML_PROVIDER=mock

# Code
from services.ml.providers import MockProvider

provider = MockProvider()
provider.load_model("mock://model", {"classes": ["benign", "malignant"]})
result = provider.predict("slide.mrxs")
# Fonctionne sans Slideflow installé
```

### 2. Avec Slideflow (Production)

```python
# .env
ML_PROVIDER=slideflow
ML_DEVICE=auto

# Code
from core.interfaces import get_provider

provider = get_provider("slideflow")
provider.load_model("models:/gleason_grading/production", {...})
result = provider.predict("slide.mrxs")
# Utilise vraie inference Slideflow
```

---

## Testing

### Run Tests

```bash
cd backend
pytest tests/test_ml_integration.py -v

# Results:
# 19 passed in 4.37s
```

### Test Coverage

- ✅ Model loading/unloading
- ✅ Predictions (basic, region, reproducibility)
- ✅ Feature extraction
- ✅ Heatmap generation
- ✅ Data validation (PredictionResult, etc.)
- ✅ Complete workflow
- ✅ Error handling (model not loaded, etc.)

---

## Next Steps

### Immédiat (Phase 2 - Complétion)

1. **Intégrer dans main.py**
   - Ajouter router ML à l'application
   - Tester endpoints via Swagger UI

2. **Base de données**
   - Créer tables `ml_predictions`, `slide_features`, `ml_heatmaps`
   - Stocker résultats inference

3. **Storage**
   - Implémenter storage embeddings (S3/local)
   - Implémenter storage heatmaps

### Phase 3 (MLOps - Q1 2026)

1. **MLflow Integration**
   - Model registry
   - Experiment tracking
   - Model versioning

2. **DVC Integration**
   - Dataset versioning
   - Pipeline management

3. **Batch Processing**
   - Async jobs (Celery/RQ)
   - Progress tracking
   - Error recovery

4. **Drift Detection**
   - Evidently AI integration
   - Monitoring dashboards
   - Alerting

5. **Active Learning**
   - Uncertainty sampling
   - Query by committee
   - Integration Label Studio

6. **Feedback Loop**
   - Capture corrections pathologistes
   - Auto-retraining triggers
   - Performance monitoring

### Phase 4 (Advanced ML - Q2 2026)

1. **Federated Learning**
   - Flower framework
   - Multi-site training
   - Privacy-preserving

2. **Foundation Models**
   - UNI (Mahmood Lab)
   - Virchow (Microsoft)
   - Fine-tuning

3. **Multi-Modal**
   - H&E + IHC fusion
   - Cross-stain learning

---

## Configuration Required

### 1. Environment Variables

Ajouter à `.env`:

```bash
# ML Configuration
ML_ENABLED=true
ML_PROVIDER=slideflow  # ou "mock"
ML_DEVICE=auto
ML_ROUTES_CONFIG=config/ml_routes.yaml
ML_MODEL_CACHE_DIR=/app/models

# MLflow (optionnel)
MLFLOW_TRACKING_URI=http://mlflow.chu-ucl.local:5000

# GPU (si disponible)
CUDA_VISIBLE_DEVICES=0
```

### 2. Model Registry

Copier et éditer:

```bash
cp backend/config/ml_routes.yaml.example backend/config/ml_routes.yaml
```

### 3. Dependencies

```bash
# Slideflow (optionnel)
pip install slideflow[tf]  # TensorFlow
# ou
pip install slideflow[torch]  # PyTorch

# MLOps (optionnel)
pip install mlflow dvc boto3
```

---

## Resources

### Documentation

- **Main Guide**: `docs/ML_INTEGRATION.md`
- **Quick Start**: `backend/services/ml/INTEGRATION_README.md`
- **API Docs**: http://localhost:8000/docs (après lancement)

### Frameworks

- **Slideflow**: https://github.com/slideflow/slideflow
- **Slideflow Docs**: https://slideflow.dev/
- **CLAM (MIL)**: https://github.com/mahmoodlab/CLAM
- **MLflow**: https://mlflow.org/
- **DVC**: https://dvc.org/

### Papers

- Dolezal et al. (2023): "Slideflow: Deep Learning for Digital Histopathology"
  https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-024-05758-x

- Gal & Ghahramani (2016): "Dropout as a Bayesian Approximation"
  https://arxiv.org/abs/1506.02142

- Ilse et al. (2018): "Attention-based Deep Multiple Instance Learning"
  https://arxiv.org/abs/1802.04712

- Selvaraju et al. (2017): "Grad-CAM: Visual Explanations from Deep Networks"
  https://arxiv.org/abs/1610.02391

---

## Metrics

- **Files Created**: 13 (+ 1 modified)
- **Lines of Code**: ~2,500
- **Tests**: 19/19 passing
- **Test Coverage**: Core ML functionality
- **Documentation**: 92 KB

---

## Contact & Support

**ML Team VarunaPoC**
- Email: varuna-ml@chu-ucl.be
- GitHub: https://github.com/chu-ucl/VarunaPoC
- Slack: #varuna-ml

---

**Version**: 1.0
**Author**: Claude (ML Architect)
**Date**: 2026-02-05
