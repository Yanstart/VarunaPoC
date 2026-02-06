# Routes

## Purpose
API endpoint definitions for VarunaPoC backend.

## Contents
- `slides.py` - Slides API (list, browse, info, overview, DZI tiles)
- `ml.py` - ML API (predict, heatmap, detect, features, models)
- `annotations.py` - Annotations CRUD + labels + spatial query + export

## Usage
Routes are registered in `main.py` using `app.include_router()`.
Annotations router is optional (requires sqlalchemy + asyncpg + geoalchemy2).

## Technical Notes
- All routes prefixed with `/api/`
- Slides: read-only (GET)
- ML: POST for compute-heavy operations, GET for status/metadata
- Annotations: full CRUD (POST/GET/PUT/DELETE) + spatial bbox filtering via PostGIS
