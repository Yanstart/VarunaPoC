# Detection Navigation Fix + Zone Interaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix navigation blocking caused by SVG overlay pointer-events, and add click-to-navigate for detection zones (issue #151).

**Architecture:** Replace per-element `pointer-events: visiblePainted` on both annotation shapes and detection previews with a centralized OSD `canvas-click` hit-testing approach. SVG elements become purely visual (`pointer-events: none` inherited from parent). Click detection is handled via `SVGGeometryElement.isPointInFill()` on OSD's `canvas-click` event, which preserves full pan/zoom navigation.

**Tech Stack:** OpenSeadragon (canvas-click handler), SVG hit-testing API, EventBus

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `frontend/src/core/Constants.js` | Modify:175 | Add `DETECTION_NAVIGATE` event |
| `frontend/src/components/AnnotationLayer.js` | Modify | Remove per-element pointer-events, add canvas-click hit-testing for annotations + detections |
| `frontend/src/viewers/ViewerInstance.js` | Modify | Add `fitImageBounds(bounds)` method (image px -> viewport) |
| `frontend/src/components/DetectionPanel.js` | Modify:383-395 | Add `_navigateToZone()` on item click |
| `frontend/src/css/annotation-layer.css` | Modify:15-22 | Remove `:hover` on shapes (no longer receives hover with pointer-events:none) |

---

### Task 1: Add DETECTION_NAVIGATE event constant

**Files:**
- Modify: `frontend/src/core/Constants.js:175`

- [ ] **Step 1: Add event constant**

After line 175 (`DETECTION_HIGHLIGHT`), add:

```javascript
    /** @payload {{ regionIndex: number, bounds: {x,y,width,height} }} */
    DETECTION_NAVIGATE: 'detection:navigate',
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/core/Constants.js
git commit -m "feat(detection): add DETECTION_NAVIGATE event constant"
```

---

### Task 2: Add `fitImageBounds()` to ViewerInstance

**Files:**
- Modify: `frontend/src/viewers/ViewerInstance.js` (after `resetView()` ~line 541)

- [ ] **Step 1: Add fitImageBounds method**

Add after `resetView()`:

```javascript
    /**
     * Fit viewport to bounds expressed in slide pixel coordinates.
     * Converts image pixels to OSD viewport coords via tiledImage.
     * @param {{x: number, y: number, width: number, height: number}} bounds - Image pixel bounds
     * @param {number} [padding=0.2] - Fractional padding around bounds (0.2 = 20%)
     */
    fitImageBounds(bounds, padding = 0.2) {
        if (!this._osdViewer || !this._osdViewer.viewport) return;

        const tiledImage = this._osdViewer.world.getItemAt(0);
        if (!tiledImage) return;

        // Convert image pixel corners to viewport coordinates
        const topLeft = tiledImage.imageToViewportCoordinates(bounds.x, bounds.y);
        const bottomRight = tiledImage.imageToViewportCoordinates(
            bounds.x + bounds.width,
            bounds.y + bounds.height,
        );

        // Add padding
        const vw = bottomRight.x - topLeft.x;
        const vh = bottomRight.y - topLeft.y;
        const padX = vw * padding;
        const padY = vh * padding;

        const rect = new OpenSeadragon.Rect(
            topLeft.x - padX,
            topLeft.y - padY,
            vw + padX * 2,
            vh + padY * 2,
        );

        this._osdViewer.viewport.fitBounds(rect);
    }
```

- [ ] **Step 2: Verify no lint errors**

Run: `cd frontend && npx eslint src/viewers/ViewerInstance.js`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/viewers/ViewerInstance.js
git commit -m "feat(viewer): add fitImageBounds() for image-pixel navigation"
```

---

### Task 3: Fix AnnotationLayer — remove pointer-events, add canvas-click hit-testing

This is the core fix. Two changes:
1. Remove `pointer-events: visiblePainted` from annotation shapes and detection previews
2. Add a single OSD `canvas-click` handler that does SVG hit-testing

**Files:**
- Modify: `frontend/src/components/AnnotationLayer.js`
- Modify: `frontend/src/css/annotation-layer.css`

- [ ] **Step 1: Remove pointer-events and click handlers from annotation elements**

In `_createAnnotationElement()` (~line 242-256), remove these lines:

```javascript
// REMOVE these lines:
el.style.pointerEvents = 'visiblePainted';
el.style.cursor = 'pointer';

// Click to select
el.addEventListener('click', (e) => {
    e.stopPropagation();
    annotationStore.selectAnnotation(anno.id);
});
```

Keep only the `dataset.annotationId` and the `isSelected` class logic.

- [ ] **Step 2: Remove pointer-events and click handlers from detection previews**

In `_renderPreviews()` (~line 359-367), remove:

```javascript
// REMOVE these lines:
polygon.style.pointerEvents = 'visiblePainted';
polygon.style.cursor = 'pointer';

// Click handler: emit event for bidirectional linking
polygon.addEventListener('click', (e) => {
    e.stopPropagation();
    this._highlightDetectionPreview(i);
    eventBus.emit(Events.DETECTION_PREVIEW_CLICKED, { index: i });
});
```

- [ ] **Step 3: Add canvas-click handler in _setupEventListeners()**

Add at the end of `_setupEventListeners()`, before the closing brace:

```javascript
        // Centralized click handler via OSD — replaces per-element pointer-events.
        // SVG elements stay pointer-events:none so OSD receives all mouse events
        // (pan/zoom works). On click, we convert coords and hit-test SVG shapes.
        this._boundCanvasClick = (event) => {
            const tiledImage = this.viewer.world.getItemAt(0);
            if (!tiledImage) return;

            // Convert click position to image pixel coordinates
            const viewportPoint = this.viewer.viewport.pointFromPixel(event.position);
            const imagePoint = tiledImage.viewportToImageCoordinates(viewportPoint);

            // Create SVG point for hit-testing
            const svgPoint = this.svg.createSVGPoint();
            svgPoint.x = imagePoint.x;
            svgPoint.y = imagePoint.y;

            // 1) Test detection previews first (higher priority, on top)
            const previews = this.previewGroup.querySelectorAll('.detection-preview');
            for (const polygon of previews) {
                if (polygon.style.display === 'none') continue;
                try {
                    if (polygon.isPointInFill(svgPoint) || polygon.isPointInStroke(svgPoint)) {
                        const index = parseInt(polygon.dataset.detectionIndex);
                        this._highlightDetectionPreview(index);
                        eventBus.emit(Events.DETECTION_PREVIEW_CLICKED, { index });
                        event.preventDefaultAction = true;
                        return;
                    }
                } catch (_) { /* isPointInFill not supported — skip */ }
            }

            // 2) Test annotation shapes
            const shapes = this.annoGroup.querySelectorAll('[data-annotation-id]');
            for (const shape of shapes) {
                try {
                    // For <g> elements (MultiPolygon), test children
                    const targets = shape.tagName === 'g'
                        ? shape.querySelectorAll('polygon, circle, rect')
                        : [shape];
                    for (const target of targets) {
                        if (target.isPointInFill?.(svgPoint) || target.isPointInStroke?.(svgPoint)) {
                            annotationStore.selectAnnotation(shape.dataset.annotationId);
                            event.preventDefaultAction = true;
                            return;
                        }
                    }
                } catch (_) { /* skip */ }
            }
        };
        this.viewer.addHandler('canvas-click', this._boundCanvasClick);
```

- [ ] **Step 4: Clean up handler in destroy()**

In `destroy()` (~line 514), add before the `if (this.svg ...)` block:

```javascript
        if (this.viewer && this._boundCanvasClick) {
            this.viewer.removeHandler('canvas-click', this._boundCanvasClick);
        }
```

- [ ] **Step 5: Update CSS — remove hover rules for annotation shapes**

In `frontend/src/css/annotation-layer.css`, remove lines 19-22:

```css
/* REMOVE — shapes no longer receive hover with pointer-events:none */
.annotation-shape:hover {
    stroke-opacity: 1;
    filter: brightness(1.2);
}
```

Keep the `.detection-preview` pulse animation and `.detection-preview--active` styles.

- [ ] **Step 6: Verify lint**

Run: `cd frontend && npx eslint src/components/AnnotationLayer.js`

- [ ] **Step 7: Manual test**

1. Load a slide, run ML detection
2. Verify: pan/zoom works OVER detection polygons (drag with mouse)
3. Verify: clicking on a detection polygon highlights it in the panel
4. Verify: clicking on an annotation selects it
5. Verify: scroll-to-zoom works everywhere

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/AnnotationLayer.js frontend/src/css/annotation-layer.css
git commit -m "fix(viewer): replace SVG pointer-events with OSD canvas-click hit-testing

Fixes navigation blocking when detection/annotation SVG polygons cover
the slide. SVG elements no longer intercept mouse events; click detection
uses SVG isPointInFill() via OSD canvas-click handler.

Fixes #151"
```

---

### Task 4: Add click-to-navigate in DetectionPanel

**Files:**
- Modify: `frontend/src/components/DetectionPanel.js:383-395`

- [ ] **Step 1: Add _navigateToZone() method**

Add after `_scrollToDetectionItem()` (~line 771):

```javascript
    /**
     * Navigate the viewer to a detection zone's bounding box.
     * @param {number} index - Detection zone index
     * @private
     */
    _navigateToZone(index) {
        if (!this.detectionResult?.geojson?.features) return;
        const feature = this.detectionResult.geojson.features[index];
        if (!feature?.geometry?.coordinates?.[0]) return;

        // Extract bounding box from polygon ring
        const ring = feature.geometry.coordinates[0];
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (const [x, y] of ring) {
            if (x < minX) minX = x;
            if (y < minY) minY = y;
            if (x > maxX) maxX = x;
            if (y > maxY) maxY = y;
        }

        const bounds = { x: minX, y: minY, width: maxX - minX, height: maxY - minY };

        // Navigate viewer
        if (this._viewerInstance?.fitImageBounds) {
            this._viewerInstance.fitImageBounds(bounds);
        }

        eventBus.emit(Events.DETECTION_NAVIGATE, { regionIndex: index, bounds });
    }
```

- [ ] **Step 2: Wire navigation into item click handler**

In the detection item click handler (~line 384-395), add `_navigateToZone` call:

Replace:
```javascript
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking on action buttons
                if (e.target.closest('.detection-item__actions') || e.target.closest('.detection-item__feedback')) {
                    return;
                }
                const idx = parseInt(item.dataset.detectionItemIndex);
                if (!isNaN(idx)) {
                    this._highlightDetectionItem(idx);
                    eventBus.emit(Events.DETECTION_ITEM_CLICKED, { index: idx });
                }
            });
```

With:
```javascript
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking on action buttons
                if (e.target.closest('.detection-item__actions') || e.target.closest('.detection-item__feedback')) {
                    return;
                }
                const idx = parseInt(item.dataset.detectionItemIndex);
                if (!isNaN(idx)) {
                    this._highlightDetectionItem(idx);
                    this._navigateToZone(idx);
                    eventBus.emit(Events.DETECTION_ITEM_CLICKED, { index: idx });
                }
            });
```

- [ ] **Step 3: Also navigate when clicking detection on the slide**

In `_setupEventListeners()` (~line 78-84), add navigation after highlight:

Replace:
```javascript
            eventBus.on(Events.DETECTION_PREVIEW_CLICKED, ({ index }) => {
                this._highlightDetectionItem(index);
                this._scrollToDetectionItem(index);
            }),
```

With:
```javascript
            eventBus.on(Events.DETECTION_PREVIEW_CLICKED, ({ index }) => {
                this._highlightDetectionItem(index);
                this._scrollToDetectionItem(index);
                this._navigateToZone(index);
            }),
```

- [ ] **Step 4: Verify lint**

Run: `cd frontend && npx eslint src/components/DetectionPanel.js`

- [ ] **Step 5: Manual test**

1. Run detection on a slide
2. Click a zone in the panel list -> viewer pans/zooms to that zone
3. Click a zone on the slide -> panel highlights + viewer centers on it
4. Toggle visibility on a zone -> zone hides/shows
5. Pan/zoom works freely over detection zones

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/DetectionPanel.js
git commit -m "feat(detection): click-to-navigate zooms viewer to zone bbox

Clicking a detection item in the panel or on the slide navigates the
viewer to the zone's bounding box with 20% padding.

Fixes #151"
```

---

### Task 5: Final verification and cleanup

- [ ] **Step 1: Run full frontend lint**

Run: `cd frontend && npm run lint`

- [ ] **Step 2: Full manual regression test**

1. Load slide, pan/zoom freely (no ML) -> OK
2. Run ML prediction -> heatmap works, pan/zoom still works
3. Run detection -> zones appear, pan/zoom works OVER zones
4. Click zone in panel -> viewer navigates to zone
5. Click zone on slide -> panel highlights + scrolls
6. Toggle zone visibility -> zone hides/shows
7. Click annotation -> annotation selected
8. Compare view with two slides -> sync still works

- [ ] **Step 3: Squash or finalize commits, push**

```bash
git push -u origin feature/detection-navigation
```
