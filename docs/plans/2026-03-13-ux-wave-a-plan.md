# UX Wave A Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a global toast notification system, then fix 4 quick-win UX issues (#164, #171, #155, #170).

**Architecture:** Event-driven ToastManager singleton listens to EventBus. Existing components emit `TOAST_SHOW` events on error/success. Bug fixes are minimal targeted changes to ClusteringOverlay, QualityBadge, and AnnotationStore.

**Tech Stack:** Vanilla JS (no framework), CSS variables from `variables.css`, EventBus pub-sub, DOM API.

**Note on innerHTML usage:** This plan uses innerHTML ONLY for static SVG icon constants defined in the source code — never for user-supplied data. This follows the same safe pattern used by MLTabsContainer.js, DetectionPanel.js, and other existing components in the codebase.

---

### Task 1: Add TOAST_SHOW event to Constants.js

**Files:**
- Modify: `frontend/src/core/Constants.js:88-89`

**Step 1: Add the event constant**

In `frontend/src/core/Constants.js`, inside the `Events` object, after the `PAGE_CHANGED` entry (line 89), add:

```javascript
    /** @payload {{ type: 'error'|'warning'|'success', message: string, duration?: number }} */
    TOAST_SHOW: 'ui:toastShow',
```

**Step 2: Verify lint passes**

Run: `cd frontend && npx eslint src/core/Constants.js`
Expected: no errors

**Step 3: Commit**

```bash
git add frontend/src/core/Constants.js
git commit -m "feat(constants): add TOAST_SHOW event for global notifications

Fixes #165"
```

---

### Task 2: Create ToastManager component

**Files:**
- Create: `frontend/src/components/ToastManager.js`

**Step 1: Create the component**

Create `frontend/src/components/ToastManager.js` with:
- Singleton pattern via `getToastManager()` export
- Fixed container (`div.toast-container`) appended to `document.body`, positioned bottom-right
- `_setupEventListeners()` subscribes to `Events.TOAST_SHOW` and all `*_ERROR` events
- Error events use `userFriendlyMLError()` to translate errors to French
- Success subscriptions for `ML_PREDICTION_COMPLETE` and `DETECTION_COMPLETE`
- `show({ type, message, duration })` method creates toast elements using DOM API
- SVG icons defined as static string constants at module level (same safe pattern as MLTabsContainer)
- Icon rendered via innerHTML on a span — safe because icons are code constants, never user data
- Max 3 visible toasts; oldest evicted when full
- Auto-dismiss via `setTimeout` (3s success, 5s warning, sticky for errors)
- Enter/exit CSS transitions triggered via class toggling
- `destroy()` cleans up all subscriptions, timers, and DOM elements

Key constants:
- `MAX_VISIBLE = 3`
- `DURATIONS = { success: 3000, warning: 5000, error: 0 }` (0 = sticky)

Imports needed:
- `eventBus` from `'../core/EventBus.js'`
- `Events` from `'../core/Constants.js'`
- `userFriendlyMLError` from `'../services/mlErrors.js'`

**Step 2: Verify lint passes**

Run: `cd frontend && npx eslint src/components/ToastManager.js`
Expected: no errors

**Step 3: Commit**

```bash
git add frontend/src/components/ToastManager.js
git commit -m "feat(toast): add ToastManager global notification component

Fixes #165"
```

---

### Task 3: Create toast CSS

**Files:**
- Create: `frontend/src/css/toast.css`
- Modify: `frontend/src/main.js` (add CSS import)

**Step 1: Create the stylesheet**

Create `frontend/src/css/toast.css` with:

- `.toast-container` — fixed bottom-right, z-index 10000, flex column-reverse, gap 8px, max-width 380px, pointer-events none
- `.toast` — flex row, align-items start, gap 10px, padding 12px 14px, border-radius 8px, left border 4px solid, background `var(--color-bg-elevated)`, box-shadow, pointer-events auto, starts invisible (opacity 0, translateX 100%)
- `.toast--visible` — opacity 1, translateX(0), transition 0.25s ease
- `.toast--exit` — opacity 0, translateX(100%)
- `.toast--error` — left border `var(--color-error)`, subtle red gradient background
- `.toast--warning` — left border `var(--color-warning)`, subtle orange gradient background
- `.toast--success` — left border `var(--color-success)`, subtle green gradient background
- `.toast__icon` — flex-shrink 0, color matches type variant
- `.toast__message` — flex 1, word-break break-word, font-size 13px
- `.toast__dismiss` — background none, border none, color secondary, font-size 18px, cursor pointer, opacity 0.6, hover opacity 1

**Step 2: Import in main.js**

Add `import './css/toast.css';` near the other CSS imports in `frontend/src/main.js`.

**Step 3: Verify build passes**

Run: `cd frontend && npm run build`
Expected: build succeeds

**Step 4: Commit**

```bash
git add frontend/src/css/toast.css frontend/src/main.js
git commit -m "feat(toast): add toast notification styles

Fixes #165"
```

---

### Task 4: Mount ToastManager in Router.js

**Files:**
- Modify: `frontend/src/core/Router.js:46,1240-1246`

**Step 1: Add import**

In `frontend/src/core/Router.js`, after the `MLTabsContainer` import (line 49), add:

```javascript
import { getToastManager } from '../components/ToastManager.js';
```

**Step 2: Initialize in constructor**

In the Router constructor, after `this._state = {};`, add:

```javascript
this._state.toastManager = getToastManager();
```

**Step 3: Add to destroyKeys**

In `_cleanup()` (line 1240), add `'toastManager'` to the start of the `destroyKeys` array.

**Step 4: Verify lint and build**

Run: `cd frontend && npx eslint src/core/Router.js && npm run build`
Expected: no errors, build succeeds

**Step 5: Commit**

```bash
git add frontend/src/core/Router.js
git commit -m "feat(toast): mount ToastManager in Router lifecycle

Fixes #165"
```

---

### Task 5: Fix clustering overlay bug (#155)

**Files:**
- Modify: `frontend/src/components/ClusteringOverlay.js:57-94`
- Modify: `frontend/src/components/ClusteringPanel.js:342-345`

**Step 1: Add CLUSTERING_ERROR listener in ClusteringOverlay**

In `frontend/src/components/ClusteringOverlay.js`, inside `_setupEventListeners()` (after the `CLUSTERING_OVERLAY_OPACITY` handler, around line 86), add:

```javascript
        // Clear overlay on clustering error (prevents stuck overlay after 429)
        this._unsubscribers.push(
            eventBus.on(Events.CLUSTERING_ERROR, () => {
                this.clusters = [];
                this.tileAssignments = [];
                this.visibleClusters.clear();
                this._clusterColors = {};
                this._render();
            }),
        );
```

**Step 2: Reset visible clusters in ClusteringPanel on error**

In `frontend/src/components/ClusteringPanel.js`, inside the catch block of `_runClustering()` (line 342), add `this._visibleClusters.clear();` before the error emit:

```javascript
        } catch (err) {
            console.error('[ClusteringPanel] Clustering failed:', err);
            this._visibleClusters.clear();
            eventBus.emit(Events.CLUSTERING_ERROR, { error: err.message });
            this._renderError(userFriendlyMLError(err));
```

**Step 3: Verify lint**

Run: `cd frontend && npx eslint src/components/ClusteringOverlay.js src/components/ClusteringPanel.js`
Expected: no errors

**Step 4: Commit**

```bash
git add frontend/src/components/ClusteringOverlay.js frontend/src/components/ClusteringPanel.js
git commit -m "fix(clustering): clear overlay on error, prevent stuck state after 429

Fixes #155"
```

---

### Task 6: Mount SimilarityPanel (#171)

**Files:**
- Modify: `frontend/src/components/MLTabsContainer.js:33-53`
- Modify: `frontend/src/core/Router.js:46,986-1005,643-646,1240-1246`
- Modify: `frontend/src/locales/*.json` (5 locale files)

**Step 1: Add "similaire" tab definition**

In `frontend/src/components/MLTabsContainer.js`, add a new entry to `TAB_DEFS` array (after the clustering entry, around line 53):

```javascript
    {
        id: 'similaire',
        i18nKey: 'tabs.similarity',
        icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="8" height="10" rx="1"/><rect x="14" y="3" width="8" height="10" rx="1"/><path d="M6 17v2M18 17v2M12 14v5"/></svg>',
    },
```

Note: SVG icon is a static code constant interpolated via innerHTML — same safe pattern as the other tab icons above it. No user data involved.

**Step 2: Add i18n key for all locales**

Add `"tabs.similarity"` key after `"tabs.clustering"` (line 144) in each locale file:

- `frontend/src/locales/fr.json`: `"tabs.similarity": "Similaire"`
- `frontend/src/locales/en.json`: `"tabs.similarity": "Similarity"`
- `frontend/src/locales/ja.json`: `"tabs.similarity": "\u985e\u4f3c"`
- `frontend/src/locales/zh.json`: `"tabs.similarity": "\u76f8\u4f3c"`
- `frontend/src/locales/hi.json`: `"tabs.similarity": "\u0938\u092e\u093e\u0928"`

**Step 3: Import SimilarityPanel in Router.js**

In `frontend/src/core/Router.js`, add after the FocusAssistPanel import (around line 45):

```javascript
import { SimilarityPanel } from '../components/SimilarityPanel.js';
```

**Step 4: Instantiate in _initMLSubPanels**

In `Router._initMLSubPanels()` (after the ClusteringPanel creation, around line 1004), add:

```javascript
        // SimilarityPanel in "similaire" tab
        const similairePane = tabsContainer.getPane('similaire');
        this._state.similarityPanel = new SimilarityPanel(similairePane, { slideId: slide.id });
```

**Step 5: Add to resetTargets**

In the `resetTargets` array (line 643-646), add `'similarityPanel'`:

```javascript
        const resetTargets = [
            'mlPanel', 'detectionPanel', 'cellCountingPanel',
            'clusteringPanel', 'qualityBadge', 'focusAssistPanel', 'autoTagBadge',
            'similarityPanel',
        ];
```

**Step 6: Add to destroyKeys**

In `_cleanup()` destroyKeys array (line 1240-1246), add `'similarityPanel'`.

**Step 7: Verify lint and build**

Run: `cd frontend && npx eslint src/core/Router.js src/components/MLTabsContainer.js && npm run build`
Expected: no errors, build succeeds

**Step 8: Commit**

```bash
git add frontend/src/components/MLTabsContainer.js frontend/src/core/Router.js frontend/src/locales/*.json
git commit -m "feat(similarity): mount SimilarityPanel in ML tabs

Fixes #171"
```

---

### Task 7: Annotation save feedback (#164)

**Files:**
- Modify: `frontend/src/services/AnnotationStore.js:113-163`

**Step 1: Verify EventBus imports exist**

Check that `eventBus` and `Events` are already imported at the top of `AnnotationStore.js`. They should be (used for `ANNOTATION_CREATED` etc.).

**Step 2: Add toast emit on create error**

In `createAnnotation()` catch block (line 125-128), add before `return null`:

```javascript
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'error',
                message: 'Sauvegarde de l\u2019annotation \u00e9chou\u00e9e. V\u00e9rifiez la connexion.',
            });
```

**Step 3: Add toast emit on update error**

In `updateAnnotation()` catch block (line 141-144), add before `return null`:

```javascript
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'error',
                message: 'Mise \u00e0 jour de l\u2019annotation \u00e9chou\u00e9e.',
            });
```

**Step 4: Add toast emit on delete error**

In `deleteAnnotation()` catch block (line 159-162), add before `return false`:

```javascript
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'error',
                message: 'Suppression de l\u2019annotation \u00e9chou\u00e9e.',
            });
```

**Step 5: Add success toast on create**

In `createAnnotation()` success path, after `eventBus.emit(Events.ANNOTATION_CREATED, ...)` (line 122):

```javascript
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: 'Annotation sauvegard\u00e9e',
                duration: 2000,
            });
```

**Step 6: Add success toast on delete**

In `deleteAnnotation()` success path, after `eventBus.emit(Events.ANNOTATION_DELETED, ...)` (line 156):

```javascript
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: 'Annotation supprim\u00e9e',
                duration: 2000,
            });
```

**Step 7: Verify lint**

Run: `cd frontend && npx eslint src/services/AnnotationStore.js`
Expected: no errors

**Step 8: Commit**

```bash
git add frontend/src/services/AnnotationStore.js
git commit -m "feat(annotations): add toast feedback for save/delete operations

Fixes #164"
```

---

### Task 8: Quality auto-load (#170)

**Files:**
- Modify: `frontend/src/components/QualityBadge.js:257-266,95-104`

**Step 1: Auto-trigger fetch in setSlide**

In `frontend/src/components/QualityBadge.js`, replace the `setSlide()` method (line 257-266) with:

```javascript
    setSlide(slideId) {
        this.slideId = slideId;
        this._data = null;
        this._hideTooltip();

        // Reset to loading state
        this.el.className = 'quality-badge';
        this._dot.className = 'quality-badge__dot';
        this._label.textContent = 'Qualit\u00e9 : \u00e9valuation...';

        // Auto-trigger quality assessment
        if (slideId) {
            this._fetchQuality(slideId);
        }
    }
```

**Step 2: Add low-quality warning toast**

In `_fetchQuality()`, after `this._render(data)` (line 100), add:

```javascript
            // Warn on low quality
            if (data.overall_score < 0.5 && this.eventBus) {
                this.eventBus.emit(Events.TOAST_SHOW, {
                    type: 'warning',
                    message: `Qualit\u00e9 faible (${Math.round(data.overall_score * 100)}%) \u2014 r\u00e9sultats ML possiblement affect\u00e9s`,
                });
            }
```

**Step 3: Verify lint**

Run: `cd frontend && npx eslint src/components/QualityBadge.js`
Expected: no errors

**Step 4: Commit**

```bash
git add frontend/src/components/QualityBadge.js
git commit -m "feat(quality): auto-evaluate quality on slide load, warn on low score

Fixes #170"
```

---

### Task 9: Final verification and push

**Step 1: Run full lint**

```bash
cd frontend && npx eslint src/core/Constants.js src/core/Router.js src/components/ToastManager.js src/components/ClusteringOverlay.js src/components/ClusteringPanel.js src/components/MLTabsContainer.js src/components/QualityBadge.js src/services/AnnotationStore.js
```
Expected: no errors

**Step 2: Run full build**

```bash
cd frontend && npm run build
```
Expected: build succeeds

**Step 3: Push and create PR**

```bash
git push -u origin feat/ux-wave-a
```

Create PR with title: `feat(ux): Wave A — toast system, annotation feedback, quick wins`

Body should reference: Closes #165, #164, #171, #155, #170
