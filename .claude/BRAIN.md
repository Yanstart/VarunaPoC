# Cerveau d'Orchestration VarunaPoC

**Version:** 1.0
**Date:** 2026-01-29

Ce document est le **point d'entree central** pour toute interaction Claude Code sur ce projet. Il definit le processus systematique de traitement des demandes utilisateur.

---

## Philosophie: Economie & Precision

**Principes fondamentaux:**
1. **Zero gaspillage de tokens** - Utiliser la memoire persistante, ne pas re-explorer
2. **Validation systematique** - Challenger chaque proposition avant implementation
3. **Sources verifiees** - Toujours citer les references officielles
4. **Admin dans la boucle** - L'utilisateur valide les decisions critiques

---

## PROCESSUS OBLIGATOIRE (Toute Demande)

```
UTILISATEUR PROMPT
       |
       v
[1. COMPREHENSION] -----> Quoi veut-il exactement?
       |                  - Parser l'intention
       |                  - Identifier le domaine (backend/frontend/infra/ml/docs)
       |                  - Verifier le scope (PoC vs hors-scope)
       |
       v
[2. CONTEXTE] ---------> Qu'avons-nous deja?
       |                  - Lire .claude/memory/LEARNINGS.md
       |                  - Lire .claude/memory/DECISIONS.md
       |                  - Consulter docs/ pertinents
       |                  - Verifier git status/log recent
       |
       v
[3. MOBILISATION] -----> Quels agents/skills utiliser?
       |                  - Choisir agent(s) specialise(s)
       |                  - Preparer skills a invoquer
       |                  - Identifier sources officielles a consulter
       |
       v
[4. PLANIFICATION] ----> Comment proceder?
       |                  - Decomposer en taches
       |                  - Estimer risques/impacts
       |                  - Preparer questions de validation
       |
       v
[5. VALIDATION ADMIN] -> Demander approbation AVANT d'agir
       |                  - Presenter le plan
       |                  - Expliquer les choix
       |                  - Attendre OK explicite
       |
       v
[6. EXECUTION] --------> Implementer avec traçabilite
       |                  - Code avec commentaires
       |                  - Commits atomiques
       |                  - Mise a jour documentation
       |
       v
[7. CAPITALISATION] ---> Enregistrer les apprentissages
                         - Mettre a jour LEARNINGS.md
                         - Ajouter decision dans DECISIONS.md
                         - Commit les changements
```

---

## Matrice de Routage Automatique

### Par Mots-Cles dans le Prompt

| Mots-Cles | Agent Principal | Skills | Sources Officielles |
|-----------|-----------------|--------|---------------------|
| tile, tuile, streaming, cache | backend-tech-lead | slide-tester | openslide.org |
| viewer, UI, bouton, interface | frontend-tech-lead | manual-updater | openseadragon.github.io |
| zoom, pan, coordonnees, sync | performance-engineer | coordinate-validator | OSD viewport docs |
| format, mrxs, bif, tiff | backend-tech-lead | slide-tester | openslide.org/formats |
| securite, auth, HIPAA, RGPD | security-architect | - | OWASP, NIST |
| PACS, DICOM, Telemis | integration-engineer | - | dicomstandard.org |
| ML, IA, modele, inference | ml-architect | - | mlflow.org, pytorch.org |
| docker, deploy, k8s, infra | infrastructure-architect | - | kubernetes.io |
| architecture, design, refactor | lead-architecte | - | CLAUDE.md |
| erreur, bug, crash, ne marche pas | performance-engineer | error-documenter | - |
| documentation, manuel, user guide | frontend-tech-lead | manual-updater | - |
| API, endpoint, route | backend-tech-lead | api-documenter | fastapi.tiangolo.com |
| pattern, factory, strategy, modulaire | design-patterns-specialist | - | refactoring.guru, GOF |
| scoring, algorithme, complexite, tri | algorithms-specialist | - | CLRS, algorithm visualizations |
| interface, abstraction, plugin, extensible | design-patterns-specialist | - | Clean Architecture |
| fallback, priorite, selection, routing | algorithms-specialist | - | - |

### Par Type de Demande

| Type | Processus |
|------|-----------|
| **Question simple** | Repondre directement avec sources |
| **Bug report** | Diagnostic → error-documenter si complexe → fix |
| **Feature request** | Analyse scope → design → validation admin → implementation |
| **Refactoring** | Architecture review → plan → validation → execution incrementale |
| **Deployment** | infrastructure-architect → checklist securite → validation |

---

## Fichiers Memoire Persistante

### .claude/memory/ROADMAP.md
**But:** Vision projet, phases, Gantt Mermaid, suivi d'avancement

**Contenu:**
- Gantt chart global (Phases 0-5)
- Gantt detail (Phase 1 & 2)
- Liste des taches par statut (Termine, En cours, A faire, Backlog)
- Dependances critiques (flowchart)
- Risques et mitigations
- Metriques de suivi

**Utilisation:**
- Consulter avant de planifier une nouvelle tache
- Mettre a jour apres chaque completion significative
- Synchroniser avec GitHub Projects Kanban

### .claude/memory/LEARNINGS.md
**But:** Eviter de refaire les memes erreurs, capitaliser les decouvertes

**Structure:**
```markdown
## [DATE] - [SUJET]
**Contexte:** Ce qu'on essayait de faire
**Probleme:** Ce qui n'a pas marche
**Solution:** Ce qui a marche
**A Retenir:** Lecon pour le futur
**Fichiers:** Liste des fichiers concernes
```

### .claude/memory/DECISIONS.md
**But:** Tracer les decisions architecturales (ADR - Architecture Decision Records)

**Structure:**
```markdown
## ADR-[NNN]: [TITRE]
**Date:** YYYY-MM-DD
**Statut:** Propose | Accepte | Rejete | Obsolete
**Contexte:** Pourquoi cette decision est necessaire
**Decision:** Ce qui a ete decide
**Consequences:** Impact positif et negatif
**Alternatives Rejetees:** Autres options considerees
**Validation Admin:** Oui/Non + commentaire
```

### .claude/memory/SESSION_CONTEXT.md
**But:** Contexte de la session courante (reset a chaque nouvelle conversation)

**Structure:**
```markdown
## Session [DATE]
**Objectif Principal:** [Ce que l'utilisateur veut accomplir]
**Fichiers Modifies:** Liste cumulative
**Taches Completees:** Checklist
**Taches Restantes:** Checklist
**Questions en Attente:** Pour l'admin
```

---

## Regles de Validation

### Quand Demander Validation Admin

**TOUJOURS demander avant:**
- Modification de plus de 3 fichiers
- Changement d'architecture (nouveau pattern, nouvelle dependance)
- Suppression de code
- Modification de configuration
- Commit/Push vers repository
- Installation de dependances
- Tout ce qui touche a la securite
- Decisions avec impact > 1 heure de travail
- **Actions illogiques ou hors contexte** (voir section ci-dessous)

**Peut proceder sans demander:**
- Lecture de fichiers
- Recherche dans le codebase
- Consultation de documentation
- Reponse a une question simple
- Correction de typo evidente

### Detection des Actions Illogiques (CRITIQUE)

**Principe:** Avant d'executer une action, verifier qu'elle a un sens dans le contexte du projet VarunaPoC (visualisation de lames histologiques).

**TOUJOURS questionner si:**
- Le contenu n'a aucun lien avec WSI/OpenSlide/OpenSeadragon/imagerie medicale
- Un fichier/dossier semble appartenir a un autre projet
- La technologie mentionnee n'existe pas dans le projet (ex: Go, Rust, QUIC)
- L'action semble disproportionnee ou hors sujet

**Format de Demande de Justification:**
```
## Verification Requise

**Action demandee:** [Description]

**Alerte:** Cette action semble hors contexte car:
- [Raison 1: ex. "QUIC-Go n'est pas utilise dans VarunaPoC"]
- [Raison 2: ex. "Ce dossier contient du code Go, le projet est Python/JS"]

**Questions:**
1. Ce contenu appartient-il vraiment a VarunaPoC?
2. Si oui, quel est le lien avec la visualisation de lames?
3. Sinon, ou devrait-il etre place?

**En attente de clarification avant de proceder.**
```

**Exemple d'erreur a eviter (2026-02-02):**
- Dossier `Quick-restructure/` contenant un projet QUIC-Go (tunneling reseau)
- N'a AUCUN rapport avec VarunaPoC (visualisation de lames)
- Aurait du etre detecte comme hors contexte et questionne
- Lecon: Toujours verifier la coherence thematique avant d'archiver/commiter

### Format de Demande de Validation

```markdown
## Validation Requise

**Action proposee:** [Description courte]

**Justification:**
- [Pourquoi cette action]
- [Benefices attendus]

**Risques identifies:**
- [Risque 1]
- [Risque 2]

**Alternatives considerees:**
1. [Alternative A] - Rejete car [raison]
2. [Alternative B] - Rejete car [raison]

**Fichiers impactes:**
- `path/to/file1.py` - [modification]
- `path/to/file2.js` - [modification]

**Voulez-vous proceder?** [Oui/Non/Modifier]
```

---

## Challenge des Propositions

### Grille d'Evaluation (Avant Implementation)

Pour chaque proposition, evaluer:

| Critere | Question | Score 0-3 |
|---------|----------|-----------|
| **Pertinence** | Repond-elle vraiment au besoin exprime? | |
| **Simplicite** | Est-ce la solution la plus simple? | |
| **Coherence** | S'integre-t-elle avec l'existant? | |
| **Maintenabilite** | Sera-t-elle facile a maintenir? | |
| **Performance** | Impact sur les performances? | |
| **Securite** | Introduit-elle des vulnerabilites? | |
| **Documentation** | Est-elle bien documentee? | |

**Score < 14:** Revoir la proposition
**Score 14-18:** Acceptable avec reserves
**Score > 18:** Excellente proposition

### Questions de Challenge Systematiques

1. **"Pourquoi pas plus simple?"** - Y a-t-il une solution avec moins de code?
2. **"Qu'existait-il avant?"** - Est-ce qu'on reinvente la roue?
3. **"Que dit la doc officielle?"** - A-t-on verifie les best practices?
4. **"Quel est le cas d'echec?"** - Que se passe-t-il si ca ne marche pas?
5. **"Qui va maintenir ca?"** - Est-ce comprehensible pour un autre dev?

---

## Utilisation Optimale de Claude Code

### Features a Maximiser

1. **Agents Specialises** - Toujours deleguer au bon expert
2. **Skills Automatises** - Invoquer pour taches repetitives
3. **TodoWrite** - Tracker les taches en cours
4. **Bash (git)** - Versionner systematiquement
5. **Glob/Grep** - Rechercher avant de recreer
6. **Task (subagents)** - Paralleliser les analyses

### Anti-Patterns a Eviter

- **Re-exploration inutile** - Consulter MEMORY avant d'explorer
- **Code sans commit** - Commiter regulierement
- **Modification sans validation** - Demander approbation
- **Solution sans source** - Toujours citer la reference
- **Reponse sans contexte** - Expliquer le raisonnement

---

## Integration Git

### Avant Toute Modification

```bash
# Verifier l'etat actuel
git status
git log --oneline -5
git diff --stat
```

### Apres Modification Significative

```bash
# Commit atomique avec message descriptif
git add [fichiers specifiques]
git commit -m "type(scope): description

- Detail 1
- Detail 2"
```

**IMPORTANT:** Ne PAS ajouter de signature `Co-Authored-By`. L'admin prefere des commits sans attribution.

### Types de Commits

- `feat`: Nouvelle fonctionnalite
- `fix`: Correction de bug
- `docs`: Documentation uniquement
- `refactor`: Refactoring sans changement fonctionnel
- `test`: Ajout/modification de tests
- `chore`: Maintenance (dependencies, configs)
- `perf`: Amelioration de performance

---

## Checklist Fin de Session

Avant de terminer une session:

- [ ] Toutes les modifications commitees?
- [ ] LEARNINGS.md mis a jour si nouvelle decouverte?
- [ ] DECISIONS.md mis a jour si decision architecturale?
- [ ] ROADMAP.md mis a jour si tache completee ou ajoutee?
- [ ] Documentation mise a jour si feature complete?
- [ ] Aucun fichier temporaire laisse?
- [ ] Aucune modification non testee?

---

## Quick Reference: Agents et Skills

### Agents (Delegation via Task)

```
chief-architect     → Orchestration generale
backend-tech-lead   → FastAPI, OpenSlide, Python
frontend-tech-lead  → Vite, JS, OpenSeadragon
performance-engineer→ Coordinates, caching, profiling
ml-architect        → MLOps, models, feedback loop
infrastructure-architect → Docker, K8s, CI/CD
lead-architecte     → Architecture globale, patterns
security-architect  → Auth, encryption, compliance
integration-engineer→ DICOM, PACS, HL7
design-patterns-specialist → Patterns GOF, SOLID, Clean Architecture
algorithms-specialist      → Structures donnees, complexite, scoring
```

### Skills (Workflows Automatises)

```
error-documenter    → Documenter erreurs dans docs/ERROR_*.md
manual-updater      → Mettre a jour docs/Manuel/
api-documenter      → Documenter endpoints FastAPI
slide-tester        → Tester tous formats (.mrxs, .bif, .tif)
coordinate-validator→ Valider mapping coordonnees
```

---

## Specialistes Fondamentaux (Support Decisionnaire)

Ces specialistes sont invoques par l'orchestrateur pour valider les approches, resoudre les problemes complexes, et guider les decisions architecturales.

### Design Patterns Specialist

**Role:** Expert en patterns de conception (GOF), principes SOLID, Clean Architecture.

**Quand l'invoquer:**
- Choix entre plusieurs approches architecturales
- Conception de systeme modulaire/extensible
- Validation qu'un design respecte les bonnes pratiques
- Refactoring pour ameliorer la maintenabilite

**Expertise:**
- **Patterns Creationnels:** Factory, Abstract Factory, Builder, Singleton, Prototype
- **Patterns Structurels:** Adapter, Bridge, Composite, Decorator, Facade, Proxy
- **Patterns Comportementaux:** Chain of Responsibility, Strategy, Observer, State
- **Principes SOLID:** Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion
- **Clean Architecture:** Layers, Boundaries, Dependency Rule

**Format de Consultation:**
```markdown
## Consultation Design Patterns

**Probleme:** [Description du probleme architectural]

**Contexte:**
- Systeme actuel: [Description]
- Contraintes: [Liste]
- Objectifs: [Liste]

**Options considerees:**
1. [Option A]
2. [Option B]

**Questions:**
- Quel pattern est le plus adapte?
- Quels sont les trade-offs?
- Comment assurer l'extensibilite?
```

### Algorithms Specialist

**Role:** Expert en structures de donnees, complexite algorithmique, systemes de scoring et selection.

**Quand l'invoquer:**
- Conception de systeme de scoring/priorite
- Optimisation de performance algorithmique
- Choix de structure de donnees optimale
- Validation de complexite (Big-O)

**Expertise:**
- **Structures:** Arrays, Lists, Trees, Heaps, Graphs, Hash Tables
- **Algorithmes:** Tri, Recherche, Graph traversal, Dynamic Programming
- **Complexite:** Time/Space complexity, Amortized analysis
- **Patterns algorithmiques:** Greedy, Divide & Conquer, Backtracking

**Format de Consultation:**
```markdown
## Consultation Algorithmes

**Probleme:** [Description du probleme algorithmique]

**Donnees:**
- Input: [Type et taille]
- Output attendu: [Description]
- Contraintes: [Temps, memoire, etc.]

**Questions:**
- Quelle structure de donnees utiliser?
- Quelle complexite viser?
- Comment gerer les cas limites?
```

---

## Exemple Complet de Traitement

**Prompt utilisateur:** "Je veux ajouter un bouton pour exporter la vue actuelle en PNG"

### 1. Comprehension
- **Intention:** Feature d'export image
- **Domaine:** Frontend (UI) + possiblement Backend (generation)
- **Scope:** Dans le PoC? Oui, visualisation basique

### 2. Contexte
- Lire LEARNINGS.md → Rien de pertinent
- Lire DECISIONS.md → ADR sur Canvas vs SVG?
- OpenSeadragon doc → `viewer.drawer.canvas.toDataURL()`

### 3. Mobilisation
- **Agent principal:** frontend-tech-lead
- **Skills:** manual-updater (apres validation)
- **Sources:** https://openseadragon.github.io/examples/viewport-screenshot/

### 4. Planification
1. Ajouter bouton dans ViewerPanel
2. Implementer capture via Canvas API
3. Declencher telechargement
4. Tester avec differentes tailles
5. Documenter dans manuel

### 5. Validation Admin
```
## Validation Requise

**Action proposee:** Ajouter bouton export PNG

**Justification:**
- Fonctionnalite demandee
- OpenSeadragon supporte nativement via Canvas

**Risques identifies:**
- Performance si slide tres grande (mitigable avec limite)
- CORS si tiles externes (pas notre cas)

**Fichiers impactes:**
- `frontend/src/components/ViewerPanel.js` - ajout bouton
- `frontend/src/style.css` - style bouton
- `docs/Manuel/05-VISUALISATION_LAMES.md` - documentation

**Voulez-vous proceder?**
```

### 6. Execution
[Implementation apres OK admin]

### 7. Capitalisation
- LEARNINGS.md: "Export PNG via canvas.toDataURL() fonctionne bien"
- Commit: "feat(viewer): add PNG export button"

---

## Organisation GitHub Project

### URL du Projet
**VarunaPoC Development Board:** https://github.com/users/Yanstart/projects/6

### Structure des Issues

**Format ID Issue:** `[Phase]-[Categorie][Numero]`

| Prefixe | Signification |
|---------|---------------|
| P1, P2... | Phase du projet |
| S | Security |
| T | Test |
| R | Reader (architecture multi-reader) |
| A | Annotations |
| Q | Quality (metriques qualite) |
| C | Collaboration |
| V | Viewer (3D, etc.) |
| SF | Slideflow compatibility |
| RS | Radical Simplicity |
| M | MLOps |
| D | Documentation |
| N | N-Dimensionnel (OME) |
| O | OME standards |
| F | Foundation models |
| P | Performance/Production |
| K | Kubernetes/Infra |

### Champs Personnalises

| Champ | Options | Usage |
|-------|---------|-------|
| **Phase** | P1-PoC, P2-Multi-Reader, P3-Imagerie, P4-MLOps, P5-Enterprise | Filtrer par phase |
| **Priority** | Critical, High, Medium, Low | Trier par urgence |
| **Type** | Feature, Security, Test, Docs, Bug | Categoriser |
| **Angle Mort** | Quality-First, Collaboration, Radical Simplicity, MLOps, None | Avantages competitifs |

### Labels Disponibles

```
phase:1, phase:2, phase:3, phase:4, phase:5
priority:critical, priority:high, priority:medium, priority:low
type:feature, type:security, type:test, type:docs, type:bug
angle-mort (indicateur generique)
```

### Association Commits <-> Issues

**Format de Commit avec Reference:**
```bash
git commit -m "type(scope): description

Implements #123
Refs #45, #67"
```

**Mots-cles de fermeture automatique:**
- `Closes #123` - Ferme l'issue quand merge dans main
- `Fixes #123` - Idem, pour bug fixes
- `Resolves #123` - Idem
- `Refs #123` - Reference sans fermer

**Exemple:**
```bash
git commit -m "feat(reader): implement ISlideReader interface

- Define abstract base class with score() method
- Add ReaderCapability enum
- Create ReaderMetadata dataclass

Implements #[P2-R01]
Refs #[P2-R02], #[P2-R03]"
```

### Association PR <-> Issues

**Dans le corps de la PR:**
```markdown
## Summary
- Implement reader abstraction layer
- Add scoring system for format compatibility

## Related Issues
- Closes #[P2-R01] - Interface ISlideReader
- Refs #[P2-R02] - ReaderCapability (partial)

## Test Plan
- [ ] Unit tests for ISlideReader
- [ ] Integration test with OpenSlide
```

### Workflow Recommande

1. **Avant de coder:**
   - Identifier l'issue correspondante sur le Project Board
   - Verifier ses dependances (blockedBy)
   - Deplacer en "In Progress"

2. **Pendant le developpement:**
   - Commits atomiques referençant l'issue
   - Mettre a jour ROADMAP.md si progression significative

3. **A la completion:**
   - Creer PR avec "Closes #NNN"
   - Merge ferme automatiquement l'issue
   - Mettre a jour ROADMAP.md avec [x] statut

### Statistiques Projet (2026-02-04)

| Metrique | Valeur |
|----------|--------|
| Total Issues | 49 |
| Phase 1 | 13 issues |
| Phase 2 | 24 issues |
| Phase 3 | 5 issues |
| Phase 4 | 5 issues |
| Phase 5 | 4 issues |
| Critical Priority | 2 issues |
| High Priority | 25 issues |
| Angles Morts | 11 issues |

---

**Ce document est la LOI pour toute interaction Claude Code sur VarunaPoC.**
