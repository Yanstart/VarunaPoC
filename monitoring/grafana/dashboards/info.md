# dashboards

## But
Fichiers JSON des dashboards Grafana pre-configures pour le monitoring de VarunaPoC.

## Pourquoi
Fournir des dashboards prets a l'emploi au demarrage de Grafana, sans configuration manuelle, couvrant la performance WSI, les ressources systeme et l'utilisation.

## Structure
- `dashboard.yml` : configuration de provisioning locale des dashboards
- `varuna-wsi-performance.json` : dashboard de performance WSI (latence tuiles, taux de cache, erreurs)
- `wsi-performance-dashboard.json` : dashboard detaille de performance des lames
- `wsi-usage-dashboard.json` : dashboard d'utilisation (sessions, requetes, formats)
- `system-resources-dashboard.json` : dashboard des ressources systeme (CPU, memoire, disque)
