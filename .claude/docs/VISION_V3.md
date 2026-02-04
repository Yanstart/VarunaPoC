# VARUNA V3 - Vision MLOps-Ready

## Executive Summary

**Date:** 2025-12-31
**Auteurs:** Conseil des Architectes VarunaPoC
**Statut:** Approuve pour implementation

---

## 1. Transformation Strategique

### De PoC Viewer vers Plateforme MLOps

```
AVANT (V2):                          APRES (V3):
+------------------+                 +----------------------------------+
| Simple Viewer    |                 | Plateforme MLOps-Ready           |
| - Tuiles DZI     |      =>         | - Viewer + IA specialisees       |
| - Navigation     |                 | - Apprentissage continu          |
| - Compare mode   |                 | - Feedback pathologistes         |
+------------------+                 | - Conformite RGPD/MDR/AI Act     |
                                     +----------------------------------+
```

### Angles Morts Resolus

| Angle Mort Commercial | Solution Varuna V3 |
|-----------------------|-------------------|
| IA figee | Continuous Learning avec MLflow + feedback |
| Corrections perdues | Capture systematique (approve/correct/reject) |
| Resultats binaires | Cartographie confiance (heatmaps WebGL) |
| Collaboration limitee | Co-visualisation temps reel (futur) |
| Vendor lock-in | Architecture ouverte (OpenSlide, standards) |

---

## 2. Architecture Cible

### Vue C4 - Niveau Container

```
                    +-------------------+
                    |   Load Balancer   |
                    |   (Nginx/Kong)    |
                    +--------+----------+
                             |
         +-------------------+-------------------+
         |                   |                   |
+--------v--------+ +--------v--------+ +--------v--------+
|  Viewer Service | |   ML Service    | |  PACS Plugin    |
|  (FastAPI)      | |  (FastAPI)      | |  (DICOM)        |
|  - Tuiles       | |  - Inference    | |  - Import       |
|  - Metadata     | |  - Feedback     | |  - Export       |
|  - Navigation   | |  - Tags/Routing | |  - Telemis      |
+-----------------+ +-----------------+ +-----------------+
         |                   |                   |
         +-------------------+-------------------+
                             |
                    +--------v----------+
                    |  Storage Layer    |
                    |  (Abstrait)       |
                    |  - Filesystem     |
                    |  - S3/MinIO       |
                    |  - PACS DICOM     |
                    +-------------------+
```

### Stack Technologique

| Couche | Technologies |
|--------|-------------|
| **Frontend** | Vite + Vanilla JS + OpenSeadragon + WebGL |
| **Backend** | Python 3.11+ + FastAPI (async) |
| **ML/IA** | MLflow + DVC + Label Studio + Evidently AI |
| **Database** | PostgreSQL (metadata, feedback) + Redis (cache) |
| **Infrastructure** | Docker + Kubernetes + Nginx + Prometheus |
| **Securite** | OAuth2/OIDC + TLS 1.3 + Audit Trail |

---

## 3. Systeme de Routage par Tags (Section 4.3 TFE)

### Concept

```
Slide Input --> Tag Extraction --> Route Selection --> Model Inference
                    |                    |                    |
              +-----v-----+        +-----v-----+        +-----v-----+
              | organ     |        | Route DB  |        | Gleason   |
              | stain     |   =>   | Config    |   =>   | Ki-67     |
              | marker    |        | YAML      |        | HER2      |
              | task      |        |           |        | Generic   |
              +-----------+        +-----------+        +-----------+
```

### Tags Supportes

- **organ:** prostate, breast, colon, lung, skin, liver, kidney, lymph_node
- **stain:** H&E, IHC, IF, special
- **marker:** Ki-67, HER2, PD-L1, p53, ER, PR, CD3, CD20
- **task:** grading, counting, classification, detection, segmentation

### Routage Exemple

```yaml
# backend/config/ml_routes.yaml
routes:
  - name: gleason_grading
    tags: {organ: prostate, stain: H&E}
    model: models/gleason_v2.1

  - name: ki67_counting
    tags: {organ: breast, stain: IHC, marker: Ki-67}
    model: models/ki67_counter_v1.3

  - name: fallback
    tags: {}  # Match tout
    model: models/generic_tumor_detection
```

---

## 4. Infrastructure MLOps (Section 4.4 TFE)

### Pipeline de Feedback

```
+-------------+     +----------------+     +---------------+
| Pathologist |---->| Varuna Viewer  |---->| Feedback API  |
| Decision    |     | (Accept/Reject)|     | (PostgreSQL)  |
+-------------+     +----------------+     +-------+-------+
                                                   |
                                                   v
+---------------+     +----------------+     +-----+-------+
| New Model     |<----| MLflow Train   |<----| DVC Dataset |
| (A/B Testing) |     | Pipeline       |     | (Versioned) |
+---------------+     +----------------+     +-------------+
```

### Declencheurs Re-entrainement

1. **100+ corrections** pour un modele specifique
2. **Approval rate < 85%** sur 7 jours
3. **30 jours** depuis dernier re-entrainement
4. **Drift detecte** (data ou prediction shift)

### Outils

| Fonction | Outil | Justification |
|----------|-------|---------------|
| Tracking experiments | MLflow | Standard industrie, UI integree |
| Versioning datasets | DVC | Git-like pour data, S3 compatible |
| Annotation | Label Studio | Open source, API REST |
| Drift detection | Evidently AI | Rapports automatises |
| Orchestration | Airflow (futur) | DAGs, scheduling, monitoring |

---

## 5. Conformite Reglementaire (Section 4.5 TFE)

### Statut Actuel: CRITIQUE

| Regulation | Statut | Risque | Action |
|------------|--------|--------|--------|
| **RGPD** | NON CONFORME | 20M EUR | Phase 1 securite |
| **MDR 2017/745** | N/A (pas IA prod) | Retrait marche | Documentation |
| **AI Act 2024/1689** | N/A (pas IA prod) | 35M EUR | Preparation |
| **ISO 15189** | NON CONFORME | Perte accreditation | Audit trail |

### Plan de Mise en Conformite

**Phase 1 (URGENT - 1-2 semaines):**
- HTTP Basic Auth (temporaire)
- HTTPS (TLS 1.3)
- Audit logs fichier
- Security headers

**Phase 2 (1-2 mois):**
- OAuth2 + JWT (Keycloak/Azure AD)
- RBAC (5 roles)
- MFA
- Pseudonymisation

**Phase 3 (3-6 mois):**
- Chiffrement at rest
- SIEM (ELK)
- AIPD validee
- Conformite complete

---

## 6. Metriques de Performance (Section 5.2 TFE)

### Objectifs

| Metrique | Exigence TFE | Architecture V3 |
|----------|--------------|-----------------|
| Temps chargement (P95) | < 2s (5 Go) | 1.3-1.8s (cache 3 niveaux) |
| Latence navigation | < 100ms | 65ms (HTTP/2, Redis) |
| Disponibilite | > 99.5% | 99.73% (HA, failover) |
| Utilisateurs simultanes | 10 | 15+ (load balancing) |

### Strategies d'Optimisation

1. **Cache 3 niveaux:** Browser (IndexedDB) -> Redis -> Nginx
2. **Load balancing:** 2+ backends, least connections
3. **HTTP/2:** Multiplexing, keepalive
4. **WebGL:** Heatmaps GPU-acceleres (60 fps)
5. **Lazy loading:** Tuiles on-demand uniquement

---

## 7. Roadmap Implementation

### Phase 2.0: Preparation (Semaines 1-2)
- [ ] Abstraction Storage (StorageProvider interface)
- [ ] Configuration centralisee (pydantic-settings)
- [ ] API versioning (/api/v1/, /api/v2/)
- [ ] Tests unitaires (coverage >80%)
- [ ] **URGENT: Securite Phase 1**

### Phase 2.1: ML Service Prototype (Semaines 3-5)
- [ ] Service FastAPI separe
- [ ] Modele mock (detections aleatoires)
- [ ] Heatmap generator
- [ ] Frontend: bouton "Run AI"

### Phase 3.1: Infrastructure MLOps (Mois 1-3)
- [ ] MLflow tracking server
- [ ] DVC remote storage
- [ ] PostgreSQL schema ML
- [ ] Label Studio

### Phase 3.2: Tag System (Mois 4-5)
- [ ] TagExtractor integration
- [ ] TagRouter integration
- [ ] UI tags

### Phase 3.3: Feedback Pipeline (Mois 6-7)
- [ ] API feedback
- [ ] FeedbackPanel UI
- [ ] Dashboard monitoring

### Phase 3.4: Continuous Learning (Mois 8-11)
- [ ] Pipeline Airflow
- [ ] A/B testing
- [ ] Drift monitoring

### Phase 3.5: Production Models (Mois 12-18)
- [ ] Gleason (prostate)
- [ ] Ki-67 (sein)
- [ ] HER2 (sein)

---

## 8. Livrables Crees (2025-12-31)

### Documentation (400+ pages)

| Document | Contenu | Localisation |
|----------|---------|--------------|
| ARCHITECTURE_V3.md | Vision globale | docs/architecture/ |
| MODULE_CONTRACTS.md | Interfaces | docs/architecture/ |
| SECURITY_ARCHITECTURE.md | Securite complete | docs/ |
| MLOPS_ARCHITECTURE.md | MLOps 60+ pages | docs/ |
| INFRASTRUCTURE_ARCHITECTURE.md | Infra complete | docs/ |
| BACKEND_REFACTORING.md | Plan 37h | docs/ |
| FRONTEND_REFACTORING.md | Plan 70 pages | docs/ |

### Code Pret a Utiliser

| Fichier | Description |
|---------|-------------|
| `backend/services/ml/tag_extractor.py` | Extraction tags (370 lignes) |
| `backend/services/ml/tag_router.py` | Routage ML (280 lignes) |
| `backend/config/ml_routes.yaml` | Config routage |
| `backend/database/schema_ml.sql` | Schema PostgreSQL |
| `docker-compose.optimized.yml` | Production-ready |
| `nginx/nginx.conf` | Load balancing |
| `monitoring/` | Prometheus + Grafana |

---

## 9. Decisions Cles

### Confirmees

1. **Vanilla JS** pour frontend (pas de React malgre TFE)
2. **Clean Architecture** backend (Hexagonal)
3. **MLflow + DVC** pour MLOps (standards industrie)
4. **PostgreSQL** pour metadata (pas NoSQL)
5. **HTTP/2** maintenant, HTTP/3 QUIC futur

### A Valider avec CHU

1. Budget securite Phase 1-3 (~90k EUR)
2. Choix IdP (Keycloak vs Azure AD)
3. Priorite modeles ML (Gleason vs Ki-67 vs HER2)
4. Timeline deploiement production

---

## 10. Risques et Mitigations

| Risque | Impact | Probabilite | Mitigation |
|--------|--------|-------------|------------|
| Securite non implementee | Critique | Haute | Phase 1 URGENT |
| Performance insuffisante | Haut | Moyenne | Cache 3 niveaux |
| Adoption pathologistes | Haut | Moyenne | Tests utilisateurs continus |
| Modeles IA inefficaces | Moyen | Moyenne | Fallback + human-in-loop |
| Conformite AI Act | Haut | Basse | Documentation precoce |

---

## 11. Prochaines Actions Immediates

### Cette Semaine

1. **URGENT:** Reunion securite (Direction + DPO + DSI)
2. Valider budget Phase 1 securite (5k EUR)
3. Creer branche `feature/security-phase1`
4. Implementer Basic Auth + HTTPS

### Ce Mois

1. Completer Phase 2.0 (abstraction, config, tests)
2. Demarrer Phase 2.1 (ML Service prototype)
3. Setup environnement MLflow/DVC local

### Ce Trimestre

1. Phase 3.1 complete (infrastructure MLOps)
2. Premier modele mock en production interne
3. Collecte feedback pathologistes

---

**Document approuve par le Conseil des Architectes VarunaPoC**

**Date:** 2025-12-31
**Version:** 1.0
