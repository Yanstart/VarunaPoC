# Fiches services — Admin

Une page par conteneur. Format standardisé : rôle, image, profils, ports,
variables d'env, commandes admin, hardening prod, liens.

## Index

| Service                                  | Profil(s)              | Page                         |
|------------------------------------------|------------------------|------------------------------|
| **Données**                              |                        |                              |
| `db` (PostgreSQL+PostGIS)                | core, dev, prod        | [db.md](./db.md)             |
| `redis` (TileCache L2)                   | cache, dev, prod       | [redis.md](./redis.md)       |
| **Auth**                                 |                        |                              |
| `keycloak` + `keycloak-db`               | auth, dev, prod        | [keycloak.md](./keycloak.md) |
| **Application**                          |                        |                              |
| `backend` (FastAPI)                      | prod                   | [backend.md](./backend.md)   |
| `frontend` (SPA Vite)                    | prod                   | [frontend.md](./frontend.md) |
| `nginx` (reverse proxy)                  | prod                   | [nginx.md](./nginx.md)       |
| `migration` (alembic run-once)           | prod                   | (cf. `backend.md`)           |
| **Intégrations santé (sandbox)**         |                        |                              |
| `orthanc` (PACS DICOM)                   | pacs, dev              | [orthanc.md](./orthanc.md)   |
| `hapi-fhir` (FHIR R4)                    | fhir, dev              | [hapi-fhir.md](./hapi-fhir.md) |
| **Observabilité**                        |                        |                              |
| `prometheus` + `grafana` + `alertmanager` + exporters | monitoring, prod | [monitoring.md](./monitoring.md) |
| **MLOps**                                |                        |                              |
| `mlflow` + `minio` + `minio-init` + `mlops-db` | mlops             | [mlops.md](./mlops.md)        |

## Convention

Chaque fiche service répond aux mêmes questions :

1. **Rôle** : pourquoi ce service existe
2. **Conteneur** : image, port hôte, volume, healthcheck
3. **Variables d'env** : ce qui est configurable
4. **Commandes admin** : logs, restart, accès shell, backup
5. **Désactiver** : comment l'enlever proprement
6. **Hardening prod** : checklist sécurité
7. **Liens** : doc upstream + sources internes

## Voir aussi

- [../README.md](../README.md) — vue d'ensemble admin
- [../INFRASTRUCTURE.md](../INFRASTRUCTURE.md) — topologie + ports
- [../PROFILES.md](../PROFILES.md) — combinaisons profils
- [../DEPLOYMENT.md](../DEPLOYMENT.md) — procédure déploiement
- [../OPERATIONS.md](../OPERATIONS.md) — ops du quotidien
