# Cerveau d'Orchestration VarunaPoC

**Version:** 2.1
**Date:** 2026-02-08

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
[7. CAPITALISATION] ---> Mettre a jour le cerveau (OBLIGATOIRE)
       |                  - Evaluer ce qui a change (matrice ci-dessous)
       |                  - Mettre a jour les fichiers memoire concernes
       |                  - Propager aux fichiers satellites si necessaire
       |
       v
[8. PROPAGATION] ------> Verifier coherence satellites
                         - Executer la matrice de propagation
                         - Corriger toute incoherence detectee
                         - S'assurer que le cerveau reste une source de verite
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
| pattern, factory, strategy, modulaire | lead-architecte | - | refactoring.guru, GOF |
| annotation, dessin, label, svg | frontend-tech-lead | - | MDN SVG docs |
| detection, heatmap, inference, phikon | ml-architect | - | slideflow.dev |
| comptage, stats, classification | backend-tech-lead | - | - |

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
- Plan MVP 15 semaines (Phases 1-4 + Post-MVP circles)
- Avancement par phase (Phase 1-2: 100%, Phase 3-4: A venir)
- Metriques de suivi
- Delivrables par phase

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

## Capitalisation & Propagation (Etapes 7-8) - OBLIGATOIRE

### Principe

A la fin de **chaque tache** (pas seulement en fin de session), Claude DOIT:
1. Identifier ce qui a change
2. Mettre a jour les fichiers memoire concernes
3. Verifier si des fichiers satellites doivent etre propages

### Carte des Fichiers du Cerveau

```
BRAIN.md (orchestration - rarement modifie)
│
├── memory/ (ETAT & APPRENTISSAGES)
│   ├── PROJECT_STATE.md   ← Snapshot: version, features, sante
│   ├── ROADMAP.md         ← Plan: phases, avancement, timeline
│   ├── LEARNINGS.md       ← Erreurs: bugs, workarounds, gotchas
│   ├── DECISIONS.md       ← Architecture: ADRs, choix techniques
│   ├── SOURCES.md         ← References: docs officielles, outils
│   └── README.md          ← Index de la memoire
│
├── docs/ (REFERENCE TECHNIQUE)
│   ├── CONTEXT.md         ← Resume rapide pour reprendre le travail
│   ├── FILES.md           ← Arborescence fichiers du projet
│   ├── README.md          ← Vue d'ensemble architecture
│   └── QUICK_START.md     ← Guide demarrage rapide
│
└── Fichiers racine projet
    └── README.md          ← Description publique du projet
```

### Matrice de Propagation

**Apres chaque tache, evaluer CHAQUE ligne de cette matrice:**

| Ce qui a change | Fichiers a mettre a jour | Priorite |
|-----------------|--------------------------|----------|
| **Bug corrige avec workaround** | `LEARNINGS.md` (nouvelle entree) | HAUTE |
| **Decision architecturale** | `DECISIONS.md` (nouvel ADR) | HAUTE |
| **Nouveau fichier cree** | `docs/FILES.md` (ajouter dans l'arbre) | HAUTE |
| **Feature implementee** | `PROJECT_STATE.md` (ajouter dans "Ce qui fonctionne") | HAUTE |
| **Phase avancee/completee** | `ROADMAP.md` (MAJ avancement), `PROJECT_STATE.md` | HAUTE |
| **Nouvelle dependance/outil** | `SOURCES.md` (ajouter reference) | MOYENNE |
| **Version bump** | `PROJECT_STATE.md`, `CONTEXT.md`, `README.md` (racine) | MOYENNE |
| **Nouveau test ajoute** | `PROJECT_STATE.md` (compteur tests) | BASSE |
| **Config modifiee** | `CONTEXT.md` (section "Comment Demarrer") | BASSE |
| **Endpoint API ajoute/modifie** | `docs/FILES.md` (routes), `PROJECT_STATE.md` | MOYENNE |

### Processus de Propagation (Checklist Mentale)

A executer apres chaque tache:

```
1. QUOI a change?
   → Lister les fichiers modifies et la nature du changement

2. MEMOIRE directe (toujours verifier):
   □ Bug/workaround?           → LEARNINGS.md
   □ Decision technique?       → DECISIONS.md
   □ Nouvelle source/outil?    → SOURCES.md

3. ETAT du projet (si feature/fix significatif):
   □ Nouvelle feature?         → PROJECT_STATE.md
   □ Progression phase?        → ROADMAP.md
   □ Nouveau fichier?          → docs/FILES.md

4. CONTEXTE (si changement structurel):
   □ Architecture modifiee?    → docs/CONTEXT.md, docs/README.md
   □ Version changee?          → PROJECT_STATE.md, CONTEXT.md, README.md racine
   □ Stack modifie?            → CONTEXT.md, docs/README.md

5. COHERENCE (verification finale):
   □ Les versions sont-elles alignees partout?
   □ Les compteurs (tests, formats, ADRs) sont-ils corrects?
   □ Pas de reference a des fichiers/agents/features inexistants?
```

### Exemples Concrets

**Exemple 1: Bug fix "tiles lentes"**
```
Changement: Routes async def → def dans slides.py
Propagation:
  ✓ LEARNINGS.md → Nouvelle entree "async def vs def"
  ✓ PROJECT_STATE.md → Performance "Tiles < 15ms" (mise a jour metrique)
  ✗ DECISIONS.md → Oui si c'est un choix architectural → ADR-019
  ✗ FILES.md → Non, pas de nouveau fichier
  ✗ ROADMAP.md → Non, pas de changement de phase
```

**Exemple 2: Feature "annotations CRUD"**
```
Changement: Nouveau module annotations (models, schemas, routes, frontend)
Propagation:
  ✓ PROJECT_STATE.md → Ajouter dans "Ce qui fonctionne"
  ✓ ROADMAP.md → Cocher la tache, MAJ pourcentage phase
  ✓ FILES.md → Ajouter tous les nouveaux fichiers dans l'arbre
  ✓ DECISIONS.md → ADR-016 (PostGIS), ADR-018 (SVG overlay)
  ✓ SOURCES.md → PostGIS, SQLAlchemy, GeoAlchemy2, Alembic, Shapely
  ✓ CONTEXT.md → MAJ "Ce qui fonctionne"
  ✗ LEARNINGS.md → Oui si bugs rencontres (port 5433, ForeignKey, etc.)
```

**Exemple 3: Simple rename/typo fix**
```
Changement: Correction typo dans un commentaire
Propagation:
  ✗ Aucune mise a jour necessaire
  (Les corrections triviales ne polluent pas le cerveau)
```

### Seuil de Declenchement

**NE PAS propager si:**
- Changement purement cosmétique (typo, formatage)
- Exploration/recherche sans modification de code
- Question simple repondue sans implementation

**TOUJOURS propager si:**
- Un fichier de code a ete cree ou significativement modifie
- Un bug non trivial a ete corrige
- Une decision technique a ete prise
- L'etat du projet a change (feature ajoutee, test ajoute, phase avancee)

---

## Checklist Fin de Session

Avant de terminer une session, verifier:

- [ ] Etapes 7-8 (Capitalisation + Propagation) executees pour chaque tache?
- [ ] Toutes les modifications commitees?
- [ ] Aucun fichier temporaire laisse?
- [ ] Aucune modification non testee?
- [ ] Le cerveau est coherent (versions, compteurs, references)?

---

## Quick Reference: Agents et Skills

### Agents (Delegation via Task)

```
chief-architect          → Orchestration generale
backend-tech-lead        → FastAPI, OpenSlide, SQLAlchemy, Python
frontend-tech-lead       → Vite, JS, OpenSeadragon, SVG overlays
performance-engineer     → Coordinates, caching, profiling, tiles
ml-architect             → Slideflow, Phikon-v2, MLOps, detection pipeline
infrastructure-architect → Docker, K8s, CI/CD, GitHub Actions
lead-architecte          → Architecture globale, patterns, design decisions
security-architect       → Auth RBAC, encryption, RGPD compliance
integration-engineer     → DICOM, PACS Telemis, HL7, pynetdicom
```

### Skills (Workflows Automatises)

```
error-documenter     → Documenter erreurs dans docs/ERROR_*.md
manual-updater       → Mettre a jour docs/Manuel/
api-documenter       → Documenter endpoints FastAPI
slide-tester         → Tester tous les 10 formats supportes (94 lames)
coordinate-validator → Valider mapping coordonnees OSD↔OpenSlide
```

---

## Support Decisionnaire

Pour les questions de patterns et d'architecture, utiliser **lead-architecte** (agent existant). Pour les questions algorithmiques/performance, utiliser **performance-engineer**. Ces agents couvrent les cas d'usage precedemment attribues aux specialistes design-patterns et algorithmes (cf. ADR-015).

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

### Etat Projet (2026-02-08)

| Metrique | Valeur |
|----------|--------|
| Version | 1.7.0 |
| Phase | 2 complete, 3 a venir |
| Tests | 94 pass, 3 skip |
| Formats | 10 (94 lames testees) |
| Branche active | feature/slideflow-integration |
| Securite runtime | 0 (pas d'auth) |
| ADRs | 20 |

---

**Ce document est la LOI pour toute interaction Claude Code sur VarunaPoC.**
