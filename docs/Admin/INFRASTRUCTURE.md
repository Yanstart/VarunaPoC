# Infrastructure & Topologie réseau

**Audience** : opérateurs, IT hôpital. Décrit ce qui tourne, sur quels ports,
qui parle à qui.

---

## Schéma logique

```
                                  ┌──────────────────────────────────────────┐
                                  │            Hôte Docker (Linux)            │
                                  │                                          │
   Navigateur clinicien           │   ┌──────────┐                            │
   https://varuna ─ TLS ────────► │   │  nginx   │ 80/443                     │
                                  │   └────┬─────┘                            │
                                  │        │                                  │
                                  │   ┌────┴────┐    ┌───────────┐           │
                                  │   │ backend │───►│ frontend  │           │
                                  │   │ (x N)   │    └───────────┘           │
                                  │   └────┬────┘                            │
                                  │        │                                  │
                                  │   ┌────┴───┬──────────┬──────────┐       │
                                  │   ▼        ▼          ▼          ▼       │
                                  │  ┌──┐    ┌────┐    ┌──────┐  ┌──────┐   │
                                  │  │db│    │redis│   │keycloak│ hapi-fhir│ │
                                  │  └──┘    └────┘    └────┬─┘  └──────┘   │
                                  │                          │               │
                                  │                     ┌────┴───┐           │
                                  │                     │keycloak│           │
                                  │                     │  -db   │           │
                                  │                     └────────┘           │
                                  │                                          │
                                  │   monitoring/    mlops/    pacs/         │
                                  │   prometheus     mlflow    orthanc       │
                                  │   grafana        minio                   │
                                  │   alertmanager   mlops-db                │
                                  │   exporters      minio-init              │
                                  └──────────────────────────────────────────┘
                                                │
                                                ▼ (prod, hospital integrations)
                          ┌─────────────────────────┐  ┌────────────────────┐
                          │ PACS hôpital (DICOM)    │  │ FHIR hôpital (DPI) │
                          │ ${PACS_HOST}            │  │ ${FHIR_BASE_URL}   │
                          └─────────────────────────┘  └────────────────────┘
```

En production, `orthanc` et `hapi-fhir` ne tournent **pas** : `PACS_HOST` et
`FHIR_BASE_URL` pointent directement vers les serveurs hospitaliers
existants.

---

## Réseau Docker

Tous les services partagent un seul bridge `varuna-network` (driver
`bridge`, nom externe `varuna-network`). La résolution se fait par nom de
service : `redis`, `db`, `keycloak`, etc. Le backend lit
`REDIS_URL=redis://redis:6379` — `redis` est résolu par le DNS interne
Docker.

**Pourquoi un seul réseau** (et pas la séparation `auth-network`/`monitoring-network`
qu'on avait dans `docker-compose.production.yml`) ? Le compose unifié
privilégie la lisibilité ; le besoin d'isolation réseau au CHU est satisfait
par un override file (voir [DEPLOYMENT.md](./DEPLOYMENT.md) section
*"Hardening prod hospital"*) plutôt que par la complexité du fichier de
base.

---

## Matrice ports / rôles

Tous les ports listés sont les **ports hôte par défaut** ; tous configurables
par variable d'env (voir `.env.dev.example` et `.env.prod.example`).

### Exposés au monde extérieur

Toujours derrière TLS via nginx en production. En dev, accessibles sur
localhost uniquement.

| Port | Service     | Protocole | Rôle                                    | Variable d'env             |
|------|-------------|-----------|-----------------------------------------|----------------------------|
| 80   | nginx       | HTTP      | Redirige vers 443 (prod)                | `HTTP_PORT`                |
| 443  | nginx       | HTTPS     | UI clinicien + API                      | `HTTPS_PORT`               |
| 8180 | keycloak    | HTTP      | OIDC console + endpoints                | `KEYCLOAK_HOST_PORT`       |

### Exposés sur localhost (dev) ou LAN admin (prod)

| Port | Service        | Rôle                                                        | Variable                     |
|------|----------------|-------------------------------------------------------------|------------------------------|
| 5433 | db             | PostgreSQL — accès admin via `psql`                         | `POSTGRES_HOST_PORT`         |
| 6380 | redis          | Redis CLI / debug                                           | `REDIS_HOST_PORT`            |
| 8042 | orthanc        | Orthanc HTTP REST + UI                                      | `ORTHANC_HTTP_HOST_PORT`     |
| 4242 | orthanc        | Orthanc DICOM (C-FIND/C-STORE/C-ECHO)                       | `ORTHANC_DICOM_HOST_PORT`    |
| 8090 | hapi-fhir      | FHIR R4 + UI                                                | `FHIR_HOST_PORT`             |
| 9090 | prometheus     | UI Prometheus + API métriques                               | `PROMETHEUS_HOST_PORT`       |
| 3000 | grafana        | Dashboards                                                  | `GRAFANA_HOST_PORT`          |
| 9093 | alertmanager   | UI Alertmanager                                             | `ALERTMANAGER_HOST_PORT`     |
| 5000 | mlflow         | Tracking server UI + API                                    | `MLFLOW_HOST_PORT`           |
| 9000 | minio          | API S3                                                      | `MINIO_HOST_PORT`            |
| 9001 | minio          | Console MinIO                                               | `MINIO_CONSOLE_HOST_PORT`    |

### Internes (réseau Docker uniquement)

Pas de mapping vers l'hôte. Accessibles uniquement entre services :
`backend:8000`, `frontend:80`, `keycloak-db:5432`, `mlops-db:5432`,
`redis-exporter:9121`, `nginx-exporter:9113`, `node-exporter:9100`,
`cadvisor:8080`.

---

## Volumes

Données persistantes. Backup régulier indispensable pour les marqués 🔴.

| Volume                        | Service        | Contenu                                | Criticité |
|-------------------------------|----------------|----------------------------------------|-----------|
| `varuna-db-data`              | db             | Annotations, users, audit, sessions    | 🔴       |
| `varuna-keycloak-db-data`     | keycloak-db    | Realm, users, sessions OIDC            | 🔴       |
| `varuna-redis-data`           | redis          | Cache (reconstructible)                | 🟢       |
| `varuna-orthanc-data`         | orthanc        | DICOM dev (sandbox uniquement)         | 🟡       |
| `varuna-hapi-data`            | hapi-fhir      | Ressources FHIR dev (sandbox)          | 🟡       |
| `varuna-backend-logs`         | backend        | Journaux applicatifs                   | 🟡       |
| `varuna-nginx-cache`          | nginx          | Cache tuiles HTTP                      | 🟢       |
| `varuna-prometheus-data`      | prometheus     | Métriques (rétention 30j prod)         | 🟡       |
| `varuna-grafana-data`         | grafana        | Dashboards, datasources                | 🟡       |
| `varuna-alertmanager-data`    | alertmanager   | État des silences/inhibitions          | 🟢       |
| `varuna-mlops-db-data`        | mlops-db       | MLflow metadata (runs, métriques ML)   | 🔴       |
| `varuna-mlops-minio-data`     | minio          | Artefacts modèles, datasets versionnés | 🔴       |

Procédure de backup : [OPERATIONS.md](./OPERATIONS.md#backup-restore).

---

## Dépendances de démarrage

Les `depends_on` du compose imposent :
- `keycloak` attend `keycloak-db: service_healthy`
- `migration` attend `db: service_healthy`
- `backend` attend `migration: service_completed_successfully` ET
  `redis: service_healthy`
- `nginx` attend `backend: service_healthy` ET `frontend: service_healthy`
- `mlflow` attend `mlops-db: service_healthy` ET
  `minio-init: service_completed_successfully`
- exporters et `prometheus` attendent leurs cibles correspondantes

Cold start typique d'un déploiement complet `prod + monitoring` :
~2–3 minutes (Keycloak met ~90 s à devenir healthy).

---

## Healthchecks et liveness

Chaque service expose un healthcheck adapté à son protocole. Récapitulatif :

| Service        | Probe                                   | Intervalle |
|----------------|-----------------------------------------|------------|
| db             | `pg_isready`                            | 10 s       |
| redis          | `redis-cli ping`                        | 10 s       |
| keycloak       | TCP socket + `/health/ready`            | 15 s       |
| backend        | `curl /api/v1/health`                   | 10 s       |
| frontend       | `wget /`                                | 10 s       |
| nginx          | `wget /health`                          | 10 s       |
| orthanc        | `Orthanc --version` (image distroless)  | 30 s       |
| hapi-fhir      | **désactivé** (image distroless)        | —          |
| prometheus     | `wget /-/healthy`                       | 30 s       |
| grafana        | `wget /api/health`                      | 30 s       |
| mlflow         | `curl /health`                          | 15 s       |
| minio          | `curl /minio/health/live`               | 10 s       |

`hapi-fhir` n'a pas de healthcheck Docker (image distroless sans shell). En
prod, le surveiller depuis l'extérieur (Prometheus blackbox-exporter ou
sonde du load balancer).

---

## Ressources matérielles recommandées

| Profil                                       | RAM minimale | RAM recommandée | CPU       | Disque  |
|----------------------------------------------|--------------|-----------------|-----------|---------|
| `dev`                                        | 4 Go         | 8 Go            | 2 cœurs   | 20 Go   |
| `prod` (sans monitoring)                     | 8 Go         | 16 Go           | 4 cœurs   | 100 Go  |
| `prod + monitoring`                          | 12 Go        | 16 Go           | 4 cœurs   | 200 Go  |
| `prod + monitoring + mlops`                  | 24 Go        | 32 Go           | 8 cœurs   | 500 Go  |
| `prod + monitoring + mlops + ML training GPU`| 32 Go        | 64 Go           | 8 cœurs + GPU NVIDIA | 1 To  |

Voir [DEPLOYMENT.md](./DEPLOYMENT.md#hardware) pour les détails GPU et le
stockage des lames (~60 Go pour le dataset de test, plusieurs To en prod).
