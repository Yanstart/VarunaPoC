/**
 * ViewerManager - Singleton manager for all viewer instances
 *
 * Central management of multiple ViewerInstance objects. Handles creation,
 * destruction, layout management, and coordination between viewers.
 * Implements Singleton + Facade patterns.
 *
 * @module viewers/ViewerManager
 *
 * @example
 * const manager = ViewerManager.getInstance();
 *
 * // Create viewers
 * const viewer1 = manager.createViewer('v1', container1);
 * const viewer2 = manager.createViewer('v2', container2);
 *
 * // Load slides
 * await viewer1.loadSlide('slide-abc');
 * await viewer2.loadSlide('slide-xyz');
 *
 * // Get all viewers
 * const allViewers = manager.getAllViewers();
 */

import { ViewerFactory } from './ViewerFactory.js';
import { eventBus } from '../core/EventBus.js';
import { Events, LayoutPresets, DEFAULT_LAYOUT, SyncConfig } from '../core/Constants.js';

/**
 * Singleton instance
 * @type {ViewerManager|null}
 */
let instance = null;

/**
 * ViewerManager class - Singleton for managing viewers
 */
class ViewerManager {
    /**
     * Private constructor (use getInstance())
     */
    constructor() {
        if (instance) {
            return instance;
        }

        /**
         * Map of viewer ID to ViewerInstance
         * @type {Map<string, import('./ViewerInstance.js').ViewerInstance>}
         * @private
         */
        this._viewers = new Map();

        /**
         * Current layout configuration
         * @type {{ columns: number, rows: number, maxViewers: number }}
         * @private
         */
        this._layout = { ...DEFAULT_LAYOUT };

        /**
         * Active viewer ID (for focus/selection)
         * @type {string|null}
         * @private
         */
        this._activeViewerId = null;

        /**
         * SyncController reference (lazy loaded)
         * @type {import('./SyncController.js').SyncController|null}
         * @private
         */
        this._syncController = null;

        /**
         * Sync enabled state
         * @type {boolean}
         * @private
         */
        this._syncEnabled = SyncConfig.ENABLED_BY_DEFAULT;

        instance = this;

        // Listen for viewer events
        this._setupEventListeners();

        console.warn('[ViewerManager] Initialized');
    }

    /**
     * Get the singleton ViewerManager instance
     * @returns {ViewerManager} The singleton instance
     */
    static getInstance() {
        if (!instance) {
            instance = new ViewerManager();
        }
        return instance;
    }

    /**
     * Setup global event listeners
     * @private
     */
    _setupEventListeners() {
        // Track viewer destruction
        eventBus.on(Events.VIEWER_DESTROYED, ({ viewerId }) => {
            this._viewers.delete(viewerId);

            if (this._activeViewerId === viewerId) {
                // Set new active viewer
                const remaining = this.getAllViewers();
                this._activeViewerId = remaining.length > 0 ? remaining[0].id : null;
            }
        });
    }

    // ==========================================
    // VIEWER CRUD OPERATIONS
    // ==========================================

    /**
     * Create a new viewer
     * @param {string} [id] - Viewer ID (auto-generated if omitted)
     * @param {HTMLElement|string} container - Container element
     * @param {Object} [options={}] - Viewer options
     * @returns {import('./ViewerInstance.js').ViewerInstance} Created viewer
     */
    createViewer(id, container, options = {}) {
        // Check viewer limit
        if (this._viewers.size >= this._layout.maxViewers) {
            console.warn(`[ViewerManager] Maximum viewers (${this._layout.maxViewers}) reached`);
            return null;
        }

        // Create viewer via factory
        const viewer = ViewerFactory.create(id, container, options);

        // Register viewer
        this._viewers.set(viewer.id, viewer);

        // Set as active if first viewer
        if (!this._activeViewerId) {
            this._activeViewerId = viewer.id;
        }

        // Emit event
        eventBus.emit(Events.VIEWER_ADDED, {
            viewerId: viewer.id,
            viewerCount: this._viewers.size,
        });

        console.warn(`[ViewerManager] Viewer "${viewer.id}" created (${this._viewers.size}/${this._layout.maxViewers})`);

        return viewer;
    }

    /**
     * Destroy a viewer
     * @param {string} viewerId - Viewer ID to destroy
     * @returns {boolean} True if destroyed
     */
    destroyViewer(viewerId) {
        const viewer = this._viewers.get(viewerId);

        if (!viewer) {
            console.warn(`[ViewerManager] Viewer "${viewerId}" not found`);
            return false;
        }

        // Destroy the viewer
        viewer.destroy();

        // Remove from map
        this._viewers.delete(viewerId);

        // Emit event
        eventBus.emit(Events.VIEWER_REMOVED, {
            viewerId,
            viewerCount: this._viewers.size,
        });

        console.warn(`[ViewerManager] Viewer "${viewerId}" destroyed (${this._viewers.size} remaining)`);

        return true;
    }

    /**
     * Get a viewer by ID
     * @param {string} viewerId - Viewer ID
     * @returns {import('./ViewerInstance.js').ViewerInstance|null} Viewer or null
     */
    getViewer(viewerId) {
        return this._viewers.get(viewerId) || null;
    }

    /**
     * Get all viewers
     * @returns {import('./ViewerInstance.js').ViewerInstance[]} Array of viewers
     */
    getAllViewers() {
        return Array.from(this._viewers.values());
    }

    /**
     * Get viewer count
     * @returns {number} Number of viewers
     */
    getViewerCount() {
        return this._viewers.size;
    }

    /**
     * Check if a viewer exists
     * @param {string} viewerId - Viewer ID
     * @returns {boolean} True if exists
     */
    hasViewer(viewerId) {
        return this._viewers.has(viewerId);
    }

    /**
     * Destroy all viewers
     */
    destroyAll() {
        const viewerIds = Array.from(this._viewers.keys());

        viewerIds.forEach(id => {
            this.destroyViewer(id);
        });

        console.warn('[ViewerManager] All viewers destroyed');
    }

    // ==========================================
    // ACTIVE VIEWER MANAGEMENT
    // ==========================================

    /**
     * Get the active viewer
     * @returns {import('./ViewerInstance.js').ViewerInstance|null} Active viewer or null
     */
    getActiveViewer() {
        return this._activeViewerId ? this._viewers.get(this._activeViewerId) : null;
    }

    /**
     * Set the active viewer
     * @param {string} viewerId - Viewer ID to make active
     * @returns {boolean} True if set successfully
     */
    setActiveViewer(viewerId) {
        if (!this._viewers.has(viewerId)) {
            console.warn(`[ViewerManager] Cannot set active: viewer "${viewerId}" not found`);
            return false;
        }

        this._activeViewerId = viewerId;
        console.warn(`[ViewerManager] Active viewer: "${viewerId}"`);

        return true;
    }

    // ==========================================
    // LAYOUT MANAGEMENT
    // ==========================================

    /**
     * Get current layout
     * @returns {{ columns: number, rows: number, maxViewers: number }}
     */
    getLayout() {
        return { ...this._layout };
    }

    /**
     * Set layout configuration
     * @param {number} columns - Number of columns
     * @param {number} rows - Number of rows
     */
    setLayout(columns, rows) {
        const maxViewers = columns * rows;

        // Destroy excess viewers if needed
        const currentCount = this._viewers.size;
        if (currentCount > maxViewers) {
            const excess = currentCount - maxViewers;
            const viewerIds = Array.from(this._viewers.keys());

            for (let i = 0; i < excess; i++) {
                const idToRemove = viewerIds[viewerIds.length - 1 - i];
                this.destroyViewer(idToRemove);
            }
        }

        this._layout = { columns, rows, maxViewers };

        eventBus.emit(Events.LAYOUT_CHANGED, this._layout);

        console.warn(`[ViewerManager] Layout set to ${columns}x${rows} (max ${maxViewers} viewers)`);
    }

    /**
     * Apply a layout preset
     * @param {string} presetName - Preset name (SINGLE, SIDE_BY_SIDE, etc.)
     */
    applyLayoutPreset(presetName) {
        const preset = LayoutPresets[presetName];

        if (!preset) {
            console.warn(`[ViewerManager] Unknown layout preset: "${presetName}"`);
            return;
        }

        this.setLayout(preset.columns, preset.rows);
    }

    /**
     * Add a viewer slot (expand layout if possible)
     * @returns {boolean} True if slot added
     */
    addViewerSlot() {
        const currentMax = this._layout.maxViewers;
        const newMax = currentMax + 1;

        // Recalculate grid
        const cols = Math.ceil(Math.sqrt(newMax));
        const rows = Math.ceil(newMax / cols);

        this._layout = { columns: cols, rows, maxViewers: newMax };

        eventBus.emit(Events.LAYOUT_CHANGED, this._layout);

        console.warn(`[ViewerManager] Added slot, layout now ${cols}x${rows}`);

        return true;
    }

    /**
     * Remove a viewer slot
     * @param {string} [viewerId] - Specific viewer to remove (or last one)
     * @returns {boolean} True if slot removed
     */
    removeViewerSlot(viewerId) {
        if (this._viewers.size === 0) {
            return false;
        }

        // Destroy specified viewer or last one
        const idToRemove = viewerId || Array.from(this._viewers.keys()).pop();
        this.destroyViewer(idToRemove);

        // Recalculate layout
        const remaining = this._viewers.size;
        if (remaining > 0) {
            const cols = Math.ceil(Math.sqrt(remaining));
            const rows = Math.ceil(remaining / cols);
            this._layout = { columns: cols, rows, maxViewers: remaining };
        } else {
            this._layout = { ...DEFAULT_LAYOUT };
        }

        eventBus.emit(Events.LAYOUT_CHANGED, this._layout);

        return true;
    }

    // ==========================================
    // SYNCHRONIZATION
    // ==========================================

    /**
     * Check if sync is enabled
     * @returns {boolean}
     */
    isSyncEnabled() {
        return this._syncEnabled;
    }

    /**
     * Enable synchronization between viewers
     * @param {string[]} [viewerIds=null] - Specific viewer IDs (null = all)
     */
    async enableSync(viewerIds = null) {
        // Lazy load SyncController
        if (!this._syncController) {
            const { SyncController } = await import('./SyncController.js');
            this._syncController = new SyncController();
        }

        // Register viewers
        const viewers = viewerIds
            ? viewerIds.map(id => this.getViewer(id)).filter(Boolean)
            : this.getAllViewers();

        viewers.forEach(viewer => {
            this._syncController.registerViewer(viewer);
        });

        // Enable sync
        this._syncController.enable(viewerIds);
        this._syncEnabled = true;

        eventBus.emit(Events.SYNC_ENABLED, {
            viewerIds: viewers.map(v => v.id),
        });

        console.warn('[ViewerManager] Sync enabled');
    }

    /**
     * Disable synchronization
     */
    disableSync() {
        if (this._syncController) {
            this._syncController.disable();
        }

        this._syncEnabled = false;

        eventBus.emit(Events.SYNC_DISABLED, {});

        console.warn('[ViewerManager] Sync disabled');
    }

    /**
     * Toggle synchronization
     * @returns {boolean} New sync state
     */
    async toggleSync() {
        if (this._syncEnabled) {
            this.disableSync();
        } else {
            await this.enableSync();
        }

        return this._syncEnabled;
    }

    /**
     * Get synced viewer IDs
     * @returns {string[]} Array of synced viewer IDs
     */
    getSyncedViewers() {
        if (!this._syncController) {
            return [];
        }

        return Array.from(this._syncController.syncedViewerIds);
    }

    // ==========================================
    // UTILITY METHODS
    // ==========================================

    /**
     * Load slide in first available viewer (or create one)
     * @param {string} slideId - Slide ID
     * @param {HTMLElement} [container] - Container for new viewer
     * @returns {Promise<import('./ViewerInstance.js').ViewerInstance>}
     */
    async loadSlide(slideId, container) {
        let viewer = this.getActiveViewer();

        if (!viewer) {
            if (!container) {
                throw new Error('ViewerManager.loadSlide: no viewer and no container provided');
            }
            viewer = this.createViewer(null, container);
        }

        await viewer.loadSlide(slideId);

        return viewer;
    }

    /**
     * Get state of all viewers
     * @returns {Object[]} Array of viewer states
     */
    getState() {
        return {
            viewerCount: this._viewers.size,
            activeViewerId: this._activeViewerId,
            layout: this._layout,
            syncEnabled: this._syncEnabled,
            viewers: this.getAllViewers().map(v => v.getState()),
        };
    }

    /**
     * Reset manager to initial state
     */
    reset() {
        this.destroyAll();
        this._layout = { ...DEFAULT_LAYOUT };
        this._activeViewerId = null;
        this._syncEnabled = SyncConfig.ENABLED_BY_DEFAULT;

        if (this._syncController) {
            this._syncController.disable();
        }

        console.warn('[ViewerManager] Reset to initial state');
    }
}

// Export singleton getter and class
export const viewerManager = ViewerManager.getInstance();
export { ViewerManager };
export default viewerManager;
