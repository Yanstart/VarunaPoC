# quality

## But
Module de metriques d'accord inter-annotateurs pour l'analyse de qualite des annotations histologiques.

## Pourquoi
Evaluer la concordance entre pathologistes (kappa de Cohen/Fleiss, F1, IoU, matrice de confusion) est essentiel pour valider la fiabilite des annotations.

## Structure
- `__init__.py` -- Point d'entree ; expose le flag `QUALITY_ENABLED`.
- `config.py` -- Seuils et parametres par defaut (IoU threshold, taille de grille, buffer point, TTL cache).
- `metrics.py` -- Fonctions mathematiques pures : kappa de Cohen, kappa de Fleiss, matrice de confusion, F1 par label, distribution IoU.
- `matching.py` -- Strategies d'appariement spatial des annotations : matching IoU (PostGIS) et matching par grille.
- `services.py` -- Couche d'orchestration connectant matching spatial et calcul de metriques, avec cache optionnel.
- `routes.py` -- Endpoints FastAPI POST pour chaque metrique de qualite.
- `schemas.py` -- Schemas Pydantic pour les requetes (PairwiseRequest, MultiRaterRequest) et reponses.
