# Manuel Administrateur — VarunaPoC

**Public** : opérateur·rices, équipe IT hôpital, SRE, devops.
**Pas le manuel utilisateur** — pour l'utilisation depuis le navigateur, voir
[`docs/Manuel/`](../Manuel/).

Ce manuel décrit comment **déployer, opérer et maintenir** l'infrastructure
VarunaPoC. Tout passe par un seul fichier `docker-compose.yml` à la racine,
piloté par des **profils Docker Compose** (un profil = un module).

---

## Index

| Document | Pour quoi |
|---|---|
| [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) | Topologie réseau, matrice ports/rôles, vue d'ensemble des conteneurs |
| [PROFILES.md](./PROFILES.md) | Quand activer/désactiver chaque profil, combinaisons recommandées |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Procédure complète de déploiement (dev, prod, hôpital), pré-requis hardware |
| [OPERATIONS.md](./OPERATIONS.md) | Commandes du quotidien (logs, backup, restore, upgrade, troubleshooting) |
| [services/](./services/) | Une page par conteneur : rôle, dépendances, ports, ops basiques |

Documents historiques toujours utiles (déploiement spécifique CHU,
break-glass, secrets management) :
[`docs/Deployment/`](../Deployment/).

---

## Démarrage rapide

### Workstation dev

```bash
cp .env.dev.example .env
docker compose --profile dev up -d
```

Lance : `db` + `redis` + `keycloak` (+ DB) + `orthanc` + `hapi-fhir`.
Le backend et le frontend tournent en local (`uvicorn`, `npm run dev`).

### Hôte de production

```bash
cp .env.prod.example .env
# Remplacer chaque "CHANGE_ME_*" par une valeur forte
docker compose --profile prod --profile monitoring up -d
```

Lance la stack complète : `db` + `migration` + `backend` (réplicat) +
`frontend` + `nginx` + `redis` + `keycloak` + Prometheus/Grafana/Alertmanager
+ exporters.

### Modules optionnels

```bash
# Ajouter le pipeline MLOps
docker compose --profile prod --profile monitoring --profile mlops up -d

# Sandbox PACS DICOM (Orthanc) sur un poste de test
docker compose --profile dev --profile pacs up -d
```

Voir [PROFILES.md](./PROFILES.md) pour la liste exhaustive et les
combinaisons.

---

## Vue d'ensemble — services et profils

| Service          | Profil(s)              | Rôle                                   | Port hôte (défaut) |
|------------------|------------------------|----------------------------------------|--------------------|
| `db`             | `core, dev, prod`      | PostgreSQL+PostGIS — annotations, audit | 5433 (dev) / 5432 (prod) |
| `redis`          | `cache, dev, prod`     | TileCache L2 — cache distribué tuiles  | 6380 (dev) / 6379 (prod) |
| `keycloak`       | `auth, dev, prod`      | OIDC IdP                               | 8180               |
| `keycloak-db`    | `auth, dev, prod`      | DB Keycloak                            | (interne)          |
| `orthanc`        | `pacs, dev`            | Sandbox PACS DICOM                     | 4242 / 8042        |
| `hapi-fhir`      | `fhir, dev`            | Sandbox FHIR R4                        | 8090               |
| `migration`      | `prod`                 | `alembic upgrade head` (run-once)     | (pas de port)      |
| `backend`        | `prod`                 | API FastAPI                            | (interne, via nginx) |
| `frontend`       | `prod`                 | SPA Vite                               | (interne, via nginx) |
| `nginx`          | `prod`                 | Reverse proxy + TLS                    | 80 / 443           |
| `prometheus`     | `monitoring, prod`     | Métriques                              | 9090               |
| `grafana`        | `monitoring, prod`     | Dashboards                             | 3000               |
| `alertmanager`   | `monitoring, prod`     | Routage des alertes                    | 9093               |
| `redis-exporter` | `monitoring, prod`     | Métriques Redis                        | (interne)          |
| `nginx-exporter` | `monitoring, prod`     | Métriques nginx                        | (interne)          |
| `node-exporter`  | `monitoring, prod`     | Métriques hôte                         | (interne)          |
| `cadvisor`       | `monitoring, prod`     | Métriques conteneurs                   | (interne)          |
| `mlflow`         | `mlops`                | Tracking expériences ML                | 5000               |
| `minio`          | `mlops`                | Stockage S3 (artefacts ML)             | 9000 / 9001        |
| `minio-init`     | `mlops`                | Bootstrap buckets MinIO (one-shot)     | (pas de port)      |
| `mlops-db`       | `mlops`                | DB PostgreSQL pour MLflow              | (interne)          |

Détail des ports, des dépendances, et des healthchecks dans
[INFRASTRUCTURE.md](./INFRASTRUCTURE.md). Chaque service a sa propre fiche
sous [`services/`](./services/).
