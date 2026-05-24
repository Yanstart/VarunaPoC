# Alignement Vision PDF §2 ↔ Implémentation VarunaPoC

**Source:** `vision.pdf` v2.0 (déc. 2025), section 2 "Cadre conceptuel et analyse des angles morts du marché"
**État repo:** commit `47651d1`, tag `v0.3.0`, 2026-05-07
**Mainteneur:** Cerveau d'orchestration

Ce document est la référence unique pour vérifier que le projet reste aligné avec
sa vision. À mettre à jour à chaque livraison de Wave qui touche un angle mort.

> **Lecture en deux temps :**
> - **§0** ci-dessous = mise à jour stratégique mai 2026 (pivot foundation models, océan bleu, opportunités). Lire en premier.
> - **§1-§7** suivants = analyse originale du PDF v2.0 (déc. 2025), à lire à travers le filtre §0.

---

## 0. Mise à jour stratégique mai 2026 — Pivot Foundation Models

Le PDF v2.0 (déc. 2025, §2.3.2 "Continuous Learning System avec MLOps complet")
décrit une approche MLOps classique : monitoring drift, feedback loops, CI/CD modèles,
uncertainty quantification — **paradigme dominant 2022-2023**.

En **2026**, le paradigme a basculé : **foundation models** (UNI, CONCH, GigaPath,
Virchow, mSTAR, Atlas) entraînés en self-supervised learning sur datasets massifs.
Émergence de **copilotes IA conversationnels** type **PathChat** (FDA Breakthrough
Device, Modella AI — racheté par AstraZeneca jan. 2026) et **SmartPath**.

### 0.1. Trajectoire dominante 2026

```
[Foundation model pré-entraîné (UNI, Virchow…)]
         │
         ▼
[Fine-tuning sur cas locaux annotés Quality-First]
         │
         ▼
[Validation rigoureuse — prospective multi-centrique]
         │
         ▼
[Déploiement avec supervision humaine + explicabilité]
```

**N'EST PAS** : « on entraîne nos propres modèles avec pipeline CI/CD continuous learning ».

### 0.2. Conséquence directe sur les Waves

Le projet **conserve** la valeur du système Quality-First, mais **comme socle de
fine-tuning et de validation**, pas comme socle de training from scratch.

| Élément du PDF §2.3.2 | Lecture 2022-2023 (PDF) | Lecture 2026 (cette MàJ) |
|---|---|---|
| Drift monitoring | Trigger pour retrain from scratch | Trigger pour **fine-tune un foundation model** sur nouvelles données ou rollback |
| Feedback loops | Corrections → retrain Phikon-v2 | Corrections → **dataset curated pour fine-tune UNI/CONCH** |
| CI/CD modèles | Retrain auto + champion/challenger | **Fine-tuning workflow** + validation hold-out + champion/challenger |
| Uncertainty quantification | Brut, non calibré | **Calibré par région** (Platt/temperature) + transparence AI Act |
| Active learning | Sélection cas pour retrain | Sélection cas pour **fine-tuning local efficient** |

Wave 10 (créée le 2026-05-07) doit donc être **pivotée** : titre, milestone,
issues réécrites pour refléter la trajectoire 2026.

### 0.3. Carte océan bleu vs hors scope (anti-réinvention de la roue)

Risque identifié : OpenSlide, QuPath, Orthanc WSI, Cytomine couvrent déjà une
grande partie de la stack visée. Notre **moat** est uniquement dans les angles
morts non couverts par ces outils.

| Périmètre | Statut stratégique | Détail |
|---|---|---|
| Viewer WSI / tile streaming | **HORS scope différenciation** — wheel-reinvention | OpenSlide + OpenSeadragon font déjà bien. Garder fonctionnel mais ne pas y mettre de R&D différenciatrice. |
| Multi-format support exotique (CZI, ZVI, formats marginaux) | **HORS scope** — wheel-reinvention | Sous-périmètre OpenSlide/Bio-Formats. Soit upstream contribution, soit accepter gap. **Issues #145, #147 : downgrade ou fermeture.** |
| Annotations CRUD + outils dessin | **DANS scope (commodity)** — fondation requise | Ne pas réinventer ce que QuPath/Cytomine font. Garder simple. |
| **Quality-First** (kappa, outliers, adjudication, versioning Git-like, dataset health) | **DANS scope — DIFFÉRENCIATEUR** | Sous-adressé par marché. Cœur de notre offre. **Wave 9 = priorité absolue.** |
| **Foundation models adapter** (UNI, CONCH, fine-tuning, validation) | **DANS scope — DIFFÉRENCIATEUR** | Plateforme bien architecturée intègre les foundation models open-access sans coût R&D massif. **Wave 10 (refonte).** |
| **AI Act compliance** (traçabilité, transparence, qualité données) | **DANS scope — DIFFÉRENCIATEUR** | Avantage commercial face aux Notified Bodies. **Wave 12 (à créer).** |
| **Intégration IMS workflow** (LIS/HIS deep, pas seulement PACS) | **DANS scope — DIFFÉRENCIATEUR** | Mandate non-négociable des acheteurs hospitaliers. **Wave 12.** |
| **Réseau RCP / second avis** (co-visualisation sync + chat ancré) | **DANS scope — DIFFÉRENCIATEUR** | Valorisable inter-hôpitaux. **Wave 12.** |
| **Federated learning** (architecture-ready) | **DANS scope — DIFFÉRENCIATEUR** | Source financement Horizon Europe / EU4Health. **Wave 12.** |
| **Copilote IA conversationnel** (PathChat-like) | **À VALIDER** — exploratoire | Signal fort 2026 (acquisition AstraZeneca/Modella). Optionnel. **Wave 12 N8.** |

### 0.4. Opportunités stratégiques 2026

Cinq opportunités identifiées qui transforment Quality-First + AI Act compliance
en **avantage commercial** :

| # | Opportunité | Levier | Action projet |
|---|---|---|---|
| **O1** | Pression réglementaire favorable (AI Act exige traçabilité, transparence, qualité données) | Notified Bodies vont demander exactement ce qu'on construit | Wave 12 N4 — documentation AI Act + Wave 9 #337 versioning Git-like |
| **O2** | Foundation models en accès ouvert (UNI, CONCH, etc., licence non-commerciale ou MIT selon le modèle) | R&D modèles = coût zéro pour nous | Wave 10 N1 — foundation model registry + adapter |
| **O3** | Remboursement IA en construction (CPT codes 2026 USA pour pathologie numérique assistée IA, EU à suivre) | Modèle économique aligné sur facturation | Documenter dans `docs/PROPOSAL_VARUNA_v2.md` (non bloquant) |
| **O4** | RCP réseau et second avis (co-visualisation + chat contextuel ancré) | Valorisation inter-hôpitaux + références | Wave 12 N6 — RCP collaborative |
| **O5** | Federated learning européen (Horizon Europe, EU4Health, initiatives nationales) | Financement R&D + différenciateur Privacy AI | Wave 12 N7 — federated learning architecture-ready |
| **O6** | Publication académique (angle "Quality-First Annotation pour conformité AI Act") | Légitimité scientifique + visibilité | Wave 12 N4 inclut un livrable paper-ready |

### 0.5. Implications sur le score d'alignement

Le score original (§6 plus bas) **6 livrées / 4 partielles / 4 manquantes** sur 14
capacités PDF §2.3 reste valide, **mais** la grille de lecture change :

- Les "manquantes" §2.3.2 (drift, feedback, CI/CD modèles, active learning) sont
  maintenant **valides en support du fine-tuning**, pas en support du retrain
  from scratch — ce qui simplifie l'implémentation et l'aligne sur la trajectoire 2026.
- 5 nouvelles capacités **non couvertes par le PDF v2.0** sont à ajouter au
  périmètre projet (Wave 12) : AI Act doc, IMS deep integration, RCP collaborative,
  federated learning, copilote IA optionnel.

Score d'alignement révisé après livraison Waves 9-10-12 : projeté à **18 livrées /
4 partielles / 1 manquante** sur 23 capacités cumulées.

---

## 0.6. Pivot produit — sortie du PoC mono-tenant (mai 2026)

> **Le projet n'est plus un PoC pour CHU UCL Namur.** Il est désormais
> conçu et instruit comme un **produit / plateforme** destiné à être déployé
> sur de **multiples sites** (hôpitaux, laboratoires, réseaux RCP, instituts
> de recherche). CHU UCL Namur reste un **early adopter / customer-zero**,
> pas le périmètre cible.

### 0.6.1. Conséquences directes

**Toute issue, doc, ADR doit être lue dans une grille produit, pas mono-tenant.**

| Avant (PoC CHU UCL Namur) | Après (produit multi-tenant) |
|---|---|
| "fine-tuning sur cas locaux du CHU UCL Namur" | "fine-tuning sur cas du tenant" — chaque tenant a son fine-tuning isolé |
| "intégration PACS Telemis" | "intégration LIS/HIS/PACS multi-vendor" — Telemis = un connecteur parmi N |
| "RCP du CHU UCL Namur" | "RCP intra-tenant + inter-tenant" — collaboration cross-organisations |
| "auth OIDC Keycloak (1 realm)" | "auth multi-tenant" — un realm par tenant ou IdP fédéré externe |
| "annotations PostgreSQL local" | "annotations isolées par tenant" — schema-per-tenant ou row-level security |
| "stockage filesystem `Slides/`" | "object storage S3-compatible" — multi-tenant, multi-region capable |
| "déploiement docker-compose" | "déploiement Helm + Kubernetes + GitOps" — scalabilité horizontale |
| "1 admin technique CHU" | "self-service tenant management" — onboarding, quotas, billing |

### 0.6.2. Implications architecturales (à intégrer dans chaque architecture)

Pour chaque composant architectural, deux questions à instruire **systématiquement** :
1. **Multi-tenant ?** Données / config / RBAC isolés correctement ?
2. **Scalabilité ?** Horizontale, verticale, et trade-offs ?

| Composant | Multi-tenant | Scalabilité (Wave 13 issue) |
|---|---|---|
| Auth (OIDC) | Multi-realm Keycloak ou fédération externe | #N9 multi-tenant + IdP federation |
| Storage (slides) | Bucket-per-tenant ou prefix-per-tenant | #N10 storage S3 + tiering |
| Database (annotations, audit, quality) | Schema-per-tenant ou RLS | #N11 DB scaling (replicas, pgbouncer, partitioning) |
| ML inference | Modèle-per-tenant (fine-tuning isolé) | #N12 ML inference scaling (Triton + GPU pool + queue) |
| Cache (TileCache) + WebSocket | Namespace par tenant | #N13 cache cluster + WS sticky session |
| Observability | Logs/traces/metrics taggués par tenant | #N14 OpenTelemetry + log aggregation + SLO |
| Deployment | Helm chart configurable | #N15 Helm + GitOps + multi-region |
| Performance & coût | SLO par tenant, FinOps | #N16 perf benchmarks + FinOps monitoring |

Wave 13 créée le 2026-05-07 pour porter ces 8 axes.

### 0.6.3. Ce que cela ne change PAS

- **Le différenciateur stratégique reste identique** : Quality-First (Q),
  Foundation Models (F), AI Act compliance (A), Réseau (N). La scalabilité (S)
  est un **multiplicateur** de ces différenciateurs, pas un différenciateur en soi.
- **Wheel-reinvention reste le piège** : Kubernetes, Helm, Redis Cluster,
  pgbouncer, OpenTelemetry, Triton sont des standards. **Ne pas les réinventer**,
  les **intégrer proprement**.
- **L'effort R&D reste concentré** sur Q + F + A + N. La scalabilité est de
  l'**ingénierie d'intégration**, pas de la R&D différenciatrice.

### 0.6.4. Critère ajouté — code S (Scalability / Multi-tenant)

Le tableau de critères §0.3 (Q, F, R, A, N, W) est étendu :

| Code | Critère |
|---|---|
| Q | Quality-First annotation comme socle de fine-tuning + validation |
| F | Foundation models intégration / fine-tuning |
| R | Radical Simplicity + intégration IMS workflow |
| A | Conformité AI Act |
| N | Réseau (RCP, federated learning, publication académique) |
| **S** | **Scalabilité + multi-tenant (produit, plus PoC)** |
| W | Risque réinvention de la roue |

### 0.6.5. Implications sur les Waves 9-12 existantes

**Aucune réorientation stratégique.** Les Waves 9-12 restent valides telles
quelles. **Mais** chaque issue gagne une **dimension scalabilité / multi-tenant**
à intégrer dans son acceptance criteria :

- Wave 9 (Quality) : kappa et outliers calculés **par tenant**, pas globalement.
  Versioning Git-like = branches par tenant.
- Wave 10 (Foundation Models) : registry **multi-tenant** (modèles fine-tunés
  isolés par tenant). MLflow Registry organise par `tenant/model_name/version`.
- Wave 12 (Stratégie 2026) :
  - AI Act doc **multi-tenant** (un dossier par tenant)
  - IMS integration **multi-vendor + multi-tenant** (connecteurs configurables)
  - RCP **intra ET inter-tenant** (cross-organisation)
  - Federated learning : déjà multi-site par construction, ajouter dimension tenant

Ces dimensions doivent être ajoutées aux 23 issues open (review en cours
2026-05-07).

---

## 1. Tableau différenciateur (PDF §2.3)

Confrontation marché actuel ↔ approche VarunaPoC ↔ état d'implémentation.

| Angle mort critique | État actuel marché | Approche VarunaPoC (vision) | Implémentation 2026-05-07 |
|---|---|---|---|
| **Quality-First Annotations** | Annotations sans QA, pas de métriques cohérence, pas de détection erreurs | Versioning Git-like, kappa inter-annotateur automatique, détection outliers, workflows adjudication | **Partiel** — kappa+F1+IoU+confusion+disagreement FAIT (Wave 3 Quality) ; outliers+adjudication+Git-like+métriques prédictives MANQUE (Wave 9) |
| **Continuous Learning MLOps** | Focus training initial, pas de monitoring drift, corrections experts perdues | Monitoring automatique drift, feedback loops actifs, pipeline CI/CD modèles, uncertainty quantification | **Faible** — inférence Slideflow + Phikon-v2 + uncertainty FAIT ; drift+feedback+CI-CD modèles+calibration+active learning MANQUE (Wave 10) |
| **Radical Simplicity** | Formation 2-4 semaines, interface complexe, installation lourde, manuel 100 pages | Zero-config, onboarding 3 minutes, interface geste-mimétique, accès navigateur direct, SSO transparent | **Avancé** — zero-config web + P95 65ms + OIDC SSO + PACS deep-link FAIT ; onboarding 3min + double-clic centrer MANQUE (Wave 11) |

---

## 2. Les 12 angles morts structurels (PDF §2.2)

Mapping fin sur la **table des 12 angles morts** que le marché actuel n'adresse
pas correctement.

| # | Catégorie | Angle mort identifié (PDF) | Réponse VarunaPoC | État | Référence code |
|---|---|---|---|---|---|
| 1 | Interopérabilité | Vendor lock-in, formats propriétaires | OpenSlide 10 formats + DICOM WSI + FHIR R4 | OK | `services/format_detector.py`, `fhir/resources.py`, `services/readers/` |
| 2 | Qualité annotations | Pas de métriques IAA, pas de détection outliers | Cohen+Fleiss kappa, F1, confusion, IoU, disagreement heatmap | PARTIEL | `quality/metrics.py`, outliers MANQUE → Wave 9 |
| 3 | MLOps | Drift monitoring quasi absent | InProcess + Subprocess + Triton stub | FAIBLE | `services/ml/worker_provider/`, drift MANQUE → Wave 10 |
| 4 | Explicabilité | Heatmaps non médicalement pertinentes | Heatmap attention + uncertainty + 3 régions confidence | PARTIEL | `services/detection/`, calibration par région MANQUE → Wave 10 |
| 5 | Feedback loops | Corrections experts perdues, active learning manuel | — | MANQUE | → Wave 10 |
| 6 | Simplicité | Courbe d'apprentissage de plusieurs semaines | Web zero-config, P95 65ms, OSD geste-mimétique | OK | `frontend/src/`, onboarding 3min → Wave 11 |
| 7 | Collaboration | Pas de co-annotation temps réel | WebSocket events (sprint 15), async via FHIR/PACS | PARTIEL | `services/workflow/websocket_hook.py`, co-annotation MANQUE |
| 8 | Privacy AI | Centralisation, frein RGPD | Hébergement interne, audit dual DB+JSON | PARTIEL | `auth/audit.py` ; federated learning hors scope |
| 9 | Reproductibilité | Versions algorithmes non tracées | Versioning code OK ; versioning datasets/runs ML MANQUE | PARTIEL | git OK, MLflow → Wave 10 |
| 10 | Cas rares | Optimisation pour fréquents, échec edge cases | — | MANQUE | OOD detection → Wave 10 |
| 11 | Intégration SI | Jonglage 5-10 systèmes | OIDC SSO + PACS Telemis deep-link + FHIR DiagnosticReport | OK | `auth/oidc.py`, `routes/slides.py:by-name`, `fhir/resources.py` |
| 12 | Modèle économique | Licensing complexe, ROI difficile | Open source MIT, hébergement interne | OK | `LICENSE`, `docs/HOSPITAL_DEPLOYMENT_EVALUATION.md` |

**Score global :** 5 OK / 4 partiels / 3 manquants sur 12 angles morts structurels.

---

## 3. Détail des 3 angles morts critiques (PDF §2.3)

### 3.1. Quality-First Annotation Platform (PDF §2.3.1)

**Constat PDF :** "23% des annotations en recherche contiennent des erreurs non détectées"
(Pantanowitz et al. 2024). Implémentation contrôles qualité réduit erreurs de 67%
en multi-sites (Hanna et al. 2023).

| Capacité demandée par PDF | Implémenté ? | Référence | Gap → action |
|---|---|---|---|
| Mesure auto kappa/Dice inter-annotateur temps réel | ✅ | `quality/metrics.py:cohen_kappa,fleiss_kappa`, `quality/matching.py` (PostGIS IoU + grid) | — |
| Détection annotations suspectes (outliers spatial/taille/forme) | ❌ | — | Wave 9 #1 — DBSCAN sur features (centroid distance, area, perimeter, complexity) |
| Workflows adjudication structurés (review par pairs, conflict resolution) | ❌ | — | Wave 9 #2 — review queue + 2-of-3 consensus + escalation |
| Versioning Git-like (branches, merge, diff visuel, rollback) | 🟡 | issue #331 (audit medicolegal seulement) | Wave 9 #3 — branches/merge/diff visuel sur annotations |
| Métriques prédictives qualité dataset (avant entraînement IA) | ❌ | — | Wave 9 #4 — agrégat IAA + outlier rate + diversité spatiale → score qualité |

### 3.2. Continuous Learning System / MLOps complet (PDF §2.3.2)

**Constat PDF :** "L'absence de suivi continu des performances IA en production est une
lacune majeure du marché actuel" (France Biotech). Continuous learning maintient
performance stable 24 mois vs dégradation 18% pour modèles statiques (Komura & Ishikawa 2024).

| Capacité demandée par PDF | Implémenté ? | Référence | Gap → action |
|---|---|---|---|
| Monitoring drift automatique (statistical comparison predictions vs validations experts) | ❌ | — | Wave 10 #1 — KS test + PSI sur distributions, alertes Prometheus |
| Feedback loops automatiques (corrections experts → dataset ré-entraînement) | ❌ | — | Wave 10 #2 — pipeline correction → curated dataset MLflow |
| Pipeline CI/CD modèles (retrain auto + validate + rollback si dégradation) | ❌ | — | Wave 10 #3 — GitHub Actions retraining + champion/challenger + auto-rollback |
| Calibration incertitude par région + visualisation zones de doute | 🟡 | uncertainty existe (`services/detection/`), calibration MANQUE | Wave 10 #4 — Platt scaling / temperature scaling + overlay confiance |
| Active learning intelligent (priorisation cas difficiles annotation experte) | ❌ | — | Wave 10 #5 — entropy-based + diversity sampling + queue annotation |

### 3.3. Radical Simplicity (PDF §2.3.3)

**Constat PDF :** "La résistance au changement des pathologistes est le principal facteur
d'échec des déploiements WSI, devant les limitations techniques" (Leeds Guide). Interface
bien conçue réduit temps formation de 85% et améliore acceptation utilisateur de 72%
(Stathonikos et al. 2023).

| Capacité demandée par PDF | Implémenté ? | Référence | Gap → action |
|---|---|---|---|
| Zero-config deployment (accès direct navigateur) | ✅ | docker-compose unifié, frontend Vite SPA | — |
| Interface geste-mimétique (zoom molette, pan, double-clic centrer) | 🟡 | OSD zoom molette + pan OK ; double-clic centrer à vérifier | Wave 11 #2 — audit interactions OSD vs microscope optique |
| Onboarding tutoriel contextuel 3min (pas de manuel 50 pages) | ❌ | docs/Manuel existe mais pas de tutoriel interactif | Wave 11 #1 — overlay shepherd.js / driver.js + 3-step tour |
| Performance perceptuelle <100ms par interaction | ✅ | tile keep-alive 0-13ms, P95 65ms, cache 3-niveaux 75-85% | — |
| Intégration transparente SI (SSO, contexte patient auto depuis PACS) | ✅ | OIDC PKCE + PACS Telemis deep-link `/slide/{name}` | — |

---

## 4. Phases PDF §5.1 ↔ Waves GitHub

Mapping historique. Les phases originales du plan 15 semaines ont été remappées
en 8 Waves itératives + sprints Strangler Fig.

| Phase PDF | Sprint | Wave réelle | Statut |
|---|---|---|---|
| 1 — Initialisation (sem. 1-3) | shadowing, stack choice, setup | (pré-Wave 1) | DONE |
| 2 — Core (sem. 4-9) | viewer, formats, annotations, ML, compare | Waves 1-2 | DONE |
| 3 — Enrichissement (sem. 10-13) | auth, audit, quality, PACS | Waves 3-4 | DONE |
| 4 — Finalisation (sem. 14-15) | tests E2E, docs, prod | Waves 6-7 + Standards | DONE |
| Post-MVP Cercle 1 (mois 4-8) | SSO, quality complet, collab temps réel | Waves 5+8 + sprint 15 (WS) | EN COURS |
| Post-MVP Cercle 2 (mois 8-14) | MLOps complet, continuous learning | **Wave 10 (à créer)** | À FAIRE |

**Note :** Wave 9 (Quality-First Deep) et Wave 11 (Radical Simplicity Polish)
correspondent à un raffinement du Cercle 1 et de la simplicité — n'ont pas
d'équivalent direct dans le plan 15 semaines original mais sont nécessaires pour
combler les angles morts §2.3.1 et §2.3.3.

---

## 5. Méthodologie NCCMT (PDF §3) — auto-évaluation

Le projet revendique l'EIDM et le modèle NCCMT en 7 étapes. Auto-évaluation :

| Étape | État | Évidence |
|---|---|---|
| 1. Définir | OK | `vision.pdf §1.1`, `docs/PROPOSAL_VARUNA_v2.md` |
| 2. Rechercher | OK | DICOM WSI, FHIR R4, OpenSlide, Slideflow, Cytomine/DSA/QuPath analysés (`docs/ETUDE_SOLUTIONS_EXISTANTES.md`) |
| 3. Estimer (Appraise) | PARTIEL | analyse écrite ; pas de scoring formel multi-critères |
| 4. Synthétiser | OK | 3 angles morts critiques identifiés + architecture neutre |
| 5. Adapter | OK | contraintes locales prises en compte (Telemis, NDPI/MRXS, hébergement interne) |
| 6. Mettre en œuvre | OK | Agile sprints 1-2 sem., 124 issues closed sur 8 Waves |
| 7. Évaluer | PARTIEL | tests automatisés OK ; tests utilisateurs cliniciens à intensifier |

---

## 6. Score d'alignement global

| Dimension | Score | Justification |
|---|---|---|
| Vision projet (PDF §1) | 10/10 | Contexte CHU UCL Namur clair, question PICR formulée |
| Cadre conceptuel (PDF §2.1-2.2) | 9/12 | 9 des 12 angles morts adressés au moins partiellement |
| 3 différenciateurs critiques (PDF §2.3) | 6+4+4=14 sub-capacités | 6 livrées / 4 partielles / 4 manquantes |
| Méthodologie EIDM (PDF §3) | 6/7 | 5 étapes OK, 2 partielles (Appraise, Évaluer) |

**Verdict :** la **fondation** des 3 angles morts critiques est solide ; la **profondeur**
des angles 1 et 2 reste majoritairement à livrer (Waves 9-10). L'angle 3 (Simplicité)
nécessite un polish ciblé (Wave 11).

---

## 7. Actions de comblement (Waves 9-11 à créer)

### Wave 9 — Quality-First Deep (PDF §2.3.1, gaps 2-5)
1. `feat(quality): outlier detection sur annotations (DBSCAN spatial/taille/forme)`
2. `feat(quality): workflow d'adjudication par pairs (review queue, conflict resolution)`
3. `feat(quality): versioning Git-like des annotations (branches, merge, diff visuel)`
4. `feat(quality): métriques prédictives qualité dataset (score avant entraînement IA)`

### Wave 10 — Continuous Learning MLOps (PDF §2.3.2, gaps 1-5)
5. `feat(mlops): monitoring drift automatique (KS test + PSI, alertes Prometheus)`
6. `feat(mlops): feedback loops auto (corrections experts → dataset MLflow)`
7. `feat(mlops): pipeline CI/CD modèles (retrain + validate + rollback)`
8. `feat(mlops): calibration incertitude par région (Platt/temperature scaling + overlay)`
9. `feat(mlops): active learning intelligent (entropy + diversity sampling)`

### Wave 11 — Radical Simplicity Polish (PDF §2.3.3, gaps 2-3)
10. `feat(ux): onboarding tutoriel contextuel 3min (shepherd.js / driver.js)`
11. `chore(ux): audit interactions geste-mimétique (double-clic centrer + vs microscope optique)`

---

## Changelog

### v1.0 (2026-05-07)
- Création initiale post-Strangler Fig sprint 15
- Mapping exhaustif PDF §2.1-2.3 ↔ implémentation
- Identification de 11 issues à créer sur 3 Waves nouvelles (9, 10, 11)

---

**Prochaine review :** après création Waves 9-10-11 (gh CLI) + premier sprint Wave 9.
