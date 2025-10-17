# Backend - FastAPI + OpenSlide

## Purpose
Serves REST API for histological slide viewing.
Handles slide detection, metadata extraction, and image serving.

## Contents
- `main.py` - FastAPI application entry point
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template
- `routes/` - API endpoints
  - `slides.py` - Slides API (list, info, overview)
- `services/` - Business logic
  - `slide_scanner.py` - Auto-detection of slides in /Slides
  - `slide_loader.py` - OpenSlide integration (metadata, overview extraction)
- `utils/` - Helper functions (currently empty)

## Dependencies
- **FastAPI:** Web framework for APIs
- **Uvicorn:** ASGI server
- **OpenSlide Python:** Library for reading slide formats
- **Pillow:** Image processing (JPEG encoding)

Official documentation:
- OpenSlide: https://openslide.org/api/python/
- FastAPI: https://fastapi.tiangolo.com/

## Installation

### 1. Create virtual environment
```bash
cd backend
python -m venv venv
```

### 2. Activate virtual environment
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

**IMPORTANT:** OpenSlide Python requires OpenSlide C library installed on system.

**Windows:**
Download from https://openslide.org/download/
Extract to C:\OpenSlide and add bin/ to PATH.

**Linux:**
```bash
sudo apt-get install openslide-tools python3-openslide
```

**Mac:**
```bash
brew install openslide
```

## Usage

### Start development server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Options:
- `--reload` - Auto-restart on code changes
- `--host 0.0.0.0` - Accept connections from any IP
- `--port 8000` - Listen on port 8000

### Access API documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Test endpoints
```bash
# Health check
curl http://localhost:8000/api/health

# List slides
curl http://localhost:8000/api/slides

# Get slide info
curl http://localhost:8000/api/slides/{slide_id}/info

# Get overview image
curl http://localhost:8000/api/slides/{slide_id}/overview --output overview.jpg
```

## Technical Notes

### Phase 1 Simplifications
- **No caching:** Slides opened/closed on each request (Phase 2 will add Redis/filesystem cache)
- **No authentication:** Open API (Phase 2 will add basic auth)
- **Simple overview extraction:** Uses `OpenSlide.get_thumbnail()` (Phase 2 will add DZI tiling)

### CORS Configuration
Currently allows http://localhost:5173 (Vite dev server).
**MUST be restricted in production!** (backend/main.py:30)

### Slide Detection
- Scans `../Slides/` recursively at startup
- Supports .mrxs, .bif, .tif, .tiff
- Verifies companion directories for .mrxs files
- Generates stable MD5-based IDs

### OpenSlide Integration
- Opens slides on-demand (no persistent connections Phase 1)
- `get_thumbnail()` automatically chooses best pyramid level
- Returns RGB PIL.Image, encoded to JPEG

## Last Updated
2025-10-17 - Phase 1 Hello World
