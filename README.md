# VarunaPoC - Digital Pathology Slide Viewer

**Plateforme web d'imagerie microscopique pour CHU UCL Namur**

Viewer vendor-neutral de lames histologiques (WSI) avec annotations, detection ML et mode comparaison. Remplace le client lourd actuel par une solution web moderne, open-source et extensible.

> **Research Use Only** - Ce logiciel est destine a la recherche et a l'enseignement.
> Il n'est pas certifie CE-IVD/FDA et ne doit pas etre utilise pour le diagnostic primaire.

## Fonctionnalites

### Viewer WSI haute performance
- Navigation fluide sur images gigapixel (100,000+ x 80,000 px)
- Tiles en < 15ms (keep-alive), zoom progressif multi-resolution
- Mode comparaison multi-lames avec synchronisation pan/zoom
- Mini-map, plein ecran, navigation clavier

### 10 formats vendor-neutral (OpenSlide)
| Format | Extension | Vendor |
|--------|-----------|--------|
| Aperio SVS | `.svs`, `.tif` | Leica |
| Hamamatsu NDPI | `.ndpi` | Hamamatsu |
| 3DHistech MIRAX | `.mrxs` | 3DHistech |
| Leica SCN | `.scn` | Leica |
| Ventana BIF | `.bif` | Roche |
| Philips TIFF | `.tif` | Philips |
| Trestle | `.tif` | Trestle |
| Sakura | `.svslide` | Sakura |
| Zeiss CZI | `.czi` | Zeiss |
| DICOM WSI | `.dcm` | Standard |

94 lames testees, 3 fichiers corrompus correctement rejetes.

### Annotations (PostgreSQL + PostGIS)
- 5 outils de dessin : rectangle, polygone, point, cercle, freehand
- Labels avec couleurs, CRUD complet + reject + batch, export GeoJSON
- Statistiques temps reel (comptage par label/type, distribution confiance)

### ML / IA (Slideflow + Phikon-v2)
- Heatmaps d'attention (64x64, ~2.5 min GPU CUDA)
- Detection automatique de regions tissulaires
- Classification tissue/background avec uncertainty quantification
- Backends d'inference interchangeables : `subprocess` (Slideflow), `inprocess` (ONNX/OpenVINO), `triton` (stub remote)

### Integration hospitaliere
- OIDC PKCE (Keycloak dev, Azure AD prod-ready), 4 roles RBAC
- FHIR R4 (DiagnosticReport sur signature de rapport, sandbox HAPI FHIR en dev)
- PACS DICOM (C-FIND/C-STORE/C-ECHO via pynetdicom, sandbox Orthanc en dev)
- Quality metrics (kappa de Cohen et Fleiss, IoU spatial via PostGIS)
- WebSocket temps reel : evenements workflow diffuses aux clients UI

### Architecture modulaire (Strangler Fig)
6 Protocols (PEP 544) abstrayant les seams backend : `AuthProvider`,
`StorageProvider`, `SlideReader`, `TileCache` (L1 mem + L2 Redis),
`WorkflowHook` (FHIR + PACS + WS), `MLWorkerProvider`. Routes consomment
via FastAPI `Depends`. Doc canonique : [`docs/architecture/MODULAR_ARCHITECTURE.md`](docs/architecture/MODULAR_ARCHITECTURE.md).

### Infrastructure
- 1000+ tests automatises (pytest, Playwright)
- CI/CD GitHub Actions (lint, tests, build Docker, Trivy, Bandit, CodeQL, Gitleaks)
- Compose unifie pilote par profils (`core`, `cache`, `auth`, `pacs`, `fhir`, `monitoring`, `mlops`, `dev`, `prod`)

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Backend API | FastAPI (Python 3.11) |
| Lecture WSI | OpenSlide 4.0 |
| Viewer web | OpenSeadragon 4.1 (Vanilla JS) |
| Base donnees | PostgreSQL 16 + PostGIS |
| ML Framework | Slideflow 2.3+ (Phikon-v2, CUDA) |
| Frontend build | Vite |
| Reverse proxy | Nginx |

## Installation et Lancement

### Option 1 : Docker (Recommande)

Un seul `docker-compose.yml` pilote par profils. Le profil `dev` lance les
services de soutien (db + redis + keycloak + orthanc + hapi-fhir) ; le backend
et le frontend tournent en local.

```bash
cp .env.dev.example .env
docker compose --profile dev up -d

# Backend et frontend en local :
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm run dev   # http://localhost:5173
```

Pour un deploiement full (backend + frontend + nginx + monitoring) :

```bash
cp .env.prod.example .env
# editer .env, remplacer chaque CHANGE_ME_*
docker compose --profile prod --profile monitoring up -d
```

Manuel administrateur complet : [`docs/Admin/`](docs/Admin/) — topologie reseau,
matrice ports/roles, comment activer/desactiver chaque profil, fiches par service.

### Option 2 : Developpement Local

**Prerequis :** Python 3.11+, Node.js 18+, OpenSlide, PostgreSQL 16 + PostGIS (optionnel)

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (nouveau terminal)
cd frontend
npm install
npm run dev
```

**OpenSlide :**
- Windows : https://openslide.org/download/
- Linux : `sudo apt-get install openslide-tools python3-openslide`

**PostgreSQL + PostGIS (pour annotations) :**
```bash
docker compose --profile dev up postgres -d
cd backend && alembic upgrade head
```

> **Note :** Le port PostgreSQL est **5433** (pas 5432) pour eviter les conflits.

### Verification

1. Backend : http://localhost:8000/api/v1/health -> `{"status":"healthy"}`
2. Frontend : http://localhost:5173
3. API Docs : http://localhost:8000/docs
4. Cliquer sur une lame -> navigation fluide dans le viewer

## Structure Projet

```
VarunaPoC/
├── backend/                    # FastAPI + OpenSlide + SQLAlchemy
│   ├── main.py                 # App entry (feature flags + Protocol singletons)
│   ├── core/interfaces/        # 6 Protocols (Strangler Fig seams)
│   ├── routes/                 # ~15 routers, dont ws.py (WebSocket)
│   ├── services/               # cache/, readers/, storage/, workflow/, ml/
│   ├── auth/                   # OIDC + RBAC (optional, AUTH_ENABLED)
│   ├── fhir/                   # FHIR R4 (optional, FHIR_ENABLED)
│   ├── quality/                # Inter-annotator kappa (optional, QUALITY_ENABLED)
│   ├── alembic/                # Migrations DB (PostgreSQL + PostGIS)
│   └── tests/                  # 1000+ tests (pytest)
│
├── frontend/                   # Vite + Vanilla JS + OpenSeadragon
│   ├── src/
│   │   ├── main.js             # Entry + routing + boot WorkflowEventService (Sprint 15)
│   │   ├── components/         # 31 composants UI (Drawing, ML, Compare, Quality, ...)
│   │   ├── services/           # ApiService, AuthService, WorkflowEventService, AnnotationStore, ...
│   │   ├── viewers/            # ViewerManager + sync multi-lames
│   │   └── core/               # EventBus, Constants
│   └── e2e/                    # Playwright (18 suites)
│
├── docs/
│   ├── Admin/                  # Manuel administrateur (topologie, profils, ops, fiches services)
│   ├── architecture/           # MODULAR_ARCHITECTURE.md canonique (Protocols + sprints)
│   ├── Manuel/                 # Manuel utilisateur clinicien
│   ├── Deployment/             # Guides specifiques CHU (secrets, breakglass, network)
│   ├── adr/                    # Architecture Decision Records
│   ├── implementation/         # Notes d'implementation (patches, fixes documentes)
│   └── standards/              # Conformite (EU AI Act, FDA, TEFCA, eHealth)
│
├── Slides/                     # Lames de test (~60 GB, 10 formats, gitignored)
├── nginx/                      # Reverse proxy + tile cache (10 GB)
├── monitoring/                 # Prometheus + Grafana + alertes
├── docker-compose.yml          # Compose unifie (profils dev/prod/core/cache/auth/pacs/fhir/monitoring/mlops)
├── .env.dev.example            # Template variables d'env (workstation dev)
└── .env.prod.example           # Template variables d'env (production)
```

## Tests

```bash
cd backend
pytest                              # Tous les tests
pytest -m unit                      # Tests unitaires
pytest -m detection                 # Tests detection
pytest tests/test_format_detector.py  # Tests formats
```

1000+ tests passent. Quelques tests sont skipped en dev local (ils necessitent
des fichiers slides specifiques ou un PostgreSQL accessible).

## Documentation

| Document | Description |
|----------|-------------|
| [docs/Admin/](docs/Admin/) | **Manuel administrateur** : topologie reseau, profils Compose, fiches par service, ops |
| [docs/architecture/MODULAR_ARCHITECTURE.md](docs/architecture/MODULAR_ARCHITECTURE.md) | **Architecture canonique** : 6 Protocols, Strangler Fig, sprint log |
| [docs/Manuel/](docs/Manuel/) | Manuel utilisateur clinicien |
| [docs/Deployment/](docs/Deployment/) | Guides specifiques CHU (secrets, breakglass, network) |
| [docs/PROPOSAL_VARUNA_v2.md](docs/PROPOSAL_VARUNA_v2.md) | Proposition projet, analyse marche, roadmap |
| [docs/FORMATS_SUPPORTED.md](docs/FORMATS_SUPPORTED.md) | Formats supportes |
| [docs/ML_INTEGRATION.md](docs/ML_INTEGRATION.md) | Integration ML/Slideflow |
| [docs/Deployment/HOSPITAL_DEPLOYMENT_EVALUATION.md](docs/Deployment/HOSPITAL_DEPLOYMENT_EVALUATION.md) | Evaluation deploiement hospitalier |
| [docs/Deployment/DEPLOYMENT_GUIDE.md](docs/Deployment/DEPLOYMENT_GUIDE.md) | Guide deploiement production |
| API Docs | http://localhost:8000/docs (Swagger UI) |

## Etat du projet

**Tag courant :** `v0.1.0` — Waves 1-4 + standards + CI/CD complets, **62 issues fermees**.

| Wave | Statut | Contenu |
|------|--------|---------|
| Wave 1 — Le viewer qui parle pathologiste | Termine | 10 formats WSI, navigation, overview, mini-map |
| Wave 2 — L'IA qui assiste | Termine | Heatmap Slideflow, detection auto, classification |
| Wave 3 — Le cas, pas le fichier | Termine | Annotations PostGIS, labels, compare mode, quality metrics |
| Wave 4 — L'ecosysteme intelligent | Termine | Auth OIDC + RBAC + audit, FHIR R4, PACS Telemis, deep-link |
| Standards (#103-#124) | Termine | EU AI Act, FDA 510(k), TEFCA, eHealth certs, anonymisation DICOM |

**Apres v0.1.0 :** migration **Strangler Fig** en cours — 6 Protocols implementes,
9 routes cablees via `Depends`, broadcast WebSocket des workflow events
(sprint 15). Voir [`docs/architecture/MODULAR_ARCHITECTURE.md`](docs/architecture/MODULAR_ARCHITECTURE.md)
pour le sprint log et la cadence.

## Licence

Apache 2.0
