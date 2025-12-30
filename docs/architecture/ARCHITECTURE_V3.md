# ARCHITECTURE V3 - Plateforme WSI Modulaire et MLOps-Ready

**Version:** 3.0.0
**Date:** 2025-12-31
**Statut:** Architecture cible pour TFE 2025-2026

---

## Table des Matières

1. [Vision et Objectifs](#1-vision-et-objectifs)
2. [Analyse de l'Architecture Actuelle](#2-analyse-de-larchitecture-actuelle)
3. [Architecture Cible V3](#3-architecture-cible-v3)
4. [Plan de Migration](#4-plan-de-migration)
5. [Roadmap Détaillée](#5-roadmap-détaillée)
6. [Références et Standards](#6-références-et-standards)

---

## 1. Vision et Objectifs

### 1.1 Transition de PoC à Plateforme

**De:**
- Viewer WSI simple (navigation, tuiles)
- Monolithique (viewer + tile server couplés)
- Statique (aucune IA, aucun feedback loop)

**Vers:**
- Plateforme modulaire multi-composants
- MLOps-ready (pipelines ML, feedback continu, versioning modèles)
- Évolutive (plugins, tags, collaboration temps réel)

### 1.2 Objectifs Principaux du TFE

| Objectif | Description | Priorité |
|----------|-------------|----------|
| **Modularité** | Isolation des modules (viewer, ML, PACS, storage) | P0 |
| **Routage par tags** | Envoyer lames aux modèles IA appropriés | P0 |
| **MLOps** | Capture feedback, ré-entraînement, versioning | P0 |
| **Conformité** | RGPD, MDR, AI Act | P0 |
| **Intégration PACS** | Plugin Telemis (query/retrieve DICOM) | P1 |
| **Collaboration** | Co-visualisation temps réel | P2 |

### 1.3 Angles Morts Résolus

| Angle Mort Actuel | Solution V3 |
|-------------------|-------------|
| IA figée (modèles statiques) | Pipeline MLOps avec ré-entraînement continu |
| Corrections perdues | Capture feedback pathologistes → ré-annotation → ré-entraînement |
| Résultats binaires | Cartographie de confiance (heatmaps, probabilités) |
| Collaboration limitée | Co-visualisation synchronisée (WebRTC/WebSocket) |
| Vendor lock-in | Architecture ouverte (12 formats supportés) |

---

## 2. Analyse de l'Architecture Actuelle

### 2.1 Structure Existante (Phase 1.7)

#### Backend (`backend/`)

```
backend/
├── main.py                     # FastAPI app entry point
├── routes/
│   └── slides.py               # API endpoints (navigation, visualization)
├── services/
│   ├── format_detector.py      # Détection multi-format OpenSlide
│   ├── tile_server.py          # Streaming tuiles DZI
│   ├── slide_loader.py         # Chargement métadonnées
│   ├── slide_scanner.py        # Scan récursif /Slides
│   └── folder_browser.py       # Navigation hiérarchique
├── utils/
│   └── (vide pour l'instant)
├── config_openslide.py         # Configuration DLL OpenSlide
└── monitoring.py               # Prometheus metrics (optionnel)
```

**Forces:**
- Service layer bien séparé (routes → services)
- Détection intelligente de 12 formats
- Cache slides (max 5 simultanés)
- Metrics Prometheus intégrées

**Faiblesses:**
- Monolithique (viewer + tile server + format detection dans un seul service)
- Pas de séparation storage/compute
- Aucune abstraction pour injection de ML
- Configuration hardcodée (pas de feature flags)

#### Frontend (`frontend/src/`)

```
frontend/src/
├── main.js                     # App entry point
├── components/
│   ├── Viewer.js               # Legacy viewer wrapper
│   ├── FolderBrowser.js        # Explorateur hiérarchique
│   ├── CompareLayout.js        # Multi-viewer side-by-side
│   ├── ViewerPanel.js          # Panel viewer individuel
│   └── SyncControls.js         # Contrôles synchronisation
├── viewers/
│   ├── ViewerManager.js        # Singleton gestionnaire viewers
│   ├── ViewerFactory.js        # Factory pattern pour création
│   ├── ViewerInstance.js       # Instance viewer avec lifecycle
│   └── SyncController.js       # Synchronisation multi-viewers
├── services/
│   └── ApiService.js           # API client (singleton)
├── core/
│   ├── EventBus.js             # Observer pattern (pub/sub)
│   └── Constants.js            # Constantes globales
└── utils/
    ├── api.js                  # Fetch helpers
    └── coordinates.js          # Transformations coordonnées OSD↔OpenSlide
```

**Forces:**
- Architecture modulaire (Factory, Singleton, Observer patterns)
- Multi-viewer avec sync optionnelle
- EventBus découplé
- Vanilla JS (pas de framework lourd)

**Faiblesses:**
- Pas de state management global (Redux/MobX)
- Aucune abstraction pour annotations/ML overlays
- Pas de WebSocket (seulement HTTP polling)
- Collaboration temps réel impossible (architecture unidirectionnelle)

### 2.2 Points de Couplage Critiques

| Couplage | Impact | Priorité Refactoring |
|----------|--------|----------------------|
| `tile_server.py` + OpenSlide direct | Impossible d'injecter ML sans modifier tile server | P0 |
| Routes monolithiques | Ajout endpoints ML = pollution routes/slides.py | P0 |
| Pas d'abstraction storage | Impossibilité de switch filesystem → S3/PACS | P1 |
| Configuration hardcodée | Pas de feature flags pour A/B testing modèles | P1 |
| Synchronisation OSD manuelle | Difficile d'ajouter annotations synchronisées | P2 |

### 2.3 Dettes Techniques Identifiées

1. **Pas de tests automatisés** (backend/frontend)
2. **Pas de versioning d'API** (breaking changes = migration manuelle)
3. **Logs non structurés** (impossible d'exploiter avec ELK/Grafana)
4. **Aucune telemetry** (pas de tracing distribué)
5. **Configuration mixée avec code** (pas de 12-factor app)

---

## 3. Architecture Cible V3

### 3.1 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Vanilla JS)                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  UI Layer (components/)                                          │  │
│  │  - Viewer (multi-panel, annotations, heatmaps)                   │  │
│  │  - FolderBrowser (navigation DICOM/filesystem)                   │  │
│  │  - AnnotationTool (drawing, labels, corrections)                 │  │
│  │  - MLDashboard (résultats, confiance, feedback)                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  State Management (state/)                                       │  │
│  │  - ViewerStore (slides, zoom, viewport)                          │  │
│  │  - AnnotationStore (annotations, edits, corrections)             │  │
│  │  - MLStore (résultats IA, confiance, tags)                       │  │
│  │  - CollaborationStore (co-visualisation, cursors)                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Communication Layer (services/)                                 │  │
│  │  - APIService (REST HTTP/2 ou gRPC)                              │  │
│  │  - WSService (WebSocket pour temps réel)                         │  │
│  │  - RTCService (WebRTC pour co-visualisation P2P)                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↕ HTTP/2, WS, WebRTC
┌─────────────────────────────────────────────────────────────────────────┐
│                       API GATEWAY (Kong, Traefik, ou Nginx)             │
│  - Routage intelligent (viewer, ML, PACS, storage)                     │
│  - Rate limiting, authentification (JWT)                                │
│  - Versioning API (v1, v2)                                              │
│  - Load balancing                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↕
┌────────────────────┬────────────────────┬────────────────────┬──────────┐
│  VIEWER SERVICE    │   ML SERVICE       │  PACS PLUGIN       │ STORAGE  │
│  (FastAPI)         │   (FastAPI)        │  (Telemis)         │ (MinIO)  │
├────────────────────┼────────────────────┼────────────────────┼──────────┤
│ - Tile streaming   │ - Routage par tags │ - DICOM Q/R        │ - S3 API │
│ - Métadonnées      │ - Inference        │ - Worklist         │ - Backup │
│ - Coord mapping    │ - Heatmap overlay  │ - Store/Retrieve   │ - Repli  │
│ - Slide cache      │ - Confiance score  │                    │FS→Cloud  │
└────────────────────┴────────────────────┴────────────────────┴──────────┘
         ↓                      ↓                      ↓               ↓
┌────────────────────┬────────────────────┬────────────────────┬──────────┐
│  OPENSLIDE LIB     │   ML PIPELINE      │  DICOM CLIENT      │FILES/S3  │
│  (format detect)   │   (MLflow)         │  (pydicom)         │          │
│  (tile extract)    │   - Model registry │                    │          │
│                    │   - Experiment     │                    │          │
│                    │     tracking       │                    │          │
│                    │   - DVC versioning │                    │          │
└────────────────────┴────────────────────┴────────────────────┴──────────┘
                                    ↓
                        ┌─────────────────────────┐
                        │  FEEDBACK LOOP ENGINE   │
                        │  - Capture corrections  │
                        │  - Ré-annotation auto   │
                        │  - Trigger ré-training  │
                        │  - A/B testing modèles  │
                        └─────────────────────────┘
```

### 3.2 Modules Détaillés

#### 3.2.1 Viewer Service (Refactoré)

**Responsabilités:**
- Streaming tuiles DZI (inchangé)
- Métadonnées slides (inchangé)
- **NOUVEAU:** Abstraction storage (filesystem, S3, PACS)
- **NOUVEAU:** API pour annotations overlay
- **NOUVEAU:** WebSocket pour collaboration temps réel

**Structure proposée:**

```
backend/viewer-service/
├── main.py                         # FastAPI app
├── api/
│   ├── v1/                         # Version 1 (actuelle)
│   │   ├── slides.py               # Endpoints navigation
│   │   ├── tiles.py                # Endpoints tuiles
│   │   └── metadata.py             # Endpoints métadonnées
│   └── v2/                         # Version 2 (future)
│       └── annotations.py          # Endpoints annotations
├── services/
│   ├── storage/                    # Abstraction storage
│   │   ├── base.py                 # Interface StorageProvider
│   │   ├── filesystem.py           # Implémentation filesystem
│   │   ├── s3.py                   # Implémentation S3/MinIO
│   │   └── pacs.py                 # Implémentation PACS DICOM
│   ├── format_detector.py          # Inchangé
│   ├── tile_server.py              # Refactoré (utilise StorageProvider)
│   └── collaboration.py            # NOUVEAU: WebSocket handler
├── models/
│   ├── slide.py                    # Pydantic models
│   ├── annotation.py               # NOUVEAU
│   └── metadata.py                 # NOUVEAU
├── config/
│   ├── settings.py                 # Settings (pydantic-settings)
│   └── feature_flags.py            # Feature flags (LaunchDarkly, etc.)
└── tests/
    ├── unit/
    └── integration/
```

**Interfaces clés:**

```python
# backend/viewer-service/services/storage/base.py

from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Optional
from pathlib import Path

class StorageProvider(ABC):
    """
    Interface abstraite pour backends de storage.
    Permet de switcher filesystem → S3 → PACS sans changer le code métier.
    """

    @abstractmethod
    async def get_slide_path(self, slide_id: str) -> Path:
        """Retourne chemin local ou télécharge depuis storage distant."""
        pass

    @abstractmethod
    async def list_slides(self, path: str = "/") -> List[Dict]:
        """Liste slides dans un dossier (hiérarchique)."""
        pass

    @abstractmethod
    async def get_metadata(self, slide_id: str) -> Dict:
        """Extrait métadonnées (OpenSlide, DICOM tags, etc.)."""
        pass

    @abstractmethod
    async def store_slide(self, file: BinaryIO, metadata: Dict) -> str:
        """Stocke une nouvelle lame, retourne slide_id."""
        pass


# backend/viewer-service/services/storage/filesystem.py

class FilesystemStorageProvider(StorageProvider):
    """
    Implémentation filesystem (actuel).
    Compatible avec l'architecture Phase 1.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    async def get_slide_path(self, slide_id: str) -> Path:
        # Utilise slide_scanner.get_slide_path_by_id() existant
        return get_slide_path_by_id(slide_id)

    # ... implémentations autres méthodes
```

#### 3.2.2 ML Service (Nouveau)

**Responsabilités:**
- Routage lames vers modèles IA appropriés (par tags)
- Inference (détection tumeurs, classification, segmentation)
- Génération heatmaps de confiance
- Versioning modèles (MLflow Model Registry)
- Feedback loop (capture corrections pathologistes)

**Structure proposée:**

```
backend/ml-service/
├── main.py                         # FastAPI app
├── api/
│   ├── inference.py                # POST /api/ml/inference
│   ├── feedback.py                 # POST /api/ml/feedback (corrections)
│   └── models.py                   # GET /api/ml/models (liste modèles)
├── services/
│   ├── model_router.py             # Routage par tags (slide → modèle)
│   ├── inference_engine.py         # Exécution inference
│   ├── heatmap_generator.py        # Génération overlays confiance
│   └── feedback_collector.py       # Capture corrections
├── pipelines/
│   ├── training/                   # Pipelines MLflow
│   │   ├── tumor_detection.py
│   │   ├── classification.py
│   │   └── segmentation.py
│   ├── preprocessing/              # Pipelines données
│   │   ├── tile_extraction.py
│   │   └── augmentation.py
│   └── evaluation/                 # Validation modèles
│       ├── metrics.py
│       └── ab_testing.py
├── models/
│   ├── registry.py                 # Interface MLflow Registry
│   ├── versioning.py               # Versioning avec DVC
│   └── deployment.py               # Déploiement modèles
├── config/
│   ├── model_tags.yaml             # Mapping tags → modèles
│   └── inference_config.yaml       # Config inference
└── tests/
    └── test_inference.py
```

**Exemple de routage par tags:**

```yaml
# backend/ml-service/config/model_tags.yaml

tag_routing:
  # Tag "breast_cancer" → modèle spécialisé sein
  breast_cancer:
    model_name: "breast-tumor-detector-v2"
    model_version: "3"
    confidence_threshold: 0.85
    preprocessing:
      - normalize_stain
      - tissue_detection
    postprocessing:
      - non_max_suppression
      - heatmap_generation

  # Tag "lung_cancer" → modèle spécialisé poumon
  lung_cancer:
    model_name: "lung-classifier-v1"
    model_version: "2"
    confidence_threshold: 0.80
    preprocessing:
      - normalize_stain
    postprocessing:
      - multi_class_overlay

  # Tag "generic" → modèle généraliste
  generic:
    model_name: "generic-pathology-v1"
    model_version: "1"
    confidence_threshold: 0.70
```

**API d'inference:**

```python
# backend/ml-service/api/inference.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.model_router import route_to_model
from services.inference_engine import run_inference

router = APIRouter(prefix="/api/ml", tags=["ml"])

class InferenceRequest(BaseModel):
    slide_id: str
    tags: List[str]  # Ex: ["breast_cancer", "high_priority"]
    roi: Optional[Dict] = None  # Region of interest (coords)

class InferenceResponse(BaseModel):
    slide_id: str
    model_name: str
    model_version: str
    predictions: List[Dict]  # [{class, confidence, bbox}, ...]
    heatmap_url: str  # URL vers heatmap overlay
    processing_time_ms: float

@router.post("/inference", response_model=InferenceResponse)
async def infer_slide(request: InferenceRequest):
    """
    Exécute inference sur une lame.

    Process:
    1. Routage par tags → sélection modèle approprié
    2. Extraction tuiles (si ROI spécifié)
    3. Inference via modèle chargé (MLflow)
    4. Génération heatmap de confiance
    5. Stockage résultats (cache + DB)

    Args:
        request: InferenceRequest avec slide_id, tags, ROI optionnel

    Returns:
        InferenceResponse avec prédictions et heatmap
    """

    # 1. Router vers le bon modèle
    model_config = route_to_model(request.tags)

    # 2. Run inference
    result = await run_inference(
        slide_id=request.slide_id,
        model_config=model_config,
        roi=request.roi
    )

    return result
```

#### 3.2.3 PACS Plugin (Intégration Telemis)

**Responsabilités:**
- Query/Retrieve DICOM (C-FIND, C-MOVE)
- Worklist management (MWL)
- Store lames au PACS (C-STORE)
- Conversion formats propriétaires → DICOM WSI

**Structure proposée:**

```
backend/pacs-plugin/
├── main.py                         # FastAPI app (ou serveur DICOM)
├── api/
│   ├── query.py                    # POST /api/pacs/query (C-FIND)
│   ├── retrieve.py                 # POST /api/pacs/retrieve (C-MOVE)
│   └── store.py                    # POST /api/pacs/store (C-STORE)
├── services/
│   ├── dicom_client.py             # Client DICOM (pydicom, pynetdicom)
│   ├── converter.py                # Conversion .mrxs/.bif → DICOM WSI
│   └── worklist.py                 # Gestion worklist
├── config/
│   └── pacs_config.yaml            # Config PACS Telemis
└── tests/
    └── test_dicom_integration.py
```

**Exemple de conversion MRXS → DICOM WSI:**

```python
# backend/pacs-plugin/services/converter.py

from pydicom.dataset import Dataset
from pydicom.uid import generate_uid
import openslide

class DicomWsiConverter:
    """
    Convertit slides propriétaires en DICOM WSI.
    Basé sur standard DICOM Supplement 145 (Whole Slide Imaging).
    """

    def convert_slide_to_dicom(
        self,
        slide_path: Path,
        patient_info: Dict
    ) -> Dataset:
        """
        Convertit slide → DICOM WSI.

        Steps:
        1. Ouvrir slide avec OpenSlide
        2. Extraire métadonnées (dimensions, magnification, vendor)
        3. Créer Dataset DICOM avec tags appropriés
        4. Encoder pyramide en JPEG2000 ou JPEG
        5. Retourner Dataset prêt pour C-STORE
        """

        slide = openslide.OpenSlide(str(slide_path))

        # Créer dataset DICOM
        ds = Dataset()
        ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.77.1.6"  # VL Whole Slide Microscopy Image
        ds.SOPInstanceUID = generate_uid()

        # Patient info
        ds.PatientName = patient_info.get("name", "ANONYMOUS")
        ds.PatientID = patient_info.get("id", "")

        # Acquisition info
        ds.Modality = "SM"  # Slide Microscopy
        ds.Manufacturer = slide.properties.get("openslide.vendor", "Unknown")

        # Image pyramid
        ds.TotalPixelMatrixColumns = slide.dimensions[0]
        ds.TotalPixelMatrixRows = slide.dimensions[1]
        ds.NumberOfFrames = slide.level_count

        # ... encoder frames JPEG2000 ...

        slide.close()
        return ds
```

#### 3.2.4 Feedback Loop Engine (Nouveau)

**Responsabilités:**
- Capture corrections pathologistes
- Ré-annotation automatique des datasets
- Déclenchement ré-entraînement (CI/CD ML)
- A/B testing modèles
- Métriques qualité modèles (drift detection)

**Structure proposée:**

```
backend/feedback-loop/
├── main.py                         # Orchestrator (Airflow, Prefect, ou simple scheduler)
├── collectors/
│   ├── annotation_collector.py     # Capture annotations frontend
│   └── correction_collector.py     # Capture corrections IA
├── processors/
│   ├── reannotation_engine.py      # Ré-étiquetage dataset
│   └── dataset_versioning.py       # Versioning avec DVC
├── triggers/
│   ├── retraining_trigger.py       # Lance pipeline MLflow
│   └── deployment_trigger.py       # Déploie nouveau modèle
├── monitoring/
│   ├── drift_detector.py           # Détection data/concept drift
│   └── quality_metrics.py          # Suivi métriques modèles
└── config/
    └── feedback_config.yaml        # Seuils déclenchement ré-training
```

**Exemple de pipeline feedback:**

```python
# backend/feedback-loop/collectors/correction_collector.py

from pydantic import BaseModel
from datetime import datetime
from typing import List

class Correction(BaseModel):
    """
    Représente une correction pathologiste.
    """
    slide_id: str
    model_prediction: Dict  # Prédiction originale IA
    pathologist_correction: Dict  # Correction manuelle
    corrected_at: datetime
    pathologist_id: str
    correction_type: str  # "false_positive", "false_negative", "refinement"

class CorrectionCollector:
    """
    Collecte corrections et décide si ré-entraînement nécessaire.
    """

    def __init__(self, db, config):
        self.db = db
        self.config = config

    async def collect_correction(self, correction: Correction):
        """
        Stocke correction et évalue besoin de ré-entraînement.

        Logique:
        - Si > 100 corrections accumulées → trigger ré-annotation
        - Si accuracy drop > 5% → trigger ré-entraînement urgent
        - Si distribution drift détecté → alert équipe ML
        """

        # 1. Stocker correction
        await self.db.store_correction(correction)

        # 2. Calculer métriques
        stats = await self.db.get_correction_stats(
            model_name=correction.model_prediction["model_name"],
            window_days=7
        )

        # 3. Déclencher actions si nécessaire
        if stats["correction_count"] > self.config.retraining_threshold:
            await self.trigger_retraining(stats)

        if stats["accuracy_drop"] > 0.05:
            await self.alert_ml_team(stats, urgency="high")
```

### 3.3 Communication Inter-Services

#### 3.3.1 API Gateway

**Choix technologiques:**
- **Kong** (open-source, plugin-rich) ou **Traefik** (cloud-native, simple)
- Authentification JWT (pas de session serveur)
- Rate limiting (par utilisateur/IP)
- Circuit breaker (fallback si ML service down)

**Configuration exemple (Kong):**

```yaml
# kong.yaml
_format_version: "2.1"

services:
  - name: viewer-service
    url: http://viewer-service:8000
    routes:
      - name: viewer-routes
        paths:
          - /api/slides
          - /api/tiles
        methods:
          - GET
          - POST
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: local

  - name: ml-service
    url: http://ml-service:8001
    routes:
      - name: ml-routes
        paths:
          - /api/ml
        methods:
          - POST
    plugins:
      - name: jwt
        config:
          claims_to_verify:
            - exp
      - name: rate-limiting
        config:
          minute: 20  # Inference coûteuse

  - name: pacs-plugin
    url: http://pacs-plugin:8002
    routes:
      - name: pacs-routes
        paths:
          - /api/pacs
        methods:
          - GET
          - POST
```

#### 3.3.2 Messaging Asynchrone (Optionnel Phase 2)

Pour découplage total, envisager **RabbitMQ** ou **Kafka**:

```
Frontend → API Gateway → Viewer Service → [Queue: inference_requests]
                                              ↓
                                          ML Service (consumer)
                                              ↓
                                          [Queue: inference_results]
                                              ↓
                                          Viewer Service (consumer) → Frontend (WebSocket)
```

### 3.4 État et Persistance

#### 3.4.1 Bases de Données

| Service | Base de Données | Rôle |
|---------|-----------------|------|
| Viewer Service | PostgreSQL | Métadonnées slides, utilisateurs, sessions |
| ML Service | PostgreSQL + MLflow DB | Résultats inference, feedback, métriques modèles |
| PACS Plugin | PostgreSQL | Cache DICOM queries, worklist |
| Feedback Loop | PostgreSQL + DVC | Corrections, datasets versionés |

**Schéma Viewer Service (simplifié):**

```sql
-- Slides
CREATE TABLE slides (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    format VARCHAR(50) NOT NULL,
    storage_provider VARCHAR(50) NOT NULL,  -- 'filesystem', 's3', 'pacs'
    storage_path TEXT NOT NULL,
    metadata JSONB,  -- Dimensions, levels, vendor, etc.
    tags TEXT[],  -- Tags pour routage ML
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Annotations
CREATE TABLE annotations (
    id UUID PRIMARY KEY,
    slide_id UUID REFERENCES slides(id),
    user_id UUID REFERENCES users(id),
    geometry JSONB NOT NULL,  -- GeoJSON polygone/point
    label VARCHAR(100),
    confidence FLOAT,  -- Si annotation IA
    is_ai_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users (simplifié, utiliser Keycloak en production)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'pathologist', 'radiologist', 'admin'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Schéma ML Service (simplifié):**

```sql
-- Inferences
CREATE TABLE inferences (
    id UUID PRIMARY KEY,
    slide_id UUID NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    predictions JSONB NOT NULL,  -- [{class, confidence, bbox}, ...]
    heatmap_url TEXT,
    processing_time_ms FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feedback (corrections)
CREATE TABLE corrections (
    id UUID PRIMARY KEY,
    inference_id UUID REFERENCES inferences(id),
    pathologist_id UUID NOT NULL,
    original_prediction JSONB NOT NULL,
    corrected_prediction JSONB NOT NULL,
    correction_type VARCHAR(50) NOT NULL,  -- 'false_positive', 'false_negative', etc.
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3.4.2 Cache

| Type de Cache | Technologie | Rôle |
|---------------|-------------|------|
| Tuiles | Redis + Filesystem | Cache tuiles fréquentes (LRU) |
| Métadonnées | Redis | Cache slide metadata (TTL 1h) |
| Résultats ML | Redis | Cache inference results (TTL 24h) |
| Sessions | Redis | Sessions utilisateurs (JWT optionnel) |

### 3.5 Sécurité et Conformité

#### 3.5.1 RGPD/HIPAA

| Exigence | Solution |
|----------|----------|
| Anonymisation | Suppression tags DICOM patient avant storage (except audit trail) |
| Encryption at rest | MinIO encryption, PostgreSQL pgcrypto |
| Encryption in transit | TLS 1.3 partout (nginx, API gateway) |
| Audit trail | Table `audit_logs` avec toutes actions sensibles |
| Right to be forgotten | Soft delete + job purge régulier |

#### 3.5.2 MDR (Medical Device Regulation)

| Exigence | Solution |
|----------|----------|
| Traçabilité modèles | MLflow Model Registry + DVC versioning |
| Validation clinique | Pipeline test/validation séparé, rapports automatiques |
| Documentation technique | Auto-génération docs (Sphinx, Swagger) |
| Change log | Git tags + CHANGELOG.md auto-généré |

#### 3.5.3 AI Act (EU)

| Exigence | Solution |
|----------|----------|
| Transparence IA | Affichage confiance score, modèle utilisé |
| Explicabilité | Heatmaps, SHAP values (optionnel) |
| Human oversight | Pathologiste DOIT valider résultats IA |
| Bias monitoring | Métriques fairness (par genre, âge, etc.) |

---

## 4. Plan de Migration

### 4.1 Stratégie: Strangler Fig Pattern

**Principe:** Remplacer progressivement l'ancien système sans réécriture complète (éviter big bang).

```
Phase 1 (Actuel)         Phase 2 (Transition)         Phase 3 (Cible)
┌────────────┐           ┌────────────┐               ┌────────────┐
│ Monolithe  │    →      │ Monolithe  │────┐          │  Gateway   │
│ (FastAPI)  │           │ (legacy)   │    │    →     │            │
└────────────┘           └────────────┘    │          └─────┬──────┘
                                            │                │
                         ┌──────────────────┘                ├─ Viewer Service
                         │                                   ├─ ML Service
                         ├─ ML Service (nouveau)             ├─ PACS Plugin
                         └─ PACS Plugin (nouveau)            └─ Storage Service
```

### 4.2 Phases de Migration

#### Phase 2.0: Préparation (2 semaines)

**Objectifs:**
- Isoler code existant en modules (sans changer comportement)
- Créer abstractions (StorageProvider, etc.)
- Ajouter tests unitaires (coverage >80%)

**Tâches:**
1. Refactor `tile_server.py` pour utiliser `StorageProvider` abstrait
2. Créer `FilesystemStorageProvider` (compatible existant)
3. Extraire configuration hardcodée → `settings.py` (pydantic-settings)
4. Ajouter feature flags (LaunchDarkly ou fichier YAML simple)
5. Tests unitaires pour tous services critiques

**Critères de succès:**
- Aucun comportement changé (regression tests passent)
- Code coverage >80%
- Architecture prête pour injection ML

#### Phase 2.1: ML Service (Prototype) (3 semaines)

**Objectifs:**
- Créer ML Service minimal (inference simple)
- Routage par tags (1 modèle de test)
- Heatmap overlay basique

**Tâches:**
1. Créer `backend/ml-service/` avec FastAPI
2. Implémenter `/api/ml/inference` (modèle mock d'abord)
3. Intégrer MLflow Model Registry
4. Créer pipeline inference simple (tumor detection)
5. Générer heatmap overlay (PIL + OpenCV)
6. Intégrer au frontend (overlay heatmap sur viewer)

**Critères de succès:**
- Inference fonctionnelle (même avec modèle simple)
- Heatmap affiché sur viewer
- Temps inference <10s pour slide entier (niveau bas résolution)

#### Phase 2.2: Feedback Loop (MVP) (2 semaines)

**Objectifs:**
- Capture corrections pathologistes
- Stockage feedback en DB
- Dashboard feedback (admin)

**Tâches:**
1. Créer UI correction (frontend: AnnotationTool)
2. API POST `/api/ml/feedback` (ML Service)
3. Stockage corrections en PostgreSQL
4. Dashboard admin (liste corrections, stats)

**Critères de succès:**
- Pathologiste peut corriger annotation IA
- Correction stockée avec métadonnées (qui, quand, quoi)
- Dashboard affiche stats corrections

#### Phase 2.3: PACS Integration (Prototype) (3 semaines)

**Objectifs:**
- Query DICOM slides depuis PACS Telemis
- Afficher dans FolderBrowser
- Retrieve slide (C-MOVE) et ouvrir dans viewer

**Tâches:**
1. Créer `backend/pacs-plugin/` avec client DICOM (pynetdicom)
2. Implémenter C-FIND (query worklist)
3. Implémenter C-MOVE (retrieve slide)
4. Créer `PacsStorageProvider`
5. Intégrer au FolderBrowser (onglet "PACS")

**Critères de succès:**
- Liste slides PACS affichée
- Slide PACS ouvrable dans viewer
- Pas de régression viewer filesystem

#### Phase 2.4: Storage Abstraction (1 semaine)

**Objectifs:**
- Support S3/MinIO pour storage slides
- Migration filesystem → S3 (optionnel, configurable)

**Tâches:**
1. Implémenter `S3StorageProvider`
2. Configuration switch (filesystem vs S3)
3. Tests migration (copie slides → S3)

**Critères de succès:**
- Viewer fonctionne identiquement avec S3
- Feature flag pour switch storage

#### Phase 3.0: MLOps Pipeline (4 semaines)

**Objectifs:**
- Pipeline complet ré-entraînement
- Versioning datasets (DVC)
- A/B testing modèles

**Tâches:**
1. Setup MLflow Tracking Server
2. Pipeline training avec Airflow/Prefect
3. Versioning datasets (DVC + S3)
4. A/B testing (2 modèles en parallèle, routing 50/50)
5. Métriques drift detection (Evidently AI)

**Critères de succès:**
- Pipeline training exécutable end-to-end
- Nouveau modèle déployable sans downtime
- A/B testing fonctionnel (métriques comparatives)

#### Phase 3.1: Collaboration Temps Réel (3 semaines)

**Objectifs:**
- Co-visualisation synchronisée
- Cursors collaboratifs
- Annotations partagées en temps réel

**Tâches:**
1. WebSocket server (collaboration service)
2. Sync viewport entre viewers (SyncController refactoré)
3. Cursors collaboratifs (affichage position autres users)
4. Annotations temps réel (broadcast via WebSocket)

**Critères de succès:**
- 2+ users peuvent voir même slide en sync
- Annotations apparaissent instantanément
- Latence <100ms pour sync viewport

### 4.3 Risques et Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression viewer existant | Moyen | Élevé | Tests automatisés exhaustifs avant chaque release |
| Performance ML inference | Élevé | Moyen | Optimisation (batching, quantization, GPU) + cache aggressif |
| Complexité architecture | Moyen | Moyen | Documentation rigoureuse, architecture decision records (ADR) |
| Intégration PACS Telemis | Élevé | Moyen | POC avec vraies données Telemis AVANT développement complet |
| Conformité RGPD/MDR | Faible | Élevé | Audit sécurité externe, checklist conformité |

---

## 5. Roadmap Détaillée

### 5.1 Timeline

```
Janvier 2026:  Phase 2.0 (Préparation)
Février 2026:  Phase 2.1 (ML Service Prototype)
Mars 2026:     Phase 2.2 (Feedback Loop MVP) + Phase 2.3 (PACS Integration POC)
Avril 2026:    Phase 2.4 (Storage Abstraction) + Tests intégration
Mai 2026:      Phase 3.0 (MLOps Pipeline)
Juin 2026:     Phase 3.1 (Collaboration Temps Réel)
Juillet 2026:  Tests validation clinique + Documentation finale
Août 2026:     Déploiement pilote CHU UCL
```

### 5.2 Livrables TFE

| Livrable | Description | Date Cible |
|----------|-------------|------------|
| **Rapport TFE** | Document complet (architecture, implémentation, résultats) | Août 2026 |
| **Code Source** | Repo GitHub avec tous services | Août 2026 |
| **Documentation Technique** | Sphinx docs auto-générées | Août 2026 |
| **Manuel Utilisateur** | Guide pathologistes (UI, workflows) | Juillet 2026 |
| **Démo Vidéo** | Screencast 10min (viewer, ML, collaboration) | Août 2026 |
| **Datasets Benchmark** | Datasets annotés pour validation modèles | Juin 2026 |
| **Rapport Conformité** | RGPD, MDR, AI Act checklist | Juillet 2026 |

### 5.3 Métriques de Succès

| Métrique | Cible | Mesure |
|----------|-------|--------|
| **Performance Viewer** | <100ms tile load (p95) | Prometheus metrics |
| **Performance ML** | <10s inference slide entier | MLflow tracking |
| **Accuracy Modèles** | >90% accuracy (tumor detection) | Validation dataset |
| **Feedback Loop** | <24h ré-entraînement après 100 corrections | Pipeline metrics |
| **Uptime** | >99% disponibilité | Monitoring (Grafana) |
| **Conformité** | 100% checklist RGPD/MDR | Audit externe |

---

## 6. Références et Standards

### 6.1 Standards Médicaux

- **DICOM:** https://www.dicomstandard.org/
- **DICOM Supplement 145 (WSI):** https://www.dicomstandard.org/News-dir/ftsup/docs/sups/sup145.pdf
- **OpenSlide Formats:** https://openslide.org/formats/
- **HL7 FHIR (interop future):** https://www.hl7.org/fhir/

### 6.2 MLOps & DevOps

- **MLflow:** https://mlflow.org/
- **DVC (Data Version Control):** https://dvc.org/
- **Evidently AI (drift detection):** https://www.evidentlyai.com/
- **12-Factor App:** https://12factor.net/

### 6.3 Architecture Patterns

- **Strangler Fig Pattern:** https://martinfowler.com/bliki/StranglerFigApplication.html
- **Event-Driven Architecture:** https://martinfowler.com/articles/201701-event-driven.html
- **API Gateway Pattern:** https://microservices.io/patterns/apigateway.html

### 6.4 Sécurité & Conformité

- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **RGPD (GDPR):** https://gdpr.eu/
- **MDR (EU 2017/745):** https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32017R0745
- **AI Act (EU):** https://artificialintelligenceact.eu/

---

## Conclusion

Cette architecture V3 transforme VarunaPoC d'un simple viewer en une **plateforme modulaire MLOps-ready** capable de:

1. **Supporter 12 formats WSI** (MRXS, BIF, SVS, NDPI, CZI, DICOM, etc.)
2. **Router intelligemment vers modèles IA spécialisés** (par tags)
3. **Capturer feedback pathologistes** et ré-entraîner modèles en continu
4. **Intégrer au PACS Telemis** (query/retrieve DICOM)
5. **Permettre collaboration temps réel** (co-visualisation synchronisée)
6. **Respecter RGPD, MDR, AI Act** (conformité réglementaire)

**Principe directeur:** Modularité maximale, couplage minimal. Chaque service peut évoluer indépendamment sans casser le reste du système.

**Prochaines étapes:**
1. Valider cette architecture avec l'équipe (retours, ajustements)
2. Démarrer Phase 2.0 (refactoring préparatoire)
3. Créer backlog détaillé (user stories, tâches techniques)
4. Setup CI/CD pour tous services
5. Commencer développement ML Service (prototype)

---

**Auteur:** VarunaPoC Team (Lead Architecte)
**Contact:** [À compléter]
**License:** Propriétaire (CHU UCL Namur)
