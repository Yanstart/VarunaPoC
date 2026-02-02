# Frontend Refactoring Plan - V3 (AI Features)

**Document Version:** 1.0
**Date:** 2025-12-31
**Status:** DRAFT - Architecture Planning
**Target:** Varuna V3 (AI-powered pathologist assistance)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [V3 Feature Requirements](#v3-feature-requirements)
4. [Identified Architectural Issues](#identified-architectural-issues)
5. [Refactoring Strategy](#refactoring-strategy)
6. [New Module Structure](#new-module-structure)
7. [State Management Pattern](#state-management-pattern)
8. [Overlay System Design](#overlay-system-design)
9. [Performance Optimizations](#performance-optimizations)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Testing Strategy](#testing-strategy)
12. [Migration Guide](#migration-guide)

---

## Executive Summary

**Goal:** Prepare frontend architecture for AI-powered features while maintaining Vanilla JS approach, clean architecture principles, and performance standards (60fps, <500MB memory).

**Key Additions:**
- Tag display system (organ, stain, marker)
- Feedback interface for pathologist validation
- Confidence map overlay system (WebGL-based)
- Annotation infrastructure with coordinate tracking
- State management for AI prediction workflows
- Future-proof foundation for co-visualization

**Principles:**
- ✅ **Vanilla JS only** (NO React despite TFE context)
- ✅ **Clean Architecture** (isolated modules, clear dependencies)
- ✅ **Performance First** (WebGL for overlays, lazy loading, debouncing)
- ✅ **Medical-Grade UX** (clear, professional, distraction-free)
- ✅ **Incremental Migration** (no big-bang rewrite)

---

## Current Architecture Analysis

### Strengths ✅

**1. Solid Design Patterns:**
- **Singleton:** `EventBus`, `ApiService` (proper global state)
- **Factory:** `ViewerFactory` (consistent viewer creation)
- **Observer:** `EventBus` (decoupled communication)
- **Mediator:** `ViewerManager` (multi-viewer coordination)
- **State Machine:** `ViewerState` (lifecycle management)

**2. Clean Module Organization:**
```
frontend/src/
├── core/           # EventBus, Constants (well-isolated)
├── viewers/        # ViewerInstance, Factory, Manager (clear separation)
├── components/     # UI components (Home, Viewer, Compare)
├── services/       # ApiService (backend abstraction)
└── utils/          # coordinates.js (critical utilities)
```

**3. Coordinate System:**
- Bidirectional OSD ↔ OpenSlide mapping (`coordinates.js`)
- Multi-level pyramid support
- Sync normalization for different slide sizes
- **Ready for annotations** (just needs annotation layer)

**4. Performance Considerations:**
- Tile streaming with DZI
- Request deduplication in ApiService
- Event debouncing ready (SyncConfig)
- ViewerInstance event suppression during sync

### Weaknesses / Gaps for V3 ❌

**1. No Overlay System:**
- Current architecture: only base slide tiles
- Missing: WebGL overlay layer for AI predictions
- Missing: Canvas-based annotation layer
- Missing: Z-index management for multi-layer rendering

**2. No State Management for AI Workflow:**
- Current: basic app state in `main.js` (page routing only)
- Missing: prediction state (pending/loaded/validated)
- Missing: feedback state (accepted/rejected/corrected)
- Missing: undo/redo for annotations
- Missing: dirty state tracking (unsaved changes)

**3. No Tag/Metadata Display:**
- Current: basic slide info panel (dimensions, format)
- Missing: tag chips UI (organ, stain, marker)
- Missing: metadata panel component
- Missing: confidence indicators

**4. Limited Component Composition:**
- Current: monolithic components (`CompareLayout.js` is 600+ lines)
- Missing: reusable UI primitives (Button, Card, Badge, etc.)
- Missing: composition pattern for complex UI
- Challenge: keep it simple without framework overhead

**5. No Feedback Interface:**
- Missing: validation controls (accept/reject/correct)
- Missing: annotation tools (bounding box, polygon, freehand)
- Missing: comment system for pathologist notes

**6. Performance Concerns:**
- Canvas-based overlays can block main thread
- No Web Worker support for heavy computations
- No virtual scrolling for large lists
- Memory leaks possible with complex event listeners

---

## V3 Feature Requirements

### 1. Tag Display System

**User Story:** As a pathologist, I need to see slide metadata (organ, stain, marker) at a glance to understand context.

**Technical Requirements:**
- Display tags as chips/badges above viewer
- Color-coded by category (organ=blue, stain=green, marker=purple)
- Editable tags (click to modify)
- Backend integration: `GET /api/slides/{id}/tags`
- State persistence: save tag changes via `PUT /api/slides/{id}/tags`

**UI Mock:**
```
┌─────────────────────────────────────────────┐
│ [Organ: Liver] [Stain: H&E] [Marker: CD20] │
│                                             │
│           OpenSeadragon Viewer              │
│                                             │
└─────────────────────────────────────────────┘
```

### 2. Feedback Interface

**User Story:** As a pathologist, I need to validate AI predictions and provide corrections.

**Technical Requirements:**
- Three-button validation: ✓ Accept | ✗ Reject | ✏️ Correct
- Accept: mark prediction as correct, save to backend
- Reject: mark prediction as incorrect, optionally add reason
- Correct: enter annotation mode, draw correct region
- Backend integration: `POST /api/predictions/{id}/feedback`
- State tracking: feedback status per prediction

**UI Mock:**
```
┌─────────────────────────────────────────────┐
│ AI Prediction: Tumor Region (Confidence 87%)│
│                                             │
│  [✓ Accept]  [✗ Reject]  [✏️ Correct]      │
└─────────────────────────────────────────────┘
```

### 3. Confidence Map Overlay

**User Story:** As a pathologist, I need to see AI confidence visually overlaid on the slide.

**Technical Requirements:**
- WebGL-based heatmap overlay (performance critical)
- Color gradient: low confidence (red) → high confidence (green)
- Transparency: 0.5 opacity (slide visible underneath)
- Toggle: show/hide overlay with button
- Zoom-independent: overlay scales with slide
- Backend integration: `GET /api/predictions/{id}/confidence-map`
- Data format: PNG tiles or vector polygons

**Rendering Strategy:**
- **Option A (Tiles):** Backend generates confidence map as PNG tiles, frontend overlays via second OpenSeadragon layer
- **Option B (Vectors):** Backend sends GeoJSON polygons with confidence values, frontend renders via WebGL canvas
- **Recommendation:** Option A for Phase 1 (simpler), Option B for Phase 2 (more flexible)

### 4. Annotation Infrastructure

**User Story:** As a pathologist, I need to draw annotations (bounding boxes, polygons) with precise coordinates.

**Technical Requirements:**
- Drawing tools: rectangle, polygon, freehand
- Coordinate tracking: store in level 0 absolute pixels
- Backend integration: `POST /api/slides/{id}/annotations`
- Annotation format (GeoJSON):
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[x1,y1], [x2,y2], ...]]
  },
  "properties": {
    "label": "Tumor",
    "author": "Dr. Smith",
    "timestamp": "2025-12-31T10:30:00Z"
  }
}
```
- Render: Canvas layer on top of OpenSeadragon
- Interaction: click to select, drag to move, handles to resize
- Save: debounced auto-save on change

### 5. Co-Visualization Preparation (Future)

**User Story:** As a pathologist, I need to collaborate with remote colleagues in real-time.

**Technical Requirements (Phase 2+):**
- WebSocket connection for real-time sync
- Cursor position broadcast
- Annotation change notifications
- Conflict resolution for concurrent edits
- **NOT in V3 initial scope** but architecture must support it

**Architecture Preparation:**
- EventBus already supports real-time event emission
- Need: WebSocket service layer
- Need: state reconciliation logic
- Need: user presence indicators

---

## Identified Architectural Issues

### Issue 1: Monolithic Components

**Problem:**
```javascript
// components/CompareLayout.js - 600+ lines, hard to maintain
class CompareLayout {
  constructor() {
    // Manages layout, viewers, sync, UI, events...
    // Too many responsibilities!
  }
}
```

**Solution: Component Composition**
```javascript
// Break into smaller, focused components
class CompareLayout {
  constructor() {
    this.layoutManager = new LayoutManager();
    this.syncController = new SyncController();
    this.viewerPanels = [];
  }
}

// Each sub-component has single responsibility
class LayoutManager {
  setLayout(preset) { /* only layout logic */ }
}

class SyncController {
  enable() { /* only sync logic */ }
}
```

### Issue 2: Missing State Management

**Problem:**
- State scattered across multiple components
- No single source of truth for AI predictions
- Hard to debug state changes
- No undo/redo support

**Current State Management:**
```javascript
// main.js
const appState = {
  currentPage: 'home',
  selectedSlide: null,
  viewer: null
};

// No centralized state for:
// - AI predictions (where stored?)
// - Feedback status (in component?)
// - Annotations (in viewer?)
```

**Solution: Centralized State Store (Vanilla JS)**
```javascript
// core/StateStore.js
class StateStore {
  constructor() {
    this._state = {
      slides: {},
      predictions: {},
      feedback: {},
      annotations: {},
      ui: {}
    };
    this._listeners = new Map();
    this._history = [];  // for undo/redo
  }

  get(path) { /* get nested state */ }
  set(path, value) { /* set + notify listeners */ }
  subscribe(path, callback) { /* observe changes */ }
  undo() { /* revert to previous state */ }
  redo() { /* restore next state */ }
}

// Usage
const store = StateStore.getInstance();
store.subscribe('predictions.slide123', (predictions) => {
  updateUI(predictions);
});

store.set('predictions.slide123', newPredictions);  // triggers update
```

**Benefits:**
- Single source of truth
- Time-travel debugging (undo/redo)
- React-like subscription pattern (but Vanilla JS)
- Easy to persist state (localStorage/sessionStorage)

### Issue 3: No Overlay Infrastructure

**Problem:**
- OpenSeadragon manages only base slide tiles
- No support for overlay layers (confidence maps, annotations)
- Canvas rendering blocks main thread (poor performance)

**Solution: Multi-Layer Rendering System**
```javascript
// layers/LayerManager.js
class LayerManager {
  constructor(viewer) {
    this.viewer = viewer;
    this.layers = new Map();

    // Layer types
    this.addLayer('base', new TileLayer(viewer));       // OpenSeadragon
    this.addLayer('confidence', new WebGLLayer(viewer)); // WebGL heatmap
    this.addLayer('annotations', new CanvasLayer(viewer)); // Canvas drawings
  }

  addLayer(id, layer) { /* z-index management */ }
  getLayer(id) { /* retrieve layer */ }
  toggleLayer(id) { /* show/hide */ }
}

// layers/WebGLLayer.js
class WebGLLayer {
  constructor(viewer) {
    this.canvas = document.createElement('canvas');
    this.gl = this.canvas.getContext('webgl2');
    this.shader = this.compileShaders();
  }

  renderHeatmap(data) {
    // WebGL rendering (60fps even with complex overlays)
    this.gl.useProgram(this.shader);
    this.gl.drawArrays(this.gl.TRIANGLES, 0, data.length);
  }
}

// layers/CanvasLayer.js
class CanvasLayer {
  constructor(viewer) {
    this.canvas = document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.annotations = [];
  }

  drawAnnotation(annotation) {
    // Canvas 2D API for vector annotations
    this.ctx.strokeStyle = annotation.color;
    this.ctx.stroke(annotation.path);
  }
}
```

**Benefits:**
- Separation of concerns (each layer independent)
- Performance (WebGL for heavy rendering)
- Flexibility (easy to add new layer types)
- Medical-grade rendering (GPU-accelerated)

### Issue 4: Event Handler Memory Leaks

**Problem:**
```javascript
// components/Viewer.js
viewer.addHandler('viewport-change', function() {
  // Anonymous function, hard to remove
  // Potential memory leak if viewer destroyed
});
```

**Solution: Explicit Handler Management**
```javascript
class ViewerInstance {
  constructor() {
    this._boundHandlers = {};
  }

  _bindEventHandlers() {
    // Bound methods (can be removed)
    this._boundHandlers.viewportChange = this._onViewportChange.bind(this);
    this._osdViewer.addHandler('viewport-change', this._boundHandlers.viewportChange);
  }

  destroy() {
    // Clean removal
    this._osdViewer.removeHandler('viewport-change', this._boundHandlers.viewportChange);
    this._boundHandlers = {};
  }
}
```

**Current Status:** ✅ Already implemented in `ViewerInstance.js`!

### Issue 5: No UI Component Library

**Problem:**
- Inline styles everywhere
- Inconsistent button styles
- No reusable UI primitives
- Hard to maintain visual consistency

**Solution: Lightweight UI Kit (Vanilla JS)**
```javascript
// ui/components/Button.js
export function Button({ label, variant = 'primary', onClick }) {
  const button = document.createElement('button');
  button.className = `btn btn-${variant}`;
  button.textContent = label;
  button.addEventListener('click', onClick);
  return button;
}

// ui/components/Badge.js
export function Badge({ text, color = 'blue' }) {
  const badge = document.createElement('span');
  badge.className = `badge badge-${color}`;
  badge.textContent = text;
  return badge;
}

// ui/components/Card.js
export function Card({ title, content, actions }) {
  const card = document.createElement('div');
  card.className = 'card';
  card.innerHTML = `
    <div class="card-header">${title}</div>
    <div class="card-body">${content}</div>
    <div class="card-actions">${actions}</div>
  `;
  return card;
}

// Usage
const acceptBtn = Button({
  label: 'Accept',
  variant: 'success',
  onClick: () => acceptPrediction()
});
```

**Benefits:**
- Consistency across UI
- Reusability
- Easy to theme (CSS variables)
- No framework overhead

---

## Refactoring Strategy

### Phase 1: Foundation (Week 1-2)

**Goal:** Prepare architecture without breaking existing functionality.

**Tasks:**
1. Create `StateStore` for centralized state management
2. Create `LayerManager` for multi-layer rendering
3. Create UI component library (Button, Badge, Card, etc.)
4. Extract reusable logic from monolithic components
5. Add comprehensive tests for new modules

**Deliverables:**
- `core/StateStore.js`
- `layers/LayerManager.js`
- `layers/WebGLLayer.js`
- `layers/CanvasLayer.js`
- `ui/components/` directory
- Test coverage: >80%

**Migration Strategy:**
- New code uses new architecture
- Existing code remains unchanged
- Gradual migration component by component

### Phase 2: Tag Display (Week 3)

**Goal:** Implement tag display system.

**Tasks:**
1. Create `TagPanel` component
2. Integrate with backend API (`/api/slides/{id}/tags`)
3. Add tag editing UI
4. Connect to StateStore
5. Add to existing Viewer page

**Deliverables:**
- `components/TagPanel.js`
- CSS styles for tag chips
- Backend integration tests
- User acceptance testing

### Phase 3: Feedback Interface (Week 4-5)

**Goal:** Implement pathologist feedback workflow.

**Tasks:**
1. Create `FeedbackPanel` component
2. Implement validation buttons (Accept/Reject/Correct)
3. Connect to StateStore (predictions state)
4. Backend integration (`/api/predictions/{id}/feedback`)
5. Add to Viewer page

**Deliverables:**
- `components/FeedbackPanel.js`
- Feedback state management
- Backend API integration
- Validation workflow tests

### Phase 4: Confidence Map Overlay (Week 6-7)

**Goal:** Implement WebGL-based confidence map.

**Tasks:**
1. Create `ConfidenceMapLayer` (extends `WebGLLayer`)
2. Implement shader programs (vertex + fragment)
3. Tile-based overlay rendering
4. Toggle controls (show/hide overlay)
5. Backend integration (`/api/predictions/{id}/confidence-map`)

**Deliverables:**
- `layers/ConfidenceMapLayer.js`
- WebGL shaders
- Overlay controls UI
- Performance benchmarks (60fps verified)

### Phase 5: Annotation System (Week 8-10)

**Goal:** Implement drawing and annotation tools.

**Tasks:**
1. Create `AnnotationLayer` (extends `CanvasLayer`)
2. Implement drawing tools (rectangle, polygon, freehand)
3. Coordinate tracking and conversion
4. Annotation CRUD operations
5. Backend integration (`/api/slides/{id}/annotations`)
6. Auto-save with debouncing

**Deliverables:**
- `layers/AnnotationLayer.js`
- `tools/DrawingTools.js`
- Annotation state management
- GeoJSON import/export
- User documentation

### Phase 6: Integration & Polish (Week 11-12)

**Goal:** Integrate all features and polish UX.

**Tasks:**
1. Integration testing (all features together)
2. Performance optimization (profiling, lazy loading)
3. UX polish (animations, transitions, feedback)
4. User documentation updates
5. Deployment preparation

**Deliverables:**
- End-to-end tests
- Performance report
- User manual updates
- Production build

---

## New Module Structure

```
frontend/src/
├── core/
│   ├── EventBus.js          ✅ EXISTING (no changes)
│   ├── Constants.js         ✅ EXISTING (add AI events)
│   └── StateStore.js        🆕 NEW (centralized state)
│
├── viewers/
│   ├── ViewerInstance.js    ✅ EXISTING (minor updates for layers)
│   ├── ViewerFactory.js     ✅ EXISTING (no changes)
│   ├── ViewerManager.js     ✅ EXISTING (no changes)
│   ├── ViewerState.js       ✅ EXISTING (no changes)
│   └── SyncController.js    ✅ EXISTING (no changes)
│
├── layers/                  🆕 NEW DIRECTORY
│   ├── LayerManager.js      🆕 Multi-layer coordination
│   ├── TileLayer.js         🆕 Base slide tiles (wraps OSD)
│   ├── WebGLLayer.js        🆕 WebGL rendering base class
│   ├── CanvasLayer.js       🆕 Canvas 2D rendering base class
│   ├── ConfidenceMapLayer.js 🆕 AI confidence heatmap
│   └── AnnotationLayer.js   🆕 Annotation drawings
│
├── components/
│   ├── Home.js              ✅ EXISTING (no changes)
│   ├── FolderBrowser.js     ✅ EXISTING (no changes)
│   ├── SlideList.js         ✅ EXISTING (no changes)
│   ├── Viewer.js            ⚠️  REFACTOR (integrate layers)
│   ├── CompareLayout.js     ⚠️  REFACTOR (split into sub-components)
│   ├── TagPanel.js          🆕 Tag display/editing
│   ├── FeedbackPanel.js     🆕 AI prediction validation
│   └── AnnotationToolbar.js 🆕 Drawing tool controls
│
├── ui/                      🆕 NEW DIRECTORY (UI component library)
│   ├── components/
│   │   ├── Button.js        🆕 Reusable button
│   │   ├── Badge.js         🆕 Tag/label chips
│   │   ├── Card.js          🆕 Card container
│   │   ├── Modal.js         🆕 Modal dialogs
│   │   ├── Dropdown.js      🆕 Dropdown menus
│   │   └── Tooltip.js       🆕 Tooltips
│   └── styles/
│       ├── variables.css    🆕 CSS custom properties
│       ├── components.css   🆕 Component styles
│       └── utilities.css    🆕 Utility classes
│
├── services/
│   ├── ApiService.js        ✅ EXISTING (add AI endpoints)
│   ├── PredictionService.js 🆕 AI prediction management
│   ├── AnnotationService.js 🆕 Annotation CRUD
│   └── WebSocketService.js  🆕 Real-time communication (future)
│
├── tools/                   🆕 NEW DIRECTORY (drawing tools)
│   ├── DrawingTool.js       🆕 Base class for tools
│   ├── RectangleTool.js     🆕 Rectangle drawing
│   ├── PolygonTool.js       🆕 Polygon drawing
│   └── FreehandTool.js      🆕 Freehand drawing
│
├── utils/
│   ├── coordinates.js       ✅ EXISTING (add annotation helpers)
│   ├── api.js               ✅ EXISTING (no changes)
│   ├── debounce.js          🆕 Debouncing utility
│   └── validation.js        🆕 Input validation
│
├── workers/                 🆕 NEW DIRECTORY (Web Workers)
│   └── confidenceMapWorker.js 🆕 Heavy computation offload
│
├── main.js                  ⚠️  REFACTOR (integrate StateStore)
└── style.css                ⚠️  REFACTOR (use CSS variables)
```

**Legend:**
- ✅ **EXISTING** - No changes or minor updates
- ⚠️  **REFACTOR** - Significant changes required
- 🆕 **NEW** - New file/directory

---

## State Management Pattern

### StateStore Architecture

**Inspired by:** Redux (unidirectional data flow) but Vanilla JS implementation.

**Core Principles:**
1. **Single Source of Truth:** All application state in one store
2. **Immutable State:** Never mutate state directly
3. **Predictable Updates:** State changes through defined actions
4. **Observable:** Components subscribe to state changes

### Implementation

```javascript
// core/StateStore.js

/**
 * StateStore - Centralized state management (Vanilla JS)
 *
 * Inspired by Redux but simplified for Varuna's needs.
 * Provides single source of truth for application state.
 *
 * @example
 * const store = StateStore.getInstance();
 *
 * // Subscribe to state changes
 * store.subscribe('predictions.slide123', (predictions) => {
 *   console.log('Predictions updated:', predictions);
 * });
 *
 * // Update state
 * store.set('predictions.slide123', newPredictions);
 */
class StateStore {
  constructor() {
    if (StateStore.instance) {
      return StateStore.instance;
    }

    /**
     * Application state tree
     * @type {Object}
     */
    this._state = {
      // Slide metadata
      slides: {},

      // AI predictions
      predictions: {
        // slideId: {
        //   id: 'pred123',
        //   type: 'tumor_detection',
        //   confidence: 0.87,
        //   regions: [...],
        //   status: 'pending' | 'accepted' | 'rejected' | 'corrected'
        // }
      },

      // Pathologist feedback
      feedback: {
        // predictionId: {
        //   action: 'accept' | 'reject' | 'correct',
        //   comment: 'Optional comment',
        //   timestamp: Date,
        //   author: 'Dr. Smith'
        // }
      },

      // Annotations
      annotations: {
        // slideId: [
        //   { type: 'polygon', coordinates: [...], label: 'Tumor' }
        // ]
      },

      // UI state
      ui: {
        currentPage: 'home',
        selectedSlide: null,
        activeLayer: 'base',
        showConfidenceMap: false,
        drawingTool: null
      }
    };

    /**
     * State change listeners
     * @type {Map<string, Set<Function>>}
     */
    this._listeners = new Map();

    /**
     * State history for undo/redo
     * @type {Array<Object>}
     */
    this._history = [];

    /**
     * Current history position
     * @type {number}
     */
    this._historyIndex = -1;

    /**
     * Maximum history size
     * @type {number}
     */
    this._maxHistory = 50;

    StateStore.instance = this;
  }

  /**
   * Get singleton instance
   * @returns {StateStore}
   */
  static getInstance() {
    if (!StateStore.instance) {
      StateStore.instance = new StateStore();
    }
    return StateStore.instance;
  }

  /**
   * Get state value by path
   * @param {string} path - Dot-notation path (e.g., 'predictions.slide123')
   * @returns {*} State value
   */
  get(path) {
    return this._getByPath(this._state, path);
  }

  /**
   * Set state value by path
   * @param {string} path - Dot-notation path
   * @param {*} value - New value
   * @param {Object} options - Options
   * @param {boolean} options.addToHistory - Add to undo/redo history (default: true)
   */
  set(path, value, options = {}) {
    const { addToHistory = true } = options;

    // Save current state to history
    if (addToHistory) {
      this._addToHistory();
    }

    // Update state (immutably)
    const newState = this._setByPath({ ...this._state }, path, value);
    this._state = newState;

    // Notify listeners
    this._notifyListeners(path, value);
  }

  /**
   * Subscribe to state changes
   * @param {string} path - Path to watch
   * @param {Function} callback - Callback function
   * @returns {Function} Unsubscribe function
   */
  subscribe(path, callback) {
    if (!this._listeners.has(path)) {
      this._listeners.set(path, new Set());
    }

    this._listeners.get(path).add(callback);

    // Return unsubscribe function
    return () => {
      const listeners = this._listeners.get(path);
      if (listeners) {
        listeners.delete(callback);
      }
    };
  }

  /**
   * Undo last state change
   * @returns {boolean} True if undo was performed
   */
  undo() {
    if (this._historyIndex > 0) {
      this._historyIndex--;
      this._state = this._history[this._historyIndex];
      this._notifyAllListeners();
      return true;
    }
    return false;
  }

  /**
   * Redo previously undone state change
   * @returns {boolean} True if redo was performed
   */
  redo() {
    if (this._historyIndex < this._history.length - 1) {
      this._historyIndex++;
      this._state = this._history[this._historyIndex];
      this._notifyAllListeners();
      return true;
    }
    return false;
  }

  /**
   * Clear all state (reset to initial)
   */
  clear() {
    this._state = {
      slides: {},
      predictions: {},
      feedback: {},
      annotations: {},
      ui: {}
    };
    this._history = [];
    this._historyIndex = -1;
    this._notifyAllListeners();
  }

  /**
   * Get entire state (for debugging)
   * @returns {Object} Current state
   */
  getState() {
    return JSON.parse(JSON.stringify(this._state));  // Deep clone
  }

  /**
   * Internal: Get value by dot-notation path
   * @private
   */
  _getByPath(obj, path) {
    const keys = path.split('.');
    let current = obj;

    for (const key of keys) {
      if (current === undefined || current === null) {
        return undefined;
      }
      current = current[key];
    }

    return current;
  }

  /**
   * Internal: Set value by dot-notation path (immutably)
   * @private
   */
  _setByPath(obj, path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    let current = obj;

    // Navigate to parent
    for (const key of keys) {
      if (!current[key]) {
        current[key] = {};
      }
      current = current[key];
    }

    // Set value
    current[lastKey] = value;
    return obj;
  }

  /**
   * Internal: Add current state to history
   * @private
   */
  _addToHistory() {
    // Remove future states if we're in the middle of history
    if (this._historyIndex < this._history.length - 1) {
      this._history = this._history.slice(0, this._historyIndex + 1);
    }

    // Add current state
    this._history.push(JSON.parse(JSON.stringify(this._state)));
    this._historyIndex++;

    // Limit history size
    if (this._history.length > this._maxHistory) {
      this._history.shift();
      this._historyIndex--;
    }
  }

  /**
   * Internal: Notify listeners of state change
   * @private
   */
  _notifyListeners(path, value) {
    // Notify exact path listeners
    const listeners = this._listeners.get(path);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(value);
        } catch (error) {
          console.error(`[StateStore] Error in listener for "${path}":`, error);
        }
      });
    }

    // Notify parent path listeners (e.g., 'predictions' when 'predictions.slide123' changes)
    const parts = path.split('.');
    for (let i = parts.length - 1; i > 0; i--) {
      const parentPath = parts.slice(0, i).join('.');
      const parentListeners = this._listeners.get(parentPath);
      if (parentListeners) {
        const parentValue = this._getByPath(this._state, parentPath);
        parentListeners.forEach(callback => {
          try {
            callback(parentValue);
          } catch (error) {
            console.error(`[StateStore] Error in parent listener for "${parentPath}":`, error);
          }
        });
      }
    }
  }

  /**
   * Internal: Notify all listeners (for undo/redo)
   * @private
   */
  _notifyAllListeners() {
    for (const [path, listeners] of this._listeners.entries()) {
      const value = this._getByPath(this._state, path);
      listeners.forEach(callback => {
        try {
          callback(value);
        } catch (error) {
          console.error(`[StateStore] Error in listener for "${path}":`, error);
        }
      });
    }
  }
}

// Export singleton
export const stateStore = StateStore.getInstance();
export { StateStore };
export default stateStore;
```

### Usage Examples

**1. Subscribe to predictions:**
```javascript
import { stateStore } from './core/StateStore.js';

// Subscribe to all predictions
const unsubscribe = stateStore.subscribe('predictions', (predictions) => {
  console.log('Predictions updated:', predictions);
  updatePredictionUI(predictions);
});

// Subscribe to specific slide's predictions
stateStore.subscribe('predictions.slide123', (predictions) => {
  console.log('Slide 123 predictions:', predictions);
});

// Unsubscribe when component is destroyed
unsubscribe();
```

**2. Update feedback status:**
```javascript
import { stateStore } from './core/StateStore.js';

function acceptPrediction(predictionId) {
  // Get current feedback
  const currentFeedback = stateStore.get('feedback') || {};

  // Update feedback
  stateStore.set(`feedback.${predictionId}`, {
    action: 'accept',
    timestamp: new Date(),
    author: 'Dr. Smith'
  });

  // Send to backend
  apiService.submitFeedback(predictionId, {
    action: 'accept'
  });
}
```

**3. Undo/Redo:**
```javascript
// Undo button click
document.getElementById('undo-btn').addEventListener('click', () => {
  if (stateStore.undo()) {
    console.log('Undo successful');
  } else {
    console.log('Nothing to undo');
  }
});

// Redo button click
document.getElementById('redo-btn').addEventListener('click', () => {
  if (stateStore.redo()) {
    console.log('Redo successful');
  }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key === 'z') {
    stateStore.undo();
  }
  if (e.ctrlKey && e.shiftKey && e.key === 'z') {
    stateStore.redo();
  }
});
```

---

## Overlay System Design

### Multi-Layer Architecture

**Goal:** Render multiple layers (base slide, confidence map, annotations) with high performance.

**Architecture:**
```
┌─────────────────────────────────────────┐
│           User Interaction              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│         Layer Manager                   │
│  - Coordinates layer rendering          │
│  - Manages z-index and visibility       │
│  - Synchronizes viewport across layers  │
└─────────────────────────────────────────┘
       ↓              ↓              ↓
┌──────────┐  ┌──────────────┐  ┌────────────┐
│  Base    │  │  Confidence  │  │ Annotation │
│  Tile    │  │  Map (WebGL) │  │ (Canvas)   │
│  Layer   │  │              │  │            │
│  (OSD)   │  │              │  │            │
└──────────┘  └──────────────┘  └────────────┘
    z:0           z:1               z:2
```

### Layer Implementation

**1. LayerManager:**
```javascript
// layers/LayerManager.js

/**
 * LayerManager - Manages multiple rendering layers
 *
 * Coordinates rendering of base tiles, overlays, and annotations.
 * Ensures proper z-index ordering and viewport synchronization.
 */
class LayerManager {
  constructor(viewerInstance) {
    this.viewer = viewerInstance;
    this.layers = new Map();
    this.container = null;
    this._initialize();
  }

  _initialize() {
    // Create layer container
    this.container = document.createElement('div');
    this.container.className = 'layer-container';
    this.container.style.cssText = `
      position: relative;
      width: 100%;
      height: 100%;
    `;

    // Insert into viewer
    this.viewer.container.appendChild(this.container);

    // Add default layers
    this.addLayer('base', new TileLayer(this.viewer), 0);
  }

  /**
   * Add a new layer
   * @param {string} id - Layer ID
   * @param {Layer} layer - Layer instance
   * @param {number} zIndex - Z-index (higher = on top)
   */
  addLayer(id, layer, zIndex) {
    layer.setZIndex(zIndex);
    this.layers.set(id, layer);
    this.container.appendChild(layer.element);

    // Sync viewport
    this._syncViewport(layer);
  }

  /**
   * Get layer by ID
   * @param {string} id - Layer ID
   * @returns {Layer|null}
   */
  getLayer(id) {
    return this.layers.get(id) || null;
  }

  /**
   * Toggle layer visibility
   * @param {string} id - Layer ID
   * @param {boolean} visible - Visibility
   */
  toggleLayer(id, visible) {
    const layer = this.layers.get(id);
    if (layer) {
      layer.setVisible(visible);
    }
  }

  /**
   * Sync viewport across all layers
   * @private
   */
  _syncViewport(layer) {
    this.viewer.on('viewportChange', (viewport) => {
      layer.updateViewport(viewport);
    });
  }

  /**
   * Destroy all layers
   */
  destroy() {
    for (const layer of this.layers.values()) {
      layer.destroy();
    }
    this.layers.clear();
    this.container.remove();
  }
}

export { LayerManager };
```

**2. Base Layer Classes:**
```javascript
// layers/Layer.js (abstract base class)

/**
 * Layer - Abstract base class for all layers
 */
class Layer {
  constructor() {
    this.element = null;
    this.visible = true;
    this.zIndex = 0;
  }

  setZIndex(zIndex) {
    this.zIndex = zIndex;
    if (this.element) {
      this.element.style.zIndex = zIndex;
    }
  }

  setVisible(visible) {
    this.visible = visible;
    if (this.element) {
      this.element.style.display = visible ? 'block' : 'none';
    }
  }

  updateViewport(viewport) {
    // Override in subclass
  }

  destroy() {
    if (this.element) {
      this.element.remove();
    }
  }
}

export { Layer };
```

**3. WebGL Layer (for confidence maps):**
```javascript
// layers/WebGLLayer.js

import { Layer } from './Layer.js';

/**
 * WebGLLayer - GPU-accelerated rendering layer
 *
 * Used for heatmaps, confidence maps, and other
 * performance-critical visualizations.
 */
class WebGLLayer extends Layer {
  constructor() {
    super();

    // Create canvas
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'webgl-layer';
    this.canvas.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    `;

    this.element = this.canvas;

    // Initialize WebGL context
    this.gl = this.canvas.getContext('webgl2', {
      alpha: true,
      premultipliedAlpha: false
    });

    if (!this.gl) {
      console.error('[WebGLLayer] WebGL 2 not supported');
      return;
    }

    // Compile shaders
    this._initShaders();

    // Create buffers
    this._initBuffers();
  }

  _initShaders() {
    // Vertex shader
    const vertexShaderSource = `
      attribute vec2 a_position;
      attribute vec2 a_texCoord;
      varying vec2 v_texCoord;

      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
        v_texCoord = a_texCoord;
      }
    `;

    // Fragment shader (heatmap)
    const fragmentShaderSource = `
      precision mediump float;
      uniform sampler2D u_texture;
      uniform float u_opacity;
      varying vec2 v_texCoord;

      // Heatmap color gradient (red -> yellow -> green)
      vec3 heatmap(float value) {
        if (value < 0.5) {
          return mix(vec3(1.0, 0.0, 0.0), vec3(1.0, 1.0, 0.0), value * 2.0);
        } else {
          return mix(vec3(1.0, 1.0, 0.0), vec3(0.0, 1.0, 0.0), (value - 0.5) * 2.0);
        }
      }

      void main() {
        float confidence = texture2D(u_texture, v_texCoord).r;
        vec3 color = heatmap(confidence);
        gl_FragColor = vec4(color, u_opacity);
      }
    `;

    this.program = this._createProgram(vertexShaderSource, fragmentShaderSource);
    this.gl.useProgram(this.program);

    // Get attribute/uniform locations
    this.locations = {
      position: this.gl.getAttribLocation(this.program, 'a_position'),
      texCoord: this.gl.getAttribLocation(this.program, 'a_texCoord'),
      texture: this.gl.getUniformLocation(this.program, 'u_texture'),
      opacity: this.gl.getUniformLocation(this.program, 'u_opacity')
    };
  }

  _createProgram(vertexSource, fragmentSource) {
    const vertexShader = this._compileShader(this.gl.VERTEX_SHADER, vertexSource);
    const fragmentShader = this._compileShader(this.gl.FRAGMENT_SHADER, fragmentSource);

    const program = this.gl.createProgram();
    this.gl.attachShader(program, vertexShader);
    this.gl.attachShader(program, fragmentShader);
    this.gl.linkProgram(program);

    if (!this.gl.getProgramParameter(program, this.gl.LINK_STATUS)) {
      console.error('[WebGLLayer] Program link error:', this.gl.getProgramInfoLog(program));
      return null;
    }

    return program;
  }

  _compileShader(type, source) {
    const shader = this.gl.createShader(type);
    this.gl.shaderSource(shader, source);
    this.gl.compileShader(shader);

    if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) {
      console.error('[WebGLLayer] Shader compile error:', this.gl.getShaderInfoLog(shader));
      return null;
    }

    return shader;
  }

  _initBuffers() {
    // Position buffer (full screen quad)
    const positions = new Float32Array([
      -1, -1,
       1, -1,
      -1,  1,
       1,  1
    ]);

    this.positionBuffer = this.gl.createBuffer();
    this.gl.bindBuffer(this.gl.ARRAY_BUFFER, this.positionBuffer);
    this.gl.bufferData(this.gl.ARRAY_BUFFER, positions, this.gl.STATIC_DRAW);

    // Texture coordinate buffer
    const texCoords = new Float32Array([
      0, 0,
      1, 0,
      0, 1,
      1, 1
    ]);

    this.texCoordBuffer = this.gl.createBuffer();
    this.gl.bindBuffer(this.gl.ARRAY_BUFFER, this.texCoordBuffer);
    this.gl.bufferData(this.gl.ARRAY_BUFFER, texCoords, this.gl.STATIC_DRAW);
  }

  /**
   * Render confidence map
   * @param {ImageData} data - Confidence data (grayscale)
   * @param {number} opacity - Opacity (0-1)
   */
  renderConfidenceMap(data, opacity = 0.5) {
    // Resize canvas if needed
    if (this.canvas.width !== data.width || this.canvas.height !== data.height) {
      this.canvas.width = data.width;
      this.canvas.height = data.height;
      this.gl.viewport(0, 0, data.width, data.height);
    }

    // Create texture from data
    const texture = this.gl.createTexture();
    this.gl.bindTexture(this.gl.TEXTURE_2D, texture);
    this.gl.texImage2D(
      this.gl.TEXTURE_2D,
      0,
      this.gl.LUMINANCE,
      data.width,
      data.height,
      0,
      this.gl.LUMINANCE,
      this.gl.UNSIGNED_BYTE,
      data.data
    );

    // Set texture parameters
    this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_S, this.gl.CLAMP_TO_EDGE);
    this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_T, this.gl.CLAMP_TO_EDGE);
    this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MIN_FILTER, this.gl.LINEAR);
    this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MAG_FILTER, this.gl.LINEAR);

    // Use program
    this.gl.useProgram(this.program);

    // Bind buffers
    this.gl.bindBuffer(this.gl.ARRAY_BUFFER, this.positionBuffer);
    this.gl.enableVertexAttribArray(this.locations.position);
    this.gl.vertexAttribPointer(this.locations.position, 2, this.gl.FLOAT, false, 0, 0);

    this.gl.bindBuffer(this.gl.ARRAY_BUFFER, this.texCoordBuffer);
    this.gl.enableVertexAttribArray(this.locations.texCoord);
    this.gl.vertexAttribPointer(this.locations.texCoord, 2, this.gl.FLOAT, false, 0, 0);

    // Set uniforms
    this.gl.activeTexture(this.gl.TEXTURE0);
    this.gl.bindTexture(this.gl.TEXTURE_2D, texture);
    this.gl.uniform1i(this.locations.texture, 0);
    this.gl.uniform1f(this.locations.opacity, opacity);

    // Enable blending
    this.gl.enable(this.gl.BLEND);
    this.gl.blendFunc(this.gl.SRC_ALPHA, this.gl.ONE_MINUS_SRC_ALPHA);

    // Draw
    this.gl.drawArrays(this.gl.TRIANGLE_STRIP, 0, 4);

    // Cleanup
    this.gl.deleteTexture(texture);
  }

  updateViewport(viewport) {
    // Sync with OpenSeadragon viewport if needed
    // For simple overlays, canvas resizes automatically
  }

  destroy() {
    if (this.gl) {
      this.gl.deleteProgram(this.program);
      this.gl.deleteBuffer(this.positionBuffer);
      this.gl.deleteBuffer(this.texCoordBuffer);
    }
    super.destroy();
  }
}

export { WebGLLayer };
```

**4. Canvas Layer (for annotations):**
```javascript
// layers/CanvasLayer.js

import { Layer } from './Layer.js';

/**
 * CanvasLayer - Canvas 2D rendering layer
 *
 * Used for annotations, drawings, and vector graphics.
 */
class CanvasLayer extends Layer {
  constructor() {
    super();

    // Create canvas
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'canvas-layer';
    this.canvas.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: auto;
    `;

    this.element = this.canvas;

    // Get 2D context
    this.ctx = this.canvas.getContext('2d');

    // Annotations storage
    this.annotations = [];
  }

  /**
   * Add annotation
   * @param {Object} annotation - Annotation data (GeoJSON format)
   */
  addAnnotation(annotation) {
    this.annotations.push(annotation);
    this.render();
  }

  /**
   * Remove annotation
   * @param {string} id - Annotation ID
   */
  removeAnnotation(id) {
    this.annotations = this.annotations.filter(a => a.id !== id);
    this.render();
  }

  /**
   * Clear all annotations
   */
  clearAnnotations() {
    this.annotations = [];
    this.render();
  }

  /**
   * Render all annotations
   */
  render() {
    // Clear canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Draw each annotation
    for (const annotation of this.annotations) {
      this._drawAnnotation(annotation);
    }
  }

  _drawAnnotation(annotation) {
    const { geometry, properties } = annotation;

    // Set style
    this.ctx.strokeStyle = properties.color || '#FF0000';
    this.ctx.lineWidth = properties.lineWidth || 2;
    this.ctx.fillStyle = properties.fillColor || 'rgba(255, 0, 0, 0.2)';

    // Draw based on geometry type
    if (geometry.type === 'Polygon') {
      this._drawPolygon(geometry.coordinates[0]);
    } else if (geometry.type === 'LineString') {
      this._drawLineString(geometry.coordinates);
    } else if (geometry.type === 'Point') {
      this._drawPoint(geometry.coordinates);
    }
  }

  _drawPolygon(coordinates) {
    if (coordinates.length === 0) return;

    this.ctx.beginPath();
    this.ctx.moveTo(coordinates[0][0], coordinates[0][1]);

    for (let i = 1; i < coordinates.length; i++) {
      this.ctx.lineTo(coordinates[i][0], coordinates[i][1]);
    }

    this.ctx.closePath();
    this.ctx.fill();
    this.ctx.stroke();
  }

  _drawLineString(coordinates) {
    if (coordinates.length === 0) return;

    this.ctx.beginPath();
    this.ctx.moveTo(coordinates[0][0], coordinates[0][1]);

    for (let i = 1; i < coordinates.length; i++) {
      this.ctx.lineTo(coordinates[i][0], coordinates[i][1]);
    }

    this.ctx.stroke();
  }

  _drawPoint(coordinates) {
    this.ctx.beginPath();
    this.ctx.arc(coordinates[0], coordinates[1], 5, 0, 2 * Math.PI);
    this.ctx.fill();
    this.ctx.stroke();
  }

  updateViewport(viewport) {
    // Resize canvas if needed
    const rect = this.canvas.getBoundingClientRect();
    if (this.canvas.width !== rect.width || this.canvas.height !== rect.height) {
      this.canvas.width = rect.width;
      this.canvas.height = rect.height;
      this.render();
    }
  }

  destroy() {
    this.annotations = [];
    super.destroy();
  }
}

export { CanvasLayer };
```

---

## Performance Optimizations

### 1. WebGL for Heavy Rendering

**Why:** Canvas 2D can block main thread for complex overlays. WebGL uses GPU acceleration.

**When to use:**
- ✅ Confidence maps (heatmaps with gradient)
- ✅ Large number of geometric shapes (>1000 polygons)
- ✅ Real-time animations
- ❌ Simple annotations (<100 shapes) - use Canvas 2D

**Performance Gain:**
- Canvas 2D: ~30fps for complex heatmap
- WebGL: 60fps easily maintained

### 2. Web Workers for Heavy Computation

**Use Cases:**
- Parse large GeoJSON annotation files
- Compute confidence map statistics
- Image processing (brightness/contrast adjustments)

**Example:**
```javascript
// workers/confidenceMapWorker.js
self.addEventListener('message', (e) => {
  const { data, type } = e.data;

  if (type === 'parse') {
    // Parse confidence map data
    const parsed = parseConfidenceData(data);
    self.postMessage({ type: 'parsed', data: parsed });
  }
});

// Main thread
const worker = new Worker('./workers/confidenceMapWorker.js');
worker.postMessage({ type: 'parse', data: rawData });
worker.addEventListener('message', (e) => {
  if (e.data.type === 'parsed') {
    renderConfidenceMap(e.data.data);
  }
});
```

### 3. Request Debouncing

**Why:** Avoid overwhelming backend with rapid requests during pan/zoom.

**Implementation:**
```javascript
// utils/debounce.js
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Usage in viewer
const debouncedSave = debounce((annotation) => {
  apiService.saveAnnotation(annotation);
}, 1000);  // Save 1s after last change

viewer.on('annotationChange', (annotation) => {
  debouncedSave(annotation);  // Debounced save
});
```

### 4. Lazy Loading

**UI Components:**
```javascript
// Load heavy components only when needed
async function showAnnotationTools() {
  // Lazy import (Vite supports this)
  const { AnnotationToolbar } = await import('./components/AnnotationToolbar.js');

  const toolbar = new AnnotationToolbar();
  container.appendChild(toolbar.element);
}
```

**Slide Metadata:**
```javascript
// Load metadata on demand, not upfront
async function onSlideSelect(slideId) {
  // Show viewer immediately (skeleton UI)
  showViewer(slideId);

  // Load metadata in background
  const metadata = await apiService.getSlideMetadata(slideId);
  updateMetadataPanel(metadata);

  // Load predictions in background
  const predictions = await apiService.getPredictions(slideId);
  updatePredictionPanel(predictions);
}
```

### 5. Memory Management

**Destroy Unused Instances:**
```javascript
class ViewerInstance {
  destroy() {
    // Remove event listeners
    this._osdViewer.removeAllHandlers();

    // Clear references
    this._osdViewer.destroy();
    this._osdViewer = null;
    this.slideMetadata = null;
    this.annotations = null;

    // Force garbage collection hint
    if (window.gc) {
      window.gc();
    }
  }
}
```

**Limit Cache Size:**
```javascript
class ApiService {
  _setCache(key, data) {
    this._cache.set(key, { data, timestamp: Date.now() });

    // Limit cache size
    if (this._cache.size > 100) {
      const oldestKey = this._getOldestCacheKey();
      this._cache.delete(oldestKey);
    }
  }
}
```

### 6. Virtual Scrolling (Future)

For large annotation lists (>1000 items):
```javascript
// Only render visible items + buffer
class VirtualList {
  render() {
    const visibleStart = Math.floor(this.scrollTop / this.itemHeight);
    const visibleEnd = Math.ceil((this.scrollTop + this.containerHeight) / this.itemHeight);

    // Render only visible + 10 buffer
    for (let i = visibleStart - 10; i < visibleEnd + 10; i++) {
      if (i >= 0 && i < this.items.length) {
        this.renderItem(this.items[i]);
      }
    }
  }
}
```

---

## Implementation Roadmap

### Week 1-2: Foundation

**Milestone:** Architectural foundation without breaking existing code.

**Tasks:**
- [ ] Create `StateStore` class
- [ ] Create `LayerManager`, `WebGLLayer`, `CanvasLayer` classes
- [ ] Create UI component library (Button, Badge, Card, Modal)
- [ ] Add AI event types to `Constants.js`
- [ ] Write unit tests for new modules (>80% coverage)
- [ ] Update `ApiService` with AI endpoint stubs

**Deliverables:**
- Fully tested new modules
- Documentation for new APIs
- No regressions in existing features

**Acceptance Criteria:**
- All existing tests pass
- New modules have >80% test coverage
- Performance benchmarks stable (no degradation)

---

### Week 3: Tag Display

**Milestone:** Pathologists can see and edit slide tags.

**Tasks:**
- [ ] Create `TagPanel` component
- [ ] Design tag chip UI (CSS)
- [ ] Integrate with backend (`GET /api/slides/{id}/tags`)
- [ ] Implement tag editing (inline edit)
- [ ] Save changes to backend (`PUT /api/slides/{id}/tags`)
- [ ] Connect to `StateStore`
- [ ] Add to Viewer page

**Deliverables:**
- Functional tag display
- Tag editing workflow
- Backend integration
- User documentation

**Acceptance Criteria:**
- Tags load within 200ms
- Editing is intuitive (click to edit)
- Changes persist to backend
- UI matches medical-grade design standards

---

### Week 4-5: Feedback Interface

**Milestone:** Pathologists can validate AI predictions.

**Tasks:**
- [ ] Create `FeedbackPanel` component
- [ ] Implement validation buttons (Accept/Reject/Correct)
- [ ] Connect to `StateStore` (predictions state)
- [ ] Backend integration (`POST /api/predictions/{id}/feedback`)
- [ ] Add confirmation dialogs for destructive actions
- [ ] Implement "Correct" mode (enter annotation mode)
- [ ] Add keyboard shortcuts (A = accept, R = reject, C = correct)
- [ ] Add to Viewer page

**Deliverables:**
- Functional feedback workflow
- Backend integration
- User documentation
- Keyboard shortcut guide

**Acceptance Criteria:**
- Feedback workflow is intuitive
- Backend receives feedback within 500ms
- "Correct" mode seamlessly transitions to annotation
- Keyboard shortcuts work reliably

---

### Week 6-7: Confidence Map Overlay

**Milestone:** AI confidence visually overlaid on slide.

**Tasks:**
- [ ] Create `ConfidenceMapLayer` (extends `WebGLLayer`)
- [ ] Implement heatmap shader (red/yellow/green gradient)
- [ ] Backend integration (`GET /api/predictions/{id}/confidence-map`)
- [ ] Parse backend data format (PNG tiles or GeoJSON)
- [ ] Add toggle button (show/hide overlay)
- [ ] Adjust opacity control (slider)
- [ ] Performance testing (maintain 60fps)
- [ ] Add to Viewer page

**Deliverables:**
- WebGL confidence map overlay
- Toggle controls
- Performance report (60fps verified)
- User documentation

**Acceptance Criteria:**
- Overlay renders at 60fps
- Toggle works instantly (<100ms)
- Opacity control is smooth
- No visual artifacts (tearing, flickering)

---

### Week 8-10: Annotation System

**Milestone:** Pathologists can draw and save annotations.

**Tasks:**
- [ ] Create `AnnotationLayer` (extends `CanvasLayer`)
- [ ] Implement drawing tools (Rectangle, Polygon, Freehand)
- [ ] Tool selector UI (toolbar)
- [ ] Coordinate tracking and conversion (OSD ↔ absolute pixels)
- [ ] Annotation CRUD in `StateStore`
- [ ] Backend integration (`POST /api/slides/{id}/annotations`)
- [ ] Auto-save with debouncing (1s delay)
- [ ] Undo/Redo support
- [ ] GeoJSON import/export
- [ ] Add to Viewer page

**Deliverables:**
- Functional annotation tools
- Annotation persistence
- Undo/Redo
- User documentation

**Acceptance Criteria:**
- Drawing tools are precise (pixel-perfect)
- Coordinates are accurate at all zoom levels
- Auto-save works reliably
- Undo/Redo doesn't lose data
- GeoJSON format is valid

---

### Week 11-12: Integration & Polish

**Milestone:** All features integrated, polished, and ready for production.

**Tasks:**
- [ ] Integration testing (all features together)
- [ ] Performance profiling and optimization
- [ ] UX polish (animations, transitions, micro-interactions)
- [ ] Accessibility audit (keyboard navigation, screen readers)
- [ ] User documentation updates
- [ ] Deployment preparation
- [ ] Load testing (multiple users, large slides)
- [ ] Security audit

**Deliverables:**
- End-to-end tests passing
- Performance report (60fps, <500MB memory)
- Updated user manual
- Production deployment guide
- Security audit report

**Acceptance Criteria:**
- All features work together seamlessly
- Performance meets targets (60fps, <500MB)
- No regressions in existing features
- User documentation is complete
- Ready for production deployment

---

## Testing Strategy

### Unit Tests

**Tools:** Vitest (Vite's test runner)

**Coverage Targets:**
- `StateStore`: 100% (critical infrastructure)
- `LayerManager`, `WebGLLayer`, `CanvasLayer`: >90%
- UI components: >80%
- Utilities (coordinates.js): 100%

**Example:**
```javascript
// __tests__/StateStore.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import { StateStore } from '../core/StateStore.js';

describe('StateStore', () => {
  let store;

  beforeEach(() => {
    store = new StateStore();
    store.clear();
  });

  it('should get state by path', () => {
    store.set('ui.currentPage', 'viewer');
    expect(store.get('ui.currentPage')).toBe('viewer');
  });

  it('should notify listeners on state change', () => {
    let notified = false;
    store.subscribe('predictions', () => { notified = true; });
    store.set('predictions.slide123', { id: 'pred1' });
    expect(notified).toBe(true);
  });

  it('should support undo/redo', () => {
    store.set('ui.currentPage', 'home');
    store.set('ui.currentPage', 'viewer');
    store.undo();
    expect(store.get('ui.currentPage')).toBe('home');
    store.redo();
    expect(store.get('ui.currentPage')).toBe('viewer');
  });
});
```

### Integration Tests

**Tools:** Playwright (end-to-end testing)

**Scenarios:**
- Complete feedback workflow (load slide → view prediction → accept → verify backend)
- Annotation workflow (draw → save → reload → verify persisted)
- Multi-layer rendering (base + confidence + annotations)

**Example:**
```javascript
// e2e/feedback-workflow.spec.js
import { test, expect } from '@playwright/test';

test('pathologist can accept AI prediction', async ({ page }) => {
  // Navigate to viewer
  await page.goto('http://localhost:5173');
  await page.click('text=Sample Slide');

  // Wait for viewer to load
  await page.waitForSelector('.viewer', { timeout: 5000 });

  // Wait for prediction to load
  await page.waitForSelector('.feedback-panel', { timeout: 3000 });

  // Click accept button
  await page.click('button:has-text("Accept")');

  // Verify feedback sent to backend
  const response = await page.waitForResponse(
    (res) => res.url().includes('/api/predictions/') && res.url().includes('/feedback')
  );
  expect(response.status()).toBe(200);

  // Verify UI updated
  await expect(page.locator('.feedback-status')).toHaveText('Accepted');
});
```

### Performance Tests

**Tools:** Chrome DevTools, Lighthouse

**Metrics:**
- Frame rate (target: 60fps)
- Memory usage (target: <500MB)
- Time to interactive (target: <2s)
- Tile load time (target: <100ms)

**Benchmarks:**
```javascript
// performance/benchmark.js
async function benchmarkConfidenceMapRendering() {
  const layer = new ConfidenceMapLayer();
  const data = generateMockConfidenceData(1000, 1000);

  performance.mark('render-start');

  for (let i = 0; i < 60; i++) {  // 60 frames
    layer.renderConfidenceMap(data);
  }

  performance.mark('render-end');
  performance.measure('render-60-frames', 'render-start', 'render-end');

  const measure = performance.getEntriesByName('render-60-frames')[0];
  const fps = 60 / (measure.duration / 1000);

  console.log(`Average FPS: ${fps.toFixed(2)}`);
  expect(fps).toBeGreaterThan(55);  // Allow 5fps margin
}
```

---

## Migration Guide

### For Developers

**Migrating Existing Components to New Architecture:**

**Before (old approach):**
```javascript
// components/OldComponent.js
let appState = {};  // Local state

function updateSlide(slideId) {
  appState.currentSlide = slideId;
  // Update UI manually
  document.getElementById('slide-name').textContent = slideId;
}
```

**After (new approach):**
```javascript
// components/NewComponent.js
import { stateStore } from '../core/StateStore.js';

class NewComponent {
  constructor() {
    // Subscribe to state
    stateStore.subscribe('ui.currentSlide', (slideId) => {
      this.render(slideId);
    });
  }

  updateSlide(slideId) {
    // Update state (triggers subscribers automatically)
    stateStore.set('ui.currentSlide', slideId);
  }

  render(slideId) {
    document.getElementById('slide-name').textContent = slideId;
  }
}
```

**Migration Checklist:**
- [ ] Identify local state variables
- [ ] Map to StateStore paths
- [ ] Replace direct DOM updates with subscriptions
- [ ] Test thoroughly (unit + integration)
- [ ] Update documentation

---

### For End Users

**No breaking changes in UI workflow.**

**New Features:**
1. **Tag Display:** Tags now visible above viewer
2. **Feedback Interface:** New buttons for AI validation
3. **Confidence Map:** Toggle overlay with new button
4. **Annotations:** New toolbar for drawing tools

**Training Materials:**
- Updated user manual (`docs/Manuel/`)
- Video tutorials (future)
- In-app tooltips

---

## Conclusion

This refactoring plan prepares Varuna's frontend for V3 AI features while maintaining:

- ✅ **Vanilla JS** (no framework bloat)
- ✅ **Clean Architecture** (modular, testable, maintainable)
- ✅ **Performance** (60fps, <500MB memory)
- ✅ **Medical-Grade UX** (professional, reliable, distraction-free)

**Next Steps:**
1. Review this document with team
2. Prioritize features (if needed)
3. Assign developers to tasks
4. Begin Week 1-2 foundation work

**Questions/Feedback:**
Contact: [Development Team]

---

**Document Status:** DRAFT
**Last Updated:** 2025-12-31
**Version:** 1.0
**Authors:** Frontend Tech Lead (Claude Agent)

---

## Appendix A: File Checklist

**New Files to Create:**

```
frontend/src/
├── core/
│   └── StateStore.js                    🆕 (Week 1)
│
├── layers/                              🆕 (Week 1)
│   ├── LayerManager.js
│   ├── Layer.js
│   ├── TileLayer.js
│   ├── WebGLLayer.js
│   ├── CanvasLayer.js
│   ├── ConfidenceMapLayer.js            🆕 (Week 6)
│   └── AnnotationLayer.js               🆕 (Week 8)
│
├── components/
│   ├── TagPanel.js                      🆕 (Week 3)
│   ├── FeedbackPanel.js                 🆕 (Week 4)
│   └── AnnotationToolbar.js             🆕 (Week 8)
│
├── ui/                                  🆕 (Week 1)
│   ├── components/
│   │   ├── Button.js
│   │   ├── Badge.js
│   │   ├── Card.js
│   │   ├── Modal.js
│   │   ├── Dropdown.js
│   │   └── Tooltip.js
│   └── styles/
│       ├── variables.css
│       ├── components.css
│       └── utilities.css
│
├── services/
│   ├── PredictionService.js             🆕 (Week 4)
│   ├── AnnotationService.js             🆕 (Week 8)
│   └── WebSocketService.js              🆕 (Future)
│
├── tools/                               🆕 (Week 8)
│   ├── DrawingTool.js
│   ├── RectangleTool.js
│   ├── PolygonTool.js
│   └── FreehandTool.js
│
├── utils/
│   ├── debounce.js                      🆕 (Week 1)
│   └── validation.js                    🆕 (Week 1)
│
└── workers/                             🆕 (Week 6)
    └── confidenceMapWorker.js
```

**Total:** ~30 new files, ~5 files to refactor

---

## Appendix B: API Endpoints (Backend Requirements)

**New endpoints needed for V3:**

```
# Tags
GET    /api/slides/{id}/tags
PUT    /api/slides/{id}/tags

# Predictions
GET    /api/predictions/{slide_id}
POST   /api/predictions/{id}/feedback
GET    /api/predictions/{id}/confidence-map

# Annotations
GET    /api/slides/{id}/annotations
POST   /api/slides/{id}/annotations
PUT    /api/annotations/{id}
DELETE /api/annotations/{id}

# WebSocket (future)
WS     /ws/collaborate/{session_id}
```

**Coordinate with Backend Tech Lead** for implementation timeline.

---

## Appendix C: Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Frame Rate | 60 fps | Chrome DevTools Performance |
| Memory Usage | < 500 MB | Task Manager |
| Time to Interactive | < 2s | Lighthouse |
| Tile Load Time | < 100ms | Network tab |
| State Update | < 16ms | Performance API |
| WebGL Render | < 16ms | requestAnimationFrame |

**Monitoring:** Set up performance budgets in CI/CD pipeline.

---

**END OF DOCUMENT**
