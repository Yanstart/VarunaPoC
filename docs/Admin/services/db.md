# db — PostgreSQL + PostGIS

## Rôle

Base de données primaire de VarunaPoC. Stocke :
- Annotations (geometries via PostGIS)
- Audit trail
- Sessions utilisateurs (roaming cross-workstation)
- Quality reports (cache JSONB)
- Users / labels / workflows

C'est le **service le plus critique** : sa perte = perte de toutes les
données cliniques produites.

## Conteneur

| | |
|---|---|
| Image | `postgis/postgis:16-3.4` |
| Profils | `core`, `dev`, `prod` |
| Port hôte | `5433` (dev) / `5432` (prod), via `POSTGRES_HOST_PORT` |
| Port interne | `5432` |
| Volume | `varuna-db-data` 🔴 critique |
| Healthcheck | `pg_isready` toutes les 10 s |

## Variables d'env

| Variable             | Défaut       | Rôle                            |
|----------------------|--------------|---------------------------------|
| `POSTGRES_DB`        | `varuna`     | Nom de la base                  |
| `POSTGRES_USER`      | `varuna`     | Utilisateur applicatif          |
| `POSTGRES_PASSWORD`  | `varuna_dev` | Mot de passe (changer en prod)  |
| `POSTGRES_HOST_PORT` | `5433`       | Port mappé sur l'hôte           |

## Schéma

Migrations gérées par Alembic dans `backend/alembic/versions/`.
Le service `migration` exécute `alembic upgrade head` au démarrage prod ;
en dev, lancer manuellement :

```bash
cd backend && alembic upgrade head
```

## Connexion admin

```bash
# Via le conteneur
docker compose exec db psql -U varuna -d varuna

# Via psql client local (host port)
psql -h localhost -p 5433 -U varuna -d varuna
```

## Backup / restore

Voir [OPERATIONS.md#backup-restore](../OPERATIONS.md#backup-restore).

```bash
docker compose exec -T db pg_dump -U varuna -d varuna -Fc > backup.dump
```

## Hardening prod

- Mot de passe fort (32+ caractères aléatoires)
- Ne PAS exposer `5432` en dehors du LAN admin (variable
  `POSTGRES_HOST_PORT` pointée sur 127.0.0.1 dans un override)
- Backup off-host quotidien
- Réplication asynchrone vers une standby si DRP requis

## Liens

- [Manuel Postgres 16](https://www.postgresql.org/docs/16/)
- [PostGIS](https://postgis.net/docs/)
- [INFRASTRUCTURE.md](../INFRASTRUCTURE.md) — table volumes
