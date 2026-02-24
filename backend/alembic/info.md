# alembic

## But
Configuration et environnement Alembic pour les migrations de schema PostgreSQL asynchrones.

## Pourquoi
Permet de versionner et appliquer les changements de schema de base de donnees de maniere incrementale et reproductible.

## Structure
- `env.py` -- Configuration de l'environnement Alembic avec moteur async SQLAlchemy (asyncpg).
- `script.py.mako` -- Template Mako pour generer les fichiers de migration.
- `versions/` -- Repertoire contenant les scripts de migration ordonnes.
