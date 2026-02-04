# Design Patterns Implémentés

**Dernière mise à jour:** 2025-12-30

---

## 1. Singleton Pattern

### EventBus (`core/EventBus.js`)
```javascript
let instance = null;

class EventBus {
    constructor() {
        if (instance) return instance;
        this._listeners = new Map();
        instance = this;
    }

    static getInstance() {
        if (!instance) instance = new EventBus();
        return instance;
    }
}

export const eventBus = EventBus.getInstance();
```

**Usage:**
```javascript
import { eventBus } from './core/EventBus.js';
eventBus.on('event', callback);
eventBus.emit('event', data);
```

### ViewerManager (`viewers/ViewerManager.js`)
```javascript
let instance = null;

class ViewerManager {
    static getInstance() {
        if (!instance) instance = new ViewerManager();
        return instance;
    }
}

export const viewerManager = ViewerManager.getInstance();
```

### ApiService (`services/ApiService.js`)
Même pattern - instance unique pour cache et déduplication requêtes.

---

## 2. Factory Pattern

### ViewerFactory (`viewers/ViewerFactory.js`)
```javascript
class ViewerFactory {
    static create(id, container, options = {}) {
        const mergedOptions = { ...DEFAULTS, ...options };
        return new ViewerInstance(id, container, mergedOptions);
    }

    static createFromPreset(presetName, id, container) {
        return ViewerFactory.create(id, container, {
            preset: presetName
        });
    }

    static createComparisonPair(container1, container2) {
        return {
            viewer1: ViewerFactory.create(null, container1),
            viewer2: ViewerFactory.create(null, container2)
        };
    }
}
```

**Usage:**
```javascript
const viewer = ViewerFactory.create('v1', container, { showNavigator: true });
const { viewer1, viewer2 } = ViewerFactory.createComparisonPair(c1, c2);
```

---

## 3. Observer Pattern (Pub/Sub)

### EventBus (`core/EventBus.js`)
```javascript
class EventBus {
    on(event, callback) {
        if (!this._listeners.has(event)) {
            this._listeners.set(event, new Set());
        }
        this._listeners.get(event).add(callback);
        return () => this.off(event, callback); // Unsubscribe function
    }

    emit(event, data) {
        const listeners = this._listeners.get(event);
        if (listeners) {
            listeners.forEach(cb => cb(data));
        }
    }
}
```

**Usage:**
```javascript
// Subscribe
const unsubscribe = eventBus.on(Events.VIEWER_PAN, (data) => {
    console.log('Pan:', data.viewport);
});

// Publish
eventBus.emit(Events.VIEWER_PAN, { viewerId: 'v1', viewport: {...} });

// Unsubscribe
unsubscribe();
```

---

## 4. State Pattern

### ViewerState (`viewers/ViewerState.js`)
```javascript
const validTransitions = new Map([
    [ViewerStates.IDLE, new Set([ViewerStates.LOADING, ViewerStates.DESTROYING])],
    [ViewerStates.LOADING, new Set([ViewerStates.READY, ViewerStates.ERROR])],
    [ViewerStates.READY, new Set([ViewerStates.LOADING, ViewerStates.DESTROYING])],
    [ViewerStates.ERROR, new Set([ViewerStates.LOADING, ViewerStates.IDLE])],
]);

class ViewerState {
    transitionTo(newState, options = {}) {
        if (!this.canTransitionTo(newState)) {
            throw new Error(`Invalid transition: ${this.current} -> ${newState}`);
        }
        this._previousState = this._currentState;
        this._currentState = newState;
        // Notify callbacks...
    }

    canTransitionTo(targetState) {
        return validTransitions.get(this._currentState)?.has(targetState);
    }
}
```

**Usage:**
```javascript
const state = new ViewerState();
state.onTransition((old, new) => console.log(`${old} -> ${new}`));
state.transitionTo(ViewerStates.LOADING);
// state.is(ViewerStates.LOADING) === true
```

---

## 5. Mediator Pattern

### SyncController (`viewers/SyncController.js`)
```javascript
class SyncController {
    constructor() {
        this._viewers = new Map();
        this.syncedViewerIds = new Set();
        this._setupEventListeners();
    }

    registerViewer(viewer) {
        this._viewers.set(viewer.id, viewer);
    }

    enable(viewerIds = null) {
        // Register viewers for sync
        this.enabled = true;
    }

    _handleViewportChange({ viewerId, viewport }) {
        // Normalize viewport from source
        const normalized = this._normalizeViewport(viewport);

        // Broadcast to all OTHER synced viewers
        this.syncedViewerIds.forEach(targetId => {
            if (targetId === viewerId) return;
            const target = this._viewers.get(targetId);
            target.setViewport(normalized);
        });
    }
}
```

**Usage:**
```javascript
const sync = new SyncController();
sync.registerViewer(viewer1);
sync.registerViewer(viewer2);
sync.enable(); // Maintenant viewer1 et viewer2 sont synchronisés
```

---

## 6. Facade Pattern

### ViewerManager (`viewers/ViewerManager.js`)
Fournit une interface simplifiée pour gérer les viewers:

```javascript
class ViewerManager {
    // CRUD simplifié
    createViewer(id, container, options)
    destroyViewer(viewerId)
    getViewer(viewerId)
    getAllViewers()

    // Layout simplifié
    setLayout(columns, rows)
    applyLayoutPreset('SIDE_BY_SIDE')

    // Sync simplifié
    enableSync()
    disableSync()
    toggleSync()
}
```

**Usage:**
```javascript
// Toute la complexité est cachée derrière l'API simple
const v1 = viewerManager.createViewer('v1', container1);
const v2 = viewerManager.createViewer('v2', container2);
viewerManager.setLayout(2, 1);
await viewerManager.enableSync();
```

---

## 7. Module Pattern (ES6)

### Encapsulation via exports
```javascript
// Constants.js - Export sélectif
export const ViewerStates = Object.freeze({ ... });
export const Events = Object.freeze({ ... });
// Variables privées restent dans le module

// index.js - Barrel exports
export { eventBus } from './EventBus.js';
export { ViewerStates, Events } from './Constants.js';
```

**Usage:**
```javascript
// Import propre depuis le barrel
import { eventBus, Events } from './core';
```

---

## 8. Composite Pattern (UI)

### Structure des composants
```
CompareLayout
├── ViewerPanel (slot 0)
│   ├── header
│   ├── ViewerInstance (OpenSeadragon)
│   └── actions
├── ViewerPanel (slot 1)
│   └── ...
└── SyncControls
    ├── LayoutSelector
    └── SyncButton
```

Chaque composant peut être traité individuellement ou comme partie du layout.

---

## Anti-Patterns Évités

### ❌ God Object
- Au lieu d'un main.js monolithique, responsabilités distribuées

### ❌ Spaghetti Events
- Events nommés et documentés dans Constants.js
- Namespacing: `viewer:pan`, `sync:enabled`, etc.

### ❌ Tight Coupling
- Communication via EventBus, pas d'appels directs entre composants
- Injection de dépendances via constructeur

### ❌ Magic Strings
- Toutes les constantes dans Constants.js
- `Events.VIEWER_PAN` au lieu de `'viewer:pan'`
