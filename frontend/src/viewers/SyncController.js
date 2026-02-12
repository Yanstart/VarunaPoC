/**
 * SyncController - Mediator Pattern for viewer synchronization
 *
 * Coordinates pan/zoom synchronization between multiple ViewerInstance objects.
 * Handles coordinate normalization for slides of different sizes.
 *
 * @module viewers/SyncController
 *
 * @example
 * const sync = new SyncController();
 * sync.registerViewer(viewer1);
 * sync.registerViewer(viewer2);
 * sync.enable();
 *
 * // Now viewer1 and viewer2 navigation is synchronized
 */

import { eventBus } from '../core/EventBus.js';
import { Events, SyncConfig } from '../core/Constants.js';

/**
 * Debounce utility for high-frequency events
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
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

/**
 * SyncController class - Mediator for viewer synchronization
 */
class SyncController {
    /**
     * Create a new SyncController
     */
    constructor() {
        /**
         * Registered viewers
         * @type {Map<string, import('./ViewerInstance.js').ViewerInstance>}
         * @private
         */
        this._viewers = new Map();

        /**
         * Set of viewer IDs that are synced
         * @type {Set<string>}
         */
        this.syncedViewerIds = new Set();

        /**
         * Whether sync is enabled
         * @type {boolean}
         */
        this.enabled = false;

        /**
         * Sync mode
         * @type {string}
         */
        this.mode = SyncConfig.MODES.FULL;

        /**
         * Source viewer ID (the one being actively manipulated)
         * @type {string|null}
         * @private
         */
        this._sourceViewerId = null;

        /**
         * Lock to prevent sync loops
         * @type {boolean}
         * @private
         */
        this._syncLock = false;

        /**
         * Event unsubscribe functions
         * @type {Function[]}
         * @private
         */
        this._unsubscribers = [];

        /**
         * Debounced sync handler
         * @type {Function}
         * @private
         */
        this._debouncedSync = debounce(
            this._handleViewportChange.bind(this),
            SyncConfig.DEBOUNCE_MS,
        );

        // Setup event listeners
        this._setupEventListeners();

        console.warn('[SyncController] Initialized');
    }

    /**
     * Setup global event listeners
     * @private
     */
    _setupEventListeners() {
        // Listen for viewport changes
        const unsubViewport = eventBus.on(Events.VIEWER_VIEWPORT_CHANGE, (data) => {
            if (this.enabled && !this._syncLock) {
                this._debouncedSync(data);
            }
        });

        // Listen for pan events
        const unsubPan = eventBus.on(Events.VIEWER_PAN, (data) => {
            if (this.enabled && !this._syncLock && this.mode !== SyncConfig.MODES.ZOOM_ONLY) {
                this._debouncedSync(data);
            }
        });

        // Listen for zoom events
        const unsubZoom = eventBus.on(Events.VIEWER_ZOOM, (data) => {
            if (this.enabled && !this._syncLock && this.mode !== SyncConfig.MODES.PAN_ONLY) {
                this._debouncedSync(data);
            }
        });

        this._unsubscribers.push(unsubViewport, unsubPan, unsubZoom);
    }

    /**
     * Register a viewer for potential synchronization
     * @param {import('./ViewerInstance.js').ViewerInstance} viewer - Viewer to register
     */
    registerViewer(viewer) {
        if (!viewer || !viewer.id) {
            console.warn('[SyncController] Invalid viewer provided');
            return;
        }

        this._viewers.set(viewer.id, viewer);
        console.warn(`[SyncController] Registered viewer "${viewer.id}"`);
    }

    /**
     * Unregister a viewer
     * @param {string} viewerId - Viewer ID to unregister
     */
    unregisterViewer(viewerId) {
        this._viewers.delete(viewerId);
        this.syncedViewerIds.delete(viewerId);
        console.warn(`[SyncController] Unregistered viewer "${viewerId}"`);
    }

    /**
     * Enable synchronization
     * @param {string[]} [viewerIds=null] - Specific viewer IDs to sync (null = all)
     */
    enable(viewerIds = null) {
        // Determine which viewers to sync
        if (viewerIds) {
            viewerIds.forEach(id => {
                if (this._viewers.has(id)) {
                    this.syncedViewerIds.add(id);
                }
            });
        } else {
            // Sync all registered viewers
            this._viewers.forEach((_, id) => {
                this.syncedViewerIds.add(id);
            });
        }

        this.enabled = true;

        eventBus.emit(Events.SYNC_ENABLED, {
            viewerIds: Array.from(this.syncedViewerIds),
        });

        console.warn(`[SyncController] Sync enabled for ${this.syncedViewerIds.size} viewers`);
    }

    /**
     * Disable synchronization
     */
    disable() {
        this.enabled = false;
        this.syncedViewerIds.clear();
        this._sourceViewerId = null;

        eventBus.emit(Events.SYNC_DISABLED, {});

        console.warn('[SyncController] Sync disabled');
    }

    /**
     * Toggle synchronization
     * @returns {boolean} New enabled state
     */
    toggle() {
        if (this.enabled) {
            this.disable();
        } else {
            this.enable();
        }
        return this.enabled;
    }

    /**
     * Check if sync is enabled
     * @returns {boolean}
     */
    isEnabled() {
        return this.enabled;
    }

    /**
     * Set sync mode
     * @param {string} mode - Sync mode (FULL, PAN_ONLY, ZOOM_ONLY)
     */
    setMode(mode) {
        if (Object.values(SyncConfig.MODES).includes(mode)) {
            this.mode = mode;
            console.warn(`[SyncController] Mode set to: ${mode}`);
        } else {
            console.warn(`[SyncController] Unknown mode: ${mode}`);
        }
    }

    /**
     * Handle viewport change from a viewer
     * @param {Object} data - Event data
     * @param {string} data.viewerId - Source viewer ID
     * @param {Object} data.viewport - Viewport bounds
     * @private
     */
    _handleViewportChange(data) {
        const { viewerId, viewport } = data;

        // Ignore if source is not in synced set
        if (!this.syncedViewerIds.has(viewerId)) {
            return;
        }

        // Get source viewer
        const sourceViewer = this._viewers.get(viewerId);
        if (!sourceViewer || !sourceViewer.isReady()) {
            return;
        }

        // Acquire sync lock to prevent loops
        this._syncLock = true;
        this._sourceViewerId = viewerId;

        try {
            // Normalize viewport from source
            const normalizedViewport = this._normalizeViewport(viewport, sourceViewer);

            // Broadcast to other synced viewers
            this.syncedViewerIds.forEach(targetId => {
                if (targetId === viewerId) {return;}

                const targetViewer = this._viewers.get(targetId);
                if (!targetViewer || !targetViewer.isReady()) {return;}

                // Denormalize for target slide dimensions
                const targetViewport = this._denormalizeViewport(normalizedViewport, targetViewer);

                // Apply viewport
                targetViewer.setViewport(targetViewport, false);
            });

        } finally {
            // Release lock after a short delay to allow animations
            setTimeout(() => {
                this._syncLock = false;
                this._sourceViewerId = null;
            }, SyncConfig.DEBOUNCE_MS * 2);
        }
    }

    /**
     * Normalize viewport to relative coordinates (0-1)
     *
     * OpenSeadragon already uses normalized coordinates where width is 1.0
     * and height is aspect ratio. This method ensures consistency.
     *
     * @param {Object} viewport - Viewport bounds from viewer
     * @param {import('./ViewerInstance.js').ViewerInstance} sourceViewer - Source viewer
     * @returns {Object} Normalized viewport
     * @private
     */
    _normalizeViewport(viewport, _sourceViewer) {
        // OSD viewport is already normalized with width = 1.0
        // Just pass through the values
        return {
            x: viewport.x,
            y: viewport.y,
            width: viewport.width,
            height: viewport.height,
            zoom: viewport.zoom,
        };
    }

    /**
     * Denormalize viewport for target slide
     *
     * @param {Object} normalizedViewport - Normalized viewport
     * @param {import('./ViewerInstance.js').ViewerInstance} targetViewer - Target viewer
     * @returns {Object} Denormalized viewport for target
     * @private
     */
    _denormalizeViewport(normalizedViewport, _targetViewer) {
        // For OSD, viewports are already in compatible normalized space
        // Just pass through the values
        return {
            x: normalizedViewport.x,
            y: normalizedViewport.y,
            width: normalizedViewport.width,
            height: normalizedViewport.height,
        };
    }

    /**
     * Manually sync all viewers to a specific viewer's current viewport
     * @param {string} sourceViewerId - Viewer to sync FROM
     */
    syncTo(sourceViewerId) {
        const sourceViewer = this._viewers.get(sourceViewerId);
        if (!sourceViewer || !sourceViewer.isReady()) {
            console.warn(`[SyncController] Source viewer "${sourceViewerId}" not ready`);
            return;
        }

        const viewport = sourceViewer.getViewport();

        this._handleViewportChange({
            viewerId: sourceViewerId,
            viewport,
        });

        console.warn(`[SyncController] Synced all viewers to "${sourceViewerId}"`);
    }

    /**
     * Get sync status
     * @returns {Object} Sync status info
     */
    getStatus() {
        return {
            enabled: this.enabled,
            mode: this.mode,
            syncedViewerIds: Array.from(this.syncedViewerIds),
            registeredViewerCount: this._viewers.size,
            sourceViewerId: this._sourceViewerId,
        };
    }

    /**
     * Destroy the sync controller
     */
    destroy() {
        // Disable sync
        this.disable();

        // Unsubscribe from all events
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];

        // Clear viewers
        this._viewers.clear();

        console.warn('[SyncController] Destroyed');
    }
}

export { SyncController };
export default SyncController;
