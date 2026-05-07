# Backend - FastAPI + OpenSlide + SQLAlchemy

## Purpose
Serves REST API for histological slide viewing, ML analysis, and annotation management.
Handles slide detection, metadata extraction, image serving, heatmap generation, and spatial annotations.

## Contents
- `main.py` - FastAPI application entry point
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template
- `routes/` - API endpoints
  - `slides.py` - Slides API (list, browse, info, overview, DZI tiles)
  - `ml.py` - ML API (predict, heatmap, detect, features)
  - `annotations.py` - Annotations CRUD + labels + spatial query + export
- `services/` - Business logic
  - `slide_scanner.py` - Auto-detection of slides in /Slides
  - `slide_loader.py` - OpenSlide integration (metadata, overview, tiles)
  - `format_detector.py` - Multi-format slide detection
  - `annotation_service.py` - Annotation CRUD operations
  - `detection/` - Heatmap-to-GeoJSON pipeline
  - `ml/` - ML provider system (Slideflow, mock)
- `models/` - SQLAlchemy ORM models
  - `annotation.py` - Annotation model (PostGIS geometry)
  - `annotation_label.py` - Label model (name, color, category)
- `schemas/` - Pydantic validation schemas
  - `annotation.py` - Annotation create/update/response
  - `detection.py` - Detection parameters and response
  - `geojson.py` - GeoJSON Feature/FeatureCollection
- `core/` - Core infrastructure
  - `database.py` - Async SQLAlchemy engine + session factory
  - `interfaces/` - Protocol-based interfaces (MLProvider)
- `alembic/` - Database migrations
- `tests/` - Pytest test suite

## Dependencies
- **FastAPI:** Web framework for APIs
- **Uvicorn:** ASGI server
- **OpenSlide Python:** Library for reading slide formats
- **Pillow:** Image processing (JPEG encoding)
- **SQLAlchemy[asyncio] + asyncpg:** Async PostgreSQL ORM
- **GeoAlchemy2:** PostGIS spatial types for SQLAlchemy
- **Alembic:** Database schema migrations
- **Slideflow:** ML feature extraction and heatmap generation
- **SciPy + scikit-image + Shapely:** Detection pipeline (contours, simplification)

## Quick Start

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start PostgreSQL (for annotations)
```bash
cd .. && cp .env.dev.example .env
docker compose --profile dev up -d db
cd backend
```

### 3. Run database migrations
```bash
python -m alembic upgrade head
```

### 4. Start development server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## API Endpoints

### Slides
- `GET /api/slides/` - List all slides (recursive scan)
- `GET /api/slides/browse` - Browse folder by folder
- `GET /api/slides/{id}/info` - Slide metadata
- `GET /api/slides/{id}/overview` - Overview image (JPEG)
- `GET /api/slides/{id}/dzi.json` - DZI descriptor for tile streaming
- `GET /api/slides/{id}/tiles/{level}/{col}_{row}.jpg` - Individual tiles

### ML Analysis
- `POST /api/ml/predict/{slide_id}` - Run ML prediction
- `GET /api/ml/heatmap/{slide_id}` - Generate attention heatmap
- `POST /api/ml/detect/{slide_id}` - Auto-detect regions (heatmap -> GeoJSON)
- `POST /api/ml/features/{slide_id}` - Extract feature embeddings
- `GET /api/ml/models` - List available models
- `GET /api/ml/health` - ML provider status

### Annotations
- `POST /api/annotations/{slide_id}` - Create annotation
- `GET /api/annotations/{slide_id}` - List (with spatial bbox filter)
- `GET /api/annotations/{slide_id}/{id}` - Get single
- `PUT /api/annotations/{slide_id}/{id}` - Update
- `DELETE /api/annotations/{slide_id}/{id}` - Delete
- `POST /api/annotations/{slide_id}/batch` - Batch create
- `GET /api/annotations/{slide_id}/export` - Export GeoJSON

### Labels
- `GET/POST /api/labels/` - List/Create labels
- `GET/PUT/DELETE /api/labels/{id}` - Get/Update/Delete label

## Database

PostgreSQL 16 + PostGIS 3.4 via Docker:
```bash
docker compose --profile dev up -d  # port 5433
```

Tables: `annotations` (with GIST spatial index), `annotation_labels`
SRID=0 (pixel coordinates, not geographic).

## Testing
```bash
# All tests
pytest tests/ -v

# Unit tests only (no DB required)
pytest tests/ -m "not db" -v

# DB integration tests (requires PostgreSQL)
pytest tests/test_annotations_api.py -v
```

94 tests, covering: slides API, ML providers, detection pipeline, annotations, coordinate mapping.

## Last Updated
2026-02-05 - Phase 2: Annotations + Detection + Slideflow ML
