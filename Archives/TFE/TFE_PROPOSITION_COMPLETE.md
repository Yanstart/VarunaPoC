# PROPOSITION DE TRAVAIL DE FIN D'ÉTUDES (TFE)

**Date de soumission :** Décembre 2025
**Institution :** [Votre établissement d'enseignement supérieur]
**Filière :** [Informatique / Ingénierie biomédicale / etc.]

---

## SUJET (TITRE) DU TFE

### Titre principal

**"Conception d'une plateforme web de microscopie virtuelle pour répondre aux défis organisationnels de l'anatomie pathologique : étude de cas au CHU UCL Namur"**

### Sous-titre

*De la dépendance fournisseur à l'interopérabilité : développement et évaluation d'une solution vendor-neutral basée sur des standards ouverts*

---

## NOM(S), PRÉNOM(S) DES ÉTUDIANTS

1. **Noël Junior Yando Fotso**
2. **Mohamed Abdullahi Ayan**

---

## MOTIFS OU RAISONS POUR LESQUELS VOUS AVEZ CHOISI CE SUJET

### 1. Réponse à une problématique RH critique dans le secteur médical

Le laboratoire d'anatomie pathologique du CHU UCL Namur fait face à une **pénurie structurelle d'anatomopathologistes**, phénomène documenté à l'échelle nationale et européenne. Cette situation entraîne :

- Des **difficultés de recrutement** persistantes
- Une **surcharge de travail** pour les équipes en place
- L'**impossibilité d'assurer la continuité des soins** sans solutions innovantes

La pathologie numérique ouvre la voie au **télétravail réellement opérationnel**, devenant un argument d'attractivité pour les recrutements. Selon le rapport de projet institutionnel (De Nizza, 2022), "offrir du télétravail réellement opérationnel dans le package favorisera l'attractivité" du laboratoire.

### 2. Des analyses chronophages impactant la qualité diagnostique

Certaines analyses essentielles au diagnostic sont extrêmement consommatrices de temps :

- **Exemple concret** : L'évaluation de la prolifération tumorale sur base d'images Ki-67 nécessite de compter manuellement environ 1000 cellules et de calculer un ratio
- Ces analyses manuelles mobilisent la concentration des pathologistes pendant de nombreuses heures
- Elles introduisent une **variabilité intra-observateur** (un même pathologiste peut donner des résultats différents à différents moments) et **inter-observateur** (différents pathologistes peuvent diverger sur le même échantillon)

Les outils de quantification sur lames virtuelles permettront d'améliorer la reproductibilité et la qualité du diagnostic.

### 3. Des collaborations actuellement impossibles

Le laboratoire n'est pas équipé pour faire de la pathologie digitale, ce qui constitue un **frein majeur** pour :

- Les **collaborations avec des experts externes** (second avis, télé-expertise)
- Les **collaborations inter-sites au sein du CHU** (Godinne, Dinant, Mont-Godinne, Sainte-Élisabeth)
- L'**activité académique et de recherche** avec d'autres acteurs universitaires
- Les projets d'**innovation et de R&D**

### 4. Une solution actuelle inadaptée aux besoins

La solution actuellement en place présente des limitations significatives :

| Aspect | Situation actuelle | Problème |
|--------|-------------------|----------|
| **Type** | Client lourd 3DHistech (CaseViewer) | Installation requise sur chaque poste |
| **Accessibilité** | Locale uniquement | Pas de télétravail, pas de collaboration distante |
| **Format** | Mirax (MRXS) propriétaire | Vendor lock-in, dépendance fournisseur |
| **Intégration** | Limitée au scope LIS | Pas de lien fluide avec le PACS Telemis |
| **Maintenance** | Difficile | Mises à jour complexes, support limité |

Le marché des solutions WSI (Whole Slide Imaging) propose majoritairement des **écosystèmes fermés** : les scanners produisent des formats propriétaires (MRXS, NDPI, SVS, BIF), les plateformes sont verrouillées, et la migration d'un fournisseur à l'autre est coûteuse et risquée.

### 5. Alignement avec la stratégie institutionnelle

Notre projet répond directement aux orientations stratégiques du CHU UCL Namur :

- **Recommandations ACI** : La pathologie digitale est qualifiée de "Challenge" à adresser dans l'audit de certification institutionnelle
- **Feuille de route 2022-2028** : Transition progressive vers un laboratoire fonctionnant entièrement en mode "pathologie digitale"
- **Positionnement concurrentiel** : Les laboratoires qui n'embrassent pas cette transition auront des difficultés face à la concurrence en matière de volume d'activité, qualité diagnostique, innovation et formation

### 6. Une problématique de recherche pertinente et actuelle

Selon Williams et al. (2023), **60% des échecs de déploiement en pathologie numérique sont dus à des facteurs humains et organisationnels** plutôt qu'à des limitations techniques. Cette statistique souligne l'importance d'une approche centrée utilisateur et d'une évaluation rigoureuse de l'acceptabilité.

Notre recherche interroge : **Une solution open source basée sur des standards ouverts (DICOM WSI, OpenSlide) peut-elle offrir une alternative viable aux solutions commerciales tout en garantissant performance, simplicité d'usage et intégration aux systèmes existants ?**

### 7. Motivations personnelles des étudiants

- **Junior Noël Yando Fotso** : Passionné par l'architecture logicielle et le développement full-stack, je souhaite appliquer mes compétences techniques à un domaine à fort impact sociétal. La conception d'une solution pour l'imagerie médicale représente un défi technique stimulant (images gigapixels, streaming de tuiles, performance temps réel) dans un contexte où la qualité du code peut directement influencer la qualité des soins.

- **Mohamed Abdullahi Ayan** : Intéressé par l'interaction homme-machine et les facteurs humains dans l'adoption technologique, je vois dans ce projet l'opportunité d'étudier comment la conception centrée utilisateur peut faciliter une transition numérique dans un environnement médical traditionnel. L'évaluation de l'utilisabilité et de l'acceptabilité constitue le cœur de ma contribution.

---

## PRINCIPAUX OBJECTIFS POURSUIVIS ET RÉALISATIONS PLANIFIÉES

### Objectif principal

**Concevoir, développer et évaluer un prototype de visionneuse web de lames histologiques (Whole Slide Imaging) répondant aux critères de performance, d'interopérabilité et de simplicité d'usage, tout en s'intégrant à l'écosystème informatique hospitalier du CHU UCL Namur.**

### Objectifs spécifiques

| # | Objectif | Description | Lien avec besoins terrain |
|---|----------|-------------|---------------------------|
| **O1** | Développer un viewer web accessible universellement | Solution fonctionnant depuis n'importe quel poste (interne CHU, VPN externe, mobile) sans installation | Télétravail, collaborations distantes |
| **O2** | Assurer le support multi-formats vendor-neutral | Prise en charge des formats MRXS (3DHistech), BIF et TIF (Roche/Ventana) via OpenSlide | Indépendance fournisseur, pérennité |
| **O3** | Concevoir une architecture intégrable au PACS | Mode "command plugin" compatible Telemis avec contexte patient automatique | Flux clinique, lien dossier patient |
| **O4** | Évaluer les performances sur lames réelles | Tests avec lames du laboratoire (250 MB à plusieurs GB) sur infrastructure réseau CHU | Validation conditions réelles |
| **O5** | Mesurer l'acceptabilité utilisateur | Évaluation de la simplicité, du gain de temps perçu, de l'intention d'adoption | Résistance au changement, formation |
| **O6** | Documenter les fondations pour l'évolution future | Spécifications pour l'ajout ultérieur d'outils IA (comptage Ki-67, détection, etc.) | R&D, aide au diagnostic |

### Réalisations planifiées

#### Livrables de recherche

| Livrable | Description | Responsable principal |
|----------|-------------|----------------------|
| **L1 - Revue de littérature** | Synthèse structurée sur la pathologie numérique, les formats WSI, les facteurs d'adoption et les solutions existantes | Junior + Mohamed |
| **L2 - Analyse des besoins** | Rapport d'observation terrain, personas utilisateurs, cartographie des workflows (clinique + recherche) | Mohamed |
| **L3 - Benchmark comparatif** | Grille d'évaluation multicritères de 8-10 solutions (open source et commerciales) | Mohamed |
| **L4 - Rapport d'évaluation technique** | Métriques de performance, résultats tests de charge, analyse des goulets d'étranglement | Junior |
| **L5 - Rapport d'évaluation utilisateur** | Résultats questionnaires SUS/TAM, analyse thématique des entretiens, recommandations UX | Mohamed |
| **L6 - Mémoire final** | Document de synthèse intégrant contexte, méthodologie, résultats, discussion et recommandations | Junior + Mohamed |

#### Livrables techniques

| Livrable | Description | Responsable principal |
|----------|-------------|----------------------|
| **T1 - Backend VarunaPoC** | API REST FastAPI avec endpoints de navigation, métadonnées et streaming de tuiles | Junior |
| **T2 - Frontend VarunaPoC** | Interface web Vite + OpenSeadragon avec navigation fluide et minimap | Junior |
| **T3 - Module multi-formats** | Support MRXS, BIF, TIF via OpenSlide avec gestion des fichiers compagnons | Junior |
| **T4 - Module intégration PACS** | Prototype d'intégration mode command plugin Telemis | Junior + Mohamed |
| **T5 - Documentation technique** | README, guide de déploiement, documentation API (OpenAPI/Swagger) | Junior |
| **T6 - Guide utilisateur** | Manuel d'utilisation destiné aux pathologistes et techniciens | Mohamed |

### Questions de recherche

Notre TFE cherche à répondre aux questions suivantes :

**QR1 - Performance technique**
> Quelles performances (temps de chargement, latence de navigation, fluidité) une solution basée sur OpenSlide et OpenSeadragon peut-elle atteindre avec des lames histologiques de plusieurs gigaoctets sur l'infrastructure réseau du CHU UCL Namur ?

**QR2 - Intégration système**
> Quels sont les défis techniques et organisationnels pour intégrer un viewer web vendor-neutral au workflow existant impliquant le PACS Telemis et le LIS Diamic ?

**QR3 - Acceptabilité utilisateur** ayan
> Quels facteurs influencent l'acceptation d'une solution web de microscopie virtuelle par les pathologistes habitués au microscope optique et au client lourd 3DHistech ?

**QR4 - Prospective architecturale**
> Quelles fondations architecturales doivent être posées dès la phase PoC pour permettre l'ajout futur d'outils d'aide au diagnostic (comptage cellulaire automatisé, algorithmes IA) ?

### Inscription dans la feuille de route institutionnelle

Notre TFE s'inscrit dans la trajectoire de transformation numérique définie par le CHU UCL Namur :

```
PLANNING INSTITUTIONNEL              CONTRIBUTION DU TFE
════════════════════════════════════════════════════════════════════

2022 ─ Accès pathologie digitale     Fondations posées :
       Scanner DESKII installé       - Scanner mono-lame opérationnel
       Format Mirax (MRXS)           - Lames numérisées disponibles

2023 ─ POC Dinant                    VarunaPoC :
       Navigation mobile             - Viewer web prototype
       R&D aide au diagnostic        - Tests multi-formats
                                     - Évaluation initiale

2024 ─ Collaborations renforcées     Résultats du TFE :
       Outils aide au diagnostic     - Recommandations déploiement
                                     - Roadmap technique documentée
                                     - Métriques de référence

2025+ ─ Laboratoire full digital     Fondations établies :
        Investissement scanner       - Architecture scalable
        IA en production             - Intégration PACS validée
                                     - Prérequis IA documentés
```

---

## MÉTHODES DE TRAVAIL UTILISÉES

### Approche méthodologique globale : Design Science Research (DSR)

Notre TFE adopte une méthodologie **Design Science Research** (Hevner et al., 2004), particulièrement adaptée aux projets de conception et d'évaluation d'artefacts technologiques. Cette approche combine :

- La **construction** d'un artefact innovant (le prototype VarunaPoC)
- L'**évaluation rigoureuse** de cet artefact selon des critères définis
- La **contribution aux connaissances** par la formalisation des apprentissages

#### Cycle DSR en trois phases

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │  1. PERTINENCE  │───▶│  2. CONCEPTION  │───▶│   3. RIGUEUR    │  │
│  │                 │    │                 │    │                 │  │
│  │ • Analyse       │    │ • Développement │    │ • Évaluation    │  │
│  │   besoins       │    │   itératif      │    │   quantitative  │  │
│  │ • Revue         │    │ • Tests         │    │ • Évaluation    │  │
│  │   littérature   │    │   continus      │    │   qualitative   │  │
│  │ • Benchmark     │    │ • Feedback      │    │ • Triangulation │  │
│  │                 │    │   utilisateurs  │    │                 │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│          │                      │                      │            │
│          ▼                      ▼                      ▼            │
│    Sem. 1-4               Sem. 5-12              Sem. 13-16         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### Phase 1 : Pertinence (Semaines 1-4)

**Objectif** : Comprendre le contexte, identifier les besoins réels et établir l'état de l'art.

#### 1.1 Observation ethnographique du terrain

| Activité | Méthode | Participants | Responsable |
|----------|---------|--------------|-------------|
| Shadowing | Observation non-participante de 2-3 pathologistes pendant leurs analyses quotidiennes (2-3 demi-journées) | Pathologistes volontaires | Junior |
| Analyse documentaire | Étude des procédures existantes, workflow LIS/PACS, documentation technique | Documents internes CHU | Junior |
| Cartographie processus | Modélisation BPMN des flux clinique et recherche | Équipe anapath + IT | Mohamed |

**Outils** : Grille d'observation structurée, journal de bord, schémas BPMN

#### 1.2 Entretiens exploratoires

| Type | Nombre | Profil | Thèmes abordés | Responsable |
|------|--------|--------|----------------|-------------|
| Semi-directif | 2-3 | Pathologistes seniors | Pratiques actuelles, irritants, attentes | Mohamed |
| Semi-directif | 1-2 | Techniciens de laboratoire | Workflow numérisation, gestion lames | Mohamed |
| Directif | 1 | Équipe IT / Biomédical | Contraintes techniques, intégration PACS | Junior |
| Directif | 1 | Contact Telemis (si possible) | Spécifications command plugin | Junior |

**Outils** : Guide d'entretien, enregistrement audio (avec consentement), retranscription

#### 1.3 Revue de littérature

| Axe | Sources | Mots-clés | Responsable |
|-----|---------|-----------|-------------|
| Pathologie numérique | PubMed, Google Scholar | "digital pathology", "whole slide imaging", "WSI adoption" | Junior + Mohamed |
| Formats et standards | Documentation technique, DICOM, OpenSlide | "DICOM WSI", "Supplement 145", "pyramidal image" | Junior |
| Facteurs d'adoption | ACM, IEEE, JAMIA | "technology acceptance", "user adoption", "healthcare IT" | Mohamed |
| Solutions existantes | Documentation produits, GitHub, publications | "QuPath", "ASAP", "OpenSlide", "Orthanc WSI" | Mohamed |

**Critères d'inclusion** : Publications 2018-2025, contexte hospitalier comparable, langue anglaise ou française

**Livrables Phase 1** :
- Synthèse des besoins utilisateurs (personas, user stories prioritaires)
- Cartographie des workflows actuels (clinique + recherche)
- Tableau comparatif de 8-10 solutions existantes
- Cadre conceptuel de la recherche

---

### Phase 2 : Conception et développement (Semaines 5-12)

**Objectif** : Développer le prototype VarunaPoC de manière itérative avec feedback continu.

#### 2.1 Méthodologie de développement : Scrum adapté

| Élément | Configuration |
|---------|---------------|
| **Durée des sprints** | 1 semaine |
| **Cérémonies** | Planning (lundi), Daily standup (async via Discord), Review + Rétro (vendredi) |
| **Backlog** | User stories priorisées issues de la Phase 1 |
| **Definition of Done** | Code fonctionnel + testé + documenté + déployable |
| **Outils** | GitHub Projects (Kanban), GitHub Issues, Pull Requests |

#### 2.2 Planning des sprints

| Sprint | Semaine | Focus | Livrables | Junior | Mohamed |
|--------|---------|-------|-----------|--------|---------|
| **1** | 5 | Setup projet | Environnement dev, structure repo, CI/CD basique | 80% | 20% |
| **2** | 6 | Backend core | API FastAPI, endpoints /info, /health | 80% | 20% |
| **3** | 7 | OpenSlide integration | Lecture MRXS, extraction tuiles | 90% | 10% |
| **4** | 8 | Frontend viewer | OpenSeadragon, navigation de base | 70% | 30% |
| **5** | 9 | Multi-formats | Support BIF, TIF, gestion erreurs | 80% | 20% |
| **6** | 10 | Navigation avancée | Minimap, breadcrumb, explorateur fichiers | 60% | 40% |
| **7** | 11 | Intégration PACS | Prototype command plugin Telemis | 70% | 30% |
| **8** | 12 | Stabilisation | Bug fixes, optimisation, documentation | 50% | 50% |

#### 2.3 Stack technologique

**Backend :**
- Python 3.11+
- FastAPI (framework web async)
- OpenSlide (lecture formats WSI)
- Pillow, NumPy (traitement images)
- Uvicorn (serveur ASGI)

**Frontend :**
- Vite (bundler)
- Vanilla JavaScript (ES6+)
- OpenSeadragon (viewer zoomable)
- CSS3 (styling minimal)

**Infrastructure :**
- Git/GitHub (versioning, collaboration)
- Docker (containerisation pour déploiement)
- GitHub Actions (CI/CD)

#### 2.4 Tests continus

| Type de test | Outil | Fréquence | Responsable |
|--------------|-------|-----------|-------------|
| Tests unitaires backend | pytest | À chaque commit | Junior |
| Tests d'intégration API | pytest + httpx | À chaque PR | Junior |
| Tests fonctionnels frontend | Manuel + Playwright (si temps) | Fin de sprint | Mohamed |
| Tests utilisateurs | Sessions avec 1-2 pathologistes | Sprints 4, 6, 8 | Mohamed |

**Livrables Phase 2** :
- Prototype VarunaPoC fonctionnel
- Documentation technique (README, API docs)
- Historique des sprints et décisions d'architecture

---

### Phase 3 : Évaluation rigoureuse (Semaines 13-16)

**Objectif** : Évaluer l'artefact selon des critères quantitatifs (performance) et qualitatifs (utilisabilité).

#### 3.1 Évaluation quantitative : Performance technique

##### Protocole de mesure

| Métrique | Objectif cible | Méthode de mesure | Outil |
|----------|----------------|-------------------|-------|
| **Temps de chargement initial** | < 2 sec (lame 5 Go) | Chronométrage du first contentful paint | Chrome DevTools, scripts automatisés |
| **Latence navigation** | < 100 ms (zoom/pan) | Mesure temps de réponse API + rendu | Performance API JavaScript |
| **Fluidité** | > 30 fps | Monitoring frame rate pendant navigation | Chrome DevTools Performance |
| **Consommation mémoire** | < 500 Mo navigateur | Mesure heap size | Chrome Task Manager |
| **Temps de réponse API** | < 200 ms (tuile 256x256) | Logs serveur | FastAPI middleware |

##### Protocole de test de charge

```
Configuration des tests :
─────────────────────────────────────────────────────────
• Utilisateurs simulés simultanés : 5, 10, 15
• Lames ouvertes en parallèle : 10, 25, 50
• Durée de chaque test : 5 minutes
• Scénarios : navigation libre, zoom rapide, pan continu
─────────────────────────────────────────────────────────

Environnements testés :
─────────────────────────────────────────────────────────
1. Local (même machine) → baseline
2. Réseau LAN CHU → conditions réelles internes
3. VPN externe → conditions télétravail
─────────────────────────────────────────────────────────
```

##### Échantillon de lames pour les tests

| Format | Nombre | Taille typique | Source |
|--------|--------|----------------|--------|
| MRXS (3DHistech) | 3-5 | 500 MB - 5 GB | Scanner DESKII Godinne |
| BIF (Ventana) | 2-3 | 200 MB - 2 GB | Si disponible |
| TIF (Generic) | 2-3 | 100 MB - 1 GB | Si disponible |

**Responsable** : Junior
**Livrable** : Rapport de performance avec graphiques et analyse des goulets d'étranglement

#### 3.2 Évaluation qualitative : Utilisabilité et acceptabilité

##### Instruments d'évaluation

| Instrument | Description | Quand | Participants |
|------------|-------------|-------|--------------|
| **SUS** (System Usability Scale) | Questionnaire standardisé 10 items, score 0-100 | Après test utilisateur | 5-8 pathologistes |
| **TAM** (Technology Acceptance Model) | Échelles utilité perçue + facilité d'usage perçue | Après test utilisateur | 5-8 pathologistes |
| **Questionnaire ad hoc** | Questions spécifiques au contexte (comparaison microscope, 3DHistech) | Après test utilisateur | 5-8 pathologistes |
| **Entretiens semi-directifs** | Exploration approfondie des perceptions, suggestions | Post-questionnaire | 3-5 volontaires |
| **Think-aloud** | Verbalisation pendant l'utilisation | Pendant test | 2-3 participants |

##### Protocole de test utilisateur

```
Durée totale : ~45 minutes par participant

1. Accueil et consentement (5 min)
   • Présentation du projet
   • Signature formulaire de consentement
   • Rappel : on teste le système, pas l'utilisateur

2. Démonstration rapide (5 min)
   • Présentation des fonctionnalités de base
   • Réponses aux questions

3. Scénarios de test (20 min)
   Scénario A : Ouvrir une lame MRXS et naviguer vers une zone d'intérêt
   Scénario B : Comparer deux régions de la même lame (zoom différent)
   Scénario C : Utiliser la minimap pour se repérer
   Scénario D : Accéder à une lame depuis le contexte PACS (si implémenté)

4. Questionnaires (10 min)
   • SUS (10 questions)
   • TAM adapté (12 questions)
   • Questions ouvertes

5. Entretien de débriefing (5 min) - optionnel
   • Points forts / points faibles perçus
   • Comparaison avec outils actuels
   • Suggestions d'amélioration
```

##### Critères de succès

| Critère | Seuil de succès | Interprétation |
|---------|-----------------|----------------|
| Score SUS | > 68 | "Above average" (Bangor et al., 2009) |
| Score SUS | > 80 | "Excellent" |
| Utilité perçue (TAM) | > 5/7 | Perception positive |
| Facilité d'usage perçue (TAM) | > 5/7 | Perception positive |
| Intention d'usage | > 5/7 | Adoption probable |
| Temps de prise en main | < 5 min | Objectif "Radical Simplicity" |

**Responsable** : Mohamed
**Livrable** : Rapport d'évaluation utilisateur avec verbatims et recommandations

#### 3.3 Analyse des données

##### Données quantitatives (performance)

- Statistiques descriptives (moyenne, médiane, écart-type, percentiles)
- Visualisations : graphiques de latence, boxplots comparatifs, courbes de charge
- Analyse des corrélations (taille lame vs temps de chargement, etc.)
- Identification des seuils critiques

##### Données quantitatives (questionnaires)

- Calcul des scores SUS et TAM selon formules standardisées
- Tests de normalité (Shapiro-Wilk)
- Statistiques descriptives par dimension
- Corrélations entre dimensions (utilité vs facilité vs intention)

##### Données qualitatives (entretiens, think-aloud)

- Retranscription intégrale des enregistrements
- Analyse thématique selon Braun & Clarke (2006) :
  1. Familiarisation avec les données
  2. Génération des codes initiaux
  3. Recherche de thèmes
  4. Révision des thèmes
  5. Définition et nomination des thèmes
  6. Rédaction du rapport
- Codage avec logiciel (NVivo ou équivalent gratuit)
- Triangulation avec données quantitatives

---

### Répartition du travail entre les étudiants

#### Vue d'ensemble

| Dimension | Junior Noël Yando Fotso | Mohamed Abdullahi Ayan |
|-----------|-------------------------|------------------------|
| **Rôle principal** | Tech Lead / Développeur principal | UX Researcher / Évaluateur |
| **Développement** | 75% | 25% |
| **Recherche terrain** | 30% | 70% |
| **Évaluation** | 40% (technique) | 60% (utilisateur) |
| **Rédaction mémoire** | 50% | 50% |

#### Détail par livrable

| Livrable | Junior | Mohamed | Coordination |
|----------|--------|---------|--------------|
| Revue de littérature (technique) | Principal | Support | Junior |
| Revue de littérature (UX/adoption) | Support | Principal | Mohamed |
| Observation terrain | Réalisation | Analyse | Mohamed |
| Entretiens exploratoires | Participation | Réalisation + Analyse | Mohamed |
| Benchmark solutions | Support | Principal | Mohamed |
| Backend VarunaPoC | Principal | Tests | Junior |
| Frontend VarunaPoC | Principal | UI/UX review | Junior |
| Intégration PACS | Principal | Validation workflow | Junior |
| Tests de performance | Principal | Support | Junior |
| Tests utilisateurs | Observation | Réalisation + Analyse | Mohamed |
| Questionnaires SUS/TAM | Support | Principal | Mohamed |
| Documentation technique | Principal | Relecture | Junior |
| Guide utilisateur | Support | Principal | Mohamed |
| Chapitre Contexte (mémoire) | Co-rédaction | Co-rédaction | Partagé |
| Chapitre Méthodologie | Support | Principal | Mohamed |
| Chapitre Implémentation | Principal | Support | Junior |
| Chapitre Résultats | 50% (perf) | 50% (UX) | Partagé |
| Chapitre Discussion | Co-rédaction | Co-rédaction | Partagé |

#### Outils de collaboration

| Outil | Usage |
|-------|-------|
| **GitHub** | Code, issues, pull requests, project board |
| **Discord/Teams** | Communication quotidienne, daily standups |
| **Google Docs** | Rédaction collaborative du mémoire |
| **Zotero** | Gestion bibliographique partagée |
| **Figma** | Maquettes UI (si nécessaire) |

---

### Considérations éthiques

| Aspect | Mesure |
|--------|--------|
| **Consentement** | Formulaire signé pour tous les participants (entretiens, tests) |
| **Anonymisation** | Aucun nom dans les données, codes d'identification |
| **Données patients** | Aucune donnée patient réelle utilisée (lames de test uniquement) |
| **RGPD** | Pas de stockage de données personnelles, suppression après analyse |
| **Enregistrements** | Audio uniquement avec consentement, suppression après retranscription |
| **Droit de retrait** | Participants informés qu'ils peuvent se retirer à tout moment |

---

### Calendrier synthétique

```
SEMAINE   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18
          │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
PHASE 1   ████████████████
Pertinence│ Obs │ Entretiens │ Revue litt │ Benchmark │
          │     │            │            │           │
PHASE 2                       ████████████████████████████████
Conception                    │S1 │S2 │S3 │S4 │S5 │S6 │S7 │S8 │
                              │   │   │   │   │   │   │   │   │
PHASE 3                                                       ████████████████
Évaluation                                                    │Perf│ UX │Anal│
                                                              │    │    │    │
RÉDACTION                                     ░░░░░░░░░░░░░░░░████████████████
                                              │ Ébauches      │ Rédaction finale│
                                                                               │
SOUTENANCE                                                                 ████│
                                                                               │
─────────────────────────────────────────────────────────────────────────────────
Légende : ████ Activité principale   ░░░░ Activité secondaire
```

---

### Risques et mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Accès limité aux pathologistes** | Moyenne | Élevé | Planifier entretiens tôt, prévoir alternatives (techniciens) |
| **Lames de test indisponibles** | Faible | Élevé | Identifier lames de démonstration OpenSlide, contacter labo tôt |
| **Problèmes intégration PACS** | Moyenne | Moyen | Prévoir mode standalone comme fallback, documenter contraintes |
| **Retards de développement** | Moyenne | Moyen | Priorisation MoSCoW, réduction scope si nécessaire |
| **Résultats évaluation négatifs** | Faible | Faible | Opportunité d'apprentissage, recommandations d'amélioration |

---

## CONTRIBUTION SCIENTIFIQUE ET PRATIQUE ATTENDUE

### Contribution scientifique

1. **Validation empirique** de la faisabilité d'une approche vendor-neutral basée sur OpenSlide/OpenSeadragon dans un contexte hospitalier belge francophone

2. **Identification des facteurs clés d'adoption** des solutions de microscopie virtuelle par les pathologistes, enrichissant la littérature sur l'acceptation technologique en santé

3. **Métriques de référence** pour les performances attendues d'un viewer WSI web (temps de chargement, latence, selon taille de lame et conditions réseau)

4. **Recommandations méthodologiques** pour l'évaluation de solutions de pathologie numérique (protocoles, instruments adaptés)

### Contribution pratique

1. **Artefact réutilisable** : Le prototype VarunaPoC, open source, pourra servir de base à d'autres institutions ou être étendu par le CHU

2. **Roadmap technique** : Documentation des prérequis pour les phases futures (annotations, IA, collaboration temps réel)

3. **Retour d'expérience** : Analyse des difficultés rencontrées et solutions trouvées, utile pour d'autres projets similaires

4. **Renforcement des compétences locales** : Transfert de connaissances vers l'équipe IT du CHU

---

## RÉFÉRENCES BIBLIOGRAPHIQUES INITIALES

### Méthodologie
- Hevner, A. R., et al. (2004). Design Science in Information Systems Research. *MIS Quarterly*, 28(1), 75-105.
- Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. *Qualitative Research in Psychology*, 3(2), 77-101.
- Bangor, A., Kortum, P., & Miller, J. (2009). Determining what individual SUS scores mean. *Journal of Usability Studies*, 4(3), 114-123.

### Pathologie numérique
- Williams, B. J., & Treanor, D. (2023). Practical guide to training and validation for primary diagnosis with whole slide imaging. *Journal of Clinical Pathology*, 76(12), 803-808.
- Stathonikos, N., et al. (2023). Being fully digital: perspective of a Dutch academic pathology laboratory. *Histopathology*, 82(1), 157-165.
- Pantanowitz, L., et al. (2024). Accuracy of quality assurance in digital pathology. *Journal of Pathology Informatics*, 15, 100347.

### Standards et technologies
- DICOM Supplement 145 – Whole Slide Imaging. NEMA.
- OpenSlide documentation. https://openslide.org/
- OpenSeadragon documentation. https://openseadragon.github.io/

### Guides de déploiement
- The Leeds Guide to Digital Pathology. Leica Biosystems.
- Task force Anatomopathologie numérique – France Biotech (2024).

---

## SIGNATURES

**Étudiant 1 :**
Nom : Noël Junior Yando Fotso
Date :
Signature :

**Étudiant 2 :**
Nom : Mohamed Abdullahi Ayan
Date :
Signature :

**Promoteur/Superviseur :**
Nom :
Date :
Signature :

---

*Document généré le 16 décembre 2025*
*Version 1.0*
