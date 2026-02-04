# Référence Rapide des Fichiers

**Dernière mise à jour:** 2026-02-02

---

## Frontend Structure

```
frontend/src/
├── main.js                      ★ ENTRY POINT - Routing, init app
├── style.css                    ★ CSS imports (order matters)
│
├── core/                        ★ CORE MODULES
│   ├── index.js                 Exports centralisés
│   ├── EventBus.js              Pub/Sub singleton (Observer pattern)
│   └── Constants.js             Toutes les constantes (Events, API, etc.)
│
├── viewers/                     ★ VIEWER SYSTEM
│   ├── index.js                 Exports centralisés
│   ├── ViewerManager.js         Singleton - gère tous les viewers
│   ├── ViewerFactory.js         Factory - crée les ViewerInstance
│   ├── ViewerInstance.js        Wrapper OpenSeadragon
│   ├── ViewerState.js           State machine (IDLE→LOADING→READY)
│   └── SyncController.js        Mediator - synchronise pan/zoom
│
├── components/                  ★ UI COMPONENTS
│   ├── index.js                 Exports centralisés
│   ├── CompareLayout.js         Layout grille multi-viewers
│   ├── ViewerPanel.js           Panel unique avec header/actions
│   ├── SyncControls.js          Barre toggle sync + layout selector
│   ├── FolderBrowser.js         Explorateur de dossiers
│   ├── SlideList.js             Grille de tuiles lames
│   ├── Home.js                  (legacy, peu utilisé)
│   └── Viewer.js                ★ LEGACY WRAPPER - backward compat
│
├── services/                    ★ API LAYER
│   ├── index.js                 Exports centralisés
│   └── ApiService.js            Client API classe avec cache
│
├── utils/                       ★ UTILITIES
│   ├── api.js                   (legacy) - fonctions fetch simples
│   └── coordinates.js           Transformations coordonnées OSD↔OpenSlide
│
└── css/                         ★ STYLES
    ├── variables.css            CSS custom properties (thème)
    ├── base.css                 Reset, scrollbar, utilities
    ├── home.css                 Page d'accueil
    ├── slide-tiles.css          Tuiles de lames
    ├── viewer.css               Page viewer single
    ├── openseadragon.css        Overrides OSD
    └── layouts/
        └── compare-layout.css   Grille multi-viewers, sync controls
```

---

## Backend Structure

```
backend/
├── main.py                      ★ ENTRY POINT - FastAPI app, CORS, tags
│
├── routes/
│   └── slides.py                ★ API ENDPOINTS
│                                  /api/slides/browse
│                                  /api/slides/{id}/info
│                                  /api/slides/{id}/dzi.json
│                                  /api/slides/{id}/tiles/{level}/{x}_{y}.jpg
│                                  /api/slides/{id}/overview
│
├── services/
│   ├── tile_server.py           ★ CORE - TileServer avec cache LRU
│   ├── slide_scanner.py         Scan récursif /Slides
│   ├── folder_browser.py        Navigation hiérarchique non-récursive
│   └── format_detector.py       Détection 12+ formats slides
│
└── utils/
    └── (vide pour l'instant)
```

---

## Fichiers Clés par Tâche

### Modifier le comportement du viewer
- `frontend/src/viewers/ViewerInstance.js` → Méthodes OSD
- `frontend/src/core/Constants.js` → Config OSD_CONFIG

### Ajouter/modifier la synchronisation
- `frontend/src/viewers/SyncController.js` → Logique sync
- `frontend/src/utils/coordinates.js` → Normalisation viewport

### Modifier le layout multi-viewer
- `frontend/src/components/CompareLayout.js` → Gestion panels
- `frontend/src/css/layouts/compare-layout.css` → Grille CSS
- `frontend/src/core/Constants.js` → LayoutPresets

### Ajouter un endpoint API
- `backend/routes/slides.py` → Route FastAPI
- `frontend/src/services/ApiService.js` → Méthode client

### Modifier la navigation dossiers
- `backend/services/folder_browser.py` → Logique browse
- `frontend/src/components/FolderBrowser.js` → UI explorateur

### Modifier le tile streaming
- `backend/services/tile_server.py` → Extraction tuiles
- `frontend/src/viewers/ViewerInstance.js` → _createTileSource()

### Ajouter un format de slide
- `backend/services/format_detector.py` → Patterns détection

---

## Imports Recommandés

```javascript
// Core
import { eventBus, Events, ViewerStates } from './core';

// Viewers
import { viewerManager, ViewerFactory } from './viewers';

// Services
import { apiService } from './services';

// Components
import { CompareLayout, ViewerPanel } from './components';

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
// Définis dans frontend/src/core/Constants.js

Events.VIEWER_CREATED        // Nouveau viewer créé
Events.VIEWER_DESTROYED      // Viewer détruit
Events.VIEWER_VIEWPORT_CHANGE // Pan ou zoom
Events.VIEWER_PAN            // Pan spécifiquement
Events.VIEWER_ZOOM           // Zoom spécifiquement

Events.SLIDE_LOADING         // Chargement en cours
Events.SLIDE_LOADED          // Lame chargée avec succès
Events.SLIDE_ERROR           // Erreur chargement

Events.SYNC_ENABLED          // Sync activée
Events.SYNC_DISABLED         // Sync désactivée

Events.LAYOUT_CHANGED        // Layout grille modifié
Events.PAGE_CHANGED          // Navigation entre pages
Events.SLIDE_SELECTED        // Lame sélectionnée (dans picker)
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
- **Phase3-Planning/MLOps/** → Avant integration ML
- **Phase3-Planning/Security/** → Avant implementation auth
- **Research/** → Pour contexte academique WSI
- **TFE/** → Pour rapport final
