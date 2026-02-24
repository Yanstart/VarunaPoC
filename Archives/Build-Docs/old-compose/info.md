# old-compose

## But
Archiver les fichiers docker-compose utilises lors des differentes phases de deploiement du projet.

## Pourquoi
Ces fichiers representent l'evolution de l'orchestration Docker, de la validation locale (Phase 1) jusqu'a la production optimisee (Phase 2.5), et servent de reference historique.

## Structure
- `docker-compose.phase1.yml` - Orchestration Phase 1 : deploiement local avec ports standard et slides montes en volume.
- `docker-compose.phase2.1.yml` - Orchestration Phase 2.1 : acces reseau avec slides locales, ports exposes sur toutes les interfaces.
- `docker-compose.phase2.2.yml` - Orchestration Phase 2.2 : production avec montage du partage reseau CHU (anapath_storage_nimble).
- `docker-compose.optimized.yml` - Orchestration Phase 2.5 : configuration production avec Nginx, load balancing, Redis et monitoring.
