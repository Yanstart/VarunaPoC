# Plan de Refactoring - Phase 2.0 à 3.1

**Version:** 3.0.0
**Date:** 2025-12-31
**Complément:** ARCHITECTURE_V3.md, MODULE_CONTRACTS.md

---

## Objectif

Plan détaillé de refactoring pour transformer le code actuel (Phase 1.7) vers l'architecture MLOps modulaire (Phase 3.x).

**Principe:** Refactoring incrémental, sans casser l'existant (pas de big bang).

---

## 1. État des Lieux - Code Actuel

### 1.1 Fichiers à Refactorer (Backend)

| Fichier | Lignes | Complexité | Priorité Refactoring |
|---------|--------|------------|----------------------|
| `services/tile_server.py` | ~235 | Moyenne | **P0** (couplage OpenSlide) |
| `services/format_detector.py` | ~783 | Élevée | P1 (OK structure, ajouter tests) |
| `services/slide_scanner.py` | ~150 | Faible | P2 (OK, juste ajouter StorageProvider) |
| `routes/slides.py` | ~276 | Faible | **P0** (monolithique, split v1/v2) |
| `main.py` | ~167 | Faible | P1 (ajouter feature flags) |

### 1.2 Fichiers à Refactorer (Frontend)

| Fichier | Lignes | Complexité | Priorité Refactoring |
|---------|--------|------------|----------------------|
| `main.js` | ~697 | Moyenne | **P0** (ajouter state management) |
| `components/Viewer.js` | ~198 | Faible | P2 (OK architecture, juste nettoyage) |
| `viewers/ViewerManager.js` | ~100 | Faible | P1 (ajouter events collaboration) |
| `services/ApiService.js` | ~150 | Faible | P1 (ajouter versioning API) |

### 1.3 Dépendances à Ajouter

**Backend:**
```
# requirements.txt (ajouts Phase 2.0)
pydantic-settings==2.0.0       # Configuration management
mlflow==2.9.0                  # ML experiment tracking
aioboto3==12.0.0               # S3/MinIO async client
pynetdicom==2.0.0              # DICOM client
pytest==7.4.0                  # Tests unitaires
pytest-asyncio==0.21.0         # Tests async
pytest-cov==4.1.0              # Code coverage
redis==5.0.0                   # Cache
sqlalchemy[asyncio]==2.0.0     # ORM async
alembic==1.12.0                # Migrations DB
```

**Frontend:**
```json
// package.json (ajouts Phase 2.0)
{
  "dependencies": {
    "peerjs": "^1.5.0",        // WebRTC P2P
    "socket.io-client": "^4.5.0",  // WebSocket client
    "idb": "^8.0.0"            // IndexedDB pour cache local
  },
  "devDependencies": {
    "vitest": "^1.0.0",        // Tests unitaires
    "@vitest/ui": "^1.0.0",    // Tests UI
    "playwright": "^1.40.0"    // Tests E2E
  }
}
```

---

## 2. Phase 2.0 - Préparation (2 semaines)

### 2.1 Objectif

Isoler code existant en modules **sans changer comportement** (refactoring safe).

### 2.2 Tâches Backend

#### Tâche 2.0.1: Abstraire Storage (3 jours)

**Fichiers créés:**
- `backend/viewer-service/services/storage/base.py` (interface)
- `backend/viewer-service/services/storage/filesystem.py` (implémentation)

**Fichiers modifiés:**
- `services/tile_server.py` (utiliser StorageProvider)
- `services/slide_scanner.py` (wrapper dans FilesystemStorageProvider)

**Tests:**
```python
# backend/tests/unit/test_storage_filesystem.py

import pytest
from services.storage.filesystem import FilesystemStorageProvider

@pytest.mark.asyncio
async def test_filesystem_storage_backward_compatible(sample_slides_dir):
    """
    GIVEN code Phase 1 (slide_scanner.py),
    WHEN wrappé dans FilesystemStorageProvider,
    THEN comportement identique.
    """
    provider = FilesystemStorageProvider(root_dir=sample_slides_dir)

    # Test list_slides()
    slides = await provider.list_slides()
    assert len(slides) > 0

    # Test get_slide_path()
    path = await provider.get_slide_path(slides[0].slide_id)
    assert path.exists()

    # Test get_metadata()
    metadata = await provider.get_metadata(slides[0].slide_id)
    assert metadata.dimensions[0] > 0
```

**Critères de succès:**
- [ ] Tests existants passent (aucune régression)
- [ ] Code coverage >80% sur nouveau code
- [ ] CI/CD vert

#### Tâche 2.0.2: Configuration Management (2 jours)

**Fichiers créés:**
- `backend/viewer-service/config/settings.py` (pydantic-settings)
- `backend/viewer-service/config/feature_flags.py`
- `.env.example` (template config)

**Exemple `settings.py`:**

```python
# backend/viewer-service/config/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """
    Configuration application (env vars + .env file).

    Variables:
        SLIDES_ROOT: Chemin racine slides (default: ./Slides)
        STORAGE_PROVIDER: Type storage (filesystem, s3, pacs)
        S3_ENDPOINT: URL S3/MinIO (si STORAGE_PROVIDER=s3)
        API_VERSION: Version API (v1, v2)
        FEATURE_ML_ENABLED: Activer ML service
        FEATURE_PACS_ENABLED: Activer PACS plugin
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    # Storage
    slides_root: Path = Path("./Slides")
    storage_provider: str = "filesystem"  # "filesystem", "s3", "pacs"

    # S3/MinIO (si storage_provider=s3)
    s3_endpoint: Optional[str] = None
    s3_bucket: str = "wsi-slides"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None

    # API
    api_version: str = "v1"
    cors_origins: str = "http://localhost:5173"

    # Feature flags
    feature_ml_enabled: bool = False
    feature_pacs_enabled: bool = False
    feature_collaboration_enabled: bool = False

    # Database
    database_url: str = "sqlite:///./varuna.db"  # Phase 1, PostgreSQL Phase 2

    # Cache
    redis_url: Optional[str] = None  # Si None, pas de cache Redis

# Singleton instance
settings = Settings()
```

**Fichiers modifiés:**
- `main.py` (utiliser `settings`)
- Tous fichiers avec config hardcodée

**Tests:**
```python
# backend/tests/unit/test_settings.py

from config.settings import Settings
import os

def test_settings_from_env_vars(monkeypatch):
    """GIVEN env vars, WHEN load settings, THEN valeurs correctes."""
    monkeypatch.setenv("SLIDES_ROOT", "/custom/path")
    monkeypatch.setenv("FEATURE_ML_ENABLED", "true")

    settings = Settings()
    assert settings.slides_root == Path("/custom/path")
    assert settings.feature_ml_enabled is True
```

**Critères de succès:**
- [ ] Aucune config hardcodée restante
- [ ] `.env.example` complet et documenté
- [ ] CI/CD utilise `.env.test`

#### Tâche 2.0.3: Versioning API (2 jours)

**Fichiers créés:**
- `backend/viewer-service/api/v1/` (move routes actuelles)
- `backend/viewer-service/api/v2/` (vide pour l'instant)
- `backend/viewer-service/api/__init__.py` (router factory)

**Structure:**

```
backend/viewer-service/api/
├── __init__.py           # Router factory
├── v1/
│   ├── __init__.py
│   ├── slides.py         # Copie routes/slides.py (deprecated)
│   └── health.py
└── v2/
    ├── __init__.py
    ├── slides.py         # Nouveau format (ajout tags, etc.)
    └── metadata.py       # Nouveau endpoint métadonnées enrichies
```

**Exemple `api/__init__.py`:**

```python
# backend/viewer-service/api/__init__.py

from fastapi import APIRouter
from .v1 import slides as slides_v1
from .v2 import slides as slides_v2, metadata as metadata_v2

def create_router(api_version: str = "v1") -> APIRouter:
    """
    Factory router selon version API.

    Args:
        api_version: "v1" ou "v2"

    Returns:
        APIRouter configuré
    """
    if api_version == "v1":
        router = APIRouter(prefix="/api/v1")
        router.include_router(slides_v1.router)
        return router

    elif api_version == "v2":
        router = APIRouter(prefix="/api/v2")
        router.include_router(slides_v2.router)
        router.include_router(metadata_v2.router)
        return router

    else:
        raise ValueError(f"Unsupported API version: {api_version}")
```

**Fichiers modifiés:**
- `main.py` (utiliser `create_router(settings.api_version)`)

**Tests:**
```python
# backend/tests/integration/test_api_versioning.py

import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_v1_api_backward_compatible():
    """GIVEN API v1, WHEN request slides, THEN format Phase 1."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/slides/")
        assert response.status_code == 200
        data = response.json()

        # Format v1 (pas de tags)
        assert "slides" in data
        assert "count" in data

@pytest.mark.asyncio
async def test_v2_api_new_format():
    """GIVEN API v2, WHEN request slides, THEN format enrichi."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v2/slides/")
        assert response.status_code == 200
        data = response.json()

        # Format v2 (avec tags)
        assert "slides" in data
        for slide in data["slides"]:
            assert "tags" in slide  # Nouveau champ v2
```

**Critères de succès:**
- [ ] v1 fonctionne identiquement (backward compatible)
- [ ] v2 accessible mais peut retourner 501 Not Implemented (stub)
- [ ] Frontend configurable pour utiliser v1 ou v2

#### Tâche 2.0.4: Tests Unitaires (3 jours)

**Objectif:** Code coverage >80% sur tous services critiques.

**Fichiers à tester en priorité:**
1. `services/storage/filesystem.py`
2. `services/format_detector.py` (ajouter tests manquants)
3. `services/tile_server.py`
4. `config/settings.py`

**Exemple test `tile_server.py`:**

```python
# backend/tests/unit/test_tile_server.py

import pytest
from services.tile_server import TileServer
from unittest.mock import Mock, patch

@pytest.fixture
def tile_server():
    return TileServer()

@pytest.fixture
def mock_openslide():
    """Mock OpenSlide pour tests sans fichiers réels."""
    with patch('openslide.OpenSlide') as mock:
        slide = Mock()
        slide.dimensions = (50000, 40000)
        slide.level_count = 4
        slide.level_dimensions = [(50000, 40000), (25000, 20000), (12500, 10000), (6250, 5000)]
        slide.level_downsamples = [1.0, 2.0, 4.0, 8.0]

        # Mock read_region
        from PIL import Image
        slide.read_region.return_value = Image.new('RGBA', (256, 256), color='white')

        mock.return_value = slide
        yield mock

@pytest.mark.asyncio
async def test_get_tile_valid_request(tile_server, mock_openslide, tmp_path):
    """GIVEN slide valide, WHEN get_tile(), THEN retourne JPEG bytes."""
    slide_path = str(tmp_path / "test.mrxs")
    tile_bytes = tile_server.get_tile(slide_path, level=0, col=0, row=0)

    assert tile_bytes is not None
    assert tile_bytes.startswith(b'\xff\xd8')  # JPEG magic bytes

@pytest.mark.asyncio
async def test_get_tile_out_of_bounds(tile_server, mock_openslide, tmp_path):
    """GIVEN tuile hors limites, WHEN get_tile(), THEN retourne None."""
    slide_path = str(tmp_path / "test.mrxs")
    tile_bytes = tile_server.get_tile(slide_path, level=0, col=9999, row=9999)

    assert tile_bytes is None
```

**Setup pytest:**

```python
# backend/conftest.py (fixtures globales)

import pytest
from pathlib import Path

@pytest.fixture
def sample_slides_dir(tmp_path):
    """Crée dossier avec slides de test."""
    slides_dir = tmp_path / "Slides"
    slides_dir.mkdir()

    # Créer structure MRXS de test
    mrxs_file = slides_dir / "test.mrxs"
    mrxs_file.write_text("fake mrxs content")

    companion_dir = slides_dir / "test"
    companion_dir.mkdir()
    (companion_dir / "Slidedat.ini").write_text("[MRXS]\nversion=1")
    (companion_dir / "Data0000.dat").write_bytes(b'\x00' * 1024)

    return slides_dir
```

**CI/CD integration:**

```yaml
# .github/workflows/backend-tests.yml

name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov=services --cov=api --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          fail_ci_if_error: true

      - name: Check coverage threshold
        run: |
          cd backend
          coverage report --fail-under=80
```

**Critères de succès:**
- [ ] Coverage >80% sur tous modules critiques
- [ ] CI/CD échoue si coverage <80%
- [ ] Tous tests passent localement et en CI

### 2.3 Tâches Frontend

#### Tâche 2.0.5: State Management (3 jours)

**Fichiers créés:**
- `frontend/src/state/ViewerStore.js`
- `frontend/src/state/AnnotationStore.js`
- `frontend/src/state/MLStore.js`

**Implémentation `ViewerStore.js`:**

```javascript
// frontend/src/state/ViewerStore.js

import { eventBus } from '../core/EventBus.js';

/**
 * ViewerStore - State management pour viewers.
 *
 * Pattern: Observable Store (reactive, immutable updates).
 */
class ViewerStore {
  constructor() {
    this._state = {
      viewers: new Map(),
      activeViewerId: null,
      syncEnabled: false
    };

    this._listeners = new Set();
  }

  /**
   * Get current state (immutable).
   */
  get state() {
    return this._deepClone(this._state);
  }

  /**
   * Update state (immutable).
   *
   * @private
   */
  _setState(updater) {
    const newState = updater(this._deepClone(this._state));
    this._state = newState;
    this._notifyListeners();
  }

  /**
   * Ajoute viewer.
   */
  addViewer(viewerId, initialState = {}) {
    this._setState(state => {
      if (state.viewers.has(viewerId)) {
        throw new Error(`Viewer ${viewerId} already exists`);
      }

      const viewerState = {
        id: viewerId,
        slideId: initialState.slideId || null,
        viewport: initialState.viewport || { x: 0, y: 0, zoom: 1 },
        annotations: [],
        mlResults: null,
        isLoading: false,
        error: null,
        ...initialState
      };

      state.viewers.set(viewerId, viewerState);
      state.activeViewerId = state.activeViewerId || viewerId;

      return state;
    });

    eventBus.emit('viewer:added', { viewerId });
  }

  /**
   * Update viewport.
   */
  updateViewport(viewerId, viewport) {
    this._setState(state => {
      const viewer = state.viewers.get(viewerId);
      if (!viewer) {
        throw new Error(`Viewer ${viewerId} not found`);
      }

      viewer.viewport = { ...viewer.viewport, ...viewport };
      state.viewers.set(viewerId, viewer);

      return state;
    });

    eventBus.emit('viewport:changed', { viewerId, viewport });

    // Sync si activé
    if (this._state.syncEnabled) {
      this._syncViewports(viewerId, viewport);
    }
  }

  /**
   * Subscribe aux changements.
   */
  subscribe(listener) {
    this._listeners.add(listener);
    return () => this._listeners.delete(listener);
  }

  /**
   * Notify listeners.
   *
   * @private
   */
  _notifyListeners() {
    const state = this.state;
    for (const listener of this._listeners) {
      listener(state);
    }
  }

  /**
   * Deep clone helper.
   *
   * @private
   */
  _deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  /**
   * Sync viewports.
   *
   * @private
   */
  _syncViewports(sourceViewerId, viewport) {
    for (const [viewerId] of this._state.viewers) {
      if (viewerId !== sourceViewerId) {
        this.updateViewport(viewerId, viewport);
      }
    }
  }
}

// Singleton
export const viewerStore = new ViewerStore();
```

**Intégration dans `main.js`:**

```javascript
// frontend/src/main.js (modifications)

import { viewerStore } from './state/ViewerStore.js';

// Subscribe aux changements state
viewerStore.subscribe(state => {
  console.log('[App] State updated:', state);
  // Mettre à jour UI si nécessaire
});

// Exemple usage
function showViewerPage(slide) {
  // ... existing code ...

  // Ajouter viewer au store
  viewerStore.addViewer('main-viewer', {
    slideId: slide.id,
    viewport: { x: 0, y: 0, zoom: 1 }
  });

  // ... existing code ...
}
```

**Tests:**

```javascript
// frontend/src/state/__tests__/ViewerStore.test.js

import { describe, it, expect, beforeEach } from 'vitest';
import { ViewerStore } from '../ViewerStore.js';

describe('ViewerStore', () => {
  let store;

  beforeEach(() => {
    store = new ViewerStore();
  });

  it('should add viewer', () => {
    store.addViewer('viewer-1', { slideId: 'slide-abc' });

    const state = store.state;
    expect(state.viewers.has('viewer-1')).toBe(true);
    expect(state.viewers.get('viewer-1').slideId).toBe('slide-abc');
  });

  it('should update viewport', () => {
    store.addViewer('viewer-1');
    store.updateViewport('viewer-1', { zoom: 2 });

    const state = store.state;
    expect(state.viewers.get('viewer-1').viewport.zoom).toBe(2);
  });

  it('should notify listeners on update', () => {
    let notified = false;
    store.subscribe(() => { notified = true; });

    store.addViewer('viewer-1');
    expect(notified).toBe(true);
  });
});
```

**Critères de succès:**
- [ ] State management fonctionnel
- [ ] Tests unitaires passent (Vitest)
- [ ] Pas de régression UI existante

#### Tâche 2.0.6: API Versioning Frontend (1 jour)

**Fichiers modifiés:**
- `frontend/src/services/ApiService.js`

**Implémentation:**

```javascript
// frontend/src/services/ApiService.js (refactoré)

class ApiService {
  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    this.apiVersion = import.meta.env.VITE_API_VERSION || 'v1';
  }

  /**
   * Build URL avec version.
   *
   * @private
   */
  _buildUrl(path, version = null) {
    const v = version || this.apiVersion;
    return `${this.baseUrl}/api/${v}${path}`;
  }

  /**
   * Fetch slides (compatible v1/v2).
   */
  async fetchSlides() {
    const url = this._buildUrl('/slides/');
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch slides: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Fetch slide metadata (v2 avec fallback v1).
   */
  async getSlideMetadata(slideId) {
    try {
      // Essayer v2 d'abord
      const url = this._buildUrl(`/slides/${slideId}/metadata`, 'v2');
      const response = await fetch(url);

      if (response.ok) {
        return response.json();
      }

      // Fallback v1
      if (response.status === 404) {
        return this._getSlideInfoV1(slideId);
      }

      throw new Error(`API error: ${response.statusText}`);

    } catch (err) {
      console.warn('v2 API failed, falling back to v1:', err);
      return this._getSlideInfoV1(slideId);
    }
  }

  /**
   * Fallback v1.
   *
   * @private
   */
  async _getSlideInfoV1(slideId) {
    const url = this._buildUrl(`/slides/${slideId}/info`, 'v1');
    const response = await fetch(url);
    return response.json();
  }
}

export const apiService = new ApiService();
```

**Configuration:**

```bash
# frontend/.env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=v1

# frontend/.env.production
VITE_API_BASE_URL=https://varuna.chu-ucl.be
VITE_API_VERSION=v2
```

**Critères de succès:**
- [ ] Frontend fonctionne avec v1 ET v2
- [ ] Fallback automatique si v2 indisponible
- [ ] Configuration via env vars

### 2.4 Livrable Phase 2.0

**À la fin de Phase 2.0:**

- [ ] Backend refactoré (StorageProvider, Settings, API versioning)
- [ ] Frontend refactoré (State management, API versioning)
- [ ] Tests unitaires >80% coverage
- [ ] CI/CD fonctionnel (tests auto, coverage check)
- [ ] Documentation mise à jour (README, ARCHITECTURE_V3.md)
- [ ] Aucune régression fonctionnelle (regression tests passent)

**Tag Git:** `v2.0.0-refactoring-complete`

---

## 3. Phase 2.1 - ML Service Prototype (3 semaines)

### 3.1 Tâche 2.1.1: Créer ML Service Minimal (1 semaine)

**Structure:**

```
backend/ml-service/
├── main.py                    # FastAPI app
├── api/
│   ├── __init__.py
│   ├── inference.py           # POST /api/ml/inference
│   ├── feedback.py            # POST /api/ml/feedback
│   └── models.py              # GET /api/ml/models
├── services/
│   ├── model_router.py        # Routage par tags
│   ├── inference_engine.py    # Exécution inference
│   └── heatmap_generator.py   # Génération heatmap
├── models/
│   ├── registry.py            # MLflow Model Registry
│   └── mock_model.py          # Modèle mock pour tests
├── config/
│   ├── settings.py            # Settings MLflow, etc.
│   └── model_tags.yaml        # Mapping tags → modèles
├── requirements.txt
└── tests/
    └── test_inference.py
```

**Implémentation `api/inference.py`:**

```python
# backend/ml-service/api/inference.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from services.inference_engine import run_inference

router = APIRouter(prefix="/api/ml", tags=["ml"])

class InferenceRequest(BaseModel):
    slide_id: str
    tags: List[str]
    roi: Optional[Dict] = None

class InferenceResponse(BaseModel):
    inference_id: str
    slide_id: str
    model_name: str
    model_version: str
    predictions: List[Dict]
    heatmap_url: Optional[str] = None
    processing_time_ms: float

@router.post("/inference", response_model=InferenceResponse)
async def infer_slide(request: InferenceRequest):
    """
    Exécute inference sur slide.

    Phase 2.1: Utilise modèle mock (détection aléatoire).
    Phase 3.0: Modèles réels MLflow.
    """
    try:
        result = await run_inference(
            slide_id=request.slide_id,
            tags=request.tags,
            roi=request.roi
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Inference error: {e}")
```

**Modèle mock (Phase 2.1):**

```python
# backend/ml-service/models/mock_model.py

import random
from typing import List, Dict

class MockTumorDetector:
    """
    Modèle mock pour tests (génère détections aléatoires).

    Phase 2.1: Permet tester pipeline sans modèle réel.
    Phase 3.0: Remplacé par modèles MLflow.
    """

    def __init__(self):
        self.name = "mock-tumor-detector"
        self.version = "0.1.0"

    def predict(self, slide_id: str) -> List[Dict]:
        """
        Génère 3-5 détections aléatoires.

        Returns:
            List of predictions with random bboxes.
        """
        num_predictions = random.randint(3, 5)
        predictions = []

        for i in range(num_predictions):
            predictions.append({
                "class": "tumor",
                "confidence": random.uniform(0.7, 0.95),
                "bbox": {
                    "x": random.randint(1000, 10000),
                    "y": random.randint(1000, 10000),
                    "width": random.randint(200, 500),
                    "height": random.randint(200, 500)
                }
            })

        return predictions
```

**Critères de succès:**
- [ ] ML Service déployable localement (Docker)
- [ ] Endpoint `/api/ml/inference` fonctionnel (modèle mock)
- [ ] Intégration avec Viewer Service (API call)

### 3.2 Tâche 2.1.2: Génération Heatmap (1 semaine)

**Implémentation `services/heatmap_generator.py`:**

```python
# backend/ml-service/services/heatmap_generator.py

import numpy as np
from PIL import Image
import cv2
from typing import List, Dict, Tuple

class HeatmapGenerator:
    """
    Génère heatmap de confiance depuis prédictions.

    Approche:
    1. Créer image vide (résolution slide / downsample)
    2. Pour chaque prédiction, dessiner bbox avec intensité = confidence
    3. Appliquer blur gaussien pour smoothing
    4. Colormap (viridis, jet, etc.)
    5. Sauvegarder PNG semi-transparent
    """

    def __init__(self, resolution: str = "medium"):
        """
        Args:
            resolution: "low" (1/64), "medium" (1/16), "high" (1/4)
        """
        self.resolution = resolution
        self.downsamples = {
            "low": 64,
            "medium": 16,
            "high": 4
        }

    def generate(
        self,
        predictions: List[Dict],
        slide_dimensions: Tuple[int, int],
        output_path: str
    ) -> str:
        """
        Génère heatmap PNG.

        Args:
            predictions: Liste prédictions avec bbox et confidence
            slide_dimensions: (width, height) niveau 0
            output_path: Chemin PNG de sortie

        Returns:
            Chemin fichier généré
        """
        downsample = self.downsamples[self.resolution]
        width, height = slide_dimensions
        heatmap_width = width // downsample
        heatmap_height = height // downsample

        # Créer heatmap vide
        heatmap = np.zeros((heatmap_height, heatmap_width), dtype=np.float32)

        # Dessiner prédictions
        for pred in predictions:
            bbox = pred["bbox"]
            confidence = pred["confidence"]

            # Convertir coords niveau 0 → coords heatmap
            x1 = bbox["x"] // downsample
            y1 = bbox["y"] // downsample
            x2 = (bbox["x"] + bbox["width"]) // downsample
            y2 = (bbox["y"] + bbox["height"]) // downsample

            # Remplir bbox avec confidence
            heatmap[y1:y2, x1:x2] = np.maximum(
                heatmap[y1:y2, x1:x2],
                confidence
            )

        # Blur gaussien (smoothing)
        heatmap = cv2.GaussianBlur(heatmap, (15, 15), 0)

        # Appliquer colormap
        heatmap_uint8 = (heatmap * 255).astype(np.uint8)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Convertir BGR → RGB
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

        # Ajouter canal alpha (semi-transparent)
        alpha = (heatmap * 128).astype(np.uint8)  # 50% transparent max
        heatmap_rgba = np.dstack([heatmap_color, alpha])

        # Sauvegarder PNG
        img = Image.fromarray(heatmap_rgba, mode='RGBA')
        img.save(output_path)

        return output_path
```

**Critères de succès:**
- [ ] Heatmap PNG généré depuis prédictions mock
- [ ] Heatmap semi-transparent (overlay sur slide)
- [ ] Performance acceptable (<2s pour génération)

### 3.3 Tâche 2.1.3: Intégration Frontend (1 semaine)

**Fichiers créés:**
- `frontend/src/components/MLOverlay.js` (overlay heatmap)
- `frontend/src/state/MLStore.js` (state ML results)

**Implémentation `MLOverlay.js`:**

```javascript
// frontend/src/components/MLOverlay.js

import OpenSeadragon from 'openseadragon';

/**
 * MLOverlay - Affiche heatmap ML sur viewer.
 *
 * Utilise OpenSeadragon overlay pour superposer heatmap PNG.
 */
export class MLOverlay {
  constructor(viewer) {
    this.viewer = viewer;
    this.overlay = null;
  }

  /**
   * Affiche heatmap.
   *
   * @param {string} heatmapUrl - URL vers heatmap PNG
   * @param {number} opacity - Opacité (0-1)
   */
  show(heatmapUrl, opacity = 0.7) {
    // Supprimer overlay existant
    this.hide();

    // Créer overlay
    const element = document.createElement('div');
    element.className = 'ml-heatmap-overlay';
    element.style.backgroundImage = `url(${heatmapUrl})`;
    element.style.backgroundSize = 'cover';
    element.style.opacity = opacity;
    element.style.pointerEvents = 'none';

    // Ajouter au viewer (couvre toute la slide)
    this.viewer.addOverlay({
      element: element,
      location: new OpenSeadragon.Rect(0, 0, 1, 1)  // Normalized coords
    });

    this.overlay = element;
  }

  /**
   * Cache heatmap.
   */
  hide() {
    if (this.overlay) {
      this.viewer.removeOverlay(this.overlay);
      this.overlay = null;
    }
  }

  /**
   * Toggle visibilité.
   */
  toggle() {
    if (this.overlay) {
      this.hide();
    } else {
      // Re-show last heatmap (TODO: stocker URL)
    }
  }
}
```

**Intégration dans `Viewer.js`:**

```javascript
// frontend/src/components/Viewer.js (modifications)

import { MLOverlay } from './MLOverlay.js';

export function initViewer(elementId) {
  // ... existing code ...

  // Créer ML overlay
  const mlOverlay = new MLOverlay(viewer);

  // Expose API
  viewer.__mlOverlay = mlOverlay;

  return viewer;
}

// Nouveau: charger ML results
export async function loadMLResults(viewer, slideId) {
  const response = await fetch(`/api/ml/inference`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      slide_id: slideId,
      tags: ['generic']  // TODO: tags depuis UI
    })
  });

  if (!response.ok) {
    throw new Error('ML inference failed');
  }

  const result = await response.json();

  // Afficher heatmap
  if (result.heatmap_url) {
    viewer.__mlOverlay.show(result.heatmap_url);
  }

  return result;
}
```

**UI Controls:**

```html
<!-- Ajouter dans viewer UI -->
<div class="ml-controls">
  <button id="ml-run-btn" class="ml-button">
    🤖 Run AI Detection
  </button>
  <button id="ml-toggle-btn" class="ml-button" disabled>
    👁️ Toggle Heatmap
  </button>
  <input
    type="range"
    id="ml-opacity-slider"
    min="0"
    max="100"
    value="70"
    disabled
  />
</div>
```

**Critères de succès:**
- [ ] Bouton "Run AI Detection" fonctionnel
- [ ] Heatmap affiché en overlay (semi-transparent)
- [ ] Toggle visibilité heatmap
- [ ] Slider opacité fonctionnel

---

## 4. Résumé et Prochaines Étapes

### 4.1 Livrables Phase 2.0 (Préparation)

| Livrable | Statut | Critère Validation |
|----------|--------|---------------------|
| StorageProvider abstraction | ✅ | Tests passent, backward compatible |
| Configuration management | ✅ | Aucune config hardcodée |
| API versioning | ✅ | v1/v2 accessibles |
| Tests unitaires >80% | ✅ | CI/CD vert, coverage report |
| State management frontend | ✅ | Stores fonctionnels, tests passent |

### 4.2 Livrables Phase 2.1 (ML Prototype)

| Livrable | Statut | Critère Validation |
|----------|--------|---------------------|
| ML Service (mock) | 🔄 | Inference endpoint fonctionnel |
| Heatmap generator | 🔄 | PNG généré, overlay affiché |
| Frontend integration | 🔄 | Bouton "Run AI" fonctionnel |

### 4.3 Prochaines Étapes

1. **Validation Phase 2.0** (cette semaine)
   - Review code refactoring
   - Valider tests coverage
   - Merger dans `develop` branch

2. **Démarrage Phase 2.1** (semaine prochaine)
   - Setup ML Service Docker
   - Implémenter modèle mock
   - Créer heatmap generator

3. **Planning Phase 2.2+** (dans 2 semaines)
   - Feedback loop MVP
   - PACS integration POC
   - Storage abstraction S3

---

**Auteur:** VarunaPoC Team (Lead Architecte)
**Version:** 3.0.0
**Date:** 2025-12-31
