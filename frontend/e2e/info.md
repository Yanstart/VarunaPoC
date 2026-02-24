# e2e

## But
Suite de tests end-to-end Playwright pour valider le comportement complet de l'application VarunaPoC dans un navigateur.

## Pourquoi
Garantir que les parcours utilisateur critiques (navigation, visualisation, annotations, authentification) fonctionnent correctement de bout en bout, sans dependre du backend grace au mocking des API.

## Structure
- `playwright.config.js` — Configuration Playwright (navigateurs, timeouts, reporter, demarrage du serveur Vite).
- `fixtures/` — Fixtures partagees (donnees de test deterministes, helpers de page).
- `helpers/` — Utilitaires de mock des endpoints API backend.
- `tests/` — Fichiers de specs organises par fonctionnalite (health, navigation, viewer, annotations, etc.).
- `playwright-report/` — Rapports HTML generes apres execution.
- `test-results/` — Artefacts de test (screenshots, traces).
