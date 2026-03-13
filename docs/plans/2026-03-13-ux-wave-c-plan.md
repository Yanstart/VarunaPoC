# UX Wave C: Heavy Features + Backend — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add ML retry logic, quality-ML cross-validation, viewport detection, metadata panel, case summary, multi-stain comparison, ML overlay toggle, and CSV export.

**Architecture:** Event-driven pub-sub via EventBus. Backend extended for viewport region filtering. Frontend ApiService gets retry wrapper. New components follow existing patterns (collapsible accordion, DOM API, i18n).

**Tech Stack:** FastAPI + OpenSlide (backend), Vanilla JS + Vite + OpenSeadragon (frontend)

**Design:** `docs/plans/2026-03-13-ux-wave-c-design.md`

---

## Task 1: Add Constants + Event Foundations

**Files:**
- Modify: `frontend/src/core/Constants.js` (Events object, line ~243 before closing `});`)

**Step 1: Add new event constants**

Add after `CELL_MARKERS_OPACITY` (line 187) and before the Clustering section (line 189):

```javascript
    // -- ML overlays global toggle (Wave C) --
    /** @payload {{ visible: boolean }} */
    ML_OVERLAYS_TOGGLE: 'ml:overlaysToggle',
```

**Step 2: Commit**

```bash
git add frontend/src/core/Constants.js
git commit -m "feat(constants): add ML_OVERLAYS_TOGGLE event

Fixes #158"
```

---

## Task 2: Retry with Backoff (#159)

**Files:**
- Modify: `frontend/src/services/ApiService.js`

**Step 1: Add `_retryableFetch` wrapper**

Add a new private method after `_fetchWithBody()` (around line 240). This method wraps a fetch call with exponential backoff for ML endpoints only:

```javascript
    /**
     * Retry wrapper for ML endpoints (429/503/504).
     * Max 3 retries with 1s/2s/4s exponential backoff.
     * @param {Function} fetchFn - () => Promise<Response>
     * @param {string} url - Request URL (used to check if ML path)
     * @returns {Promise<Response>}
     * @private
     */
    async _retryableFetch(fetchFn, url) {
        const isML = url.includes('/ml/');
        const retryStatuses = [429, 503, 504];
        const maxRetries = 3;
        const baseDelay = 1000;

        let lastResponse = await fetchFn();

        if (!isML || !retryStatuses.includes(lastResponse.status)) {
            return lastResponse;
        }

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            const delay = baseDelay * Math.pow(2, attempt - 1);
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'warning',
                message: i18nService.t('api.retryIn', { seconds: delay / 1000 }),
                duration: delay,
            });
            await new Promise(resolve => setTimeout(resolve, delay));
            lastResponse = await fetchFn();
            if (!retryStatuses.includes(lastResponse.status)) {
                return lastResponse;
            }
        }

        return lastResponse;
    }
```

**Step 2: Wire into `_fetch()` and `_fetchWithBody()`**

In `_fetch()` (line 153), replace:
```javascript
const response = await fetch(url, { method: 'GET', headers });
```
with:
```javascript
const response = await this._retryableFetch(
    () => fetch(url, { method: 'GET', headers }), url,
);
```

In `_fetchWithBody()` (line 208), replace:
```javascript
const response = await fetch(url, {
    method,
    headers,
    body: JSON.stringify(body),
});
```
with:
```javascript
const response = await this._retryableFetch(
    () => fetch(url, { method, headers, body: JSON.stringify(body) }), url,
);
```

**Step 3: Add i18n keys to all 5 locales**

Add to each locale file:

- `fr.json`: `"api.retryIn": "Worker ML occupe, nouvel essai dans {seconds}s..."`
- `en.json`: `"api.retryIn": "ML worker busy, retrying in {seconds}s..."`
- `ja.json`: `"api.retryIn": "MLワーカービジー、{seconds}秒後にリトライ..."`
- `zh.json`: `"api.retryIn": "ML工作器忙碌，{seconds}秒后重试..."`
- `hi.json`: `"api.retryIn": "ML वर्कर व्यस्त, {seconds}s में पुनः प्रयास..."`

**Step 4: Add imports if needed**

`ApiService.js` already imports `eventBus` and `Events` and `i18nService` — verify, add if missing.

**Step 5: Commit**

```bash
git add frontend/src/services/ApiService.js frontend/src/locales/*.json
git commit -m "feat(api): add exponential backoff retry for ML endpoints

429/503/504 responses on /ml/ paths trigger up to 3 retries with
1s/2s/4s delays. Toast warning shown during retry.

Fixes #159"
```

---

## Task 3: Quality-ML Cross-Validation (#160)

**Files:**
- Modify: `frontend/src/components/MLPanel.js`

**Step 1: Add quality cache and listener**

In constructor (after line 43 `this.isCollapsed = ...`), add:
```javascript
        this._qualityScore = null;
```

In `_setupEventListeners()` (around line 223), add:
```javascript
        this._unsubscribers.push(
            eventBus.on(Events.QUALITY_READY, ({ slideId, metrics }) => {
                if (slideId === this.slideId) {
                    this._qualityScore = metrics.overall_score ?? metrics.score ?? null;
                    this._updateQualityWarning();
                }
            }),
        );
```

**Step 2: Add warning banner method**

Add new method:
```javascript
    _updateQualityWarning() {
        const existing = this.element.querySelector('.ml-panel__quality-warning');
        if (existing) existing.remove();

        if (this._qualityScore !== null && this._qualityScore < 0.6) {
            const warning = document.createElement('div');
            warning.className = 'ml-panel__quality-warning';
            warning.textContent = i18nService.t('ml.qualityWarning', {
                score: (this._qualityScore * 100).toFixed(0),
            });
            const content = this.element.querySelector('.ml-panel__content');
            if (content) content.prepend(warning);
        }
    }
```

**Step 3: Reset quality on `setSlide()`**

In `setSlide()` method (around line 300), add:
```javascript
        this._qualityScore = null;
        const existing = this.element.querySelector('.ml-panel__quality-warning');
        if (existing) existing.remove();
```

**Step 4: Add i18n keys**

- `fr.json`: `"ml.qualityWarning": "Qualite faible ({score}%) — resultats potentiellement peu fiables"`
- `en.json`: `"ml.qualityWarning": "Low quality ({score}%) — results may be unreliable"`
- `ja.json`: `"ml.qualityWarning": "品質低下 ({score}%) — 結果が信頼できない可能性があります"`
- `zh.json`: `"ml.qualityWarning": "质量低 ({score}%) — 结果可能不可靠"`
- `hi.json`: `"ml.qualityWarning": "कम गुणवत्ता ({score}%) — परिणाम अविश्वसनीय हो सकते हैं"`

**Step 5: Commit**

```bash
git add frontend/src/components/MLPanel.js frontend/src/locales/*.json
git commit -m "feat(ml): show quality warning when score below 60%

MLPanel listens to QUALITY_READY and shows inline warning banner
when quality score < 0.6. Non-blocking — user can proceed.

Fixes #160"
```

---

## Task 4: Detection Viewport Region (#156) — Backend

**Files:**
- Modify: `backend/routes/ml.py` (detect endpoint, line 690)
- Modify: `backend/services/detection/pipeline.py`

**Step 1: Add `region` parameter to detect endpoint**

In `detect_regions_endpoint()` (line 692), add parameter:
```python
    region: Optional[str] = Query(None, description="Viewport region x,y,w,h in slide pixels"),
```

Add import at top if needed:
```python
from typing import Optional
```

**Step 2: Parse region and pass to pipeline**

After `geojson = run_pipeline(...)` (line 733-739), add region filtering:

```python
        geojson = run_pipeline(
            heatmap=heatmap_result.heatmap,
            slide_dimensions=heatmap_result.slide_dimensions,
            threshold=threshold,
            min_area=min_area,
            simplify_tolerance=simplify_tolerance,
        )

        # Filter by viewport region if specified
        if region:
            try:
                rx, ry, rw, rh = [float(v) for v in region.split(",")]
                filtered = [
                    f for f in geojson.features
                    if _centroid_in_region(f.properties.get("centroid", [0, 0]), rx, ry, rw, rh)
                ]
                geojson = GeoJSONFeatureCollection(
                    features=filtered,
                    metadata={"num_regions": len(filtered)},
                )
            except (ValueError, TypeError):
                pass  # Invalid region format — return unfiltered
```

**Step 3: Add helper function**

Add at module level in `ml.py`:
```python
def _centroid_in_region(centroid: list, rx: float, ry: float, rw: float, rh: float) -> bool:
    """Check if centroid [x, y] falls within region bbox."""
    if len(centroid) < 2:
        return False
    cx, cy = centroid
    return rx <= cx <= rx + rw and ry <= cy <= ry + rh
```

**Step 4: Commit**

```bash
git add backend/routes/ml.py
git commit -m "feat(detection): add viewport region filtering to detect endpoint

Optional region=x,y,w,h query param filters detected contours by
centroid within viewport bounds. Keeps full-slide detection when
region is not specified.

Fixes #156"
```

---

## Task 5: Detection Viewport Region (#156) — Frontend

**Files:**
- Modify: `frontend/src/components/DetectionPanel.js` (`_runDetection()`, line 503)
- Modify: `frontend/src/services/ApiService.js` (`detect()`, line 669)

**Step 1: Update ApiService.detect() to pass region**

In `detect()` method (line 669), add after the existing queryParams:
```javascript
        if (params.region) queryParams.set('region', params.region);
```

**Step 2: Send viewport bounds in DetectionPanel._runDetection()**

In `_runDetection()` (line 515), modify the `apiService.detect()` call:

Replace:
```javascript
            this.detectionResult = await apiService.detect(this.slideId, {
                threshold: this.threshold,
                min_area: this.minArea,
                prediction_class: this.predictionClass,
            });
```

With:
```javascript
            const detectParams = {
                threshold: this.threshold,
                min_area: this.minArea,
                prediction_class: this.predictionClass,
            };

            if (this.analysisScope === 'viewport' && this._viewerInstance) {
                const bounds = this._viewerInstance.getViewportPixelBounds();
                if (bounds) {
                    detectParams.region = `${bounds.x},${bounds.y},${bounds.width},${bounds.height}`;
                }
            }

            this.detectionResult = await apiService.detect(this.slideId, detectParams);
```

**Step 3: Commit**

```bash
git add frontend/src/components/DetectionPanel.js frontend/src/services/ApiService.js
git commit -m "feat(detection): send viewport bounds for scoped detection

When analysisScope is 'viewport', extract pixel bounds from
ViewerInstance and pass as region query param to detect endpoint.

Fixes #156"
```

---

## Task 6: MetadataPanel (#167)

**Files:**
- Create: `frontend/src/components/MetadataPanel.js`
- Create: `frontend/src/css/metadata-panel.css`
- Modify: `frontend/src/core/Router.js` (mount in #info panel)
- Modify: `frontend/src/locales/*.json`

**Step 1: Create MetadataPanel component**

```javascript
/**
 * MetadataPanel - Detailed slide metadata display
 *
 * Fetches from /slides/{id}/info + /slides/{id}/tags.
 * Displays in collapsible accordion with copy button.
 *
 * @module components/MetadataPanel
 */

import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

export class MetadataPanel {
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = null;
        this._metadata = null;
        this._tags = null;

        this._unsubscribers = [];

        this.element = document.createElement('div');
        this.element.className = 'metadata-panel';
        this.container.appendChild(this.element);

        this._unsubscribers.push(
            eventBus.on(Events.LOCALE_CHANGED, () => this._render()),
        );
    }

    async setSlide(slideId) {
        this.slideId = slideId;
        this._metadata = null;
        this._tags = null;
        this._render();

        if (!slideId) return;

        try {
            const [info, tags] = await Promise.all([
                apiService.getSlideInfo(slideId),
                apiService.getSlideTags(slideId).catch(() => []),
            ]);
            this._metadata = info;
            this._tags = tags;
            this._render();
        } catch {
            // Info panel already shows basic data
        }
    }

    _render() {
        this.element.textContent = '';
        const _t = (k, p) => i18nService.t(k, p);

        // Header
        const header = document.createElement('div');
        header.className = 'metadata-panel__header';
        header.textContent = _t('metadata.title');
        this.element.appendChild(header);

        if (!this._metadata) return;

        const body = document.createElement('dl');
        body.className = 'metadata-panel__body';

        const m = this._metadata;
        const [w, h] = m.dimensions || [0, 0];
        const mpp = m.mpp_x || m.properties?.['openslide.mpp-x'];
        const scanner = m.properties?.['openslide.vendor'] || null;
        const objective = m.properties?.['openslide.objective-power'] || null;

        this._addRow(body, _t('metadata.format'), m.format || '—');
        this._addRow(body, _t('metadata.dimensions'),
            `${w.toLocaleString()} x ${h.toLocaleString()} px`);

        if (mpp) {
            const mmW = ((w * parseFloat(mpp)) / 1000).toFixed(1);
            const mmH = ((h * parseFloat(mpp)) / 1000).toFixed(1);
            this._addRow(body, '', `${mmW} x ${mmH} mm`);
            this._addRow(body, _t('metadata.mpp'), `${parseFloat(mpp).toFixed(3)} um/px`);
        }

        if (scanner) this._addRow(body, _t('metadata.scanner'), scanner);

        // Stain from tags
        const stainTag = Array.isArray(this._tags)
            ? this._tags.find(t => t.key === 'stain')
            : null;
        if (stainTag) this._addRow(body, _t('metadata.stain'), stainTag.value);

        if (objective) this._addRow(body, _t('metadata.objective'), `${objective}x`);

        this.element.appendChild(body);

        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'metadata-panel__copy';
        copyBtn.textContent = _t('metadata.copy');
        copyBtn.addEventListener('click', () => this._copyToClipboard());
        this.element.appendChild(copyBtn);
    }

    _addRow(dl, label, value) {
        if (label) {
            const dt = document.createElement('dt');
            dt.textContent = label;
            dl.appendChild(dt);
        }
        const dd = document.createElement('dd');
        dd.textContent = value;
        dl.appendChild(dd);
    }

    _copyToClipboard() {
        const rows = this.element.querySelectorAll('dt, dd');
        const text = Array.from(rows).map(el => el.textContent).join('\n');
        navigator.clipboard.writeText(text).then(() => {
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: i18nService.t('metadata.copied'),
                duration: 2000,
            });
        });
    }

    destroy() {
        this._unsubscribers.forEach(fn => fn());
        this._unsubscribers = [];
        if (this.element.parentNode) this.element.parentNode.removeChild(this.element);
    }
}
```

**Step 2: Create CSS**

```css
/* metadata-panel.css */
.metadata-panel {
    margin-top: 1rem;
    border-top: 1px solid var(--border-color, #e0e0e0);
    padding-top: 0.5rem;
}
.metadata-panel__header {
    font-weight: 600;
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
    color: var(--text-secondary, #666);
}
.metadata-panel__body {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.25rem 0.75rem;
    font-size: 0.8rem;
    margin: 0;
}
.metadata-panel__body dt {
    color: var(--text-secondary, #888);
    margin: 0;
}
.metadata-panel__body dd {
    margin: 0;
    font-weight: 500;
}
.metadata-panel__copy {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    cursor: pointer;
    border: 1px solid var(--border-color, #ccc);
    border-radius: 4px;
    background: var(--bg-secondary, #f5f5f5);
}
.metadata-panel__copy:hover {
    background: var(--bg-hover, #eee);
}
```

**Step 3: Mount in Router**

In `Router.js`, add import:
```javascript
import { MetadataPanel } from '../components/MetadataPanel.js';
```

In `_loadSlide()` (after the existing info panel content, around line 774), mount:
```javascript
        this._state.metadataPanel = new MetadataPanel(infoPanel);
        this._state.metadataPanel.setSlide(slide.id);
```

Add to `resetTargets` array (line 695):
```javascript
'metadataPanel',
```

Add to `destroyKeys` array (line 1369).

**Step 4: Add i18n keys**

- `fr.json`: `"metadata.title": "Metadonnees"`, `"metadata.format": "Format"`, `"metadata.dimensions": "Dimensions"`, `"metadata.mpp": "Resolution (MPP)"`, `"metadata.scanner": "Scanner"`, `"metadata.stain": "Coloration"`, `"metadata.objective": "Objectif"`, `"metadata.copy": "Copier"`, `"metadata.copied": "Metadonnees copiees"`
- `en.json`: `"metadata.title": "Metadata"`, `"metadata.format": "Format"`, `"metadata.dimensions": "Dimensions"`, `"metadata.mpp": "Resolution (MPP)"`, `"metadata.scanner": "Scanner"`, `"metadata.stain": "Stain"`, `"metadata.objective": "Objective"`, `"metadata.copy": "Copy"`, `"metadata.copied": "Metadata copied"`
- `ja.json`: `"metadata.title": "メタデータ"`, `"metadata.format": "フォーマット"`, `"metadata.dimensions": "寸法"`, `"metadata.mpp": "解像度 (MPP)"`, `"metadata.scanner": "スキャナー"`, `"metadata.stain": "染色"`, `"metadata.objective": "対物レンズ"`, `"metadata.copy": "コピー"`, `"metadata.copied": "メタデータをコピーしました"`
- `zh.json`: `"metadata.title": "元数据"`, `"metadata.format": "格式"`, `"metadata.dimensions": "尺寸"`, `"metadata.mpp": "分辨率 (MPP)"`, `"metadata.scanner": "扫描仪"`, `"metadata.stain": "染色"`, `"metadata.objective": "物镜"`, `"metadata.copy": "复制"`, `"metadata.copied": "元数据已复制"`
- `hi.json`: `"metadata.title": "मेटाडेटा"`, `"metadata.format": "प्रारूप"`, `"metadata.dimensions": "आयाम"`, `"metadata.mpp": "रिज़ॉल्यूशन (MPP)"`, `"metadata.scanner": "स्कैनर"`, `"metadata.stain": "रंगाई"`, `"metadata.objective": "ऑब्जेक्टिव"`, `"metadata.copy": "कॉपी करें"`, `"metadata.copied": "मेटाडेटा कॉपी किया गया"`

**Step 5: Import CSS**

In `frontend/index.html` or wherever CSS is loaded, add `metadata-panel.css`. Or in `MetadataPanel.js` if using Vite's CSS import:
```javascript
import '../css/metadata-panel.css';
```

**Step 6: Commit**

```bash
git add frontend/src/components/MetadataPanel.js frontend/src/css/metadata-panel.css frontend/src/core/Router.js frontend/src/locales/*.json
git commit -m "feat(metadata): add MetadataPanel showing detailed slide properties

Displays format, dimensions, MPP, scanner, stain, and objective
in the #info sidebar. Copy button for clipboard export.

Fixes #167"
```

---

## Task 7: Case Summary in Sidebar (#169)

**Files:**
- Modify: `frontend/src/components/CaseSidebar.js`
- Modify: `frontend/src/locales/*.json`

**Step 1: Fetch annotation stats on setCase()**

In `setCase()` (line 78), after `this._render()`, add stats fetching:

```javascript
        this._fetchStats();
```

Add new method:
```javascript
    async _fetchStats() {
        if (!this.slides || this.slides.length === 0) return;

        try {
            const statsPromises = this.slides.map(slide =>
                apiService.getAnnotationStats(slide.id).catch(() => ({ count: 0 })),
            );
            const allStats = await Promise.all(statsPromises);

            this.slides.forEach((slide, i) => {
                slide._annotationCount = allStats[i]?.count ?? 0;
            });

            this._updateBadges();
        } catch {
            // Non-critical — badges just won't show
        }
    }
```

**Step 2: Update badges after fetch**

```javascript
    _updateBadges() {
        const items = this.element.querySelectorAll('.case-sidebar__item');
        items.forEach(item => {
            const slideId = item.dataset.slideId;
            const slide = this.slides.find(s => s.id === slideId);
            if (!slide) return;

            // Remove old badge if exists
            const oldBadge = item.querySelector('.case-sidebar__badge');
            if (oldBadge) oldBadge.remove();

            const badge = document.createElement('span');
            badge.className = 'case-sidebar__badge';
            badge.textContent = String(slide._annotationCount || 0);
            if (slide._annotationCount > 0) badge.classList.add('case-sidebar__badge--active');
            item.appendChild(badge);
        });

        // Progress header
        const annotated = this.slides.filter(s => (s._annotationCount || 0) > 0).length;
        const header = this.element.querySelector('.case-sidebar__count');
        if (header) {
            header.textContent = i18nService.t('case.progress', {
                annotated,
                total: this.slides.length,
            });
        }
    }
```

**Step 3: Add import**

Add at top of `CaseSidebar.js`:
```javascript
import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';
```

**Step 4: Check ApiService has getAnnotationStats**

Verify `apiService.getAnnotationStats(slideId)` exists. If not, add:
```javascript
    async getAnnotationStats(slideId) {
        return this._fetch(`${this.baseUrl}/api/v1/slides/${encodeURIComponent(slideId)}/annotations/stats`);
    }
```

**Step 5: Add i18n keys**

- `fr.json`: `"case.progress": "{annotated}/{total} lames annotees"`
- `en.json`: `"case.progress": "{annotated}/{total} slides annotated"`
- `ja.json`: `"case.progress": "{annotated}/{total}枚注釈済み"`
- `zh.json`: `"case.progress": "{annotated}/{total}张已标注"`
- `hi.json`: `"case.progress": "{annotated}/{total} स्लाइड एनोटेट"`

**Step 6: Commit**

```bash
git add frontend/src/components/CaseSidebar.js frontend/src/services/ApiService.js frontend/src/locales/*.json
git commit -m "feat(case): add annotation count badges and progress to CaseSidebar

Fetches annotation stats per slide in parallel. Shows count badge
per slide item and N/M progress in case header.

Fixes #169"
```

---

## Task 8: Multi-Stain Comparison (#168)

**Files:**
- Modify: `frontend/src/components/CaseSidebar.js` (add compare button)
- Modify: `frontend/src/components/SimilarityPanel.js` (replace window.open)
- Modify: `frontend/src/core/Router.js` (handle compare event)

**Step 1: Add compare button to CaseSidebar**

In `_render()`, inside `this.slides.forEach(slide => { ... })` (after the info block, before the click handler, around line 172), add a compare button for non-active slides:

```javascript
            if (slide.id !== this.activeSlideId) {
                const compareBtn = document.createElement('button');
                compareBtn.className = 'case-sidebar__compare-btn';
                compareBtn.title = i18nService.t('case.compare');
                compareBtn.textContent = '\u2194';  // ↔ arrows
                compareBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    eventBus.emit(Events.CASE_SLIDE_SWITCH, {
                        slideId: slide.id,
                        compare: true,
                    });
                });
                item.appendChild(compareBtn);
            }
```

Add import for `eventBus` and `Events` at top:
```javascript
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
```

**Step 2: Fix SimilarityPanel.js — replace window.open**

In `SimilarityPanel.js` (line 259), replace:
```javascript
            window.open('/slide/' + result.slide_id, '_blank');
```
with:
```javascript
            eventBus.emit(Events.CASE_SLIDE_SWITCH, { slideId: result.slide_id });
```

Add import at top:
```javascript
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
```

**Step 3: Handle compare event in Router**

In `showViewerPage()`, add listener after the existing nav listeners:
```javascript
        this._state._compareSwitchUnsub = eventBus.on(Events.CASE_SLIDE_SWITCH, ({ slideId, compare }) => {
            if (compare) {
                this.showComparePage(this._state.selectedSlide);
            }
        });
```

In `_cleanup()`, add:
```javascript
        if (this._state._compareSwitchUnsub) { this._state._compareSwitchUnsub(); this._state._compareSwitchUnsub = null; }
```

**Step 4: Add i18n key**

- `fr.json`: `"case.compare": "Comparer avec cette lame"`
- `en.json`: `"case.compare": "Compare with this slide"`
- `ja.json`: `"case.compare": "このスライドと比較"`
- `zh.json`: `"case.compare": "与此切片比较"`
- `hi.json`: `"case.compare": "इस स्लाइड से तुलना करें"`

**Step 5: Commit**

```bash
git add frontend/src/components/CaseSidebar.js frontend/src/components/SimilarityPanel.js frontend/src/core/Router.js frontend/src/locales/*.json
git commit -m "feat(case): add multi-stain compare button and fix SimilarityPanel

Compare button on non-active slides in CaseSidebar opens compare mode.
SimilarityPanel now uses EventBus instead of window.open.

Fixes #168"
```

---

## Task 9: ML Overlay Toggle (#158)

**Files:**
- Modify: `frontend/src/core/Router.js` (keyboard listener)
- Modify: `frontend/src/components/HeatmapOverlay.js`
- Modify: `frontend/src/components/ClusteringOverlay.js`
- Modify: `frontend/src/components/CellMarkerOverlay.js`
- Modify: `frontend/src/components/AnnotationLayer.js`

**Step 1: Add keyboard listener in Router**

In `showViewerPage()`, inside the existing `_keyNavHandler` or after it, extend the keyboard handling to include `M` key:

Add a new handler or extend existing:
```javascript
        this._state._mlToggleHandler = (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
            if (e.key === 'm' || e.key === 'M') {
                this._state._mlOverlaysHidden = !this._state._mlOverlaysHidden;
                eventBus.emit(Events.ML_OVERLAYS_TOGGLE, { visible: !this._state._mlOverlaysHidden });
            }
        };
        document.addEventListener('keydown', this._state._mlToggleHandler);
```

In `_cleanup()`, add:
```javascript
        if (this._state._mlToggleHandler) { document.removeEventListener('keydown', this._state._mlToggleHandler); this._state._mlToggleHandler = null; }
        this._state._mlOverlaysHidden = false;
```

**Step 2: HeatmapOverlay listens to toggle**

In `HeatmapOverlay._setupEventListeners()` (or constructor), add:
```javascript
        this._unsubscribers.push(
            eventBus.on(Events.ML_OVERLAYS_TOGGLE, ({ visible }) => {
                if (this.overlayElement) {
                    this.overlayElement.style.display = visible ? '' : 'none';
                }
            }),
        );
```

**Step 3: ClusteringOverlay listens to toggle**

Same pattern:
```javascript
        this._unsubscribers.push(
            eventBus.on(Events.ML_OVERLAYS_TOGGLE, ({ visible }) => {
                if (this.overlayElement) {
                    this.overlayElement.style.display = visible ? '' : 'none';
                }
            }),
        );
```

**Step 4: CellMarkerOverlay listens to toggle**

Same pattern — already has `_unsubscribers`:
```javascript
        this._unsubscribers.push(
            eventBus.on(Events.ML_OVERLAYS_TOGGLE, ({ visible }) => {
                if (this.canvas) {
                    this.canvas.style.display = visible ? '' : 'none';
                }
            }),
        );
```

**Step 5: AnnotationLayer — hide detection previews on toggle**

In `AnnotationLayer._setupEventListeners()`, add:
```javascript
        this._unsubscribers.push(
            eventBus.on(Events.ML_OVERLAYS_TOGGLE, ({ visible }) => {
                const previews = this.svg?.querySelectorAll('.detection-preview');
                if (previews) {
                    previews.forEach(el => { el.style.display = visible ? '' : 'none'; });
                }
            }),
        );
```

**Step 6: Visual badge when hidden**

In Router, after the toggle emit, show/hide a badge:
```javascript
                // Show/hide ML hidden badge
                let badge = document.querySelector('.ml-hidden-badge');
                if (this._state._mlOverlaysHidden) {
                    if (!badge) {
                        badge = document.createElement('div');
                        badge.className = 'ml-hidden-badge';
                        badge.textContent = i18nService.t('ml.overlaysHidden');
                        document.querySelector('.viewer-area')?.appendChild(badge);
                    }
                } else if (badge) {
                    badge.remove();
                }
```

**Step 7: Add i18n key**

- `fr.json`: `"ml.overlaysHidden": "ML masque (M)"`
- `en.json`: `"ml.overlaysHidden": "ML hidden (M)"`
- `ja.json`: `"ml.overlaysHidden": "ML非表示 (M)"`
- `zh.json`: `"ml.overlaysHidden": "ML已隐藏 (M)"`
- `hi.json`: `"ml.overlaysHidden": "ML छिपा (M)"`

**Step 8: Commit**

```bash
git add frontend/src/core/Router.js frontend/src/core/Constants.js \
  frontend/src/components/HeatmapOverlay.js frontend/src/components/ClusteringOverlay.js \
  frontend/src/components/CellMarkerOverlay.js frontend/src/components/AnnotationLayer.js \
  frontend/src/locales/*.json
git commit -m "feat(ml): add M key toggle for all ML overlays

Pressing M toggles heatmap, clustering, cell markers, and detection
previews simultaneously. Shows 'ML masque' badge when hidden.

Fixes #158"
```

---

## Task 10: CSV Export (#161)

**Files:**
- Create: `frontend/src/services/ExportService.js`
- Modify: `frontend/src/components/DetectionPanel.js`
- Modify: `frontend/src/components/CellCountingPanel.js`

**Step 1: Create ExportService**

```javascript
/**
 * ExportService - Pure JS CSV export utility
 * @module services/ExportService
 */

export class ExportService {
    /**
     * Generate CSV string from rows.
     * @param {string[]} headers - Column headers
     * @param {Array<Array<string|number>>} rows - Data rows
     * @returns {string} CSV content
     */
    static toCSV(headers, rows) {
        const escape = (val) => {
            const str = String(val ?? '');
            return str.includes(',') || str.includes('"') || str.includes('\n')
                ? `"${str.replace(/"/g, '""')}"` : str;
        };
        const lines = [headers.map(escape).join(',')];
        for (const row of rows) {
            lines.push(row.map(escape).join(','));
        }
        return lines.join('\n');
    }

    /**
     * Trigger browser download of CSV.
     * @param {string} csv - CSV string
     * @param {string} filename - Download filename
     */
    static download(csv, filename) {
        const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Build date string for filenames.
     * @returns {string} YYYY-MM-DD
     */
    static dateStamp() {
        return new Date().toISOString().slice(0, 10);
    }
}
```

**Step 2: Add export button to DetectionPanel**

In `_renderResults()` (where results are shown, after the results list), add an export button:

```javascript
        const exportBtn = document.createElement('button');
        exportBtn.className = 'detection-panel__btn detection-panel__btn--export';
        exportBtn.textContent = i18nService.t('export.csv');
        exportBtn.addEventListener('click', () => this._exportCSV());
        // Append after results section
```

Add export method:
```javascript
    _exportCSV() {
        if (!this.detectionResult?.geojson?.features) return;

        const headers = ['region', 'confidence', 'area_px', 'centroid_x', 'centroid_y', 'label'];
        const rows = this.detectionResult.geojson.features.map((f, i) => [
            `detection_${i}`,
            f.properties.confidence,
            f.properties.area_px,
            f.properties.centroid?.[0] ?? '',
            f.properties.centroid?.[1] ?? '',
            this.selectedLabelId || '',
        ]);

        const csv = ExportService.toCSV(headers, rows);
        const slideName = this.slideId || 'slide';
        ExportService.download(csv, `${slideName}_detection_${ExportService.dateStamp()}.csv`);
    }
```

Add import:
```javascript
import { ExportService } from '../services/ExportService.js';
```

**Step 3: Add export button to CellCountingPanel**

Similar pattern — add button in `_renderResults()`:

```javascript
        const exportBtn = document.createElement('button');
        exportBtn.className = 'cell-counting-panel__btn cell-counting-panel__btn--export';
        exportBtn.textContent = i18nService.t('export.csv');
        exportBtn.addEventListener('click', () => this._exportCSV());
```

Add export method:
```javascript
    _exportCSV() {
        if (!this._lastResult) return;
        const r = this._lastResult;

        const headers = ['metric', 'value'];
        const rows = [
            ['total_cells', r.total_cells],
            ['positive', r.positive],
            ['negative', r.negative],
            ['ratio', r.ratio],
            ['percentage', r.percentage],
        ];

        // Add cell positions if available
        if (r.cells && r.cells.length > 0) {
            rows.push([]);  // Empty separator
            rows.push(['cell_x', 'cell_y', 'positive']);
            for (const cell of r.cells) {
                rows.push([cell.x, cell.y, cell.positive]);
            }
        }

        const csv = ExportService.toCSV(headers, rows);
        const slideName = this.slideId || 'slide';
        ExportService.download(csv, `${slideName}_counting_${ExportService.dateStamp()}.csv`);
    }
```

Add import:
```javascript
import { ExportService } from '../services/ExportService.js';
```

**Step 4: Store last result in CellCountingPanel**

In the counting result handler, cache: `this._lastResult = result;`

**Step 5: Add i18n key**

- `fr.json`: `"export.csv": "Exporter CSV"`
- `en.json`: `"export.csv": "Export CSV"`
- `ja.json`: `"export.csv": "CSVエクスポート"`
- `zh.json`: `"export.csv": "导出CSV"`
- `hi.json`: `"export.csv": "CSV निर्यात"`

**Step 6: Commit**

```bash
git add frontend/src/services/ExportService.js \
  frontend/src/components/DetectionPanel.js \
  frontend/src/components/CellCountingPanel.js \
  frontend/src/locales/*.json
git commit -m "feat(export): add CSV export for detection and cell counting results

Pure JS CSV generation with BOM for Excel compatibility. Export
buttons in DetectionPanel (regions) and CellCountingPanel (counts +
cell positions).

Fixes #161"
```

---

## Dependency Order

```
Task 1: Constants (foundation)
  ├── Task 2: Retry backoff (#159) — independent
  ├── Task 3: Quality-ML warning (#160) — independent
  ├── Task 4: Detection region backend (#156) — independent
  ├── Task 5: Detection region frontend (#156) — depends on Task 4
  ├── Task 6: MetadataPanel (#167) — independent
  ├── Task 7: Case summary (#169) — independent
  ├── Task 8: Multi-stain compare (#168) — independent
  ├── Task 9: ML overlay toggle (#158) — depends on Task 1
  └── Task 10: CSV export (#161) — independent
```

Tasks 2, 3, 4, 6, 7, 8, 10 are independent after Task 1. Task 5 depends on Task 4. Task 9 depends on Task 1 (for the event constant).

Implementation order: 1 → (2, 3, 4, 6, 7, 8, 10 in sequence) → 5 → 9
