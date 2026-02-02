# VarunaPoC Backend - Architecture Diagrams

**Date:** 2025-12-31
**Version:** 1.0
**Auteur:** Backend Tech Lead

---

## 1. Vue d'Ensemble: Clean Architecture en Couches

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ FastAPI Endpoints (REST API)                             │  │
│  │  - health.py (/)                                         │  │
│  │  - slides.py (/api/v1/slides)                           │  │
│  │  - visualization.py (/api/v1/slides/{id}/tiles)        │  │
│  │  - tags.py (/api/v1/tags) [MLOps]                      │  │
│  │  - feedback.py (/api/v1/feedback) [MLOps]              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Middleware                                               │  │
│  │  - Error Handler (exceptions → HTTP codes)              │  │
│  │  - Logging Middleware                                   │  │
│  │  - Metrics Middleware (Prometheus)                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Use Cases (Orchestration)                                │  │
│  │  - ListSlidesUseCase                                     │  │
│  │  - GetSlideMetadataUseCase                              │  │
│  │  - GetTileUseCase                                       │  │
│  │  - AddTagUseCase [MLOps]                                │  │
│  │  - SubmitFeedbackUseCase [MLOps]                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            │ DTOs (Data Transfer Objects)        │
│                            ▼                                     │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Domain Operations
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                             │
│        (AUCUNE dépendance vers couches externes)                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Entities (Objets métier avec identité)                  │  │
│  │  - Slide (id, name, path, dimensions, levels)           │  │
│  │  - Tag (id, name, category, color) [MLOps]              │  │
│  │  - Feedback (id, rating, comment) [MLOps]               │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Value Objects (Objets immuables)                        │  │
│  │  - SlideId (MD5 hash validation)                        │  │
│  │  - TileCoordinates (level, col, row)                    │  │
│  │  - Level0Coordinates (x, y)                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Repository Interfaces (Ports)                           │  │
│  │  - SlideRepository (find_by_id, find_all, get_metadata) │  │
│  │  - TagRepository [MLOps]                                │  │
│  │  - FeedbackRepository [MLOps]                           │  │
│  │  - CacheRepository                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Domain Services (Logique métier pure)                   │  │
│  │  - SlideService (validation, calculs)                   │  │
│  │  - TileService (conversion coordonnées)                 │  │
│  │  - TagService [MLOps]                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Domain Exceptions                                        │  │
│  │  - SlideNotFoundError                                   │  │
│  │  - TileOutOfBoundsError                                 │  │
│  │  - PathTraversalError                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             ▲
                             │ Implements Interfaces
                             │
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                          │
│           (Adaptateurs - Implémentations concrètes)             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ OpenSlide Adapter                                        │  │
│  │  - OpenSlideAdapter (implements SlideRepository)        │  │
│  │  - FormatDetector (détection multi-format)              │  │
│  │  - TileExtractor (extraction tuiles OpenSlide)          │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Filesystem Adapter                                       │  │
│  │  - FileScanner (scan dossiers)                          │  │
│  │  - PathValidator (sécurité path traversal)              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Cache Adapter                                            │  │
│  │  - MemoryCache (implements CacheRepository)             │  │
│  │  - RedisCache (Phase 2)                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Database Adapter [MLOps]                                 │  │
│  │  - SQLAlchemy Models (Tag, Feedback, AuditEvent)        │  │
│  │  - TagRepositoryImpl (implements TagRepository)         │  │
│  │  - FeedbackRepositoryImpl                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ PACS Adapter [Phase 2+]                                  │  │
│  │  - TelemisClient (HTTP client Telemis API)              │  │
│  │  - DICOMAdapter (conversion DICOM ↔ Slide)             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼ Accès externe
                    ┌──────────────────────┐
                    │  External Systems    │
                    │  - OpenSlide DLL     │
                    │  - Filesystem        │
                    │  - Redis (cache)     │
                    │  - PostgreSQL (DB)   │
                    │  - PACS Telemis      │
                    └──────────────────────┘
```

---

## 2. Flux de Dépendances (Dependency Flow)

**Règle d'or:** Les dépendances pointent TOUJOURS vers l'intérieur (vers le Domain)

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  ┌──────────────┐          ┌──────────────┐          │
│  │ Presentation │   uses   │ Application  │          │
│  │   Layer      │─────────>│    Layer     │          │
│  └──────────────┘          └──────────────┘          │
│         │                         │                   │
│         │                         │                   │
│         │      uses               │  uses             │
│         └─────────┬───────────────┘                   │
│                   │                                   │
│                   ▼                                   │
│           ┌──────────────┐                            │
│           │    Domain    │                            │
│           │     Layer    │  <──────── CORE MÉTIER    │
│           └──────────────┘           PAS DE          │
│                   ▲                 DÉPENDANCES       │
│                   │                  EXTERNES         │
│                   │                                   │
│                   │ implements                        │
│                   │                                   │
│         ┌─────────────────┐                           │
│         │ Infrastructure  │                           │
│         │      Layer      │                           │
│         └─────────────────┘                           │
│                   │                                   │
│                   ▼                                   │
│          External Systems                             │
│                                                        │
└────────────────────────────────────────────────────────┘

KEY:
─────> Dépendance directe (import)
```

**Exemples concrets:**

```python
# ✅ CORRECT: Presentation dépend de Application
# presentation/api/v1/slides.py
from application.use_cases.get_slide_metadata import GetSlideMetadataUseCase

# ✅ CORRECT: Application dépend de Domain
# application/use_cases/get_slide_metadata.py
from domain.repositories.slide_repository import SlideRepository

# ✅ CORRECT: Infrastructure implémente Domain
# infrastructure/openslide/openslide_adapter.py
from domain.repositories.slide_repository import SlideRepository
class OpenSlideAdapter(SlideRepository):  # implements interface
    pass

# ❌ INCORRECT: Domain ne doit JAMAIS dépendre de Infrastructure
# domain/repositories/slide_repository.py
from infrastructure.openslide.openslide_adapter import OpenSlideAdapter  # INTERDIT!

# ❌ INCORRECT: Domain ne doit JAMAIS dépendre de Presentation
# domain/services/slide_service.py
from presentation.schemas.slide_schema import SlideSchema  # INTERDIT!
```

---

## 3. Workflow: Récupération Métadonnées Slide

**Exemple concret:** `GET /api/v1/slides/{slide_id}/info`

```
┌──────────────┐
│   Frontend   │
│  (Browser)   │
└──────┬───────┘
       │ HTTP GET /api/v1/slides/a1b2c3d4e5f6/info
       ▼
┌──────────────────────────────────────────────────────┐
│ PRESENTATION: FastAPI Endpoint                       │
│ ┌──────────────────────────────────────────────────┐ │
│ │ presentation/api/v1/slides.py                    │ │
│ │                                                  │ │
│ │ @router.get("/{slide_id}/info")                 │ │
│ │ async def get_slide_info(                       │ │
│ │     slide_id: str,                              │ │
│ │     use_case = Depends(get_metadata_use_case)  │ │
│ │ ):                                               │ │
│ │     return await use_case.execute(slide_id)     │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────────────┘
               │
               │ 1. Dependency Injection
               │    use_case = GetSlideMetadataUseCase(repo)
               ▼
┌──────────────────────────────────────────────────────┐
│ APPLICATION: Use Case                                │
│ ┌──────────────────────────────────────────────────┐ │
│ │ application/use_cases/get_slide_metadata.py      │ │
│ │                                                  │ │
│ │ class GetSlideMetadataUseCase:                  │ │
│ │     def __init__(self, repo: SlideRepository):  │ │
│ │         self.repo = repo                        │ │
│ │                                                  │ │
│ │     async def execute(self, slide_id_str):      │ │
│ │         # 2. Valider ID                         │ │
│ │         slide_id = SlideId(slide_id_str)        │ │
│ │                                                  │ │
│ │         # 3. Vérifier existence                 │ │
│ │         slide = await self.repo.find_by_id(id)  │ │
│ │         if not slide:                           │ │
│ │             raise SlideNotFoundError(id)        │ │
│ │                                                  │ │
│ │         # 4. Récupérer métadonnées              │ │
│ │         metadata = await self.repo.get_metadata()│ │
│ │                                                  │ │
│ │         # 5. Retourner DTO                      │ │
│ │         return SlideMetadataDTO(...)            │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────────────┘
               │
               │ 2. Appelle méthode repository
               │    find_by_id(SlideId)
               ▼
┌──────────────────────────────────────────────────────┐
│ DOMAIN: Repository Interface (Port)                  │
│ ┌──────────────────────────────────────────────────┐ │
│ │ domain/repositories/slide_repository.py          │ │
│ │                                                  │ │
│ │ class SlideRepository(ABC):                     │ │
│ │     @abstractmethod                             │ │
│ │     async def find_by_id(self, id: SlideId):    │ │
│ │         pass                                     │ │
│ │                                                  │ │
│ │     @abstractmethod                             │ │
│ │     async def get_metadata(self, id: SlideId):  │ │
│ │         pass                                     │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────────────┘
               │
               │ 3. Implémenté par
               ▼
┌──────────────────────────────────────────────────────┐
│ INFRASTRUCTURE: OpenSlide Adapter                    │
│ ┌──────────────────────────────────────────────────┐ │
│ │ infrastructure/openslide/openslide_adapter.py    │ │
│ │                                                  │ │
│ │ class OpenSlideAdapter(SlideRepository):        │ │
│ │                                                  │ │
│ │     async def find_by_id(self, id: SlideId):    │ │
│ │         # 4a. Chercher dans cache               │ │
│ │         cached = await self.cache.get(f"id:{id}")│ │
│ │         if cached: return Slide(**cached)       │ │
│ │                                                  │ │
│ │         # 4b. Scanner filesystem                │ │
│ │         path = await scanner.find_path(id)      │ │
│ │                                                  │ │
│ │         # 4c. Ouvrir avec OpenSlide             │ │
│ │         slide_obj = openslide.OpenSlide(path)   │ │
│ │         slide = Slide(...)                      │ │
│ │         slide_obj.close()                       │ │
│ │                                                  │ │
│ │         # 4d. Mettre en cache                   │ │
│ │         await self.cache.set(f"id:{id}", slide) │ │
│ │                                                  │ │
│ │         return slide                            │ │
│ │                                                  │ │
│ │     async def get_metadata(self, id: SlideId):  │ │
│ │         slide = await self.find_by_id(id)       │ │
│ │         slide_obj = openslide.OpenSlide(path)   │ │
│ │         metadata = {...}  # Extract OpenSlide   │ │
│ │         slide_obj.close()                       │ │
│ │         return metadata                         │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────────────┘
               │
               │ 5. Accès externe
               ▼
        ┌──────────────┐
        │  OpenSlide   │
        │     DLL      │
        │ (libopenslide│
        │    -0.dll)   │
        └──────┬───────┘
               │
               │ 6. Lit fichiers
               ▼
        ┌──────────────┐
        │  Filesystem  │
        │ /Slides/     │
        │  test.mrxs   │
        │  test/       │
        │   Slidedat   │
        │   Data*.dat  │
        └──────────────┘
```

**Légende:**

- **Dependency Injection (1):** FastAPI injecte `GetSlideMetadataUseCase` avec `OpenSlideAdapter`
- **Validation (2):** Use case valide `slide_id` avec `SlideId` value object
- **Appel Interface (3):** Use case appelle méthode abstraite `find_by_id()`
- **Implémentation (4):** `OpenSlideAdapter` implémente la logique concrète
- **Accès Externe (5-6):** Adapter accède OpenSlide DLL et filesystem

**Flux de retour:**

```
Filesystem → OpenSlide → OpenSlideAdapter → Slide (Entity) →
Use Case → SlideMetadataDTO → FastAPI Endpoint → JSON Response → Frontend
```

---

## 4. Dependency Injection: Wiring Complet

**Comment les dépendances sont injectées**

```
┌────────────────────────────────────────────────────────────┐
│ main.py (Application Startup)                             │
│                                                            │
│ 1. Charger configuration                                  │
│    settings = Settings()  # depuis .env                   │
│                                                            │
│ 2. Créer instance FastAPI                                 │
│    app = FastAPI(...)                                     │
│                                                            │
│ 3. Enregistrer error handlers                             │
│    app.add_exception_handler(DomainException, handler)    │
│                                                            │
│ 4. Inclure routers                                        │
│    app.include_router(slides.router)                      │
└────────────────────────────────────────────────────────────┘
                          │
                          │ FastAPI startup
                          ▼
┌────────────────────────────────────────────────────────────┐
│ presentation/api/dependencies.py                           │
│                                                            │
│ @lru_cache()                                              │
│ def get_cache():                                          │
│     if settings.cache_type == "memory":                   │
│         return MemoryCache()  # Singleton                 │
│     elif settings.cache_type == "redis":                  │
│         return RedisCache()                               │
│                                                            │
│ @lru_cache()                                              │
│ def get_file_scanner():                                   │
│     return FileScanner()  # Singleton                     │
│                                                            │
│ def get_slide_repository(                                 │
│     cache = Depends(get_cache),                           │
│     scanner = Depends(get_file_scanner)                   │
│ ):                                                         │
│     return OpenSlideAdapter(cache, scanner)               │
│                                                            │
│ def get_slide_metadata_use_case(                          │
│     repo = Depends(get_slide_repository)                  │
│ ):                                                         │
│     return GetSlideMetadataUseCase(repo)                  │
└────────────────────────────────────────────────────────────┘
                          │
                          │ Depends()
                          ▼
┌────────────────────────────────────────────────────────────┐
│ presentation/api/v1/slides.py                              │
│                                                            │
│ @router.get("/{slide_id}/info")                           │
│ async def get_slide_info(                                 │
│     slide_id: str,                                        │
│     use_case: GetSlideMetadataUseCase =                   │
│         Depends(get_slide_metadata_use_case)              │
│ ):                                                         │
│     result = await use_case.execute(slide_id)             │
│     return result                                         │
└────────────────────────────────────────────────────────────┘
```

**Graphe de dépendances:**

```
get_slide_info (endpoint)
    │
    └─> get_slide_metadata_use_case (factory)
            │
            └─> GetSlideMetadataUseCase (use case)
                    │
                    └─> get_slide_repository (factory)
                            │
                            ├─> get_cache (singleton)
                            │       └─> MemoryCache
                            │
                            └─> get_file_scanner (singleton)
                                    └─> FileScanner
                                            │
                                            └─> OpenSlideAdapter
```

**Lifecycle:**

- **Singletons** (`@lru_cache()`): Créés UNE FOIS au startup (cache, scanner)
- **Transient** (sans cache): Créés À CHAQUE requête (use cases, repositories)

**Avantages:**

- Testabilité: Remplacer `get_slide_repository` par mock dans tests
- Flexibilité: Changer `MemoryCache` par `RedisCache` via config
- Pas de couplage: Endpoint ne sait pas quelle implémentation il utilise

---

## 5. Architecture MLOps: Extensions Phase 2

**Modules ajoutés pour MLOps**

```
┌──────────────────────────────────────────────────────────┐
│                     PRESENTATION                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │ NEW: /api/v1/tags                                  │  │
│  │  POST   /{slide_id}/tags        (ajouter tag)     │  │
│  │  GET    /{slide_id}/tags        (lister tags)     │  │
│  │  DELETE /{slide_id}/tags/{id}   (supprimer tag)   │  │
│  │                                                    │  │
│  │ NEW: /api/v1/feedback                              │  │
│  │  POST   /{slide_id}/feedback    (soumettre)       │  │
│  │  GET    /{slide_id}/feedback    (lister)          │  │
│  │  GET    /export                 (export CSV ML)   │  │
│  │                                                    │  │
│  │ NEW: /api/v1/ml                                    │  │
│  │  POST   /inference              (inférence)       │  │
│  │  GET    /models                 (lister modèles)  │  │
│  │  GET    /training-data          (export dataset)  │  │
│  │                                                    │  │
│  │ NEW: /api/v1/pacs                                  │  │
│  │  POST   /import                 (import DICOM)    │  │
│  │  POST   /export/{slide_id}      (export PACS)     │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                     APPLICATION                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ NEW Use Cases:                                     │  │
│  │  - AddTagUseCase                                   │  │
│  │  - RemoveTagUseCase                                │  │
│  │  - SubmitFeedbackUseCase                           │  │
│  │  - RunInferenceUseCase                             │  │
│  │  - ImportFromPACSUseCase                           │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                       DOMAIN                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ NEW Entities:                                      │  │
│  │  - Tag (id, name, category, color, created_by)    │  │
│  │  - Feedback (id, rating, comment, coordinates)    │  │
│  │  - MLModel (id, name, version, type)              │  │
│  │  - InferenceResult (predictions, confidence)      │  │
│  │                                                    │  │
│  │ NEW Repositories:                                  │  │
│  │  - TagRepository (add, remove, get_tags)          │  │
│  │  - FeedbackRepository (submit, get_feedback)      │  │
│  │  - MLModelRepository (load_model, run_inference)  │  │
│  │  - PACSRepository (import, export, sync)          │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE                         │
│  ┌────────────────────────────────────────────────────┐  │
│  │ NEW: infrastructure/database/                      │  │
│  │  - SQLAlchemy models (Tag, Feedback, AuditEvent)  │  │
│  │  - TagRepositoryImpl (PostgreSQL)                 │  │
│  │  - FeedbackRepositoryImpl (PostgreSQL)            │  │
│  │                                                    │  │
│  │ NEW: infrastructure/ml/                            │  │
│  │  - ModelLoader (PyTorch/TensorFlow)               │  │
│  │  - InferenceEngine (GPU acceleration)             │  │
│  │  - Preprocessing (image normalization)            │  │
│  │                                                    │  │
│  │ NEW: infrastructure/pacs/                          │  │
│  │  - TelemisClient (HTTP API client)                │  │
│  │  - DICOMAdapter (conversion DICOM ↔ Slide)       │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │     External Systems          │
          │  - PostgreSQL (tags, feedback)│
          │  - PyTorch models (.pth)      │
          │  - PACS Telemis (HTTP API)    │
          └───────────────────────────────┘
```

**Isolation des modules:**

```
slides.py (existant)          tags.py (MLOps)
     │                             │
     ▼                             ▼
SlideRepository           TagRepository
     │                             │
     ▼                             ▼
OpenSlideAdapter          TagRepositoryImpl
     │                             │
     ▼                             ▼
OpenSlide DLL              PostgreSQL

ISOLATION: Erreur dans tags.py ne casse PAS slides.py
```

---

## 6. Testing Strategy: Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Peu de tests (lents, fragiles)
                    │   (Selenium,    │    Testent workflow complet
                    │   Cypress)      │    Frontend + Backend + DB
                    └────────┬────────┘
                             │
                    ┌────────▼────────────┐
                    │ Integration Tests   │  ← Tests moyens (modérés)
                    │ (pytest avec DB,    │    Testent adaptateurs
                    │  OpenSlide réels)   │    Infrastructure + Domain
                    └────────┬────────────┘
                             │
              ┌──────────────▼──────────────────┐
              │        Unit Tests               │  ← Beaucoup (rapides)
              │  (pytest avec mocks)            │    Testent logique pure
              │  Domain + Application Layer     │    Aucune I/O
              └─────────────────────────────────┘
```

**Distribution recommandée:**

- **70% Unit Tests:** Domain entities, value objects, use cases (mocks)
- **20% Integration Tests:** Adapters OpenSlide, database, cache
- **10% E2E Tests:** Endpoints API complets

**Exemples:**

```python
# tests/unit/domain/entities/test_slide.py
def test_slide_get_level_dimensions():
    """Test logique métier pure (rapide, aucune I/O)."""
    slide = Slide(...)
    assert slide.get_level_dimensions(0) == (100000, 80000)

# tests/integration/infrastructure/test_openslide_adapter.py
@pytest.mark.asyncio
async def test_find_by_id_real_file():
    """Test avec vrai fichier OpenSlide (lent, I/O)."""
    adapter = OpenSlideAdapter(...)
    slide = await adapter.find_by_id(SlideId("abc123"))
    assert slide.level_count > 0

# tests/e2e/api/test_slides_api.py
def test_full_workflow():
    """Test workflow complet (très lent, tout le stack)."""
    client = TestClient(app)
    response = client.get("/api/v1/slides/")
    assert response.status_code == 200
```

---

## 7. Déploiement: Docker Multi-Stage

**Architecture conteneurs:**

```
┌──────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                          │
│  ┌────────────────┐  ┌────────────────┐                 │
│  │   Frontend     │  │    Backend     │                 │
│  │  (Vite + Vue)  │  │ (FastAPI)      │                 │
│  │  Port: 8080    │  │ Port: 8000     │                 │
│  └────────┬───────┘  └───────┬────────┘                 │
│           │                   │                          │
│           │                   │ Accède                   │
│           │                   ▼                          │
│           │         ┌─────────────────┐                  │
│           │         │   PostgreSQL    │                  │
│           │         │   (Tags, FB)    │                  │
│           │         │   Port: 5432    │                  │
│           │         └─────────────────┘                  │
│           │                   │                          │
│           │                   │ Cache                    │
│           │                   ▼                          │
│           │         ┌─────────────────┐                  │
│           │         │     Redis       │                  │
│           │         │   (Cache)       │                  │
│           │         │   Port: 6379    │                  │
│           │         └─────────────────┘                  │
│           │                                              │
│           │ HTTP                                         │
│           ▼                                              │
│  ┌────────────────────┐                                  │
│  │      Nginx         │                                  │
│  │  (Reverse Proxy)   │                                  │
│  │   Port: 80/443     │                                  │
│  └────────────────────┘                                  │
│                                                          │
│  Volume: /slides (partagé avec Backend)                 │
└──────────────────────────────────────────────────────────┘
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - SLIDES_ROOT=/slides
      - DATABASE_URL=postgresql://user:pass@postgres:5432/varuna
      - CACHE_TYPE=redis
      - REDIS_URL=redis://redis:6379
    volumes:
      - /path/to/slides:/slides:ro  # Read-only
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - VITE_API_URL=http://backend:8000

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=varuna
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

---

## Conclusion

Cette architecture permet:

1. **Isolation complète:** Erreur dans tags ne casse pas tile serving
2. **Testabilité:** 70% tests unitaires sans I/O
3. **Extensibilité:** Ajout ML, PACS, audit sans refonte
4. **Maintenabilité:** Code clair, responsabilités séparées
5. **Performance:** Cache Redis, pooling DB, async partout

**Prochaine étape:** Commencer migration progressive (Étape 1: Configuration centralisée)
