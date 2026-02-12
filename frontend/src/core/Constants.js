
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
 * Event names used by EventBus
 * Namespaced to avoid collisions
 * @readonly
 * @enum {string}
 */
export const Events = Object.freeze({
    // Viewer lifecycle events
    VIEWER_CREATED: 'viewer:created',
    VIEWER_DESTROYED: 'viewer:destroyed',
    VIEWER_STATE_CHANGE: 'viewer:stateChange',

    // Slide events
    SLIDE_LOADING: 'slide:loading',
    SLIDE_LOADED: 'slide:loaded',
    SLIDE_UNLOADED: 'slide:unloaded',
    SLIDE_ERROR: 'slide:error',

    // Navigation events (for sync)
    VIEWER_PAN: 'viewer:pan',
    VIEWER_ZOOM: 'viewer:zoom',
    VIEWER_VIEWPORT_CHANGE: 'viewer:viewportChange',

    // Sync events
    SYNC_ENABLED: 'sync:enabled',
    SYNC_DISABLED: 'sync:disabled',
    SYNC_VIEWERS_CHANGED: 'sync:viewersChanged',

    // Layout events
    LAYOUT_CHANGED: 'layout:changed',
    VIEWER_ADDED: 'layout:viewerAdded',
    VIEWER_REMOVED: 'layout:viewerRemoved',

    // UI events
    SLIDE_SELECTED: 'ui:slideSelected',
    FOLDER_CHANGED: 'ui:folderChanged',
    PAGE_CHANGED: 'ui:pageChanged',

    // ML events
    ML_PREDICTION_START: 'ml:predictionStart',
    ML_PREDICTION_COMPLETE: 'ml:predictionComplete',
    ML_PREDICTION_ERROR: 'ml:predictionError',
    ML_HEATMAP_LOADING: 'ml:heatmapLoading',
    ML_HEATMAP_READY: 'ml:heatmapReady',
    ML_HEATMAP_ERROR: 'ml:heatmapError',
    ML_HEATMAP_TOGGLE: 'ml:heatmapToggle',
    ML_HEATMAP_OPACITY_CHANGE: 'ml:heatmapOpacityChange',
    ML_MODEL_LOADED: 'ml:modelLoaded',
    ML_MODEL_UNLOADED: 'ml:modelUnloaded',

    // Annotation events
    ANNOTATION_CREATED: 'annotation:created',
    ANNOTATION_UPDATED: 'annotation:updated',
    ANNOTATION_DELETED: 'annotation:deleted',
    ANNOTATION_SELECTED: 'annotation:selected',
    ANNOTATIONS_LOADED: 'annotation:loaded',
    ANNOTATION_STATS_UPDATED: 'annotation:statsUpdated',

    // Drawing tool events
    TOOL_CHANGED: 'tool:changed',
    DRAWING_START: 'drawing:start',
    DRAWING_END: 'drawing:end',

    // Layer events
    LAYER_VISIBILITY_CHANGED: 'layer:visibilityChanged',
    LAYER_OPACITY_CHANGED: 'layer:opacityChanged',

    // Detection events
    DETECTION_START: 'detection:start',
    DETECTION_COMPLETE: 'detection:complete',
    DETECTION_ERROR: 'detection:error',
    DETECTION_PREVIEW: 'detection:preview',
    DETECTION_CONFIRM: 'detection:confirm',
    DETECTION_REJECT: 'detection:reject',

    // Auth events (Phase 3)
    AUTH_LOGIN: 'auth:login',
    AUTH_LOGOUT: 'auth:logout',
    AUTH_TOKEN_REFRESHED: 'auth:tokenRefreshed',
    AUTH_ERROR: 'auth:error',
    AUTH_ROLE_CHANGED: 'auth:roleChanged',

    // Quality metrics events (Phase 4)
    QUALITY_LOADING: 'quality:loading',
    QUALITY_READY: 'quality:ready',
    QUALITY_ERROR: 'quality:error',
    QUALITY_DISAGREEMENT_TOGGLE: 'quality:disagreementToggle',
});

/**
 * API endpoints configuration
 * @readonly
 */
export const API = Object.freeze({
    BASE_URL: 'http://localhost:8000',
    ENDPOINTS: {
        HEALTH: '/api/health',
        SLIDES: '/api/slides',
        BROWSE: '/api/slides/browse',
        SLIDE_INFO: (id) => `/api/slides/${id}/info`,
        SLIDE_OVERVIEW: (id) => `/api/slides/${id}/overview`,
        TILE: (id, level, x, y, w, h) => `/api/slides/${id}/tile/${level}/${x}/${y}/${w}/${h}`,
        SLIDE_BY_NAME: (name) => `/api/slides/by-name/${encodeURIComponent(name)}`,
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
    /** Sync is disabled by default per user requirement */
    ENABLED_BY_DEFAULT: false,

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
