# ML Services

Services pour MLOps et apprentissage continu dans VarunaPoC.

**Référence principale:** `docs/MLOPS_ARCHITECTURE.md`

---

## Vue d'Ensemble

Ce package contient tous les services nécessaires pour:
- Extraction automatique de tags (organ, stain, marker)
- Routage intelligent vers modèles spécialisés
- Inférence ML avec uncertainty quantification
- Capture et gestion du feedback pathologistes
- Continuous learning (re-entraînement automatisé)
- Monitoring drift et performance

---

## Modules Disponibles

### ✅ Implémentés (Phase 3.1-3.2)

#### `tag_extractor.py`
Extraction automatique de tags depuis métadonnées slides.

```python
from services.ml import TagExtractor

extractor = TagExtractor()
tags = extractor.extract_tags("path/to/slide.mrxs", "MRXS")
# tags = {"organ": "prostate", "stain": "H&E", "confidence": 0.85, ...}
```

**Sources de tags (par priorité):**
1. DICOM metadata (confidence 0.95)
2. OpenSlide properties (confidence 0.85)
3. Filename parsing (confidence 0.70)
4. ML inference (confidence 0.75)

#### `tag_router.py`
Routage intelligent vers modèles spécialisés basé sur tags.

```python
from services.ml import TagRouter

router = TagRouter("config/ml_routes.yaml")
tags = {"organ": "prostate", "stain": "H&E", "task": "grading"}
route = router.route(tags)
# route.model_path = "models:/gleason_grading/production"
```

**Stratégies de matching:**
- Exact match (tous les tags)
- Partial match (organ + stain minimum)
- Fallback (modèle générique)

---

### 🚧 À Implémenter (Phase 3.3-3.5)

#### `model_inference.py`
Inférence ML avec uncertainty quantification.

**Features:**
- Monte Carlo Dropout pour uncertainty
- Grad-CAM pour explainability
- SHAP values (optionnel)
- Batch processing pour performance

**Usage prévu:**
```python
from services.ml import ModelInferenceService

inference = ModelInferenceService(router)
result = inference.predict(slide_id, tags)
# result = {
#     "prediction_class": "gleason_4",
#     "confidence": 0.92,
#     "uncertainty": 0.05,
#     "gradcam_url": "/api/ml/gradcam/abc123"
# }
```

#### `feedback_service.py`
Capture et gestion du feedback pathologistes.

**Features:**
- Stockage feedback en DB
- Validation feedback
- Incrémentation compteurs re-entraînement
- Export pour Label Studio

**Usage prévu:**
```python
from services.ml import FeedbackService

feedback_service = FeedbackService()
feedback_service.record_feedback({
    "slide_id": "abc123",
    "action": "correct",
    "original_prediction": "gleason_3",
    "corrected_prediction": "gleason_4"
})
```

#### `dataset_builder.py`
Construction datasets enrichis avec feedback.

**Features:**
- Merge feedback avec dataset existant
- Validation qualité données
- Versioning avec DVC
- Export formats (COCO, YOLO, etc.)

**Usage prévu:**
```python
from services.ml import DatasetBuilder

builder = DatasetBuilder(model_id="gleason_grading_v2")
dataset_path = builder.build_dataset_with_feedback()
# Versionne automatiquement avec DVC
```

#### `retraining_monitor.py`
Monitoring et déclenchement re-entraînement.

**Features:**
- Vérification seuils (feedback count, approval rate, time)
- Déclenchement pipeline Airflow
- Tracking retraining history

**Usage prévu:**
```python
from services.ml import RetrainingMonitor

monitor = RetrainingMonitor(model_id="gleason_grading_v2")
if monitor.should_trigger_retraining():
    monitor.trigger_retraining_pipeline()
```

#### `drift_detector.py`
Détection drift données/prédictions.

**Features:**
- Data drift (Kolmogorov-Smirnov, PSI)
- Prediction drift (distribution changes)
- Performance drift (metric degradation)
- Integration avec Evidently AI

**Usage prévu:**
```python
from services.ml import DriftDetector

detector = DriftDetector(model_id="gleason_grading_v2")
drift_report = detector.check_drift()
if drift_report["drift_detected"]:
    detector.send_alert()
```

---

## Configuration

### `config/ml_routes.yaml`
Configuration du routage par tags.

**Structure:**
```yaml
routes:
  - model_id: "gleason_grading_v2"
    model_name: "Gleason Grading Model"
    model_version: "2.1.0"
    model_path: "models:/gleason_grading/production"
    priority: 100
    min_confidence: 0.85
    task_type: "grading"
    required_tags:
      organ: "prostate"
      stain: "H&E"
      task: "grading"
```

**Commandes:**
```bash
# Valider configuration
python -m services.ml.tag_router

# Recharger configuration (hot reload)
# Via API: POST /api/ml/routes/reload
```

---

## Database Schema

**Tables principales:**

- `slides_metadata` - Métadonnées slides avec tags ML
- `ml_predictions` - Prédictions ML + uncertainty
- `ml_feedback` - Feedback pathologistes
- `model_registry` - Registry modèles (sync MLflow)
- `retraining_logs` - Historique re-entraînements
- `drift_monitoring` - Logs drift detection

**Création schema:**
```bash
psql -U varuna_ml -d varuna_db -f backend/database/schema_ml.sql
```

**Views utiles:**
- `model_performance_summary` - Stats par modèle
- `pending_feedback_summary` - Feedback non traité
- `active_learning_priority_queue` - Cas à annoter en priorité

---

## Intégration avec MLflow

**Setup MLflow tracking:**
```bash
# Start MLflow server
mlflow server --host 0.0.0.0 --port 5000 \
  --backend-store-uri postgresql://mlflow:pass@db:5432/mlflow \
  --default-artifact-root s3://varuna-ml-models
```

**Configuration Python:**
```python
import mlflow

mlflow.set_tracking_uri("http://mlflow.chu-ucl.local:5000")
mlflow.set_experiment("varuna_pathology_ml")

with mlflow.start_run():
    mlflow.log_param("model_type", "gleason_grading")
    mlflow.log_metric("accuracy", 0.94)
    mlflow.pytorch.log_model(model, "model")
```

**Model Registry:**
```bash
# Register model
mlflow models register-model "runs:/<run_id>/model" "gleason_grading"

# Promote to production
mlflow models transition-model-version-stage \
  --name "gleason_grading" \
  --version 2 \
  --stage Production
```

---

## Intégration avec DVC

**Setup DVC:**
```bash
# Initialize DVC
dvc init

# Add remote storage
dvc remote add -d minio s3://varuna-ml-data
dvc remote modify minio endpointurl http://minio.chu-ucl.local:9000

# Configure credentials
export MINIO_SECRET_KEY="your-secret-key"
dvc remote modify minio secret_access_key env:MINIO_SECRET_KEY
```

**Versioning datasets:**
```bash
# Add dataset
dvc add data/annotations/gleason_v1
git add data/annotations/gleason_v1.dvc .gitignore
git commit -m "data: Add Gleason annotations v1"

# Push to remote
dvc push

# Pull specific version
git checkout v2.0-with-feedback
dvc pull
```

---

## Testing

**Tests unitaires:**
```bash
# Test tag extraction
python backend/services/ml/tag_extractor.py

# Test tag routing
python backend/services/ml/tag_router.py

# Run all ML tests
pytest backend/services/ml/tests/
```

**Integration tests:**
```bash
# Test full inference pipeline
pytest backend/tests/integration/test_ml_pipeline.py

# Test feedback loop
pytest backend/tests/integration/test_feedback_loop.py
```

---

## Monitoring

**Métriques à surveiller:**

1. **Model Performance:**
   - Approval rate (objectif: > 85%)
   - Confidence score (moyenne)
   - Uncertainty score (distribution)
   - Inference time (< 5s)

2. **Feedback Volume:**
   - Feedback count (par jour/semaine)
   - Corrections vs approvals ratio
   - Pending feedback count

3. **Drift Detection:**
   - Data drift (PSI < 0.25)
   - Prediction drift (KS statistic)
   - Performance drift (metric changes)

**Dashboards:**
- Grafana: http://grafana.chu-ucl.local:3000
- MLflow UI: http://mlflow.chu-ucl.local:5000
- Label Studio: http://labelstudio.chu-ucl.local:8080

---

## Troubleshooting

### Tag extraction échoue

**Problème:** Tags non extraits (confidence = 0)

**Solutions:**
1. Vérifier filename patterns
2. Ajouter keywords dans `_load_organ_keywords()`
3. Activer ML inference (si modèle disponible)
4. Assignation manuelle via UI

### Routing vers mauvais modèle

**Problème:** Slide routée vers modèle incorrect

**Solutions:**
1. Vérifier tags extraits (`/api/slides/{id}/tags`)
2. Vérifier configuration `ml_routes.yaml`
3. Ajuster `required_tags` pour modèle concerné
4. Reload configuration: `POST /api/ml/routes/reload`

### Re-entraînement pas déclenché

**Problème:** Seuil feedback atteint mais pas de retraining

**Solutions:**
1. Vérifier fonction `should_trigger_retraining()` en DB
2. Vérifier logs Airflow
3. Tester manuellement: `airflow dags trigger feedback_retraining_<model>`
4. Vérifier permissions MLflow/DVC

---

## References

**Documentation:**
- Architecture MLOps: `docs/MLOPS_ARCHITECTURE.md`
- API Endpoints: http://localhost:8000/docs
- MLflow: https://mlflow.org/docs/latest/
- DVC: https://dvc.org/doc

**Papers:**
- Sculley et al. (2023): "Hidden Technical Debt in ML Systems"
- Pantanowitz et al. (2024): "Annotation Quality in Digital Pathology"
- Settles (2009): "Active Learning Literature Survey"

**Tools:**
- MLflow: https://github.com/mlflow/mlflow
- DVC: https://github.com/iterative/dvc
- Label Studio: https://github.com/heartexlabs/label-studio
- Evidently AI: https://github.com/evidentlyai/evidently

---

**Version:** 1.0 (Phase 3.1-3.2 implémentée)
**Dernière mise à jour:** 2025-12-31
**Contact:** ML Team VarunaPoC
