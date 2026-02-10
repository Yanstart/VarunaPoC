# Architecture Decision Records - VarunaPoC

**But:** Tracer toutes les decisions architecturales significatives avec leur contexte et justification.

**Format:** ADR (Architecture Decision Record) - Michael Nygard

---

## ADR-001: Vanilla JavaScript sans Framework

**Date:** 2025-10-17
**Statut:** Accepte
**Contexte:** Choix du framework frontend pour le viewer
**Decision:** Utiliser Vanilla JavaScript sans React/Vue/Angular
**Consequences:**
- (+) Pas de dependance framework, pas d'obsolescence rapide
- (+) Bundle minimal, performance optimale
- (+) Controle total sur le DOM
- (-) Pas de composants reactifs automatiques
- (-) Plus de code boilerplate manuel
**Alternatives Rejetees:**
- React: Overkill pour un viewer, bundle trop gros
- Vue: Idem, complexite inutile
- Svelte: Interessant mais equipe non familiere
**Validation Admin:** Oui - Decision initiale du projet

---

## ADR-002: OpenSlide + OpenSeadragon Stack

**Date:** 2025-10-17
**Statut:** Accepte
**Contexte:** Choix des librairies pour WSI (Whole Slide Imaging)
**Decision:** Backend OpenSlide (Python) + Frontend OpenSeadragon
**Consequences:**
- (+) Standards de l'industrie, tres documentes
- (+) Support 10+ formats de slides (94 lames testees)
- (+) OpenSeadragon gere le tiling automatiquement
- (+) Communautes actives
- (-) OpenSlide a des bugs (BIF LEFT direction, broken slides)
- (-) Dependance a des binaires natifs (DLL Windows)
**Alternatives Rejetees:**
- Lecteurs proprietaires: Vendor lock-in
- DICOM pur: Pas tous les formats supportes
- Custom reader: Reinventer la roue
**Validation Admin:** Oui - Stack recommandee par la litterature

---

## ADR-003: DZI Protocol pour Tile Serving

**Date:** 2025-10-17
**Statut:** Accepte
**Contexte:** Protocole de communication tiles entre backend et frontend
**Decision:** Utiliser Deep Zoom Image (DZI) protocol
**Consequences:**
- (+) Support natif OpenSeadragon
- (+) Simple: metadata JSON + tiles JPEG
- (+) Cacheable, compatible CDN
- (-) Pas de standard medical (DICOM Web serait mieux pour integration PACS)
**Alternatives Rejetees:**
- IIIF: Plus complexe, pas necessaire pour PoC
- DICOM Web: Complexite, tous les formats ne sont pas DICOM
- Custom protocol: Maintenance couteuse
**Validation Admin:** Oui - Simplicite priorisee pour PoC

---

## ADR-004: Event-Driven Architecture (EventBus)

**Date:** 2025-12-30
**Statut:** Accepte
**Contexte:** Communication entre composants frontend
**Decision:** Implementer un EventBus singleton (pattern Observer) avec unsubscribe
**Consequences:**
- (+) Decouplage total entre composants
- (+) Facilite l'ajout de nouveaux composants
- (+) Debug mode pour tracer les events
- (-) Flux de donnees moins explicite
- (-) Risque de "event spaghetti" si mal gere
- (-) Attention aux listener leaks (voir ADR-017)
**Alternatives Rejetees:**
- Props drilling: Trop de couplage
- Context global: Pas assez flexible
- Redux-like: Overkill sans framework
**Validation Admin:** Oui - Architecture documentee dans PATTERNS.md

---

## ADR-005: Factory Pattern pour Viewers

**Date:** 2025-12-30
**Statut:** Accepte
**Contexte:** Creation de multiples viewers avec configurations differentes
**Decision:** ViewerFactory avec presets (default, minimal, compare, thumbnail)
**Consequences:**
- (+) Configuration standardisee
- (+) Presets reutilisables
- (+) Encapsulation de la complexite OSD
- (-) Un niveau d'indirection supplementaire
**Alternatives Rejetees:**
- Configuration directe: Duplication de code
- Builder pattern: Trop verbeux pour ce cas
**Validation Admin:** Oui - Simplifie le code d'appel

---

## ADR-006: State Machine pour Viewer Lifecycle

**Date:** 2025-12-30
**Statut:** Accepte
**Contexte:** Gestion des etats du viewer (IDLE, LOADING, READY, ERROR)
**Decision:** Implementer ViewerState avec transitions validees
**Consequences:**
- (+) Empeche les transitions invalides
- (+) Callbacks sur enter/exit chaque etat
- (+) Debug facilite (etat explicite)
- (-) Complexite ajoutee pour cas simples
**Alternatives Rejetees:**
- Boolean flags: Etats ambigus possibles
- Simple string: Pas de validation
**Validation Admin:** Oui - Best practice pour composants complexes

---

## ADR-007: Multi-Viewer avec SyncController (Mediator)

**Date:** 2025-12-30
**Statut:** Accepte
**Contexte:** Synchronisation pan/zoom entre plusieurs viewers
**Decision:** SyncController centralise comme Mediator
**Consequences:**
- (+) Logique de sync centralisee
- (+) Evite couplage viewer-to-viewer
- (+) Debouncing integre (16ms)
- (-) Single point of complexity
**Alternatives Rejetees:**
- Sync peer-to-peer: Boucles infinies, complexite O(n^2)
- Events simples: Pas de controle sur timing
**Validation Admin:** Oui - Pattern Mediator classique

---

## ADR-008: MD5 Hash comme Slide ID

**Date:** 2025-10-27
**Statut:** Accepte
**Contexte:** Generation d'identifiants uniques pour les lames
**Decision:** MD5 du chemin complet comme ID
**Consequences:**
- (+) Deterministe (meme path = meme ID)
- (+) URL-safe
- (+) Pas de collision pratique
- (-) Change si le fichier est deplace
- (-) MD5 cryptographiquement faible (mais pas un probleme ici)
**Validation Admin:** Oui - Simple et efficace pour PoC

---

## ADR-009: LRU Cache pour Slides Ouvertes

**Date:** 2025-10-28
**Statut:** Accepte
**Contexte:** Gestion memoire pour OpenSlide objects
**Decision:** Cache LRU avec max 5 slides simultanees
**Consequences:**
- (+) Evite re-ouverture couteuse (~200-500ms)
- (+) Limite memoire (slides = gigaoctets)
- (+) Simple a implementer
- (-) Cache perdu au restart
- (-) Pas de persistence cross-process
**Alternatives Rejetees:**
- Pas de cache: Performance degradee
- Cache illimite: Memoire explosive
- Redis: Overkill pour PoC (prevu post-MVP)
**Validation Admin:** Oui - Bon compromis performance/memoire

---

## ADR-010: Cerveau d'Orchestration

**Date:** 2026-01-29
**Statut:** Accepte
**Contexte:** Besoin d'un systeme pour economiser tokens, valider propositions, et maintenir contexte
**Decision:** Creer .claude/BRAIN.md + .claude/memory/ avec LEARNINGS.md et DECISIONS.md
**Consequences:**
- (+) Processus systematique pour toute demande
- (+) Memoire persistante entre sessions
- (+) Validation admin explicite
- (+) Tracabilite des decisions
- (-) Overhead administratif
- (-) Fichiers a maintenir synchronises
**Alternatives Rejetees:**
- Statu quo: Perte de contexte, tokens gaspilles
- Base de donnees: Overkill, pas accessible a Claude
- Wiki externe: Pas integre au workflow
**Validation Admin:** Oui

---

## ADR-011: Securite - RBAC + JWT (Phase 3)

**Date:** 2026-01-29 (Planifie), MAJ 2026-02-08
**Statut:** Propose
**Contexte:** Score securite 0/10, API completement ouverte, non conforme RGPD
**Decision:** Implementer RBAC + JWT comme solution auth Phase 3 (semaines 10-13)
**Consequences:**
- (+) Controle d'acces granulaire (Viewer, Annotator, Admin, SuperAdmin)
- (+) Tokens stateless, scalable
- (+) Compatible SSO futur (SAML 2.0/OAuth 2.0)
- (-) Complexite token refresh/revocation
- (-) Necessite HTTPS obligatoire
**Alternatives Rejetees:**
- HTTP Basic Auth: Trop basique, pas de roles
- Session cookies: Stateful, problemes scaling
- OAuth2 direct: Necessite IdP externe, trop pour Phase 3
**Validation Admin:** En attente

---

## ADR-012: MLOps Tag-Based Routing

**Date:** 2025-12-31 (Planifie)
**Statut:** Propose
**Contexte:** Besoin de router les slides vers les bons modeles ML
**Decision:** Systeme de tags (organe, coloration, marqueur) → routing automatique
**Consequences:**
- (+) Modeles specialises plus precis que generiques
- (+) Extensible (nouveaux tags, nouveaux modeles)
- (+) Configuration declarative (YAML)
- (-) Necessite extraction tags fiable
- (-) Maintenance de la table de routage
**Alternatives Rejetees:**
- Modele unique: Moins precis
- Selection manuelle: Friction utilisateur
- Detection automatique format: Insuffisant pour routing ML
**Validation Admin:** En attente

---

## ADR-013: Repository Restructuration avec Archives/

**Date:** 2026-02-02
**Statut:** Accepte
**Contexte:** Repository encombre par 35+ fichiers Phase 2+/3+ melanges avec le PoC Phase 1
**Decision:** Creer dossier Archives/ avec sous-dossiers thematiques pour isoler la documentation future
**Consequences:**
- (+) Racine epuree, focus sur Phase courante visible
- (+) Documentation future preservee mais hors du chemin critique
- (+) Structure claire avec README explicatif dans Archives/
- (+) Facilite navigation pour nouveaux contributeurs
- (-) Risque d'oubli des documents archives
- (-) Maintenance du README Archives/ necessaire
**Alternatives Rejetees:**
- Supprimer docs Phase 2+: Perte d'information precieuse
- Branches separees: Trop complexe pour de la documentation
- Sous-dossiers dans docs/: Moins de separation visuelle
**Validation Admin:** Oui (session 2026-02-02)

---

## ADR-014: Systeme de Selection Multi-Reader avec Scoring

**Date:** 2026-02-04
**Statut:** Accepte
**Contexte:** Besoin de supporter plusieurs bibliotheques de lecture (OpenSlide, Bio-Formats, libvips) avec selection automatique et fallback
**Decision:** Architecture modulaire combinant Strategy + Chain of Responsibility + Registry patterns avec systeme de scoring 0-100
**Consequences:**
- (+) Readers interchangeables sans modifier le core
- (+) Fallback automatique si reader echoue
- (+) Plugins peuvent enregistrer leurs readers dynamiquement
- (+) Complexite O(n) ou n = nombre de readers (5-10)
- (+) Scoring explicite pour prioritisation
- (-) Un niveau d'abstraction supplementaire
- (-) Overhead minime pour le cas mono-reader actuel
**Details Techniques:**
- Score 100 = support parfait (ex: OpenSlide pour MRXS)
- Score 80 = bon support avec limitations (ex: OpenSlide pour DICOM)
- Score 60 = support partiel (ex: OpenSlide pour CZI)
- Score 0 = non supporte (ex: OpenSlide pour VSI)
**Fichiers:** `docs/architecture/READER_SELECTION_SYSTEM.md`
**Validation Admin:** Oui (session 2026-02-04)

---

## ADR-015: Specialistes Design Patterns et Algorithmes dans le Cerveau

**Date:** 2026-02-04
**Statut:** Accepte
**Contexte:** Besoin de valider les approches architecturales et algorithmiques avant implementation
**Decision:** Ajouter deux specialistes au cerveau d'orchestration pour consultation
**Consequences:**
- (+) Validation patterns avant implementation
- (+) Analyse complexite algorithmique systematique
- (+) Decisions architecturales mieux documentees
- (-) Etape supplementaire dans le processus
**Fichiers:** `.claude/BRAIN.md` (section "Specialistes Fondamentaux")
**Validation Admin:** Oui (session 2026-02-04)

---

## ADR-016: PostgreSQL + PostGIS pour Annotations

**Date:** 2026-02-05
**Statut:** Accepte
**Contexte:** Besoin de stocker des annotations geometriques (polygones, points, rectangles) sur les lames
**Decision:** PostgreSQL 15 + PostGIS avec async SQLAlchemy + GeoAlchemy2, SRID=0 (coordonnees pixels)
**Consequences:**
- (+) Requetes spatiales performantes (intersection, containment)
- (+) Standard industriel pour donnees geometriques
- (+) GeoJSON natif via ST_AsGeoJSON
- (+) Compatible avec le standard OGC
- (-) Dependance lourde (PostgreSQL + extension PostGIS)
- (-) SRID=0 non standard (mais correct pour coordonnees pixels)
**Alternatives Rejetees:**
- SQLite + SpatiaLite: Pas async, moins performant multi-user
- MongoDB GeoJSON: Pas de schema strict, overkill
- Fichiers GeoJSON: Pas de CRUD concurrent, pas de requetes spatiales
**Port:** 5433 (pas 5432, conflit TimescaleDB)
**Validation Admin:** Oui (session 2026-02-05)

---

## ADR-017: Unsubscribe Pattern pour EventBus

**Date:** 2026-02-06
**Statut:** Accepte
**Contexte:** Memory leaks: composants detruits recevant encore des events → crashs null reference
**Decision:** `eventBus.on()` retourne une fonction unsubscribe. Chaque composant stocke les unsubscribers dans `this._unsubscribers[]` et les appelle dans `destroy()`
**Consequences:**
- (+) Zero listener leaks
- (+) Pattern simple et coherent
- (+) Pas besoin de garder reference aux callbacks
- (-) Discipline requise (chaque composant doit implementer le pattern)
**Alternatives Rejetees:**
- WeakRef callbacks: Support navigateur incertain, complexe
- Auto-cleanup par EventBus: Necessiterait tracking de composants
- Event delegation (DOM): Pas applicable pour events custom
**Fichiers:** `frontend/src/core/EventBus.js`, tous les composants Phase 2
**Validation Admin:** Oui (session 2026-02-06)

---

## ADR-018: SVG Overlay pour Annotations (pas Canvas)

**Date:** 2026-02-05
**Statut:** Accepte
**Contexte:** Choix du rendu pour annotations sur le viewer OSD
**Decision:** SVG overlay au lieu de Canvas HTML5
**Consequences:**
- (+) Chaque annotation = element DOM interactif (click, hover, edit)
- (+) Styling CSS simple (couleurs, opacite, bordures)
- (+) Accessible et inspectable dans DevTools
- (+) Hit-testing natif du navigateur
- (-) Performance degradee avec 1000+ annotations (DOM lourd)
- (-) Pas de rendu personnalise complexe (gradients, effets)
**Alternatives Rejetees:**
- Canvas HTML5: Rapide mais pas interactif sans hit-testing manuel
- WebGL: Overkill, complexite extreme
- OSD overlay API: Trop limitee pour annotations complexes
**Fichiers:** `frontend/src/components/AnnotationLayer.js`
**Validation Admin:** Oui (session 2026-02-05)

---

## ADR-019: Sync def (pas async def) pour Routes OpenSlide

**Date:** 2026-02-05
**Statut:** Accepte
**Contexte:** Routes `async def` avec I/O synchrone OpenSlide bloquaient l'event loop (30s+ pour 28 tiles)
**Decision:** Toutes les routes slides.py en `def` (pas `async def`). FastAPI les execute dans le threadpool.
**Consequences:**
- (+) Performance 15x meilleure (2.1s au lieu de 30s+ pour 28 tiles)
- (+) Event loop jamais bloque
- (+) Zero changement d'API
- (-) Pas de concurrence asyncio dans la route (pas un probleme)
**A Retenir:** Regle d'or: si I/O synchrone → `def`. Si I/O async (aiohttp, asyncpg) → `async def`.
**Fichiers:** `backend/routes/slides.py` (6 routes)
**Validation Admin:** Oui (session 2026-02-05)

---

## ADR-020: Slideflow + Phikon-v2 pour ML

**Date:** 2026-02-05
**Statut:** Accepte
**Contexte:** Besoin d'inference ML sur les lames (heatmaps, detection, classification)
**Decision:** Slideflow framework + Phikon-v2 (Owkin foundation model) via CUDA
**Consequences:**
- (+) Phikon-v2 = state-of-the-art pour pathologie (foundation model DINO)
- (+) Slideflow gere le tiling, batching, normalisation
- (+) Heatmaps 64x64 en ~2.5min GPU
- (+) Uncertainty quantification native
- (-) GPU CUDA requis (pas de fallback CPU pratique)
- (-) Ne supporte pas DICOM ni Generic TIFF sans MPP
- (-) transformers>=4.22 requis
**Alternatives Rejetees:**
- CLAM: Plus ancien, moins generaliste
- Custom PyTorch: Maintenance lourde
- TensorFlow Serving: Ecosysteme different
**Fichiers:** `backend/services/ml/slideflow_service.py`, `backend/routes/ml.py`
**Validation Admin:** Oui (session 2026-02-05)

---

## Index des Decisions par Domaine

### Architecture Frontend
- ADR-001: Vanilla JavaScript sans Framework
- ADR-004: Event-Driven Architecture (EventBus)
- ADR-005: Factory Pattern pour Viewers
- ADR-006: State Machine pour Viewer Lifecycle
- ADR-007: Multi-Viewer avec SyncController
- ADR-017: Unsubscribe Pattern pour EventBus
- ADR-018: SVG Overlay pour Annotations

### Architecture Backend
- ADR-002: OpenSlide + OpenSeadragon Stack
- ADR-003: DZI Protocol pour Tile Serving
- ADR-008: MD5 Hash comme Slide ID
- ADR-009: LRU Cache pour Slides Ouvertes
- ADR-014: Systeme de Selection Multi-Reader avec Scoring
- ADR-016: PostgreSQL + PostGIS pour Annotations
- ADR-019: Sync def pour Routes OpenSlide
- ADR-020: Slideflow + Phikon-v2 pour ML

### Securite
- ADR-011: Securite RBAC + JWT (Phase 3)

### MLOps
- ADR-012: MLOps Tag-Based Routing

### Orchestration
- ADR-010: Cerveau d'Orchestration
- ADR-015: Specialistes Design Patterns et Algorithmes

### Organisation Repository
- ADR-013: Repository Restructuration avec Archives/

---

**Derniere mise a jour:** 2026-02-08
**Nombre total d'ADR:** 20
