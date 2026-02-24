# utils

## But
Fournir des fonctions utilitaires partagees pour les appels API et les transformations de coordonnees.

## Pourquoi
Centraliser la logique technique reutilisable (fetch, conversion de coordonnees) pour eviter la duplication dans les composants et les services.

## Structure
- `api.js` — Client API fonctionnel legacy : fetchSlides, getSlideInfo, getOverviewUrl, fetchBrowse (communication avec le backend FastAPI).
- `coordinates.js` — Utilitaires de transformation de coordonnees entre l'espace normalise OpenSeadragon, les pixels absolus OpenSlide et les niveaux pyramidaux.
