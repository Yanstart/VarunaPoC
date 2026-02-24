# detection

## But
Pipeline de conversion heatmap vers regions GeoJSON pour la detection automatique de structures histologiques.

## Pourquoi
Transformer les heatmaps ML en contours polygonaux exploitables par le viewer permet aux pathologistes de visualiser et valider les detections.

## Structure
- `__init__.py` -- Re-exporte detect_regions, heatmap_to_contours, simplify_contour.
- `pipeline.py` -- Orchestration complete : heatmap -> seuil -> contours -> simplification -> mise a l'echelle -> GeoJSON FeatureCollection.
- `postprocessing.py` -- Traitement bas niveau : seuillage, fermeture morphologique, marching squares, simplification Douglas-Peucker.
