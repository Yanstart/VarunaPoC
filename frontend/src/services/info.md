# services

## But
Regrouper les services metier singleton qui gerent la communication avec le backend, l'authentification, les annotations et l'internationalisation.

## Pourquoi
Encapsuler la logique d'acces aux donnees et d'etat applicatif dans des classes reutilisables, decouples des composants d'interface.

## Structure
- `index.js` — Point d'entree : re-exporte ApiService et ApiError.
- `ApiService.js` — Client API singleton pour toutes les requetes vers le backend FastAPI (lames, dossiers, annotations, ML, qualite).
- `AuthService.js` — Service d'authentification OIDC PKCE (mode anonyme ou Keycloak).
- `AnnotationStore.js` — Store local des annotations avec synchronisation backend et emission d'evenements.
- `I18nService.js` — Service d'internationalisation : chargement des traductions JSON, changement de locale, fonction t() de traduction.
