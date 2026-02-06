# Components

## Purpose
Reusable UI components using Vanilla JavaScript (class-based).

## Contents

### Viewer
- `MLPanel.js` - ML analysis panel (predict, heatmap toggle, opacity slider)
- `HeatmapOverlay.js` - Canvas overlay for ML attention heatmaps on OpenSeadragon

### Annotations (Phase 2)
- `AnnotationLayer.js` - SVG overlay for rendering annotations on OpenSeadragon
- `DrawingTools.js` - Drawing toolbar (rectangle, polygon, point, freehand, circle)
- `LayerManager.js` - Layer visibility/opacity panel in info sidebar
- `DetectionPanel.js` - Auto-detection workflow (detect -> preview -> accept/reject -> confirm)

### Navigation
- `FolderBrowser.js` - Hierarchical folder navigation for slides
- `CompareLayout.js` - Side-by-side multi-viewer layout

## Design Pattern
Class-based components with:
- Constructor accepts container element + options
- EventBus for inter-component communication
- `destroy()` method for cleanup (event listeners, DOM elements)
- Singleton stores for shared state (AnnotationStore)

## Key Coordinate Systems
- **OpenSeadragon viewport**: normalized 0.0-1.0 coordinates
- **Slide pixels**: absolute pixel coordinates (level 0)
- **Screen pixels**: browser DOM coordinates

Mapping: `tiledImage.getBounds(true)` for viewport coords,
`viewport.viewportToViewerElementCoordinates()` for screen pixels.
