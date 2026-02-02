# MLOPS_INTEGRATION_GUIDE.md

**Guide d'Intégration MLOps - VarunaPoC Phase 3**

**Date:** 2025-12-31
**Version:** 1.0
**Audience:** Développeurs, Data Scientists, DevOps

---

## Table des Matières

1. [Introduction](#1-introduction)
2. [Prérequis](#2-prérequis)
3. [Phase 3.1: Infrastructure MLOps](#3-phase-31-infrastructure-mlops)
4. [Phase 3.2: Tag System & Routing](#4-phase-32-tag-system--routing)
5. [Phase 3.3: Feedback Pipeline](#5-phase-33-feedback-pipeline)
6. [Phase 3.4: Continuous Learning](#6-phase-34-continuous-learning)
7. [Validation & Testing](#7-validation--testing)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Introduction

Ce guide détaille l'intégration progressive des fonctionnalités MLOps dans VarunaPoC existant.

**Objectif:** Transformer VarunaPoC en plateforme d'apprentissage continu sans casser le code existant.

**Principe:** Intégration incrémentale par feature flags - le système actuel continue de fonctionner.

---

## 2. Prérequis

### 2.1. Infrastructure Existante

**Vérifier que VarunaPoC Phase 1-2 fonctionne:**

```bash
# Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev

# Tester
curl http://localhost:8000/api/health
# {"status": "healthy"}
```

### 2.2. Outils Requis

**Installer:**

```bash
# Python packages (backend)
pip install mlflow dvc evidently-ai label-studio-sdk apache-airflow

# Database (PostgreSQL >= 13)
# Docker: docker run -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15

# MinIO (S3-compatible storage)
# Docker: docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
```

### 2.3. Credentials & Secrets

**Créer fichier `.env.mlops`:**

```bash
# backend/.env.mlops

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# DVC
DVC_REMOTE_URL=s3://varuna-ml-data
DVC_REMOTE_ENDPOINT=http://localhost:9000

# PostgreSQL
DATABASE_URL=postgresql://varuna:password@localhost:5432/varuna_ml

# Label Studio
LABEL_STUDIO_URL=http://localhost:8080
LABEL_STUDIO_API_KEY=your-api-key-here
```

---

## 3. Phase 3.1: Infrastructure MLOps

**Durée estimée:** 2-3 semaines

### 3.1.1. Setup MLflow

**Étape 1: Créer database MLflow**

```sql
-- Via psql
CREATE DATABASE mlflow_db;
CREATE USER mlflow_user WITH PASSWORD 'mlflow_password';
GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO mlflow_user;
```

**Étape 2: Démarrer MLflow tracking server**

```bash
# Terminal 1
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri postgresql://mlflow_user:mlflow_password@localhost:5432/mlflow_db \
  --default-artifact-root s3://varuna-ml-models \
  --serve-artifacts

# Vérifier: http://localhost:5000
```

**Étape 3: Tester tracking**

```python
# test_mlflow.py
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("test_experiment")

with mlflow.start_run():
    mlflow.log_param("test_param", 42)
    mlflow.log_metric("test_metric", 0.95)
    print("MLflow tracking OK!")
```

### 3.1.2. Setup DVC

**Étape 1: Initialiser DVC**

```bash
cd VarunaPoC
dvc init

# Ajouter remote MinIO
dvc remote add -d minio s3://varuna-ml-data
dvc remote modify minio endpointurl http://localhost:9000
dvc remote modify minio access_key_id minioadmin
dvc remote modify minio secret_access_key minioadmin

# Test connexion
dvc remote list
```

**Étape 2: Versionner premier dataset**

```bash
# Créer dossier test
mkdir -p data/test_dataset
echo "test data" > data/test_dataset/sample.txt

# Ajouter à DVC
dvc add data/test_dataset
git add data/test_dataset.dvc .gitignore
git commit -m "test: Add test dataset"

# Push vers remote
dvc push
```

### 3.1.3. Setup Database ML

**Étape 1: Créer schema**

```bash
# Créer database
createdb varuna_ml

# Appliquer schema
psql -U postgres -d varuna_ml -f backend/database/schema_ml.sql

# Vérifier tables
psql -U postgres -d varuna_ml -c "\dt"
# Doit afficher: slides_metadata, ml_predictions, ml_feedback, etc.
```

**Étape 2: Configurer connexion backend**

```python
# backend/database/connection.py (NOUVEAU)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/varuna_ml")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.1.4. Setup Label Studio

**Étape 1: Démarrer Label Studio**

```bash
# Via Docker
docker run -p 8080:8080 \
  -v $(pwd)/label_studio_data:/label-studio/data \
  heartexlabs/label-studio:latest

# Ou via pip
label-studio start --port 8080

# Accéder: http://localhost:8080
```

**Étape 2: Créer projet WSI**

```bash
# Via API
curl -X POST http://localhost:8080/api/projects \
  -H "Authorization: Token your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "VarunaPoC Annotations",
    "label_config": "<View><Image name=\"slide\" value=\"$image\"/><PolygonLabels name=\"regions\" toName=\"slide\"><Label value=\"Tumeur\"/><Label value=\"Normal\"/></PolygonLabels></View>"
  }'
```

### 3.1.5. Validation Phase 3.1

**Checklist:**

- [ ] MLflow tracking server accessible (http://localhost:5000)
- [ ] DVC push/pull fonctionne
- [ ] Database `varuna_ml` créée avec toutes les tables
- [ ] Label Studio accessible (http://localhost:8080)
- [ ] MinIO accessible (http://localhost:9001)

**Test intégration:**

```bash
# Test complet infrastructure
python backend/tests/integration/test_mlops_infrastructure.py
```

---

## 4. Phase 3.2: Tag System & Routing

**Durée estimée:** 2-3 semaines

### 4.2.1. Intégrer TagExtractor

**Étape 1: Ajouter au backend existant**

```python
# backend/services/slide_scanner.py (MODIFIER)

from services.ml import TagExtractor

# Ajouter instance globale
tag_extractor = TagExtractor()

def scan_slides_directory():
    """
    Liste toutes les lames (EXISTANT).

    MODIFICATION: Ajouter extraction tags.
    """
    slides = []
    detector = FormatDetector()

    for slide_format in detector.scan_directory(SLIDES_DIR):
        slide_id = generate_slide_id(slide_format.entry_point)

        # NOUVEAU: Extraire tags
        tags = tag_extractor.extract_tags(
            str(slide_format.entry_point),
            slide_format.format_string
        )

        slides.append({
            "id": slide_id,
            "name": slide_format.entry_point.name,
            "format": slide_format.format_string,
            # NOUVEAU: Ajouter tags
            "tags": tags
        })

    return slides
```

**Étape 2: Stocker tags en DB**

```python
# backend/services/slide_metadata_service.py (NOUVEAU)

from database.connection import get_db
from sqlalchemy.sql import text

def store_slide_tags(slide_id: str, tags: dict, slide_metadata: dict):
    """
    Stocke tags ML en database.

    Args:
        slide_id: ID unique slide
        tags: Tags extraits (organ, stain, marker)
        slide_metadata: Métadonnées slide (dimensions, etc.)
    """
    db = next(get_db())

    query = text("""
        INSERT INTO slides_metadata
        (slide_id, slide_path, slide_name, format, vendor, width, height,
         organ, stain, marker, tags_source, tags_confidence)
        VALUES
        (:slide_id, :path, :name, :format, :vendor, :width, :height,
         :organ, :stain, :marker, :source, :confidence)
        ON CONFLICT (slide_id) DO UPDATE SET
            organ = EXCLUDED.organ,
            stain = EXCLUDED.stain,
            marker = EXCLUDED.marker,
            tags_source = EXCLUDED.tags_source,
            tags_confidence = EXCLUDED.tags_confidence,
            updated_at = NOW()
    """)

    db.execute(query, {
        "slide_id": slide_id,
        "path": slide_metadata["path"],
        "name": slide_metadata["name"],
        "format": slide_metadata["format"],
        "vendor": slide_metadata.get("vendor"),
        "width": slide_metadata.get("width"),
        "height": slide_metadata.get("height"),
        "organ": tags.get("organ"),
        "stain": tags.get("stain"),
        "marker": tags.get("marker"),
        "source": tags.get("source"),
        "confidence": tags.get("confidence")
    })

    db.commit()
```

### 4.2.2. Configurer Router

**Étape 1: Créer configuration**

```bash
# Déjà créé: backend/config/ml_routes.yaml
# Éditer selon modèles disponibles

# Valider configuration
python backend/services/ml/tag_router.py
```

**Étape 2: Endpoint routing**

```python
# backend/routes/ml_inference.py (NOUVEAU)

from fastapi import APIRouter, HTTPException
from services.ml import TagRouter

router = APIRouter(prefix="/api/ml", tags=["ml_inference"])

tag_router = TagRouter("config/ml_routes.yaml")

@router.get("/route/{slide_id}")
async def get_model_route(slide_id: str):
    """
    Détermine quel modèle utiliser pour une slide.

    Returns:
        {
            "model_id": str,
            "model_name": str,
            "model_version": str,
            "confidence_threshold": float
        }
    """
    # Récupérer tags depuis DB
    tags = get_slide_tags(slide_id)

    # Router
    route = tag_router.route(tags)

    return {
        "model_id": route.model_id,
        "model_name": route.model_name,
        "model_version": route.model_version,
        "confidence_threshold": route.min_confidence,
        "tags_used": tags
    }
```

### 4.2.3. UI pour assignation manuelle

**Étape 1: Composant frontend**

```javascript
// frontend/src/components/ml/TagAssignmentPanel.js (NOUVEAU)

export class TagAssignmentPanel {
    constructor(slideId) {
        this.slideId = slideId;
    }

    async render() {
        const tags = await this.fetchCurrentTags();

        return `
        <div class="tag-assignment-panel">
            <h3>Tags ML</h3>

            ${tags.confidence < 0.7 ? `
                <div class="alert alert-warning">
                    Confiance faible (${(tags.confidence * 100).toFixed(1)}%)
                    - Assignation manuelle recommandée
                </div>
            ` : ''}

            <form id="tag-form">
                <label>Organ:</label>
                <select name="organ">
                    <option value="">-- Sélectionner --</option>
                    <option value="prostate" ${tags.organ === 'prostate' ? 'selected' : ''}>Prostate</option>
                    <option value="sein" ${tags.organ === 'sein' ? 'selected' : ''}>Sein</option>
                    <option value="côlon" ${tags.organ === 'côlon' ? 'selected' : ''}>Côlon</option>
                    <!-- etc. -->
                </select>

                <label>Stain:</label>
                <select name="stain">
                    <option value="">-- Sélectionner --</option>
                    <option value="H&E" ${tags.stain === 'H&E' ? 'selected' : ''}>H&E</option>
                    <option value="IHC" ${tags.stain === 'IHC' ? 'selected' : ''}>IHC</option>
                    <!-- etc. -->
                </select>

                <button type="submit">Sauvegarder Tags</button>
            </form>
        </div>
        `;
    }

    async fetchCurrentTags() {
        const response = await fetch(`/api/slides/${this.slideId}/tags`);
        return response.json();
    }

    async saveTags(tags) {
        await fetch(`/api/slides/${this.slideId}/tags`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                ...tags,
                source: 'manual',
                confidence: 1.0
            })
        });
    }
}
```

### 4.2.4. Validation Phase 3.2

**Checklist:**

- [ ] Tags extraits pour 80%+ des slides
- [ ] Routing fonctionne (`/api/ml/route/{id}`)
- [ ] Assignation manuelle disponible dans UI
- [ ] Tags stockés en DB

**Test:**

```bash
# Test extraction + routing
curl http://localhost:8000/api/ml/route/abc123
# → {"model_id": "gleason_grading_v2", ...}
```

---

## 5. Phase 3.3: Feedback Pipeline

**Durée estimée:** 2-3 semaines

### 5.3.1. Endpoint Feedback

**Créer API feedback:**

```python
# backend/routes/ml_feedback.py (NOUVEAU)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/ml", tags=["ml_feedback"])

class FeedbackCreate(BaseModel):
    slide_id: str
    prediction_id: str
    action: str  # "approve", "correct", "reject"
    original_prediction: dict | None = None
    corrected_prediction: dict | None = None
    notes: str | None = None

@router.post("/feedback")
async def record_feedback(feedback: FeedbackCreate):
    """
    Enregistre feedback pathologiste.

    Process:
    1. Valide feedback
    2. Stocke en DB
    3. Incrémente compteur retraining
    """
    # Valider
    if feedback.action not in ["approve", "correct", "reject"]:
        raise HTTPException(400, "Invalid action")

    # Stocker en DB
    db = next(get_db())
    query = text("""
        INSERT INTO ml_feedback
        (slide_id, prediction_id, model_id, model_version, action,
         original_prediction, corrected_prediction, notes, pathologist_id)
        VALUES
        (:slide_id, :prediction_id, :model_id, :model_version, :action,
         :original::jsonb, :corrected::jsonb, :notes, :pathologist_id)
    """)

    db.execute(query, {
        "slide_id": feedback.slide_id,
        "prediction_id": feedback.prediction_id,
        # ... autres params
    })
    db.commit()

    return {"status": "recorded", "message": "Feedback enregistré"}
```

### 5.3.2. UI Feedback Panel

**Intégrer dans viewer:**

```javascript
// frontend/src/components/ml/FeedbackPanel.js (NOUVEAU)

// Voir docs/MLOPS_ARCHITECTURE.md Section 4.2 pour code complet

export class FeedbackPanel {
    render(prediction) {
        return `
        <div class="feedback-panel">
            <h3>ML Prediction</h3>
            <div class="prediction">${prediction.class}</div>
            <div class="confidence">${(prediction.confidence * 100).toFixed(1)}%</div>

            <div class="actions">
                <button onclick="handleFeedback('approve')">✓ Correct</button>
                <button onclick="handleFeedback('correct')">✎ Correct</button>
                <button onclick="handleFeedback('reject')">✗ Reject</button>
            </div>
        </div>
        `;
    }
}
```

### 5.3.3. Validation Phase 3.3

**Checklist:**

- [ ] Endpoint `/api/ml/feedback` fonctionne
- [ ] FeedbackPanel visible dans viewer
- [ ] Feedback stocké en DB
- [ ] Dashboard feedback stats disponible

---

## 6. Phase 3.4: Continuous Learning

**Durée estimée:** 3-4 mois

### 6.4.1. Setup Airflow

**Installation:**

```bash
# Via Docker Compose
# Voir: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/

docker-compose up -d

# Accéder: http://localhost:8080
# Login: airflow / airflow
```

### 6.4.2. DAG Re-entraînement

**Créer pipeline:**

```python
# pipelines/retraining/feedback_retraining_dag.py

# Voir docs/MLOPS_ARCHITECTURE.md Section 5.2 pour code complet

from airflow import DAG
from airflow.operators.python import PythonOperator

# Tasks:
# 1. Check threshold
# 2. Prepare dataset (DVC)
# 3. Train model (MLflow)
# 4. Validate
# 5. Deploy A/B test
```

### 6.4.3. Validation Phase 3.4

**Checklist:**

- [ ] Airflow DAG créé et activé
- [ ] Re-entraînement manuel fonctionne
- [ ] Auto-trigger sur seuil feedback
- [ ] A/B testing déployé

---

## 7. Validation & Testing

### 7.1. Tests Unitaires

```bash
# Tag extraction
pytest backend/services/ml/tests/test_tag_extractor.py

# Tag routing
pytest backend/services/ml/tests/test_tag_router.py

# Feedback
pytest backend/services/ml/tests/test_feedback_service.py
```

### 7.2. Tests Intégration

```bash
# Pipeline complet
pytest backend/tests/integration/test_ml_pipeline.py

# Vérifier:
# - Tag extraction → Routing → Inference → Feedback → Dataset update
```

### 7.3. Tests End-to-End

```bash
# Scenario utilisateur complet
# 1. Upload slide
# 2. Tags auto-extraits
# 3. Modèle routé
# 4. Prédiction affichée
# 5. Pathologiste corrige
# 6. Feedback enregistré
```

---

## 8. Troubleshooting

### MLflow connexion refused

**Symptôme:** `requests.exceptions.ConnectionError`

**Solution:**
```bash
# Vérifier MLflow running
curl http://localhost:5000/health

# Redémarrer si nécessaire
mlflow server --host 0.0.0.0 --port 5000 ...
```

### DVC push échoue

**Symptôme:** `ERROR: failed to push data to remote`

**Solution:**
```bash
# Vérifier MinIO accessible
curl http://localhost:9000/minio/health/live

# Test credentials
dvc remote list
dvc remote modify minio access_key_id minioadmin
dvc remote modify minio secret_access_key minioadmin
```

### Tags non extraits

**Symptôme:** `tags = {"organ": None, "confidence": 0.0}`

**Solution:**
1. Vérifier filename pattern
2. Ajouter keywords dans `tag_extractor.py`
3. Assignation manuelle via UI

---

## Next Steps

**Après intégration complète:**

1. Entraîner premiers modèles spécialisés
2. Déployer en production avec monitoring
3. Collecter feedback réel pathologistes
4. Itérer sur modèles

**Roadmap modèles:**
- Phase 3.5.1: Gleason grading (prostate)
- Phase 3.5.2: Ki-67 counting (sein)
- Phase 3.5.3: HER2 scoring (sein)

---

**Version:** 1.0
**Dernière mise à jour:** 2025-12-31
**Contact:** ML Team VarunaPoC
