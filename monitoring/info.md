# monitoring

## But
Stack d'observabilite: Prometheus (metriques) + Grafana (dashboards) + alertes. Surveille les performances du viewer et l'infrastructure.

## Pourquoi
Indispensable en milieu hospitalier: temps de reponse des tuiles, charge serveur, disponibilite. Permet de detecter les degradations avant impact clinique.

## Comment
- Prometheus scrape le backend toutes les 5s (`/metrics`)
- Grafana provisionne automatiquement les dashboards et datasources au demarrage
- Alertes definies en YAML (latence, erreurs, ressources systeme)

## Structure
```
monitoring/
  prometheus.yml               # Config Prometheus (scrape intervals, jobs, labels CHU UCL Namur)
  alerts/
    varuna-alerts.yml          # Regles d'alerte (response time, tile failures, DB, resources)
  grafana/
    dashboards/                # 4 dashboards JSON (WSI perf, usage, system resources)
      dashboard.yml            # Config provisioning auto
    provisioning/
      dashboards/              # Provider config (auto-load dashboards)
      datasources/             # Config Prometheus datasource (source canonique)
```
