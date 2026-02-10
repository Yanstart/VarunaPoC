# Contexte Rapide - VarunaPoC

**Pour reprendre le travail rapidement**
**Derniere mise a jour:** 2026-02-08

---

## Direction Actuelle: Plateforme WSI Quality-First (MVP 15 semaines)

### Transformation
Le projet Varuna est passe d'un **PoC viewer simple** (Phase 1) a une **Plateforme WSI avec annotations, ML et detection** (Phase 2 terminee). Phase 3 (Auth, PACS, Quality Metrics) a venir.

### 3 Differenciateurs (cf. docs/PROPOSAL_VARUNA_v2.md):
1. **Quality-First Annotations** - Metriques IAA, detection outliers, versioning
2. **Continuous Learning MLOps** - Drift monitoring, feedback loops, CI/CD modeles
3. **Radical Simplicity** - Zero-config, onboarding 3 min, <100ms latence

### Positionnement Reglementaire:
- **Aujourd'hui:** Recherche et enseignement (IVDR Classe A, FDA Exempt)
- **Moyen terme:** Aide a la decision consultative
- **Long terme (optionnel):** Certification IVDR Classe C / FDA 510(k)

---

## Etat Actuel du Projet

### Version: 1.7.0
### Date: 2026-02-08
### Branche: feature/slideflow-integration
### Phase: 2 TERMINEE, Phase 3 A VENIR

### Ce qui fonctionne:
- [x] Navigation hierarchique dans /Slides
- [x] Viewer single avec tile streaming DZI (< 15ms keep-alive)
- [x] Compare Mode (multi-viewer 2x1, 2x2, synchronise)
- [x] 10 formats vendor-neutral via OpenSlide (SVS, NDPI, MRXS, SCN, BIF, TIFF, CZI, DICOM, Sakura, Trestle)
- [x] 94 lames testees, 3 corrompues correctement rejetees
- [x] Annotations CRUD (PostgreSQL + PostGIS, 5 outils dessin, labels couleurs, export GeoJSON)
- [x] ML Slideflow + Phikon-v2 (heatmaps CUDA, detection regions, classification + uncertainty)
- [x] Detection automatique regions tissulaires (heatmap -> scipy -> shapely -> GeoJSON)
- [x] Counting/classification stats temps reel
- [x] 94 tests automatises (pytest)
- [x] CI/CD GitHub Actions (lint, tests, Docker, Trivy, Bandit, CodeQL, Gitleaks)

### Phase 3 (A VENIR - semaines 10-13):
- [ ] Auth RBAC + JWT + audit trail
- [ ] Quality metrics annotations (kappa inter-annotateur)
- [ ] Integration PACS Telemis (command plugin)

### Phase 4 (A VENIR - semaines 14-15):
- [ ] Tests E2E (Playwright/Selenium)
- [ ] Documentation + formation utilisateurs
- [ ] Mise en production

---

## Documentation Strategique

| Document | Description |
|----------|-------------|
| `docs/PROPOSAL_VARUNA_v2.md` | Proposition projet v2 (marche, architecture, roadmap, couts) |
| `HOSPITAL_DEPLOYMENT_EVALUATION.md` | Evaluation deploiement hospitalier (gaps, comparaison, plan) |
| `.claude/docs/ARCHITECTURE_V3.md` | Architecture cible (modules, services) |
| `.claude/docs/MODULE_CONTRACTS.md` | Interfaces entre modules |

---

## Alertes

### SECURITE: PAS D'AUTHENTIFICATION RUNTIME
```
Score CI/CD: OK (Trivy, Bandit, CodeQL, Gitleaks)
Score runtime: 0 (pas d'auth, pas d'audit trail)
Action: Phase 3, Sprint 1 (Auth RBAC + JWT)
```

### DEPLOIEMENT HOSPITALIER: PAS PRET
```
Verdict: NOT production-ready (cf. HOSPITAL_DEPLOYMENT_EVALUATION.md)
Gaps critiques: Auth, audit trail, PACS, PHI
Timeline vers clinical: 9-12 mois
Positioning actuel: Recherche/enseignement only
```

---

## Comment Demarrer

### Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# -> http://localhost:5173
```

### PostgreSQL + PostGIS (pour annotations)
```bash
docker compose -f docker-compose.dev.yml up postgres -d
cd backend && alembic upgrade head
# Note: port 5433 (pas 5432)
```

---

## Fichiers Cles a Connaitre

| Tache | Fichier(s) |
|-------|-----------|
| Entry point frontend | `frontend/src/main.js` |
| Entry point backend | `backend/main.py` (v1.7.0) |
| Config/Constantes | `frontend/src/core/Constants.js` |
| Gestionnaire viewers | `frontend/src/viewers/ViewerManager.js` |
| Tile streaming | `backend/services/tile_server.py` |
| Format detection | `backend/services/format_detector.py` |
| Annotations CRUD | `backend/routes/annotations.py` |
| ML inference | `backend/routes/ml.py` |
| Annotation overlay | `frontend/src/components/AnnotationLayer.js` |
| Drawing tools | `frontend/src/components/DrawingTools.js` |
| ML heatmap | `frontend/src/components/HeatmapOverlay.js` |
| Detection panel | `frontend/src/components/DetectionPanel.js` |
| Annotation store | `frontend/src/services/AnnotationStore.js` |
| DB models | `backend/models/annotation.py` |
| DB migrations | `backend/alembic/` |

---

## Architecture en 30 Secondes

```
User -> main.js -> showHomePage() / showViewerPage() / showComparePage()
                        |
                        v
             CompareLayout -> ViewerPanel[] -> ViewerInstance -> OpenSeadragon
                   |
                   +-- SyncControls -> SyncController -> EventBus
                   +-- AnnotationLayer (SVG overlay)
                   +-- DrawingTools (5 outils)
                   +-- DetectionPanel + CountingPanel
                   +-- HeatmapOverlay (canvas ML)
                   +-- LayerManager (visibilite)

Backend:
  FastAPI -> routes/slides.py    (tiles DZI, info, browse)
          -> routes/annotations.py (CRUD PostGIS)
          -> routes/ml.py         (Slideflow + Phikon-v2)
```

**Patterns:** Singleton (EventBus, ViewerManager), Factory (ViewerFactory), Observer (EventBus), Mediator (SyncController), State (ViewerState)

---

## Stack Technologique

| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI (Python 3.11) |
| Lecture WSI | OpenSlide 4.0 |
| Viewer | OpenSeadragon 4.1 (Vanilla JS) |
| Base donnees | PostgreSQL 15 + PostGIS (port 5433) |
| ML | Slideflow 2.3+ (Phikon-v2, CUDA) |
| Frontend build | Vite |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus (optionnel) |

---

## Contacts / References

- **Repository:** https://github.com/Yanstart/VarunaPoC
- OpenSeadragon: https://openseadragon.github.io/docs/
- OpenSlide: https://openslide.org/api/python/
- FastAPI: https://fastapi.tiangolo.com/
- Slideflow: https://slideflow.dev/

---

## Git Branches

- `main` - Production stable
- `feature/slideflow-integration` - Developpement actif (Phase 2)
