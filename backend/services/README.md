# Services

## Purpose
Business logic layer for backend operations.
Handles slide detection, ML analysis, annotation management, and detection pipeline.

## Contents
- `slide_scanner.py` - Auto-detection of slides in /Slides directory
- `slide_loader.py` - OpenSlide operations (metadata, overview, tiles)
- `format_detector.py` - Multi-format slide structure detection
- `annotation_service.py` - Annotation CRUD with PostGIS spatial queries
- `detection/` - Heatmap-to-GeoJSON detection pipeline
  - `pipeline.py` - Main detection orchestration
  - `postprocessing.py` - Contour extraction, simplification, scaling
- `ml/` - ML provider system
  - `providers/slideflow_provider.py` - Slideflow integration (extractor + classifier modes)
  - `providers/mock_provider.py` - Mock provider for testing

## Detection Pipeline
```
Heatmap (H,W) float [0,1]
  -> threshold (configurable, default 0.5)
  -> scipy.ndimage.binary_closing (clean noise)
  -> scipy.ndimage.label (connected components)
  -> skimage.measure.find_contours (marching squares)
  -> filter by min_area
  -> simplify Douglas-Peucker (reduce vertices)
  -> scale coords: heatmap_px -> slide_level0_px
  -> GeoJSON FeatureCollection
```

## ML Provider System
Uses Protocol-based interface (`core/interfaces/ml_provider.py`):
- `predict()` - Classification with uncertainty
- `generate_heatmap()` - Attention/Grad-CAM heatmap
- `extract_features()` - Feature embedding extraction

Slideflow provider supports:
- **Extractor mode** (Phase 1-2): Feature norms as attention proxy
- **Classifier mode** (Phase 3): Trained model with Grad-CAM
