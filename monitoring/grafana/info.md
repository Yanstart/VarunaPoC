# grafana

## But
Configuration Grafana pour les dashboards de monitoring et la connexion aux sources de donnees du projet.

## Pourquoi
Visualiser en temps reel les metriques de performance (latence tuiles, taux de cache, utilisation ressources) via des dashboards pre-configures provisionnes automatiquement au demarrage.

## Structure
- `dashboards/` : fichiers JSON des dashboards Grafana (performance WSI, ressources systeme, usage)
- `provisioning/` : configuration de provisioning automatique (datasources et dashboards)
