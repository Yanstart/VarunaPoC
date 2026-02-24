# keycloak

## But
Configuration du realm Keycloak pour le fournisseur d'identite OIDC de developpement.

## Pourquoi
L'export du realm permet de reconstruire automatiquement l'environnement Keycloak (clients, roles, politiques de securite) lors du deploiement Docker.

## Structure
- `realm-export.json` -- Export complet du realm "varuna" : client varuna-viewer, roles (LECTURE_SEULE, INFIRMIER, MEDECIN, ADMIN_TECHNIQUE), politiques de brute force et sessions.
