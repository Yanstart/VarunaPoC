# UX Wave C: Heavy Features + Backend — Design

**Goal:** Add ML retry logic, quality-ML cross-validation, viewport detection, metadata panel, case summary, multi-stain comparison, ML overlay toggle, and CSV export.

**Issues:** #156, #158, #159, #160, #161, #167, #168, #169

**Architecture:** Event-driven. Backend extended for viewport detection. Frontend ApiService gets retry logic. New MetadataPanel component. CaseSidebar enriched with badges. CSV export via pure JS (no dependencies).

---

## 1. Retry with Backoff (#159)

### Problem

429/503/504 errors shown as permanent failures. User must retry manually.

### Solution

Add exponential backoff retry in `ApiService._fetchWithBody()` for ML endpoints. Max 3 retries with 1s/2s/4s delays. Show warning toast during retry. Non-ML endpoints (auth, slides) are not retried.

### Retry logic

```
Request → 429/503/504 → toast "Worker busy, retry in 1s" → wait 1s → retry
  → 429/503/504 → toast "Retry in 2s" → wait 2s → retry
  → 429/503/504 → toast "Retry in 4s" → wait 4s → retry
  → fail → throw original error
```

Only retry paths containing `/ml/`.

### Files

- MODIFY: `frontend/src/services/ApiService.js` — add `_retryableFetch()` wrapper (~60 lines)

---

## 2. Quality-ML Cross-Validation (#160)

### Problem

MLPanel runs analysis without checking quality. Low-quality slides produce unreliable results.

### Solution

MLPanel listens to `QUALITY_READY` event and caches quality score. Before analysis, if score < 0.6, show inline warning banner. Non-blocking — user can proceed.

### Files

- MODIFY: `frontend/src/components/MLPanel.js` — add quality listener + warning banner (~40 lines)

---

## 3. Detection Viewport Region (#156)

### Problem

DetectionPanel has viewport toggle UI but backend ignores it. Detection always runs on full slide.

### Solution

**Backend:** Add optional `region` query param (comma-separated x,y,w,h in slide pixels) to detect endpoint. After contour extraction, filter contours whose centroid falls within the region bbox.

**Frontend:** When `analysisScope === 'viewport'`, extract pixel bounds from `viewerInstance.getViewportPixelBounds()` and include as `region` query param.

### Files

- MODIFY: `backend/routes/ml.py` — add region param, filter contours (~30 lines)
- MODIFY: `frontend/src/components/DetectionPanel.js` — send viewport bounds (~15 lines)
- MODIFY: `frontend/src/services/ApiService.js` — pass region param in detect() (~5 lines)

---

## 4. MetadataPanel (#167)

### Problem

Slide metadata (scanner, MPP, dimensions, stain) not accessible. Only format + structure shown in header.

### Solution

New `MetadataPanel` component in `#info` sidebar. Fetches from existing `/slides/{id}/info` + `/slides/{id}/tags`. Displays in collapsible accordion with copy button.

### Display

```
┌─ Métadonnées ──────────────────────┐
│ Format: MIRAX (.mrxs)              │
│ Dimensions: 98304 × 73728 px       │
│             49.2 × 36.9 mm         │
│ MPP: 0.5 µm/px                     │
│ Scanner: 3DHistech Pannoramic      │
│ Coloration: H&E                    │
│ Objectif: 20×                      │
│                          [Copier]  │
└────────────────────────────────────┘
```

### Files

- NEW: `frontend/src/components/MetadataPanel.js` (~150 lines)
- NEW: `frontend/src/css/metadata-panel.css` (~50 lines)
- MODIFY: `frontend/src/core/Router.js` — mount in #info div
- MODIFY: `frontend/src/locales/*.json` — i18n keys

---

## 5. Case Summary in Sidebar (#169)

### Problem

CaseSidebar shows slide names but no status info (annotations, quality, analysis state).

### Solution

On `setCase()`, fetch annotation stats per slide in parallel. Show annotation count badge + quality dot per slide. Case progress header.

### UI

```
┌─ Cas: Patient_001 (5 lames) ──────┐
│ 2/5 lames annotées                 │
│                                     │
│ [●] slide_HE.mrxs          🟢 12  │
│     slide_Ki67.mrxs         🟡  3  │
│ [●] slide_HER2.mrxs        🔴  0  │
└────────────────────────────────────┘
```

Green/yellow/red dot = quality score. Number = annotation count.

### Files

- MODIFY: `frontend/src/components/CaseSidebar.js` — fetch stats, render badges (~120 lines)

---

## 6. Multi-Stain Comparison (#168)

### Problem

No way to quickly compare two stains from the same case. SimilarityPanel opens new tab instead of compare mode.

### Solution

- Add "Compare" icon button next to each non-active slide in CaseSidebar
- Click emits `CASE_SLIDE_SWITCH` event with compare flag → Router opens CompareLayout
- Fix SimilarityPanel: replace `window.open()` with EventBus event

### Files

- MODIFY: `frontend/src/components/CaseSidebar.js` — add compare button per slide (~30 lines)
- MODIFY: `frontend/src/components/SimilarityPanel.js` — replace window.open (~10 lines)
- MODIFY: `frontend/src/core/Router.js` — handle compare event (~15 lines)

---

## 7. ML Overlay Toggle (#158 — simplified)

### Problem

No quick way to toggle all ML overlays on/off for before/after comparison.

### Solution

Keyboard shortcut `M` toggles all ML overlays simultaneously. New event `ML_OVERLAYS_TOGGLE`. Each overlay (heatmap, detection previews, cell markers, clustering) listens and hides/shows. Visual badge "ML masqué" when hidden.

### Files

- MODIFY: `frontend/src/core/Constants.js` — add `ML_OVERLAYS_TOGGLE` event
- MODIFY: `frontend/src/core/Router.js` — keyboard listener for M key
- MODIFY: `frontend/src/components/HeatmapOverlay.js` — listen to toggle
- MODIFY: `frontend/src/components/ClusteringOverlay.js` — listen to toggle
- MODIFY: `frontend/src/components/CellMarkerOverlay.js` — listen to toggle
- MODIFY: `frontend/src/components/AnnotationLayer.js` — listen to toggle (detection previews)

---

## 8. CSV Export (#161 — simplified)

### Problem

ML results only visible in UI, no export for clinical documentation.

### Solution

Pure JS CSV export (no dependencies). Export buttons in DetectionPanel and CellCountingPanel.

- DetectionPanel: CSV with columns (region, confidence, area_px, centroid_x, centroid_y, label)
- CellCountingPanel: CSV with summary row + cell positions if available
- Filename: `{slideName}_detection_{YYYY-MM-DD}.csv`

### Files

- NEW: `frontend/src/services/ExportService.js` — CSV generation + download utility (~60 lines)
- MODIFY: `frontend/src/components/DetectionPanel.js` — add export button (~20 lines)
- MODIFY: `frontend/src/components/CellCountingPanel.js` — add export button (~20 lines)

---

## Dependency Order

```
Constants.js (ML_OVERLAYS_TOGGLE event)
  ├── #159 Retry backoff (independent)
  ├── #160 Quality-ML warning (independent)
  ├── #156 Detection region (independent)
  ├── #167 MetadataPanel (independent)
  ├── #169 Case summary (independent)
  ├── #168 Multi-stain compare (independent)
  ├── #158 ML overlay toggle (independent)
  └── #161 CSV export (independent)
```

Implementation order: Constants → all 8 in sequence (share git state)
