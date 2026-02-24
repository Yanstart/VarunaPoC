# Backend

## But
API FastAPI pour le viewer de lames histologiques. Sert les tuiles, gere les annotations, l'authentification, le ML, et les standards medicaux.

## Pourquoi
Point d'entree unique entre le frontend OpenSeadragon et les services (OpenSlide, ML, FHIR, DICOM). Architecture feature-flagged: seul le coeur (slides + annotations) est obligatoire.

## Comment
- FastAPI async + SQLAlchemy async + PostgreSQL/PostGIS
- Feature flags: `AUTH_ENABLED`, `FHIR_ENABLED`, `QUALITY_ENABLED`
- OpenSlide pour lire les lames multi-vendeur (MRXS, BIF, SVS, NDPI...)
- Tile server DZI pour le streaming de tuiles vers OpenSeadragon

## Structure
```
backend/
  main.py              # Point d'entree FastAPI, import conditionnel des modules
  alembic/             # Migrations DB (5 versions: annotations, auth, quality, labels, corrections)
  auth/                # OIDC + RBAC + audit trail (optionnel, AUTH_ENABLED)
  config/              # Config YAML (ml_routes.yaml)
  core/                # Database engine, exceptions, interfaces ML
  fhir/                # FHIR R4 stub pour integration EHR (optionnel, FHIR_ENABLED)
  keycloak/            # Export realm Keycloak (realm-export.json)
  models/              # ORM: Annotation, Label, QualityReport, ShareToken, Correction
  quality/             # Accord inter-annotateur: Cohen/Fleiss kappa (optionnel)
  routes/              # Endpoints API (~15 routers: slides, ml, annotations, dicom, fhir...)
  schemas/             # Pydantic: AnnotationCreate/Response, GeoJSON, Detection
  services/            # Logique metier (tile_server, format_detector, annotation_service, ML, DICOM, HL7v2...)
    cache/             # Disk cache (numpy) + memory cache (LRU)
    detection/         # Pipeline ML: heatmap -> contours -> GeoJSON
    ml/                # Tag extraction, routing, clustering, drift, retraining
    readers/           # Lecteurs pluggables: OpenSlide, OME-TIFF, OME-Zarr, Bio-Formats
  tests/               # Pytest: ~110 fichiers, couverture standards + formats + ML
  utils/               # Helpers divers
```

## Points cles
- `services/format_detector.py` (35K lignes) = detection auto des formats multi-fichiers (MRXS, BIF...)
- `services/readers/` = architecture pluggable, facile a etendre
- `routes/ml.py` = plus gros routeur (~52K lignes, inference, heatmaps, embeddings)
