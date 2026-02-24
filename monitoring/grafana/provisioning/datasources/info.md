# datasources

## But
Configuration YAML de la datasource Prometheus pour Grafana, provisionnee automatiquement au demarrage.

## Pourquoi
Connecter Grafana a Prometheus (http://prometheus:9090) comme source de donnees par defaut, sans configuration manuelle, avec un intervalle de scrape de 5 secondes.

## Structure
- `prometheus.yml` : datasource Prometheus (type proxy, defaut, non editable, methode POST, intervalle 5s)
