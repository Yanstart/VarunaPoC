# Contexte Rapide - VarunaPoC

**Pour reprendre le travail rapidement**

---

## NOUVELLE DIRECTION: V3 MLOps-Ready (TFE 2025-2026)

### Transformation Majeure
Le projet Varuna passe d'un **PoC viewer simple** vers une **Plateforme WSI modulaire et MLOps-ready**.

### Objectifs TFE:
1. Viewer WSI vendor-neutral (12 formats) - FAIT
2. Systeme de routage par tags pour modeles IA specialises - A FAIRE
3. Infrastructure MLOps (capture feedback, versioning, re-entrainement) - A FAIRE
4. Conformite RGPD/MDR/AI Act - A FAIRE
5. Integration PACS Telemis - A FAIRE

### Angles Morts a Resoudre:
- IA figee -> apprentissage continu
- Corrections perdues -> capture feedback pathologistes
- Resultats binaires -> cartographie de confiance
- Vendor lock-in -> architecture ouverte (deja fait)

---

## Etat Actuel du Projet

### Version: 2.0.1 (Bugfix Compare Mode)
### Date: 2025-12-30
### Prochaine Version: 3.0 (MLOps-Ready)

### Ce qui fonctionne:
- [x] Navigation hierarchique dans /Slides
- [x] Viewer single avec tile streaming DZI
- [x] Compare Mode (multi-viewer 2x1, 2x2)
- [x] Synchronisation pan/zoom (toggle)
- [x] Mini-map (navigator) sur chaque viewer
- [x] Formats: .mrxs, .bif, .tif (12 formats via OpenSlide)

### Ce qui est planifie (V3):
- [ ] Systeme de tags (organe, coloration, marqueur)
- [ ] Routage automatique vers modeles IA
- [ ] Capture feedback pathologistes
- [ ] Infrastructure MLOps (MLflow, DVC)
- [ ] Securite (OAuth2, audit trail, chiffrement)
- [ ] Integration PACS Telemis

---

## Documentation Architecture V3

### Documents Crees par le Conseil des Architectes:

**Architecture Globale:**
- `docs/architecture/ARCHITECTURE_V3.md` - Vision complete
- `docs/architecture/MODULE_CONTRACTS.md` - Interfaces entre modules
- `docs/architecture/REFACTORING_PLAN.md` - Plan de migration

**Securite (CRITIQUE - Score actuel: 3.1/10):**
- `docs/SECURITY_ARCHITECTURE.md` - Architecture complete
- `docs/SECURITY_EXECUTIVE_SUMMARY.md` - Resume direction
- `docs/SECURITY_PHASE1_IMPLEMENTATION.md` - Actions immediates

**MLOps:**
- `docs/MLOPS_ARCHITECTURE.md` - Reference principale (60+ pages)
- `docs/MLOPS_INTEGRATION_GUIDE.md` - Guide step-by-step
- `backend/services/ml/tag_extractor.py` - Code pret
- `backend/services/ml/tag_router.py` - Code pret
- `backend/database/schema_ml.sql` - Schema PostgreSQL
- `backend/config/ml_routes.yaml` - Configuration routage

**Infrastructure:**
- `docs/INFRASTRUCTURE_ARCHITECTURE.md` - Architecture complete
- `docker-compose.optimized.yml` - Production-ready
- `nginx/nginx.conf` - Load balancing + cache
- `monitoring/` - Prometheus + Grafana

**Backend Refactoring:**
- `docs/BACKEND_REFACTORING.md` - Plan complet (37h)
- `docs/BACKEND_ARCHITECTURE_DIAGRAM.md` - Diagrammes

**Frontend Refactoring:**
- `docs/FRONTEND_REFACTORING.md` - Plan V3 features (70 pages)

---

## Alertes Critiques

### SECURITE: AUCUNE AUTHENTIFICATION
```
Score actuel: 0/10 sur authentification
Risque: Acces libre a toutes les donnees patients
Action: Implementer HTTP Basic Auth CETTE SEMAINE
```

### CONFORMITE: NON CONFORME RGPD
```
Statut: Systeme NON utilisable en production
Risque: Amende jusqu'a 20M EUR
Action: Phase 1 securite (5k EUR, 1-2 semaines)
```

---

## Roadmap V3 (12-18 mois)

### Phase 2.0: Preparation (2 semaines)
- [ ] Abstraction Storage (StorageProvider)
- [ ] Configuration centralisee (pydantic-settings)
- [ ] API versioning (/api/v1/, /api/v2/)
- [ ] Tests unitaires (coverage >80%)
- [ ] Securite Phase 1 (Basic Auth, HTTPS, Audit)

### Phase 2.1: ML Service Prototype (3 semaines)
- [ ] Service FastAPI separe
- [ ] Modele mock (detections aleatoires)
- [ ] Heatmap generator (overlays confiance)
- [ ] Frontend: bouton "Run AI", affichage heatmap

### Phase 3.1: Infrastructure MLOps (Mois 1-3)
- [ ] Setup MLflow tracking server
- [ ] Setup DVC avec remote storage
- [ ] Database PostgreSQL + schema ML
- [ ] Setup Label Studio

### Phase 3.2: Tag System & Routing (Mois 4-5)
- [ ] TagExtractor integration (code pret)
- [ ] TagRouter integration (code pret)
- [ ] UI assignation manuelle tags

### Phase 3.3: Feedback Pipeline (Mois 6-7)
- [ ] Endpoints API feedback
- [ ] FeedbackPanel UI dans viewer
- [ ] Dashboard monitoring

### Phase 3.4: Continuous Learning (Mois 8-11)
- [ ] Pipeline Airflow re-entrainement
- [ ] A/B testing infrastructure
- [ ] Monitoring drift actif

### Phase 3.5: Production Models (Mois 12-18)
- [ ] Gleason grading (prostate)
- [ ] Ki-67 counting (sein)
- [ ] HER2 scoring (sein)

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

### Docker (Phase 2.5+)
```bash
docker-compose -f docker-compose.optimized.yml up -d
# -> http://localhost (Nginx load balanced)
```

---

## Fichiers Cles a Connaitre

| Tache | Fichier(s) |
|-------|-----------|
| Point d'entree frontend | `frontend/src/main.js` |
| Config/Constantes | `frontend/src/core/Constants.js` |
| Gestionnaire viewers | `frontend/src/viewers/ViewerManager.js` |
| Sync entre viewers | `frontend/src/viewers/SyncController.js` |
| Layout multi-viewer | `frontend/src/components/CompareLayout.js` |
| Tile streaming | `backend/services/tile_server.py` |
| Navigation dossiers | `backend/services/folder_browser.py` |
| **NOUVEAU: Tags ML** | `backend/services/ml/tag_extractor.py` |
| **NOUVEAU: Routage ML** | `backend/services/ml/tag_router.py` |
| **NOUVEAU: Config ML** | `backend/config/ml_routes.yaml` |

---

## Architecture en 30 Secondes

### Actuelle (V2):
```
User -> main.js -> showHomePage() / showViewerPage() / showComparePage()
                         |
                         v
              CompareLayout -> ViewerPanel[] -> ViewerInstance -> OpenSeadragon
                    |
                    +-- SyncControls -> SyncController -> EventBus
```

### Cible (V3):
```
API Gateway (Kong/Traefik)
    +-- Viewer Service (tuiles, metadonnees)
    +-- ML Service (inference, feedback loop)
    +-- PACS Plugin (DICOM integration)
    +-- Storage Service (filesystem/S3/PACS abstrait)
```

**Patterns:**
- Singleton: EventBus, ViewerManager, ApiService, StateStore (V3)
- Factory: ViewerFactory
- Observer: EventBus
- Mediator: SyncController
- State: ViewerState
- **NOUVEAU V3:** Clean Architecture / Hexagonal, Repository Pattern

---

## Stack Technologique V3

### Backend:
- Python 3.11+ / FastAPI (async)
- OpenSlide (lecture WSI)
- PostgreSQL (metadonnees, feedback, ML)
- Redis (cache tuiles, sessions)
- MLflow (tracking modeles)
- DVC (versioning datasets)

### Frontend:
- Vite + Vanilla JS (PAS de React)
- OpenSeadragon (viewer)
- WebGL (heatmaps confiance)
- StateStore (gestion etat centralisee)

### Infrastructure:
- Docker / Kubernetes
- Nginx (load balancing, cache)
- Prometheus + Grafana (monitoring)
- HTTP/2 (HTTP/3 QUIC futur)

---

## Metriques de Performance (TFE Section 5.2)

| Metrique | Exigence | Actuel | Cible V3 |
|----------|----------|--------|----------|
| Temps chargement (P95) | < 2s | ~3s | 1.3-1.8s |
| Latence navigation (P95) | < 100ms | ~150ms | 65ms |
| Disponibilite | > 99.5% | N/A | 99.73% |
| Utilisateurs simultanes | 10 | ~3 | 15+ |

---

## Regles Importantes (CLAUDE.md)

1. **Pas d'emojis dans les logs Python** (cause erreurs encodage Windows)
2. **Documenter les erreurs** dans `/docs/ERROR_*.md`
3. **Documenter les endpoints** avec docstrings FastAPI completes
4. **Vanilla JS uniquement** - pas de React/Vue/Angular
5. **Tile streaming** - jamais charger l'image complete
6. **NOUVEAU: Securite by Design** - Auth + Audit sur tout endpoint
7. **NOUVEAU: Clean Architecture** - Isolation modules, interfaces claires

---

## Contacts / References

- OpenSeadragon: https://openseadragon.github.io/docs/
- OpenSlide: https://openslide.org/api/python/
- FastAPI: https://fastapi.tiangolo.com/
- MLflow: https://mlflow.org/docs/latest/index.html
- DVC: https://dvc.org/doc
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/

---

## Git Branches

- `main` - Production stable
- `develop` - Developpement actif (branche actuelle)
- `feature/mlops-infrastructure` - A creer pour Phase 3
- `feature/security-phase1` - A creer URGENT

---

**Derniere mise a jour:** 2025-12-31
**Version contexte:** 3.0
**Auteur:** Conseil des Architectes VarunaPoC
