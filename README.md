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
- Labels avec couleurs, CRUD complet, export GeoJSON
- Statistiques temps reel (comptage par label/type, distribution confiance)

### ML / IA (Slideflow + Phikon-v2)
- Heatmaps d'attention (64x64, ~2.5 min GPU CUDA)
- Detection automatique de regions tissulaires
- Classification tissue/background avec uncertainty quantification

### Infrastructure
- 94 tests automatises (pytest)
- CI/CD GitHub Actions (lint, tests, build Docker, Trivy, Bandit, CodeQL, Gitleaks)
- Docker multi-container

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Backend API | FastAPI (Python 3.11) |
| Lecture WSI | OpenSlide 4.0 |
| Viewer web | OpenSeadragon 4.1 (Vanilla JS) |
| Base donnees | PostgreSQL 15 + PostGIS |
| ML Framework | Slideflow 2.3+ (Phikon-v2, CUDA) |
| Frontend build | Vite |
| Reverse proxy | Nginx |

## Installation et Lancement

### Option 1 : Docker (Recommande)

```bash
# Deploiement Phase 2 (backend + frontend + PostgreSQL)
docker compose -f docker-compose.dev.yml up -d

# Acces:
# Frontend: http://localhost
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

Voir [DOCKER_DEPLOYMENT_CHECKLIST.md](DOCKER_DEPLOYMENT_CHECKLIST.md) pour le guide complet.

### Option 2 : Developpement Local

**Prerequis :** Python 3.11+, Node.js 18+, OpenSlide, PostgreSQL 15 + PostGIS (optionnel)

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
docker compose -f docker-compose.dev.yml up postgres -d
cd backend && alembic upgrade head
```

> **Note :** Le port PostgreSQL est **5433** (pas 5432) pour eviter les conflits.

### Verification

1. Backend : http://localhost:8000/api/health -> `{"status":"healthy"}`
2. Frontend : http://localhost:5173
3. API Docs : http://localhost:8000/docs
4. Cliquer sur une lame -> navigation fluide dans le viewer

## Structure Projet

```
VarunaPoC/
├── backend/                    # FastAPI + OpenSlide + SQLAlchemy
│   ├── main.py                 # Entry point (v1.7.0)
│   ├── routes/
│   │   ├── slides.py           # API slides (list, browse, info, tiles, dzi)
│   │   ├── annotations.py      # CRUD annotations + labels + stats
│   │   └── ml.py               # ML inference (heatmap, detect, predict)
│   ├── services/
│   │   ├── format_detector.py  # Detection 10+ formats
│   │   ├── tile_server.py      # Streaming tuiles DZI
│   │   └── detection/          # Pipeline heatmap -> GeoJSON
│   ├── models/                 # ORM (Annotation, AnnotationLabel)
│   ├── schemas/                # Pydantic (annotation, geojson, detection)
│   ├── alembic/                # Migrations DB
│   └── tests/                  # 94 tests (pytest)
│
├── frontend/                   # Vite + Vanilla JS + OpenSeadragon
│   ├── src/
│   │   ├── main.js             # Entry point + routing
│   │   ├── components/
│   │   │   ├── AnnotationLayer.js   # SVG overlay annotations
│   │   │   ├── DrawingTools.js      # Rectangle, Polygon, etc.
│   │   │   ├── LayerManager.js      # Visibilite/opacite
│   │   │   ├── DetectionPanel.js    # Detection automatique
│   │   │   ├── CountingPanel.js     # Statistiques temps reel
│   │   │   ├── HeatmapOverlay.js    # Overlay ML canvas
│   │   │   ├── MLPanel.js           # Panel analyse ML
│   │   │   ├── CompareLayout.js     # Mode multi-viewer
│   │   │   └── FolderBrowser.js     # Navigation dossiers
│   │   ├── services/
│   │   │   ├── ApiService.js        # Client API singleton
│   │   │   └── AnnotationStore.js   # Etat annotations
│   │   └── core/
│   │       ├── EventBus.js          # Pub/sub decouplage
│   │       └── Constants.js         # Configuration
│   └── index.html
│
├── docs/                       # Documentation technique
│   ├── PROPOSAL_VARUNA_v2.md   # Proposal projet v2
│   ├── ARCHITECTURE.md         # Architecture technique
│   ├── Manuel/                 # Manuel utilisateur
│   └── Deployment/             # Guides deploiement
│
├── Slides/                     # Lames de test (gitignored)
├── docker-compose.dev.yml      # PostgreSQL+PostGIS (port 5433)
└── HOSPITAL_DEPLOYMENT_EVALUATION.md  # Evaluation deploiement hospitalier
```

## Tests

```bash
cd backend
pytest                              # Tous les tests
pytest -m unit                      # Tests unitaires
pytest -m detection                 # Tests detection
pytest tests/test_format_detector.py  # Tests formats
```

94 tests passent, 3 skipped (necessitent fichiers slides specifiques).

## Documentation

| Document | Description |
|----------|-------------|
| [PROPOSAL_VARUNA_v2.md](docs/PROPOSAL_VARUNA_v2.md) | Proposition projet, analyse marche, roadmap |
| [HOSPITAL_DEPLOYMENT_EVALUATION.md](HOSPITAL_DEPLOYMENT_EVALUATION.md) | Evaluation deploiement hospitalier |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture technique |
| [FORMATS_SUPPORTED.md](docs/FORMATS_SUPPORTED.md) | Formats supportes |
| [ML_INTEGRATION.md](docs/ML_INTEGRATION.md) | Integration ML/Slideflow |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Guide deploiement production |
| [docs/Manuel/](docs/Manuel/) | Manuel utilisateur |
| API Docs | http://localhost:8000/docs (Swagger UI) |

## Roadmap

| Phase | Statut | Contenu |
|-------|--------|---------|
| **Phase 1** (sem. 1-3) | Termine | Viewer basique, detection formats, overview |
| **Phase 2** (sem. 4-9) | Termine | 10 formats, annotations PostGIS, ML Slideflow, compare mode |
| **Phase 3** (sem. 10-13) | A venir | Auth RBAC, audit trail, quality metrics, PACS Telemis |
| **Phase 4** (sem. 14-15) | A venir | Tests E2E, documentation, mise en production |

Voir [PROPOSAL_VARUNA_v2.md](docs/PROPOSAL_VARUNA_v2.md) pour la roadmap complete.

## Licence

Apache 2.0

---

**VERSION :** 1.7.0
**DATE :** 2026-02-08
**BRANCHE :** feature/slideflow-integration
