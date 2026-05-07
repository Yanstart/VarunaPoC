# Stack monitoring — Prometheus, Grafana, Alertmanager, exporters

Cette page couvre tous les services du profil `monitoring` :

- `prometheus` — collecte et stocke les métriques
- `grafana` — dashboards
- `alertmanager` — routage des alertes (mail, webhook)
- `redis-exporter` — métriques Redis
- `nginx-exporter` — métriques nginx
- `node-exporter` — métriques hôte (CPU, RAM, disque, réseau)
- `cadvisor` — métriques par conteneur

Activation :
```bash
docker compose --profile prod --profile monitoring up -d
```

Pour la stack monitoring SEULE (sur un host dédié observabilité) :
```bash
docker compose --profile monitoring up -d
```

---

## prometheus

| | |
|---|---|
| Image | `prom/prometheus:v2.48.1` |
| Port hôte | `9090` (UI + API), via `PROMETHEUS_HOST_PORT` |
| Volume | `varuna-prometheus-data` 🟡 (rétention `PROMETHEUS_RETENTION`, défaut 30j) |
| Healthcheck | `wget /-/healthy` |

**Config** : `monitoring/prometheus.yml` (montage read-only) + `monitoring/alerts/*`

UI : http://localhost:9090
- `/targets` — liste des cibles scrapées et leur état
- `/alerts` — alertes actives
- `/graph` — explorateur PromQL

```bash
# Recharger la config sans downtime (si --web.enable-lifecycle activé)
docker compose kill -s SIGHUP prometheus
```

## grafana

| | |
|---|---|
| Image | `grafana/grafana:10.2.3` |
| Port hôte | `3000` |
| Volume | `varuna-grafana-data` 🟡 (dashboards perso, alerting) |
| Plugin | `redis-datasource` (auto-installé) |

UI : http://localhost:3000
Login initial : `${GRAFANA_ADMIN_USER}` / `${GRAFANA_ADMIN_PASSWORD}`
(défauts `admin`/`admin` à changer en prod).

Dashboards provisionnés depuis `monitoring/grafana/dashboards/` (read-only
mount). Datasources depuis `monitoring/grafana/datasources/`.

## alertmanager

| | |
|---|---|
| Image | `prom/alertmanager:v0.26.0` |
| Port hôte | `9093` |
| Volume | `varuna-alertmanager-data` 🟢 |

**Config** : `monitoring/alertmanager.yml` (routes, receivers).
Templates : `monitoring/alert-templates.tmpl`.

Pour configurer un receiver SMTP / Slack : éditer `alertmanager.yml`,
puis `docker compose restart alertmanager`.

## Exporters

| Service          | Image                                       | Cible scrapée                           |
|------------------|---------------------------------------------|-----------------------------------------|
| `redis-exporter` | `oliver006/redis_exporter:v1.55.0-alpine`   | `redis:6379` (auth via `REDIS_PASSWORD`)|
| `nginx-exporter` | `nginx/nginx-prometheus-exporter:1.0.0`     | `nginx:80/nginx_status`                 |
| `node-exporter`  | `prom/node-exporter:v1.7.0`                 | `/proc`, `/sys`, `/` (read-only)        |
| `cadvisor`       | `gcr.io/cadvisor/cadvisor:v0.47.0`          | Docker socket + cgroups                 |

Aucun de ces exporters n'expose un port hôte ; tous sont scrapés en
interne par Prometheus.

---

## Métriques applicatives

Le backend Varuna expose `/metrics` (Prometheus exposition format) avec
notamment :

| Métrique                                          | Type      | Description                                   |
|---------------------------------------------------|-----------|-----------------------------------------------|
| `varuna_tile_cache_hits_total{level}`             | Counter   | Hits L1/L2 du TileCache                       |
| `varuna_tile_cache_misses_total{level}`           | Counter   | Misses                                        |
| `varuna_tile_cache_lookup_seconds{outcome}`       | Histogram | Latence lookup cache                          |
| `varuna_tile_load_seconds`                        | Histogram | Temps de production d'une tuile (cache miss)  |
| `varuna_workflow_events_total{event_type, hook_type, status}` | Counter | Événements workflow émis par les hooks |
| `varuna_ml_inference_seconds{model}`              | Histogram | Latence inférence ML                           |

Voir aussi le dashboard `Varuna Application` dans Grafana.

---

## Hardening prod

- Tous les ports admin (9090, 3000, 9093) bind sur `127.0.0.1` ou
  derrière nginx avec auth — utiliser un override file
  (`docker-compose.hospital.yml`)
- `GRAFANA_ADMIN_PASSWORD` 32+ chars
- Backup périodique de `varuna-prometheus-data` et
  `varuna-grafana-data` (dashboards créés dans l'UI = perdus si volume KO)
- Configurer un receiver Alertmanager fonctionnel (au minimum un mail
  d'astreinte)

## Liens

- [docs/Deployment/MONITORING_GUIDE.md](../../Deployment/MONITORING_GUIDE.md)
- `monitoring/` — toute la config (prometheus, grafana, alertmanager)
- [Prometheus operating](https://prometheus.io/docs/prometheus/latest/management_api/)
