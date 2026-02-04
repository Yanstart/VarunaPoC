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
- (+) Support 12+ formats de slides
- (+) OpenSeadragon gere le tiling automatiquement
- (+) Communautes actives
- (-) OpenSlide a des bugs (BIF LEFT direction)
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
**Decision:** Implementer un EventBus singleton (pattern Observer)
**Consequences:**
- (+) Decouplage total entre composants
- (+) Facilite l'ajout de nouveaux composants
- (+) Debug mode pour tracer les events
- (-) Flux de donnees moins explicite
- (-) Risque de "event spaghetti" si mal gere
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
**Alternatives Rejetees:**
- UUID: Non deterministe, cache inefficace
- Path encode: Caracteres speciaux problematiques
- Auto-increment DB: Necessite base de donnees
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
- Redis: Overkill pour PoC (prevu V3)
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
- (-) Fichiers a maintenir
**Alternatives Rejetees:**
- Statu quo: Perte de contexte, tokens gaspilles
- Base de donnees: Overkill, pas accessible a Claude
- Wiki externe: Pas integre au workflow
**Validation Admin:** En cours (cette session)

---

## ADR-011: Securite Phase 1 - Basic Auth + HTTPS

**Date:** 2026-01-29 (Planifie)
**Statut:** Propose
**Contexte:** Score securite 0/10, non conforme RGPD
**Decision:** Implementer HTTP Basic Auth + TLS comme premiere etape
**Consequences:**
- (+) Bloque acces non authentifie immediatement
- (+) Simple a implementer (FastAPI support natif)
- (+) Compatible avec tous les clients HTTP
- (-) Credentials en base64 (necessité HTTPS)
- (-) Pas de gestion de sessions/tokens
**Alternatives Rejetees:**
- JWT direct: Plus complexe a implementer correctement
- OAuth2: Necessite IdP, trop pour Phase 1
- Rien: Inacceptable pour donnees medicales
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
- (+) Racine epuree, focus sur Phase 1 visible
- (+) Documentation Phase 2+/3+ preservee mais hors du chemin critique
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
- En cas d'echec, essai du reader suivant par score decroissant

**Fichiers:**
- `docs/architecture/READER_SELECTION_SYSTEM.md` (document de conception complet)
- Future implementation dans `backend/services/readers/`

**Alternatives Rejetees:**
- Reader unique (OpenSlide): Formats Olympus/Zeiss non supportes
- Selection manuelle: Friction utilisateur, erreurs
- If/else sur extension: Non extensible, maintenance difficile

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
- (+) Reference aux patterns standard (GOF, SOLID)
- (-) Etape supplementaire dans le processus

**Specialistes:**
1. **Design Patterns Specialist** - GOF, SOLID, Clean Architecture
2. **Algorithms Specialist** - Structures donnees, complexite, scoring

**Fichiers:**
- `.claude/BRAIN.md` (section "Specialistes Fondamentaux")

**Validation Admin:** Oui (session 2026-02-04)

---

## Template pour Nouvelles Decisions

```markdown
## ADR-[NNN]: [TITRE]

**Date:** YYYY-MM-DD
**Statut:** Propose | Accepte | Rejete | Obsolete
**Contexte:** [Pourquoi cette decision est necessaire]
**Decision:** [Ce qui a ete decide]
**Consequences:**
- (+) [Avantage 1]
- (+) [Avantage 2]
- (-) [Inconvenient 1]
- (-) [Inconvenient 2]
**Alternatives Rejetees:**
- [Option A]: [Raison du rejet]
- [Option B]: [Raison du rejet]
**Validation Admin:** [Oui/Non/En attente] + [commentaire]
```

---

## Index des Decisions par Domaine

### Architecture Frontend
- ADR-001: Vanilla JavaScript sans Framework
- ADR-004: Event-Driven Architecture (EventBus)
- ADR-005: Factory Pattern pour Viewers
- ADR-006: State Machine pour Viewer Lifecycle
- ADR-007: Multi-Viewer avec SyncController

### Architecture Backend
- ADR-002: OpenSlide + OpenSeadragon Stack
- ADR-003: DZI Protocol pour Tile Serving
- ADR-008: MD5 Hash comme Slide ID
- ADR-009: LRU Cache pour Slides Ouvertes
- ADR-014: Systeme de Selection Multi-Reader avec Scoring

### Securite
- ADR-011: Securite Phase 1 - Basic Auth + HTTPS

### MLOps
- ADR-012: MLOps Tag-Based Routing

### Orchestration
- ADR-010: Cerveau d'Orchestration
- ADR-015: Specialistes Design Patterns et Algorithmes

### Organisation Repository
- ADR-013: Repository Restructuration avec Archives/

---

**Derniere mise a jour:** 2026-02-04
**Nombre total d'ADR:** 15
