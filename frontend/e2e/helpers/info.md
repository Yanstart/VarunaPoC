# helpers

## But
Fournir des fonctions utilitaires pour intercepter et simuler les reponses des endpoints API backend dans les tests E2E.

## Pourquoi
Permettre des tests deterministes et rapides sans backend reel en mockant les routes HTTP via l'interception de requetes Playwright.

## Structure
- `api-mock.js` — Fonctions de mock pour les endpoints `/api/health`, `/api/slides/browse`, `/api/slides/{id}/info`, `/api/auth/*`, annotations et modeles ML.
