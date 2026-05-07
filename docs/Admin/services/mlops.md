# Stack MLOps — MLflow, MinIO, mlops-db

Cette page couvre tous les services du profil `mlops` :

- `mlflow` — tracking server (UI + API)
- `minio` — stockage S3-compatible pour les artefacts
- `minio-init` — bootstrap des buckets (run-once)
- `mlops-db` — PostgreSQL pour le backend MLflow

Pas activé par défaut. Activation :
```bash
docker compose --profile mlops up -d                # MLOps seul
docker compose --profile prod --profile mlops up -d # Sur le host applicatif (déconseillé)
```

Recommandé : héberger MLOps sur un **hôte séparé** de l'applicatif prod.
Le backend Varuna log vers MLflow via `MLFLOW_TRACKING_URI`.

---

## mlflow

| | |
|---|---|
| Image | `ghcr.io/mlflow/mlflow:v2.16.2` |
| Port hôte | `5000` (UI + API) |
| Healthcheck | `curl /health` |

**Backend store** : `postgresql://mlflow@mlops-db:5432/mlflow`
**Artifact root** : `s3://mlflow-artifacts` (sur MinIO)

UI : http://localhost:5000
- Expériences, runs, métriques, paramètres
- Model Registry pour le promotion staging → production

## minio

| | |
|---|---|
| Image | `minio/minio:RELEASE.2024-10-02T17-50-41Z` |
| Ports hôte | `9000` (S3 API), `9001` (UI Console) |
| Volume | `varuna-mlops-minio-data` 🔴 (artefacts modèles, datasets) |
| Healthcheck | `curl /minio/health/live` |

UI Console : http://localhost:9001
Login : `${MINIO_ROOT_USER}` / `${MINIO_ROOT_PASSWORD}` (défauts `varuna-admin`/`varuna_dev`).

Buckets :
- `mlflow-artifacts` — artefacts MLflow (modèles, plots, …)
- `varuna-ml-data` — datasets versionnés (DVC remote)

## minio-init

Container one-shot. Au démarrage de la stack `mlops` :
- Configure l'alias `mc` pour pointer sur `minio:9000`
- Crée `mlflow-artifacts` et `varuna-ml-data` s'ils n'existent pas
- Exit 0

Si on a besoin d'un troisième bucket : éditer l'`entrypoint` dans le
compose ou faire la création via UI MinIO.

## mlops-db

| | |
|---|---|
| Image | `postgres:16-alpine` |
| Volume | `varuna-mlops-db-data` 🔴 (metadata MLflow, runs, métriques) |
| Pas de port hôte exposé |

---

## Variables d'env

| Variable                  | Défaut                  | Rôle                                       |
|---------------------------|-------------------------|--------------------------------------------|
| `MLFLOW_HOST_PORT`        | `5000`                  | Port mappé MLflow                          |
| `MINIO_HOST_PORT`         | `9000`                  | Port S3                                    |
| `MINIO_CONSOLE_HOST_PORT` | `9001`                  | Port UI Console                            |
| `MINIO_ROOT_USER`         | `varuna-admin`          | User root MinIO                            |
| `MINIO_ROOT_PASSWORD`     | `varuna_dev`            | Mot de passe (32+ chars en prod)           |
| `MLOPS_DB_PASSWORD`       | `mlops_dev`             | Mot de passe PostgreSQL                    |

## Intégration backend Varuna

Le backend (en prod) loggue les inférences ML :

```env
MLFLOW_TRACKING_URI=http://mlflow.example:5000
MLFLOW_S3_ENDPOINT_URL=http://minio.example:9000
AWS_ACCESS_KEY_ID=${MINIO_ROOT_USER}
AWS_SECRET_ACCESS_KEY=${MINIO_ROOT_PASSWORD}
```

Côté Python : `mlflow.log_metric(...)`, `mlflow.log_artifact(...)`.
Côté DVC : `dvc remote add -d minio s3://varuna-ml-data` puis
`dvc remote modify minio endpointurl http://minio.example:9000`.

## Désactiver

Pas de flag — il suffit de ne pas activer le profil. La stack n'a aucun
impact sur le reste si elle ne tourne pas.

## Hardening prod

- `MINIO_ROOT_PASSWORD` ET `MLOPS_DB_PASSWORD` 32+ chars distincts
- Ne PAS exposer 5000/9000/9001 sur Internet ouvert ; mettre derrière un
  proxy avec auth, ou les binder sur LAN admin
- Backup chiffré de `varuna-mlops-minio-data` (modèles entraînés —
  perte = ré-entraînement)
- Si la pipeline est partagée entre équipes, configurer des credentials
  séparés (MinIO IAM users)

## Liens

- [MLflow docs](https://mlflow.org/docs/2.16.2/)
- [MinIO docs](https://min.io/docs/)
- [DVC docs](https://dvc.org/doc)
- `Archives/Phase3-Planning/` — design pipeline ré-entraînement
