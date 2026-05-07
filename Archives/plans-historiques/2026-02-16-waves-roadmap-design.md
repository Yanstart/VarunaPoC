# VarunaPoC — Roadmap par Vagues d'Impact Utilisateur

**Date** : 2026-02-16
**Approche** : Vagues d'impact utilisateur (Approach B)
**Principe directeur** : *Tout ce qui sera fait sera pensé pour l'utilisateur.*

---

## Sources d'analyse

Ce roadmap synthétise 4 rapports du cerveau d'orchestration :

1. **analyse_ux_anapath.md** — Stratégie UX pour workflow pathologiste (7 quick-wins, 5 évolutions structurelles, mapping terminologique)
2. **audit_backend_frontend_gap.md** — 18/24 endpoints connectés, 6 gaps identifiés, règle "No Endpoint Without UX"
3. **features_ml_pathologiste.md** — 18 features ML organisées en 4 catégories (A: existantes à mieux présenter, B: évidentes, C: créatives)
4. **pipeline_feedback_caching.md** — Feedback loop, cache 3 niveaux, 9 nouveaux endpoints, schéma table corrections

## Tensions identifiées

| Tension | Résolution |
|---------|-----------|
| Scope creep (18 features ML × 5 évolutions UX × 9 endpoints) | Priorisation par impact utilisateur perçu, pas par complexité technique |
| ML features vs UX — le pathologiste ne veut pas "de l'IA" | L'IA assiste discrètement, jamais ne juge. Wave 2 = "L'IA qui assiste" |
| Home refonte = quick-win dans rapport UX mais structurel en réalité | Déplacé en Wave 3 avec le concept "cas" complet |
| Cache Redis vs cache spécialisé ML | Cache 3 niveaux spécialisé (mémoire/disque/vecteur) plutôt que Redis générique |

---

## Structure GitHub

### Labels

| Label | Description |
|-------|-------------|
| `wave:1` `wave:2` `wave:3` `wave:4` | Vague d'appartenance |
| `domain:ux` `domain:ml` `domain:infra` | Domaine technique |
| `type:feature` `type:refactor` | Nature du changement |
| `priority:critical` `priority:high` `priority:medium` `priority:low` | Priorité |

### Milestones

| Milestone | Nom |
|-----------|-----|
| 1 | Wave 1 — Le viewer qui parle pathologiste |
| 2 | Wave 2 — L'IA qui assiste |
| 3 | Wave 3 — Le cas, pas le fichier |
| 4 | Wave 4 — L'écosystème intelligent |

---

## Wave 1 — Le viewer qui parle pathologiste

**Objectif** : L'interface parle la langue du pathologiste. Aucune feature nouvelle — on polit l'existant.

| # | ID | Titre | Domaine | Priorité |
|---|-----|-------|---------|----------|
| #60 | W1-UX01 | Terminologie FR pathologiste dans toute l'interface | UX | critical |
| #61 | W1-UX02 | Labels d'annotation prédéfinis métier | UX | critical |
| #62 | W1-UX03 | Panneaux ML et Quality masqués par défaut (accordéon fermé) | UX | high |
| #63 | W1-UX04 | Sync pan/zoom activé par défaut en mode comparaison | UX | high |
| #64 | W1-UX05 | Barre de status en grossissement optique (×10, ×40) | UX | medium |
| #65 | W1-UX06 | Toolbar contextuelle — 2 outils visibles, reste en sous-menu | UX | medium |
| #66 | W1-UX07 | Badge incertitude ML sur prédictions existantes | UX | medium |
| #67 | W1-UX08 | Comptage annotations intégré dans sidebar | UX | low |
| #68 | W1-INF01 | Table corrections SQL + migration Alembic | Infra | high |
| #71 | W1-INF02 | Cache disque embeddings niveau 2 (.npy structuré) | Infra | high |
| #73 | W1-INF03 | Cache mémoire metadata niveau 1 (lru_cache, TTL) | Infra | medium |

**Livrable utilisateur** : Le viewer ressemble à un outil de pathologiste, pas à un prototype tech.

---

## Wave 2 — L'IA qui assiste

**Objectif** : L'IA devient utile au quotidien — Focus Assist, mesures auto, feedback, auto-tags.

| # | ID | Titre | Domaine | Priorité |
|---|-----|-------|---------|----------|
| #70 | W2-ML01 | Focus Assist — backend GET /ml/focus/{slide_id} | ML | critical |
| #74 | W2-ML02 | Focus Assist — frontend FocusAssistPanel | UX | critical |
| #77 | W2-ML03 | Mesure auto dimension tumorale — backend GET /ml/measure/{slide_id} | ML | high |
| #79 | W2-ML04 | Mesure auto — frontend badge dimensions dans DetectionPanel | UX | high |
| #85 | W2-ML05 | Feedback pathologiste — backend POST /ml/feedback/{slide_id} | Infra | high |
| #86 | W2-ML06 | Feedback — frontend boutons Confirmer/Corriger/Rejeter | UX | high |
| #87 | W2-ML07 | Auto-tag lame — backend GET /ml/tags/{slide_id} | ML | medium |
| #88 | W2-ML08 | Auto-tag — frontend badge sous nom de lame | UX | medium |
| #89 | W2-INF01 | Background task pré-calcul embeddings au chargement de lame | Infra | high |
| #91 | W2-INF02 | Sélecteur modèle ML utilisable (UX, pas technique) | UX | low |

**Livrable utilisateur** : "L'IA m'a montré où regarder et a mesuré la tumeur pour moi."

---

## Wave 3 — Le cas, pas le fichier

**Objectif** : Le pathologiste travaille avec des cas (dossiers patients), pas des fichiers .svs.

| # | ID | Titre | Domaine | Priorité |
|---|-----|-------|---------|----------|
| #69 | W3-UX01 | Concept cas : grouper lames par dossier parent dans la Home | UX | critical |
| #72 | W3-UX02 | Sidebar contextuelle viewer — liste lames du même cas | UX | critical |
| #75 | W3-UX03 | Switch rapide intra-cas (clic = change lame sans retour Home) | UX | high |
| #76 | W3-UX04 | Refonte Home — vue cas par défaut + fallback explorateur fichiers | UX | high |
| #78 | W3-ML01 | Similarity Search — index vectoriel FAISS/pgvector | Infra | high |
| #80 | W3-ML02 | Similarity Search — backend POST /ml/similar/{slide_id} | ML | high |
| #82 | W3-ML03 | Similarity Search — frontend SimilarityPanel | UX | high |
| #84 | W3-INF01 | FeedbackCollector service — agrégation corrections + seuils | Infra | medium |

**Livrable utilisateur** : "J'ouvre un cas et je navigue entre les lames comme avec mon microscope multi-objectifs."

---

## Wave 4 — L'écosystème intelligent

**Objectif** : Features avancées (clustering, QC, drift) + ops (monitoring, ré-entraînement).

| # | ID | Titre | Domaine | Priorité |
|---|-----|-------|---------|----------|
| #81 | W4-ML01 | Comptage cellulaire — backend POST /ml/count/{slide_id} | ML | high |
| #83 | W4-ML02 | Comptage cellulaire — frontend résultat dans CountingPanel | UX | high |
| #90 | W4-ML03 | Clustering morphologique — backend POST /ml/cluster/{slide_id} | ML | medium |
| #92 | W4-ML04 | Clustering morpho — frontend overlay multi-couleur | UX | medium |
| #93 | W4-ML05 | QC auto qualité lame — backend GET /ml/quality/{slide_id} | ML | medium |
| #94 | W4-ML06 | QC auto — frontend badge qualité dans barre de titre | UX | medium |
| #95 | W4-OPS01 | DriftDetector service — monitoring distributions embeddings | Infra | medium |
| #96 | W4-OPS02 | Dashboard admin drift + qualité modèles | UX | low |
| #97 | W4-OPS03 | Pipeline ré-entraînement DVC → Slideflow MIL → MLflow | Infra | low |
| #98 | W4-UX01 | Vue Mes cas worklist comme page d'accueil | UX | medium |
| #99 | W4-UX02 | Historique cas — retrouver un cas déjà lu | UX | low |

**Livrable utilisateur** : "Le système apprend de mes corrections et m'alerte quand la qualité baisse."

---

## Issues existantes conservées

Ces issues pré-existantes ne sont pas dans les vagues mais restent ouvertes pour référence future :

| # | Titre | Raison |
|---|-------|--------|
| #27 | Rate Limiting | Sécurité — à traiter quand multi-utilisateur |
| #35 | Merge Automatique Annotations | Qualité annotations — pertinent pour Wave 2+ |
| #37 | Detection Outliers Annotations | Qualité — à relier à W4-ML05 |
| #38 | Slideflow Adapter Python | Intégration — utile pour W4-OPS03 |
| #39 | Abstraction ViewerInterface | Architecture — long terme |
| #40 | OME-TIFF Reader Plugin | Formats — sur demande utilisateur |
| #41 | OME-Zarr Reader Plugin | Formats — sur demande utilisateur |
| #42 | UNI Embeddings Integration | ML — alternative à Phikon |
| #46 | DICOM WSI Export | Interopérabilité — sur demande |
| #49 | Prometheus Metrics | Ops — à relier à W4-OPS01 |

## Issues fermées (16)

Issues complétées ou absorbées par les nouvelles vagues :
#22, #28, #29, #30, #31, #32, #33, #34, #36, #43, #44, #45, #47, #48, #50, #51

---

## Graphe de dépendances simplifié

```
Wave 1 (fondations)
├── W1-INF01 (table corrections) ──→ W2-ML05 (feedback backend)
├── W1-INF02 (cache disque) ──→ W2-INF01 (background tasks)
│                              ├─→ W3-ML01 (FAISS index)
│                              ├─→ W4-ML03 (clustering)
│                              └─→ W4-ML05 (QC auto)
└── W1-INF03 (cache mémoire) ──→ W2-ML07 (auto-tag)

Wave 2 (IA assistante)
├── W2-ML05 (feedback) ──→ W2-ML06 (frontend) ──→ W3-INF01 (FeedbackCollector)
├── W2-ML03 (mesure) ──→ W2-ML04 (frontend)
├── W2-ML07 (auto-tag) ──→ W2-ML08 (frontend)
└── W2-ML01 (focus) ──→ W2-ML02 (frontend)

Wave 3 (concept cas)
├── W3-UX01 (grouper cas) ──→ W3-UX02 (sidebar) ──→ W3-UX03 (switch)
│                           └──→ W3-UX04 (refonte Home)
├── W3-ML01 (FAISS) ──→ W3-ML02 (API) ──→ W3-ML03 (frontend)
└── W3-INF01 (FeedbackCollector) ──→ W4-OPS01 (drift)

Wave 4 (écosystème)
├── W4-ML01 (comptage) ──→ W4-ML02 (frontend)
├── W4-ML03 (clustering) ──→ W4-ML04 (frontend)
├── W4-ML05 (QC) ──→ W4-ML06 (frontend)
├── W4-OPS01 (drift) ──→ W4-OPS02 (dashboard)
│                     └──→ W4-OPS03 (ré-entraînement)
└── W4-UX01 (worklist) ──→ W4-UX02 (historique)
```

---

## Règle opérationnelle

> **No Endpoint Without UX** : Chaque endpoint backend doit avoir un composant frontend qui montre le résultat à l'utilisateur, une méthode dans ApiService.js, et un test E2E couvrant le flux complet.

## Checklist par feature

```
[] Endpoint backend opérationnel
[] Méthode dans ApiService.js
[] Composant frontend qui affiche/utilise le résultat
[] L'utilisateur peut déclencher et voir la feature sans quitter le viewer
[] Test E2E qui couvre le flux complet
```
