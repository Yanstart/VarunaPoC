# scripts

## But
Scripts de backup et restore PostgreSQL pour l'environnement de production VarunaPoC.

## Pourquoi
L'equipe IT du CHU a besoin de scripts simples et fiables pour sauvegarder et restaurer la base de donnees PostgreSQL + PostGIS utilisee pour les annotations, labels et rapports qualite. Ces scripts encapsulent les commandes Docker Compose et pg_dump/pg_restore.

## Comment
- `backup.sh` execute `pg_dump` en format custom (-Fc) via `docker compose exec` sur le conteneur `db`
- `restore.sh` arrete le backend, drop/recreate la base, execute `pg_restore`, puis redemarre le backend
- Les deux scripts sourcent `.env.production` pour les credentials (POSTGRES_USER, POSTGRES_DB)
- Les deux utilisent `docker-compose.production.yml` comme fichier compose

## Structure
```
scripts/
  backup.sh       # Sauvegarde timestampee (pg_dump -Fc) dans ./backups/
  restore.sh      # Restauration depuis un fichier .dump avec confirmation
  info.md         # Ce fichier
```
