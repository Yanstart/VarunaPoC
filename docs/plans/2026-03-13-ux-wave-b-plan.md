# UX Wave B Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add ML progress indicator, heatmap legend, focus zone navigation, slide prev/next, detection correction UX, and cell marker overlay.

**Architecture:** Event-driven components on EventBus. Canvas overlays follow existing HeatmapOverlay/ClusteringOverlay pattern. Backend extended for cell positions.

**Tech Stack:** Vanilla JS, CSS variables from `variables.css`, EventBus pub-sub, DOM API, canvas 2D. Backend: Python dataclass + FastAPI.

**Note on innerHTML usage:** This plan uses innerHTML ONLY for static SVG icon constants defined in the source code — never for user-supplied data. Same safe pattern as MLTabsContainer.js, DetectionPanel.js, ToastManager.js.

---

### Task 1: Add new events to Constants.js

**Files:**
- Modify: `frontend/src/core/Constants.js:91,177,189`

**Step 1: Add UI events**

In `frontend/src/core/Constants.js`, in the `// -- UI --` section, after `TOAST_SHOW` (line 91), add:

```javascript
    /** @payload {{ slideId: string, bbox: number[], centroid: number[] }} */
    FOCUS_ZONE_NAVIGATE: 'ui:focusZoneNavigate',
    /** @payload (none) */
    SLIDE_NAV_PREV: 'ui:slideNavPrev',
    /** @payload (none) */
    SLIDE_NAV_NEXT: 'ui:slideNavNext',
```

**Step 2: Add cell marker events**

After `CELL_COUNTING_ERROR` (line 177), add:

```javascript
    /** @payload {{ visible: boolean }} */
    CELL_MARKERS_TOGGLE: 'cellCounting:markersToggle',
    /** @payload {{ opacity: number }} */
    CELL_MARKERS_OPACITY: 'cellCounting:markersOpacity',
```

**Step 3: Verify lint passes**

Run: `cd frontend && npx eslint src/core/Constants.js`
Expected: no errors

**Step 4: Commit**

```bash
git add frontend/src/core/Constants.js
git commit -m "feat(constants): add Wave B events for navigation, progress, cell markers

Fixes #152, #154, #157, #166"
```

---

### Task 2: Create MLProgressBar component + CSS

**Files:**
- Create: `frontend/src/components/MLProgressBar.js`
- Create: `frontend/src/css/ml-progress.css`
- Modify: `frontend/src/style.css` (add CSS import)

**Step 1: Create MLProgressBar.js**

Create `frontend/src/components/MLProgressBar.js` with:

- Import `eventBus` from `'../core/EventBus.js'` and `Events` from `'../core/Constants.js'`
- Import `i18nService` from `'../services/I18nService.js'`
- Class `MLProgressBar` with constructor receiving `container` (HTMLElement)
- `_build()`: Create `div.ml-progress-bar` container with:
  - `div.ml-progress-bar__track` (the animated bar)
  - `span.ml-progress-bar__label` (text: "1 analyse en cours")
  - Initially hidden (`display: none`)
- `_setupEventListeners()`: Subscribe to:
  - `Events.ML_WORKER_BUSY` → increment `this._activeCount`, call `_update()`
  - `Events.ML_WORKER_FREE` → decrement `this._activeCount` (min 0), call `_update()`
- `_update()`:
  - If `_activeCount > 0`: show bar, set label text to `${count} analyse(s) en cours`, add class `ml-progress-bar--active`
  - If `_activeCount === 0`: add class `ml-progress-bar--done` (green flash), then after 800ms hide and remove classes
- `destroy()`: Unsubscribe all events, remove DOM, reset state
- Store unsubscribers in `this._unsubscribers` array

Key state:
- `this._activeCount = 0`
- `this._hideTimer = null` (for the delayed hide after completion)

**Step 2: Create ml-progress.css**

Create `frontend/src/css/ml-progress.css` with:

- `.ml-progress-bar` — position absolute, top 0, left 0, right 0, height 3px, z-index 300, display none, pointer-events none
- `.ml-progress-bar--active` — display block
- `.ml-progress-bar__track` — height 100%, background linear-gradient(90deg, var(--color-primary) 0%, var(--color-primary-light, #60a5fa) 50%, var(--color-primary) 100%), background-size 200% 100%, animation `ml-progress-shimmer 1.5s ease-in-out infinite`
- `.ml-progress-bar--done .ml-progress-bar__track` — background var(--color-success), animation none
- `.ml-progress-bar__label` — position absolute, top 6px, right 8px, font-size 11px, color var(--color-text-secondary), background var(--color-bg-elevated), padding 2px 8px, border-radius 4px, box-shadow
- `@keyframes ml-progress-shimmer` — `0% { background-position: 200% 0 }` → `100% { background-position: -200% 0 }`

**Step 3: Import CSS in style.css**

In `frontend/src/style.css`, add `@import './css/ml-progress.css';` near the other CSS imports.

**Step 4: Verify lint and build**

Run: `cd frontend && npx eslint src/components/MLProgressBar.js && npm run build`
Expected: no errors, build succeeds

**Step 5: Commit**

```bash
git add frontend/src/components/MLProgressBar.js frontend/src/css/ml-progress.css frontend/src/style.css
git commit -m "feat(progress): add MLProgressBar global progress indicator

Fixes #157"
```

---

### Task 3: Create HeatmapLegend component + CSS

**Files:**
- Create: `frontend/src/components/HeatmapLegend.js`
- Create: `frontend/src/css/heatmap-legend.css`
- Modify: `frontend/src/style.css` (add CSS import)
- Modify: `frontend/src/locales/*.json` (5 locale files)

**Step 1: Create HeatmapLegend.js**

Create `frontend/src/components/HeatmapLegend.js` with:

- Import `eventBus` from `'../core/EventBus.js'`, `Events` from `'../core/Constants.js'`, `i18nService` from `'../services/I18nService.js'`
- Class `HeatmapLegend` with constructor receiving `container` (HTMLElement)
- `_build()`: Create `div.heatmap-legend` (initially hidden, `display: none`) with:
  - `span.heatmap-legend__label-low` text: i18n `"legend.low"` (default "Faible")
  - `div.heatmap-legend__gradient` — empty div styled with CSS gradient
  - `span.heatmap-legend__label-high` text: i18n `"legend.high"` (default "Élevé")
  - `div.heatmap-legend__title` text: i18n `"legend.attention"` (default "Attention")
- `_setupEventListeners()`:
  - `Events.ML_HEATMAP_TOGGLE` → show/hide based on `{visible}` payload
  - `Events.ML_HEATMAP_OPACITY_CHANGE` → set element opacity to match heatmap
  - `Events.LOCALE_CHANGED` → update text labels
- `destroy()`: Unsubscribe, remove DOM

**Step 2: Create heatmap-legend.css**

Create `frontend/src/css/heatmap-legend.css` with:

- `.heatmap-legend` — position absolute, bottom 12px, left 12px, z-index 300, display none, flex row, align-items center, gap 6px, background var(--color-bg-elevated), padding 6px 10px, border-radius 6px, box-shadow, pointer-events auto, font-size 11px
- `.heatmap-legend--visible` — display flex
- `.heatmap-legend__gradient` — width 120px, height 10px, border-radius 3px, background: `linear-gradient(90deg, #0000ff 0%, #00ffff 25%, #00ff00 50%, #ffff00 75%, #ff0000 100%)`
- `.heatmap-legend__label-low`, `.heatmap-legend__label-high` — color var(--color-text-secondary), font-size 10px, white-space nowrap
- `.heatmap-legend__title` — position absolute, bottom -14px, left 50%, transform translateX(-50%), font-size 9px, color var(--color-text-tertiary), white-space nowrap

**Step 3: Import CSS in style.css**

Add `@import './css/heatmap-legend.css';` in `frontend/src/style.css`.

**Step 4: Add i18n keys**

Add to each locale file after existing keys:

- `frontend/src/locales/fr.json`: `"legend.low": "Faible"`, `"legend.high": "Élevé"`, `"legend.attention": "Attention"`
- `frontend/src/locales/en.json`: `"legend.low": "Low"`, `"legend.high": "High"`, `"legend.attention": "Attention"`
- `frontend/src/locales/ja.json`: `"legend.low": "低"`, `"legend.high": "高"`, `"legend.attention": "注意"`
- `frontend/src/locales/zh.json`: `"legend.low": "低"`, `"legend.high": "高"`, `"legend.attention": "注意"`
- `frontend/src/locales/hi.json`: `"legend.low": "कम"`, `"legend.high": "उच्च"`, `"legend.attention": "ध्यान"`

**Step 5: Verify lint and build**

Run: `cd frontend && npx eslint src/components/HeatmapLegend.js && npm run build`
Expected: no errors

**Step 6: Commit**

```bash
git add frontend/src/components/HeatmapLegend.js frontend/src/css/heatmap-legend.css frontend/src/style.css frontend/src/locales/*.json
git commit -m "feat(legend): add HeatmapLegend color scale for ML heatmap

Fixes #153"
```

---

### Task 4: Wire FocusAssist zone navigation (#152)

**Files:**
- Modify: `frontend/src/components/FocusAssistPanel.js:390-410`
- Modify: `frontend/src/core/Router.js:989-1012`

**Step 1: Update FocusAssistPanel to use Constants event**

In `frontend/src/components/FocusAssistPanel.js`, find the `_selectZone` method (around line 390-410). Replace the custom event string:

```javascript
eventBus.emit('focus:zone-selected', {
```

with:

```javascript
eventBus.emit(Events.FOCUS_ZONE_NAVIGATE, {
```

Ensure `Events` is imported at the top of the file from `'../core/Constants.js'`. It should already be imported — verify.

**Step 2: Add zone navigate handler in Router**

In `frontend/src/core/Router.js`, in the `showViewerPage` method (or a new `_setupViewerEventListeners` method), after creating the viewerInstance, add:

```javascript
        // Focus zone navigation — pan+zoom viewer to selected zone
        this._state._focusNavUnsub = eventBus.on(Events.FOCUS_ZONE_NAVIGATE, ({ bbox }) => {
            const vi = this._state.viewerInstance;
            if (!vi || !bbox || bbox.length !== 4) return;

            const [xMin, yMin, xMax, yMax] = bbox;
            const padding = 0.2; // 20% padding around zone
            const w = xMax - xMin;
            const h = yMax - yMin;
            const padW = w * padding;
            const padH = h * padding;

            // Convert slide pixel bbox to normalized viewport coords
            const dims = vi.getSlideDimensions?.() || vi.dimensions;
            if (!dims) return;
            const slideW = dims.width || dims.x;
            const slideH = dims.height || dims.y;

            vi.setViewport({
                x: (xMin - padW) / slideW,
                y: (yMin - padH) / slideH,
                width: (w + 2 * padW) / slideW,
                height: (h + 2 * padH) / slideH,
            });
        });
```

Also add cleanup in `_cleanup()`: call `this._state._focusNavUnsub?.()` before the destroyKeys loop.

**Step 3: Verify getSlideDimensions or dimensions property**

Check that `ViewerInstance` exposes slide dimensions. It should have `this.dimensions` set during initialization from the slide info. If the property name differs, adjust accordingly.

**Step 4: Verify lint**

Run: `cd frontend && npx eslint src/components/FocusAssistPanel.js src/core/Router.js`
Expected: no errors

**Step 5: Commit**

```bash
git add frontend/src/components/FocusAssistPanel.js frontend/src/core/Router.js
git commit -m "feat(focus): wire zone navigation to viewer pan+zoom

Fixes #152"
```

---

### Task 5: Add prev/next slide navigation (#166)

**Files:**
- Modify: `frontend/src/core/Router.js:894-987,1029-1061`
- Modify: `frontend/src/locales/*.json` (5 locale files)

**Step 1: Add i18n keys**

Add to each locale file:

- `fr.json`: `"nav.prevSlide": "Lame précédente"`, `"nav.nextSlide": "Lame suivante"`, `"nav.slidePosition": "{current}/{total}"`
- `en.json`: `"nav.prevSlide": "Previous slide"`, `"nav.nextSlide": "Next slide"`, `"nav.slidePosition": "{current}/{total}"`
- `ja.json`: `"nav.prevSlide": "前のスライド"`, `"nav.nextSlide": "次のスライド"`, `"nav.slidePosition": "{current}/{total}"`
- `zh.json`: `"nav.prevSlide": "上一张"`, `"nav.nextSlide": "下一张"`, `"nav.slidePosition": "{current}/{total}"`
- `hi.json`: `"nav.prevSlide": "पिछली स्लाइड"`, `"nav.nextSlide": "अगली स्लाइड"`, `"nav.slidePosition": "{current}/{total}"`

**Step 2: Store case slides in Router state**

In `Router._initCaseSidebar()` (line 1029-1061), after `caseSlides` is populated, store it:

```javascript
        this._state.caseSlides = caseSlides;
        this._state.currentSlideId = slide.id;
```

**Step 3: Add nav buttons in _buildViewerHeader**

In `_buildViewerHeader(slide)` (line 894), after `header.appendChild(titleDiv)` (line 920) and before the compare button (line 923), insert a nav button group:

```javascript
        // Slide navigation buttons
        const navGroup = document.createElement('div');
        navGroup.className = 'viewer-header__nav';
        navGroup.id = 'slide-nav-group';
        navGroup.style.display = 'none'; // Hidden until case loaded

        const prevBtn = document.createElement('button');
        prevBtn.className = 'header-button header-button--nav';
        prevBtn.id = 'slide-nav-prev';
        prevBtn.title = this._t('nav.prevSlide');
        prevBtn.disabled = true;
        prevBtn.textContent = '◀';
        prevBtn.addEventListener('click', () => eventBus.emit(Events.SLIDE_NAV_PREV));

        const posLabel = document.createElement('span');
        posLabel.className = 'viewer-header__nav-pos';
        posLabel.id = 'slide-nav-pos';
        posLabel.textContent = '';

        const nextBtn = document.createElement('button');
        nextBtn.className = 'header-button header-button--nav';
        nextBtn.id = 'slide-nav-next';
        nextBtn.title = this._t('nav.nextSlide');
        nextBtn.disabled = true;
        nextBtn.textContent = '▶';
        nextBtn.addEventListener('click', () => eventBus.emit(Events.SLIDE_NAV_NEXT));

        navGroup.appendChild(prevBtn);
        navGroup.appendChild(posLabel);
        navGroup.appendChild(nextBtn);
        header.appendChild(navGroup);
```

**Step 4: Add navigation event handlers**

In the Router constructor or `showViewerPage`, add event listeners:

```javascript
        this._state._slideNavPrevUnsub = eventBus.on(Events.SLIDE_NAV_PREV, () => {
            this._navigateSlide(-1);
        });
        this._state._slideNavNextUnsub = eventBus.on(Events.SLIDE_NAV_NEXT, () => {
            this._navigateSlide(1);
        });
```

Add a new method `_navigateSlide(delta)`:

```javascript
    _navigateSlide(delta) {
        const slides = this._state.caseSlides;
        const currentId = this._state.currentSlideId;
        if (!slides || slides.length <= 1) return;

        const idx = slides.findIndex(s => s.id === currentId);
        if (idx < 0) return;

        const newIdx = idx + delta;
        if (newIdx < 0 || newIdx >= slides.length) return;

        this._handleSlideSwitch(slides[newIdx]);
    }
```

**Step 5: Update nav UI after case sidebar loads**

After `this._state.caseSlides = caseSlides`, call `this._updateSlideNav()`:

```javascript
    _updateSlideNav() {
        const slides = this._state.caseSlides;
        const currentId = this._state.currentSlideId;
        const navGroup = document.getElementById('slide-nav-group');
        if (!navGroup || !slides || slides.length <= 1) return;

        navGroup.style.display = 'flex';
        const idx = slides.findIndex(s => s.id === currentId);

        const prevBtn = document.getElementById('slide-nav-prev');
        const nextBtn = document.getElementById('slide-nav-next');
        const posLabel = document.getElementById('slide-nav-pos');

        if (prevBtn) prevBtn.disabled = idx <= 0;
        if (nextBtn) nextBtn.disabled = idx >= slides.length - 1;
        if (posLabel) posLabel.textContent = `${idx + 1}/${slides.length}`;
    }
```

**Step 6: Add keyboard shortcuts**

In `showViewerPage`, add a keydown listener on `document`:

```javascript
        this._state._keyNavHandler = (e) => {
            // Don't navigate if typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
            if (e.key === 'ArrowLeft') eventBus.emit(Events.SLIDE_NAV_PREV);
            if (e.key === 'ArrowRight') eventBus.emit(Events.SLIDE_NAV_NEXT);
        };
        document.addEventListener('keydown', this._state._keyNavHandler);
```

Clean up in `_cleanup()`: `document.removeEventListener('keydown', this._state._keyNavHandler)`.

**Step 7: Verify lint**

Run: `cd frontend && npx eslint src/core/Router.js`
Expected: no errors

**Step 8: Commit**

```bash
git add frontend/src/core/Router.js frontend/src/locales/*.json
git commit -m "feat(nav): add prev/next slide navigation with keyboard shortcuts

Fixes #166"
```

---

### Task 6: Enhance detection correction UX (#163)

**Files:**
- Modify: `frontend/src/components/DetectionPanel.js:427-500`

**Step 1: Add toast on feedback submission**

In `frontend/src/components/DetectionPanel.js`, find the `_submitFeedback` method. After the successful API call, add:

```javascript
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: type === 'confirmed' ? 'Feedback confirmé'
                    : type === 'rejected' ? 'Feedback rejeté'
                    : 'Correction enregistrée',
                duration: 2000,
            });
```

**Step 2: Add hover highlight on detection items**

In the detection item event handling (the delegated click/mouse handlers), add mouseenter/mouseleave handlers for `.detection-item` elements:

In the `_setupResultEventListeners()` or wherever detection item interactions are wired, add:

```javascript
        // Hover highlight on detection items
        this._resultContainer.addEventListener('mouseenter', (e) => {
            const item = e.target.closest('[data-detection-item-index]');
            if (item) {
                const idx = parseInt(item.dataset.detectionItemIndex, 10);
                eventBus.emit(Events.DETECTION_HIGHLIGHT, { regionIndex: idx });
            }
        }, true);

        this._resultContainer.addEventListener('mouseleave', (e) => {
            const item = e.target.closest('[data-detection-item-index]');
            if (item) {
                eventBus.emit(Events.DETECTION_HIGHLIGHT, { regionIndex: null });
            }
        }, true);
```

Note: Use `true` (capture phase) for mouseenter/mouseleave event delegation.

**Step 3: Verify lint**

Run: `cd frontend && npx eslint src/components/DetectionPanel.js`
Expected: no errors

**Step 4: Commit**

```bash
git add frontend/src/components/DetectionPanel.js
git commit -m "feat(detection): add toast feedback and hover highlight for corrections

Fixes #163"
```

---

### Task 7: Extend backend cell counting with positions (#154 — backend)

**Files:**
- Modify: `backend/services/ml/counting.py:21-29,89-145`
- Modify: `backend/routes/ml.py` (count endpoint)

**Step 1: Extend CellCountResult dataclass**

In `backend/services/ml/counting.py`, update the `CellCountResult` dataclass (line 21-28):

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
    cells: Optional[list] = None  # [{x, y, positive}] in slide pixel coords
```

**Step 2: Compute cell positions in _count_real**

In `_count_real()` (line 89-145), after the contour loop (line 129-131), add position collection when requested. Modify the method signature to accept `include_positions: bool = False` and a `slide_dimensions` tuple:

```python
    def _count_real(
        self,
        slide_path: str,
        provider,
        stain: str,
        region=None,
        include_positions: bool = False,
        slide_dimensions: tuple[int, int] | None = None,
    ) -> CellCountResult:
```

Replace the contour loop (lines 129-133) with:

```python
        heatmap_h, heatmap_w = heatmap.shape[:2]
        cells_list = [] if include_positions else None

        for contour, confidence in contours:
            is_positive = confidence >= intensity_threshold
            if is_positive:
                positive += 1

            if include_positions and slide_dimensions:
                # Centroid of contour in heatmap space → slide pixel space
                cx = float(np.mean(contour[:, 0]))
                cy = float(np.mean(contour[:, 1]))
                scale_x = slide_dimensions[0] / heatmap_w
                scale_y = slide_dimensions[1] / heatmap_h
                cells_list.append({
                    "x": round(cx * scale_x),
                    "y": round(cy * scale_y),
                    "positive": is_positive,
                })
```

Add `cells=cells_list` to the returned `CellCountResult`.

Also update the mock `_count_mock` method to return `cells=None`.

**Step 3: Update route to pass include_positions**

In `backend/routes/ml.py`, find the `count_cells` endpoint. Add `include_positions: bool = False` query parameter. Pass it and slide dimensions through to the service:

```python
@router.post("/count/{slide_id}", response_model=CountingResponse)
async def count_cells(
    slide_id: str,
    request: CountRequest = CountRequest(),
    include_positions: bool = False,
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
) -> CountingResponse:
```

Before calling the service, get slide dimensions:

```python
    slide_dims = None
    if include_positions:
        try:
            import openslide
            with openslide.OpenSlide(str(slide_path)) as osr:
                slide_dims = osr.dimensions  # (width, height)
        except Exception:
            pass  # Fall back to no positions
```

Pass to service: `..., include_positions=include_positions, slide_dimensions=slide_dims`

Update `CountingResponse` model to include optional `cells` field:

```python
class CountingResponse(BaseModel):
    total_cells: int
    positive: int
    negative: int
    ratio: float
    percentage: str
    processing_time_ms: float
    cells: Optional[list] = None
```

**Step 4: Verify lint**

Run: `cd backend && ruff check services/ml/counting.py routes/ml.py`
Expected: no errors

**Step 5: Commit**

```bash
git add backend/services/ml/counting.py backend/routes/ml.py
git commit -m "feat(counting): expose cell positions in counting endpoint

Adds include_positions query param to return cell centroids
in slide pixel coordinates. Positions computed from existing
contour extraction pipeline.

Fixes #154"
```

---

### Task 8: Create CellMarkerOverlay + panel controls (#154 — frontend)

**Files:**
- Create: `frontend/src/components/CellMarkerOverlay.js`
- Create: `frontend/src/css/cell-markers.css`
- Modify: `frontend/src/style.css` (add CSS import)
- Modify: `frontend/src/components/CellCountingPanel.js`
- Modify: `frontend/src/services/ApiService.js`

**Step 1: Update ApiService**

In `frontend/src/services/ApiService.js`, find the `countCells` method. Add `includePositions` parameter:

```javascript
    async countCells(slideId, options = {}) {
        const params = new URLSearchParams();
        if (options.stain) params.set('stain', options.stain);
        if (options.includePositions) params.set('include_positions', 'true');
        const url = `${this.baseUrl}/api/v1/ml/count/${encodeURIComponent(slideId)}?${params}`;
        // ... existing fetch logic
    }
```

If the method currently doesn't accept options, wrap the existing stain parameter.

**Step 2: Create CellMarkerOverlay.js**

Create `frontend/src/components/CellMarkerOverlay.js` following the ClusteringOverlay pattern:

- Import `eventBus`, `Events`
- Class `CellMarkerOverlay` with constructor receiving `viewerInstance`
- Store `this.viewer = viewerInstance.viewer` (OSD viewer)
- `_build()`: Create a `div.cell-marker-overlay` with a `<canvas>` child. Position absolute, pointer-events none, z-index 260.
- `_setupEventListeners()`:
  - `Events.CELL_COUNTING_COMPLETE` → store cell data, render if visible
  - `Events.CELL_MARKERS_TOGGLE` → toggle visibility, render
  - `Events.CELL_MARKERS_OPACITY` → update opacity
  - OSD `'viewport-change'` and `'animation-finish'` → `_render()` with rAF dedup
- `setCells(cells)`: Store cell positions array `[{x, y, positive}, ...]`
- `_render()`:
  - Get canvas dimensions from container
  - Clear canvas
  - If not visible or no cells, return
  - For each cell, convert slide pixel coords to viewer element coords via:
    ```javascript
    const tiledImage = this.viewer.world.getItemAt(0);
    const viewportPoint = tiledImage.imageToViewportCoordinates(cell.x, cell.y);
    const webPoint = this.viewer.viewport.viewportToViewerElementCoordinates(viewportPoint);
    ```
  - Draw filled circle: green (`#22c55e`) for positive, blue (`#3b82f6`) for negative
  - Radius scales with zoom: `Math.max(2, Math.min(6, 3 * currentZoom / baseZoom))`
- `clear()`: Clear cells and canvas
- `destroy()`: Unsubscribe, remove DOM

**Step 3: Create cell-markers.css**

Create `frontend/src/css/cell-markers.css`:

- `.cell-marker-overlay` — position absolute, top 0, left 0, width 100%, height 100%, pointer-events none, z-index 260

**Step 4: Import CSS in style.css**

Add `@import './css/cell-markers.css';` in `frontend/src/style.css`.

**Step 5: Add toggle + opacity controls in CellCountingPanel**

In `frontend/src/components/CellCountingPanel.js`, in the results rendering method (after the ratio bar), add:

- A checkbox labeled "Afficher les marqueurs" that emits `Events.CELL_MARKERS_TOGGLE` with `{visible: checked}`
- An opacity slider (0-100) that emits `Events.CELL_MARKERS_OPACITY` with `{opacity: value/100}`

When calling `apiService.countCells()`, pass `{includePositions: true}`. After receiving results, emit `CELL_COUNTING_COMPLETE` with the cells data.

**Step 6: Verify lint and build**

Run: `cd frontend && npx eslint src/components/CellMarkerOverlay.js src/components/CellCountingPanel.js src/services/ApiService.js && npm run build`
Expected: no errors, build succeeds

**Step 7: Commit**

```bash
git add frontend/src/components/CellMarkerOverlay.js frontend/src/css/cell-markers.css frontend/src/style.css frontend/src/components/CellCountingPanel.js frontend/src/services/ApiService.js
git commit -m "feat(counting): add CellMarkerOverlay for spatial cell visualization

Canvas overlay renders colored dots for positive/negative cells.
Toggle and opacity controls in CellCountingPanel.

Fixes #154"
```

---

### Task 9: Mount all new components in Router.js

**Files:**
- Modify: `frontend/src/core/Router.js:46,258-300,989-1012,1240-1260`

**Step 1: Add imports**

In `frontend/src/core/Router.js`, add after existing component imports:

```javascript
import { MLProgressBar } from '../components/MLProgressBar.js';
import { HeatmapLegend } from '../components/HeatmapLegend.js';
import { CellMarkerOverlay } from '../components/CellMarkerOverlay.js';
```

**Step 2: Mount MLProgressBar and HeatmapLegend in showViewerPage**

After `viewerArea` is created (around line 280), mount the progress bar and legend:

```javascript
        // ML progress bar at top of viewer area
        this._state.mlProgressBar = new MLProgressBar(viewerArea);

        // Heatmap legend at bottom-left of viewer area
        this._state.heatmapLegend = new HeatmapLegend(viewerArea);
```

**Step 3: Mount CellMarkerOverlay in _initMLSubPanels**

After creating `viewerInstance`, mount the cell marker overlay:

```javascript
        // Cell marker overlay on viewer
        this._state.cellMarkerOverlay = new CellMarkerOverlay(viewerInstance);
```

This should go in `showViewerPage` after `viewerInstance` is created (similar to where `clusteringOverlay` is created).

**Step 4: Add to resetTargets**

Add `'cellMarkerOverlay'` to the resetTargets array (it should have a `clear()` method called on slide switch):

After the existing resetTargets loop, add:

```javascript
        if (this._state.cellMarkerOverlay && this._state.cellMarkerOverlay.clear) {
            this._state.cellMarkerOverlay.clear();
        }
```

**Step 5: Add to destroyKeys**

In `_cleanup()`, add `'mlProgressBar'`, `'heatmapLegend'`, `'cellMarkerOverlay'` to the `destroyKeys` array.

Also clean up event subscriptions:

```javascript
        this._state._focusNavUnsub?.();
        this._state._slideNavPrevUnsub?.();
        this._state._slideNavNextUnsub?.();
        if (this._state._keyNavHandler) {
            document.removeEventListener('keydown', this._state._keyNavHandler);
        }
```

**Step 6: Verify lint and build**

Run: `cd frontend && npx eslint src/core/Router.js && npm run build`
Expected: no errors, build succeeds

**Step 7: Commit**

```bash
git add frontend/src/core/Router.js
git commit -m "feat(router): mount MLProgressBar, HeatmapLegend, CellMarkerOverlay

Integrates Wave B components into viewer lifecycle."
```

---

### Task 10: Final verification

**Step 1: Run full lint**

```bash
cd frontend && npx eslint src/core/Constants.js src/core/Router.js src/components/MLProgressBar.js src/components/HeatmapLegend.js src/components/CellMarkerOverlay.js src/components/FocusAssistPanel.js src/components/DetectionPanel.js src/components/CellCountingPanel.js src/services/ApiService.js
```
Expected: no errors

**Step 2: Run backend lint**

```bash
cd backend && ruff check services/ml/counting.py routes/ml.py
```
Expected: no errors

**Step 3: Run full frontend build**

```bash
cd frontend && npm run build
```
Expected: build succeeds

**Step 4: Push and create PR**

```bash
git push -u origin feat/ux-wave-b
```

Create PR with title: `feat(ux): Wave B — ML progress, heatmap legend, zone nav, cell markers, corrections`

Body should reference: Closes #152, #153, #154, #157, #163, #166
