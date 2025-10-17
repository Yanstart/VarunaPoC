# Routes

## Purpose
API endpoint definitions for VarunaPoC backend.

## Contents
- `slides.py` - Slides API endpoints

## Usage
Routes are registered in `main.py` using `app.include_router()`.

## Technical Notes
- All routes prefixed with `/api/`
- Read-only operations (GET only for Phase 1)
- Error handling via FastAPI HTTPException
