# Build-Docs

## But
Documentation des configurations Docker et des differences de build entre les phases de deploiement du projet VarunaPoC.

## Pourquoi
Conserver la trace des choix de build (Phase 1 localhost, Phase 2.1 reseau, Linux) et l'inventaire des fichiers Docker crees, pour reference lors d'evolutions futures.

## Structure
- `BUILD_DIFFERENCES.md` - Comparaison des configurations de build entre Phase 1, Phase 2.1 et Linux (ports, CORS, chemins).
- `DOCKER_FILES_SUMMARY.md` - Inventaire complet des 13 fichiers Docker crees pour la Phase 1 (Dockerfiles, .env, scripts).
- `old-compose/` - Sous-dossier contenant les anciens fichiers docker-compose par phase.
