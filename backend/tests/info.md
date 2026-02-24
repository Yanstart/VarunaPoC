# tests

## But
Suite de tests unitaires, d'integration et de bout en bout pour le backend FastAPI.

## Pourquoi
Les tests automatises garantissent la non-regression et valident le comportement de chaque module (auth, annotations, detection, ML, qualite, FHIR, cache, readers).

## Structure
- `conftest.py` -- Fixtures pytest partages : client FastAPI, session DB async, configuration OpenSlide.
- `test_health.py` -- Tests des endpoints de base et health checks.
- `test_auth_jwt.py` -- Tests de validation JWT et decodage de tokens.
- `test_auth_dependencies.py` -- Tests des dependencies d'authentification FastAPI.
- `test_audit.py` -- Tests de la piste d'audit.
- `test_annotations_api.py` -- Tests CRUD de l'API annotations.
- `test_annotation_service.py` -- Tests du service d'annotations.
- `test_detection_api.py` -- Tests de l'API de detection automatique.
- `test_detection_pipeline.py` -- Tests du pipeline heatmap -> contours.
- `test_ml_integration.py` -- Tests d'integration ML (providers, inference).
- `test_ml_real_slides.py` -- Tests ML sur de vraies lames.
- `test_quality_api.py` -- Tests de l'API metriques de qualite.
- `test_quality_metrics.py` -- Tests des fonctions mathematiques de metriques.
- `test_slides_api.py` -- Tests de l'API de navigation des lames.
- `test_coordinate_mapping.py` -- Tests de conversion de coordonnees.
- `test_similarity_index.py` -- Tests de l'index de similarite FAISS.
- `test_disk_cache.py` -- Tests du cache disque.
- `test_memory_cache.py` -- Tests du cache memoire.
- `test_pacs_integration.py` -- Tests d'integration PACS/DICOM.
- `test_fhir_standards.py` -- Tests de conformite FHIR R4.
- `test_readers.py` -- Tests des lecteurs de lames.
- `load/` -- Tests de charge Locust.
