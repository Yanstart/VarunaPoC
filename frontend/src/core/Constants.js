
/**
 * Constants - Global constants and configuration
 *
 * Centralized configuration for the VarunaPoC application.
 * Follows the Module pattern for encapsulation.
 *
 * @module core/Constants
 */

/**
 * Viewer state enumeration
 * Used by ViewerState pattern to manage viewer lifecycle
 * @readonly
 * @enum {string}
 */
export const ViewerStates = Object.freeze({
    /** Viewer created but no slide loaded */
    IDLE: 'idle',
    /** Slide is being loaded */
    LOADING: 'loading',
    /** Slide loaded and ready for interaction */
    READY: 'ready',
    /** Error occurred during loading or operation */
    ERROR: 'error',
    /** Viewer is being destroyed */
    DESTROYING: 'destroying',
});

/**
 * Event names used by EventBus.
 *
 * Each event documents its expected payload shape. Components that emit or
 * subscribe to an event MUST conform to the documented payload to prevent
 * silent runtime mismatches.
 *
 * @readonly
 * @enum {string}
 */
export const Events = Object.freeze({
    // -- Viewer lifecycle --
    /** @payload {{ viewerId: string }} */
    VIEWER_CREATED: 'viewer:created',
    /** @payload {{ viewerId: string }} */
    VIEWER_DESTROYED: 'viewer:destroyed',
    /** @payload {{ viewerId: string, state: ViewerStates }} */
    VIEWER_STATE_CHANGE: 'viewer:stateChange',

    // -- Slide --
    /** @payload {{ viewerId: string, slideId: string }} */
    SLIDE_LOADING: 'slide:loading',
    /** @payload {{ viewerId: string, slideId: string }} */
    SLIDE_LOADED: 'slide:loaded',
    /** @payload {{ viewerId: string }} */
    SLIDE_UNLOADED: 'slide:unloaded',
    /** @payload {{ viewerId: string, error: string }} */
    SLIDE_ERROR: 'slide:error',

    // -- Navigation (sync) --
    /** @payload {{ viewerId: string, center: {x,y} }} */
    VIEWER_PAN: 'viewer:pan',
    /** @payload {{ viewerId: string, zoom: number }} */
    VIEWER_ZOOM: 'viewer:zoom',
    /** @payload {{ viewerId: string, bounds: {x,y,width,height} }} */
    VIEWER_VIEWPORT_CHANGE: 'viewer:viewportChange',
    /** @payload {{ level: number }} — keyboard shortcut: jump to zoom preset 1-5 */
    VIEWER_ZOOM_PRESET: 'viewer:zoomPreset',

    // -- Sync --
    /** @payload {{ viewerIds: string[] }} */
    SYNC_ENABLED: 'sync:enabled',
    /** @payload (none) */
    SYNC_DISABLED: 'sync:disabled',
    /** @payload {{ viewerIds: string[] }} */
    SYNC_VIEWERS_CHANGED: 'sync:viewersChanged',

    // -- Layout --
    /** @payload {{ layout: LayoutPresets, viewerCount: number }} */
    LAYOUT_CHANGED: 'layout:changed',
    /** @payload {{ viewerId: string, panelIndex: number }} */
    VIEWER_ADDED: 'layout:viewerAdded',
    /** @payload {{ viewerId: string }} */
    VIEWER_REMOVED: 'layout:viewerRemoved',

    // -- UI --
    /** @payload {{ slideId: string, slideName: string }} */
    SLIDE_SELECTED: 'ui:slideSelected',
    /** @payload {{ path: string }} */
    FOLDER_CHANGED: 'ui:folderChanged',
    /** @payload {{ page: Pages }} */
    PAGE_CHANGED: 'ui:pageChanged',
    /** @payload {{ type: 'error'|'warning'|'success', message: string, duration?: number }} */
    TOAST_SHOW: 'ui:toastShow',
    /** @payload {{ slideId: string, bbox: number[], centroid: number[] }} */
    FOCUS_ZONE_NAVIGATE: 'ui:focusZoneNavigate',
    /** @payload (none) */
    SLIDE_NAV_PREV: 'ui:slideNavPrev',
    /** @payload (none) */
    SLIDE_NAV_NEXT: 'ui:slideNavNext',

    // -- ML --
    /** @payload {{ viewerId: string, slideId: string, modelId: string }} */
    ML_PREDICTION_START: 'ml:predictionStart',
    /** @payload {{ viewerId: string, prediction: string, confidence: number, probabilities: Object }} */
    ML_PREDICTION_COMPLETE: 'ml:predictionComplete',
    /** @payload {{ viewerId: string, error: string }} */
    ML_PREDICTION_ERROR: 'ml:predictionError',
    /** @payload {{ viewerId: string }} */
    ML_HEATMAP_LOADING: 'ml:heatmapLoading',
    /** @payload {{ viewerId: string, imageUrl: string }} */
    ML_HEATMAP_READY: 'ml:heatmapReady',
    /** @payload {{ viewerId: string, error: string }} */
    ML_HEATMAP_ERROR: 'ml:heatmapError',
    /** @payload {{ viewerId: string, visible: boolean }} */
    ML_HEATMAP_TOGGLE: 'ml:heatmapToggle',
    /** @payload {{ viewerId: string, opacity: number }} */
    ML_HEATMAP_OPACITY_CHANGE: 'ml:heatmapOpacityChange',
    /** @payload {{ modelId: string, modelName: string }} */
    ML_MODEL_LOADED: 'ml:modelLoaded',
    /** @payload (none) */
    ML_MODEL_UNLOADED: 'ml:modelUnloaded',
    /** @payload {{ label: string }} */
    ML_WORKER_BUSY: 'ml:workerBusy',
    /** @payload (none) */
    ML_WORKER_FREE: 'ml:workerFree',

    // -- Annotations --
    /** @payload {{ annotation: Object, slideId: string }} */
    ANNOTATION_CREATED: 'annotation:created',
    /** @payload {{ annotation: Object }} */
    ANNOTATION_UPDATED: 'annotation:updated',
    /** @payload {{ annotationId: string }} */
    ANNOTATION_DELETED: 'annotation:deleted',
    /** @payload {{ annotationId: string|null }} */
    ANNOTATION_SELECTED: 'annotation:selected',
    /** @payload {{ slideId: string, annotations: Object[] }} */
    ANNOTATIONS_LOADED: 'annotation:loaded',
    /** @payload {{ slideId: string, count: number }} */
    ANNOTATION_STATS_UPDATED: 'annotation:statsUpdated',
    /** @payload {{ annotation: Object }} */
    ANNOTATION_VALIDATED: 'annotation:validated',
    /** @payload {{ annotation: Object }} */
    ANNOTATION_REJECTED: 'annotation:rejected',
    /** @payload {{ annotation: Object }} */
    ANNOTATION_NOTES_CHANGED: 'annotation:notesChanged',
    /** @payload {{ action: Object }} */
    UNDO: 'history:undo',
    /** @payload {{ action: Object }} */
    REDO: 'history:redo',

    // -- Drawing tools --
    /** @payload {{ tool: string }} */
    TOOL_CHANGED: 'tool:changed',
    /** @payload {{ enabled: boolean }} */
    QUIZ_MODE_TOGGLE: 'quiz:toggle',
    /** @payload {{ tool: string }} */
    DRAWING_START: 'drawing:start',
    /** @payload {{ tool: string }} */
    DRAWING_END: 'drawing:end',

    // -- Layers --
    /** @payload {{ layerId: string, visible: boolean }} */
    LAYER_VISIBILITY_CHANGED: 'layer:visibilityChanged',
    /** @payload {{ layerId: string, opacity: number }} */
    LAYER_OPACITY_CHANGED: 'layer:opacityChanged',

    // -- Sync mode --
    /** @payload {{ mode: SyncConfig.MODES }} */
    SYNC_MODE_CHANGED: 'sync:modeChanged',

    // -- Detection --
    /** @payload {{ viewerId: string }} */
    DETECTION_START: 'detection:start',
    /** @payload {{ viewerId: string, numRegions: number, regions: Object[] }} */
    DETECTION_COMPLETE: 'detection:complete',
    /** @payload {{ viewerId: string, error: string }} */
    DETECTION_ERROR: 'detection:error',
    /** @payload {{ viewerId: string, features: Object[] }} */
    DETECTION_PREVIEW: 'detection:preview',
    /** @payload {{ viewerId: string, regionIndex: number }} */
    DETECTION_CONFIRM: 'detection:confirm',
    /** @payload {{ viewerId: string, regionIndex: number }} */
    DETECTION_REJECT: 'detection:reject',
    /** @payload {{ regionIndex: number }} */
    DETECTION_PREVIEW_CLICKED: 'detection:previewClicked',
    /** @payload {{ regionIndex: number }} */
    DETECTION_ITEM_CLICKED: 'detection:itemClicked',
    /** @payload {{ regionIndex: number|null, visible?: boolean }} */
    DETECTION_HIGHLIGHT: 'detection:highlight',
    /** @payload {{ regionIndex: number, bounds: {x,y,width,height} }} */
    DETECTION_NAVIGATE: 'detection:navigate',
    /** @payload {} */
    DETECTION_VALIDATE_CURRENT: 'detection:validateCurrent',
    /** @payload {} */
    DETECTION_REJECT_CURRENT: 'detection:rejectCurrent',
    /** @payload {} */
    DETECTION_NEXT: 'detection:next',

    // -- Cell counting (Wave 4) --
    /** @payload {{ viewerId: string }} */
    CELL_COUNTING_START: 'cellCounting:start',
    /** @payload {{ viewerId: string, counts: Object }} */
    CELL_COUNTING_COMPLETE: 'cellCounting:complete',
    /** @payload {{ viewerId: string, error: string }} */
    CELL_COUNTING_ERROR: 'cellCounting:error',
    /** @payload {{ visible: boolean }} */
    CELL_MARKERS_TOGGLE: 'cellCounting:markersToggle',
    /** @payload {{ opacity: number }} */
    CELL_MARKERS_OPACITY: 'cellCounting:markersOpacity',

    // -- ML overlays global toggle (Wave C) --
    /** @payload {{ visible: boolean }} */
    ML_OVERLAYS_TOGGLE: 'ml:overlaysToggle',

    // -- Clustering (Wave 4) --
    /** @payload {{ viewerId: string }} */
    CLUSTERING_START: 'clustering:start',
    /** @payload {{ viewerId: string, clusters: Object[] }} */
    CLUSTERING_COMPLETE: 'clustering:complete',
    /** @payload {{ viewerId: string, error: string }} */
    CLUSTERING_ERROR: 'clustering:error',
    /** @payload {{ viewerId: string, visible: boolean }} */
    CLUSTERING_OVERLAY_TOGGLE: 'clustering:overlayToggle',
    /** @payload {{ viewerId: string, opacity: number }} */
    CLUSTERING_OVERLAY_OPACITY: 'clustering:overlayOpacity',

    // -- Auth (Phase 3) --
    /** @payload {{ user: Object }} */
    AUTH_LOGIN: 'auth:login',
    /** @payload (none) */
    AUTH_LOGOUT: 'auth:logout',
    /** @payload {{ accessToken: string }} */
    AUTH_TOKEN_REFRESHED: 'auth:tokenRefreshed',
    /** @payload {{ error: string }} */
    AUTH_ERROR: 'auth:error',
    /** @payload {{ roles: string[] }} */
    AUTH_ROLE_CHANGED: 'auth:roleChanged',

    // -- I18n (Wave 6) --
    /** @payload {{ locale: string }} */
    LOCALE_CHANGED: 'i18n:localeChanged',

    // -- Case navigation (Wave 3) --
    /** @payload {{ caseId: string }} */
    CASE_SELECTED: 'ui:caseSelected',
    /** @payload {{ slideId: string, caseId: string }} */
    CASE_SLIDE_SWITCH: 'case:slideSwitch',

    // -- Quality metrics (Phase 4) --
    /** @payload {{ slideId: string }} */
    QUALITY_LOADING: 'quality:loading',
    /** @payload {{ slideId: string, metrics: Object }} */
    QUALITY_READY: 'quality:ready',
    /** @payload {{ slideId: string, error: string }} */
    QUALITY_ERROR: 'quality:error',
    /** @payload {{ visible: boolean }} */
    QUALITY_DISAGREEMENT_TOGGLE: 'quality:disagreementToggle',

    // -- Drift monitoring (Wave 4) --
    /** @payload {{ slideId: string }} */
    DRIFT_LOADING: 'drift:loading',
    /** @payload {{ slideId: string, driftData: Object }} */
    DRIFT_READY: 'drift:ready',
    /** @payload {{ slideId: string, error: string }} */
    DRIFT_ERROR: 'drift:error',

    // -- Theme (Wave 6) --
    /** @payload {{ theme: string }} */
    THEME_CHANGED: 'ui:themeChanged',
});

/**
 * API endpoints configuration
 * @readonly
 */
export const API = Object.freeze({
    BASE_URL: 'http://localhost:8000',
    VERSION: 'v1',
    ENDPOINTS: {
        HEALTH: '/api/v1/health',
        SLIDES: '/api/v1/slides',
        BROWSE: '/api/v1/slides/browse',
        SLIDE_INFO: (id) => `/api/v1/slides/${id}/info`,
        SLIDE_OVERVIEW: (id) => `/api/v1/slides/${id}/overview`,
        TILE: (id, level, x, y, w, h) => `/api/v1/slides/${id}/tile/${level}/${x}/${y}/${w}/${h}`,
        SLIDE_BY_NAME: (name) => `/api/v1/slides/by-name/${encodeURIComponent(name)}`,
    },
});

/**
 * OpenSeadragon default configuration
 * @readonly
 */
export const OSD_CONFIG = Object.freeze({
    // Tile settings
    TILE_SIZE: 256,
    TILE_OVERLAP: 0,
    MIN_ZOOM_IMAGE_RATIO: 0.1,
    MAX_ZOOM_PIXEL_RATIO: 10,

    // Animation settings
    ANIMATION_TIME: 0.3,
    BLEND_TIME: 0.1,
    SPRING_STIFFNESS: 10,

    // UI settings
    SHOW_NAVIGATOR: true,
    NAVIGATOR_POSITION: 'BOTTOM_RIGHT',
    NAVIGATOR_SIZE_RATIO: 0.15,
    SHOW_ZOOM_CONTROL: true,
    SHOW_HOME_CONTROL: true,
    SHOW_FULLSCREEN_CONTROL: true,

    // Performance settings
    IMAGE_LOADER_LIMIT: 5,
    MAX_IMAGE_CACHE_COUNT: 200,
    TIMEOUT: 30000,

    // Gesture settings
    GESTURE_SETTINGS_MOUSE: {
        clickToZoom: false,
        dblClickToZoom: true,
        flickEnabled: true,
        pinchToZoom: true,
    },
});

/**
 * Layout presets for multi-viewer configurations
 * @readonly
 */
export const LayoutPresets = Object.freeze({
    SINGLE: { columns: 1, rows: 1, maxViewers: 1 },
    SIDE_BY_SIDE: { columns: 2, rows: 1, maxViewers: 2 },
    STACKED: { columns: 1, rows: 2, maxViewers: 2 },
    GRID_2X2: { columns: 2, rows: 2, maxViewers: 4 },
    GRID_3X2: { columns: 3, rows: 2, maxViewers: 6 },
    GRID_3X3: { columns: 3, rows: 3, maxViewers: 9 },
});

/**
 * Default layout configuration
 * @readonly
 */
export const DEFAULT_LAYOUT = LayoutPresets.SINGLE;

/**
 * Sync mode configuration
 * @readonly
 */
export const SyncConfig = Object.freeze({
    /** Sync is enabled by default for compare mode */
    ENABLED_BY_DEFAULT: true,

    /** Debounce time for sync events (ms) */
    DEBOUNCE_MS: 16, // ~60fps

    /** Modes of synchronization */
    MODES: {
        /** Sync both pan and zoom */
        FULL: 'full',
        /** Sync only pan movements */
        PAN_ONLY: 'panOnly',
        /** Sync only zoom level */
        ZOOM_ONLY: 'zoomOnly',
    },
});

/**
 * Page/Route identifiers
 * @readonly
 * @enum {string}
 */
export const Pages = Object.freeze({
    HOME: 'home',
    VIEWER: 'viewer',
    COMPARE: 'compare',
    LOGIN: 'login',
    CALLBACK: 'callback',
});

/**
 * CSS class names for consistent styling
 * @readonly
 */
export const CSSClasses = Object.freeze({
    // Layout classes
    VIEWER_CONTAINER: 'viewer-container',
    VIEWER_PANEL: 'viewer-panel',
    COMPARE_LAYOUT: 'compare-layout',
    GRID_LAYOUT: 'grid-layout',

    // State classes
    LOADING: 'is-loading',
    READY: 'is-ready',
    ERROR: 'is-error',
    ACTIVE: 'is-active',
    SYNCED: 'is-synced',
    SELECTED: 'is-selected',

    // Component classes
    SLIDE_CARD: 'slide-card',
    FOLDER_ITEM: 'folder-item',
    SYNC_BUTTON: 'sync-button',
    SYNC_ENABLED: 'sync-enabled',
});

/**
 * Local storage keys
 * @readonly
 */
export const StorageKeys = Object.freeze({
    LAST_PATH: 'varuna_lastPath',
    PREFERRED_LAYOUT: 'varuna_preferredLayout',
    SYNC_ENABLED: 'varuna_syncEnabled',
    DEBUG_MODE: 'varuna_debugMode',
    PENDING_SLIDE_NAME: 'varuna_pending_slide',
    THEME: 'varuna_theme',
});

/**
 * Error messages
 * @readonly
 */
export const ErrorMessages = Object.freeze({
    SLIDE_NOT_FOUND: 'Slide not found',
    SLIDE_LOAD_FAILED: 'Failed to load slide',
    VIEWER_NOT_FOUND: 'Viewer not found',
    INVALID_COORDINATES: 'Invalid coordinates',
    API_ERROR: 'API request failed',
    SYNC_ERROR: 'Synchronization error',
});

/**
 * Supported slide formats
 * Reference: docs/Manuel/04-FORMATS_SUPPORTES.md (to be created)
 * @readonly
 */
export const SupportedFormats = Object.freeze({
    MRXS: { extension: '.mrxs', vendor: '3DHistech', name: 'MIRAX' },
    BIF: { extension: '.bif', vendor: 'Roche/Ventana', name: 'Ventana BIF' },
    TIF: { extension: '.tif', vendor: 'Generic', name: 'TIFF/BigTIFF' },
    SVS: { extension: '.svs', vendor: 'Aperio', name: 'ScanScope Virtual Slide' },
    NDPI: { extension: '.ndpi', vendor: 'Hamamatsu', name: 'NanoZoomer' },
    SCN: { extension: '.scn', vendor: 'Leica', name: 'Leica SCN' },
});

// Export all constants as default object for convenience
export default {
    ViewerStates,
    Events,
    API,
    OSD_CONFIG,
    LayoutPresets,
    DEFAULT_LAYOUT,
    SyncConfig,
    Pages,
    CSSClasses,
    StorageKeys,
    ErrorMessages,
    SupportedFormats,
};
