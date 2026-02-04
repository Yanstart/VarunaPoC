# Architecture VarunaPoC - Multi-Viewer System

**Dernière mise à jour:** 2025-12-30
**Version:** 2.0 (Post-refactoring)

---

## Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
├─────────────────────────────────────────────────────────────────┤
│  main.js                                                        │
│    ├── showHomePage()      → FolderBrowser                      │
│    ├── showViewerPage()    → Single Viewer (legacy)             │
│    └── showComparePage()   → CompareLayout (multi-viewer)       │
├─────────────────────────────────────────────────────────────────┤
│  CORE                        │  VIEWERS                         │
│  ├── EventBus.js            │  ├── ViewerManager.js (Singleton)│
│  └── Constants.js           │  ├── ViewerFactory.js (Factory)  │
│                              │  ├── ViewerInstance.js (Wrapper) │
│  COMPONENTS                  │  ├── ViewerState.js (State)      │
│  ├── CompareLayout.js       │  └── SyncController.js (Mediator)│
│  ├── ViewerPanel.js         │                                   │
│  ├── SyncControls.js        │  SERVICES                         │
│  ├── FolderBrowser.js       │  └── ApiService.js               │
│  └── Viewer.js (legacy)     │                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
├─────────────────────────────────────────────────────────────────┤
│  main.py (FastAPI)                                              │
│    └── routes/slides.py                                         │
│          ├── /api/slides/browse      → folder_browser.py        │
│          ├── /api/slides/{id}/info   → tile_server.py           │
│          ├── /api/slides/{id}/dzi    → tile_server.py           │
│          └── /api/slides/{id}/tiles  → tile_server.py           │
├─────────────────────────────────────────────────────────────────┤
│  SERVICES                                                        │
│  ├── tile_server.py      → TileServer (cache LRU, OpenSlide)   │
│  ├── slide_scanner.py    → Scan récursif /Slides               │
│  ├── folder_browser.py   → Navigation hiérarchique             │
│  └── format_detector.py  → Détection formats (12+)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flow Principal

### 1. Page Home → Single Viewer
```
User clique lame → handleSlideSelect(slide)
  → showViewerPage(slide)
    → initViewer('viewer')           // Crée ViewerInstance via legacy wrapper
    → loadSlideWithTiles(viewer, id) // Charge via ViewerInstance.loadSlide()
```

### 2. Page Home → Compare Mode
```
User clique "Compare Mode" → showComparePage()
  → new CompareLayout(container, { initialLayout: 'SIDE_BY_SIDE' })
    → Crée 2 ViewerPanel
      → Chaque panel crée un ViewerInstance via ViewerManager
    → Crée SyncControls (toggle sync, layout selector)

User clique "Select Slide" dans un panel
  → showSlidePicker()
    → User sélectionne lame
    → compareLayout.loadSlideAt(panelIndex, slideId, slideName)
```

### 3. Synchronisation
```
Sync activée → viewerManager.enableSync()
  → SyncController.enable()
    → Écoute Events.VIEWER_VIEWPORT_CHANGE sur EventBus
    → Quand viewer1 bouge:
      1. Normalise viewport (0-1)
      2. Broadcast aux autres viewers
      3. Chaque viewer applique le viewport
```

---

## Communication Inter-Composants

```
┌──────────────┐     EventBus      ┌──────────────┐
│ ViewerPanel  │ ──── emit ──────▶ │ SyncController│
│              │                   │              │
│ (pan/zoom)   │ ◀─── subscribe ── │ (broadcast)  │
└──────────────┘                   └──────────────┘
       │                                  │
       │         ┌──────────────┐         │
       └────────▶│   EventBus   │◀────────┘
                 │              │
                 │ Events:      │
                 │ - VIEWER_PAN │
                 │ - VIEWER_ZOOM│
                 │ - SYNC_*     │
                 └──────────────┘
```

---

## Hiérarchie des Classes

```
ViewerManager (Singleton)
  └── manages: Map<viewerId, ViewerInstance>

ViewerFactory (Static)
  └── creates: ViewerInstance

ViewerInstance
  ├── wraps: OpenSeadragon.Viewer
  ├── has: ViewerState
  └── emits: Events via EventBus

SyncController (Mediator)
  ├── registers: ViewerInstance[]
  └── listens: EventBus (VIEWER_* events)

CompareLayout
  ├── contains: ViewerPanel[]
  ├── has: SyncControls
  └── delegates to: ViewerManager

ViewerPanel
  ├── wraps: ViewerInstance
  └── provides: UI (header, actions, empty state)
```

---

## États du Viewer (State Pattern)

```
         ┌──────────┐
         │   IDLE   │ (initial)
         └────┬─────┘
              │ loadSlide()
              ▼
         ┌──────────┐
         │ LOADING  │
         └────┬─────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
┌──────────┐   ┌──────────┐
│  READY   │   │  ERROR   │
└────┬─────┘   └────┬─────┘
     │              │
     │ loadSlide()  │ retry
     └──────────────┘
              │
              ▼
         ┌──────────┐
         │DESTROYING│ (terminal)
         └──────────┘
```

---

## Coordonnées

### OpenSeadragon (Frontend)
- **Normalisées**: x,y dans [0, 1] où width=1.0
- **Aspect ratio**: height = width * (slideHeight/slideWidth)

### OpenSlide (Backend)
- **Absolues**: pixels au niveau 0 (full resolution)
- **Multi-niveaux**: level 0 = max res, level N = downsampled

### Conversion
```javascript
// OSD → OpenSlide
const absoluteX = normalizedX * slideWidth;

// OpenSlide → OSD
const normalizedX = absoluteX / slideWidth;

// Voir: frontend/src/utils/coordinates.js
```

---

## Points d'Extension

### Ajouter un nouveau format de slide
1. `backend/services/format_detector.py` → Ajouter pattern détection
2. Tester avec OpenSlide

### Ajouter une fonctionnalité viewer
1. `frontend/src/viewers/ViewerInstance.js` → Ajouter méthode
2. Exposer via `ViewerManager` si nécessaire
3. Émettre événement via `EventBus` si besoin de sync

### Modifier le layout
1. `frontend/src/core/Constants.js` → Ajouter preset dans `LayoutPresets`
2. `frontend/src/css/layouts/compare-layout.css` → Ajouter classe CSS
3. `frontend/src/components/SyncControls.js` → Ajouter bouton layout

### Ajouter endpoint API
1. `backend/routes/slides.py` → Ajouter route
2. `frontend/src/services/ApiService.js` → Ajouter méthode
3. Documenter dans docstring (voir API Documentation Protocol dans CLAUDE.md)
