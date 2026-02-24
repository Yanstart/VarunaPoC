# viewers

## But
Gerer le cycle de vie, la creation et la synchronisation des instances de viewers de lames histologiques.

## Pourquoi
Abstraire la complexite d'OpenSeadragon derriere des patterns (Factory, State, Mediator, Adapter) pour supporter la comparaison multi-viewers et l'ajout futur de backends de rendu alternatifs.

## Structure
- `index.js` — Point d'entree : re-exporte ViewerManager, ViewerFactory, ViewerInstance, ViewerState, SyncController.
- `ViewerManager.js` — Singleton gestionnaire de tous les viewers actifs (creation, destruction, layout).
- `ViewerFactory.js` — Factory avec presets pour creer des ViewerInstance avec des configurations predefinies (standard, minimal, comparaison).
- `ViewerInstance.js` — Wrapper OpenSeadragon encapsulant un viewer unique avec gestion d'etat et chargement de lames.
- `ViewerState.js` — Machine a etats (idle, loading, ready, error, destroying) avec validation des transitions.
- `SyncController.js` — Mediateur de synchronisation pan/zoom entre plusieurs viewers avec normalisation des coordonnees.
- `ViewerInterface.js` — Interface abstraite definissant le contrat pour tout adaptateur de viewer.
- `OSDViewerAdapter.js` — Adaptateur concret pour OpenSeadragon implementant ViewerInterface.
- `CornerstoneViewerAdapter.js` — Stub pour une future integration Cornerstone3D (non implemente).
- `NDViewState.js` — Etat de vue N-dimensionnel pour l'imagerie multi-plans (Z-stack, canaux, time-lapse).
