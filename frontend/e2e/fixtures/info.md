# fixtures

## But
Fournir des fixtures Playwright partagees (donnees de test, helpers de page) reutilisables par tous les specs E2E.

## Pourquoi
Centraliser les donnees de test deterministes et les helpers communs pour eviter la duplication et assurer la coherence entre les specs.

## Structure
- `base.js` — Fixture principale : apiUrl (URL backend), waitForApp (attente du DOM), mockSlideData (donnees de lames, dossiers et annotations deterministes).
