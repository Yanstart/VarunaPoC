# UX Wave A: Foundation + Quick Wins — Design

**Goal:** Build a global toast notification system, then fix 4 quick-win UX issues that depend on it or are independently simple.

**Issues:** #165, #164, #171, #155, #170

**Architecture:** Event-driven — new ToastManager listens to EventBus, components emit toast events on error/success. Existing panel patterns (accordion, setSlide, destroy) reused throughout.

---

## 1. Toast Notification System (#165)

### Component: ToastManager

Singleton mounted once in Router.js. Creates a fixed `#toast-container` (bottom-right), manages a queue of max 3 visible toasts.

```
EventBus ──emit TOAST_SHOW──→ ToastManager ──renders──→ toast stack
                                    │
                         ┌──────────┼──────────┐
                         │          │          │
                      error      warning    success
                     (sticky)   (5s auto)  (3s auto)
```

### Toast anatomy

```
┌─────────────────────────────────────┐
│ ▌ [icon]  Message text         [×]  │
└─────────────────────────────────────┘
  │                               │
  colored left-border          dismiss btn
```

### Event contract

```javascript
Events.TOAST_SHOW = 'ui:toastShow'
// payload: { type: 'error'|'warning'|'success', message: string, duration?: number }
```

### Auto-subscriptions

ToastManager subscribes to all `*_ERROR` events from Constants.js and translates them to error toasts using `userFriendlyMLError()`. Also subscribes to key success events:

- `ML_PREDICTION_COMPLETE` → success toast
- `DETECTION_COMPLETE` → success toast with region count
- `ANNOTATION_CREATED` → success toast (subtle)

### Public API

```javascript
toastManager.show({ type: 'error', message: 'Sauvegarde echouee' });
```

Any component can also emit `Events.TOAST_SHOW` via EventBus for decoupled usage.

### Files

- NEW: `frontend/src/components/ToastManager.js`
- NEW: `frontend/src/css/toast.css`
- MODIFY: `frontend/src/core/Constants.js` — add `TOAST_SHOW` event
- MODIFY: `frontend/src/core/Router.js` — instantiate ToastManager, add to destroy

---

## 2. Annotation Save Feedback (#164)

### Problem

`AnnotationStore.createAnnotation()` returns null on error, logs to console only. User loses their drawing silently.

### Solution

Emit `Events.TOAST_SHOW` from AnnotationStore catch blocks. No local retry queue (YAGNI).

### Changes

- `AnnotationStore.createAnnotation()` catch → emit error toast
- `AnnotationStore.updateAnnotation()` catch → emit error toast
- `AnnotationStore.deleteAnnotation()` catch → emit error toast
- Success paths: emit success toast for create and delete (not update — too noisy)

### Files

- MODIFY: `frontend/src/services/AnnotationStore.js` — 6 emit calls in catch/success blocks

---

## 3. Mount SimilarityPanel (#171)

### Problem

SimilarityPanel is fully implemented but never instantiated in the viewer.

### Solution

Add a "similaire" tab to MLTabsContainer and mount SimilarityPanel there, same pattern as FocusAssistPanel in the "analyse" tab.

### Changes

- `Router._initMLSubPanels()` — create SimilarityPanel in a new tab pane
- Add `similarityPanel` to `resetTargets` for slide switching
- Add `similarityPanel` to `destroyKeys` for cleanup

### Files

- MODIFY: `frontend/src/core/Router.js` — ~10 lines in 3 locations

---

## 4. Clustering Overlay Bug (#155)

### Problem

After 429 error, clustering overlay persists and toggle checkbox has no effect. State desync between panel and overlay.

### Solution

On `CLUSTERING_ERROR`, overlay clears its canvas and resets visible clusters. Panel resets checkbox state.

### Changes

- `ClusteringOverlay._setupEventListeners()` — add listener for `CLUSTERING_ERROR` → call `clear()` and reset `visibleClusters`
- `ClusteringPanel._renderError()` — clear `_visibleClusters` set

### Files

- MODIFY: `frontend/src/components/ClusteringOverlay.js` — ~5 lines
- MODIFY: `frontend/src/components/ClusteringPanel.js` — ~2 lines

---

## 5. Quality Auto-Load (#170)

### Problem

QualityBadge shows "cliquez pour evaluer" until first click. Quality should auto-evaluate on slide load.

### Solution

`QualityBadge.setSlide()` auto-triggers `_fetchQuality()`. If score < 50%, emit a warning toast.

### Changes

- `QualityBadge.setSlide()` — call `_fetchQuality(slideId)` automatically
- After quality ready with low score → emit `Events.TOAST_SHOW` warning

### Files

- MODIFY: `frontend/src/components/QualityBadge.js` — ~5 lines

---

## Dependency Order

```
#165 Toast System ──→ #164 Annotation Feedback
       │               #170 Quality Auto-Load (warning toast on low score)
       │
#155 Clustering Bug (independent)
#171 SimilarityPanel Mount (independent)
```

Implementation order: #165 → (#155, #171 in parallel) → #164 → #170
