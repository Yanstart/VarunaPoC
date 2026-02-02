# MLOPS_ARCHITECTURE.md

**VarunaPoC - Architecture MLOps pour Apprentissage Continu en Pathologie Digitale**

**Status:** Architecture de référence pour Phase 3
**Version:** 1.0
**Date:** 2025-12-31
**Auteur:** ML Architect Agent (VarunaPoC)

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Système de Routage par Tags](#2-système-de-routage-par-tags)
3. [Infrastructure MLOps](#3-infrastructure-mlops)
4. [Pipeline de Feedback Pathologistes](#4-pipeline-de-feedback-pathologistes)
5. [Architecture Technique](#5-architecture-technique)
6. [Structures de Données](#6-structures-de-données)
7. [Intégration avec VarunaPoC Existant](#7-intégration-avec-varunapoc-existant)
8. [Roadmap d'Implémentation](#8-roadmap-dimplémentation)
9. [Références & Outils](#9-références--outils)

---

## 1. Vue d'Ensemble

### 1.1. Mission MLOps

**Objectif:** Transformer VarunaPoC en plateforme d'apprentissage continu où les modèles ML s'améliorent automatiquement grâce aux validations/corrections des pathologistes.

**Principe de base:**
```
Slide → ML Inference → Pathologiste valide/corrige → Feedback capturé → Dataset enrichi → Re-entraînement automatisé → Modèle amélioré
```

### 1.2. Workflow Complet

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VARUNA MLOps PIPELINE                         │
└─────────────────────────────────────────────────────────────────────┘

1. INGESTION & TAGGING
   ↓
   Slide + Metadata DICOM → Tag Extractor → [organ, stain, marker, task]

2. ROUTING
   ↓
   Tag-based Router → Modèle spécialisé (Gleason, Ki-67, HER2, etc.)

3. INFERENCE
   ↓
   ML Model → Prédictions + Uncertainty + Explainability (Grad-CAM)

4. PATHOLOGIST FEEDBACK
   ↓
   Interface validation → [Approve, Correct, Reject, Annotate]

5. FEEDBACK CAPTURE
   ↓
   Feedback DB → Versioned Dataset (DVC) → MLflow Tracking

6. CONTINUOUS LEARNING
   ↓
   Seuil corrections atteint → Re-entraînement → Validation → Déploiement A/B

7. MONITORING
   ↓
   Drift Detection → Performance Tracking → Alertes qualité
```

### 1.3. Principes Fondamentaux

**Quality-First:**
- Jamais de prédiction sans score de confiance
- Uncertainty quantification obligatoire (Monte Carlo Dropout)
- Explainability systématique (Grad-CAM, SHAP)

**Human-in-the-Loop:**
- Pathologiste garde contrôle total
- Active learning pour prioriser cas incertains
- Feedback multi-niveaux (validation, correction, annotation)

**MLOps Automation:**
- Versioning complet (code + data + models)
- Pipeline CI/CD pour modèles
- A/B testing avant déploiement production
- Rollback automatique si dégradation

---

## 2. Système de Routage par Tags

### 2.1. Architecture des Tags

**Hiérarchie de tags (4 niveaux):**

```python
{
    "organ": str,           # sein, prostate, côlon, poumon, etc.
    "stain": str,           # H&E, IHC, IF, etc.
    "marker": str | null,   # Ki-67, HER2, PDL1, etc. (si IHC)
    "task": str             # classification, segmentation, detection, grading, counting
}
```

**Exemples de combinaisons:**

| Slide Type | organ | stain | marker | task | Modèle Routé |
|------------|-------|-------|--------|------|--------------|
| Prostate H&E | prostate | H&E | null | grading | Gleason Grading Model |
| Sein IHC Ki-67 | sein | IHC | Ki-67 | counting | Ki-67 Proliferation Index |
| Sein IHC HER2 | sein | IHC | HER2 | classification | HER2 Scoring Model |
| Côlon H&E | côlon | H&E | null | classification | Colorectal Tumor Classifier |
| Poumon PDL1 | poumon | IHC | PDL1 | detection | PD-L1 TPS Quantification |

### 2.2. Sources de Tags

**Priorité de détection (du plus fiable au moins fiable):**

1. **DICOM Metadata (si disponible)**
   ```python
   # Extraction depuis tags DICOM WSI
   organ = dicom_metadata.get("AnatomicRegionSequence", None)
   stain = dicom_metadata.get("StainSequence", None)
   marker = dicom_metadata.get("SpecimenDescriptionSequence", None)
   ```

2. **Inférence par Modèle Léger**
   ```python
   # Modèle de classification rapide sur overview
   # Réseau léger (MobileNetV3, EfficientNet-Lite)
   # Input: thumbnail 512x512
   # Output: [organ_probs, stain_probs]
   # Latence: < 100ms

   tag_classifier = TagClassifierModel()
   tags = tag_classifier.predict(slide_overview)
   # tags = {"organ": "sein", "stain": "H&E", "confidence": 0.94}
   ```

3. **Assignation Manuelle (Fallback)**
   ```python
   # Interface UI pour pathologiste
   # Si auto-détection échoue ou confiance < seuil
   # Stocké dans metadata DB pour réutilisation
   ```

### 2.3. Tag Router Implementation

**Router central:**

```python
# backend/services/ml/tag_router.py

from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ModelRoute:
    """Route vers modèle ML spécialisé."""
    model_id: str           # Identifiant unique modèle
    model_name: str         # Nom lisible
    model_version: str      # Version (semantic versioning)
    model_path: str         # Chemin vers artefact MLflow
    priority: int           # Priorité si plusieurs matchs
    min_confidence: float   # Seuil confiance minimum
    task_type: str          # classification, segmentation, etc.

class TagRouter:
    """
    Routeur intelligent basé sur tags.

    Références:
    - Tag-based ML routing pattern (Uber Michelangelo)
    - Multi-model serving architecture (Netflix)
    """

    def __init__(self, routes_config_path: str):
        self.routes = self._load_routes_config(routes_config_path)
        self.fallback_model = self._load_fallback_model()

    def route(self, tags: Dict[str, str]) -> ModelRoute:
        """
        Route une lame vers le modèle approprié.

        Args:
            tags: {"organ": "prostate", "stain": "H&E", "marker": null, "task": "grading"}

        Returns:
            ModelRoute: Route vers modèle spécialisé ou fallback

        Examples:
            >>> router = TagRouter("config/ml_routes.yaml")
            >>> tags = {"organ": "prostate", "stain": "H&E", "task": "grading"}
            >>> route = router.route(tags)
            >>> print(route.model_name)
            "Gleason Grading Model v2.1"
        """
        # Recherche exacte (tous les tags matchent)
        exact_matches = self._find_exact_matches(tags)
        if exact_matches:
            return self._select_best_route(exact_matches)

        # Recherche partielle (organ + stain minimum)
        partial_matches = self._find_partial_matches(tags)
        if partial_matches:
            return self._select_best_route(partial_matches)

        # Fallback vers modèle générique
        return self.fallback_model

    def _find_exact_matches(self, tags: Dict) -> list[ModelRoute]:
        """Match exact sur tous les tags."""
        matches = []
        for route in self.routes:
            if self._tags_match(route.required_tags, tags, exact=True):
                matches.append(route)
        return matches

    def _find_partial_matches(self, tags: Dict) -> list[ModelRoute]:
        """Match partiel (organ + stain minimum)."""
        matches = []
        for route in self.routes:
            required = ["organ", "stain"]
            if all(route.required_tags.get(k) == tags.get(k) for k in required):
                matches.append(route)
        return matches

    def _select_best_route(self, matches: list[ModelRoute]) -> ModelRoute:
        """Sélectionne le meilleur match par priorité."""
        return max(matches, key=lambda r: r.priority)
```

**Configuration des routes (YAML):**

```yaml
# backend/config/ml_routes.yaml

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

  - model_id: "ki67_counter_v3"
    model_name: "Ki-67 Proliferation Index"
    model_version: "3.0.1"
    model_path: "models:/ki67_counting/production"
    priority: 100
    min_confidence: 0.90
    task_type: "counting"
    required_tags:
      organ: "sein"
      stain: "IHC"
      marker: "Ki-67"
      task: "counting"

  - model_id: "her2_scoring_v1"
    model_name: "HER2 Scoring Model"
    model_version: "1.5.0"
    model_path: "models:/her2_scoring/production"
    priority: 100
    min_confidence: 0.88
    task_type: "classification"
    required_tags:
      organ: "sein"
      stain: "IHC"
      marker: "HER2"
      task: "classification"

  # Fallback générique
  - model_id: "generic_tumor_detection"
    model_name: "Generic Tumor Detection"
    model_version: "1.0.0"
    model_path: "models:/generic_detection/production"
    priority: 1
    min_confidence: 0.75
    task_type: "detection"
    required_tags: {}  # Match tout
```

### 2.4. Tag Extraction Service

**Service d'extraction automatique:**

```python
# backend/services/ml/tag_extractor.py

import openslide
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TagExtractor:
    """
    Extracteur de tags depuis métadonnées slide.

    Sources:
    1. DICOM metadata (si format DICOM)
    2. OpenSlide properties (vendor-specific)
    3. Filename parsing (fallback)
    4. ML inference (si nécessaire)
    """

    def __init__(self, tag_classifier_model=None):
        self.tag_classifier = tag_classifier_model
        self.organ_keywords = self._load_organ_keywords()
        self.stain_keywords = self._load_stain_keywords()

    def extract_tags(self, slide_path: str, slide_format: str) -> Dict:
        """
        Extrait tags d'une lame.

        Args:
            slide_path: Chemin vers lame
            slide_format: Format détecté (DICOM, MRXS, etc.)

        Returns:
            {
                "organ": str | null,
                "stain": str | null,
                "marker": str | null,
                "task": str | null,
                "confidence": float,
                "source": str  # "dicom", "properties", "filename", "ml_inference"
            }
        """
        # 1. Essayer DICOM si applicable
        if slide_format.lower() == "dicom":
            tags = self._extract_from_dicom(slide_path)
            if tags and tags.get("confidence", 0) > 0.9:
                return tags

        # 2. Essayer OpenSlide properties
        tags = self._extract_from_openslide_properties(slide_path)
        if tags and tags.get("confidence", 0) > 0.8:
            return tags

        # 3. Parser filename (patterns communs)
        tags = self._extract_from_filename(slide_path)
        if tags and tags.get("confidence", 0) > 0.7:
            return tags

        # 4. ML inference (si modèle disponible)
        if self.tag_classifier:
            tags = self._extract_via_ml_inference(slide_path)
            if tags and tags.get("confidence", 0) > 0.75:
                return tags

        # 5. Fallback: demander assignation manuelle
        return {
            "organ": None,
            "stain": None,
            "marker": None,
            "task": None,
            "confidence": 0.0,
            "source": "manual_required"
        }

    def _extract_from_dicom(self, slide_path: str) -> Optional[Dict]:
        """Extraction depuis tags DICOM."""
        # TODO: Implémenter avec pydicom
        # Lire tags DICOM standard pour WSI
        pass

    def _extract_from_openslide_properties(self, slide_path: str) -> Optional[Dict]:
        """
        Extraction depuis propriétés OpenSlide.

        OpenSlide expose metadata vendor-specific:
        - 3DHistech: Properties avec "3DHISTECH." prefix
        - Aperio: Properties avec "aperio." prefix
        - Ventana: Properties avec description texte
        """
        try:
            slide = openslide.OpenSlide(slide_path)
            properties = dict(slide.properties)
            slide.close()

            # Recherche par keywords dans properties
            organ = self._find_organ_in_text(" ".join(properties.values()))
            stain = self._find_stain_in_text(" ".join(properties.values()))

            if organ or stain:
                return {
                    "organ": organ,
                    "stain": stain,
                    "marker": None,  # Difficile à extraire automatiquement
                    "task": None,
                    "confidence": 0.8,
                    "source": "openslide_properties"
                }
        except Exception as e:
            logger.warning(f"Error extracting from OpenSlide properties: {e}")

        return None

    def _extract_from_filename(self, slide_path: str) -> Optional[Dict]:
        """
        Parsing patterns communs de noms de fichiers.

        Patterns fréquents:
        - "prostate_HE_patient123.mrxs"
        - "breast_Ki67_sample45.svs"
        - "colon_HER2_case789.bif"
        """
        import re
        from pathlib import Path

        filename = Path(slide_path).stem.lower()

        organ = self._find_organ_in_text(filename)
        stain = self._find_stain_in_text(filename)

        # Recherche marker IHC
        marker = None
        markers = ["ki-67", "ki67", "her2", "pdl1", "pd-l1", "er", "pr"]
        for m in markers:
            if m in filename:
                marker = m.upper().replace("-", "")
                break

        if organ or stain or marker:
            return {
                "organ": organ,
                "stain": stain,
                "marker": marker,
                "task": None,
                "confidence": 0.7,
                "source": "filename_parsing"
            }

        return None

    def _extract_via_ml_inference(self, slide_path: str) -> Optional[Dict]:
        """
        Inférence ML pour détecter organ + stain.

        Utilise un modèle léger (EfficientNet-Lite) entraîné sur overview.
        """
        if not self.tag_classifier:
            return None

        try:
            # Charger thumbnail
            slide = openslide.OpenSlide(slide_path)
            thumbnail = slide.get_thumbnail((512, 512))
            slide.close()

            # Inférence
            predictions = self.tag_classifier.predict(thumbnail)

            if predictions["confidence"] > 0.75:
                return {
                    "organ": predictions.get("organ"),
                    "stain": predictions.get("stain"),
                    "marker": None,
                    "task": None,
                    "confidence": predictions["confidence"],
                    "source": "ml_inference"
                }
        except Exception as e:
            logger.error(f"ML inference failed: {e}")

        return None

    def _find_organ_in_text(self, text: str) -> Optional[str]:
        """Recherche organ par keywords."""
        text = text.lower()
        for organ, keywords in self.organ_keywords.items():
            if any(kw in text for kw in keywords):
                return organ
        return None

    def _find_stain_in_text(self, text: str) -> Optional[str]:
        """Recherche stain par keywords."""
        text = text.lower()
        for stain, keywords in self.stain_keywords.items():
            if any(kw in text for kw in keywords):
                return stain
        return None

    def _load_organ_keywords(self) -> Dict[str, list]:
        """Keywords pour détection organ."""
        return {
            "prostate": ["prostate", "prostatic"],
            "sein": ["breast", "mammary", "sein"],
            "côlon": ["colon", "colorectal", "rectal"],
            "poumon": ["lung", "pulmonary", "poumon"],
            "foie": ["liver", "hepatic", "foie"],
            "rein": ["kidney", "renal", "rein"]
        }

    def _load_stain_keywords(self) -> Dict[str, list]:
        """Keywords pour détection stain."""
        return {
            "H&E": ["h&e", "he", "hematoxylin", "eosin"],
            "IHC": ["ihc", "immunohistochemistry", "immunohistochimie"],
            "IF": ["if", "immunofluorescence"]
        }
```

---

## 3. Infrastructure MLOps

### 3.1. Stack Technologique

**Outils recommandés (éprouvés en production):**

| Composant | Outil | Justification |
|-----------|-------|---------------|
| **Versioning Data** | DVC | Standard industrie, intégration Git native |
| **Versioning Models** | MLflow | Tracking expérimentations + registry modèles |
| **Annotation Platform** | Label Studio | Open source, supporte WSI, ML-assisted labeling |
| **Monitoring** | Evidently AI | Drift detection, data quality, model performance |
| **Model Serving** | FastAPI + TorchServe | Déjà FastAPI, TorchServe pour PyTorch models |
| **Pipeline Orchestration** | Airflow / Prefect | Workflows complexes, retry logic, scheduling |
| **Container Registry** | Docker Hub / Harbor | Versioning images Docker |
| **CI/CD** | GitHub Actions / GitLab CI | Intégration native avec repo |

### 3.2. Architecture de Versioning

**Git + DVC + MLflow (triangle d'or MLOps):**

```
VarunaPoC/
├── .git/                           ← Code versioning (Git)
├── .dvc/                           ← Data versioning (DVC)
│   ├── config                      # Remote storage config (S3, MinIO, NAS)
│   └── cache/                      # Cache local datasets
│
├── data/
│   ├── raw/                        ← Slides originales (pointeur DVC)
│   │   ├── train.dvc               # DVC file (hash + remote path)
│   │   └── val.dvc
│   │
│   ├── annotations/                ← Annotations pathologistes (DVC)
│   │   ├── gleason_v1.dvc
│   │   ├── gleason_v2.dvc          # Version avec corrections feedback
│   │   └── ki67_v1.dvc
│   │
│   └── feedback/                   ← Feedback capturé (DVC)
│       ├── corrections.dvc
│       └── validations.dvc
│
├── models/
│   ├── gleason_grading/
│   │   ├── v1.0/
│   │   │   ├── model.pth           ← Poids modèle (MLflow artifact)
│   │   │   ├── MLmodel             # MLflow metadata
│   │   │   └── conda.yaml          # Environnement reproductible
│   │   └── v2.0/
│   │
│   └── ki67_counting/
│       └── v1.0/
│
├── mlruns/                         ← MLflow tracking (local ou remote)
│   ├── 0/                          # Experiment ID
│   │   ├── meta.yaml
│   │   └── <run_id>/               # Run spécifique
│   │       ├── params/
│   │       ├── metrics/
│   │       └── artifacts/
│   └── models/                     # MLflow Model Registry
│
└── pipelines/
    ├── training/                   ← Airflow DAGs
    │   ├── train_gleason.py
    │   └── train_ki67.py
    │
    └── retraining/                 ← Auto-retraining workflows
        └── feedback_retraining.py
```

**Commandes DVC typiques:**

```bash
# Initialiser DVC
dvc init

# Configurer remote storage (exemple MinIO)
dvc remote add -d minio s3://varuna-ml-data
dvc remote modify minio endpointurl http://minio.chu-ucl.local:9000

# Ajouter dataset au versioning
dvc add data/raw/prostate_slides_batch1
git add data/raw/prostate_slides_batch1.dvc
git commit -m "data: Add prostate slides batch 1"

# Push data vers remote
dvc push

# Récupérer version spécifique
git checkout v2.0-with-feedback
dvc pull  # Récupère données correspondant à ce commit
```

**Commandes MLflow typiques:**

```bash
# Start MLflow tracking server
mlflow server --host 0.0.0.0 --port 5000 \
  --backend-store-uri postgresql://mlflow:pass@db:5432/mlflow \
  --default-artifact-root s3://varuna-ml-models

# Log experiment (Python)
import mlflow

mlflow.set_experiment("gleason_grading")

with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_param("batch_size", 32)
    mlflow.log_metric("accuracy", 0.94)
    mlflow.log_metric("dice_score", 0.89)
    mlflow.pytorch.log_model(model, "model")

# Register model
mlflow.register_model("runs:/<run_id>/model", "gleason_grading")

# Promote to production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="gleason_grading",
    version=2,
    stage="Production"
)
```

### 3.3. Annotation Platform (Label Studio)

**Configuration Label Studio pour WSI:**

```yaml
# label_studio_config.yaml

title: "VarunaPoC Annotation Platform"

labeling_config: |
  <View>
    <Header value="Annotation de Lame Histologique"/>

    <!-- Image WSI avec zoom/pan -->
    <Image name="slide" value="$image" zoom="true" zoomControl="true"/>

    <!-- Annotations polygonales (tumeur, stroma, etc.) -->
    <PolygonLabels name="regions" toName="slide">
      <Label value="Tumeur" background="red"/>
      <Label value="Stroma" background="blue"/>
      <Label value="Nécrose" background="yellow"/>
      <Label value="Normal" background="green"/>
    </PolygonLabels>

    <!-- Classification Gleason (si prostate) -->
    <Choices name="gleason_primary" toName="slide" choice="single"
             visibleWhen="organ==prostate">
      <Choice value="3"/>
      <Choice value="4"/>
      <Choice value="5"/>
    </Choices>

    <Choices name="gleason_secondary" toName="slide" choice="single"
             visibleWhen="organ==prostate">
      <Choice value="3"/>
      <Choice value="4"/>
      <Choice value="5"/>
    </Choices>

    <!-- Ki-67 counting (si marker Ki-67) -->
    <KeyPointLabels name="ki67_positive" toName="slide"
                    visibleWhen="marker==Ki-67">
      <Label value="Positive" background="red"/>
      <Label value="Negative" background="blue"/>
    </KeyPointLabels>

    <!-- Commentaire pathologiste -->
    <TextArea name="notes" toName="slide"
              placeholder="Notes additionnelles..."/>

    <!-- Quality flags -->
    <Choices name="quality" toName="slide" choice="multiple">
      <Choice value="Artefact présent"/>
      <Choice value="Zone floue"/>
      <Choice value="Pli de tissu"/>
      <Choice value="Qualité excellente"/>
    </Choices>
  </View>

# ML-assisted labeling (pre-annotations)
ml_backend:
  url: "http://localhost:9090"  # VarunaPoC ML backend
  timeout: 30

# Storage
storage:
  type: "s3"
  path: "s3://varuna-annotations"

# User management
users:
  - username: "pathologist1"
    role: "annotator"
  - username: "pathologist2"
    role: "annotator"
  - username: "ml_engineer"
    role: "reviewer"
```

**Intégration avec VarunaPoC:**

```python
# backend/services/ml/label_studio_connector.py

from label_studio_sdk import Client

class LabelStudioConnector:
    """
    Connecteur avec Label Studio pour annotations.

    Workflow:
    1. VarunaPoC détecte nouvelle slide
    2. Crée task dans Label Studio
    3. Pathologiste annote via Label Studio UI
    4. Webhook notifie VarunaPoC quand terminé
    5. VarunaPoC importe annotations et met à jour dataset
    """

    def __init__(self, url: str, api_key: str):
        self.client = Client(url=url, api_key=api_key)

    def create_annotation_task(self, slide_id: str, slide_metadata: dict):
        """
        Crée task d'annotation pour une slide.

        Args:
            slide_id: ID unique slide
            slide_metadata: Tags, dimensions, etc.
        """
        project_id = self._get_or_create_project(slide_metadata["organ"])

        task = {
            "data": {
                "image": f"http://varuna-backend/api/slides/{slide_id}/overview",
                "slide_id": slide_id,
                "organ": slide_metadata.get("organ"),
                "stain": slide_metadata.get("stain"),
                "marker": slide_metadata.get("marker")
            },
            "meta": {
                "dimensions": slide_metadata["dimensions"],
                "vendor": slide_metadata["vendor"]
            }
        }

        self.client.create_task(project_id, task)

    def get_completed_annotations(self, project_id: int):
        """Récupère annotations complétées."""
        tasks = self.client.get_tasks(project_id)
        completed = [t for t in tasks if t.get("is_labeled")]
        return completed

    def export_annotations(self, project_id: int, export_format="JSON"):
        """
        Exporte annotations au format souhaité.

        Formats supportés: JSON, COCO, YOLO, Pascal VOC
        """
        return self.client.export_tasks(project_id, export_format)
```

---

## 4. Pipeline de Feedback Pathologistes

### 4.1. Types de Feedback

**4 niveaux de feedback:**

1. **Validation (Approve):** Prédiction ML correcte
2. **Correction (Correct):** Prédiction ML incorrecte, pathologiste corrige
3. **Rejet (Reject):** Prédiction ML inutilisable, annotation manuelle complète
4. **Annotation (Annotate):** Cas sans prédiction ML, annotation from scratch

### 4.2. Interface de Feedback

**Mockup UI (intégration frontend VarunaPoC):**

```javascript
// frontend/src/components/ml/FeedbackPanel.js

class FeedbackPanel {
    /**
     * Panel de feedback pathologiste intégré au viewer.
     *
     * Affiche:
     * - Prédiction ML + confiance
     * - Grad-CAM overlay (explainability)
     * - Boutons validation/correction
     * - Formulaire annotation si nécessaire
     */

    render(prediction) {
        return `
        <div class="feedback-panel">
            <h3>ML Prediction</h3>

            <!-- Prédiction -->
            <div class="prediction">
                <span class="label">${prediction.class}</span>
                <span class="confidence ${this.getConfidenceClass(prediction.confidence)}">
                    ${(prediction.confidence * 100).toFixed(1)}%
                </span>
            </div>

            <!-- Uncertainty (si disponible) -->
            ${prediction.uncertainty ? `
                <div class="uncertainty">
                    <label>Uncertainty:</label>
                    <progress value="${prediction.uncertainty}" max="1"></progress>
                    <span>${(prediction.uncertainty * 100).toFixed(1)}%</span>
                </div>
            ` : ''}

            <!-- Grad-CAM toggle -->
            <button onclick="toggleGradCAM()">
                ${this.gradcam_enabled ? 'Hide' : 'Show'} Explainability
            </button>

            <!-- Actions feedback -->
            <div class="feedback-actions">
                <button class="approve" onclick="handleFeedback('approve')">
                    ✓ Correct
                </button>
                <button class="correct" onclick="handleFeedback('correct')">
                    ✎ Correct Prediction
                </button>
                <button class="reject" onclick="handleFeedback('reject')">
                    ✗ Reject & Annotate
                </button>
            </div>

            <!-- Formulaire correction (si "Correct" cliqué) -->
            <div id="correction-form" style="display:none">
                <h4>Correct Prediction</h4>
                <select name="corrected_class">
                    <option value="gleason_3">Gleason 3</option>
                    <option value="gleason_4">Gleason 4</option>
                    <option value="gleason_5">Gleason 5</option>
                </select>
                <textarea name="notes" placeholder="Notes..."></textarea>
                <button onclick="submitCorrection()">Submit</button>
            </div>
        </div>
        `;
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.9) return 'high';
        if (confidence >= 0.75) return 'medium';
        return 'low';
    }
}

async function handleFeedback(action) {
    const feedback = {
        slide_id: currentSlideId,
        prediction_id: currentPrediction.id,
        action: action,  // "approve", "correct", "reject"
        timestamp: new Date().toISOString(),
        pathologist_id: getCurrentUser().id
    };

    if (action === "approve") {
        // Validation simple
        await fetch(`/api/ml/feedback`, {
            method: 'POST',
            body: JSON.stringify(feedback)
        });
        showNotification("Validation enregistrée");
    }
    else if (action === "correct") {
        // Afficher formulaire correction
        document.getElementById("correction-form").style.display = "block";
    }
    else if (action === "reject") {
        // Rediriger vers Label Studio pour annotation complète
        const labelStudioUrl = await createLabelStudioTask(currentSlideId);
        window.open(labelStudioUrl, '_blank');
    }
}

async function submitCorrection() {
    const correction = {
        slide_id: currentSlideId,
        prediction_id: currentPrediction.id,
        action: "correct",
        original_prediction: currentPrediction.class,
        corrected_prediction: document.querySelector('[name="corrected_class"]').value,
        notes: document.querySelector('[name="notes"]').value,
        timestamp: new Date().toISOString(),
        pathologist_id: getCurrentUser().id
    };

    await fetch(`/api/ml/feedback`, {
        method: 'POST',
        body: JSON.stringify(correction)
    });

    showNotification("Correction enregistrée - sera incluse au prochain ré-entraînement");
    document.getElementById("correction-form").style.display = "none";
}
```

### 4.3. Backend Feedback API

**Endpoints FastAPI:**

```python
# backend/routes/ml_feedback.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/ml", tags=["ml_feedback"])

class FeedbackCreate(BaseModel):
    """Schema feedback pathologiste."""
    slide_id: str
    prediction_id: str
    action: str  # "approve", "correct", "reject", "annotate"
    original_prediction: Optional[str] = None
    corrected_prediction: Optional[str] = None
    notes: Optional[str] = None
    pathologist_id: str
    timestamp: datetime

@router.post("/feedback")
async def record_feedback(feedback: FeedbackCreate):
    """
    Enregistre feedback pathologiste.

    Process:
    1. Valide feedback
    2. Stocke en DB
    3. Incrémente compteur pour auto-retraining
    4. Notifie système de monitoring

    Returns:
        {"status": "recorded", "feedback_id": str}
    """
    # Valider action
    valid_actions = ["approve", "correct", "reject", "annotate"]
    if feedback.action not in valid_actions:
        raise HTTPException(400, f"Invalid action. Must be one of {valid_actions}")

    # Stocker feedback
    feedback_id = await feedback_service.store_feedback(feedback.dict())

    # Incrémenter compteur retraining
    await retraining_monitor.increment_feedback_count(
        model_id=get_model_for_slide(feedback.slide_id),
        feedback_type=feedback.action
    )

    # Vérifier si seuil atteint pour retraining
    if await retraining_monitor.should_trigger_retraining():
        await trigger_retraining_pipeline()

    return {
        "status": "recorded",
        "feedback_id": feedback_id,
        "message": "Feedback enregistré avec succès"
    }

@router.get("/feedback/stats")
async def get_feedback_stats(model_id: Optional[str] = None):
    """
    Statistiques feedback pour monitoring.

    Returns:
        {
            "total_feedback": int,
            "approvals": int,
            "corrections": int,
            "rejections": int,
            "approval_rate": float,
            "pending_retraining": bool
        }
    """
    stats = await feedback_service.get_stats(model_id)
    return stats
```

### 4.4. Feedback Storage Schema

**Structure PostgreSQL:**

```sql
-- backend/database/schema_feedback.sql

CREATE TABLE ml_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slide_id VARCHAR(255) NOT NULL,
    prediction_id VARCHAR(255) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,

    -- Feedback details
    action VARCHAR(50) NOT NULL CHECK (action IN ('approve', 'correct', 'reject', 'annotate')),
    original_prediction JSONB,  -- Prédiction ML originale
    corrected_prediction JSONB,  -- Correction pathologiste (si action='correct')
    notes TEXT,

    -- Metadata
    pathologist_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'included_in_retraining', 'archived'

    -- Training inclusion tracking
    included_in_training_run VARCHAR(255),  -- MLflow run_id
    inclusion_timestamp TIMESTAMP,

    -- Indexes
    CONSTRAINT fk_slide FOREIGN KEY (slide_id) REFERENCES slides(id),
    CONSTRAINT fk_pathologist FOREIGN KEY (pathologist_id) REFERENCES users(id)
);

CREATE INDEX idx_feedback_slide ON ml_feedback(slide_id);
CREATE INDEX idx_feedback_model ON ml_feedback(model_id);
CREATE INDEX idx_feedback_action ON ml_feedback(action);
CREATE INDEX idx_feedback_status ON ml_feedback(processing_status);
CREATE INDEX idx_feedback_timestamp ON ml_feedback(timestamp DESC);

-- Vue stats feedback
CREATE VIEW feedback_stats AS
SELECT
    model_id,
    model_version,
    COUNT(*) as total_feedback,
    SUM(CASE WHEN action = 'approve' THEN 1 ELSE 0 END) as approvals,
    SUM(CASE WHEN action = 'correct' THEN 1 ELSE 0 END) as corrections,
    SUM(CASE WHEN action = 'reject' THEN 1 ELSE 0 END) as rejections,
    ROUND(100.0 * SUM(CASE WHEN action = 'approve' THEN 1 ELSE 0 END) / COUNT(*), 2) as approval_rate,
    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_retraining
FROM ml_feedback
GROUP BY model_id, model_version;
```

---

## 5. Architecture Technique

### 5.1. Diagramme Complet

```
┌────────────────────────────────────────────────────────────────────────┐
│                          VARUNA MLOps STACK                             │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│  FRONTEND       │
│  (Vite + JS)    │
│                 │
│  - Viewer       │
│  - Feedback UI  │
│  - GradCAM viz  │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI)                                                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐   │
│  │  Routes         │  │  Services        │  │  ML Services        │   │
│  │  - /slides      │  │  - slide_loader  │  │  - tag_extractor    │   │
│  │  - /ml/predict  │  │  - tile_server   │  │  - tag_router       │   │
│  │  - /ml/feedback │  │  - format_detect │  │  - model_inference  │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────────┘   │
└─────────┬───────────────────────┬────────────────────┬─────────────────┘
          │                       │                    │
          ↓                       ↓                    ↓
┌──────────────────┐   ┌──────────────────┐  ┌─────────────────────┐
│  PostgreSQL DB   │   │  Model Serving   │  │  Label Studio       │
│                  │   │  (TorchServe)    │  │  (Annotation)       │
│  - slides        │   │                  │  │                     │
│  - ml_feedback   │   │  - Gleason model │  │  - Projects         │
│  - ml_predictions│   │  - Ki-67 model   │  │  - Tasks            │
│  - users         │   │  - HER2 model    │  │  - Annotations      │
└──────────────────┘   └──────────────────┘  └─────────────────────┘
          │                       │                    │
          └───────────────────────┴────────────────────┘
                                  │
                                  ↓
                    ┌──────────────────────────────┐
                    │  MLOPS INFRASTRUCTURE        │
                    │                              │
                    │  ┌────────────────────────┐ │
                    │  │  MLflow Tracking       │ │
                    │  │  - Experiments         │ │
                    │  │  - Runs                │ │
                    │  │  - Model Registry      │ │
                    │  └────────────────────────┘ │
                    │                              │
                    │  ┌────────────────────────┐ │
                    │  │  DVC                   │ │
                    │  │  - Data versioning     │ │
                    │  │  - Dataset tracking    │ │
                    │  │  - Remote storage      │ │
                    │  └────────────────────────┘ │
                    │                              │
                    │  ┌────────────────────────┐ │
                    │  │  Airflow / Prefect     │ │
                    │  │  - Training pipelines  │ │
                    │  │  - Retraining DAGs     │ │
                    │  │  - Data validation     │ │
                    │  └────────────────────────┘ │
                    │                              │
                    │  ┌────────────────────────┐ │
                    │  │  Evidently AI          │ │
                    │  │  - Drift detection     │ │
                    │  │  - Model monitoring    │ │
                    │  │  - Data quality        │ │
                    │  └────────────────────────┘ │
                    └──────────────────────────────┘
                                  │
                                  ↓
                    ┌──────────────────────────────┐
                    │  STORAGE                     │
                    │                              │
                    │  ┌────────────────────────┐ │
                    │  │  S3 / MinIO            │ │
                    │  │  - Raw slides          │ │
                    │  │  - Annotations         │ │
                    │  │  - Model artifacts     │ │
                    │  │  - Feedback data       │ │
                    │  └────────────────────────┘ │
                    └──────────────────────────────┘
```

### 5.2. Continuous Learning Workflow

**Automatisation complète:**

```python
# pipelines/retraining/feedback_retraining_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'varuna-ml',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email': ['ml-team@chu-ucl.be'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'feedback_retraining_gleason',
    default_args=default_args,
    description='Auto-retraining triggered by pathologist feedback',
    schedule_interval=None,  # Trigger manuel ou par seuil
    catchup=False,
)

# Task 1: Check if retraining needed
def check_retraining_threshold(**context):
    """
    Vérifie si seuil de feedback atteint.

    Critères:
    - Au moins 100 nouvelles corrections
    - OU approval rate < 85%
    - OU 30 jours depuis dernier retraining
    """
    from services.ml.retraining_monitor import RetrainingMonitor

    monitor = RetrainingMonitor(model_id="gleason_grading_v2")
    should_retrain = monitor.check_threshold()

    if not should_retrain:
        raise AirflowSkipException("Retraining threshold not reached")

    return should_retrain

check_threshold = PythonOperator(
    task_id='check_threshold',
    python_callable=check_retraining_threshold,
    dag=dag,
)

# Task 2: Prepare dataset
def prepare_training_dataset(**context):
    """
    Prépare dataset enrichi avec feedback.

    Process:
    1. Récupère feedback pending
    2. Merge avec dataset existant
    3. Valide qualité données
    4. Version avec DVC
    """
    from services.ml.dataset_builder import DatasetBuilder

    builder = DatasetBuilder(model_id="gleason_grading_v2")

    # Récupérer feedback
    feedback_data = builder.fetch_pending_feedback()

    # Merger avec dataset existant
    merged_dataset = builder.merge_with_existing(feedback_data)

    # Valider qualité
    validation_report = builder.validate_quality(merged_dataset)
    if not validation_report["is_valid"]:
        raise ValueError(f"Dataset quality check failed: {validation_report['errors']}")

    # Versionner avec DVC
    dataset_path = builder.save_dataset(merged_dataset)
    dvc_version = builder.version_with_dvc(dataset_path)

    # Pousser metadata vers MLflow
    mlflow.log_param("dataset_version", dvc_version)
    mlflow.log_param("dataset_size", len(merged_dataset))
    mlflow.log_param("feedback_count", len(feedback_data))

    return dataset_path

prepare_dataset = PythonOperator(
    task_id='prepare_dataset',
    python_callable=prepare_training_dataset,
    dag=dag,
)

# Task 3: Train model
def train_model(**context):
    """
    Entraîne nouveau modèle.

    Configuration:
    - Même architecture que production
    - Hyperparams depuis MLflow (best run)
    - Early stopping sur validation
    - Checkpointing automatique
    """
    import mlflow
    from training.gleason_trainer import GleasonTrainer

    dataset_path = context['task_instance'].xcom_pull(task_ids='prepare_dataset')

    # Setup MLflow
    mlflow.set_experiment("gleason_grading_retraining")

    with mlflow.start_run():
        trainer = GleasonTrainer(
            dataset_path=dataset_path,
            config="config/gleason_training.yaml"
        )

        # Training avec logging automatique
        trainer.train()

        # Évaluation
        metrics = trainer.evaluate()

        # Log metrics
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.pytorch.log_model(trainer.model, "model")

        run_id = mlflow.active_run().info.run_id
        return run_id

train_model_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag,
)

# Task 4: Validate model
def validate_model(**context):
    """
    Valide nouveau modèle vs production.

    Critères:
    - Accuracy >= production model
    - Dice score >= production model
    - Inter-annotator agreement >= 0.8
    - Pas de régression sur test set
    """
    from services.ml.model_validator import ModelValidator

    run_id = context['task_instance'].xcom_pull(task_ids='train_model')

    validator = ModelValidator()

    # Charger nouveau modèle
    new_model = mlflow.pytorch.load_model(f"runs:/{run_id}/model")

    # Charger modèle production
    production_model = mlflow.pytorch.load_model("models:/gleason_grading/Production")

    # Comparer performances
    comparison = validator.compare_models(
        new_model=new_model,
        production_model=production_model,
        test_dataset="data/test/gleason_test.dvc"
    )

    # Décision déploiement
    if not comparison["is_better"]:
        raise ValueError(f"New model not better than production: {comparison}")

    mlflow.log_metrics(comparison["metrics"])

    return comparison

validate_model_task = PythonOperator(
    task_id='validate_model',
    python_callable=validate_model,
    dag=dag,
)

# Task 5: A/B test deployment
def deploy_ab_test(**context):
    """
    Déploie en A/B test (20% traffic).

    Process:
    1. Register model version
    2. Deploy avec 20% traffic
    3. Monitor pendant 48h
    4. Auto-promote si succès
    """
    from services.ml.model_deployer import ModelDeployer

    run_id = context['task_instance'].xcom_pull(task_ids='train_model')

    deployer = ModelDeployer()

    # Register new version
    model_version = mlflow.register_model(
        f"runs:/{run_id}/model",
        "gleason_grading"
    )

    # Deploy A/B test
    deployer.deploy_ab_test(
        model_name="gleason_grading",
        new_version=model_version.version,
        traffic_split={"production": 0.8, "challenger": 0.2}
    )

    # Schedule monitoring
    deployer.schedule_ab_monitoring(
        duration_hours=48,
        auto_promote_threshold=0.95  # 95% approval rate
    )

    return model_version.version

deploy_ab_task = PythonOperator(
    task_id='deploy_ab_test',
    python_callable=deploy_ab_test,
    dag=dag,
)

# Task 6: Mark feedback as processed
def mark_feedback_processed(**context):
    """Marque feedback comme inclus dans training."""
    from services.ml.feedback_service import FeedbackService

    run_id = context['task_instance'].xcom_pull(task_ids='train_model')

    feedback_service = FeedbackService()
    feedback_service.mark_as_processed(
        model_id="gleason_grading_v2",
        training_run_id=run_id
    )

mark_processed = PythonOperator(
    task_id='mark_feedback_processed',
    python_callable=mark_feedback_processed,
    dag=dag,
)

# Define task dependencies
check_threshold >> prepare_dataset >> train_model_task >> validate_model_task >> deploy_ab_task >> mark_processed
```

---

## 6. Structures de Données

### 6.1. Database Schema Complet

```sql
-- backend/database/schema_ml.sql

-- ============================================================================
-- SLIDES METADATA (avec tags ML)
-- ============================================================================

CREATE TABLE slides_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slide_id VARCHAR(255) UNIQUE NOT NULL,  -- MD5 hash du path
    slide_path TEXT NOT NULL,
    slide_name VARCHAR(500),
    format VARCHAR(100),
    vendor VARCHAR(100),

    -- Dimensions
    width INT,
    height INT,
    level_count INT,

    -- Tags ML (auto-détectés ou manuels)
    organ VARCHAR(100),
    stain VARCHAR(100),
    marker VARCHAR(100),
    task VARCHAR(100),
    tags_source VARCHAR(50),  -- 'dicom', 'properties', 'filename', 'ml_inference', 'manual'
    tags_confidence FLOAT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP,

    CONSTRAINT chk_tags_source CHECK (tags_source IN ('dicom', 'properties', 'filename', 'ml_inference', 'manual'))
);

CREATE INDEX idx_slides_metadata_slide_id ON slides_metadata(slide_id);
CREATE INDEX idx_slides_metadata_organ ON slides_metadata(organ);
CREATE INDEX idx_slides_metadata_stain ON slides_metadata(stain);
CREATE INDEX idx_slides_metadata_marker ON slides_metadata(marker);

-- ============================================================================
-- ML PREDICTIONS
-- ============================================================================

CREATE TABLE ml_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id VARCHAR(255) UNIQUE NOT NULL,

    -- Slide reference
    slide_id VARCHAR(255) NOT NULL,

    -- Model info
    model_id VARCHAR(255) NOT NULL,
    model_name VARCHAR(255),
    model_version VARCHAR(50),

    -- Prediction details
    prediction_class VARCHAR(255),
    prediction_proba JSONB,  -- {"class1": 0.85, "class2": 0.10, ...}
    confidence_score FLOAT,
    uncertainty_score FLOAT,  -- Monte Carlo Dropout variance

    -- Region of interest (si applicable)
    roi_coordinates JSONB,  -- {"x": 1000, "y": 2000, "width": 500, "height": 500}

    -- Explainability
    gradcam_path TEXT,  -- Chemin vers heatmap GradCAM
    shap_values JSONB,  -- SHAP values (si applicable)

    -- Metadata
    inference_time_ms FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Status tracking
    validation_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'corrected', 'rejected'

    CONSTRAINT fk_slide FOREIGN KEY (slide_id) REFERENCES slides_metadata(slide_id),
    CONSTRAINT chk_validation_status CHECK (validation_status IN ('pending', 'approved', 'corrected', 'rejected'))
);

CREATE INDEX idx_predictions_slide ON ml_predictions(slide_id);
CREATE INDEX idx_predictions_model ON ml_predictions(model_id);
CREATE INDEX idx_predictions_status ON ml_predictions(validation_status);
CREATE INDEX idx_predictions_timestamp ON ml_predictions(timestamp DESC);

-- ============================================================================
-- ML FEEDBACK (voir section 4.4 ci-dessus)
-- ============================================================================
-- Déjà définie précédemment

-- ============================================================================
-- MODEL REGISTRY (sync avec MLflow)
-- ============================================================================

CREATE TABLE model_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id VARCHAR(255) UNIQUE NOT NULL,
    model_name VARCHAR(255) NOT NULL,

    -- Versioning
    version VARCHAR(50) NOT NULL,
    stage VARCHAR(50) DEFAULT 'staging',  -- 'staging', 'production', 'archived'

    -- Artifacts
    mlflow_run_id VARCHAR(255),
    artifact_uri TEXT,

    -- Performance metrics
    metrics JSONB,  -- {"accuracy": 0.94, "dice": 0.89, ...}

    -- Required tags
    required_tags JSONB,  -- {"organ": "prostate", "stain": "H&E"}

    -- Deployment
    deployment_date TIMESTAMP,
    traffic_percentage INT DEFAULT 0,  -- Pour A/B testing

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_stage CHECK (stage IN ('staging', 'production', 'archived')),
    CONSTRAINT chk_traffic CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100)
);

CREATE INDEX idx_model_registry_model_id ON model_registry(model_id);
CREATE INDEX idx_model_registry_stage ON model_registry(stage);

-- ============================================================================
-- RETRAINING MONITORING
-- ============================================================================

CREATE TABLE retraining_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    model_id VARCHAR(255) NOT NULL,

    -- Trigger info
    trigger_type VARCHAR(50),  -- 'feedback_threshold', 'scheduled', 'manual'
    trigger_timestamp TIMESTAMP DEFAULT NOW(),

    -- Dataset info
    dataset_version VARCHAR(255),  -- DVC version hash
    dataset_size INT,
    feedback_count INT,

    -- Training info
    mlflow_run_id VARCHAR(255),
    training_duration_seconds INT,

    -- Results
    validation_metrics JSONB,
    comparison_with_production JSONB,

    -- Deployment
    deployment_status VARCHAR(50),  -- 'validated', 'deployed', 'failed', 'rollback'
    deployment_timestamp TIMESTAMP,

    -- Metadata
    notes TEXT,

    CONSTRAINT fk_model FOREIGN KEY (model_id) REFERENCES model_registry(model_id),
    CONSTRAINT chk_trigger_type CHECK (trigger_type IN ('feedback_threshold', 'scheduled', 'manual')),
    CONSTRAINT chk_deployment_status CHECK (deployment_status IN ('validated', 'deployed', 'failed', 'rollback'))
);

CREATE INDEX idx_retraining_logs_model ON retraining_logs(model_id);
CREATE INDEX idx_retraining_logs_timestamp ON retraining_logs(trigger_timestamp DESC);

-- ============================================================================
-- DRIFT MONITORING
-- ============================================================================

CREATE TABLE drift_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    model_id VARCHAR(255) NOT NULL,

    -- Drift detection
    check_timestamp TIMESTAMP DEFAULT NOW(),
    drift_type VARCHAR(50),  -- 'data_drift', 'prediction_drift', 'performance_drift'

    -- Metrics
    drift_score FLOAT,  -- PSI, KS statistic, etc.
    drift_threshold FLOAT,
    drift_detected BOOLEAN,

    -- Details
    drift_details JSONB,  -- Détails par feature/classe

    -- Actions
    alert_sent BOOLEAN DEFAULT FALSE,
    retraining_triggered BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_model FOREIGN KEY (model_id) REFERENCES model_registry(model_id),
    CONSTRAINT chk_drift_type CHECK (drift_type IN ('data_drift', 'prediction_drift', 'performance_drift'))
);

CREATE INDEX idx_drift_model ON drift_monitoring(model_id);
CREATE INDEX idx_drift_timestamp ON drift_monitoring(check_timestamp DESC);
CREATE INDEX idx_drift_detected ON drift_monitoring(drift_detected);

-- ============================================================================
-- VIEWS UTILES
-- ============================================================================

-- Vue: Statistics par modèle
CREATE VIEW model_performance_summary AS
SELECT
    mr.model_id,
    mr.model_name,
    mr.version,
    mr.stage,
    COUNT(DISTINCT mp.id) as total_predictions,
    SUM(CASE WHEN mp.validation_status = 'approved' THEN 1 ELSE 0 END) as approvals,
    SUM(CASE WHEN mp.validation_status = 'corrected' THEN 1 ELSE 0 END) as corrections,
    SUM(CASE WHEN mp.validation_status = 'rejected' THEN 1 ELSE 0 END) as rejections,
    ROUND(100.0 * SUM(CASE WHEN mp.validation_status = 'approved' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(DISTINCT mp.id), 0), 2) as approval_rate,
    AVG(mp.confidence_score) as avg_confidence,
    AVG(mp.uncertainty_score) as avg_uncertainty
FROM model_registry mr
LEFT JOIN ml_predictions mp ON mr.model_id = mp.model_id
GROUP BY mr.model_id, mr.model_name, mr.version, mr.stage;

-- Vue: Pending feedback count par modèle
CREATE VIEW pending_feedback_count AS
SELECT
    model_id,
    COUNT(*) as pending_count,
    MAX(timestamp) as last_feedback_date
FROM ml_feedback
WHERE processing_status = 'pending'
GROUP BY model_id;
```

### 6.2. Configuration Files

**DVC Configuration:**

```yaml
# .dvc/config

[core]
    remote = minio
    autostage = true

['remote "minio"']
    url = s3://varuna-ml-data
    endpointurl = http://minio.chu-ucl.local:9000
    access_key_id = varuna-ml-access-key
    secret_access_key = ${MINIO_SECRET_KEY}

['remote "backup"']
    url = s3://varuna-ml-data-backup
    endpointurl = http://backup.chu-ucl.local:9000
```

**MLflow Configuration:**

```yaml
# backend/config/mlflow_config.yaml

tracking_uri: "postgresql://mlflow:password@db.chu-ucl.local:5432/mlflow"
artifact_root: "s3://varuna-ml-models"

default_experiment_name: "varuna_pathology_ml"

model_registry:
  backend_store_uri: "postgresql://mlflow:password@db.chu-ucl.local:5432/mlflow"

autolog:
  frameworks:
    - pytorch
    - tensorflow
  metrics:
    - accuracy
    - precision
    - recall
    - f1_score
    - auc_roc
    - dice_coefficient

tags:
  project: "VarunaPoC"
  environment: "production"
  team: "ML-Pathology"
```

---

## 7. Intégration avec VarunaPoC Existant

### 7.1. Points d'Intégration

**Backend (FastAPI):**

```
backend/
├── routes/
│   ├── slides.py (EXISTANT - pas de modification)
│   └── ml_inference.py (NOUVEAU)
│   └── ml_feedback.py (NOUVEAU)
│
├── services/
│   ├── slide_loader.py (EXISTANT - pas de modification)
│   ├── tile_server.py (EXISTANT - pas de modification)
│   │
│   └── ml/  (NOUVEAU)
│       ├── tag_extractor.py
│       ├── tag_router.py
│       ├── model_inference.py
│       ├── feedback_service.py
│       ├── dataset_builder.py
│       ├── retraining_monitor.py
│       └── drift_detector.py
│
├── models/  (NOUVEAU)
│   └── (MLflow artifacts chargés dynamiquement)
│
└── config/  (NOUVEAU)
    ├── ml_routes.yaml
    └── mlflow_config.yaml
```

**Frontend (Vite + JS):**

```
frontend/src/
├── components/
│   ├── Viewer.js (EXISTANT - modification mineure)
│   │
│   └── ml/  (NOUVEAU)
│       ├── FeedbackPanel.js
│       ├── PredictionOverlay.js
│       └── GradCAMViewer.js
│
└── services/
    └── mlApi.js (NOUVEAU - API calls ML)
```

### 7.2. Migration Progressive (Phases)

**Phase 3.1: Infrastructure MLOps (2-3 mois)**
- [ ] Setup MLflow tracking server
- [ ] Setup DVC avec remote storage
- [ ] Créer schema DB (slides_metadata, ml_predictions, ml_feedback)
- [ ] Implémenter tag extraction basique (filename + properties)
- [ ] Configurer Label Studio

**Phase 3.2: Tag System & Routing (1-2 mois)**
- [ ] Implémenter TagExtractor complet
- [ ] Implémenter TagRouter
- [ ] Créer configuration ml_routes.yaml
- [ ] Tester avec 1 modèle fallback générique

**Phase 3.3: Feedback Pipeline (2 mois)**
- [ ] Créer FeedbackPanel UI
- [ ] Implémenter /api/ml/feedback endpoint
- [ ] Connecter avec Label Studio
- [ ] Dashboard feedback stats

**Phase 3.4: Continuous Learning (3-4 mois)**
- [ ] Créer pipeline Airflow retraining
- [ ] Implémenter DatasetBuilder avec DVC
- [ ] A/B testing infrastructure
- [ ] Monitoring drift (Evidently AI)

**Phase 3.5: Production Models (ongoing)**
- [ ] Entraîner Gleason grading model
- [ ] Entraîner Ki-67 counting model
- [ ] Entraîner HER2 scoring model
- [ ] Etc.

### 7.3. Endpoints API Nouveaux

```python
# backend/routes/ml_inference.py

@router.post("/ml/predict", tags=["ml_inference"])
async def predict(slide_id: str):
    """
    Inférence ML sur une lame.

    Process:
    1. Extrait tags (organ, stain, marker)
    2. Route vers modèle approprié
    3. Exécute inférence
    4. Calcule uncertainty + GradCAM
    5. Stocke prédiction en DB

    Returns:
        {
            "prediction_id": str,
            "model_used": str,
            "prediction_class": str,
            "confidence": float,
            "uncertainty": float,
            "gradcam_url": str
        }
    """

@router.get("/ml/models", tags=["ml_inference"])
async def list_models():
    """
    Liste modèles disponibles.

    Returns:
        [
            {
                "model_id": str,
                "model_name": str,
                "version": str,
                "stage": str,
                "required_tags": {...},
                "metrics": {...}
            }
        ]
    """

@router.get("/ml/predictions/{slide_id}", tags=["ml_inference"])
async def get_predictions(slide_id: str):
    """
    Récupère prédictions pour une lame.

    Returns:
        [
            {
                "prediction_id": str,
                "model_name": str,
                "prediction_class": str,
                "confidence": float,
                "validation_status": str,
                "timestamp": datetime
            }
        ]
    """
```

---

## 8. Roadmap d'Implémentation

### 8.1. Timeline Complète (12-18 mois)

```
Phase 3.1: Infrastructure MLOps (Mois 1-3)
├── Semaine 1-2: Setup MLflow + DVC + MinIO
├── Semaine 3-4: Schema DB + migrations
├── Semaine 5-6: Label Studio setup + intégration
├── Semaine 7-8: Tag extraction basique
├── Semaine 9-10: Tests infrastructure
├── Semaine 11-12: Documentation + formation équipe

Phase 3.2: Tag System & Routing (Mois 4-5)
├── Semaine 13-14: Implémenter TagExtractor complet
├── Semaine 15-16: Implémenter TagRouter
├── Semaine 17-18: Configuration ml_routes.yaml
├── Semaine 19-20: Tests routing avec modèle fallback

Phase 3.3: Feedback Pipeline (Mois 6-7)
├── Semaine 21-22: FeedbackPanel UI
├── Semaine 23-24: Backend feedback API
├── Semaine 25-26: Intégration Label Studio
├── Semaine 27-28: Dashboard feedback + tests

Phase 3.4: Continuous Learning (Mois 8-11)
├── Semaine 29-32: Pipeline Airflow retraining
├── Semaine 33-36: DatasetBuilder + versioning DVC
├── Semaine 37-40: A/B testing infrastructure
├── Semaine 41-44: Monitoring drift (Evidently AI)

Phase 3.5: Production Models (Mois 12-18)
├── Mois 12-13: Gleason grading model (prostate)
├── Mois 14-15: Ki-67 counting model (sein)
├── Mois 16-17: HER2 scoring model (sein)
├── Mois 18: Généralisation autres organes/markers
```

### 8.2. Milestones Clés

**Milestone 1 (Fin Mois 3): "MLOps Foundation Ready"**
- [ ] MLflow tracking opérationnel
- [ ] DVC data versioning fonctionnel
- [ ] Label Studio configuré
- [ ] 1 dataset de test versionné

**Milestone 2 (Fin Mois 5): "Intelligent Routing Operational"**
- [ ] Tags auto-détectés pour 80% des slides
- [ ] Router dirige vers modèles appropriés
- [ ] 1 modèle fallback déployé

**Milestone 3 (Fin Mois 7): "Feedback Loop Complete"**
- [ ] Pathologistes peuvent valider/corriger
- [ ] Feedback stocké et versionné
- [ ] Dashboard monitoring feedback

**Milestone 4 (Fin Mois 11): "Continuous Learning Active"**
- [ ] Re-entraînement automatisé fonctionnel
- [ ] A/B testing déployé
- [ ] Drift detection en production

**Milestone 5 (Fin Mois 18): "Multi-Model Production"**
- [ ] 3+ modèles spécialisés en production
- [ ] Approval rate > 85% global
- [ ] Temps d'analyse réduit de 50%

---

## 9. Références & Outils

### 9.1. Outils MLOps (Officiels)

**Versioning & Tracking:**
- **MLflow:** https://mlflow.org/docs/latest/index.html
  - Tracking: https://mlflow.org/docs/latest/tracking.html
  - Model Registry: https://mlflow.org/docs/latest/model-registry.html
  - Projects: https://mlflow.org/docs/latest/projects.html

- **DVC:** https://dvc.org/doc
  - Get Started: https://dvc.org/doc/start
  - Data Versioning: https://dvc.org/doc/use-cases/versioning-data-and-model-files
  - Pipelines: https://dvc.org/doc/user-guide/pipelines

**Annotation:**
- **Label Studio:** https://labelstud.io/guide/
  - WSI Support: https://labelstud.io/templates/image_wsi.html
  - ML Backend: https://labelstud.io/guide/ml.html
  - Export Formats: https://labelstud.io/guide/export.html

**Monitoring:**
- **Evidently AI:** https://docs.evidentlyai.com/
  - Data Drift: https://docs.evidentlyai.com/user-guide/tests-and-reports/data-drift
  - Model Performance: https://docs.evidentlyai.com/user-guide/tests-and-reports/classification-performance

**Orchestration:**
- **Apache Airflow:** https://airflow.apache.org/docs/
  - DAGs: https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html
  - Best Practices: https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html

- **Prefect:** https://docs.prefect.io/
  - Flows: https://docs.prefect.io/concepts/flows/
  - Tasks: https://docs.prefect.io/concepts/tasks/

**Model Serving:**
- **TorchServe:** https://pytorch.org/serve/
  - Getting Started: https://pytorch.org/serve/getting_started.html
  - Model Archiver: https://github.com/pytorch/serve/tree/master/model-archiver

- **FastAPI:** https://fastapi.tiangolo.com/ (déjà utilisé)

### 9.2. Papers de Référence

**MLOps & Continuous Learning:**
- Sculley et al. (2023): "Hidden Technical Debt in Machine Learning Systems"
  - https://papers.nips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html

- Lwakatare et al. (2020): "DevOps for AI – Challenges in Development of AI-enabled Applications"
  - https://arxiv.org/abs/2001.06848

**Medical AI:**
- Pantanowitz et al. (2024): "Annotation Quality in Digital Pathology"
- Komura & Ishikawa (2024): "Machine Learning Approaches for Pathologic Diagnosis"
  - https://www.nature.com/articles/s41467-019-13471-3

**Explainable AI:**
- Selvaraju et al. (2017): "Grad-CAM: Visual Explanations from Deep Networks"
  - https://arxiv.org/abs/1610.02391

- Lundberg & Lee (2017): "A Unified Approach to Interpreting Model Predictions" (SHAP)
  - https://arxiv.org/abs/1705.07874

**Active Learning:**
- Settles (2009): "Active Learning Literature Survey"
  - https://burrsettles.com/pub/settles.activelearning.pdf

- Budd et al. (2021): "A Survey on Active Learning and Human-in-the-Loop Deep Learning"
  - https://arxiv.org/abs/2108.00941

**Drift Detection:**
- Rabanser et al. (2019): "Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift"
  - https://arxiv.org/abs/1810.11953

- Gama et al. (2014): "A Survey on Concept Drift Adaptation"
  - https://dl.acm.org/doi/10.1145/2523813

### 9.3. Datasets & Benchmarks

**Public Pathology Datasets:**
- **Camelyon16/17:** Breast cancer metastases detection
  - https://camelyon17.grand-challenge.org/

- **PANDA Challenge:** Prostate cancer Gleason grading
  - https://www.kaggle.com/c/prostate-cancer-grade-assessment

- **TCGA:** The Cancer Genome Atlas (multi-organ)
  - https://www.cancer.gov/about-nci/organization/ccg/research/structural-genomics/tcga

- **PatchCamelyon:** Benchmark dataset (327k patches)
  - https://github.com/basveeling/pcam

**Frameworks:**
- **PathML:** Computational pathology toolkit
  - https://github.com/Dana-Farber-AIOS/pathml

- **HistomicsTK:** Digital pathology toolkit
  - https://github.com/DigitalSlideArchive/HistomicsTK

- **CLAM:** Clustering-Constrained Attention Multiple Instance Learning
  - https://github.com/mahmoodlab/CLAM

### 9.4. Community & Forums

- **Grand Challenge:** Medical imaging competitions
  - https://grand-challenge.org/

- **MLOps Community:** Best practices, tools, discussions
  - https://mlops.community/

- **Papers with Code:** ML benchmarks + implementations
  - https://paperswithcode.com/area/medical

---

## Conclusion

Cette architecture MLOps transforme VarunaPoC en plateforme d'apprentissage continu, où chaque validation/correction de pathologiste améliore automatiquement les modèles ML. Le système de routage par tags garantit que chaque slide est analysée par le modèle le plus approprié, tandis que le pipeline de feedback ferme la boucle d'amélioration continue.

**Principes clés à retenir:**

1. **Quality-First:** Jamais de prédiction sans confiance + explainability
2. **Human-in-the-Loop:** Pathologiste garde le contrôle, ML assiste
3. **Automation:** Versioning, training, deployment automatisés
4. **Pragmatisme:** Utiliser outils éprouvés (MLflow, DVC, Label Studio)
5. **Incremental:** Déployer progressivement, valider chaque phase

**Prochaines étapes:**

1. Valider cette architecture avec équipe médicale CHU UCL Namur
2. Prioriser modèles selon besoins cliniques (Gleason? Ki-67? HER2?)
3. Commencer Phase 3.1 (Infrastructure MLOps)
4. Former équipe sur MLflow + DVC + Label Studio

---

**Version:** 1.0
**Dernière mise à jour:** 2025-12-31
**Contact:** ML Architect (VarunaPoC)
**License:** Propriétaire CHU UCL Namur
