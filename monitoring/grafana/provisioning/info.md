# provisioning

## But
Configuration de provisioning automatique Grafana pour charger dashboards et datasources au demarrage.

## Pourquoi
Eliminer la configuration manuelle de Grafana en provisionnant automatiquement la source de donnees Prometheus et les dashboards du projet via des fichiers YAML.

## Structure
- `dashboards/` : configuration du fournisseur de dashboards (chemin, intervalle de mise a jour)
- `datasources/` : configuration de la datasource Prometheus (URL, methode, intervalle)
