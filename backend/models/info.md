# models

## But
Modeles ORM SQLAlchemy definissant le schema de la base de donnees PostgreSQL/PostGIS.

## Pourquoi
Centraliser les modeles ORM assure la coherence entre le schema de la base, les migrations Alembic et les requetes applicatives.

## Structure
- `__init__.py` -- Re-exporte tous les modeles (Annotation, AnnotationLabel, Correction, auth, quality).
- `annotation.py` -- Modele Annotation : geometries spatiales PostGIS sur lames histologiques.
- `annotation_label.py` -- Modele AnnotationLabel : labels de categorisation (Tumeur, Stroma, Necrose, etc.).
- `correction.py` -- Modele Correction : suivi des corrections pathologistes sur les predictions ML.
- `quality_report.py` -- Modele QualityReport : cache des resultats de metriques de qualite (kappa, F1, IoU).
- `share_token.py` -- Modele ShareToken : tokens de partage de lames avec permissions et expiration.
