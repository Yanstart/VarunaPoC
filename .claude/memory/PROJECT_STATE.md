# Etat du Projet - VarunaPoC

**Derniere mise a jour:** 2026-02-20
**Mis a jour par:** Cerveau d'Orchestration

---

## Snapshot Actuel

### Version & Phase
- **Version:** 2.0.0
- **Phase:** Phase 3.1 (Auth) COMPLETE, Phase 4 (Quality) COMPLETE
- **Branche Git:** `main` (commit 96261b2)
- **Plan:** MVP 15 semaines (cf. PROPOSAL_VARUNA_v2.md)
- **Prochaine etape:** Phase 3.3 Integration PACS Telemis
- **Issues:** 124/124 closed, all PRs merged

### Sante du Projet

| Aspect | Score | Commentaire |
|--------|-------|-------------|
| Fonctionnalite | 9/10 | Viewer, annotations, ML, compare mode, detection, counting, quality metrics |
| Architecture | 9/10 | Patterns solides (Factory, Singleton, Observer, Mediator), modules isoles |
| Securite | 7/10 | OIDC PKCE, RBAC 4 roles, JWT RS256/ES256, audit trail, break-glass |
| Tests | 8/10 | 156 tests backend (pytest), 21 skipped. Pas de tests E2E frontend |
| Documentation | 9/10 | Proposal v2, hospital evaluation, architecture, manuel, API docs |
| MLOps | 5/10 | Slideflow + Phikon-v2 integre, pas de monitoring/drift/feedback loop |
| Performance | 8/10 | Tiles < 15ms keep-alive, 94 lames 10 formats |
| CI/CD | 9/10 | 10/10 CI jobs pass, security scans, CD pipeline (GHCR), all green |

---

## Ce Qui Fonctionne

### Backend (port 8000)
- [x] Detection 10+ formats de slides (FormatDetector + _try_open_slide)
- [x] Navigation hierarchique `/api/slides/browse`
- [x] Metadata slides `/api/slides/{id}/info`
- [x] Tile streaming DZI `/api/slides/{id}/tiles/{level}/{x}_{y}.jpg`
- [x] Overview/thumbnail generation
- [x] LRU cache (5 slides max)
- [x] Prometheus metrics (optionnel)
- [x] Annotations CRUD `/api/annotations/{slide_id}` (PostgreSQL + PostGIS)
- [x] Labels avec couleurs `/api/annotations/labels`
- [x] Stats annotations `/api/annotations/{slide_id}/stats`
- [x] ML heatmap `/api/ml/heatmap/{slide_id}` (Slideflow + Phikon-v2)
- [x] ML detection `/api/ml/detect/{slide_id}` (heatmap -> scipy -> shapely -> GeoJSON)
- [x] ML predict `/api/ml/predict/{slide_id}` (classification + uncertainty)
- [x] DB lifespan graceful (async context manager)
- [x] Routes synchrones (def, pas async def) pour OpenSlide threadpool
- [x] **Auth OIDC PKCE** (Keycloak dev, Azure AD prod-ready)
- [x] **RBAC 4 roles claims-based** (LECTURE_SEULE, INFIRMIER, MEDECIN, ADMIN_TECHNIQUE)
- [x] **JWT validation RS256/ES256** avec JWKS cache TTL 1h
- [x] **Audit trail** dual DB+JSON (INFO/WARNING/CRITICAL)
- [x] **Break-glass** emergency sessions 30min
- [x] **Session roaming** cross-workstation (PostgreSQL)
- [x] **FHIR R4 stub** DiagnosticReport builder
- [x] **Quality metrics** `/api/quality/{slide_id}/...` (7 endpoints)
- [x] **Cohen's kappa** pairwise + IoU spatial matching (PostGIS)
- [x] **Fleiss' kappa** multi-rater + grid-based matching
- [x] **Confusion matrix, F1/P/R per label, IoU distribution**
- [x] **Disagreement heatmap** GeoJSON overlay
- [x] **Quality cache table** `quality_reports` (JSONB, TTL 5min)

### Frontend (port 5173)
- [x] Page Home avec FolderBrowser
- [x] Page Viewer single slide
- [x] Page Compare multi-viewer (2x1, 2x2, etc.)
- [x] Synchronisation pan/zoom (toggle)
- [x] Mini-map (navigator) sur chaque viewer
- [x] EventBus pour communication (avec unsubscribe pattern)
- [x] ViewerManager singleton
- [x] ViewerFactory avec presets
- [x] AnnotationLayer (SVG overlay)
- [x] DrawingTools (rectangle, polygone, point, cercle, freehand)
- [x] LayerManager (visibilite, opacite)
- [x] DetectionPanel (auto-detect workflow, label selector, confidence bar)
- [x] CountingPanel (stats temps reel par label/type)
- [x] HeatmapOverlay (canvas overlay, cached image, coordinate mapping)
- [x] MLPanel (predict, heatmap trigger)
- [x] AnnotationStore (CRUD client, loadStats, computeLocalStats)
- [x] **AuthService PKCE** (login/logout, token refresh)
- [x] **LoginPage** + **UserMenu** (role display, session info)
- [x] **Role-based UI** (component visibility per role)
- [x] **QualityPanel** (annotator selector, kappa badge, confusion matrix, F1 table, IoU histogram)
- [x] **Disagreement overlay** (hatched SVG polygons)

### 10 Formats Supportes (94 lames testees)
- [x] Aperio SVS (.svs, .tif)
- [x] Hamamatsu NDPI (.ndpi)
- [x] 3DHistech MIRAX (.mrxs)
- [x] Leica SCN (.scn)
- [x] Ventana BIF (.bif)
- [x] Philips TIFF (.tif)
- [x] Trestle (.tif)
- [x] Sakura (.svslide)
- [x] Zeiss CZI (.czi) - sauf JPEG XR
- [x] DICOM WSI (.dcm)
- [x] Generic TIFF pyramidal (.tif)

### Formats Non Supportes (identifies)
- Olympus VSI (3 lames) - necessite Bio-Formats
- Zeiss ZVI (5 lames) - format legacy
- Zeiss CZI JPEG XR (4 lames) - codec manquant
- Fichiers corrompus (3) : Hamamatsu-1.ndpi, Leica-3.scn, Leica-Fluorescence-1.scn

---

## Ce Qui Ne Fonctionne Pas / Manque

### Prochaine Etape (Phase 3.3)
- [ ] **Integration PACS Telemis** - Command plugin (lancement viewer depuis PACS)
- [ ] **Endpoint by-accession** - Resolution accession number -> slide
- [ ] **Contexte patient automatique** - slide_id -> patient context

### Phase 4 Finalisation (Semaines 14-15)
- [ ] **Tests E2E** - Playwright/Selenium
- [ ] **Tests charge** - 10 utilisateurs simultanes
- [ ] **Documentation formation** - Sessions utilisateurs

### Post-MVP
- [ ] **SSO institutionnel** (SAML 2.0/OAuth 2.0 complet)
- [ ] **Collaboration temps reel** (WebSocket)
- [ ] **Quality-First complet** (outlier detection, adjudication, versioning Git-like)
- [ ] **MLOps complet** (drift monitoring, feedback loops, CI/CD modeles)
- [ ] **Chiffrement au repos**
- [ ] **Redis cache** tuiles
- [ ] **DICOM export** (Supplement 145)

---

## Fichiers Cles (Reference Rapide)

### Backend
```
backend/
├── main.py                          # Entry point FastAPI v2.0.0
├── config_openslide.py              # DLL config Windows
├── routes/
│   ├── slides.py                    # API slides (6 routes, sync def)
│   ├── annotations.py               # CRUD annotations + labels + stats
│   └── ml.py                        # ML inference endpoints
├── services/
│   ├── format_detector.py           # Detection 10+ formats (+ _try_open_slide)
│   ├── tile_server.py               # Streaming tuiles DZI
│   ├── folder_browser.py            # Navigation hierarchique
│   ├── slide_scanner.py             # Scan recursif + cache
│   ├── detection/                   # Pipeline heatmap -> GeoJSON
│   │   ├── pipeline.py              # scipy ndimage -> skimage -> shapely
│   │   └── heatmap_processor.py     # Traitement heatmaps
│   └── ml/
│       ├── tag_extractor.py         # Extraction tags organe/stain
│       ├── tag_router.py            # Routage ML par tags
│       └── slideflow_service.py     # Integration Slideflow + Phikon-v2
├── auth/                            # Phase 3.1 - Auth OIDC
│   ├── __init__.py                  # AUTH_ENABLED flag
│   ├── config.py                    # OIDC configuration
│   ├── oidc.py                      # OIDC PKCE flow
│   ├── jwt_validator.py             # JWT RS256/ES256 validation
│   ├── dependencies.py              # FastAPI auth dependencies
│   ├── audit.py                     # Audit trail (DB + JSON)
│   ├── models.py                    # User/Session ORM
│   ├── schemas.py                   # Auth Pydantic schemas
│   ├── routes.py                    # Auth endpoints
│   ├── rbac.py                      # Role-based access control
│   └── break_glass.py               # Emergency access
├── fhir/                            # Phase 3.1 - FHIR R4
│   ├── __init__.py                  # FHIR_ENABLED flag
│   ├── resources.py                 # DiagnosticReport builder
│   ├── routes.py                    # FHIR endpoints
│   └── patient_context.py           # Patient context
├── quality/                         # Phase 4 - Quality Metrics
│   ├── __init__.py                  # QUALITY_ENABLED flag
│   ├── config.py                    # Thresholds, Landis-Koch scale
│   ├── metrics.py                   # Cohen/Fleiss kappa, F1, confusion matrix
│   ├── schemas.py                   # Pydantic models
│   ├── matching.py                  # IoU spatial + grid matching (PostGIS)
│   ├── services.py                  # Orchestration layer
│   └── routes.py                    # 7 API endpoints
├── models/
│   ├── annotation.py                # ORM Annotation + AnnotationLabel
│   ├── quality_report.py            # ORM cache table (JSONB)
│   └── __init__.py
├── schemas/
│   ├── annotation.py                # Pydantic schemas
│   ├── geojson.py                   # GeoJSON models
│   └── detection.py                 # Detection schemas
├── core/database.py                 # SQLAlchemy async + PostGIS
├── alembic/                         # Migrations DB (001, 002, 003)
├── tests/                           # 156 tests pytest
├── monitoring.py                    # Prometheus metrics
└── requirements.txt
```

### Frontend
```
frontend/src/
├── main.js                          # Entry + routing (HOME/VIEWER/COMPARE)
├── core/
│   ├── EventBus.js                  # Observer pattern (with unsubscribe)
│   └── Constants.js                 # Config centralisee
├── viewers/
│   ├── ViewerManager.js             # Singleton gestionnaire
│   ├── ViewerFactory.js             # Factory pattern
│   ├── ViewerInstance.js            # Wrapper OSD
│   ├── ViewerState.js               # State machine
│   └── SyncController.js            # Mediator sync
├── components/
│   ├── AnnotationLayer.js           # SVG overlay annotations + disagreement
│   ├── DrawingTools.js              # 5 outils dessin
│   ├── LayerManager.js              # Visibilite/opacite
│   ├── DetectionPanel.js            # Auto-detect workflow
│   ├── CountingPanel.js             # Stats temps reel
│   ├── HeatmapOverlay.js            # Canvas overlay ML
│   ├── MLPanel.js                   # Panel analyse ML
│   ├── QualityPanel.js              # Phase 4 - Quality metrics panel
│   ├── CompareLayout.js             # Grid multi-viewer
│   ├── ViewerPanel.js               # Panel individuel
│   ├── FolderBrowser.js             # Explorateur dossiers
│   ├── SyncControls.js              # UI sync
│   ├── LoginPage.js                 # Phase 3.1 - Login
│   └── UserMenu.js                  # Phase 3.1 - User info
├── services/
│   ├── ApiService.js                # Client API singleton + quality methods
│   ├── AnnotationStore.js           # Etat annotations (CRUD, stats)
│   └── AuthService.js               # Phase 3.1 - OIDC PKCE client
├── css/
│   ├── login.css                    # Phase 3.1
│   ├── user-menu.css                # Phase 3.1
│   └── quality-panel.css            # Phase 4
└── ...
```

### Documentation strategique
```
docs/
├── PROPOSAL_VARUNA_v2.md            # Proposition projet v2 (marche, architecture, roadmap)
├── ARCHITECTURE.md                  # Architecture technique
├── ML_INTEGRATION.md                # Integration Slideflow
├── FORMATS_SUPPORTED.md             # Formats supportes
├── Manuel/                          # Documentation utilisateur
├── Deployment/
│   ├── TELEMIS_INTEGRATION_GUIDE.md # Guide integration PACS Telemis
│   └── ...                          # Network, monitoring guides
└── architecture/
    └── SYSTEM_PATTERNS.md           # Phase 3.1 patterns doc

HOSPITAL_DEPLOYMENT_EVALUATION.md    # Evaluation deploiement hospitalier (racine)
```

---

## Metriques de Performance (Mesures Reelles)

| Metrique | Valeur Mesuree | Source |
|----------|----------------|--------|
| Tile load (keep-alive) | 0-13ms | Tests Phase 2 |
| 28 tiles (premier chargement) | ~2.1s | Tests Phase 2 |
| ML heatmap (Phikon-v2, CUDA) | ~2.5 min | Tests Phase 2 |
| Formats supportes | 10 | 94 lames testees |
| Tests backend | 156 pass, 21 skip | pytest |
| Detection regions | 3 regions (72-88% confidence) | threshold=0.3 |

---

## Git Status (2026-02-20)

### Branches
- `main` - Production stable (commit 96261b2)
- `develop` - Development branch

### Commits Recents
```
96261b2 fix(ci): share runner network namespace for E2E backend container
5acb054 fix(ci): use container bridge IP for E2E Playwright tests
b79f143 fix(ci): add docker prune before builds to prevent disk full errors
f899aae fix(ci): use --network=host for e2e backend container
5f6fbc9 fix(ci): use docker exec for health checks (DooD compatible)
```

### CI/CD Pipeline Status
**CI (ci.yml)** — 10 jobs, ALL PASS:
- Detect Changes, Backend Lint/Test/Docker, Frontend Lint/Build/Docker, Integration, E2E Playwright, CI Status

**Security (security.yml)** — 7 jobs:
- PASS: Secret Scan, Dependency Scan (x2), Docker Scan (x2)
- FAIL (informational, continue-on-error): CodeQL (x2), Python Security, JS Security, HIPAA Compliance

**CD (cd.yml)** — on push to main:
- Build + push to GHCR, GitHub Release on tags, deployment manifest update

**Other**: notify-failure.yml, update-project.yml

**Self-hosted runner toggle**: `vars.USE_SELF_HOSTED` (DooD compatible)

---

## Positionnement & Contexte

### Recherche Use Only
- **Aujourd'hui** : outil de recherche et d'enseignement (IVDR Classe A, FDA Exempt)
- **Objectif moyen terme** : outil d'aide a la decision consultatif
- **Option long terme** : certification IVDR Classe C / FDA 510(k) si validation clinique

### 3 Differenciateurs (cf. PROPOSAL_VARUNA_v2.md)
1. **Quality-First Annotations** - Metriques IAA (kappa FAIT), detection outliers, versioning
2. **Continuous Learning MLOps** - Drift monitoring, feedback loops, CI/CD modeles
3. **Radical Simplicity** - Zero-config, onboarding 3 min, < 100ms latence

### Gaps Critiques pour Deploiement Hospitalier (cf. HOSPITAL_DEPLOYMENT_EVALUATION.md)
1. ~~Authentification (RBAC + JWT)~~ FAIT (Phase 3.1)
2. ~~Audit trail (structured logging + table)~~ FAIT (Phase 3.1)
3. Integration PACS (command plugin Telemis) - PROCHAIN
4. Protection PHI (de-identification) - Post-MVP
5. HTTPS/TLS - Depends on nginx config

---

**Ce fichier est mis a jour au debut de chaque session Claude Code.**
