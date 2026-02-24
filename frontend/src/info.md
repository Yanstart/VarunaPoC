# frontend/src

## But
Code source du viewer. Architecture en 4 couches: Core (events/config) -> Services (API/state) -> Viewers (OpenSeadragon) -> Components (UI).

## Structure
```
src/
  main.js              # Bootstrap: routing (#home, #viewer, #compare), init services
  core/
    EventBus.js        # Pub-Sub singleton (40+ types d'events)
    Constants.js       # Enums, endpoints API, config OSD, layouts, formats supportes
  services/
    ApiService.js      # HTTP client singleton (cache 5min, deduplication) [974 lignes]
    AuthService.js     # OIDC PKCE (Keycloak, roles: MEDECIN, ADMIN, RADIOLOGIST)
    AnnotationStore.js # State annotations client-side (labels, outils, selections)
    I18nService.js     # i18n (fr default, 5 langues, LocalStorage)
  viewers/
    ViewerManager.js   # Registre singleton de tous les ViewerInstance
    ViewerFactory.js   # Factory pattern (presets: default, compact)
    ViewerInstance.js   # Wrapper OpenSeadragon + state machine [637 lignes]
    SyncController.js  # Sync pan/zoom multi-viewer (debounce 16ms/60fps)
    ViewerState.js     # State machine: idle -> loading -> ready | error -> destroying
  components/          # 31 composants UI (voir frontend/info.md pour details)
  css/                 # 28 fichiers CSS modulaires (dark theme)
  locales/             # Traductions JSON (fr, en, ja, zh, hi)
  utils/               # coordinates.js (viewport <-> pixels), api.js (legacy)
```
