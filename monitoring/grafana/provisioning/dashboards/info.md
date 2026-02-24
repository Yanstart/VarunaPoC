# dashboards

## But
Configuration YAML du fournisseur de dashboards Grafana pour le chargement automatique depuis le systeme de fichiers.

## Pourquoi
Permettre a Grafana de charger automatiquement les dashboards JSON du projet sans intervention manuelle, avec mise a jour toutes les 10 secondes.

## Structure
- `dashboard-provider.yml` : provider "VarunaPoC Dashboards" pointant vers /var/lib/grafana/dashboards, avec structure de dossiers activee
