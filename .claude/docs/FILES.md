# Reference Rapide des Fichiers

**Derniere mise a jour:** 2026-02-12

---

## Frontend Structure

```
frontend/src/
├── main.js                      ★ ENTRY POINT - Routing, init app (HOME/VIEWER/COMPARE)
├── style.css                    ★ CSS imports (order matters)
│
├── core/                        ★ CORE MODULES
│   ├── index.js                 Exports centralises
│   ├── EventBus.js              Pub/Sub singleton (Observer pattern, unsubscribe support)
│   └── Constants.js             Toutes les constantes (Events, API, OSD_CONFIG, etc.)
│
├── viewers/                     ★ VIEWER SYSTEM
│   ├── index.js                 Exports centralises
│   ├── ViewerManager.js         Singleton - gere tous les viewers
│   ├── ViewerFactory.js         Factory - cree les ViewerInstance (presets)
│   ├── ViewerInstance.js        Wrapper OpenSeadragon + tile source DZI
│   ├── ViewerState.js           State machine (IDLE→LOADING→READY→ERROR)
│   └── SyncController.js        Mediator - synchronise pan/zoom multi-viewer
│
├── components/                  ★ UI COMPONENTS
│   ├── index.js                 Exports centralises
│   ├── CompareLayout.js         Layout grille multi-viewers (2x1, 2x2)
│   ├── ViewerPanel.js           Panel unique avec header/actions + tous composants Phase 2
│   ├── SyncControls.js          Barre toggle sync + layout selector
│   ├── FolderBrowser.js         Explorateur de dossiers hierarchique
│   ├── SlideList.js             Grille de tuiles lames
│   ├── AnnotationLayer.js       ★ PHASE 2 - SVG overlay annotations sur OSD
│   ├── DrawingTools.js          ★ PHASE 2 - 5 outils dessin (rect, polygon, point, circle, freehand)
│   ├── LayerManager.js          ★ PHASE 2 - Controle visibilite/opacite annotations
│   ├── DetectionPanel.js        ★ PHASE 2 - Workflow detection auto (label selector, confidence bar)
│   ├── CountingPanel.js         ★ PHASE 2 - Stats temps reel par label/type
│   ├── HeatmapOverlay.js        ★ PHASE 2 - Canvas overlay ML (cached image, coordinate mapping)
│   ├── MLPanel.js               ★ PHASE 2 - Panel analyse ML (predict, heatmap trigger)
│   ├── QualityPanel.js           ★ PHASE 3.2 - Quality metrics panel (kappa, confusion, F1, IoU)
│   ├── LoginPage.js             ★ PHASE 3.1 - OIDC login page
│   ├── UserMenu.js              ★ PHASE 3.1 - User info, role display, logout
│   ├── Home.js                  (legacy, peu utilise)
│   └── Viewer.js                ★ LEGACY WRAPPER - backward compat
│
├── services/                    ★ API LAYER
│   ├── index.js                 Exports centralises
│   ├── ApiService.js            Client API singleton avec cache + quality methods
│   ├── AnnotationStore.js       ★ PHASE 2 - Etat annotations (CRUD, loadStats, computeLocalStats)
│   └── AuthService.js           ★ PHASE 3.1 - OIDC PKCE client (login, logout, refresh)
│
├── utils/                       ★ UTILITIES
│   ├── api.js                   (legacy) - fonctions fetch simples
│   └── coordinates.js           Transformations coordonnees OSD↔OpenSlide
│
└── css/                         ★ STYLES
    ├── variables.css            CSS custom properties (theme)
    ├── base.css                 Reset, scrollbar, utilities
    ├── home.css                 Page d'accueil
    ├── slide-tiles.css          Tuiles de lames
    ├── viewer.css               Page viewer single
    ├── openseadragon.css        Overrides OSD
    ├── login.css                ★ PHASE 3.1 - Login page styles
    ├── user-menu.css            ★ PHASE 3.1 - User menu styles
    ├── quality-panel.css        ★ PHASE 3.2 - Quality panel styles
    └── layouts/
        └── compare-layout.css   Grille multi-viewers, sync controls
```

---

## Backend Structure

```
backend/
├── main.py                      ★ ENTRY POINT - FastAPI app v2.0.0, CORS, lifespan DB
├── config_openslide.py          Configuration DLL OpenSlide (Windows)
│
├── routes/
│   ├── slides.py                ★ API SLIDES (sync def, pas async)
│   │                              /api/slides (list)
│   │                              /api/slides/browse (hierarchique)
│   │                              /api/slides/{id}/info
│   │                              /api/slides/{id}/dzi.json
│   │                              /api/slides/{id}/tiles/{level}/{x}_{y}.jpg
│   │                              /api/slides/{id}/overview
│   │
│   ├── annotations.py           ★ PHASE 2 - CRUD annotations + labels + stats
│   │                              /api/annotations/{slide_id} (GET, POST)
│   │                              /api/annotations/{slide_id}/{id} (PUT, DELETE)
│   │                              /api/annotations/labels (GET, POST)
│   │                              /api/annotations/{slide_id}/stats (GET)
│   │
│   └── ml.py                    ★ PHASE 2 - ML inference endpoints
│                                  /api/ml/heatmap/{slide_id} (Slideflow + Phikon-v2)
│                                  /api/ml/detect/{slide_id} (regions tissulaires)
│                                  /api/ml/predict/{slide_id} (classification + uncertainty)
│
├── services/
│   ├── tile_server.py           ★ CORE - TileServer avec cache LRU (5 slides max)
│   ├── slide_scanner.py         Scan recursif /Slides + cache
│   ├── folder_browser.py        Navigation hierarchique non-recursive
│   ├── format_detector.py       Detection 10+ formats (+ _try_open_slide validation)
│   │
│   ├── detection/               ★ PHASE 2 - Pipeline detection
│   │   ├── __init__.py
│   │   ├── pipeline.py          heatmap → scipy ndimage → skimage contours → shapely → GeoJSON
│   │   └── heatmap_processor.py Traitement heatmaps numpy
│   │
│   └── ml/                      ★ PHASE 2 - Services ML
│       ├── __init__.py
│       ├── slideflow_service.py Integration Slideflow + Phikon-v2 (CUDA)
│       ├── tag_extractor.py     Extraction tags organe/stain depuis metadata
│       └── tag_router.py        Routage ML par tags (config YAML)
│
├── auth/                        ★ PHASE 3.1 - Auth OIDC
│   ├── __init__.py              AUTH_ENABLED flag
│   ├── config.py                OIDC configuration
│   ├── oidc.py                  OIDC PKCE flow
│   ├── jwt_validator.py         JWT RS256/ES256 validation, JWKS cache
│   ├── dependencies.py          FastAPI auth dependencies (require_role)
│   ├── audit.py                 Audit trail (DB + JSON logging)
│   ├── models.py                User/Session ORM models
│   ├── schemas.py               Auth Pydantic schemas
│   ├── routes.py                Auth API endpoints
│   ├── rbac.py                  Role-based access control
│   └── break_glass.py           Emergency access (30min sessions)
│
├── fhir/                        ★ PHASE 3.1 - FHIR R4 Stub
│   ├── __init__.py              FHIR_ENABLED flag
│   ├── resources.py             DiagnosticReport builder
│   ├── routes.py                FHIR endpoints
│   └── patient_context.py       Patient context resolution
│
├── quality/                     ★ PHASE 3.2 - Quality Metrics
│   ├── __init__.py              QUALITY_ENABLED flag
│   ├── config.py                Thresholds, Landis-Koch scale, cache TTL
│   ├── metrics.py               Cohen/Fleiss kappa, F1, confusion matrix (pure functions)
│   ├── schemas.py               Pydantic models for all metric results
│   ├── matching.py              IoU spatial matching (PostGIS) + grid matching
│   ├── services.py              Orchestration (matching + metrics + cache)
│   └── routes.py                7 API endpoints /api/quality/{slide_id}/...
│
├── models/                      ★ PHASE 2+ - ORM SQLAlchemy
│   ├── __init__.py
│   ├── annotation.py            Annotation + AnnotationLabel (PostGIS Geometry)
│   └── quality_report.py        ★ PHASE 3.2 - Quality cache table (JSONB, TTL)
│
├── schemas/                     ★ PHASE 2 - Pydantic validation
│   ├── __init__.py
│   ├── annotation.py            AnnotationCreate/Update/Response schemas
│   ├── geojson.py               GeoJSON Feature/FeatureCollection models
│   └── detection.py             DetectionResult/DetectionRegion schemas
│
├── core/                        ★ PHASE 2 - Infrastructure
│   ├── __init__.py
│   └── database.py              SQLAlchemy async engine + PostGIS (port 5433)
│
├── alembic/                     ★ PHASE 2+ - Migrations DB
│   ├── env.py                   Config Alembic (load_dotenv!)
│   ├── versions/
│   │   ├── 001_create_annotations.py  Tables annotations + labels
│   │   ├── 002_auth_audit.py          ★ PHASE 3.1 - Auth + audit tables
│   │   └── 003_quality_reports.py     ★ PHASE 3.2 - Quality cache table
│   └── alembic.ini              (dans backend/)
│
├── monitoring.py                Prometheus metrics (optionnel)
│
├── tests/                       ★ 156 tests pytest
│   ├── conftest.py              Fixtures pytest
│   ├── test_format_detector.py  Tests 10+ formats (94 lames)
│   ├── test_tile_server.py      Tests tile serving
│   ├── test_slide_scanner.py    Tests scan
│   ├── test_folder_browser.py   Tests navigation
│   ├── test_detection.py        Tests pipeline detection
│   ├── test_annotations.py      Tests CRUD annotations
│   ├── test_auth_dependencies.py ★ PHASE 3.1 - Tests auth dependencies
│   ├── test_auth_jwt.py          ★ PHASE 3.1 - Tests JWT validation
│   ├── test_audit.py             ★ PHASE 3.1 - Tests audit trail
│   ├── test_quality_metrics.py   ★ PHASE 3.2 - 31 tests quality metrics
│   └── test_quality_api.py       ★ PHASE 3.2 - 7 integration tests
│
└── requirements.txt             Dependencies Python
```

---

## Fichiers Cles par Tache

### Modifier le comportement du viewer
- `frontend/src/viewers/ViewerInstance.js` → Methodes OSD, _createTileSource()
- `frontend/src/core/Constants.js` → Config OSD_CONFIG

### Ajouter/modifier la synchronisation
- `frontend/src/viewers/SyncController.js` → Logique sync (debounce 16ms)
- `frontend/src/utils/coordinates.js` → Normalisation viewport

### Modifier le layout multi-viewer
- `frontend/src/components/CompareLayout.js` → Gestion panels
- `frontend/src/css/layouts/compare-layout.css` → Grille CSS
- `frontend/src/core/Constants.js` → LayoutPresets

### Ajouter un endpoint API
- `backend/routes/slides.py` ou `annotations.py` ou `ml.py` → Route FastAPI
- `frontend/src/services/ApiService.js` → Methode client

### Travailler avec les annotations
- `backend/routes/annotations.py` → CRUD API
- `backend/models/annotation.py` → ORM (Annotation, AnnotationLabel)
- `backend/schemas/annotation.py` → Pydantic validation
- `frontend/src/services/AnnotationStore.js` → Client state
- `frontend/src/components/AnnotationLayer.js` → SVG overlay
- `frontend/src/components/DrawingTools.js` → Outils dessin

### Travailler avec le ML
- `backend/routes/ml.py` → Endpoints ML
- `backend/services/ml/slideflow_service.py` → Slideflow + Phikon-v2
- `backend/services/detection/pipeline.py` → Detection regions
- `frontend/src/components/MLPanel.js` → Panel UI
- `frontend/src/components/HeatmapOverlay.js` → Canvas overlay
- `frontend/src/components/DetectionPanel.js` → Detection workflow

### Modifier la navigation dossiers
- `backend/services/folder_browser.py` → Logique browse
- `frontend/src/components/FolderBrowser.js` → UI explorateur

### Modifier le tile streaming
- `backend/services/tile_server.py` → Extraction tuiles (LRU cache)
- `frontend/src/viewers/ViewerInstance.js` → _createTileSource()

### Ajouter un format de slide
- `backend/services/format_detector.py` → Patterns detection + _try_open_slide

### Travailler avec l'authentification
- `backend/auth/config.py` → Configuration OIDC (issuer, client_id, etc.)
- `backend/auth/dependencies.py` → `require_role()` FastAPI dependency
- `backend/auth/audit.py` → Audit trail (log_audit_event)
- `frontend/src/services/AuthService.js` → PKCE flow, token management
- `frontend/src/components/LoginPage.js` → Login UI
- `frontend/src/components/UserMenu.js` → User info, role display

### Travailler avec les quality metrics
- `backend/quality/metrics.py` → Pure functions (kappa, F1, confusion matrix)
- `backend/quality/matching.py` → Spatial matching (PostGIS IoU, grid)
- `backend/quality/services.py` → Orchestration (matching + metrics + cache)
- `backend/quality/routes.py` → 7 API endpoints
- `frontend/src/components/QualityPanel.js` → Quality metrics UI
- `frontend/src/services/ApiService.js` → Quality API methods

### Modifier la base de donnees
- `backend/models/annotation.py` → ORM models
- `backend/core/database.py` → Engine SQLAlchemy async
- `backend/alembic/` → Migrations (alembic revision --autogenerate)
- `docker-compose.dev.yml` → PostgreSQL + PostGIS (port 5433)

---

## Imports Recommandes

```javascript
// Core
import { eventBus, Events, ViewerStates } from './core';

// Viewers
import { viewerManager, ViewerFactory } from './viewers';

// Services
import { apiService } from './services';
import { annotationStore } from './services/AnnotationStore.js';

// Components
import { CompareLayout, ViewerPanel } from './components';
import { AnnotationLayer } from './components/AnnotationLayer.js';
import { DrawingTools } from './components/DrawingTools.js';
import { DetectionPanel } from './components/DetectionPanel.js';

// Utils
import coordinates from './utils/coordinates.js';
```

---

## CSS Variables Principales

```css
/* Couleurs - frontend/src/css/variables.css */
--color-primary: #4a9eff;
--color-bg-base: #000000;
--color-bg-elevated: #1a1a1a;
--color-text-primary: #e0e0e0;
--color-error: #ff6b6b;
--color-success: #4caf50;

/* Layout */
--grid-gap: 8px;
--viewer-header-height: 40px;

/* Sync */
--sync-enabled-color: var(--color-success);
--sync-disabled-color: var(--color-text-muted);
```

---

## Events Principaux (EventBus)

```javascript
// Definis dans frontend/src/core/Constants.js

// Viewer lifecycle
Events.VIEWER_CREATED        // Nouveau viewer cree
Events.VIEWER_DESTROYED      // Viewer detruit
Events.VIEWER_VIEWPORT_CHANGE // Pan ou zoom
Events.VIEWER_PAN            // Pan specifiquement
Events.VIEWER_ZOOM           // Zoom specifiquement

// Slides
Events.SLIDE_LOADING         // Chargement en cours
Events.SLIDE_LOADED          // Lame chargee avec succes
Events.SLIDE_ERROR           // Erreur chargement

// Sync
Events.SYNC_ENABLED          // Sync activee
Events.SYNC_DISABLED         // Sync desactivee

// Layout
Events.LAYOUT_CHANGED        // Layout grille modifie
Events.PAGE_CHANGED          // Navigation entre pages
Events.SLIDE_SELECTED        // Lame selectionnee (dans picker)

// Annotations (Phase 2)
Events.ANNOTATION_CREATED    // Annotation creee
Events.ANNOTATION_UPDATED    // Annotation modifiee
Events.ANNOTATION_DELETED    // Annotation supprimee
Events.ANNOTATION_STATS_UPDATED // Stats recalculees
Events.DRAWING_MODE_CHANGED  // Mode dessin actif/inactif
```

---

## Archives Structure (Reference Only)

Documents Phase 2+/3+ archives pour reference future.
**NE PAS MODIFIER** - Reactiver si necessaire.

```
Archives/
├── README.md                        # Index et guide reactivation
│
├── Backups/                         # Sauvegardes configuration
│   ├── .env.phase2.1.backup.*      # Variables environnement
│   └── docker-compose.*.backup.*   # Compose backups
│
├── Build-Docs/                      # Documentation build
│   ├── BUILD_DIFFERENCES.md        # Variantes de build
│   └── DOCKER_FILES_SUMMARY.md     # Changelog Docker
│
├── Phase2-Deployment/               # Deploiement Phase 2
│   ├── DEPLOYMENT_READY.md         # Status snapshot
│   └── PHASE2_DEPLOYMENT_SUMMARY.md
│
├── Phase2-Refactoring/              # Plans refactoring
│   ├── BACKEND_REFACTORING.md      # Plan refactor backend
│   ├── FRONTEND_REFACTORING.md     # Plan refactor frontend
│   ├── BACKEND_ARCHITECTURE_DIAGRAM.md
│   └── INFRASTRUCTURE_ARCHITECTURE.md
│
├── Phase3-Planning/                 # Planification future
│   ├── Infrastructure/
│   │   └── INFRASTRUCTURE_OVERVIEW.md
│   ├── MLOps/
│   │   ├── MLOPS_ARCHITECTURE.md
│   │   ├── MLOPS_INTEGRATION_GUIDE.md
│   │   └── MLOPS_QUICK_START.md
│   └── Security/
│       ├── SECURITY_ARCHITECTURE.md
│       ├── SECURITY_EXECUTIVE_SUMMARY.md
│       └── SECURITY_PHASE1_IMPLEMENTATION.md
│
├── Research/                        # Articles academiques
│   ├── *.pdf                       # Papers WSI/pathologie
│   └── Essai_Rapport_TFE_WSI.docx
│
└── TFE/                             # Documents these
    ├── TFE_PROPOSITION_COMPLETE.md
    ├── INFRASTRUCTURE_SUMMARY_TFE.md
    └── HE141888_HE202723_rapport_TFE_2026.pdf
```

### Quand Consulter Archives/

- **Phase2-Refactoring/** → Avant gros refactoring backend/frontend
- **Phase3-Planning/MLOps/** → Avant integration ML avancee
- **Phase3-Planning/Security/** → Avant implementation auth
- **Research/** → Pour contexte academique WSI
- **TFE/** → Pour rapport final
