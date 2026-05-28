# models

## But
Modeles ORM SQLAlchemy definissant le schema de la base de donnees PostgreSQL/PostGIS.

## Pourquoi
Centraliser les modeles ORM assure la coherence entre le schema de la base, les migrations Alembic et les requetes applicatives.

## Structure
- `__init__.py` -- Re-exporte tous les modeles (Annotation, AnnotationLabel, Correction, MLModel, auth, quality).
- `annotation.py` -- Modele Annotation : geometries spatiales PostGIS sur lames histologiques.
- `annotation_label.py` -- Modele AnnotationLabel : labels de categorisation (Tumeur, Stroma, Necrose, etc.).
- `correction.py` -- Modele Correction : suivi des corrections pathologistes sur les predictions ML.
- `ml_model.py` -- Modele MLModel : registre des modeles d'IA (foundation models, classifiers entraines, embeddings). FK target pour annotations.source_model_id, corrections.model_id. Lifecycle registered_at -> deployed_at -> retired_at (soft delete uniquement). Voir issue #370.
- `quality_report.py` -- Modele QualityReport : cache des resultats de metriques de qualite (kappa, F1, IoU).
- `share_token.py` -- Modele ShareToken : tokens de partage de lames avec permissions et expiration.
- `view_history.py` -- Modele ViewHistory : une ligne par paire (slide, utilisateur) traquant la frequence et la recence des consultations.
- `worklist.py` -- Modele WorklistAssignment : attribution d'une lame a un pathologiste pour annotation/revue.
