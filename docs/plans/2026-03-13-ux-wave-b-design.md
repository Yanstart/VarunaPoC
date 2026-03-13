# UX Wave B: ML UX + Navigation — Design

**Goal:** Improve ML visualization UX (progress, legends, markers, corrections) and add slide navigation within cases.

**Issues:** #152, #153, #154, #157, #163, #166

**Architecture:** Event-driven — new components subscribe to existing EventBus events. Backend extended for cell positions. Canvas overlays reuse existing OSD integration pattern from HeatmapOverlay/ClusteringOverlay.

---

## 1. FocusAssist Zone Navigation (#152)

### Problem

FocusAssistPanel emits `'focus:zone-selected'` on zone click, but nothing handles it. The viewer doesn't pan/zoom to the selected zone.

### Solution

Register the event in Constants.js as `FOCUS_ZONE_NAVIGATE`. Router listens and calls `viewerInstance.setViewport()` to fit the zone bbox with 20% padding.

### Data Flow

```
FocusAssistPanel._selectZone(index)
  → eventBus.emit(FOCUS_ZONE_NAVIGATE, {bbox, centroid, slideId})
  → Router handler
  → viewerInstance.setViewport({x, y, width, height})
```

Zone payload already contains `bbox: [x_min, y_min, x_max, y_max]` in slide pixel coordinates. ViewerInstance.setViewport() accepts normalized coords, so we convert via slide dimensions.

### Files

- MODIFY: `frontend/src/core/Constants.js` — add `FOCUS_ZONE_NAVIGATE` event
- MODIFY: `frontend/src/components/FocusAssistPanel.js` — use Constants event instead of string literal
- MODIFY: `frontend/src/core/Router.js` — add zone navigate listener (~15 lines)

---

## 2. Next/Prev Slide Navigation (#166)

### Problem

No way to quickly navigate between sibling slides in a case without returning to home page or using the sidebar.

### Solution

Add prev/next buttons in the viewer header (between compare and ML buttons). Store case slides array and current index in Router state. Add keyboard shortcuts (ArrowLeft/ArrowRight when no input focused).

### UI

```
[← Back]  Slide Name  [◀ Prev] [Next ▶]  [Compare] [ML] [Theme] [Lang] [User]
```

Buttons disabled at first/last slide. Show "N/M" counter between buttons.

### Events

```javascript
SLIDE_NAV_PREV: 'ui:slideNavPrev'   // Keyboard or button
SLIDE_NAV_NEXT: 'ui:slideNavNext'
```

### Files

- MODIFY: `frontend/src/core/Constants.js` — add nav events
- MODIFY: `frontend/src/core/Router.js` — add nav buttons to `_buildViewerHeader()`, store slide index, add keyboard listener, add event handlers (~60 lines)
- MODIFY: `frontend/src/locales/*.json` — add `"nav.prevSlide"`, `"nav.nextSlide"` keys
- MODIFY: `frontend/src/css/viewer.css` or similar — button styling

---

## 3. ML Progress Indicator (#157)

### Problem

Each ML panel has its own isolated spinner. No global indicator when ML operations are running.

### Solution

New `MLProgressBar` singleton component — thin animated bar at top of `.viewer-area`. Subscribes to `ML_WORKER_BUSY`/`ML_WORKER_FREE` events, tracks active operation count.

### UI

```
┌─ viewer-area ─────────────────────────────┐
│ ███████████░░░░░░░░░░░░  1 analyse en cours│  ← thin bar (3px) + label
│                                            │
│          [OpenSeadragon viewer]             │
│                                            │
└────────────────────────────────────────────┘
```

- Count > 0: indeterminate animated bar (CSS animation, blue gradient shimmer)
- Count → 0: brief green flash (300ms), then hide
- Label shows count + "analyse(s) en cours"

### Files

- NEW: `frontend/src/components/MLProgressBar.js` (~90 lines)
- NEW: `frontend/src/css/ml-progress.css` (~40 lines)
- MODIFY: `frontend/src/core/Router.js` — mount in viewer-area, add to destroyKeys

---

## 4. Heatmap Color Legend (#153)

### Problem

Heatmap overlay uses jet colormap (blue→red) but shows no visual reference for what colors mean.

### Solution

New `HeatmapLegend` component — small gradient bar shown when heatmap is visible. Positioned bottom-left of viewer area.

### UI

```
┌────────────────────────────┐
│  Faible ▓▓▓▓▓▓▓▓▓ Élevé   │  ← gradient: blue→cyan→green→yellow→red
│         Attention           │
└────────────────────────────┘
```

- Shows/hides with `ML_HEATMAP_TOGGLE` event
- Opacity follows `ML_HEATMAP_OPACITY_CHANGE`
- Pure CSS gradient (no canvas needed)

### Files

- NEW: `frontend/src/components/HeatmapLegend.js` (~80 lines)
- NEW: `frontend/src/css/heatmap-legend.css` (~35 lines)
- MODIFY: `frontend/src/core/Router.js` — mount in viewer-area, add to destroyKeys
- MODIFY: `frontend/src/locales/*.json` — add legend label keys

---

## 5. Detection Correction UX (#163)

### Problem

DetectionPanel has confirm/reject/refine feedback buttons but no toast feedback on submission. Hovering a detection item doesn't highlight the region on the slide consistently.

### Solution

Enhance existing DetectionPanel with:
- Emit `TOAST_SHOW` success on feedback submission
- Emit `DETECTION_HIGHLIGHT` on detection item hover (event already exists)
- Clear highlight on mouseleave
- Visual badge for feedback status (checkmark/cross/edit icon)

### Files

- MODIFY: `frontend/src/components/DetectionPanel.js` — add toast emit, hover highlight emit (~30 lines)

---

## 6. Cell Marker Overlay (#154)

### Problem

CellCountingPanel shows only text results (counts, percentage). No spatial visualization of where cells are.

### Solution

**Backend:** Extend `CellCountResult` to include cell positions. The `_count_real()` method already computes contour centroids internally — just expose them. Add `include_positions` query parameter.

**Frontend:** New `CellMarkerOverlay` (canvas-based, same pattern as ClusteringOverlay). Renders colored dots: green (positive), red/blue (negative). Toggle + opacity controls in CellCountingPanel.

### Backend Response Extension

```python
@dataclass
class CellCountResult:
    total_cells: int
    positive: int
    negative: int
    ratio: float
    percentage: str
    processing_time_ms: float
    metadata: Optional[Dict] = field(default_factory=dict)
    cells: Optional[List[Dict]] = None  # [{x, y, positive: bool}, ...]
```

Positions are centroids of contours in heatmap space, scaled to slide pixel coordinates.

### Events

```javascript
CELL_MARKERS_TOGGLE: 'cellCounting:markersToggle'    // {visible: boolean}
CELL_MARKERS_OPACITY: 'cellCounting:markersOpacity'   // {opacity: number}
```

### Files

- MODIFY: `backend/services/ml/counting.py` — compute and return cell positions (~25 lines)
- MODIFY: `backend/routes/ml.py` — add `include_positions` param to count endpoint (~5 lines)
- NEW: `frontend/src/components/CellMarkerOverlay.js` (~150 lines)
- NEW: `frontend/src/css/cell-markers.css` (~20 lines)
- MODIFY: `frontend/src/core/Constants.js` — add cell marker events
- MODIFY: `frontend/src/components/CellCountingPanel.js` — add toggle + opacity controls (~30 lines)
- MODIFY: `frontend/src/core/Router.js` — mount overlay, add to destroyKeys
- MODIFY: `frontend/src/services/ApiService.js` — add `include_positions` param

---

## Dependency Order

```
Constants.js events (foundation)
  ├── #152 FocusAssist nav (independent)
  ├── #166 Next/prev nav (independent)
  ├── #157 ML progress bar (independent)
  ├── #153 Heatmap legend (independent)
  ├── #163 Correction UX (independent)
  └── #154 Cell markers (backend → frontend)
```

Implementation order: Constants → (#152, #166, #157, #153, #163 in parallel) → #154 (backend then frontend)
