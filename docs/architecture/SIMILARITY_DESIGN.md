# Conception — Recherche de lames similaires

**Statut :** Design — non implémenté
**Auteur :** Issu d'une revue collaborative (PoC TFE)
**Date :** 2026-05-27
**Public cible :** Dev backend / frontend, rédaction du rapport TFE
**Préalable :** Lecture de [`MODULAR_ARCHITECTURE.md`](./MODULAR_ARCHITECTURE.md) recommandée

---

## 1. Pourquoi ce document existe

L'écran `SimilarityPanel` est présent dans le frontend (`frontend/src/components/SimilarityPanel.js`) et l'appel `POST /api/v1/ml/similar/{slide_id}` est câblé côté `ApiService`. **L'endpoint backend n'a jamais été implémenté.** Le commentaire d'entête du composant évoque vaguement *« FAISS-based cosine similarity »* — c'est une intention, pas une définition.

Implémenter cet endpoint sans définir au préalable *ce qu'on appelle « similaire »* produirait un résultat techniquement correct mais cliniquement trompeur. En pathologie numérique, deux lames ne sont jamais similaires *en général* — elles le sont selon une dimension donnée. Ce document fige ces dimensions, l'architecture qui les expose, et la stratégie de cache.

---

## 2. Décisions structurantes (à lire en premier)

| # | Décision | Justification |
|---|---|---|
| D1 | La similarité est **multi-critère**, **sélectionnée par l'utilisateur** | Aucune définition unique n'est universellement valide. Le pathologiste sait ce qu'il cherche ; le système expose les dimensions, pas un score magique. |
| D2 | 4 catégories × 10-12 critères fins, regroupés hiérarchiquement | Cohérent avec les profils utilisateurs (pressé / fin / chercheur). Granularité validée par les données déjà persistées (table `annotations`, `corrections`, `view_history`). |
| D3 | Agrégation par **moyenne arithmétique** des sous-scores actifs | Simple, transparent, défendable. Pas de poids cachés. L'utilisateur module en cochant / décochant. |
| D4 | Score décomposé exposé dans la réponse (`criteria_scores`) | Traçabilité clinique : chaque résultat est inspectable. Évite la boîte noire. |
| D5 | Sémantique : skip silencieux des slides sans embedding cache, champ `coverage` dans la réponse | Robustesse face à la latence de pré-calcul background. L'utilisateur sait que la comparaison est partielle. |
| D6 | Persistance : **cache Redis TTL 30 minutes**, clé `similarity:{slide_id}:{criteria_hash}` | Cohérent avec `quality_reports`. Évite recalcul sur reclic. Pas de table dédiée — pas d'enjeu de purge / RGPD. |
| D7 | Aucun changement de schéma DB. Tous les critères workflow sont calculables via SQL sur les tables existantes. | Intégration smooth — pas de migration, pas de risque de drift. |
| D8 | RBAC strict : les critères workflow ne révèlent que des slides accessibles à l'utilisateur dans son tenant | Pas de canal latéral. Conforme à l'audit existant. |

---

## 3. État de l'existant (rappel)

| Brique | Endroit | Statut | Rôle dans la similarité |
|---|---|---|---|
| `SimilarityPanel.js` (379 l.) | `frontend/src/components/` | ✅ écrit, intégré dans `ViewerPanel` | UI prête, à étendre avec checkboxes |
| `ApiService.getSimilarSlides` | `frontend/src/services/` | ✅ existe | Appel HTTP câblé |
| `disk_cache.load_embeddings(slide_id, model)` | `backend/services/cache/` | ✅ existe | Source des embeddings sémantiques |
| `background_tasks.extract_features` | `backend/services/` | ✅ lancé à l'ouverture d'une slide | Alimente le cache d'embeddings asynchronement |
| `slide_scanner` | `backend/services/` | ✅ existe | Source des métadonnées techniques |
| Tables `annotations`, `annotation_labels`, `corrections`, `view_history` | `backend/models/` | ✅ migrations 001-009 | Source des critères workflow |
| `quality_reports` (pattern de cache JSONB TTL) | Table | ✅ existe | Précédent pour le cache de similarité |
| **`POST /ml/similar/{id}`** | Endpoint | ❌ inexistant | À implémenter |

---

## 4. Les quatre catégories de critères

Le panel UI affiche 4 sections pliables. Chaque section contient N cases à cocher. La règle : *au moins un critère coché, sinon le bouton « Rechercher » est désactivé*.

### A. Technique (instantané, sans GPU)

Comparaison de tuples de métadonnées lues du scanner.

| ID | Critère | Source | Score binaire / continu |
|---|---|---|---|
| `tech.vendor` | Fournisseur scanner identique | `slide_scanner.format` | binaire (1.0 ou 0.0) |
| `tech.format` | Format fichier identique | `slide_scanner.format_string` | binaire |
| `tech.magnification` | Magnification effective comparable | OpenSlide `openslide.objective-power` | continu : `1 − abs(diff) / max` |
| `tech.dimensions` | Dimensions niveau 0 comparables | OpenSlide `level_dimensions[0]` | continu : ratio géométrique |

### B. Apparence visuelle (rapide, ~100-300 ms par slide)

Signatures dérivées de la thumbnail (~128 px).

| ID | Critère | Méthode | Score |
|---|---|---|---|
| `visual.phash` | Empreinte perceptuelle 64-bit | downsample 8×8 grayscale, threshold par moyenne | `1 − hamming/64` |
| `visual.color_hist` | Histogramme de couleur RGB | 16 bins / canal, normalisé | `1 − chi2 / max_chi2` |
| `visual.tissue_density` | Pourcentage de pixels non-fond | masque Otsu sur niveau de gris | `1 − abs(diff)` |

### C. Sémantique (lourd, dépend du cache embeddings)

Utilise les embeddings déjà calculés en background par Slideflow.

| ID | Critère | Source | Score |
|---|---|---|---|
| `semantic.resnet50` | Embedding ResNet50 ImageNet | `disk_cache/<slide_id>/resnet50.npy` | cosine similarity |
| `semantic.phikon` | Embedding Phikon (modèle pathologie) | `disk_cache/<slide_id>/phikon.npy` | cosine similarity |
| `semantic.tile_stats` | Distribution des features sur les tiles | stats agrégées sur l'embedding | cosine sur vecteur réduit |

**Cache miss policy** : si l'embedding d'une slide candidate n'est pas présent dans le disk_cache, la slide est **silencieusement exclue** du calcul pour ce critère. La réponse contient un champ `coverage` indiquant la complétude.

### D. Workflow (clinique, requêtes SQL pures)

| ID | Critère | SQL (concept) | Score |
|---|---|---|---|
| `workflow.labels_overlap` | Labels présents sur les deux slides | Jaccard sur `annotations.label_id` distinct par slide | `\|A ∩ B\| / \|A ∪ B\|` |
| `workflow.status_match` | Statut majoritaire identique | mode(`annotations.status`) par slide | binaire |
| `workflow.annotation_type_match` | Mix manuel/auto similaire | ratio `auto / manual` par slide | `1 − abs(diff)` |
| `workflow.models_overlap` | Modèles AI ayant tourné dessus | Jaccard sur `corrections.model_name` | Jaccard |
| `workflow.rejection_pattern` | Type d'erreur AI dominant identique | mode(`corrections.rejection_reason`) | binaire |
| `workflow.coannotation` | Cohorte de pathologistes commune | Jaccard sur `annotations.created_by` | Jaccard |
| `workflow.coview` | Vue par les mêmes utilisateurs | Jaccard sur `view_history.user_sub` | Jaccard |
| `workflow.annotation_density` | Cas chargé vs simple | `COUNT(annotations) / area` | `1 − abs(diff) / max` |

Toutes les requêtes utilisent un filtre `WHERE tenant_id = :user_tenant` pour respecter l'isolation multi-établissement.

---

## 5. Architecture — composants impactés

```
┌──────────────────────────────────────────────────────────────────────┐
│   SimilarityPanel.js  (frontend)                                     │
│   ─ accordéon par catégorie (A/B/C/D)                                │
│   ─ checkboxes fines (1 par critère)                                 │
│   ─ bouton "Rechercher" (désactivé si 0 critère coché)               │
│   ─ résultats : grille de thumbnails                                 │
│   ─ tooltip par résultat : breakdown des criteria_scores             │
│   ─ banner d'avertissement si coverage < 100% sur catégorie C        │
└────────────────────┬─────────────────────────────────────────────────┘
                     │ POST /api/v1/ml/similar/{slide_id}
                     │     ?criteria=tech.vendor,visual.phash,semantic.resnet50
                     │     &top_k=5&max_candidates=40
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│   routes/ml.py :: get_similar_slides()                               │
│   ─ vérifie auth + RBAC (require_role MEDECIN/ADMIN_TECHNIQUE)       │
│   ─ vérifie cache Redis (clé = slide_id + criteria_hash)             │
│   ─ délègue à services/ml/similarity.py                              │
└────────────────────┬─────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│   services/ml/similarity.py :: search_similar()  (NOUVEAU)           │
│                                                                       │
│   ┌─ for each criterion id ───────────────────────────────────┐     │
│   │   dispatcher → scorer module                              │     │
│   │   ─ "tech.*"     → technical_scorer                       │     │
│   │   ─ "visual.*"   → visual_scorer                          │     │
│   │   ─ "semantic.*" → semantic_scorer                        │     │
│   │   ─ "workflow.*" → workflow_scorer                        │     │
│   └────────────────────────────────────────────────────────────┘     │
│                                                                       │
│   ┌─ aggregate(sub_scores) = mean()                                   │
│   ┌─ sort desc, top_k                                                 │
│   └─ return + cache en Redis (TTL 30 min)                             │
└──┬──────────────┬──────────────┬─────────────────┬───────────────────┘
   │              │              │                 │
   ▼              ▼              ▼                 ▼
┌────────┐  ┌───────────┐  ┌────────────────┐  ┌──────────────────────┐
│ tech   │  │ visual    │  │ semantic       │  │ workflow             │
│ scorer │  │ scorer    │  │ scorer         │  │ scorer               │
│        │  │           │  │                │  │                      │
│ Lit    │  │ Compute   │  │ Lit            │  │ Requêtes SQL sur     │
│ slide_ │  │ pHash +   │  │ disk_cache.    │  │ annotations /        │
│ scanner│  │ histo +   │  │ load_          │  │ corrections /        │
│ cache  │  │ density   │  │ embeddings()   │  │ view_history         │
│ RAM    │  │           │  │                │  │ (filtre tenant_id)   │
│ existe │  │ NOUVEAU   │  │ existe         │  │                      │
└────────┘  └───────────┘  └────────────────┘  └──────────────────────┘
```

**Lignes nouvelles estimées :**

| Fichier | LOC | Type |
|---|---|---|
| `backend/services/ml/similarity.py` | ~250 | nouveau |
| `backend/routes/ml.py` (endpoint + schémas) | ~80 | ajout |
| `frontend/src/components/SimilarityPanel.js` | ~150 | extension |
| `frontend/src/css/similarity-panel.css` | ~40 | ajout |
| `backend/tests/test_similarity.py` | ~150 | nouveau |
| **Total** | **~670** | sans nouvelle dépendance ni migration |

---

## 6. Flow utilisateur — séquence détaillée

```
T0 : user ouvre slide A
     ├─► viewer charge dzi.json + tiles
     ├─► background_tasks lance extract_features(A) asynchronement
     │   ↳ ~20s, écrit disk_cache/A/resnet50.npy
     │
T1 : user navigue, zoome, peut-être annote
     │
T2 : user clique sur l'accordéon "Lames similaires"
     ├─► panel s'ouvre, état initial :
     │   ─ catégorie A pliée, checkboxes [tech.vendor ☑, tech.format ☑]
     │     défaut : la pré-sélection minimum garantit un résultat instantané
     │   ─ catégories B, C, D pliées vide
     │   ─ bouton "Rechercher" activé (>=1 critère coché)
     │
T3 : user déplie C, coche [semantic.resnet50 ☑]
     ├─► hint visuel "calcul léger si embeddings pré-calculés"
     │
T4 : user clique "Rechercher"
     ├─► POST /api/v1/ml/similar/{A}
     │     ?criteria=tech.vendor,tech.format,semantic.resnet50
     │     &top_k=5&max_candidates=40
     │
T5 : backend
     ├─► auth + RBAC OK
     ├─► criteria_hash = sha1(sorted_criteria) → clé Redis
     ├─► cache miss
     │
     ├─► slide_scanner.get_all_slides() (filtre tenant=user.tenant_id, != A)
     │   → 39 candidats
     │
     ├─► pour chaque candidat C :
     │     scores = {}
     │     scores["tech.vendor"]      = technical_scorer.vendor(A, C)
     │     scores["tech.format"]      = technical_scorer.format(A, C)
     │     scores["semantic.resnet50"] = semantic_scorer.cosine(A, C, "resnet50")
     │       ↳ disk_cache lookup A : hit
     │       ↳ disk_cache lookup C : miss → skip ce critère pour C, flag coverage
     │     final_score = mean(scores.values()) hors None
     │
     ├─► sort desc, take top 5
     ├─► écrit dans Redis sous clé similarity:A:{hash} TTL=1800s
     │
T6 : réponse JSON renvoyée au frontend
     {
       "criteria_used": ["tech.vendor", "tech.format", "semantic.resnet50"],
       "candidates_scanned": 39,
       "coverage": { "semantic.resnet50": "14/39" },
       "results": [
         {
           "slide_id": "abc...",
           "name": "CMU-2.svs",
           "overview_url": "/api/v1/slides/abc.../overview",
           "score": 0.87,
           "criteria_scores": {
             "tech.vendor": 1.0,
             "tech.format": 1.0,
             "semantic.resnet50": 0.61
           }
         },
         ...
       ]
     }
     │
T7 : frontend
     ├─► render grille thumbnails
     ├─► banner si coverage < 100% sur un critère
     │   "Comparaison sémantique sur 14 lames seulement (embeddings en cours)"
     ├─► tooltip par carte : détail criteria_scores
```

---

## 7. Contrat HTTP

### Requête

```http
POST /api/v1/ml/similar/{slide_id}
Authorization: Bearer <jwt>

Query parameters:
  criteria        : CSV list of criterion IDs (e.g. "tech.vendor,visual.phash")
                    obligatoire, ≥1 valeur, IDs validés contre une liste blanche
  top_k           : int, default 5, max 50
  max_candidates  : int, default 40, max 200 (limite le scan pour la latence)
  aggregation     : "mean" (default) — réservé pour évolution future
```

### Réponse 200

```json
{
  "slide_id": "abc...",
  "criteria_used": ["tech.vendor", "tech.format", "semantic.resnet50"],
  "aggregation": "mean",
  "candidates_scanned": 39,
  "coverage": {
    "tech.vendor": "39/39",
    "tech.format": "39/39",
    "semantic.resnet50": "14/39"
  },
  "results": [
    {
      "slide_id": "xyz...",
      "name": "CMU-2.svs",
      "overview_url": "/api/v1/slides/xyz.../overview",
      "score": 0.87,
      "criteria_scores": {
        "tech.vendor": 1.0,
        "tech.format": 1.0,
        "semantic.resnet50": 0.61
      }
    }
  ],
  "cached": false,
  "computed_at": "2026-05-27T13:45:00Z"
}
```

### Erreurs

| Code | Cause | Message |
|---|---|---|
| 400 | `criteria` vide ou IDs inconnus | "Unknown or empty criteria. Allowed: ..." |
| 401 | Pas de token | "Missing authentication token" |
| 403 | Rôle insuffisant | "Insufficient permissions. Required: MEDECIN, ADMIN_TECHNIQUE" |
| 404 | `slide_id` inexistant ou hors tenant | "Slide not found" |
| 422 | Slide source non lisible (corruption) | "Could not read source slide for fingerprinting" |
| 503 | Tous les scorers ont échoué | "All requested criteria failed (check server logs)" |

---

## 8. Stratégie de cache (D6)

| Aspect | Décision |
|---|---|
| Backend | Redis L2 (réutilise `services/cache/redis_cache.py`) |
| Clé | `similarity:{slide_id}:{sha1(sorted_criteria_csv)}:{top_k}` |
| TTL | 1800 secondes (30 minutes) |
| Granularité | Une entrée par combinaison `(slide source, set de critères, top_k)` |
| Invalidation | TTL naturel uniquement. Pas d'invalidation explicite sur nouvelle annotation — tolérable car les critères workflow évoluent lentement et un refresh manuel suffit. |
| Réponse | Champ `cached: bool` informe le frontend (utile pour debug et pour ne pas re-déclencher de précalcul) |

Justification du TTL : la médiane d'usage d'un panel similarity est probablement courte (le pathologiste fait quelques recherches puis passe à autre chose). 30 min évite le recalcul lors d'allers-retours dans la même session sans encombrer Redis.

---

## 9. Sécurité, RGPD, audit

| Surface | Mesure |
|---|---|
| Filtrage tenant | `WHERE tenant_id = current_user.tenant_id` sur toutes les requêtes SQL. Le scanner filtre aussi en mémoire. |
| RBAC | `Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE"))` — pas accessible aux profils `LECTURE_SEULE` et `INFIRMIER` qui ne sont pas censés faire de recherche cas-comparables. |
| Audit | Chaque appel à `/ml/similar` génère un log audit `READ similarity_search slide={id} criteria={list}` (utile pour suivre les patterns de recherche). |
| Pas d'ID patient renvoyé | Seuls `slide_id`, `name` (filename), `overview_url`. Pas de PII. |
| Coverage transparent | L'utilisateur sait quand sa comparaison est partielle — pas de faux signal de complétude. |

---

## 10. Hors-scope du PoC (roadmap)

Ces éléments sont **volontairement écartés** mais documentés pour le rapport :

1. **Index FAISS pour le scaling** — utile au-delà de quelques centaines de slides. Pour le PoC (~60 slides), un parcours linéaire suffit. Migration triviale : changer `services/ml/similarity.py::semantic_scorer` pour interroger un index pré-construit au lieu de boucler sur `disk_cache`.

2. **Pré-calcul automatique des pHash et color_hist** — pour l'instant calculés à la volée + cachés en RAM. Pour une base plus large, les persister dans une table dédiée (ou même dans Redis avec TTL plus long) éviterait le coût du premier appel.

3. **Pondération configurable des critères** — actuellement moyenne uniforme. Une UI avec sliders par critère est envisageable mais sort du périmètre PoC.

4. **Apprentissage des poids depuis les corrections utilisateur** — possible en exploitant la table `corrections` : si l'utilisateur valide souvent des slides similaires sur le critère `workflow.labels_overlap`, on pourrait booster ce critère. Boucle de feedback intéressante pour une thèse de doctorat, pas pour ce TFE.

5. **Stratégie d'éviction du cache disk_cache embeddings** — pas notre problème ici, mais à terme la table peut grossir indéfiniment (1 fichier `.npy` par (slide, modèle)).

6. **Recherche cross-tenant pour des consultations multicentre** — supposerait un cadre de gouvernance et un opt-in explicite. Hors scope.

---

## 11. Annexes — exemples de requêtes SQL pour les critères workflow

```sql
-- workflow.labels_overlap (Jaccard sur labels distincts présents)
WITH labels_A AS (
    SELECT DISTINCT label_id
    FROM annotations
    WHERE slide_id = :slide_a AND tenant_id = :tenant AND label_id IS NOT NULL
),
labels_B AS (
    SELECT DISTINCT label_id
    FROM annotations
    WHERE slide_id = :slide_b AND tenant_id = :tenant AND label_id IS NOT NULL
)
SELECT
    COALESCE(
        (SELECT COUNT(*) FROM labels_A INNER JOIN labels_B USING (label_id))::float
        / NULLIF((SELECT COUNT(DISTINCT label_id) FROM (
            SELECT label_id FROM labels_A UNION SELECT label_id FROM labels_B) u), 0),
        0.0
    ) AS jaccard;

-- workflow.rejection_pattern (mode des rejection_reason)
SELECT rejection_reason, COUNT(*) AS n
FROM corrections
WHERE slide_id = :slide_id AND tenant_id = :tenant
  AND correction_type = 'rejected'
GROUP BY rejection_reason
ORDER BY n DESC
LIMIT 1;

-- workflow.coview (Jaccard sur view_history.user_sub)
-- analogue à labels_overlap, sur view_history.

-- workflow.annotation_density
SELECT COUNT(*)::float / NULLIF(:slide_area_um2, 0) AS density
FROM annotations
WHERE slide_id = :slide_id AND tenant_id = :tenant;
```

---

## 12. Points ouverts avant implémentation

Aucun bloquant. Le design est figé sur les décisions D1-D8. Implémentation à découper en deux PR :

1. **PR 1 — Backend** : `services/ml/similarity.py` + `routes/ml.py::get_similar_slides` + tests + cache Redis. Aucun impact frontend, l'endpoint retourne déjà JSON consommable.
2. **PR 2 — Frontend** : extension du `SimilarityPanel` avec checkboxes catégoriques + tooltip détail + banner coverage.

Permet de livrer le backend (testable via Swagger) avant de finaliser l'UI.
