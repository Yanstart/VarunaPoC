# cache

## But
Systeme de cache a deux niveaux (memoire L1, disque L2) pour les resultats de calculs ML.

## Pourquoi
Les calculs ML (embeddings, heatmaps) sont couteux ; le cache evite les recalculs et accelere les requetes suivantes.

## Structure
- `__init__.py` -- Package cache (vide).
- `memory_cache.py` -- Cache L1 en memoire avec TTL (cachetools), statistiques hits/misses.
- `disk_cache.py` -- Cache L2 sur disque au format numpy .npy, organise par slide_id et modele, ecriture atomique.
