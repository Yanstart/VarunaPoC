# backend — FastAPI API

## Rôle

Cœur applicatif. Sert tuiles WSI, annotations, ML, FHIR, DICOM, audit. C'est
le service que `nginx` proxy en `/api/v1/*`.

## Conteneur

| | |
|---|---|
| Image | `${BACKEND_IMAGE}:${BACKEND_IMAGE_TAG}` (default `ghcr.io/yanstart/varunapoc/backend:main`) |
| Profils | `prod` (en dev = `uvicorn` local) |
| Port interne | `8000` |
| Port hôte | aucun (passe par `nginx`) |
| Volumes | `./Slides:/slides:ro`, `varuna-backend-logs:/app/logs` |
| Healthcheck | `curl /api/v1/health` toutes les 10 s |
| Replicas | `BACKEND_REPLICAS` (défaut 1, 2 en prod recommandé) |

## Variables d'env

| Variable                          | Défaut                                       | Rôle                                                       |
|-----------------------------------|----------------------------------------------|------------------------------------------------------------|
| `BACKEND_IMAGE`                   | `ghcr.io/yanstart/varunapoc/backend`         | Registre/image                                             |
| `BACKEND_IMAGE_TAG`               | `main`                                       | Tag (pinner sur release en prod)                           |
| `BACKEND_REPLICAS`                | `1`                                          | Nombre de réplicas                                         |
| `DATABASE_URL`                    | `postgresql+asyncpg://...@db:5432/varuna`    | Construite à partir de `POSTGRES_*`                        |
| `REDIS_URL`                       | `redis://redis:6379` (auth opt.)             | TileCache L2                                               |
| `SLIDES_REPOSITORY_PATH`          | `/slides`                                    | Mount des lames (read-only)                                |
| `LOG_LEVEL`                       | `info`                                       | `debug`/`info`/`warning`                                   |
| `UVICORN_WORKERS`                 | `2`                                          | Nb. workers async                                          |
| `CORS_ORIGINS`                    | `http://localhost:5173`                      | Liste séparée par virgule                                  |
| `AUTH_ENABLED`                    | `true`                                       | `false` = mode anonyme (dev)                               |
| `OIDC_ISSUER_URL`                 | `http://keycloak:8080/realms/varuna`         | Endpoint OIDC pour validation JWT                          |
| `ML_ENABLED`                      | `true`                                       | Désactive endpoints `/api/v1/ml/*` si `false`              |
| `ML_PROVIDER`                     | `slideflow`                                  | `slideflow`/`mock`/`openslide`                             |
| `ML_WORKER_BACKEND`               | `subprocess`                                 | `subprocess`/`inprocess`/`triton` (Sprint 11)              |
| `TILE_CACHE_L2_ENABLED`           | `true`                                       | `false` = L1 mémoire seul                                  |
| `FHIR_ENABLED`                    | `false`                                      | Active `FHIRWorkflowHook`                                  |
| `FHIR_BASE_URL`                   | `http://hapi-fhir:8080/fhir`                 | Endpoint FHIR (sandbox ou hôpital)                         |
| `PACS_ENABLED`                    | `false`                                      | Active `PACSWorkflowHook`                                  |
| `PACS_HOST`                       | `orthanc`                                    | Sandbox ; en prod, FQDN PACS hôpital                       |
| `WORKFLOW_WS_BROADCAST_ENABLED`   | `true`                                       | Active broadcast WebSocket (Sprint 15)                     |

Liste exhaustive : voir `backend/.env.example`.

## Endpoints clés

| Endpoint                     | Rôle                                        |
|------------------------------|---------------------------------------------|
| `/api/v1/health`             | Liveness (200 OK si DB joignable)           |
| `/api/v1/slides`             | Liste lames                                 |
| `/api/v1/slides/{id}/tiles`  | Stream tuiles WSI                           |
| `/api/v1/annotations/*`      | CRUD + reject + batch                       |
| `/api/v1/ml/*`               | Detect / predict / heatmap (via MLWorker)   |
| `/api/v1/exports/dicom/*`    | Export DICOM SR                             |
| `/api/v1/quality/*`          | Métriques inter-annotateurs                 |
| `/api/v1/ws/events`          | WebSocket workflow events (Sprint 15)       |
| `/metrics`                   | Prometheus exposition                       |
| `/docs`                      | Swagger UI                                  |
| `/redoc`                     | ReDoc                                       |

## Commandes admin

```bash
# Logs
docker compose logs -f backend

# Restart sans toucher aux autres
docker compose restart backend

# Migration DB manuelle (run-once)
docker compose run --rm migration

# Accès shell
docker compose exec backend bash

# Test endpoint
curl -fsS http://localhost:8000/api/v1/health  # via nginx en prod : curl https://.../api/v1/health
```

## Désactiver des modules

Le backend lit les feature flags au démarrage (`backend/core/feature_flags.py`).
Désactiver = setter `*_ENABLED=false` dans `.env`. Liste des flags :

- `AUTH_ENABLED`
- `ML_ENABLED`
- `FHIR_ENABLED`
- `PACS_ENABLED`
- `TILE_CACHE_L2_ENABLED`
- `QUALITY_ENABLED`
- `WORKFLOW_WS_BROADCAST_ENABLED`

Au démarrage, le backend log :
```
Feature flags enabled: annotations, ml, processing, ...
```

## Hardening prod

- Pinner `BACKEND_IMAGE_TAG` sur un tag de release (pas `main`)
- `BACKEND_REPLICAS=2` minimum (haute dispo)
- `UVICORN_WORKERS=4` pour 4–8 cœurs
- `LOG_LEVEL=info` (pas `debug`)
- `CORS_ORIGINS` strictement la liste des domaines autorisés
- `AUTH_ENABLED=true` obligatoire

## Liens

- `backend/main.py` — point d'entrée
- `backend/.env.example` — variables exhaustives
- `docs/architecture/MODULAR_ARCHITECTURE.md` — Protocols + sprints
