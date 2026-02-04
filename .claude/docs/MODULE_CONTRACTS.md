# Module Contracts - Interfaces et Contrats d'API

**Version:** 3.0.0
**Date:** 2025-12-31
**Complément:** ARCHITECTURE_V3.md

---

## Objectif

Ce document définit les **contrats d'interface** entre modules de l'architecture V3. Un bug dans le module X ne doit **jamais** casser le module Y grâce à des interfaces claires et des contrats stricts.

**Principe:** Design by Contract (DbC) - chaque module expose une API stable, testable, et documentée.

---

## 1. Storage Provider Interface

### 1.1 Contrat Abstrait

```python
# backend/viewer-service/services/storage/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, BinaryIO
from pathlib import Path
from pydantic import BaseModel

class SlideMetadata(BaseModel):
    """Métadonnées slide (agnostique du format)."""
    slide_id: str
    name: str
    format: str  # "MRXS", "BIF", "SVS", etc.
    dimensions: tuple[int, int]  # (width, height) niveau 0
    level_count: int
    level_dimensions: List[tuple[int, int]]
    vendor: Optional[str] = None
    tags: List[str] = []  # Pour routage ML
    storage_provider: str  # "filesystem", "s3", "pacs"

class StorageProvider(ABC):
    """
    Interface abstraite pour backends de storage.

    Implémentations:
    - FilesystemStorageProvider (Phase 1 compatible)
    - S3StorageProvider (MinIO)
    - PacsStorageProvider (DICOM C-MOVE)

    Garanties:
    - Toutes méthodes async (non-blocking)
    - Lever FileNotFoundError si slide inexistant
    - Retourner types Pydantic (validation auto)
    """

    @abstractmethod
    async def list_slides(
        self,
        path: str = "/",
        recursive: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[SlideMetadata]:
        """
        Liste slides dans un chemin (hiérarchique ou récursif).

        Args:
            path: Chemin relatif depuis racine storage
            recursive: Si True, scan tous sous-dossiers
            tags: Filtre par tags (optionnel)

        Returns:
            Liste de SlideMetadata

        Raises:
            FileNotFoundError: Si path n'existe pas
            PermissionError: Si accès interdit
        """
        pass

    @abstractmethod
    async def get_slide_path(self, slide_id: str) -> Path:
        """
        Retourne chemin local vers slide.

        Pour storage distant (S3, PACS), télécharge dans cache local.

        Args:
            slide_id: ID unique slide (MD5 ou UUID)

        Returns:
            Path vers fichier local

        Raises:
            FileNotFoundError: Si slide_id inexistant
        """
        pass

    @abstractmethod
    async def get_metadata(self, slide_id: str) -> SlideMetadata:
        """
        Extrait métadonnées slide (sans ouvrir avec OpenSlide).

        Utilise cache si disponible.

        Args:
            slide_id: ID unique slide

        Returns:
            SlideMetadata

        Raises:
            FileNotFoundError: Si slide_id inexistant
        """
        pass

    @abstractmethod
    async def store_slide(
        self,
        file: BinaryIO,
        metadata: Dict,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Stocke nouvelle slide dans storage.

        Args:
            file: Fichier binaire slide
            metadata: Métadonnées (patient info, acquisition date, etc.)
            tags: Tags pour routage ML (optionnel)

        Returns:
            slide_id (UUID généré)

        Raises:
            ValueError: Si format non supporté
        """
        pass

    @abstractmethod
    async def delete_slide(self, slide_id: str) -> bool:
        """
        Supprime slide (soft delete ou hard delete selon config).

        Args:
            slide_id: ID slide à supprimer

        Returns:
            True si supprimé, False si déjà absent

        Raises:
            PermissionError: Si utilisateur n'a pas droits
        """
        pass
```

### 1.2 Implémentation Filesystem (Phase 1 Compatible)

```python
# backend/viewer-service/services/storage/filesystem.py

from .base import StorageProvider, SlideMetadata
from services.slide_scanner import scan_slides_directory, get_slide_path_by_id
from services.format_detector import FormatDetector
from pathlib import Path
from typing import List, Optional

class FilesystemStorageProvider(StorageProvider):
    """
    Implémentation filesystem (compatible Phase 1).

    Configuration:
        SLIDES_ROOT: Path racine /Slides
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.detector = FormatDetector()

    async def list_slides(
        self,
        path: str = "/",
        recursive: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[SlideMetadata]:
        """Liste slides dans dossier (réutilise code existant)."""

        # Utiliser slide_scanner.py existant
        slides = scan_slides_directory()

        # Convertir en SlideMetadata
        results = []
        for slide in slides:
            metadata = SlideMetadata(
                slide_id=slide["id"],
                name=slide["name"],
                format=slide["format"],
                dimensions=(0, 0),  # TODO: extraire si disponible
                level_count=0,
                level_dimensions=[],
                storage_provider="filesystem",
                tags=slide.get("tags", [])
            )
            results.append(metadata)

        # Filtrer par tags si spécifié
        if tags:
            results = [s for s in results if any(t in s.tags for t in tags)]

        return results

    async def get_slide_path(self, slide_id: str) -> Path:
        """Retourne chemin local (direct, pas de download)."""
        path = get_slide_path_by_id(slide_id)
        if not path:
            raise FileNotFoundError(f"Slide {slide_id} not found")
        return Path(path)

    async def get_metadata(self, slide_id: str) -> SlideMetadata:
        """Extrait métadonnées (wrapper slide_loader.py)."""
        from services.slide_loader import get_slide_metadata

        path = await self.get_slide_path(slide_id)
        raw_metadata = get_slide_metadata(str(path))

        return SlideMetadata(
            slide_id=slide_id,
            name=path.name,
            format=raw_metadata.get("format", "unknown"),
            dimensions=tuple(raw_metadata["dimensions"]),
            level_count=raw_metadata["level_count"],
            level_dimensions=raw_metadata["level_dimensions"],
            vendor=raw_metadata.get("vendor"),
            storage_provider="filesystem",
            tags=[]  # TODO: extraire depuis DB ou fichier sidecar
        )

    async def store_slide(
        self,
        file: BinaryIO,
        metadata: Dict,
        tags: Optional[List[str]] = None
    ) -> str:
        """Stocke slide dans /Slides (upload)."""
        # TODO: implémenter upload
        raise NotImplementedError("Upload not implemented in Phase 1")

    async def delete_slide(self, slide_id: str) -> bool:
        """Supprime slide (soft delete)."""
        # TODO: implémenter soft delete
        raise NotImplementedError("Delete not implemented in Phase 1")
```

### 1.3 Implémentation S3 (Phase 2)

```python
# backend/viewer-service/services/storage/s3.py

import aioboto3
from .base import StorageProvider, SlideMetadata
from pathlib import Path
import tempfile

class S3StorageProvider(StorageProvider):
    """
    Implémentation S3/MinIO.

    Configuration:
        S3_ENDPOINT: URL endpoint (ex: https://minio.chu-ucl.local)
        S3_BUCKET: Nom bucket (ex: wsi-slides)
        S3_ACCESS_KEY: Access key
        S3_SECRET_KEY: Secret key
    """

    def __init__(self, endpoint: str, bucket: str, access_key: str, secret_key: str):
        self.endpoint = endpoint
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.cache_dir = Path(tempfile.gettempdir()) / "varuna_cache"
        self.cache_dir.mkdir(exist_ok=True)

    async def list_slides(
        self,
        path: str = "/",
        recursive: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[SlideMetadata]:
        """Liste objets S3 avec prefix."""

        session = aioboto3.Session()
        async with session.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        ) as s3:
            # Lister objets avec prefix
            prefix = path.lstrip("/")
            response = await s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                Delimiter="/" if not recursive else ""
            )

            results = []
            for obj in response.get("Contents", []):
                key = obj["Key"]
                # Extraire métadonnées depuis tags S3
                tags_response = await s3.get_object_tagging(Bucket=self.bucket, Key=key)
                obj_tags = [t["Value"] for t in tags_response["TagSet"]]

                # Filtrer par tags si spécifié
                if tags and not any(t in obj_tags for t in tags):
                    continue

                # Construire SlideMetadata (métadonnées complètes dans tags S3)
                metadata = SlideMetadata(
                    slide_id=key,  # S3 key = slide_id
                    name=Path(key).name,
                    format="unknown",  # TODO: extraire depuis metadata
                    dimensions=(0, 0),
                    level_count=0,
                    level_dimensions=[],
                    storage_provider="s3",
                    tags=obj_tags
                )
                results.append(metadata)

            return results

    async def get_slide_path(self, slide_id: str) -> Path:
        """Télécharge slide depuis S3 vers cache local."""

        cache_path = self.cache_dir / slide_id
        if cache_path.exists():
            # Cache hit
            return cache_path

        # Cache miss - télécharger
        session = aioboto3.Session()
        async with session.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        ) as s3:
            await s3.download_file(self.bucket, slide_id, str(cache_path))

        return cache_path

    # ... autres méthodes similaires
```

---

## 2. ML Service Interface

### 2.1 API REST Contract

#### 2.1.1 POST /api/ml/inference

**Request:**

```json
{
  "slide_id": "abc123",
  "tags": ["breast_cancer", "high_priority"],
  "roi": {  // Optionnel: Region of Interest
    "x": 1000,
    "y": 1000,
    "width": 5000,
    "height": 5000,
    "level": 0
  },
  "options": {
    "confidence_threshold": 0.85,  // Optionnel: override default
    "return_heatmap": true,
    "heatmap_resolution": "medium"  // "low", "medium", "high"
  }
}
```

**Response (200 OK):**

```json
{
  "inference_id": "inf_xyz789",
  "slide_id": "abc123",
  "model_name": "breast-tumor-detector-v2",
  "model_version": "3",
  "predictions": [
    {
      "class": "tumor",
      "confidence": 0.92,
      "bbox": {
        "x": 1500,
        "y": 2000,
        "width": 300,
        "height": 250
      },
      "metadata": {
        "grade": "high",
        "size_mm": 2.5
      }
    }
  ],
  "heatmap_url": "/api/ml/heatmaps/inf_xyz789.png",
  "processing_time_ms": 4523,
  "created_at": "2026-01-15T14:30:00Z"
}
```

**Erreurs:**

- `404`: Slide not found
- `400`: Invalid tags or ROI
- `503`: ML service unavailable
- `500`: Inference error

#### 2.1.2 POST /api/ml/feedback

**Request:**

```json
{
  "inference_id": "inf_xyz789",
  "pathologist_id": "path_001",
  "corrections": [
    {
      "prediction_index": 0,
      "correction_type": "false_positive",  // "false_positive", "false_negative", "refinement"
      "corrected_class": null,  // Si false_positive
      "corrected_bbox": null,
      "notes": "Artifact, not tumor"
    }
  ]
}
```

**Response (200 OK):**

```json
{
  "feedback_id": "fb_456",
  "status": "accepted",
  "retraining_triggered": false,  // True si seuil atteint
  "message": "Feedback recorded. 78/100 corrections needed for retraining."
}
```

#### 2.1.3 GET /api/ml/models

**Response:**

```json
{
  "models": [
    {
      "name": "breast-tumor-detector-v2",
      "version": "3",
      "tags_supported": ["breast_cancer"],
      "status": "production",
      "accuracy": 0.94,
      "created_at": "2025-12-01T10:00:00Z",
      "deployed_at": "2026-01-01T08:00:00Z"
    },
    {
      "name": "lung-classifier-v1",
      "version": "2",
      "tags_supported": ["lung_cancer"],
      "status": "shadow",  // A/B testing (shadow mode)
      "accuracy": 0.89,
      "created_at": "2025-11-15T12:00:00Z",
      "deployed_at": "2025-12-20T14:00:00Z"
    }
  ]
}
```

### 2.2 Pydantic Models (Contract Validation)

```python
# backend/ml-service/models/inference.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime

class ROI(BaseModel):
    """Region of Interest (optionnel)."""
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    level: int = Field(0, ge=0)

class InferenceOptions(BaseModel):
    """Options inference."""
    confidence_threshold: float = Field(0.85, ge=0.0, le=1.0)
    return_heatmap: bool = True
    heatmap_resolution: str = Field("medium", regex="^(low|medium|high)$")

class InferenceRequest(BaseModel):
    """Request inference."""
    slide_id: str = Field(..., min_length=1)
    tags: List[str] = Field(..., min_items=1)
    roi: Optional[ROI] = None
    options: InferenceOptions = InferenceOptions()

    @validator("tags")
    def validate_tags(cls, v):
        """Valide tags supportés."""
        supported_tags = ["breast_cancer", "lung_cancer", "colon_cancer", "generic"]
        for tag in v:
            if tag not in supported_tags:
                raise ValueError(f"Unsupported tag: {tag}")
        return v

class BoundingBox(BaseModel):
    """Bounding box prédiction."""
    x: int
    y: int
    width: int
    height: int

class Prediction(BaseModel):
    """Prédiction individuelle."""
    class_: str = Field(..., alias="class")  # "class" est mot-clé Python
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    metadata: Dict = {}

class InferenceResponse(BaseModel):
    """Response inference."""
    inference_id: str
    slide_id: str
    model_name: str
    model_version: str
    predictions: List[Prediction]
    heatmap_url: Optional[str] = None
    processing_time_ms: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 3. PACS Plugin Interface

### 3.1 DICOM Query API

#### 3.1.1 POST /api/pacs/query

**Request:**

```json
{
  "query_type": "worklist",  // "worklist", "study", "series"
  "filters": {
    "patient_id": "12345",  // Optionnel
    "patient_name": "*DUPONT*",  // Wildcards supportés
    "modality": "SM",  // Slide Microscopy
    "study_date": "20260101-20260131"  // Range format DICOM
  },
  "limit": 50
}
```

**Response:**

```json
{
  "results": [
    {
      "patient_id": "12345",
      "patient_name": "DUPONT^JEAN",
      "study_instance_uid": "1.2.3.4.5.6.7.8.9",
      "series_instance_uid": "1.2.3.4.5.6.7.8.9.1",
      "modality": "SM",
      "study_date": "20260115",
      "number_of_images": 1,
      "description": "Breast biopsy H&E"
    }
  ],
  "total_count": 1
}
```

#### 3.1.2 POST /api/pacs/retrieve

**Request:**

```json
{
  "study_instance_uid": "1.2.3.4.5.6.7.8.9",
  "series_instance_uid": "1.2.3.4.5.6.7.8.9.1",
  "destination": "local"  // "local" ou "storage" (S3)
}
```

**Response (202 Accepted):**

```json
{
  "retrieval_id": "retr_abc123",
  "status": "pending",
  "estimated_time_seconds": 30
}
```

**GET /api/pacs/retrieve/{retrieval_id} (polling status):**

```json
{
  "retrieval_id": "retr_abc123",
  "status": "completed",  // "pending", "downloading", "completed", "failed"
  "slide_id": "slide_xyz789",  // Disponible après completion
  "slide_path": "/cache/pacs/slide_xyz789.dcm"
}
```

### 3.2 DICOM Store API

#### 3.2.1 POST /api/pacs/store

**Request (multipart/form-data):**

```
POST /api/pacs/store
Content-Type: multipart/form-data

file: [DICOM file binary]
patient_id: "12345"
patient_name: "DUPONT^JEAN"
study_description: "Breast biopsy H&E"
```

**Response:**

```json
{
  "store_id": "store_def456",
  "status": "success",
  "study_instance_uid": "1.2.3.4.5.6.7.8.9.2",
  "message": "Slide stored successfully to PACS"
}
```

---

## 4. Frontend State Contracts

### 4.1 ViewerStore (State Management)

```javascript
// frontend/src/state/ViewerStore.js

/**
 * ViewerStore - State management pour viewers.
 *
 * Contract:
 * - Immutable updates (pas de mutation directe)
 * - Actions documentées (add, remove, update)
 * - Events émis sur changements (via EventBus)
 */

class ViewerStore {
  constructor() {
    this.state = {
      viewers: new Map(),  // Map<viewerId, ViewerState>
      activeViewerId: null,
      syncEnabled: false
    };

    this.listeners = new Set();
  }

  /**
   * Ajoute viewer au store.
   *
   * @param {string} viewerId - ID unique viewer
   * @param {Object} initialState - État initial
   * @returns {void}
   * @emits viewer:added
   */
  addViewer(viewerId, initialState) {
    if (this.state.viewers.has(viewerId)) {
      throw new Error(`Viewer ${viewerId} already exists`);
    }

    const viewerState = {
      id: viewerId,
      slideId: initialState.slideId || null,
      viewport: initialState.viewport || { x: 0, y: 0, zoom: 1 },
      annotations: [],
      mlResults: null,
      isLoading: false,
      error: null
    };

    // Immutable update
    const newViewers = new Map(this.state.viewers);
    newViewers.set(viewerId, viewerState);

    this.state = {
      ...this.state,
      viewers: newViewers,
      activeViewerId: this.state.activeViewerId || viewerId
    };

    this.emit('viewer:added', { viewerId, state: viewerState });
  }

  /**
   * Met à jour viewport viewer.
   *
   * @param {string} viewerId - ID viewer
   * @param {Object} viewport - Nouveau viewport {x, y, zoom}
   * @returns {void}
   * @emits viewport:changed
   */
  updateViewport(viewerId, viewport) {
    const viewer = this.state.viewers.get(viewerId);
    if (!viewer) {
      throw new Error(`Viewer ${viewerId} not found`);
    }

    const updatedViewer = {
      ...viewer,
      viewport: { ...viewer.viewport, ...viewport }
    };

    const newViewers = new Map(this.state.viewers);
    newViewers.set(viewerId, updatedViewer);

    this.state = {
      ...this.state,
      viewers: newViewers
    };

    this.emit('viewport:changed', { viewerId, viewport: updatedViewer.viewport });

    // Si sync enabled, propager aux autres viewers
    if (this.state.syncEnabled) {
      this.syncViewports(viewerId, updatedViewer.viewport);
    }
  }

  /**
   * Synchronise viewport avec autres viewers.
   *
   * @private
   * @param {string} sourceViewerId - Viewer source
   * @param {Object} viewport - Viewport à propager
   * @returns {void}
   */
  syncViewports(sourceViewerId, viewport) {
    for (const [viewerId, viewer] of this.state.viewers) {
      if (viewerId !== sourceViewerId) {
        this.updateViewport(viewerId, viewport);
      }
    }
  }

  /**
   * Subscribe aux changements.
   *
   * @param {Function} listener - Callback (event, data) => void
   * @returns {Function} Unsubscribe function
   */
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Émet event aux listeners.
   *
   * @private
   */
  emit(event, data) {
    for (const listener of this.listeners) {
      listener(event, data);
    }
  }
}

// Singleton instance
export const viewerStore = new ViewerStore();
```

### 4.2 AnnotationStore

```javascript
// frontend/src/state/AnnotationStore.js

/**
 * AnnotationStore - State management pour annotations.
 *
 * Contract:
 * - Annotations GeoJSON (standard)
 * - Sync avec backend via API
 * - Événements temps réel (WebSocket)
 */

class AnnotationStore {
  constructor() {
    this.state = {
      annotations: new Map(),  // Map<slideId, Annotation[]>
      pendingSync: new Set(),  // IDs annotations non synchronisées
      collaborators: new Map()  // Map<userId, {name, color, cursor}>
    };
  }

  /**
   * Ajoute annotation locale (pas encore synchronisée).
   *
   * @param {string} slideId - ID slide
   * @param {Object} annotation - Annotation GeoJSON
   * @returns {string} Annotation ID
   * @emits annotation:added
   */
  addAnnotation(slideId, annotation) {
    const annotationId = `ann_${Date.now()}_${Math.random()}`;

    const annotationWithId = {
      id: annotationId,
      slideId,
      userId: this.getCurrentUserId(),
      createdAt: new Date().toISOString(),
      isAiGenerated: false,
      ...annotation
    };

    const slideAnnotations = this.state.annotations.get(slideId) || [];
    slideAnnotations.push(annotationWithId);

    this.state.annotations.set(slideId, slideAnnotations);
    this.state.pendingSync.add(annotationId);

    this.emit('annotation:added', { slideId, annotation: annotationWithId });

    // Sync avec backend (async, fire-and-forget)
    this.syncAnnotation(annotationWithId).catch(err => {
      console.error('Failed to sync annotation:', err);
      this.emit('annotation:sync-failed', { annotationId, error: err });
    });

    return annotationId;
  }

  /**
   * Synchronise annotation avec backend.
   *
   * @private
   * @param {Object} annotation - Annotation à synchroniser
   * @returns {Promise<void>}
   */
  async syncAnnotation(annotation) {
    const response = await fetch('/api/annotations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(annotation)
    });

    if (!response.ok) {
      throw new Error(`Sync failed: ${response.statusText}`);
    }

    this.state.pendingSync.delete(annotation.id);
    this.emit('annotation:synced', { annotationId: annotation.id });
  }

  /**
   * Reçoit annotation depuis WebSocket (collaborateur).
   *
   * @param {Object} annotation - Annotation reçue
   * @returns {void}
   * @emits annotation:received
   */
  receiveRemoteAnnotation(annotation) {
    const slideAnnotations = this.state.annotations.get(annotation.slideId) || [];

    // Éviter duplicata
    if (slideAnnotations.some(a => a.id === annotation.id)) {
      return;
    }

    slideAnnotations.push(annotation);
    this.state.annotations.set(annotation.slideId, slideAnnotations);

    this.emit('annotation:received', { annotation });
  }

  // ... autres méthodes (update, delete, etc.)
}

export const annotationStore = new AnnotationStore();
```

---

## 5. WebSocket Protocol (Collaboration)

### 5.1 Connection

**Client → Server:**

```json
{
  "type": "connect",
  "userId": "user_123",
  "sessionId": "session_abc",
  "slideId": "slide_xyz"
}
```

**Server → Client:**

```json
{
  "type": "connected",
  "sessionId": "session_abc",
  "collaborators": [
    {
      "userId": "user_456",
      "name": "Dr. Dupont",
      "color": "#4a9eff",
      "cursor": { "x": 1000, "y": 2000 }
    }
  ]
}
```

### 5.2 Viewport Sync

**Client → Server (broadcast):**

```json
{
  "type": "viewport:update",
  "sessionId": "session_abc",
  "viewport": {
    "x": 1500,
    "y": 2500,
    "zoom": 0.5
  }
}
```

**Server → Other Clients:**

```json
{
  "type": "viewport:update",
  "userId": "user_123",
  "viewport": {
    "x": 1500,
    "y": 2500,
    "zoom": 0.5
  }
}
```

### 5.3 Annotation Sync

**Client → Server:**

```json
{
  "type": "annotation:add",
  "sessionId": "session_abc",
  "annotation": {
    "id": "ann_123",
    "slideId": "slide_xyz",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[...]]
    },
    "label": "tumor",
    "confidence": null
  }
}
```

**Server → Other Clients:**

```json
{
  "type": "annotation:add",
  "userId": "user_123",
  "annotation": { ... }
}
```

---

## 6. Testing Contracts

### 6.1 Unit Tests (Pytest)

**Chaque module DOIT avoir:**

```python
# backend/viewer-service/tests/unit/test_storage_provider.py

import pytest
from services.storage.filesystem import FilesystemStorageProvider
from services.storage.base import SlideMetadata

@pytest.fixture
def storage_provider(tmp_path):
    """Fixture: storage provider avec données test."""
    return FilesystemStorageProvider(root_dir=tmp_path)

class TestFilesystemStorageProvider:
    """Tests contrat StorageProvider (filesystem implementation)."""

    @pytest.mark.asyncio
    async def test_list_slides_empty_directory(self, storage_provider):
        """GIVEN dossier vide, WHEN list_slides(), THEN retourne liste vide."""
        slides = await storage_provider.list_slides()
        assert slides == []

    @pytest.mark.asyncio
    async def test_get_slide_path_not_found(self, storage_provider):
        """GIVEN slide inexistant, WHEN get_slide_path(), THEN FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await storage_provider.get_slide_path("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_metadata_returns_valid_pydantic_model(self, storage_provider, sample_slide):
        """GIVEN slide valide, WHEN get_metadata(), THEN retourne SlideMetadata valide."""
        metadata = await storage_provider.get_metadata(sample_slide.id)

        # Validation automatique Pydantic
        assert isinstance(metadata, SlideMetadata)
        assert metadata.slide_id == sample_slide.id
        assert metadata.dimensions[0] > 0
        assert metadata.level_count > 0

    # ... autres tests (tags filter, recursive scan, etc.)
```

### 6.2 Integration Tests

```python
# backend/tests/integration/test_viewer_ml_integration.py

import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestViewerMLIntegration:
    """Tests intégration Viewer Service ↔ ML Service."""

    @pytest.mark.asyncio
    async def test_inference_workflow(self, viewer_client: AsyncClient, ml_client: AsyncClient):
        """
        GIVEN slide chargé dans viewer,
        WHEN request inference via ML service,
        THEN résultats affichés dans viewer.
        """

        # 1. Upload slide via viewer service
        slide_response = await viewer_client.post(
            "/api/slides/upload",
            files={"file": sample_slide_file},
            data={"tags": "breast_cancer"}
        )
        assert slide_response.status_code == 201
        slide_id = slide_response.json()["slide_id"]

        # 2. Request inference via ML service
        inference_response = await ml_client.post(
            "/api/ml/inference",
            json={
                "slide_id": slide_id,
                "tags": ["breast_cancer"]
            }
        )
        assert inference_response.status_code == 200
        inference_data = inference_response.json()

        # 3. Vérifier résultats
        assert inference_data["model_name"] == "breast-tumor-detector-v2"
        assert len(inference_data["predictions"]) > 0
        assert inference_data["heatmap_url"] is not None

        # 4. Récupérer heatmap
        heatmap_response = await ml_client.get(inference_data["heatmap_url"])
        assert heatmap_response.status_code == 200
        assert heatmap_response.headers["content-type"] == "image/png"
```

---

## 7. Versioning et Breaking Changes

### 7.1 API Versioning Strategy

**Approche:** URI versioning (`/api/v1/`, `/api/v2/`)

**Règles:**
1. **v1 (stable):** Aucun breaking change, seulement ajouts compatibles
2. **v2 (next):** Breaking changes autorisés, migration progressive
3. **Deprecation:** Annoncer 6 mois avant suppression v1

**Exemple migration:**

```python
# backend/viewer-service/api/v1/slides.py (deprecated)

@router.get("/slides/{slide_id}/info", deprecated=True)
async def get_slide_info_v1(slide_id: str):
    """
    DEPRECATED: Use /api/v2/slides/{slide_id}/metadata instead.
    Will be removed in v3.0.0 (August 2026).
    """
    # ... implementation ...

# backend/viewer-service/api/v2/slides.py (new)

@router.get("/slides/{slide_id}/metadata")
async def get_slide_metadata_v2(slide_id: str):
    """
    Retourne métadonnées slide (format amélioré avec tags).

    Breaking changes depuis v1:
    - Ajout champ "tags" (List[str])
    - Renommage "format" → "format_string"
    - Suppression champ "has_companions" (redondant avec "companion_dirs")
    """
    # ... implementation ...
```

### 7.2 Frontend API Client Versioning

```javascript
// frontend/src/services/ApiService.js

class ApiService {
  constructor() {
    this.apiVersion = 'v2';  // Config centralisée
    this.baseUrl = import.meta.env.VITE_API_BASE_URL;
  }

  /**
   * Fetch slide metadata (utilise version API configurée).
   */
  async getSlideMetadata(slideId) {
    const url = `${this.baseUrl}/api/${this.apiVersion}/slides/${slideId}/metadata`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Fallback vers v1 si v2 indisponible (migration progressive).
   */
  async getSlideMetadataWithFallback(slideId) {
    try {
      return await this.getSlideMetadata(slideId);
    } catch (err) {
      console.warn('v2 API failed, falling back to v1:', err);

      // Fallback v1
      const urlV1 = `${this.baseUrl}/api/v1/slides/${slideId}/info`;
      const response = await fetch(urlV1);
      return response.json();
    }
  }
}
```

---

## Conclusion

Ces contrats garantissent:

1. **Isolation:** Un bug dans ML Service ne casse pas Viewer Service
2. **Testabilité:** Chaque interface testable indépendamment (mocks faciles)
3. **Évolutivité:** Nouveaux storage providers sans changer code métier
4. **Documentation:** Contrats = documentation exécutable (Pydantic, JSDoc)

**Prochaines étapes:**
1. Implémenter interfaces abstraites (StorageProvider, etc.)
2. Écrire tests contrat pour chaque interface
3. CI/CD: tests contrat obligatoires avant merge
4. Documentation auto-générée (Sphinx, Swagger)

---

**Auteur:** VarunaPoC Team (Lead Architecte)
**Version:** 3.0.0
**Date:** 2025-12-31
