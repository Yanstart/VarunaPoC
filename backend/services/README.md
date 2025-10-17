# Services

## Purpose
Business logic layer for backend operations.
Handles slide detection, OpenSlide integration, and data processing.

## Contents
- `slide_scanner.py` - Auto-detection of slides in /Slides directory
- `slide_loader.py` - OpenSlide operations (metadata, overview extraction)

## Technical Notes

### slide_scanner.py
- Scans ../Slides recursively
- Generates MD5-based IDs for stable references
- Caches slide paths to avoid repeated filesystem scans
- Verifies .mrxs companion directory structure

### slide_loader.py
- Uses OpenSlide.get_thumbnail() for simple overview extraction
- Converts PIL.Image to JPEG bytes
- Detects format from vendor metadata or extension
- No persistent slide objects (opened/closed per request)

## Phase 1 Simplifications
- No caching (Redis/filesystem)
- No connection pooling
- Direct OpenSlide calls (no abstraction layer)
