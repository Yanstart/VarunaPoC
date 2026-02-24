# config

## But
Fichiers de configuration YAML pour le routage des modeles ML.

## Pourquoi
Externaliser la configuration du routage ML permet de modifier les modeles disponibles et leurs criteres de selection sans changer le code.

## Structure
- `ml_routes.yaml` -- Configuration active du routage ML base sur tags (organe, coloration, tache).
- `ml_routes.yaml.example` -- Exemple commente de configuration avec strategies de matching et fallback.
