# Opérations — commandes du quotidien

---

## État de la stack

```bash
# Liste les conteneurs actifs et leur état healthy
docker compose --profile prod --profile monitoring ps

# Stats live (CPU/RAM/I/O par service)
docker stats $(docker compose ps -q)

# Quel profil est actif ?
docker compose config --profiles
```

## Logs

```bash
# Logs d'un service
docker compose logs -f backend
docker compose logs --tail=100 keycloak

# Logs de tous les services depuis 1 h
docker compose logs --since 1h

# Logs persistés sur disque
docker volume inspect varuna-backend-logs
```

## Redémarrage / arrêt

```bash
# Redémarrer un service sans toucher aux autres
docker compose restart backend

# Stop tout
docker compose --profile prod --profile monitoring stop

# Stop + suppression conteneurs (volumes intacts)
docker compose --profile prod --profile monitoring down

# Stop + suppression VOLUMES (data loss)
docker compose --profile prod --profile monitoring down -v
```

---

## Backup / restore <a id="backup-restore"></a>

### Sauvegarder PostgreSQL (db)

```bash
docker compose exec -T db \
  pg_dump -U varuna -d varuna -Fc \
  > backup-varuna-$(date +%F).dump
```

### Restaurer

```bash
# La DB doit être vide. Si besoin de la recréer :
docker compose exec db psql -U postgres -c "DROP DATABASE varuna;"
docker compose exec db psql -U postgres -c "CREATE DATABASE varuna OWNER varuna;"

# Restaurer
docker compose exec -T db \
  pg_restore -U varuna -d varuna < backup-varuna-2026-05-07.dump
```

### Sauvegarder Keycloak

Le realm est exporté à chaque modification UI ; mais pour un backup
complet :

```bash
docker compose exec -T keycloak-db \
  pg_dump -U keycloak -d keycloak -Fc \
  > backup-keycloak-$(date +%F).dump
```

### Sauvegarder MLflow + MinIO

```bash
# DB MLflow
docker compose exec -T mlops-db \
  pg_dump -U mlflow -d mlflow -Fc \
  > backup-mlflow-$(date +%F).dump

# MinIO : copier le bucket (ou snapshot du volume)
docker compose exec minio mc mirror /data/mlflow-artifacts /backup/mlflow-artifacts
```

### Sauvegarder les volumes (méthode universelle)

```bash
# Pour chaque volume critique (🔴 dans INFRASTRUCTURE.md)
for vol in varuna-db-data varuna-keycloak-db-data varuna-mlops-db-data varuna-mlops-minio-data; do
  docker run --rm \
    -v "$vol":/data:ro \
    -v "$(pwd)":/backup \
    alpine tar czf "/backup/$vol-$(date +%F).tgz" -C /data .
done
```

---

## Health checks et alertes

Endpoints de healthcheck exposés :

| Service     | URL                                       |
|-------------|-------------------------------------------|
| backend     | `http://localhost:8000/api/v1/health`     |
| nginx       | `http://localhost/health`                 |
| keycloak    | `http://localhost:8180/health/ready`      |
| prometheus  | `http://localhost:9090/-/healthy`         |
| grafana     | `http://localhost:3000/api/health`        |
| mlflow      | `http://localhost:5000/health`            |

Alertes Prometheus : voir `monitoring/alerts/` et la section
[`PROMETHEUS_ALERTS`](../Deployment/MONITORING_GUIDE.md) du guide
monitoring.

---

## Rotation des secrets

Voir [docs/Deployment/SECRET_ROTATION.md](../Deployment/SECRET_ROTATION.md).

---

## Nettoyage

```bash
# Conteneurs arrêtés et images orphelines
docker compose down --remove-orphans
docker image prune -f

# Volumes orphelins (DANGER : data loss)
docker volume prune

# Tout sauf les volumes
docker compose --profile prod --profile monitoring down --rmi local
```

---

## Troubleshooting rapide

| Symptôme                                                  | Diagnostic                                                                                          |
|-----------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| `keycloak` reste `starting` plus de 2 min                | Healthy autour de 90 s. Si > 3 min : `docker compose logs keycloak`. Vérifier `keycloak-db: healthy`. |
| Backend log `redis: Connection refused`                   | Redis pas démarré. Profil `cache` actif ?                                                           |
| Tile request 502/504                                      | nginx → backend : `docker compose logs backend nginx`. Souvent `BACKEND_REPLICAS` insuffisant.     |
| `WS /api/v1/ws/events` se déconnecte sans cesse           | nginx ne propage pas l'upgrade WebSocket. Vérifier `nginx/nginx.conf` `proxy_set_header Upgrade`.   |
| Le frontend dit "Slide not found" alors qu'il existe      | `SLIDES_HOST_PATH` mal monté. `docker compose exec backend ls /slides`.                            |
| HAPI FHIR `ERR_EMPTY_RESPONSE`                            | Cold start ~45 s. Patience. Si persistant : `docker compose logs hapi-fhir`.                       |
| Orthanc accessible mais auth refusée                       | `ORTHANC_USER` / `ORTHANC_PASSWORD` mal alignés avec ce que le backend envoie.                     |
| Prometheus ne scrape pas un service                       | `monitoring/prometheus.yml` doit lister la cible. Voir `http://localhost:9090/targets`.            |

---

## Voir aussi

- [docs/Deployment/PRODUCTION_RUNBOOK.md](../Deployment/PRODUCTION_RUNBOOK.md) — runbook étendu
- [docs/Deployment/BREAKGLASS_PROCEDURE.md](../Deployment/BREAKGLASS_PROCEDURE.md) — accès urgence
- [docs/Deployment/NETWORK_TROUBLESHOOTING.md](../Deployment/NETWORK_TROUBLESHOOTING.md) — réseau
