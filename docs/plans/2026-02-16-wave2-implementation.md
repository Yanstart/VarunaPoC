# Wave 2 — L'IA qui assiste — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the AI useful to pathologists daily — Focus Assist, auto-measurements, feedback loop, auto-tags, background pre-computation, and a user-friendly model selector.

**Architecture:** 4 backend/frontend pairs (Focus Assist, Measurement, Feedback, Auto-tag) + 2 infrastructure tasks (background embeddings pre-computation, model selector UX). Backend adds 4 new endpoints to `routes/ml.py`. Frontend adds 2 new panels (FocusAssistPanel, auto-tag badge in ViewerPanel) and extends DetectionPanel with measurements and feedback buttons. All new endpoints use the existing MLProvider pattern and caches from Wave 1.

**Tech Stack:** FastAPI, SQLAlchemy (Correction model), numpy/scipy (contour analysis, Feret diameter), cachetools (MemoryCache), DiskCache (.npy), OpenSeadragon viewport API, vanilla JS components with EventBus pub/sub.

---

## Parallel Groups

Wave 2 has 4 independent chains that can be implemented in parallel:

| Group | Issues | Description |
|-------|--------|-------------|
| **A: Focus Assist** | #70, #74 | Backend focus endpoint + FocusAssistPanel frontend |
| **B: Measurement + Feedback** | #77, #79, #85, #86 | Measure endpoint + dimension badges + feedback endpoint + confirm/reject buttons |
| **C: Auto-tag** | #87, #88 | Tags endpoint + badge in viewer header |
| **D: Infrastructure** | #89, #91 | Background embeddings pre-computation + model selector UX |

---

## Group A: Focus Assist (Critical Path)

### Task A1: Focus Assist Backend — GET /ml/focus/{slide_id} (#70)

**Files:**
- Modify: `backend/routes/ml.py` (add endpoint + Pydantic models after line 88)
- Test: `backend/tests/test_focus_endpoint.py` (create)

**Step 1: Add Pydantic models to `routes/ml.py`**

After the existing `ModelInfoResponse` class (line ~138), add:

```python
class FocusZone(BaseModel):
    """A single zone of interest."""
    rank: int
    score: float = Field(..., ge=0.0, le=1.0)
    centroid: List[float]
    bbox: List[float]
    area_px: float

class FocusResponse(BaseModel):
    """Response for focus assist endpoint."""
    slide_id: str
    zones: List[FocusZone]
    model_id: str
    total_zones_above_threshold: int
```

**Step 2: Add the endpoint**

After the `/detect/{slide_id}` endpoint (~line 594), add:

```python
@router.get("/focus/{slide_id}", response_model=FocusResponse)
async def get_focus_zones(
    slide_id: str,
    top_n: int = Query(10, ge=1, le=50, description="Number of top zones to return"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum attention score"),
    resolution_level: int = Query(2, ge=0, le=5, description="Heatmap resolution"),
    prediction_class: str = Query("tissue", description="Target class"),
    provider=Depends(get_ml_provider),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
```

Implementation logic:
1. Get slide path via `get_slide_path_by_id(slide_id)`, raise 404 if not found
2. Check `DiskCache.load_heatmap(slide_id, model_id)` first
3. If cache miss, generate heatmap via `provider.generate_heatmap(slide_path, prediction_class, resolution_level)` and cache result
4. Threshold the heatmap, find contours using `heatmap_to_contours` from `services.detection.postprocessing`
5. For each contour: compute centroid, bbox, area, score (mean heatmap value inside contour)
6. Sort by score descending, take top_n
7. Return `FocusResponse`

Import at top of file:
```python
from services.cache.disk_cache import DiskCache
```

Add DiskCache singleton dependency:
```python
_disk_cache = None
def get_disk_cache():
    global _disk_cache
    if _disk_cache is None:
        _disk_cache = DiskCache()
    return _disk_cache
```

**Step 3: Write test**

Create `backend/tests/test_focus_endpoint.py`:
- `test_focus_returns_zones`: Mock provider with fake heatmap, verify response structure
- `test_focus_empty_heatmap`: Heatmap with all zeros returns empty zones
- `test_focus_cache_hit`: Verify DiskCache is checked before generating heatmap
- `test_focus_validates_params`: top_n=0 returns 422, threshold=2.0 returns 422

**Step 4: Add ApiService method**

In `frontend/src/services/ApiService.js`, after `extractFeatures()` method (~line 481), add:

```javascript
/**
 * Get focus assist zones for a slide
 * @param {string} slideId - Slide ID
 * @param {Object} [options={}] - Options
 * @param {number} [options.topN=10] - Number of top zones
 * @param {number} [options.threshold=0.5] - Score threshold
 * @returns {Promise<Object>} Focus response with zones array
 */
async getFocusZones(slideId, options = {}) {
    const params = new URLSearchParams({
        top_n: options.topN || 10,
        threshold: options.threshold || 0.5,
    });
    return this.get(`/api/ml/focus/${encodeURIComponent(slideId)}?${params}`);
}
```

**Step 5: Commit**

```bash
git add backend/routes/ml.py backend/tests/test_focus_endpoint.py frontend/src/services/ApiService.js
git commit -m "feat(ml): add Focus Assist endpoint GET /ml/focus/{slide_id} (#70)"
```

---

### Task A2: FocusAssistPanel Frontend (#74)

**Files:**
- Create: `frontend/src/components/FocusAssistPanel.js`
- Create: `frontend/src/css/focus-assist.css`
- Modify: `frontend/src/components/ViewerPanel.js` (wire up panel)
- Modify: `frontend/src/style.css` (import CSS)
- Test: `frontend/e2e/tests/10-focus-assist.spec.js` (create)

**Step 1: Create FocusAssistPanel component**

Create `frontend/src/components/FocusAssistPanel.js`:

```javascript
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';

class FocusAssistPanel {
    constructor(container, options = {}) {
        this.container = container;
        this.viewerId = options.viewerId || null;
        this.slideId = null;
        this.zones = [];
        this.isCollapsed = true;
        this.isLoading = false;
        this.activeZoneIndex = null;
        this.element = null;
        this._overlayElements = [];
        this._build();
    }
```

Key methods:
- `_build()`: Create DOM elements using `document.createElement`. Accordion header with title "Zones d'interet IA" and chevron span, body hidden by default. Use `textContent` for all text. Same accordion pattern as MLPanel/DetectionPanel.
- `setSlide(slideId)`: Store slideId, reset zones, render idle state
- `_loadZones()`: Call `apiService.getFocusZones(this.slideId)`, populate `this.zones`, render list
- `_renderZoneList()`: Build DOM elements for each zone. Each zone item is a clickable div with: title "Zone {rank}", score badge built via `document.createElement('span')` with `textContent`, and a location pin button.
- `_onZoneClick(index)`: Set `activeZoneIndex`, emit `focus:zone-selected` event with bbox coordinates for viewport navigation.
- `_toggleCollapse()`: Same accordion pattern as MLPanel/DetectionPanel
- `destroy()`: Clean up

**NOTE:** All DOM construction must use safe methods (`document.createElement`, `textContent`, `appendChild`). Never use string-based HTML injection.

**Step 2: Create CSS**

Create `frontend/src/css/focus-assist.css` with styles for:
- `.focus-assist-panel` container
- `.focus-assist-panel__header--collapsible` + chevron (same pattern as other panels)
- `.focus-assist-panel__zone-item` clickable rows with hover state
- `.focus-assist-panel__score` badge (green >=0.8, yellow >=0.5, red <0.5)
- `.focus-assist-panel__zone-item--active` highlight for selected zone

**Step 3: Wire into ViewerPanel**

In `frontend/src/components/ViewerPanel.js`:
1. Add import: `import { FocusAssistPanel } from './FocusAssistPanel.js';`
2. Add property `this.focusAssistPanel = null;` in constructor
3. In `_toggleMLPanel()`, create FocusAssistPanel alongside DetectionPanel:
```javascript
if (!this.focusAssistPanel) {
    this.focusAssistPanel = new FocusAssistPanel(this.viewerContainer, {
        viewerId: this.viewer ? this.viewer.id : this.id,
    });
}
```
4. Toggle visibility with the ML button
5. In `loadSlide()`, notify focusAssistPanel: `if (this.focusAssistPanel) this.focusAssistPanel.setSlide(slideId);`

**Step 4: Handle zone navigation in ViewerPanel**

Listen for `focus:zone-selected` event in `_setupEventListeners()`:
```javascript
eventBus.on('focus:zone-selected', (data) => {
    if (data.viewerId === this.viewer?.id && this.viewer) {
        const rect = this.viewer.viewer.viewport.imageToViewportRectangle(
            data.bbox[0], data.bbox[1],
            data.bbox[2] - data.bbox[0], data.bbox[3] - data.bbox[1]
        );
        this.viewer.viewer.viewport.fitBounds(rect);
    }
});
```

**Step 5: Import CSS in style.css**

Add to `frontend/src/style.css`:
```css
@import './css/focus-assist.css';
```

**Step 6: E2E test**

Create `frontend/e2e/tests/10-focus-assist.spec.js`:
- Mock `GET /api/ml/focus/*` returning 3 zones with scores
- Open viewer, load slide, open ML panel
- Verify FocusAssistPanel is visible with accordion header
- Click a zone item, verify viewport navigation event
- Verify score badges render correctly

**Step 7: Commit**

```bash
git add frontend/src/components/FocusAssistPanel.js frontend/src/css/focus-assist.css \
    frontend/src/components/ViewerPanel.js frontend/src/style.css \
    frontend/e2e/tests/10-focus-assist.spec.js
git commit -m "feat(ux): add FocusAssistPanel with zone navigation (#74)"
```

---

## Group B: Measurement + Feedback

### Task B1: Measurement Backend — GET /ml/measure/{slide_id} (#77)

**Files:**
- Modify: `backend/routes/ml.py` (add endpoint + Pydantic models)
- Create: `backend/services/measurement.py` (Feret diameter computation)
- Test: `backend/tests/test_measurement.py` (create)

**Step 1: Create measurement service**

Create `backend/services/measurement.py`:

```python
"""
Measurement Service - Compute physical measurements from detected regions.

Converts pixel measurements to millimeters using slide MPP (microns per pixel).
Computes Feret diameter (max caliper diameter) for TNM staging.
"""

import numpy as np
from scipy.spatial.distance import pdist
from typing import List, Dict, Tuple

def compute_feret_diameter(contour_points: np.ndarray) -> float:
    """Compute Feret diameter (max distance between any two contour points)."""
    if len(contour_points) < 2:
        return 0.0
    distances = pdist(contour_points)
    return float(np.max(distances)) if len(distances) > 0 else 0.0

def pixels_to_mm(value_px: float, mpp: float) -> float:
    """Convert pixel measurement to millimeters. mpp = microns per pixel."""
    return value_px * mpp / 1000.0

def measure_regions(
    contours_with_confidence: List[Tuple[np.ndarray, float]],
    slide_dimensions: Tuple[int, int],
    heatmap_shape: Tuple[int, int],
    mpp: float,
) -> List[Dict]:
    """Measure all detected regions, converting to mm."""
    measurements = []
    scale_x = slide_dimensions[0] / heatmap_shape[1]
    scale_y = slide_dimensions[1] / heatmap_shape[0]

    for i, (contour, confidence) in enumerate(contours_with_confidence):
        # Scale contour to slide coordinates
        scaled = contour.copy().astype(float)
        scaled[:, 0] *= scale_x
        scaled[:, 1] *= scale_y

        feret_px = compute_feret_diameter(scaled)
        area_px = _polygon_area(scaled)
        perimeter_px = _polygon_perimeter(scaled)

        xs, ys = scaled[:, 0], scaled[:, 1]
        bbox = [float(np.min(xs)), float(np.min(ys)),
                float(np.max(xs)), float(np.max(ys))]

        measurements.append({
            "region_id": i,
            "label": "Tumor",
            "feret_diameter_mm": round(pixels_to_mm(feret_px, mpp), 2),
            "area_mm2": round(pixels_to_mm(area_px ** 0.5, mpp) ** 2, 2),
            "perimeter_mm": round(pixels_to_mm(perimeter_px, mpp), 2),
            "bbox_mm": [round(pixels_to_mm(v, mpp), 2) for v in bbox],
            "confidence": round(confidence, 4),
        })

    return measurements

def _polygon_area(points: np.ndarray) -> float:
    n = len(points)
    if n < 3:
        return 0.0
    x, y = points[:, 0], points[:, 1]
    return abs(float(
        np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])
        + x[-1] * y[0] - x[0] * y[-1]
    )) / 2.0

def _polygon_perimeter(points: np.ndarray) -> float:
    if len(points) < 2:
        return 0.0
    diffs = np.diff(points, axis=0, append=points[:1])
    return float(np.sum(np.sqrt(np.sum(diffs**2, axis=1))))
```

**Step 2: Add Pydantic models and endpoint to ml.py**

After the FocusResponse model, add:

```python
class RegionMeasurement(BaseModel):
    region_id: int
    label: str
    feret_diameter_mm: float
    area_mm2: float
    perimeter_mm: float
    bbox_mm: List[float]
    confidence: float

class MeasurementResponse(BaseModel):
    slide_id: str
    measurements: List[RegionMeasurement]
    mpp: float
    unit: str = "mm"
```

Endpoint:
```python
@router.get("/measure/{slide_id}", response_model=MeasurementResponse)
async def measure_slide(
    slide_id: str,
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    prediction_class: str = Query("tissue"),
    resolution_level: int = Query(2, ge=0, le=5),
    provider=Depends(get_ml_provider),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
```

Logic:
1. Get slide path, raise 404 if not found
2. Get MPP from OpenSlide: `openslide.OpenSlide(slide_path).properties.get('openslide.mpp-x', '0.25')`
3. Generate heatmap (check disk cache first)
4. Extract contours via `heatmap_to_contours`
5. Call `measure_regions()` from the new service
6. Return `MeasurementResponse`

**Step 3: Add requirements**

Add `scipy>=1.11.0` to `backend/requirements.txt` under a "Phase 6: Wave 2" section.

**Step 4: Write tests**

Create `backend/tests/test_measurement.py`:
- `test_feret_diameter_square`: 4-point square contour, Feret = diagonal
- `test_feret_diameter_line`: 2-point line, Feret = distance
- `test_pixels_to_mm`: Simple conversion (1000px at 0.25 mpp = 0.25mm)
- `test_measure_regions_basic`: Full pipeline with mock contours

**Step 5: Add ApiService method**

```javascript
async getMeasurement(slideId, options = {}) {
    const params = new URLSearchParams({
        threshold: options.threshold || 0.5,
        prediction_class: options.predictionClass || 'tissue',
    });
    return this.get(`/api/ml/measure/${encodeURIComponent(slideId)}?${params}`);
}
```

**Step 6: Commit**

```bash
git add backend/services/measurement.py backend/routes/ml.py \
    backend/tests/test_measurement.py backend/requirements.txt \
    frontend/src/services/ApiService.js
git commit -m "feat(ml): add measurement endpoint GET /ml/measure/{slide_id} (#77)"
```

---

### Task B2: Measurement Frontend — Dimensions in DetectionPanel (#79)

**Files:**
- Modify: `frontend/src/components/DetectionPanel.js` (add measurement display)
- Modify: `frontend/src/css/detection-panel.css` (measurement styles)

**Step 1: Add measurement fetching to DetectionPanel**

In `DetectionPanel._runDetection()`, after detection completes, also fetch measurements:

```javascript
// After this.detectionResult is set:
try {
    this.measurementResult = await apiService.getMeasurement(this.slideId, {
        threshold: this.threshold,
    });
} catch (e) {
    console.warn('[DetectionPanel] Measurement fetch failed:', e);
    this.measurementResult = null;
}
```

Add `this.measurementResult = null;` to constructor state and `_resetState()`.

**Step 2: Display measurements in detection items**

Modify `_renderDetectionItem()` to show dimensions when available:

```javascript
_renderDetectionItem(feature, index) {
    // ... existing code for the detection item ...
    const measurement = this.measurementResult?.measurements?.[index];
    const dimText = measurement
        ? `${measurement.feret_diameter_mm} mm`
        : '';
    // Add a span element with class "detection-item__dimension" showing dimText
    // Use textContent to set the text safely
}
```

**Step 3: Add CSS for dimension badge**

```css
.detection-item__dimension {
    font-size: 0.75rem;
    color: var(--color-info, #60a5fa);
    font-weight: 600;
    margin-left: 0.5rem;
}
```

**Step 4: Commit**

```bash
git add frontend/src/components/DetectionPanel.js frontend/src/css/detection-panel.css
git commit -m "feat(ux): display tumor dimensions in DetectionPanel (#79)"
```

---

### Task B3: Feedback Backend — POST /ml/feedback/{slide_id} (#85)

**Files:**
- Modify: `backend/routes/ml.py` (add endpoint + Pydantic models)
- Test: `backend/tests/test_feedback_endpoint.py` (create)

**Step 1: Add Pydantic models**

```python
class FeedbackRequest(BaseModel):
    """Pathologist feedback on an ML prediction."""
    original_annotation_id: str = Field(..., description="UUID of the original annotation")
    correction_type: str = Field(..., pattern="^(confirmed|rejected|refined|relabeled)$")
    corrected_class: Optional[str] = None
    corrected_geometry: Optional[Dict] = None
    notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    correction_id: str
    slide_id: str
    correction_type: str
    stats: Dict[str, int]
```

**Step 2: Add endpoint**

```python
@router.post("/feedback/{slide_id}", response_model=FeedbackResponse)
async def submit_feedback(
    slide_id: str,
    request: FeedbackRequest,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
```

Logic:
1. Validate `original_annotation_id` is a valid UUID
2. Create `Correction` ORM record:
   - `annotation_id` = request.original_annotation_id
   - `slide_id` = slide_id
   - `correction_type` = request.correction_type
   - `comment` = request.notes
   - `created_by` = current_user.username
3. If correction_type in ('rejected', 'confirmed'), optionally update original annotation's type
4. Query correction stats for this slide: `SELECT correction_type, COUNT(*) FROM corrections WHERE slide_id = ? GROUP BY correction_type`
5. Return `FeedbackResponse`

Database session: Use async session from `core.database`:
```python
from core.database import get_async_session
from models.correction import Correction
from sqlalchemy import select, func
```

**Step 3: Write tests**

Create `backend/tests/test_feedback_endpoint.py`:
- `test_submit_confirmed_feedback`: POST with correction_type=confirmed, verify 200 + correction_id returned
- `test_submit_rejected_feedback`: POST with correction_type=rejected
- `test_invalid_correction_type`: POST with correction_type=invalid, verify 422
- `test_feedback_stats`: Submit multiple corrections, verify stats dict

Note: Tests may require DB fixture or can use mocked session depending on test infrastructure.

**Step 4: Add ApiService method**

```javascript
async submitFeedback(slideId, feedback) {
    return this.post(`/api/ml/feedback/${encodeURIComponent(slideId)}`, feedback);
}
```

**Step 5: Commit**

```bash
git add backend/routes/ml.py backend/tests/test_feedback_endpoint.py \
    frontend/src/services/ApiService.js
git commit -m "feat(ml): add feedback endpoint POST /ml/feedback/{slide_id} (#85)"
```

---

### Task B4: Feedback Frontend — Confirm/Correct/Reject Buttons (#86)

**Files:**
- Modify: `frontend/src/components/DetectionPanel.js` (add feedback buttons)
- Modify: `frontend/src/css/detection-panel.css` (feedback button styles)
- Test: `frontend/e2e/tests/11-feedback.spec.js` (create)

**Step 1: Add feedback buttons to each detection item**

In `_renderDetectionItem()`, add feedback buttons after the existing accept/reject buttons. Use `document.createElement` for all elements:

- If `this.feedbackStatus.get(index)` exists, show a badge span with the status text
- Otherwise, show two buttons: "Confirmer" and "Rejeter"
- Both use `textContent` for labels (no string-based HTML)

**Step 2: Add feedback submission logic**

Add `this.feedbackStatus = new Map();` to constructor.

Add method:
```javascript
async _submitFeedback(index, correctionType) {
    const feature = this.detectionResult?.geojson?.features?.[index];
    if (!feature) return;

    try {
        await apiService.submitFeedback(this.slideId, {
            original_annotation_id: feature.id || `detection_${index}`,
            correction_type: correctionType,
            notes: null,
        });
        this.feedbackStatus.set(index, correctionType);
        this._renderPreview();
    } catch (err) {
        console.error('[DetectionPanel] Feedback failed:', err);
    }
}
```

**Step 3: Bind feedback buttons in `_renderPreview()`**

```javascript
this.element.querySelectorAll('.detection-item__fb-btn--confirm').forEach(btn => {
    btn.addEventListener('click', () => this._submitFeedback(
        parseInt(btn.dataset.index), 'confirmed'));
});
this.element.querySelectorAll('.detection-item__fb-btn--reject').forEach(btn => {
    btn.addEventListener('click', () => this._submitFeedback(
        parseInt(btn.dataset.index), 'rejected'));
});
```

**Step 4: Add CSS**

```css
.detection-item__feedback {
    display: flex;
    gap: 0.25rem;
    margin-top: 0.25rem;
}
.detection-item__fb-btn {
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid var(--border-color, #444);
    background: transparent;
    color: var(--text-secondary, #aaa);
    cursor: pointer;
}
.detection-item__fb-btn--confirm:hover {
    background: rgba(34, 197, 94, 0.2);
    border-color: #22c55e;
    color: #22c55e;
}
.detection-item__fb-btn--reject:hover {
    background: rgba(239, 68, 68, 0.2);
    border-color: #ef4444;
    color: #ef4444;
}
.detection-item__feedback-badge {
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 600;
}
.detection-item__feedback-badge--confirmed {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
}
.detection-item__feedback-badge--rejected {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
}
```

**Step 5: E2E test**

Create `frontend/e2e/tests/11-feedback.spec.js`:
- Mock detection results and feedback endpoint
- Run detection, verify feedback buttons appear
- Click "Confirmer", verify POST to /ml/feedback and badge appears
- Click "Rejeter", verify POST with correction_type=rejected

**Step 6: Commit**

```bash
git add frontend/src/components/DetectionPanel.js frontend/src/css/detection-panel.css \
    frontend/e2e/tests/11-feedback.spec.js
git commit -m "feat(ux): add Confirm/Reject feedback buttons in DetectionPanel (#86)"
```

---

## Group C: Auto-tag

### Task C1: Auto-tag Backend — GET /ml/tags/{slide_id} (#87)

**Files:**
- Modify: `backend/routes/ml.py` (add endpoint)
- Test: `backend/tests/test_tags_endpoint.py` (create)

**Step 1: Add Pydantic models and endpoint**

```python
class TagsResponse(BaseModel):
    slide_id: str
    tags: Dict[str, Optional[str]]
    source: str

@router.get("/tags/{slide_id}", response_model=TagsResponse)
async def get_slide_tags(
    slide_id: str,
    tag_extractor=Depends(get_tag_extractor),
    current_user: CurrentUser = Depends(get_current_user),
):
```

Logic:
1. Check MemoryCache first: `cache.get(f"tags:{slide_id}")`
2. If miss, get slide path, extract format from extension
3. Call `tag_extractor.extract_tags(slide_path, slide_format)`
4. Store in MemoryCache: `cache.set(f"tags:{slide_id}", tags)`
5. Return `TagsResponse` with tags dict and source

Add MemoryCache singleton dependency:
```python
from services.cache.memory_cache import MemoryCache

_memory_cache = None
def get_memory_cache():
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache(maxsize=512, ttl=300)
    return _memory_cache
```

**Step 2: Write tests**

Create `backend/tests/test_tags_endpoint.py`:
- `test_tags_from_filename`: Slide named "prostate_HE_sample.svs" returns organ=prostate, stain=H&E
- `test_tags_cache_hit`: Second call uses cache (verify cache.get is called)
- `test_tags_unknown_slide`: Slide with no identifiable tags returns null fields + source="manual_required"

**Step 3: Add ApiService method**

```javascript
async getSlideTags(slideId) {
    return this.get(`/api/ml/tags/${encodeURIComponent(slideId)}`);
}
```

**Step 4: Commit**

```bash
git add backend/routes/ml.py backend/tests/test_tags_endpoint.py \
    frontend/src/services/ApiService.js
git commit -m "feat(ml): add auto-tag endpoint GET /ml/tags/{slide_id} (#87)"
```

---

### Task C2: Auto-tag Frontend — Badge in Viewer Header (#88)

**Files:**
- Modify: `frontend/src/components/ViewerPanel.js` (add tag badge)
- Create: `frontend/src/css/auto-tag.css`
- Modify: `frontend/src/style.css` (import CSS)

**Step 1: Add tag loading to ViewerPanel.loadSlide()**

After `this.slideId = slideId;` and title update in `loadSlide()`, add:

```javascript
// Auto-tag: fetch and display slide tags
this._loadSlideTags(slideId);
```

Add methods using safe DOM construction only:
```javascript
async _loadSlideTags(slideId) {
    try {
        const result = await apiService.getSlideTags(slideId);
        this._renderTagBadge(result.tags);
    } catch (err) {
        console.warn('[ViewerPanel] Tag fetch failed:', err);
    }
}

_renderTagBadge(tags) {
    // Remove existing badge
    const existing = this.element.querySelector('.viewer-panel-tags');
    if (existing) existing.remove();

    const parts = [tags.organ, tags.stain, tags.pathology].filter(Boolean);
    if (parts.length === 0) return;

    const badge = document.createElement('div');
    badge.className = 'viewer-panel-tags';
    badge.textContent = parts.join(' \u2014 ');

    const header = this.element.querySelector('.viewer-panel-header');
    if (header) {
        header.appendChild(badge);
    }
}
```

**Step 2: Add CSS**

Create `frontend/src/css/auto-tag.css`:
```css
.viewer-panel-tags {
    font-size: 0.7rem;
    color: var(--text-secondary, #999);
    padding: 2px 8px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
    margin-left: auto;
    white-space: nowrap;
}
```

Import in `style.css`: `@import './css/auto-tag.css';`

**Step 3: E2E test**

Create `frontend/e2e/tests/12-auto-tag.spec.js`:
- Mock `GET /api/ml/tags/*` returning organ=Prostate, stain=H&E
- Load a slide, verify `.viewer-panel-tags` appears with expected text

**Step 4: Commit**

```bash
git add frontend/src/components/ViewerPanel.js frontend/src/css/auto-tag.css \
    frontend/src/style.css frontend/e2e/tests/12-auto-tag.spec.js
git commit -m "feat(ux): display auto-tag badge in viewer header (#88)"
```

---

## Group D: Infrastructure

### Task D1: Background Embeddings Pre-computation (#89)

**Files:**
- Modify: `backend/routes/slides.py` (trigger background task on slide info)
- Create: `backend/services/background_tasks.py` (pre-computation service)
- Test: `backend/tests/test_background_tasks.py` (create)

**Step 1: Create background task service**

Create `backend/services/background_tasks.py`:

```python
"""
Background Tasks Service - Pre-computation of ML embeddings.

Triggered when a slide is opened. Checks disk cache first,
then runs extraction via MLProvider in background.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Track in-progress tasks to avoid duplicates
_active_tasks = set()

async def precompute_embeddings(slide_id: str, slide_path: str):
    """Pre-compute and cache embeddings for a slide."""
    if slide_id in _active_tasks:
        logger.debug("Embeddings already being computed for %s", slide_id)
        return

    _active_tasks.add(slide_id)
    try:
        from services.cache.disk_cache import DiskCache
        cache = DiskCache()

        # Check cache first
        model_name = os.getenv("ML_EXTRACTOR", "resnet50_imagenet")
        if cache.exists(slide_id, model_name, "embeddings"):
            logger.debug("Embeddings already cached for %s", slide_id)
            return

        # Extract features
        from core.interfaces import get_provider
        provider_name = os.getenv("ML_PROVIDER", "slideflow")
        provider = get_provider(provider_name)

        if not provider.model_loaded:
            logger.warning(
                "ML provider not loaded, skipping pre-computation for %s",
                slide_id,
            )
            return

        result = provider.extract_features(slide_path, tile_size=224, overlap=0)

        # Cache to disk
        cache.save_embeddings(slide_id, model_name, result.embeddings)
        logger.info(
            "Pre-computed embeddings for %s: %s",
            slide_id, result.embeddings.shape,
        )

    except Exception as e:
        logger.error(
            "Background embedding extraction failed for %s: %s",
            slide_id, e,
        )
    finally:
        _active_tasks.discard(slide_id)
```

**Step 2: Trigger from slide info endpoint**

In `backend/routes/slides.py`, modify `get_slide_info()`:

Add `BackgroundTasks` parameter:
```python
from fastapi import BackgroundTasks

@router.get("/{slide_id}/info", tags=["visualization"])
def get_slide_info(
    slide_id: str,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
):
```

After `metadata = get_slide_metadata(slide_path)`, add:
```python
    # Trigger background embedding pre-computation
    import os
    if os.getenv("ML_ENABLED", "true").lower() == "true":
        from services.background_tasks import precompute_embeddings
        background_tasks.add_task(precompute_embeddings, slide_id, slide_path)
```

**Step 3: Write tests**

Create `backend/tests/test_background_tasks.py`:
- `test_precompute_skips_if_cached`: Mock DiskCache.exists returning True, verify extract_features NOT called
- `test_precompute_saves_to_cache`: Mock provider returning embeddings, verify DiskCache.save_embeddings called
- `test_precompute_handles_provider_error`: Mock provider raising, verify no crash
- `test_precompute_deduplicates`: Call twice, verify only one extraction runs

**Step 4: Commit**

```bash
git add backend/services/background_tasks.py backend/routes/slides.py \
    backend/tests/test_background_tasks.py
git commit -m "feat(infra): background embeddings pre-computation on slide load (#89)"
```

---

### Task D2: ML Model Selector UX (#91)

**Files:**
- Modify: `frontend/src/components/MLPanel.js` (add model dropdown)
- Modify: `frontend/src/css/ml-panel.css` (dropdown styles)

**Step 1: Add model loading to MLPanel**

In `MLPanel._build()`, add a model selector dropdown before the predict button. Build using `document.createElement`:

```javascript
const modelSelector = document.createElement('div');
modelSelector.className = 'ml-panel__model-selector';

const modelLabel = document.createElement('label');
modelLabel.className = 'ml-panel__model-label';
modelLabel.textContent = 'Modele IA';
modelSelector.appendChild(modelLabel);

const modelSelect = document.createElement('select');
modelSelect.className = 'ml-panel__model-select';
modelSelect.disabled = true;
const defaultOpt = document.createElement('option');
defaultOpt.value = '';
defaultOpt.textContent = 'Chargement...';
modelSelect.appendChild(defaultOpt);
modelSelector.appendChild(modelSelect);
```

Insert before the actions div in the panel content.

**Step 2: Fetch models on panel creation**

Add method:
```javascript
async _loadModels() {
    try {
        const models = await apiService.listModels();
        this._populateModelSelector(models);
    } catch (err) {
        console.warn('[MLPanel] Could not load models:', err);
    }
}
```

Model name mapping (technical to friendly):
```javascript
_friendlyModelName(model) {
    const nameMap = {
        'ctranspath': 'CTransPath',
        'phikon': 'Phikon v2',
        'uni': 'UNI',
        'resnet50_imagenet': 'ResNet-50',
    };
    const name = model.model_name || model.model_id;
    for (const [key, friendly] of Object.entries(nameMap)) {
        if (name.toLowerCase().includes(key)) return friendly;
    }
    return name;
}
```

Populate selector using `document.createElement('option')` with `textContent` for each model.

**Step 3: Wire selected model to prediction**

Store `this.selectedModelId` and pass it to `apiService.predict()`:
```javascript
async _runPrediction() {
    // ... existing code ...
    const result = await apiService.predict(this.slideId, {
        numMcSamples: 10,
        modelId: this.selectedModelId || undefined,
    });
}
```

**Step 4: Add CSS**

```css
.ml-panel__model-selector {
    margin-bottom: 0.5rem;
}
.ml-panel__model-label {
    font-size: 0.75rem;
    color: var(--text-secondary, #aaa);
    display: block;
    margin-bottom: 0.25rem;
}
.ml-panel__model-select {
    width: 100%;
    padding: 4px 8px;
    background: var(--bg-secondary, #2a2a2a);
    color: var(--text-primary, #eee);
    border: 1px solid var(--border-color, #444);
    border-radius: 4px;
    font-size: 0.8rem;
}
```

**Step 5: Commit**

```bash
git add frontend/src/components/MLPanel.js frontend/src/css/ml-panel.css
git commit -m "feat(ux): user-friendly ML model selector dropdown (#91)"
```

---

## E2E Test Mocks Update

### Task E1: Update API Mocks for Wave 2

**Files:**
- Modify: `frontend/e2e/helpers/api-mock.js` (add Wave 2 endpoint mocks)

Add mocks for all new endpoints:
- `mockFocusAssist(page)`: Mock `GET /api/ml/focus/*` with 3 sample zones
- `mockMeasurement(page)`: Mock `GET /api/ml/measure/*` with 2 measurements
- `mockFeedback(page)`: Mock `POST /api/ml/feedback/*` returning success
- `mockSlideTags(page)`: Mock `GET /api/ml/tags/*` returning organ/stain tags

Add these to `setupFullMocks()` function.

**Commit:**
```bash
git add frontend/e2e/helpers/api-mock.js
git commit -m "test(e2e): add Wave 2 API mocks for focus, measurement, feedback, tags"
```

---

## Verification

```bash
# Backend unit tests
cd /data/VarunaPoC/backend && python -m pytest tests/test_focus_endpoint.py tests/test_measurement.py tests/test_feedback_endpoint.py tests/test_tags_endpoint.py tests/test_background_tasks.py -v

# Existing tests still pass
cd /data/VarunaPoC/backend && python -m pytest tests/test_disk_cache.py tests/test_memory_cache.py -v

# E2E tests (requires Playwright)
cd /data/VarunaPoC/frontend && npx playwright test e2e/tests/10-focus-assist.spec.js e2e/tests/11-feedback.spec.js e2e/tests/12-auto-tag.spec.js

# All E2E
cd /data/VarunaPoC/frontend && npx playwright test
```

---

## Implementation Order

1. **Groups A, B, C, D execute in parallel** (no cross-dependencies)
2. Within Group B, tasks are sequential: B1 then B2, B3 then B4
3. Task E1 (mock updates) can run last after all groups complete
4. Final verification: run all tests, push, create PR
