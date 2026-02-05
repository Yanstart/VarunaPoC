# ML Integration with Slideflow

**VarunaPoC - Machine Learning Integration Architecture**

---

## Vue d'Ensemble

Ce document décrit l'intégration de **Slideflow** (https://github.com/slideflow/slideflow) dans VarunaPoC pour fournir des capacités d'intelligence artificielle sur les lames histologiques.

**Slideflow** est le framework open-source de référence pour deep learning sur whole slide images (WSI), développé par le Mahmood Lab (Harvard Medical School).

**Pourquoi Slideflow?**
- Support natif des gigapixel images (WSI)
- Multiple Instance Learning (MIL) pour classification à l'échelle slide
- Self-Supervised Learning (SSL) pour pre-training sans annotations
- Normalisation de coloration (Macenko, StainGAN, Reinhard)
- Explainability intégrée (heatmaps, uncertainty quantification)
- Production-ready (batch inference, GPU/CPU, model serving)

---

## Architecture

### Principes

1. **Abstraction via Protocol**: Interface `MLProvider` découple l'API du provider ML
2. **Pluggable**: Facile d'ajouter d'autres providers (TorchVision, Hugging Face, etc.)
3. **Dégradation gracieuse**: Fallback CPU si GPU indisponible, mock si Slideflow absent
4. **Lazy loading**: Modèles chargés à la demande (pas au startup)
5. **Privacy-first**: Pas de données patient dans logs, support federated learning

### Composants

```
backend/
├── core/
│   ├── interfaces/
│   │   └── ml_provider.py          # Interface MLProvider (Protocol)
│   └── exceptions/
│       └── ml_exceptions.py        # Exceptions ML custom
├── services/
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── tag_extractor.py        # Existant
│   │   ├── tag_router.py           # Existant
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── slideflow_provider.py   # Implémentation Slideflow
│   │   │   └── mock_provider.py        # Mock pour tests/dev
│   │   ├── model_registry.py       # Registry de modèles
│   │   └── inference_service.py    # Service orchestration
│   └── models/
│       └── (modèles pré-entraînés via DVC/MLflow)
└── routes/
    └── ml.py                        # API endpoints ML
```

---

## 1. Interface MLProvider

**Fichier**: `backend/core/interfaces/ml_provider.py`

Interface abstraite définissant le contrat pour tout provider ML.

```python
from typing import Protocol, Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass

@dataclass
class PredictionResult:
    """Résultat de prédiction ML."""
    prediction_class: str
    confidence: float
    probabilities: Dict[str, float]
    uncertainty: Optional[float] = None
    execution_time_ms: Optional[float] = None
    model_id: str = ""
    slide_id: str = ""

@dataclass
class FeatureExtractionResult:
    """Résultat d'extraction de features."""
    embeddings: np.ndarray  # Shape: (N, D) - N patches, D dimensions
    coordinates: List[Tuple[int, int]]  # (x, y) pour chaque patch
    slide_id: str = ""
    model_id: str = ""

@dataclass
class HeatmapResult:
    """Résultat de génération de heatmap."""
    heatmap: np.ndarray  # Shape: (H, W) - valeurs [0, 1]
    slide_dimensions: Tuple[int, int]  # (width, height)
    resolution_level: int
    slide_id: str = ""

class MLProvider(Protocol):
    """
    Interface pour providers ML (Slideflow, TorchVision, etc.).

    Toute implémentation doit fournir ces méthodes.
    """

    def load_model(self, model_path: str, model_config: Dict) -> None:
        """
        Charge un modèle depuis artefact.

        Args:
            model_path: Chemin vers modèle (local ou MLflow URI)
            model_config: Configuration (device, batch_size, etc.)
        """
        ...

    def predict(
        self,
        slide_path: str,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Prédiction sur slide ou région.

        Args:
            slide_path: Chemin vers lame
            region: (x, y, width, height) optionnel

        Returns:
            Résultat de prédiction avec incertitude
        """
        ...

    def extract_features(
        self,
        slide_path: str,
        tile_size: int = 224,
        overlap: int = 0
    ) -> FeatureExtractionResult:
        """
        Extraction de features (embeddings) pour MIL.

        Args:
            slide_path: Chemin vers lame
            tile_size: Taille des patches (px)
            overlap: Chevauchement entre patches (px)

        Returns:
            Features + coordonnées pour chaque patch
        """
        ...

    def generate_heatmap(
        self,
        slide_path: str,
        prediction_class: str,
        resolution_level: int = 2
    ) -> HeatmapResult:
        """
        Génère heatmap d'attention pour classe prédite.

        Args:
            slide_path: Chemin vers lame
            prediction_class: Classe pour laquelle générer heatmap
            resolution_level: Niveau de résolution (0=max)

        Returns:
            Heatmap normalisée [0, 1]
        """
        ...

    def get_model_info(self) -> Dict:
        """
        Retourne metadata du modèle chargé.

        Returns:
            {
                "model_id": str,
                "version": str,
                "task_type": str,
                "classes": List[str],
                "input_size": Tuple[int, int],
                "device": str,
                "metrics": Dict
            }
        """
        ...
```

**Références:**
- Protocol Pattern: https://peps.python.org/pep-0544/
- Dependency Inversion Principle (SOLID)

---

## 2. Slideflow Provider

**Fichier**: `backend/services/ml/providers/slideflow_provider.py`

Implémentation concrète utilisant Slideflow.

### Features Principales

#### 2.1. Initialisation avec Lazy Loading

```python
class SlideflowProvider:
    """Provider ML basé sur Slideflow."""

    def __init__(self, device: str = "auto"):
        self.device = self._detect_device(device)
        self.model = None
        self.model_config = {}
        self._slideflow_available = self._check_slideflow()

    def _check_slideflow(self) -> bool:
        """Vérifie disponibilité Slideflow."""
        try:
            import slideflow as sf
            return True
        except ImportError:
            logger.warning("Slideflow not installed - ML features disabled")
            return False

    def _detect_device(self, device: str) -> str:
        """Détecte GPU disponible ou fallback CPU."""
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return device
```

**Pourquoi ce pattern?**

L'application démarre même si Slideflow n'est pas installé. Les routes ML retournent simplement un message informatif au lieu de crasher. C'est critique en dev où tous les devs n'ont pas forcément besoin de ML.

#### 2.2. Chargement de Modèles

```python
def load_model(self, model_path: str, model_config: Dict) -> None:
    """
    Charge modèle Slideflow.

    Supports:
    - Modèles locaux (.pt, .h5)
    - MLflow URIs (models:/model_name/version)
    - Hugging Face Hub
    """
    if not self._slideflow_available:
        raise MLProviderError("Slideflow not installed")

    import slideflow as sf

    # Déterminer type de source
    if model_path.startswith("models:/"):
        # MLflow model
        model = self._load_from_mlflow(model_path)
    elif model_path.startswith("hf://"):
        # Hugging Face Hub
        model = self._load_from_huggingface(model_path)
    else:
        # Local file
        model = sf.model.load(model_path)

    # Configuration device
    if self.device == "cuda":
        model = model.cuda()

    self.model = model
    self.model_config = model_config

    logger.info(f"Model loaded: {model_path} on {self.device}")
```

**Références:**
- MLflow Model Registry: https://mlflow.org/docs/latest/model-registry.html
- Hugging Face Hub: https://huggingface.co/docs/huggingface_hub

#### 2.3. Inference avec Uncertainty

```python
def predict(
    self,
    slide_path: str,
    region: Optional[Tuple[int, int, int, int]] = None,
    num_mc_samples: int = 10
) -> PredictionResult:
    """
    Prédiction avec Monte Carlo Dropout pour uncertainty.

    Process:
    1. Tiling slide en patches
    2. Forward passes multiples avec dropout
    3. Aggregation par vote ou attention
    4. Calcul uncertainty (variance des prédictions)
    """
    import slideflow as sf
    import time

    start = time.time()

    # Load slide
    wsi = sf.WSI(slide_path, tile_px=self.model_config.get("tile_size", 224))

    # Extract tiles (avec region si spécifiée)
    if region:
        tiles = wsi.build_generator(region=region)
    else:
        tiles = wsi.build_generator()

    # Monte Carlo Dropout (multiple forward passes)
    predictions_mc = []
    for _ in range(num_mc_samples):
        pred = self.model.predict(tiles, training=True)  # Keep dropout active
        predictions_mc.append(pred)

    # Aggregation
    predictions_mc = np.array(predictions_mc)
    mean_pred = predictions_mc.mean(axis=0)
    uncertainty = predictions_mc.var(axis=0).mean()  # Epistemic uncertainty

    # Classe prédite
    pred_class_idx = np.argmax(mean_pred)
    pred_class = self.model.config["classes"][pred_class_idx]
    confidence = mean_pred[pred_class_idx]

    # Probabilities dict
    probabilities = {
        cls: float(mean_pred[i])
        for i, cls in enumerate(self.model.config["classes"])
    }

    elapsed_ms = (time.time() - start) * 1000

    return PredictionResult(
        prediction_class=pred_class,
        confidence=float(confidence),
        probabilities=probabilities,
        uncertainty=float(uncertainty),
        execution_time_ms=elapsed_ms,
        model_id=self.model_config.get("model_id", "unknown"),
        slide_id=Path(slide_path).stem
    )
```

**Pourquoi Monte Carlo Dropout?**

En médical AI, la confiance binaire (92% = cancer) est cliniquement insuffisante. Il faut quantifier l'incertitude du modèle:
- **Haute confiance + basse incertitude** → Prédiction fiable
- **Haute confiance + haute incertitude** → Modèle surconfiant (danger!)
- **Basse confiance + haute incertitude** → Demander validation expert

**Références:**
- Gal & Ghahramani (2016): "Dropout as a Bayesian Approximation"
- Komura & Ishikawa (2024): "ML in Pathology"

#### 2.4. Feature Extraction pour MIL

```python
def extract_features(
    self,
    slide_path: str,
    tile_size: int = 224,
    overlap: int = 0
) -> FeatureExtractionResult:
    """
    Extraction features pour Multiple Instance Learning.

    Returns embeddings (N patches, D dimensions) pour chaque patch.
    Ces features peuvent ensuite être agrégées avec attention mechanism.
    """
    import slideflow as sf

    wsi = sf.WSI(slide_path, tile_px=tile_size, overlap=overlap)

    # Extract features via backbone (sans classification head)
    features_extractor = self.model.get_feature_extractor()

    embeddings = []
    coordinates = []

    for tile, (x, y) in wsi.build_generator(return_coords=True):
        # Forward pass through backbone
        features = features_extractor(tile)
        embeddings.append(features.cpu().numpy())
        coordinates.append((x, y))

    embeddings = np.vstack(embeddings)  # (N, D)

    return FeatureExtractionResult(
        embeddings=embeddings,
        coordinates=coordinates,
        slide_id=Path(slide_path).stem,
        model_id=self.model_config.get("model_id", "unknown")
    )
```

**Pourquoi MIL?**

Une WSI fait 100,000×100,000 pixels. Impossible de la passer entièrement dans un CNN. Solution:
1. Découper en 1000 patches de 224×224
2. Extraire features pour chaque patch (via backbone pré-entraîné)
3. Agréger avec attention mechanism (CLAM, DSMIL)
4. Classifier au niveau slide

**Références:**
- Ilse et al. (2018): "Attention-based Deep MIL"
- Lu et al. (2021): "Data-efficient Computational Pathology"

#### 2.5. Heatmap Generation

```python
def generate_heatmap(
    self,
    slide_path: str,
    prediction_class: str,
    resolution_level: int = 2
) -> HeatmapResult:
    """
    Génère heatmap d'attention montrant régions influençant prédiction.

    Méthodes supportées:
    - Grad-CAM (gradient-based)
    - Attention weights (si modèle MIL)
    - Occlusion sensitivity
    """
    import slideflow as sf

    wsi = sf.WSI(slide_path, tile_px=224)

    # Génération heatmap
    heatmap_generator = sf.grad.GradientHeatmap(
        model=self.model,
        target_class=prediction_class,
        method="gradcam"  # ou "attention", "occlusion"
    )

    heatmap = heatmap_generator.generate(
        wsi,
        level=resolution_level,
        batch_size=32
    )

    # Normalisation [0, 1]
    heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())

    return HeatmapResult(
        heatmap=heatmap,
        slide_dimensions=wsi.dimensions,
        resolution_level=resolution_level,
        slide_id=Path(slide_path).stem
    )
```

**Pourquoi les heatmaps?**

Explainability critique en médical AI. Le pathologiste doit voir:
- Quelles régions ont influencé la décision
- Le modèle se concentre-t-il sur les bonnes structures?
- Y a-t-il des artefacts ou biais?

**Références:**
- Selvaraju et al. (2017): "Grad-CAM: Visual Explanations"
- CLAIM Guidelines (2020): "AI Reporting in Medical Imaging"

---

## 3. API Endpoints

**Fichier**: `backend/routes/ml.py`

API REST pour consommer services ML.

### 3.1. Prediction Endpoint

```python
@router.post("/predict/{slide_id}")
async def predict_slide(
    slide_id: str,
    region: Optional[RegionRequest] = None,
    model_id: Optional[str] = None
):
    """
    Prédiction ML sur slide ou région.

    Process:
    1. Récupérer slide depuis DB
    2. Extraire tags (organ, stain) via TagExtractor
    3. Router vers modèle approprié via TagRouter
    4. Inference via SlideflowProvider
    5. Stocker résultat en DB (ml_predictions)

    Returns:
        {
            "prediction_class": "gleason_4",
            "confidence": 0.92,
            "uncertainty": 0.05,
            "probabilities": {"gleason_3": 0.05, "gleason_4": 0.92, ...},
            "model_id": "gleason_grading_v2",
            "execution_time_ms": 2340
        }
    """
```

### 3.2. Feature Extraction Endpoint

```python
@router.post("/features/{slide_id}")
async def extract_features(
    slide_id: str,
    tile_size: int = 224,
    model_id: Optional[str] = None
):
    """
    Extraction features pour MIL.

    Use cases:
    - Pre-compute embeddings pour active learning
    - Similarity search entre slides
    - Clustering pour dataset exploration

    Returns:
        {
            "slide_id": "abc123",
            "embeddings": [...],  # (N, D) array
            "coordinates": [(x1, y1), ...],
            "embedding_dim": 1024,
            "num_patches": 1500
        }
    """
```

### 3.3. Heatmap Endpoint

```python
@router.get("/heatmap/{slide_id}")
async def get_heatmap(
    slide_id: str,
    prediction_class: str,
    resolution_level: int = 2
):
    """
    Génère heatmap d'explainability.

    Returns heatmap as image (PNG) avec overlay sur slide.

    Headers:
        Content-Type: image/png
    """
```

### 3.4. Batch Processing

```python
@router.post("/batch/predict")
async def batch_predict(
    slide_ids: List[str],
    background_tasks: BackgroundTasks
):
    """
    Batch inference asynchrone.

    Pour gros volumes (re-training, validation, etc.)

    Process:
    1. Créer job en DB (batch_jobs table)
    2. Lancer processing en background
    3. Retourner job_id
    4. Client poll /batch/status/{job_id}

    Returns:
        {
            "job_id": "batch_abc123",
            "status": "queued",
            "total_slides": 150,
            "estimated_time_minutes": 45
        }
    """
```

---

## 4. Configuration

### 4.1. Model Registry

**Fichier**: `config/ml_models.yaml`

Registry des modèles disponibles.

```yaml
models:
  - model_id: "gleason_grading_v2"
    model_name: "Gleason Grading (Prostate)"
    version: "2.1.0"
    provider: "slideflow"
    model_path: "models:/gleason_grading/production"
    task_type: "classification"
    classes: ["gleason_3", "gleason_4", "gleason_5"]

    # Hardware
    device: "cuda"  # ou "cpu", "auto"
    batch_size: 32

    # Inference params
    tile_size: 224
    overlap: 0
    num_mc_samples: 10  # Pour uncertainty

    # Performance
    reference_metrics:
      accuracy: 0.94
      auc_roc: 0.97
      inference_time_ms: 2000

    # Tags routing (lien avec TagRouter)
    required_tags:
      organ: "prostate"
      stain: "H&E"
      task: "grading"

    # Clinical info
    clinical_use: "Gleason grading pour diagnostic cancer prostate"
    validation_dataset: "PANDA challenge 2020"
    trained_by: "CHU UCL ML Team"
    approved_by: "Dr. Dupont (Pathologist)"

  - model_id: "tumor_detection_generic"
    model_name: "Generic Tumor Detection"
    version: "1.0.0"
    provider: "slideflow"
    model_path: "models:/tumor_detection/production"
    task_type: "segmentation"
    device: "auto"
    # Fallback model (pas de required_tags)
```

### 4.2. Runtime Configuration

**Variables d'environnement** (`.env`):

```bash
# ML Configuration
ML_ENABLED=true
ML_PROVIDER=slideflow  # ou "mock" pour dev
ML_DEVICE=auto  # cuda, cpu, auto
ML_MODEL_CACHE_DIR=/app/models
ML_MAX_BATCH_SIZE=64

# MLflow Integration
MLFLOW_TRACKING_URI=http://mlflow.chu-ucl.local:5000
MLFLOW_EXPERIMENT_NAME=varuna_pathology_ml

# GPU Settings
CUDA_VISIBLE_DEVICES=0  # GPU index si multi-GPU
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Feature flags
ML_UNCERTAINTY_ENABLED=true
ML_HEATMAP_ENABLED=true
ML_BATCH_PROCESSING_ENABLED=true
```

---

## 5. Database Schema

**Tables ML** (à ajouter à `database/schema.sql`):

```sql
-- ML Predictions storage
CREATE TABLE ml_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slide_id VARCHAR(255) NOT NULL REFERENCES slides(slide_id),
    model_id VARCHAR(100) NOT NULL,

    -- Results
    prediction_class VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    uncertainty FLOAT,
    probabilities JSONB,  -- {"class1": 0.1, "class2": 0.9}

    -- Context
    region JSONB,  -- {x, y, width, height} si prédiction régionale
    tags JSONB,  -- Tags utilisés pour routing

    -- Performance
    execution_time_ms INTEGER,
    device VARCHAR(20),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),

    -- Indexes
    INDEX idx_slide_id (slide_id),
    INDEX idx_model_id (model_id),
    INDEX idx_prediction_class (prediction_class),
    INDEX idx_created_at (created_at)
);

-- Features storage (pour MIL)
CREATE TABLE slide_features (
    feature_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slide_id VARCHAR(255) NOT NULL REFERENCES slides(slide_id),
    model_id VARCHAR(100) NOT NULL,

    embeddings BYTEA,  -- Numpy array serialized
    coordinates JSONB,  -- [(x1, y1), (x2, y2), ...]
    embedding_dim INTEGER,
    num_patches INTEGER,

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_slide_features (slide_id, model_id)
);

-- Heatmaps storage
CREATE TABLE ml_heatmaps (
    heatmap_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES ml_predictions(prediction_id),
    slide_id VARCHAR(255) NOT NULL,

    heatmap_path VARCHAR(500),  -- Chemin S3/local
    resolution_level INTEGER,
    generation_method VARCHAR(50),  -- "gradcam", "attention", "occlusion"

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_slide_heatmap (slide_id)
);

-- Batch jobs tracking
CREATE TABLE ml_batch_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,  -- "predict", "extract_features"

    status VARCHAR(20) NOT NULL,  -- "queued", "running", "completed", "failed"
    total_slides INTEGER,
    processed_slides INTEGER DEFAULT 0,
    failed_slides INTEGER DEFAULT 0,

    config JSONB,  -- Job configuration
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_by VARCHAR(255),

    INDEX idx_job_status (status, created_at)
);
```

---

## 6. Tests

### 6.1. Unit Tests avec Mocks

**Fichier**: `tests/services/ml/test_slideflow_provider.py`

```python
import pytest
from unittest.mock import Mock, patch
from services.ml.providers.slideflow_provider import SlideflowProvider

@pytest.fixture
def mock_slideflow():
    """Mock Slideflow pour tests sans installation."""
    with patch("services.ml.providers.slideflow_provider.sf") as mock_sf:
        yield mock_sf

def test_predict_without_slideflow():
    """Test que provider échoue gracieusement si Slideflow absent."""
    provider = SlideflowProvider()
    provider._slideflow_available = False

    with pytest.raises(MLProviderError, match="Slideflow not installed"):
        provider.predict("test_slide.mrxs")

def test_predict_with_mock(mock_slideflow):
    """Test inference avec Slideflow mocké."""
    provider = SlideflowProvider()
    provider._slideflow_available = True

    # Mock model response
    mock_model = Mock()
    mock_model.predict.return_value = np.array([0.1, 0.9])
    mock_model.config = {"classes": ["benign", "malignant"]}
    provider.model = mock_model

    result = provider.predict("test_slide.mrxs")

    assert result.prediction_class == "malignant"
    assert result.confidence == pytest.approx(0.9, 0.01)
    assert result.uncertainty is not None
```

### 6.2. Integration Tests

**Fichier**: `tests/integration/test_ml_pipeline.py`

```python
@pytest.mark.integration
@pytest.mark.skipif(not SLIDEFLOW_AVAILABLE, reason="Slideflow not installed")
def test_full_ml_pipeline(test_slide_path):
    """
    Test pipeline complet:
    1. Tag extraction
    2. Model routing
    3. Inference
    4. Heatmap generation
    """
    # 1. Extract tags
    extractor = TagExtractor()
    tags = extractor.extract_tags(test_slide_path, "MRXS")
    assert tags["organ"] is not None

    # 2. Route to model
    router = TagRouter()
    route = router.route(tags)
    assert route is not None

    # 3. Inference
    provider = SlideflowProvider()
    provider.load_model(route.model_path, route.__dict__)
    result = provider.predict(test_slide_path)

    assert result.confidence > 0.0
    assert result.uncertainty is not None

    # 4. Heatmap
    heatmap = provider.generate_heatmap(
        test_slide_path,
        result.prediction_class
    )
    assert heatmap.heatmap.shape[0] > 0
```

---

## 7. Déploiement

### 7.1. Installation Slideflow

**Dockerfile** (extension):

```dockerfile
# Add ML dependencies
RUN pip install slideflow[tf] \
    && pip install mlflow boto3 dvc

# Download pre-trained models (via DVC)
COPY .dvc/ /app/.dvc/
RUN dvc pull models/
```

**Requirements** (extension de `requirements.txt`):

```
# ML Core
slideflow==2.2.0
tensorflow==2.14.0  # ou pytorch==2.1.0
mlflow==2.9.0

# Preprocessing
opencv-python==4.8.1
scikit-image==0.22.0

# Explainability
captum==0.7.0  # For Grad-CAM

# Optional (federated learning)
flower==1.6.0
```

### 7.2. GPU Support

**Docker Compose** (`docker-compose.gpu.yml`):

```yaml
services:
  backend:
    image: varuna-backend-gpu
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - ML_DEVICE=cuda
      - CUDA_VISIBLE_DEVICES=0
```

**Vérification GPU**:

```bash
# Dans container
python -c "import torch; print(torch.cuda.is_available())"
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

### 7.3. Monitoring

**Prometheus metrics** (à ajouter à `monitoring.py`):

```python
from prometheus_client import Counter, Histogram, Gauge

ml_predictions_total = Counter(
    'ml_predictions_total',
    'Total ML predictions',
    ['model_id', 'prediction_class']
)

ml_inference_duration_seconds = Histogram(
    'ml_inference_duration_seconds',
    'ML inference duration',
    ['model_id']
)

ml_uncertainty_gauge = Gauge(
    'ml_uncertainty_latest',
    'Latest uncertainty value',
    ['model_id']
)

ml_gpu_memory_usage = Gauge(
    'ml_gpu_memory_bytes',
    'GPU memory usage'
)
```

---

## 8. Workflow Exemples

### 8.1. Inference Simple

```python
# API Client
response = requests.post(
    "http://localhost:8000/api/ml/predict/slide_abc123"
)

result = response.json()
print(f"Prédiction: {result['prediction_class']}")
print(f"Confiance: {result['confidence']:.2%}")
print(f"Incertitude: {result['uncertainty']:.3f}")

# Récupérer heatmap
heatmap_url = f"/api/ml/heatmap/slide_abc123?class={result['prediction_class']}"
```

### 8.2. Active Learning

```python
# 1. Extraire features pour toutes slides
for slide_id in slide_ids:
    features = api.extract_features(slide_id)
    store_in_db(features)

# 2. Calculer uncertainty sur batch
predictions = api.batch_predict(slide_ids)

# 3. Sélectionner top N incertain
uncertain_slides = sorted(
    predictions,
    key=lambda p: p["uncertainty"],
    reverse=True
)[:100]

# 4. Envoyer pour annotation expert
for slide in uncertain_slides:
    send_to_label_studio(slide)
```

### 8.3. Feedback Loop

```python
# 1. Expert corrige prédiction dans UI
feedback = {
    "prediction_id": "pred_abc123",
    "original_class": "gleason_3",
    "corrected_class": "gleason_4",
    "pathologist_id": "dr_dupont"
}

api.submit_feedback(feedback)

# 2. Feedback automatiquement ajouté à dataset
# 3. Monitoring vérifie seuils retraining
if retraining_monitor.should_trigger():
    # 4. Pipeline Airflow déclenché
    trigger_retraining_pipeline("gleason_grading_v2")
```

---

## 9. Sécurité & Privacy

### 9.1. Data Protection

- **Pas de PHI dans logs**: Anonymisation slide_id
- **Chiffrement au repos**: Models et predictions chiffrés (AES-256)
- **Audit trail**: Toutes prédictions loggées avec timestamp

### 9.2. Federated Learning

Pour collaboration multi-sites sans partage données:

```python
# Site A, B, C entraînent localement
# Seuls gradients partagés (pas les données)

from flower import fl

class PathologyClient(fl.client.NumPyClient):
    def fit(self, parameters, config):
        # Train on local data
        model.set_weights(parameters)
        model.fit(local_training_data)
        return model.get_weights(), len(local_data), {}

fl.client.start_numpy_client(
    server_address="federated.chu-ucl.local:8080",
    client=PathologyClient()
)
```

**Références:**
- Flower: https://flower.dev/
- TFF: https://www.tensorflow.org/federated

---

## 10. Roadmap

### Phase 1 (Actuel): Foundation ✅
- Architecture modulaire
- TagExtractor + TagRouter

### Phase 2: Slideflow Integration 🚧
- MLProvider interface
- SlideflowProvider implementation
- API endpoints (predict, features, heatmap)
- Tests

### Phase 3: Production Features
- Batch processing
- Active learning
- Drift detection
- MLflow integration

### Phase 4: Advanced ML
- Federated learning
- Multi-modal fusion (H&E + IHC)
- Foundation models (UNI, Virchow)

---

## Références

### Frameworks
- **Slideflow**: https://github.com/slideflow/slideflow
- **CLAM**: https://github.com/mahmoodlab/CLAM (MIL reference)
- **MLflow**: https://mlflow.org/
- **DVC**: https://dvc.org/

### Papers
- Pantanowitz et al. (2024): "Annotation Quality in Digital Pathology"
- Komura & Ishikawa (2024): "ML in Pathology"
- Ilse et al. (2018): "Attention-based Deep MIL"
- Gal & Ghahramani (2016): "Dropout as Bayesian Approximation"

### Standards
- **FDA SaMD**: https://www.fda.gov/medical-devices/software-medical-device-samd
- **CLAIM Guidelines**: https://pubs.rsna.org/doi/10.1148/ryai.2020200029
- **DICOM WSI**: https://www.dicomstandard.org/

---

**Version**: 1.0
**Date**: 2026-02-05
**Auteur**: ML Architecture Team
**Contact**: varuna-ml@chu-ucl.be
