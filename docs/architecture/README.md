# Documentation Architecture V3 - VarunaPoC

**Date:** 2025-02-05 (Mise à jour architecture modulaire)
**Version:** 3.1.0

---

## Vue d'Ensemble

Cette documentation définit l'architecture cible pour transformer VarunaPoC d'un **viewer WSI simple** (Phase 1) en une **plateforme MLOps modulaire** (Phase 3).

**Objectif TFE 2025-2026:** Développer un système d'intelligence artificielle pour l'analyse de lames histologiques, avec apprentissage continu et conformité réglementaire.

**⭐ NOUVEAU:** Architecture modulaire avec interfaces Python (Protocols) - voir `MODULAR_ARCHITECTURE.md`

---

## Documents Disponibles

### 0. [SYSTEM_PATTERNS.md](./SYSTEM_PATTERNS.md) — Current implementation reference

**Reference architecturale concrete** basee sur le code implemente (Phases 1-3.1).

**Contenu:**
- Patterns backend (module optionnel, Depends(), RBAC, audit, DB)
- Patterns frontend (EventBus, Singleton, Component lifecycle, role-based UI)
- Modele de donnees actuel (annotations, users, audit, sessions)
- Auth OIDC PKCE + Break-Glass + Session Roaming
- Guide d'extension pour features futures: versioning, expertise croisee, commentaires
- Checklist d'ajout de feature

**Lire en premier** pour implementer une nouvelle feature sur le code actuel.

---

### 1. [MODULAR_ARCHITECTURE.md](./MODULAR_ARCHITECTURE.md) — Target design (Protocol interfaces)

**Guide complet architecture modulaire** avec interfaces Python (Protocols).
Ces interfaces definissent la cible architecturale; les implementations concretes
existantes (auth OIDC, PostgreSQL quality, OpenSlide tile server) n'en heritent
pas encore — la migration est progressive (voir REFACTORING_PLAN.md).

**Contenu:**
- Vision (probleme → solution architecture modulaire)
- Principes architecturaux (SOLID, Design Patterns detailles)
- Structure des interfaces (5 interfaces cles: Auth, Storage, Loader, Cache, Workflow)
- Modules et implementations (code exemples complets)
- Guide d'implementation pas-a-pas (ajouter provider custom)
- Tests modulaires (pytest, markers, fixtures)
- Migration progressive (Phase 1 → Phase 2)
- FAQ complete

**Public:** Developpeurs backend, nouveaux contributeurs, architectes
**Quand lire:** Comprendre interfaces, ajouter provider, ecrire tests modulaires

---

### 2. [QUICK_START_MODULAR.md](./QUICK_START_MODULAR.md)

**Guide rapide architecture modulaire** (pour developpeurs presses).

**Contenu:**
- Concept en 30 secondes
- Structure dossiers (5 min)
- Les 5 interfaces cles (resume)
- Exemple complet ajout RedisCache (10 min)
- Tests Pytest (5 min)
- Commandes utiles
- Patterns de code courants
- Erreurs courantes

**Public:** Developpeurs presses, quick reference
**Quand lire:** Demarrer rapidement, reference rapide

---

### 3. [IMPLEMENTATION_REPORT.md](./IMPLEMENTATION_REPORT.md)

**Rapport d'implementation architecture modulaire** (management/equipe).

**Contenu:**
- Resume executif
- Livrables (interfaces, tests, docs crees)
- Architecture actuelle vs cible (diagrammes)
- Compatibilite retroactive (migration sans breaking changes)
- Impact et benefices (pour developpeurs, institutions, maintenance)
- Metriques (code cree, coverage, temps estimes)
- Prochaines etapes (court/moyen/long terme)
- Risques et mitigations

**Public:** Management, project managers, leads techniques
**Quand lire:** Vue d'ensemble implementation, decisions, planification

---

### 4. [ARCHITECTURE_V3.md](./ARCHITECTURE_V3.md)

**Architecture cible V3** - Plateforme MLOps modulaire complète.

**Contenu:**
- Vision et objectifs du TFE
- Analyse de l'architecture actuelle (Phase 1.7)
- Architecture cible V3 (modules, services, communication)
- Plan de migration (Strangler Fig Pattern)
- Roadmap détaillée (Phases 2.0 à 3.1)
- Références et standards (DICOM, MLOps, conformité)

**Lire en premier** pour comprendre la vision globale.

---

### 5. [MODULE_CONTRACTS.md](./MODULE_CONTRACTS.md)

**Contrats d'interface** entre modules pour garantir isolation et testabilité.

**Contenu:**
- Storage Provider Interface (filesystem, S3, PACS)
- ML Service API (inference, feedback, models)
- PACS Plugin Interface (DICOM query/retrieve/store)
- Frontend State Contracts (ViewerStore, AnnotationStore)
- WebSocket Protocol (collaboration temps réel)
- Testing Contracts (unit, integration)
- API Versioning Strategy (v1/v2)

**Lire avant implémentation** pour comprendre les contrats à respecter.

---

### 6. [REFACTORING_PLAN.md](./REFACTORING_PLAN.md)

**Plan détaillé de refactoring** pour migrer du code actuel vers V3.

**Contenu:**
- État des lieux code actuel (fichiers, complexité)
- Phase 2.0: Préparation (Storage abstraction, Config management, API versioning, Tests)
- Phase 2.1: ML Service Prototype (Inference mock, Heatmap generation, Frontend integration)
- Tâches concrètes avec critères de succès
- Livrables et checkpoints

**Lire avant développement** pour suivre le plan de migration étape par étape.

---

## Principes Directeurs

### 1. Modularité Maximale

**Un bug dans X ne doit JAMAIS casser Y.**

- Services isolés (Viewer, ML, PACS, Storage)
- Interfaces abstraites (StorageProvider, etc.)
- Communication via API REST ou événements
- Chaque module testable indépendamment

### 2. Couplage Minimal

**Design by Contract (DbC).**

- Contrats d'interface clairs (Pydantic models, TypeScript interfaces)
- Versioning API (v1/v2) pour éviter breaking changes
- Dépendances explicites (pas de globals cachés)
- Tests de contrat obligatoires

### 3. Simplicité Avant Performance

**Phase 1: Simple et fonctionnel. Phase 2: Optimisation.**

- Pas d'optimisation prématurée
- Vanilla JS (pas de React/Vue pour l'instant)
- PostgreSQL (pas de NoSQL sauf besoin prouvé)
- Monolithe modulaire avant microservices

### 4. Code Production-Ready

**Clean code, sécurisé, testé, documenté.**

- Tests unitaires (>80% coverage)
- Tests d'intégration (workflows complets)
- Logs structurés (JSON, ELK compatible)
- Documentation auto-générée (Swagger, Sphinx)

### 5. Conformité Réglementaire

**RGPD, MDR, AI Act dès le départ.**

- Anonymisation patient (DICOM tags)
- Audit trail (qui a vu quoi, quand)
- Versioning modèles ML (MLflow Registry)
- Documentation technique complète

---

## Roadmap

### Phase 2.0: Préparation (2 semaines) - Janvier 2026

**Objectif:** Refactorer code existant sans changer comportement.

**Livrables:**
- StorageProvider abstraction (filesystem, S3, PACS ready)
- Configuration management (pydantic-settings, feature flags)
- API versioning (v1/v2)
- Tests unitaires (>80% coverage)
- State management frontend (stores)

**Status:** 🔄 En cours (voir REFACTORING_PLAN.md)

---

### Phase 2.1: ML Service Prototype (3 semaines) - Février 2026

**Objectif:** Créer ML Service minimal avec modèle mock.

**Livrables:**
- ML Service (FastAPI) avec endpoint inference
- Modèle mock (détections aléatoires)
- Heatmap generator (PNG overlay)
- Frontend integration (bouton "Run AI", overlay heatmap)

**Status:** ⏸️ Planifié

---

### Phase 2.2: Feedback Loop MVP (2 semaines) - Mars 2026

**Objectif:** Capturer corrections pathologistes.

**Livrables:**
- UI correction (AnnotationTool)
- API feedback (POST /api/ml/feedback)
- Stockage corrections (PostgreSQL)
- Dashboard admin (stats corrections)

**Status:** ⏸️ Planifié

---

### Phase 2.3: PACS Integration POC (3 semaines) - Mars 2026

**Objectif:** Query/Retrieve slides depuis PACS Telemis.

**Livrables:**
- PACS Plugin (pynetdicom)
- C-FIND, C-MOVE implémentés
- PacsStorageProvider
- FolderBrowser onglet "PACS"

**Status:** ⏸️ Planifié

---

### Phase 3.0: MLOps Pipeline (4 semaines) - Mai 2026

**Objectif:** Pipeline complet ML avec ré-entraînement.

**Livrables:**
- MLflow Tracking Server
- Pipeline training (Airflow/Prefect)
- DVC versioning datasets
- A/B testing modèles
- Drift detection (Evidently AI)

**Status:** ⏸️ Planifié

---

### Phase 3.1: Collaboration Temps Réel (3 semaines) - Juin 2026

**Objectif:** Co-visualisation synchronisée.

**Livrables:**
- WebSocket server
- Viewport sync multi-users
- Cursors collaboratifs
- Annotations temps réel

**Status:** ⏸️ Planifié

---

## Stack Technologique

### Backend

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Framework** | FastAPI | Moderne, async, auto-docs |
| **Slide Processing** | OpenSlide | Standard industrie, 12 formats |
| **ML Tracking** | MLflow | Expérimentation, versioning modèles |
| **Data Versioning** | DVC | Git pour datasets |
| **Database** | PostgreSQL | Robuste, ACID, JSON support |
| **Cache** | Redis | Performance, sessions |
| **Storage** | MinIO (S3-compatible) | Scalable, backup cloud |
| **DICOM** | pynetdicom, pydicom | Standard médical |
| **Tests** | pytest, pytest-cov | Coverage, async support |

### Frontend

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Build Tool** | Vite | Rapide, moderne |
| **Language** | Vanilla JS | Pas de framework lourd |
| **Viewer** | OpenSeadragon | Éprouvé pour gigapixel |
| **State** | Custom stores | Simple, pas de Redux/MobX |
| **WebSocket** | socket.io-client | Collaboration temps réel |
| **WebRTC** | PeerJS | P2P co-visualisation |
| **Tests** | Vitest, Playwright | Unitaires + E2E |

### DevOps

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Container** | Docker, Docker Compose | Portabilité, isolation |
| **CI/CD** | GitHub Actions | Gratuit, intégré GitHub |
| **Monitoring** | Prometheus, Grafana | Métriques, dashboards |
| **Logging** | ELK Stack | Logs centralisés |
| **Gateway** | Kong / Traefik | Routage, auth, rate limiting |

---

## Standards et Conformité

### Standards Médicaux

- **DICOM:** https://www.dicomstandard.org/
- **DICOM WSI Supplement 145:** https://www.dicomstandard.org/News-dir/ftsup/docs/sups/sup145.pdf
- **OpenSlide Formats:** https://openslide.org/formats/
- **HL7 FHIR (future):** https://www.hl7.org/fhir/

### MLOps & DevOps

- **12-Factor App:** https://12factor.net/
- **MLflow:** https://mlflow.org/
- **DVC:** https://dvc.org/
- **Evidently AI (drift):** https://www.evidentlyai.com/

### Architecture Patterns

- **Strangler Fig:** https://martinfowler.com/bliki/StranglerFigApplication.html
- **Event-Driven Architecture:** https://martinfowler.com/articles/201701-event-driven.html
- **API Gateway:** https://microservices.io/patterns/apigateway.html

### Sécurité & Conformité

- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **RGPD (GDPR):** https://gdpr.eu/
- **MDR (EU 2017/745):** https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32017R0745
- **AI Act (EU):** https://artificialintelligenceact.eu/

---

## Ressources Complémentaires

### Documentation Projet

- **CLAUDE.md** - Instructions globales pour Claude Agent
- **README.md** - Documentation utilisateur principale
- **docs/Manuel/** - Manuel utilisateur (fonctionnalités validées)
- **docs/ERROR_*.md** - Erreurs documentées
- **.claude/docs/** - Documentation architecture (ce dossier)

### Références Externes

- **OpenSlide Python API:** https://openslide.org/api/python/
- **OpenSeadragon Docs:** https://openseadragon.github.io/docs/
- **FastAPI Tutorial:** https://fastapi.tiangolo.com/tutorial/
- **MLflow Documentation:** https://mlflow.org/docs/latest/index.html
- **Pydantic Settings:** https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

## Contact et Support

**Équipe VarunaPoC:**
- Lead Architecte: [À compléter]
- Tech Lead Backend: [À compléter]
- Tech Lead Frontend: [À compléter]
- ML Engineer: [À compléter]

**Repository:** https://github.com/[À compléter]/VarunaPoC

**License:** Propriétaire (CHU UCL Namur)

---

## Changelog

### v3.0.0 (2025-12-31)

- Architecture V3 complète
- Module contracts définis
- Plan de refactoring détaillé
- Roadmap TFE 2025-2026

### v2.0.0 (Phase antérieure)

- Voir git tags pour historique

---

**Dernière mise à jour:** 2025-12-31
**Prochaine révision:** Après Phase 2.0 (Février 2026)
