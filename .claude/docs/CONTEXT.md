# Contexte Rapide - VarunaPoC

**Pour reprendre le travail rapidement**
**Derniere mise a jour:** 2026-02-12

---

## Direction Actuelle: Plateforme WSI Quality-First (MVP 15 semaines)

### Transformation
Le projet Varuna est passe d'un **PoC viewer simple** (Phase 1) a une **Plateforme WSI complete** avec annotations, ML, auth OIDC, audit trail et quality metrics. Phase 3.3 (Integration PACS Telemis) en cours.

### 3 Differenciateurs (cf. docs/PROPOSAL_VARUNA_v2.md):
1. **Quality-First Annotations** - Metriques IAA (kappa FAIT), detection outliers, versioning
2. **Continuous Learning MLOps** - Drift monitoring, feedback loops, CI/CD modeles
3. **Radical Simplicity** - Zero-config, onboarding 3 min, <100ms latence

### Positionnement Reglementaire:
- **Aujourd'hui:** Recherche et enseignement (IVDR Classe A, FDA Exempt)
- **Moyen terme:** Aide a la decision consultative
- **Long terme (optionnel):** Certification IVDR Classe C / FDA 510(k)

---

## Etat Actuel du Projet

### Version: 2.0.0
### Date: 2026-02-12
### Branche: main (commit 1b867c5)
### Phase: 3.1 Auth COMPLETE, 3.2 Quality COMPLETE, 3.3 PACS EN COURS

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
- [x] **Auth OIDC PKCE** (Keycloak dev, Azure AD prod-ready)
- [x] **RBAC 4 roles claims-based** (LECTURE_SEULE, INFIRMIER, MEDECIN, ADMIN_TECHNIQUE)
- [x] **JWT RS256/ES256** validation, JWKS cache TTL 1h
- [x] **Audit trail** dual DB+JSON (INFO/WARNING/CRITICAL)
- [x] **Break-glass** emergency sessions 30min
- [x] **Session roaming** cross-workstation
- [x] **FHIR R4 stub** DiagnosticReport builder
- [x] **Quality metrics** (Cohen/Fleiss kappa, F1, confusion matrix, IoU, disagreement heatmap)
- [x] **QualityPanel** frontend (annotator selector, kappa badge, disagreement overlay)
- [x] 156 tests automatises (pytest), 21 skipped
- [x] CI/CD GitHub Actions 8/8 jobs pass (lint, tests, Docker, security scans)

### Phase 3.3 (EN COURS):
- [ ] Integration PACS Telemis (command plugin)
- [ ] Endpoint by-accession (resolution accession -> slide)
- [ ] Contexte patient automatique

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
| `docs/Deployment/TELEMIS_INTEGRATION_GUIDE.md` | Guide integration PACS Telemis |
| `docs/architecture/SYSTEM_PATTERNS.md` | Patterns systeme (Phase 3.1) |
| `.claude/docs/ARCHITECTURE_V3.md` | Architecture cible (modules, services) |
| `.claude/docs/MODULE_CONTRACTS.md` | Interfaces entre modules |

---

## Alertes

### SECURITE: AUTH OIDC OPERATIONNELLE
```
Score CI/CD: OK (Trivy, Bandit, CodeQL, Gitleaks, HIPAA)
Score runtime: 7/10 (OIDC PKCE, RBAC 4 roles, audit trail, break-glass)
Manque: chiffrement au repos, de-identification PHI (Post-MVP)
```

### DEPLOIEMENT HOSPITALIER: PRESQUE PRET
```
Verdict: NOT production-ready (cf. HOSPITAL_DEPLOYMENT_EVALUATION.md)
Gaps restants: PACS integration, E2E tests, formation, PHI de-identification
Timeline vers clinical: 6-9 mois (ameliore depuis Phase 3.1)
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

### PostgreSQL + PostGIS + Keycloak (pour auth + annotations)
```bash
docker compose --profile dev up -d
cd backend && alembic upgrade head
# PostgreSQL port 5433, Keycloak port 8180
```

### Keycloak Test Users
| Username | Password | Role |
|----------|----------|------|
| dr.martin | password | MEDECIN |
| nurse.dupont | password | INFIRMIER |
| admin | password | ADMIN_TECHNIQUE |
| viewer | password | LECTURE_SEULE |

---

## Fichiers Cles a Connaitre

| Tache | Fichier(s) |
|-------|-----------|
| Entry point frontend | `frontend/src/main.js` |
| Entry point backend | `backend/main.py` (v2.0.0) |
| Config/Constantes | `frontend/src/core/Constants.js` |
| Gestionnaire viewers | `frontend/src/viewers/ViewerManager.js` |
| Tile streaming | `backend/services/tile_server.py` |
| Format detection | `backend/services/format_detector.py` |
| Annotations CRUD | `backend/routes/annotations.py` |
| ML inference | `backend/routes/ml.py` |
| Auth OIDC | `backend/auth/` (11 fichiers) |
| Audit trail | `backend/auth/audit.py` |
| Quality metrics | `backend/quality/` (7 fichiers) |
| Quality panel | `frontend/src/components/QualityPanel.js` |
| Auth frontend | `frontend/src/services/AuthService.js` |
| FHIR stub | `backend/fhir/` (4 fichiers) |
| Annotation overlay | `frontend/src/components/AnnotationLayer.js` |
| Drawing tools | `frontend/src/components/DrawingTools.js` |
| ML heatmap | `frontend/src/components/HeatmapOverlay.js` |
| Detection panel | `frontend/src/components/DetectionPanel.js` |
| Annotation store | `frontend/src/services/AnnotationStore.js` |
| DB models | `backend/models/` (annotation.py, quality_report.py) |
| DB migrations | `backend/alembic/` (001, 002, 003) |

---

## Architecture en 30 Secondes

```
User -> main.js -> [Auth Guard] -> showHomePage() / showViewerPage() / showComparePage()
                        |
                        v
             CompareLayout -> ViewerPanel[] -> ViewerInstance -> OpenSeadragon
                   |
                   +-- SyncControls -> SyncController -> EventBus
                   +-- AnnotationLayer (SVG overlay + disagreement)
                   +-- DrawingTools (5 outils)
                   +-- DetectionPanel + CountingPanel
                   +-- HeatmapOverlay (canvas ML)
                   +-- QualityPanel (kappa, confusion, F1, IoU)
                   +-- LayerManager (visibilite)

Auth:
  AuthService (PKCE) -> LoginPage / UserMenu -> role-based component visibility

Backend:
  FastAPI -> routes/slides.py       (tiles DZI, info, browse)
          -> routes/annotations.py  (CRUD PostGIS)
          -> routes/ml.py           (Slideflow + Phikon-v2)
          -> auth/routes.py         (OIDC, JWT, session, audit)
          -> fhir/routes.py         (DiagnosticReport)
          -> quality/routes.py      (kappa, F1, confusion, IoU, disagreements)
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
| Auth | OIDC PKCE (Keycloak dev, Azure AD prod) |
| ML | Slideflow 2.3+ (Phikon-v2, CUDA) |
| Frontend build | Vite |
| CI/CD | GitHub Actions (CI + Security + CD) |
| Monitoring | Prometheus (optionnel) |

---

## Contacts / References

- **Repository:** https://github.com/Yanstart/VarunaPoC
- OpenSeadragon: https://openseadragon.github.io/docs/
- OpenSlide: https://openslide.org/api/python/
- FastAPI: https://fastapi.tiangolo.com/
- Slideflow: https://slideflow.dev/
- Keycloak: https://www.keycloak.org/documentation

---

## Git Branches

- `main` - Production stable (commit 1b867c5, all phases merged)
- `feature/slideflow-integration` - Merged to main (Phase 3.1 + 3.2 + 4)
