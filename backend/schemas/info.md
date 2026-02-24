# schemas

## But
Schemas Pydantic definissant les modeles de requete et reponse de l'API REST.

## Pourquoi
Centraliser les schemas assure la validation automatique des donnees, la generation de documentation OpenAPI et la coherence du contrat d'API.

## Structure
- `__init__.py` -- Re-exporte tous les schemas (Annotation, Detection, GeoJSON).
- `annotation.py` -- Schemas CRUD pour annotations et labels (create, update, response, batch).
- `detection.py` -- Schemas pour le pipeline de detection automatique (seuil, aire min, simplification).
- `geojson.py` -- Types GeoJSON standard (Geometry, Feature, FeatureCollection) en coordonnees pixel.
