# État du Projet — VarunaPoC

**Dernière mise à jour:** 2026-05-07
**Mis à jour par:** Cerveau d'orchestration
**Commit courant:** `47651d1` sur `main`

---

## Snapshot

### Versionnage

| | Valeur |
|---|---|
| Tag courant | `v0.3.0` |
| Tags publiés | `v0.1.0`, `v0.2.0`, `v0.3.0` |
| Branche active | `main` |
| Dernier commit | `47651d1 docs(docs): refresh broken refs, version drift, and obsolete content` |

### GitHub project (post pivot stratégique 2026-05-07)

| Wave | Closed/Total | Statut |
|---|---|---|
| 1 — Le viewer qui parle pathologiste | 11/11 | DONE |
| 2 — L'IA qui assiste | 10/10 | DONE |
| 3 — Le cas, pas le fichier | 8/8 | DONE |
| 4 — L'écosystème intelligent | 11/11 | DONE |
| 5 — Robustesse ML & Compatibilité | 5/7 | #147 fermée (wheel-reinvention), #145 #146 priority:low |
| 6 — Intelligence Visible | 29/29 | DONE |
| 7 — Platform Hardening | 45/45 | DONE |
| 8 — Annotation Clinique | 6/8 | 2 open priority:critical (#330, #331) |
| **9 — Quality-First Deep** | **0/4** | CREATED 2026-05-07 |
| **10 — Foundation Models & Validation** | **0/8** | CREATED + PIVOTED 2026-05-07 |
| **11 — Radical Simplicity Polish** | **0/2** | CREATED 2026-05-07 |
| **12 — Stratégie 2026 : AI Act + Workflow + Réseau** | **0/5** | CREATED 2026-05-07 |
| **13 — Scalability & Multi-tenant** | **0/8** | CREATED 2026-05-07 (pivot produit) |

**Total : 126 closed, 27 open.** Standards (#103-#124) tous fermés. #358 doublon fermé.

**Chemin critique 2026** (8 issues `priority:critical`) :
- #330, #331 — annotations cliniques validées pathologiste
- #337 — versioning Git-like (AI Act + publication académique)
- #346, #347 — foundation models registry + fine-tuning workflow
- #349 — AI Act compliance doc (Notified Bodies)
- #350 — IMS workflow integration (mandate non-négociable acheteurs)
- **#354 — multi-tenant data isolation + auth federation (pivot produit)**

### Santé projet

| Aspect | Score | Commentaire |
|---|---|---|
| Fonctionnalité | 9/10 | Viewer 10 formats, annotations, ML, compare, quality, FHIR, PACS, WS broadcast |
| Architecture | 10/10 | 6 Protocols PEP 544, Strangler Fig sprints 1-15, conformance verrouillée |
| Sécurité | 8/10 | OIDC PKCE, RBAC 4 rôles, JWT RS256/ES256, audit dual DB+JSON, break-glass |
| Tests | 9/10 | 1033 tests collectés (3 collection errors fixables), conformance Protocol locked |
| Documentation | 9/10 | docs/Admin manuel admin, docs/Manuel clinicien, MODULAR_ARCHITECTURE.md canonique |
| MLOps | 5/10 | Inférence Slideflow + Phikon-v2 OK ; drift / feedback / CI-CD modèles MANQUE (Wave 10) |
| Performance | 9/10 | P95 65ms, keep-alive 0-13ms, cache hit 75-85%, dispo 99.73% |
| CI/CD | 9/10 | 10/10 jobs CI, security scans (Trivy/Bandit/CodeQL/Gitleaks), CD GHCR |

---

## Architecture post-`v0.1.0` (Strangler Fig)

Six Protocols PEP 544 dans `backend/core/interfaces/`. Implémenteurs concrets
dans `backend/services/`. Routes consomment via FastAPI `Depends`.

| Protocol | Implémenteur(s) | Wirage |
|---|---|---|
| `AuthProvider` | `OIDCAuthProvider` | available, legacy `dependencies.py` primaire |
| `StorageProvider` | `FilesystemStorageProvider` | `routes/ml.py` (9 sites), `routes/slides.py` (5 sites async) |
| `SlideReader` | `OpenSlideReader`, `BioFormatsReader`, `OMETIFFReader`, `OMEZarrReader` | `services/tile_server.py` (transitif) |
| `TileCache` | `TwoLevelTileCache` (L1 mem + L2 Redis) | `routes/slides.py:get_tile` |
| `WorkflowHook` | `FHIRWorkflowHook`, `PACSWorkflowHook`, `WebSocketWorkflowHook` (sprint 15), `CompositeWorkflowHook`, `NoOpWorkflowHook` | `routes/exports.py`, `routes/annotations.py` (CRUD + reject + batch) |
| `MLWorkerProvider` | `MLWorkerProxy` (subprocess), `InProcessMLWorker` (ONNX/OpenVINO), `TritonClientMLWorker` (stub) | `routes/ml.py` (sprint 12, 9 handlers) |

**Sprint 15** (WebSocket broadcast) : `WebSocketWorkflowHook` + `WorkflowEventBroadcaster`
publient les `WorkflowEvent` (REPORT_SIGNED, ANNOTATION_*) aux clients connectés
sur `GET /api/v1/ws/events`. Frontend : `WorkflowEventService` singleton réémet
sur l'EventBus sous `workflow:<event_type>` et `workflow:event`.

**Doc canonique :** `docs/architecture/MODULAR_ARCHITECTURE.md`. Conformance Protocol
verrouillée par `tests/unit/test_protocol_conformance.py`.

---

## Infrastructure dev (`docker-compose.yml --profile dev`)

| Service | Port host | Rôle | Activation |
|---|---|---|---|
| `postgres` (PostGIS 16) | 5433 | Annotations, audit, sessions, quality | toujours |
| `keycloak` | 8180 | OIDC dev | `AUTH_ENABLED=true` |
| `redis` | 6380 | TileCache L2 | `TILE_CACHE_L2_ENABLED=true` |
| `hapi-fhir` | 8090 | FHIR R4 sandbox | `FHIR_ENABLED=true` |
| `orthanc` | 4242 (DICOM) / 8042 (HTTP) | PACS sandbox | `PACS_ENABLED=true` |

Docker-compose unifié multi-profiles (`core`, `auth`, `cache`, `pacs`, `fhir`,
`monitoring`, `mlops`, `dev`, `prod`). Cf. `docs/Admin/PROFILES.md`.

---

## Alignement avec `vision.pdf §2` + pivot stratégique mai 2026

Synthèse — détail dans `.claude/memory/VISION_ALIGNMENT.md` (§0 = pivot,
§1-§7 = analyse PDF originale).

### Pivot foundation models (mai 2026)

Le PDF v2.0 (déc. 2025 §2.3.2) décrivait MLOps classique 2022-2023 (training
from scratch). Trajectoire dominante 2026 :
**foundation model pré-entraîné (UNI/CONCH/Virchow) → fine-tuning local sur
cas annotés Quality-First → validation prospective multi-centrique →
déploiement supervisé**.

Wave 10 a été pivotée. Wave 12 créée pour les axes stratégiques 2026 hors PDF.

### Les 3 angles morts critiques (PDF §2.3) + axes stratégiques 2026

**1. Quality-First Annotation Platform** — fondation OK, deep features Wave 9 (4 issues)
- ✅ Cohen + Fleiss kappa, IoU, F1, confusion matrix, disagreement heatmap
- 🔵 Wave 9 : outliers (#335), adjudication (#336), **versioning Git-like (#337 priority:critical)**, métriques prédictives qualité (#338)

**2. Foundation Models & Validation** (pivot Wave 10, 8 issues)
- ✅ Inférence Slideflow + Phikon-v2 (CUDA), uncertainty brut
- 🔵 Wave 10 : foundation model registry (#346 priority:critical), fine-tuning workflow (#347 priority:critical), validation prospective (#348), CI/CD fine-tuning (#341), drift (#339), feedback loops (#340), calibration AI Act (#342), active learning (#343)

**3. Radical Simplicity** — fondation OK, polish Wave 11 (2 issues)
- ✅ Zero-config browser, P95 <100ms, OIDC SSO, PACS deep-link
- 🔵 Wave 11 : onboarding 3min (#344 DEFER), audit geste-mimétique (#345)

**4. Axes stratégiques 2026** (Wave 12, 5 issues) — non couverts par PDF v2.0
- 🔵 AI Act compliance doc (#349 priority:critical) — différenciateur Notified Bodies + publication académique
- 🔵 IMS workflow integration deep (#350 priority:critical) — mandate non-négociable acheteurs hospitaliers
- 🔵 RCP collaborative (#351) — réseau hôpitaux + second avis
- 🔵 Federated learning architecture-ready (#352) — Horizon Europe / EU4Health
- 🔵 Copilote IA conversationnel (#353 EXPLORATOIRE) — signal AstraZeneca/Modella

**Score révisé** :
- PDF original §2.3 : 6/4/4 sur 14 capacités → cible **18/4/1 sur 23 capacités** après livraison Waves 9-12.
- Chemin critique 2026 : **7 issues `priority:critical`** (#330, #331, #337, #346, #347, #349, #350).

---

## Ce qui fonctionne (en bref)

### Backend (port 8000)
- Viewer WSI 10 formats (94 lames testées) — DZI tile streaming
- Annotations PostGIS (CRUD, labels, stats, GeoJSON, batch)
- ML Slideflow + Phikon-v2 + 3 backends (subprocess / inprocess ONNX-OpenVINO / triton stub)
- Quality metrics (Cohen + Fleiss kappa, F1, confusion, IoU, disagreement)
- Auth OIDC PKCE + RBAC 4 rôles + audit dual DB+JSON + break-glass + session roaming
- FHIR R4 (DiagnosticReport builder + WorkflowHook)
- PACS Telemis deep-link (`/slide/{name}` resolution)
- WebSocket broadcaster (sprint 15) `GET /api/v1/ws/events`
- Cache 3 niveaux : L1 mem + L2 Redis + L3 nginx (10 GB)

### Frontend (port 5173)
- Pages Home / Viewer / Compare (multi-viewer 2x1, 2x2)
- 5 outils dessin (rectangle, polygone, point, cercle, freehand)
- Panels : ML, Detection, Counting, Quality, Heatmap overlay
- Auth PKCE + role-based UI + WorkflowEventService (WS subscriber)
- 31 components, 18 e2e suites Playwright

---

## Ce qui manque (post pivot 2026-05-07)

19 issues open au total. Voir `ROADMAP.md §4` pour le détail priorisé.

### Chemin critique (`priority:critical`, 8 issues)

| # | Wave | Titre |
|---|---|---|
| #330 | 8 | Édition contour des détections IA (E key, vertex drag) |
| #331 | 8 | Historique versionné annotations (audit medicolegal) |
| #337 | 9 | Versioning Git-like annotations (AI Act + publication académique) |
| #346 | 10 | Foundation model registry + adapter (UNI, CONCH, Virchow…) |
| #347 | 10 | Fine-tuning workflow local (LoRA + full FT, MLflow) |
| #349 | 12 | Documentation AI Act (Art. 9-15) pour Notified Bodies |
| #350 | 12 | IMS workflow integration (LIS/HIS deep, au-delà PACS) |
| **#354** | **13** | **Multi-tenant data isolation + auth federation (pivot produit)** |

### Backlog priority:high+medium+low (19 issues)

- Wave 5 : #145 (low), #146 (low) — wheel-reinvention OpenSlide
- Wave 9 : #335, #336 (high), #338 (medium)
- Wave 10 : #339, #340, #341, #348 (high), #342, #343 (medium)
- Wave 11 : #344 DEFER, #345 (medium)
- Wave 12 : #351 (high), #352 (medium), #353 (low EXPLORATOIRE)
- Wave 13 : #355, #356, #357, #359, #360, #361 (high), #362 (medium)

### Décisions stratégiques 2026-05-07

- **#147 fermée** : wheel-reinvention sur 22 lames marginales (formats que OpenSlide/Bio-Formats devraient gérer ou ignorer)
- **#358 fermée** : doublon de #359 (504 GitHub timeout)
- **#145 downgrade priority:low** : bug upstream OpenSlide, pas de différenciateur stratégique
- **Wave 10 pivotée** : "Continuous Learning MLOps" → "Foundation Models & Validation"
- **Wave 13 créée** : "Scalability & Multi-tenant" — pivot produit acté
- **23 issues open ré-alignées** : commentaire d'alignement multi-tenant + scalabilité posté sur chaque
- **4 issues genericized** dans body : #339, #341, #343, #351 ("CHU UCL Namur" → "tenant (CHU UCL Namur = customer-zero)")

---

## Métriques (mesures réelles)

| Métrique | Valeur | Source |
|---|---|---|
| Tests backend | 1033 collectés | `pytest --collect-only -q` |
| Tile load (keep-alive) | 0-13 ms | tests Phase 2 |
| Tile load P95 (premier chargement) | ~65 ms | benchmarks |
| 28 tiles premier chargement | ~2.1 s | tests Phase 2 |
| ML heatmap (Phikon-v2 CUDA) | ~2.5 min | tests Phase 2 |
| Cache hit rate (L1+L2+nginx) | 75-85% | Prometheus |
| Disponibilité (Phase 2.5) | 99.73% | benchmarks |
| Lames testées | 94 (10 formats) | `test_format_detector.py` |
| Détection régions auto | 3 régions (72-88% conf.) | threshold 0.3 |

---

## Positionnement

### Recherche Use Only (status 2026-05-07)
- Aujourd'hui : outil de recherche et d'enseignement (IVDR Classe A, FDA Exempt)
- Moyen terme : outil d'aide à la décision consultatif
- Long terme : certification IVDR Classe C / FDA 510(k) si validation clinique

### Différenciateurs (PDF §2.3 + pivot mai 2026) vs marché
- **Quality-First** — kappa auto + outlier detection + adjudication + versioning Git-like (vs marché : annotations sans QA)
- **Foundation Models & Validation** (pivot 2026) — fine-tuning UNI/CONCH/Virchow + validation prospective + drift sur fine-tuned (vs marché : training from scratch ou black-box vendor)
- **Radical Simplicity + IMS deep** — zero-config + onboarding 3min + SSO transparent + accès navigateur direct + intégration LIS/HIS bidirectionnelle (vs marché : formation 2-4 semaines + manuel 100 pages + système séparé du workflow IMS)
- **AI Act compliance différenciateur réglementaire** (axe 2026) — traçabilité versioning Git-like + transparence calibration + audit dossier Notified Bodies (vs marché : compliance theatre)
- **Réseau RCP + federated learning** (axe 2026) — co-visualisation sync + chat ancré + architecture-ready Horizon Europe (vs marché : silos hospitaliers)

### Multiplicateur produit (pivot 2026-05-07)
- **Multi-tenant + scalabilité** : la plateforme sert N tenants (hôpitaux, laboratoires, instituts) avec isolation stricte (DB, storage, ML, auth, cache, observability per-tenant). C'est un **multiplicateur** des différenciateurs Q+F+A+N, pas un différenciateur en soi. Wheel-reinvention évitée : intégration de standards (Kubernetes, Helm, Triton, Redis Cluster, OpenTelemetry, ArgoCD).
- CHU UCL Namur reste **customer-zero / early adopter**, plus le périmètre cible.

### Gaps déploiement hospitalier (cf. `docs/HOSPITAL_DEPLOYMENT_EVALUATION.md`)
1. ~~Authentification (RBAC + JWT)~~ FAIT (Wave 3)
2. ~~Audit trail (structured logging + table)~~ FAIT (Wave 3)
3. ~~Intégration PACS Telemis~~ FAIT (Wave 3 — deep-link)
4. Protection PHI (de-identification) — Wave 5+
5. HTTPS/TLS — `nginx/` profile prod

---

## Liens rapides

| Quoi | Path |
|---|---|
| Roadmap | `.claude/memory/ROADMAP.md` |
| Vision alignment PDF §2 | `.claude/memory/VISION_ALIGNMENT.md` |
| Cerveau orchestration | `.claude/BRAIN.md` |
| Décisions techniques | `.claude/memory/DECISIONS.md` |
| Learnings (bugs, workarounds) | `.claude/memory/LEARNINGS.md` |
| Architecture canonique | `docs/architecture/MODULAR_ARCHITECTURE.md` |
| Manuel admin | `docs/Admin/` |
| Manuel utilisateur | `docs/Manuel/` |
| Vision source | `vision.pdf` |
| Proposal opérationnel | `docs/PROPOSAL_VARUNA_v2.md` |

---

**Ce fichier est mis à jour au début de chaque session Claude Code et après chaque tâche significative.**
