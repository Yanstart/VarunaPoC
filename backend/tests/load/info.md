# load

## But
Tests de charge simulant des sessions de pathologistes pour evaluer les performances du backend.

## Pourquoi
Valider que le serveur supporte la charge reelle (navigation de lames, tuiles, annotations) avant le deploiement hospitalier.

## Structure
- `__init__.py` -- Package load tests.
- `locustfile.py` -- Scenario Locust simulant un pathologiste : navigation, zoom/pan (tuiles), lecture et creation d'annotations.
- `run_load_test.py` -- Script CLI pour lancer Locust en mode headless, parser les resultats CSV et afficher un resume pass/fail.
