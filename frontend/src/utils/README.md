# Utils

## Purpose
Frontend utility functions and helpers.

## Contents
- `api.js` - Backend API client

## Technical Notes

### api.js
- Fetch-based API client
- Functions for each endpoint:
  - `fetchSlides()` → GET /api/slides
  - `getSlideInfo(id)` → GET /api/slides/{id}/info
  - `getOverviewUrl(id)` → Returns URL string
- Error handling via exceptions
- No retry logic (Phase 1 simplicity)
