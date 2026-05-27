# ML Models Registry — Admin Guide

**Statut :** ✅ Endpoint actif depuis le sprint #370 (migration 010)
**Public cible :** Administrateurs techniques (rôle Keycloak `ADMIN_TECHNIQUE`) responsables du parc de modèles d'IA déployés sur Varuna.

---

## 1. Pourquoi ce registre

Chaque modèle d'IA qui produit des annotations (`auto`, `auto_confirmed`) ou des prédictions doit être **identifié de façon stable** pour :

- Tracer la **provenance** d'une annotation (issue #363 : `annotations.source_model_id`)
- Permettre l'**audit AI Act** art. 12 (logging des décisions algorithmiques)
- Reproduire un **dataset d'entraînement** (issue #365 : `dataset_snapshots.training_dataset_id`)
- Configurer le **routing champion / challenger** (issue #341)
- Vérifier la **conformité de licence** avant déploiement clinique

Le registre est la table `ml_models`. Cette page documente comment l'administrer.

---

## 2. Concepts

### Identité d'un modèle
`(tenant_id, name, version)` — unique. Une fois enregistré, ces trois champs sont **immuables**. Pour changer l'identité, on enregistre un nouveau modèle.

### Tenant scope
- `tenant_id = "global"` → modèle partagé entre tous les établissements (foundation models, modèles publics). **Réservé à `ADMIN_TECHNIQUE`** lors de l'enregistrement.
- `tenant_id = "<slug>"` → modèle privé d'un tenant (modèle entraîné en interne sur des données du CHU).

Un caller voit toujours `(ses modèles privés + les modèles globaux)`.

### Lifecycle
```
registered_at  ──►  deployed_at  ──►  retired_at
   (POST /)         (POST /deploy)      (POST /retire ou DELETE)
```

Une fois `retired_at` posé, la fiche **n'est jamais supprimée** physiquement. Les annotations historiques continuent à pointer vers elle pour l'audit.

### Catégories supportées (Pydantic `TaskType`)
- `feature_extractor` — extraction d'embeddings (Phikon-v2, UNI, ResNet50, etc.) — `embedding_dim` obligatoire
- `classifier` — classification tile/slide
- `detector` — détection de régions
- `segmenter` — segmentation

### Licences supportées (Pydantic `License`)
Orientation 100 % open source — voir l'enum complet dans `backend/schemas/ml_model.py` :

- OSI permissives : `apache-2.0`, `mit`, `bsd-2-clause`, `bsd-3-clause`, `mpl-2.0`
- OSI copyleft : `gpl-2.0`, `gpl-3.0`, `lgpl-3.0`, `agpl-3.0`
- Creative Commons commercial OK : `cc-by-4.0`, `cc-by-sa-4.0`, `cc0-1.0`
- Creative Commons non-commercial (UNI, CONCH) : `cc-by-nc-4.0`, `cc-by-nc-nd-4.0`
- Hugging Face : `openrail`
- Tracking compliance : `proprietary`, `other` (avec `description` obligatoire)

Les champs calculés `commercial_use_allowed` et `open_source` (dans `MLModelOut`) dérivent de la licence — utiles pour les checks d'usage avant déploiement.

---

## 3. Opérations courantes

Toutes les opérations passent par l'API REST sous `/api/v1/ml-models`. La doc Swagger interactive est à https://localhost:8443/api/v1/docs (cliquer sur la section *ML Models Registry*).

### 3.1 Enregistrer un modèle (manuel)

```bash
ADMIN_TOKEN="$(your_token)"
curl -sk -X POST https://localhost:8443/api/v1/ml-models \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-tumor-classifier",
    "version": "1.0.0",
    "framework": "pytorch",
    "architecture": "ResNet50",
    "task_type": "classifier",
    "license": "apache-2.0",
    "checkpoint_uri": "s3://chu-models/tumor-classifier-v1.pt",
    "checkpoint_hash": "sha256-...",
    "mlflow_run_id": "abc123def",
    "mlflow_model_uri": "models:/my-tumor-classifier/Production"
  }'
```

### 3.2 Enregistrer un foundation model (tenant global)

```bash
curl -sk -X POST https://localhost:8443/api/v1/ml-models \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "global",
    "name": "phikon-v2",
    "version": "2025.02",
    "framework": "pytorch",
    "architecture": "ViT-B/16 (Phikon)",
    "task_type": "feature_extractor",
    "embedding_dim": 768,
    "license": "cc-by-nc-nd-4.0",
    "checkpoint_uri": "hf://owkin/phikon-v2"
  }'
```

Tenant `global` est refusé pour tout rôle autre que `ADMIN_TECHNIQUE`.

### 3.3 Bootstrap automatique via le seeder

Pour pré-remplir le registre avec les modèles déjà actifs (au minimum Phikon-v2) :

```bash
docker exec varuna-backend python -m scripts.seed_ml_models
```

Idempotent — re-exécutable sans danger. Insère uniquement ce qui manque.

### 3.4 Lister les modèles

```bash
# Tous (sauf retirés)
curl -sk -H "Authorization: Bearer $TOKEN" \
  https://localhost:8443/api/v1/ml-models

# Filtres
curl -sk -H "Authorization: Bearer $TOKEN" \
  "https://localhost:8443/api/v1/ml-models?task_type=feature_extractor&only_deployed=true"

# Inclure les retirés (pour audit)
curl -sk -H "Authorization: Bearer $TOKEN" \
  "https://localhost:8443/api/v1/ml-models?include_retired=true"
```

### 3.5 Déployer un modèle

```bash
curl -sk -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://localhost:8443/api/v1/ml-models/{model_id}/deploy
```

Idempotent. Pose `deployed_at = NOW()` si pas déjà déployé. Refuse (409) si le modèle est retiré.

### 3.6 Retirer un modèle (soft delete)

```bash
curl -sk -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://localhost:8443/api/v1/ml-models/{model_id}/retire

# ou (équivalent)
curl -sk -X DELETE -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://localhost:8443/api/v1/ml-models/{model_id}
```

Pose `retired_at = NOW()`. La fiche reste lisible pour audit.

### 3.7 Mettre à jour la description / license

```bash
curl -sk -X PATCH -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  https://localhost:8443/api/v1/ml-models/{model_id} \
  -d '{"description": "Updated by Dr Martin after model card v2 review", "license": "apache-2.0"}'
```

**Champs PATCH-ables uniquement** : `framework`, `architecture`, `input_shape`, `embedding_dim`, `checkpoint_hash`, `checkpoint_uri`, `mlflow_*`, `license`, `usage_constraints`, `description`, `metadata_extra`. Les fields d'**identité** (`name`, `version`, `task_type`) sont rejetés silencieusement par Pydantic.

---

## 4. Audit

Chaque opération critique génère un événement audit (table `audit_log`) :

| Endpoint | Event type | Niveau |
|---|---|---|
| `POST /ml-models` | `ML_MODEL_REGISTERED` | INFO |
| `PATCH /ml-models/{id}` | `ML_MODEL_UPDATED` | INFO |
| `POST /ml-models/{id}/deploy` | `ML_MODEL_DEPLOYED` | INFO |
| `POST /ml-models/{id}/retire` | `ML_MODEL_RETIRED` | WARNING |
| `DELETE /ml-models/{id}` | `ML_MODEL_RETIRED` (via alias) | WARNING |

Les événements incluent `resource_type=ml_model`, `resource_id=<uuid>`, `details={name, version, tenant_id, ...}`. L'intégrité de ces audit logs sera renforcée par l'issue #368 (WORM + hash chain).

---

## 5. Bonne hygiène

1. **Toujours déclarer `mlflow_run_id`** quand le modèle vient d'un entraînement tracké MLflow. C'est ce qui permettra à #347 (fine-tuning) et #341 (CI/CD champion/challenger) de reconstituer la chaîne complète.
2. **`checkpoint_hash` = SHA-256** du fichier de poids — utile pour détecter une corruption ou un swap silencieux.
3. **Ne supprimez jamais physiquement** une fiche `ml_models` via raw SQL : les annotations historiques deviendraient orphelines (FK `ON DELETE SET NULL` les préserve, mais perd l'attribution).
4. **`license=other`** doit toujours s'accompagner d'une `description` explicite citant les conditions d'usage — refusé par Pydantic sinon.
5. **Audit régulier** : lister les modèles avec `commercial_use_allowed=false` (champ calculé dans la réponse) et confirmer qu'ils ne sont pas déployés dans des contextes commerciaux.

---

## 6. Références

- Migration : `backend/alembic/versions/010_ml_models.py`
- ORM : `backend/models/ml_model.py`
- Schémas Pydantic : `backend/schemas/ml_model.py`
- Routes : `backend/routes/ml_models.py`
- Seeder : `backend/scripts/seed_ml_models.py`
- Audit gap résolu : G2 de `docs/architecture/ANNOTATION_DATA_MODEL_AUDIT.md`
- Issue : [#370 — ml_models registry table schema](https://github.com/Yanstart/VarunaPoC/issues/370)
- Issues consommatrices (FK target) : #346, #363, #365, #341, #347
