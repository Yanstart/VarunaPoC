# core

## But
Fournir les modules fondamentaux de l'application : constantes globales, configuration et bus d'evenements.

## Pourquoi
Centraliser la configuration et la communication inter-composants pour eviter le couplage direct entre modules et garantir la coherence applicative.

## Structure
- `index.js` — Point d'entree : re-exporte EventBus, constantes et configuration.
- `Constants.js` — Constantes globales : etats du viewer, noms d'evenements, configuration API, presets de layout, cles de stockage, formats supportes.
- `EventBus.js` — Bus d'evenements singleton (pattern Observer/Pub-Sub) pour la communication decouple entre composants.
