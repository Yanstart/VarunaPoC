# core

## But
Infrastructure centrale du backend : base de donnees, interfaces abstraites et exceptions metier.

## Pourquoi
Centraliser les fondations techniques (connexion DB, contrats d'interface, hierarchie d'erreurs) garantit la coherence et facilite l'inversion de dependances.

## Structure
- `__init__.py` -- Package core : database, exceptions, interfaces ML.
- `database.py` -- Configuration async SQLAlchemy + PostgreSQL/PostGIS (engine, session factory, Base).
- `exceptions/` -- Exceptions metier specifiques au domaine.
- `interfaces/` -- Interfaces abstraites (Protocol) pour les providers ML.
