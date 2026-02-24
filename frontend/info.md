# Frontend

## But
Viewer de lames histologiques gigapixel. Interface Vanilla JS + Vite + OpenSeadragon pour navigation, annotations, ML, et comparaison multi-lames.

## Pourquoi
OpenSeadragon est le standard open-source pour l'imagerie zoomable. Vanilla JS (pas de framework) pour garder le bundle leger et le controle total sur le rendu.

## Comment
- Vite 5 pour le build (dev port 5173, build -> dist/)
- OpenSeadragon 4.1 pour le rendu des tuiles DZI
- Architecture: EventBus (pub-sub) + Services singleton + Components classe
- Dark theme par defaut, i18n (fr/en/ja/zh/hi)

## Structure
```
frontend/
  index.html           # SPA entry point (#app container)
  vite.config.js       # Build config (port 5173, sourcemaps)
  src/
    main.js            # Bootstrap: routing, init services, render pages
    core/              # EventBus (pub-sub), Constants (40+ events, endpoints, layouts)
    services/          # ApiService, AuthService (OIDC PKCE), AnnotationStore, I18nService
    components/        # 31 composants UI (DrawingTools, MLPanel, FolderBrowser, CompareLayout...)
    viewers/           # ViewerManager, ViewerInstance (OSD wrapper), SyncController, ViewerFactory
    css/               # 28 fichiers CSS modulaires (dark theme, variables custom properties)
    locales/           # fr.json, en.json, ja.json, zh.json, hi.json
    utils/             # api.js (legacy fetch), coordinates.js (viewport <-> pixels)
  e2e/                 # Playwright 1.50: 18 tests (navigation, annotations, ML, auth, a11y)
```

## Points cles
- `components/DrawingTools.js` = 6 outils (select, rectangle, polygon, point, circle, freehand)
- `viewers/SyncController.js` = synchronisation pan/zoom entre viewers (60fps debounce)
- `components/CompareLayout.js` = grilles SINGLE, SIDE_BY_SIDE, GRID_2X2, GRID_3X3
- `services/ApiService.js` = cache 5min TTL + deduplication des requetes
