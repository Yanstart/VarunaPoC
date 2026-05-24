# VarunaPoC — Roadmap & Alignement Vision

**Version:** 6.1
**Date:** 2026-05-07
**Statut:** Document vivant — aligné avec `vision.pdf §2` **+ pivot stratégique mai 2026 (foundation models + produit multi-tenant)**

Roadmap unique et à jour. **Deux pivots stratégiques actés le 2026-05-07** :

1. **Pivot foundation models** : MLOps classique (training from scratch + retrain) → foundation model pré-entraîné + fine-tuning local + validation rigoureuse + déploiement supervisé. Wave 10 pivotée. Wave 12 créée (AI Act, IMS deep, RCP, Federated, Copilote IA).
2. **Pivot produit multi-tenant** (v6.1) : sortie du PoC mono-tenant CHU UCL Namur → produit / plateforme déployable sur N tenants. Wave 13 créée (Scalability & Multi-tenant, 8 issues). Toutes les issues open enrichies d'une dimension multi-tenant + scalabilité (commentaire d'alignement).

Voir `.claude/memory/VISION_ALIGNMENT.md §0` (foundation models) et **§0.6** (produit multi-tenant) pour le détail.

**GitHub Project Board:** https://github.com/users/Yanstart/projects/6
**Commit courant:** `47651d1` sur `main`. Tags : `v0.1.0`, `v0.2.0`, `v0.3.0`.

**Documents stratégiques:**
- `vision.pdf` — vision projet v2.0 (déc. 2025), section 2 = cadre conceptuel + 12 angles morts + 3 critiques
- `docs/PROPOSAL_VARUNA_v2.md` — déclinaison opérationnelle de la vision
- `docs/architecture/MODULAR_ARCHITECTURE.md` — architecture canonique (6 Protocols)
- `.claude/memory/VISION_ALIGNMENT.md` — mapping détaillé PDF §2 ↔ implémentation

---

## 1. État global

### 1.1. Milestones GitHub (au 2026-05-07, après pivot stratégique)

| Wave | Thème | Closed / Total | Statut |
|---|---|---|---|
| 1 | Le viewer qui parle pathologiste | 11/11 | DONE |
| 2 | L'IA qui assiste | 10/10 | DONE |
| 3 | Le cas, pas le fichier | 8/8 | DONE |
| 4 | L'écosystème intelligent | 11/11 | DONE |
| 5 | Robustesse ML & Compatibilité | 5/7 | EN COURS — #147 fermée (wheel-reinvention), #145 downgrade priority:low, #146 priority:low |
| 6 | Intelligence Visible | 29/29 | DONE |
| 7 | Platform Hardening | 45/45 | DONE |
| 8 | Annotation Clinique | 6/8 | EN COURS — 2 open (#330 priority:critical, #331 priority:critical) |
| **9** | **Quality-First Deep** | **0/4** | **CREATED 2026-05-07** — outliers, adjudication, versioning Git-like (priority:critical), métriques prédictives qualité |
| **10** | **Foundation Models & Validation** (pivot du 2026-05-07) | **0/8** | **CREATED + PIVOTED** — drift, feedback, fine-tuning workflow CI/CD, calibration, active learning + N1 registry, N2 fine-tuning workflow, N3 validation prospective |
| **11** | **Radical Simplicity Polish** | **0/2** | **CREATED** — onboarding 3min (DEFER), audit geste-mimétique |
| **12** | **Stratégie 2026 : AI Act + Workflow + Réseau** | **0/5** | **CREATED 2026-05-07** — N4 AI Act doc (priority:critical), N5 IMS deep (priority:critical), N6 RCP collab, N7 federated learning, N8 copilote IA (exploratoire) |
| **13** | **Scalability & Multi-tenant** | **0/8** | **CREATED 2026-05-07 (pivot produit)** — multi-tenant data isolation (priority:critical), storage S3, DB scaling, ML inference Triton, cache+WS scaling, observability OTel, Helm+GitOps, perf+FinOps |

**Total : 126 closed (#358 doublon fermé), 27 open** (Standards #103-#124 tous fermés). Détail
dans §4.

### 1.1.1. Note sur le pivot Wave 10

Wave 10 a été **renommée et recadrée le 2026-05-07** :
- Ancien nom : "Continuous Learning MLOps" (paradigme 2022-2023, training from scratch)
- Nouveau nom : "Foundation Models & Validation"
- Issue #341 réécrite intégralement (Phikon retrain → fine-tuning UNI/CONCH workflow)
- Issues #339, #340, #342, #343 recadrées (en support fine-tuning, plus retrain from scratch)
- 3 nouvelles issues créées (N1, N2, N3)

### 1.2. Architecture post-`v0.1.0` — Strangler Fig (sprints 1-15)

Six Protocols PEP 544 abstraient les seams du backend ; chaque Protocol a
au moins un implémenteur concret câblé via FastAPI `Depends`.

| Protocol | Implémenteur(s) | Status |
|---|---|---|
| `AuthProvider` | `OIDCAuthProvider` | available — legacy `dependencies.py` reste primaire |
| `StorageProvider` | `FilesystemStorageProvider` | wired (`routes/ml.py`, `routes/slides.py`) |
| `SlideReader` | `OpenSlideReader`, `BioFormatsReader`, `OMETIFFReader`, `OMEZarrReader` | wired transitif (`services/tile_server.py`) |
| `TileCache` | `TwoLevelTileCache` (L1 mem + L2 Redis) | wired (`routes/slides.py:get_tile`) |
| `WorkflowHook` | `FHIRWorkflowHook`, `PACSWorkflowHook`, `WebSocketWorkflowHook` (sprint 15), `CompositeWorkflowHook`, `NoOpWorkflowHook` | wired (`routes/exports.py`, `routes/annotations.py`) |
| `MLWorkerProvider` | `MLWorkerProxy`, `InProcessMLWorker`, `TritonClientMLWorker` | wired (`routes/ml.py`, sprint 12) |

Conformance Protocol verrouillée par `tests/unit/test_protocol_conformance.py`.

### 1.3. Métriques (mesures)

| Métrique | Valeur |
|---|---|
| Tests backend collectés | 1033 (3 collection errors fixables) |
| Lames testées | 94 (10 formats supportés) |
| Tile load (keep-alive) | 0-13 ms |
| Tile load P95 (chargement initial) | ~65 ms |
| Disponibilité (Phase 2.5) | 99.73% |
| Cache hit rate (L1+L2+nginx) | 75-85% |
| ML heatmap (Phikon-v2 CUDA) | ~2.5 min |

---

## 2. Alignement avec `vision.pdf §2`

Mapping condensé — détail dans `VISION_ALIGNMENT.md`.

### 2.1. Les 12 angles morts structurels (PDF §2.2)

| # | Angle mort | Couverture VarunaPoC |
|---|---|---|
| 1 | Interopérabilité (vendor lock-in) | OK — 10 formats OpenSlide, FHIR R4, DICOM WSI |
| 2 | Qualité annotations | PARTIEL — kappa+F1+IoU+confusion FAIT, outliers/adjudication MANQUE |
| 3 | MLOps | FAIBLE — inférence FAIT, drift/feedback/CI-CD modèles MANQUE |
| 4 | Explicabilité | PARTIEL — heatmaps + uncertainty existent, calibration par région MANQUE |
| 5 | Feedback loops | MANQUE |
| 6 | Simplicité | OK — web zero-config, perf <100ms, intégration SI |
| 7 | Collaboration | PARTIEL — WebSocket events FAIT (sprint 15), co-annotation temps réel MANQUE |
| 8 | Privacy AI | NON ABORDÉ — federated learning Post-MVP |
| 9 | Reproductibilité | PARTIEL — versioning code OK, versioning datasets/runs ML MANQUE |
| 10 | Cas rares | MANQUE — out-of-distribution detection |
| 11 | Intégration SI | OK — OIDC SSO, PACS Telemis deep-link, FHIR DiagnosticReport |
| 12 | Modèle économique | OK — open source MIT, hébergement interne |

### 2.2. Les 3 angles morts critiques (PDF §2.3)

#### 2.2.1. Quality-First Annotation Platform

| Capacité PDF | État |
|---|---|
| Mesure auto kappa/Dice inter-annotateur | FAIT (Cohen+Fleiss+IoU+F1+confusion+disagreement heatmap) |
| Détection annotations suspectes (outliers spatial/taille/forme) | MANQUE → Wave 9 #1 |
| Workflows d'adjudication structurés | MANQUE → Wave 9 #2 |
| Versioning Git-like (branches, merge, diff visuel, rollback) | PARTIEL — issue #331 (audit medicolegal) ; deep version → Wave 9 #3 |
| Métriques prédictives qualité dataset | MANQUE → Wave 9 #4 |

#### 2.2.2. Continuous Learning System / MLOps complet

| Capacité PDF | État |
|---|---|
| Monitoring drift automatique | MANQUE → Wave 10 #1 |
| Feedback loops auto (corrections → ré-entraînement) | MANQUE → Wave 10 #2 |
| Pipeline CI/CD modèles avec rollback | MANQUE → Wave 10 #3 |
| Calibration incertitude par région | PARTIEL → Wave 10 #4 |
| Active learning intelligent | MANQUE → Wave 10 #5 |

#### 2.2.3. Radical Simplicity

| Capacité PDF | État |
|---|---|
| Zero-config browser | FAIT |
| Interface geste-mimétique (zoom molette, double-clic centrer) | À VÉRIFIER → Wave 11 #2 |
| Onboarding tutoriel contextuel 3min | MANQUE → Wave 11 #1 |
| Performance perceptuelle <100ms | FAIT (P95 65ms, keep-alive 0-13ms) |
| Intégration transparente SI (SSO + PACS) | FAIT |

### 2.3. Score d'alignement

**14 capacités critiques (PDF §2.3) :** 6 livrées, 4 partielles, 4 manquantes.

Le projet a la **fondation alignée**. Les 4 manquantes + 4 partielles
constituent les **Waves 9, 10, 11** (à créer en GitHub project, voir §4).

---

## 3. Phases historiques (référence)

Les phases originales de la `vision.pdf §5.1` (Initialisation 1-3, Core 4-9,
Enrichissement 10-13, Finalisation 14-15) ont été remappées en **8 Waves**
GitHub. Mapping :

| Phase PDF | Sprint | Wave correspondante |
|---|---|---|
| 1 — Initialisation (sem. 1-3) | shadowing, stack, setup | (pré-Wave 1) |
| 2 — Core (sem. 4-9) | viewer, formats, annotations, ML, compare | Waves 1-2 |
| 3 — Enrichissement (sem. 10-13) | auth, audit, quality, PACS | Waves 3-4 |
| 4 — Finalisation (sem. 14-15) | tests E2E, docs, prod | Waves 6-7 + Standards |
| Post-MVP Cercle 1 (mois 4-8) | SSO, quality complet, collab temps réel | Waves 5+8 + sprints Strangler Fig |
| Post-MVP Cercle 2 (mois 8-14) | MLOps complet, continuous learning | **Wave 10 (à créer)** |

---

## 4. Backlog opérationnel — 19 issues open

### 4.1. Wave 5 — Robustesse ML (downgrade après pivot 2026-05-07)

| # | Titre | Priorité | Note |
|---|---|---|---|
| #145 | BIF direction error workaround | priority:low | Wheel-reinvention OpenSlide. Upstream-only ou accepter gap. |
| #146 | Uvicorn multi-worker / gunicorn | priority:low | Production hardening, indirect. |

#147 fermée le 2026-05-07 (wheel-reinvention sur 22 lames marginales — voir comment de fermeture).

### 4.2. Wave 8 — Annotation Clinique (héritage interview pathologiste)

| # | Titre | Priorité | Alignement stratégique |
|---|---|---|---|
| #330 | Édition contour des détections IA (E key, vertex drag) | priority:critical | Q + F — corrections expertes = data fine-tuning Wave 10 |
| #331 | Historique versionné annotations (audit medicolegal) | priority:critical | A — fondation AI Act + base Wave 9 #337 |

### 4.3. Wave 9 — Quality-First Deep (créée 2026-05-07)

| # | Titre | Priorité | Alignement |
|---|---|---|---|
| #335 | Outlier detection annotations (DBSCAN spatial/taille/forme) | priority:high | Q + F — filter dataset avant fine-tuning |
| #336 | Workflow adjudication par pairs | priority:high | Q + A + N — peer review = AI Act + base RCP |
| **#337** | **Versioning Git-like annotations** | **priority:critical** | **A core + Q + N — LE différenciateur AI Act + publication académique** |
| #338 | Métriques prédictives qualité dataset | priority:medium | Q + F — gate avant fine-tuning |

### 4.4. Wave 10 — Foundation Models & Validation (pivot 2026-05-07)

| # | Titre | Priorité | Alignement |
|---|---|---|---|
| **#346 (N1)** | **Foundation model registry + adapter (UNI, CONCH, Virchow, GigaPath, mSTAR)** | **priority:critical** | **F core — pierre angulaire de Wave 10** |
| **#347 (N2)** | **Fine-tuning workflow local (LoRA + full FT, MLflow)** | **priority:critical** | **F core + Q — moteur du fine-tuning** |
| #348 (N3) | Validation prospective multi-centrique | priority:high | F + Q + A + N — étape "Évaluer" trajectoire 2026 |
| #341 (réécrite) | CI/CD fine-tuning + champion/challenger + auto-rollback | priority:high | F + A — automatisation #347 |
| #339 | Drift monitoring sur fine-tuned foundation model | priority:high | F + A — déclencheur auto fine-tuning |
| #340 | Feedback loops (corrections → dataset MLflow + commit Wave 9 #337) | priority:high | Q + F + A — boucle complète |
| #342 | Calibration uncertainty (Platt/temperature scaling) | priority:medium | A core + F — transparence AI Act |
| #343 | Active learning (entropy + diversity sampling sur embeddings foundation models) | priority:medium | F + Q — sélection cas pour fine-tuning |

### 4.5. Wave 11 — Radical Simplicity Polish

| # | Titre | Priorité | Alignement |
|---|---|---|---|
| #344 | Onboarding tutoriel contextuel 3min | priority:medium | R — DEFER (attend Wave 12 N5 IMS) |
| #345 | Audit geste-mimétique (double-clic centrer, etc.) | priority:medium | R — non bloqué |

### 4.6. Wave 12 — Stratégie 2026 : AI Act + Workflow + Réseau (créée 2026-05-07)

| # | Titre | Priorité | Alignement |
|---|---|---|---|
| **#349 (N4)** | **Documentation AI Act (Art. 9-15) pour Notified Bodies** | **priority:critical** | **A core + N — différenciateur réglementaire + paper-ready** |
| **#350 (N5)** | **IMS workflow integration (LIS/HIS deep, au-delà PACS)** | **priority:critical** | **R core — mandate non-négociable acheteurs hospitaliers** |
| #351 (N6) | RCP collaborative (co-visualisation sync + chat contextuel ancré) | priority:high | N core — réseau hôpitaux + second avis |
| #352 (N7) | Federated learning architecture-ready (Horizon Europe / EU4Health) | priority:medium | N core + F — financement EU + Privacy AI |
| #353 (N8) | Copilote IA conversationnel (PathChat-like) — EXPLORATOIRE | priority:low | F — optionnel, à valider trimestriellement |

### 4.7. Wave 13 — Scalability & Multi-tenant (créée 2026-05-07, pivot produit)

| # | Titre | Priorité | Alignement |
|---|---|---|---|
| **#354 (N9)** | **Multi-tenant data isolation + auth federation** | **priority:critical** | **S core — pierre angulaire pivot produit** |
| #355 (N10) | Storage S3-compatible + tiering hot/cold + multi-tenant | priority:high | S — sortie filesystem local |
| #356 (N11) | DB scaling (read replicas + pgbouncer + partitioning) | priority:high | S — passage à l'échelle PostgreSQL |
| #357 (N12) | ML inference scaling (Triton + GPU pool + batch + queue) | priority:high | S + F — sortie inference in-process |
| #359 (N13) | Cache cluster + WebSocket scaling (Redis Sentinel + sticky session) | priority:high | S — multi-réplicas cohérents |
| #360 (N14) | Observability at scale (OpenTelemetry + log aggregation + multi-tenant SLO) | priority:high | S + A — opérer aveugle = échec |
| #361 (N15) | Helm chart + GitOps deployment + multi-region readiness | priority:high | S — sortie docker-compose mono-host |
| #362 (N16) | Performance benchmarks + FinOps monitoring (k6 + cost dashboards par tenant) | priority:medium | S — capacity planning + tarification |

### 4.8. Vue priorisée

**8 issues `priority:critical`** = les vrais bloqueurs stratégiques (chemin critique 2026) :
- #330, #331 (annotations cliniques validées par pathologiste)
- #337 (versioning Git-like — AI Act + publication)
- #346 / #347 (foundation models registry + fine-tuning workflow)
- #349 (AI Act doc) / #350 (IMS deep)
- **#354 (multi-tenant data isolation + auth federation — pivot produit)**

Ces 8 issues constituent le **chemin critique 2026**.

---

## 5. Risques & mitigations

| ID | Risque | Impact | Probabilité | Statut | Mitigation |
|---|---|---|---|---|---|
| R1 | Auth non déployée | CRITIQUE | HIGH | RÉSOLU | OIDC PKCE + RBAC + audit (Wave 3) |
| R2 | Bus factor = 1 | CRITIQUE | HIGH | ATTÉNUATION | Open source MIT, 1033 tests, CI/CD, stack standard |
| R3 | Adoption limitée | CRITIQUE | MOYEN | ATTÉNUATION | Co-conception pathologistes (Wave 8), Radical Simplicity (Wave 11) |
| R4 | Compliance RGPD | ÉLEVÉ | MOYEN | PARTIEL | Auth + audit FAIT, de-identification Post-MVP, EHDS (échéance mars 2031) |
| R5 | Performance annotations | MOYEN | FAIBLE | OK | PostgreSQL + PostGIS indices |
| R6 | Incompatibilité PACS | MOYEN | MOYEN | OK | PACS Telemis deep-link FAIT, fallback partagé |
| R7 | ML drift post-déploiement | MOYEN | MOYEN | PLANIFIÉ | Wave 10 (drift monitoring + feedback loops) |
| R8 | Annotations non-fiables | ÉLEVÉ | MOYEN | PLANIFIÉ | Wave 9 (outlier detection + adjudication) |

---

## 6. Liens

| Doc | Path | Description |
|---|---|---|
| Vision | `vision.pdf` | Document source v2.0 (déc. 2025) |
| Proposal | `docs/PROPOSAL_VARUNA_v2.md` | Déclinaison opérationnelle |
| Architecture canonique | `docs/architecture/MODULAR_ARCHITECTURE.md` | 6 Protocols + sprint log |
| Vision alignment | `.claude/memory/VISION_ALIGNMENT.md` | Mapping détaillé PDF §2 ↔ code |
| Cerveau | `.claude/BRAIN.md` | Orchestration |
| Decisions | `.claude/memory/DECISIONS.md` | ADRs |
| Learnings | `.claude/memory/LEARNINGS.md` | Erreurs capitalisées |
| Project State | `.claude/memory/PROJECT_STATE.md` | Snapshot courant |
| Hospital Eval | `docs/HOSPITAL_DEPLOYMENT_EVALUATION.md` | Évaluation déploiement hospitalier |

---

## Changelog

### v6.1 (2026-05-07) — pivot produit multi-tenant + scalabilité
- **Wave 13 créée** : "Scalability & Multi-tenant" — 8 issues #354-#362 (multi-tenant data isolation `priority:critical` cœur, storage S3, DB scaling, ML inference Triton, cache+WS scaling, observability OTel, Helm+GitOps, perf+FinOps)
- **Pivot produit acté** : sortie du PoC mono-tenant CHU UCL Namur → produit / plateforme multi-tenant. CHU UCL Namur reste customer-zero / early adopter.
- **23 issues open ré-alignées** : commentaire d'alignement multi-tenant + scalabilité posté sur chaque issue. 4 issues genericized dans le body (#339, #341, #343, #351 — "CHU UCL Namur" → "tenant (CHU UCL Namur = customer-zero)").
- **VISION_ALIGNMENT.md §0.6 ajouté** : pivot produit + critère **S** (Scalabilité / multi-tenant) ajouté à la grille (Q, F, R, A, N, S, W).
- **#358 fermé** : doublon de #359 créé suite à un 504 GitHub.
- Chemin critique : 7 → 8 issues `priority:critical` (#354 ajoutée).

### v6.0 (2026-05-07) — pivot stratégique foundation models
- **Pivot Wave 10** : "Continuous Learning MLOps" → "Foundation Models & Validation". Issue #341 réécrite (Phikon retrain → fine-tuning UNI/CONCH workflow). Issues #339/#340/#342/#343 recadrées (support fine-tuning, plus retrain from scratch). 3 nouvelles issues créées : #346 (N1 registry), #347 (N2 fine-tuning workflow), #348 (N3 validation prospective)
- **Wave 12 créée** : "Stratégie 2026 : AI Act + Workflow + Réseau" — 5 issues #349 (N4 AI Act doc), #350 (N5 IMS deep), #351 (N6 RCP), #352 (N7 federated), #353 (N8 copilote IA exploratoire)
- **Hisse #337 priority:critical** (LE différenciateur AI Act + publication académique)
- **Wave 9 recadrée** : 4 issues (#335-#338) avec angles fine-tuning + AI Act explicites
- **Issue #147 fermée** (wheel-reinvention sur 22 lames marginales)
- **Issue #145 downgrade priority:low** (wheel-reinvention OpenSlide upstream-only)
- **Issue #344 marquée DEFER** (attend Wave 12 N5 IMS pour ne pas faire un onboarding incohérent avec workflow réel)
- **VISION_ALIGNMENT.md §0 ajouté** : pivot foundation models + carte océan bleu vs hors scope + 6 opportunités stratégiques (AI Act, Foundation models open, CPT codes, RCP, federated EU, publication académique)

### v5.0 (2026-05-07) — première mise à jour PDF §2
- Réalignement complet avec `vision.pdf §2` (cadre conceptuel + 12 angles morts + 3 critiques)
- Remplace v4.x (qui ignorait Waves 5-8 et Strangler Fig sprints 1-15)
- Ajout section "Alignement vision PDF" avec score 6/4/4 sur les 14 capacités critiques
- Création initiale Waves 9, 10, 11 (avant pivot v6.0)
- Mise à jour métriques : 1033 tests, tag v0.3.0, commit 47651d1
- Risque R8 ajouté (annotations non-fiables)

### v4.0 (2026-02-12) — obsolète
- Phase 3.1 et 3.2 marquées TERMINE, Phase 3.3 PACS EN COURS

### v3.0 (2026-02-08) — obsolète
- Réalignement avec PROPOSAL_VARUNA_v2.md plan 15 semaines

### v2.0 (2026-02-04) — obsolète
- Fusion ANALYSE_DIRECTION_PROJET.md

### v1.0 (2026-02-04) — obsolète
- Création initiale

---

**Dernière mise à jour:** 2026-05-07
**Prochaine review:** Après création Waves 9-11 (gh CLI)
**Responsable:** Cerveau d'orchestration
