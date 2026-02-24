# auth

## But
Module d'authentification OIDC, autorisation RBAC et piste d'audit pour la securite hospitaliere.

## Pourquoi
Les environnements hospitaliers exigent une authentification stricte, un controle d'acces par role et une tracabilite complete de chaque action.

## Structure
- `__init__.py` -- Point d'entree du module ; expose le flag `AUTH_ENABLED`.
- `config.py` -- Configuration OIDC depuis les variables d'environnement (issuer, audience, roles).
- `dependencies.py` -- Dependencies FastAPI (`get_current_user`, `require_role`) pour l'injection d'authentification.
- `jwt_validator.py` -- Validation et decodage des tokens JWT via JWKS (RS256, ES256).
- `oidc.py` -- Decouverte OIDC et cache du JWKS avec TTL configurable.
- `audit.py` -- Piste d'audit double : PostgreSQL (primaire) + fichier JSON (reprise apres sinistre).
- `break_glass.py` -- Acces d'urgence temporaire avec elevation de privileges et audit CRITICAL.
- `session_roaming.py` -- Sauvegarde/restauration de l'etat de session entre postes de travail.
- `models.py` -- Modeles ORM SQLAlchemy (User, AuditEvent, SessionState, BreakGlassLog).
- `routes.py` -- Endpoints FastAPI : /me, /break-glass, /session.
- `schemas.py` -- Schemas Pydantic pour les requetes et reponses d'authentification.
