/**
 * CompareLayout - Multi-viewer grid layout component
 *
 * Manages a grid of ViewerPanel components for side-by-side slide comparison.
 * Supports various layouts (1x1, 2x1, 2x2, etc.) and synchronization.
 *
 * @module components/CompareLayout
 *
 * @example
 * const layout = new CompareLayout(document.getElementById('app'));
 * layout.setLayout(2, 1); // Side by side
 * await layout.loadSlideAt(0, 'slide-abc', 'Sample A');
 * await layout.loadSlideAt(1, 'slide-xyz', 'Sample B');
 */

import { ViewerPanel } from './ViewerPanel.js';
import { SyncControls } from './SyncControls.js';
import { viewerManager } from '../viewers/ViewerManager.js';
import { eventBus } from '../core/EventBus.js';
import { Events, LayoutPresets, CSSClasses } from '../core/Constants.js';

/**
 * CompareLayout class - Grid layout for multiple viewers
 */
class CompareLayout {
    /**
     * Create a new CompareLayout
     * @param {HTMLElement} container - Container element for the layout
     * @param {Object} [options={}] - Configuration options
     * @param {string} [options.initialLayout='SINGLE'] - Initial layout preset
     * @param {boolean} [options.showSyncControls=true] - Show sync controls bar
     * @param {Function} [options.onSlideSelect] - Callback when slide selector clicked
     */
    constructor(container, options = {}) {
        /**
         * Options
         * @type {Object}
         */
        this.options = {
            initialLayout: 'SINGLE',
            showSyncControls: true,
            onSlideSelect: null,
            ...options,
        };

        /**
         * Container element
         * @type {HTMLElement}
         */
        this.container = container;

        /**
         * Layout element
         * @type {HTMLElement}
         */
        this.element = null;

        /**
         * ViewerPanel instances
         * @type {ViewerPanel[]}
         */
        this.panels = [];

        /**
         * Current layout configuration
         * @type {{ columns: number, rows: number, maxViewers: number }}
         */
        this.layout = { ...LayoutPresets[this.options.initialLayout] };

        /**
         * SyncControls instance
         * @type {SyncControls|null}
         */
        this.syncControls = null;

        /**
         * Active panel index
         * @type {number}
         */
        this.activePanelIndex = 0;

        /** @type {Array<Function>} EventBus unsubscribe functions */
        this._unsubscribers = [];

        // Build the layout
        this._build();
    }

    /**
     * Build layout DOM structure
     * @private
     */
    _build() {
        // Create layout container
        this.element = document.createElement('div');
        this.element.className = CSSClasses.COMPARE_LAYOUT;
        this.element.dataset.layout = this.options.initialLayout.toLowerCase();

        // Apply initial layout class
        this._applyLayoutClass();

        // Add to container
        this.container.appendChild(this.element);

        // IMPORTANT: Update ViewerManager layout BEFORE creating panels
        // This ensures max viewers is set correctly
        viewerManager.setLayout(this.layout.columns, this.layout.rows);

        // Create initial panels
        this._createPanels();

        // Create sync controls if enabled
        if (this.options.showSyncControls) {
            this._createSyncControls();
        }

        // Setup event listeners
        this._setupEventListeners();

        console.warn(`[CompareLayout] Created with ${this.layout.maxViewers} panels`);
    }

    /**
     * Apply CSS class for current layout
     * @private
     */
    _applyLayoutClass() {
        // Remove old layout classes
        this.element.classList.remove(
            'layout-1x1', 'layout-2x1', 'layout-1x2',
            'layout-2x2', 'layout-3x2', 'layout-3x3',
        );

        // Add current layout class
        const layoutClass = `layout-${this.layout.columns}x${this.layout.rows}`;
        this.element.classList.add(layoutClass);
        this.element.dataset.layout = layoutClass;
    }

    /**
     * Create panel instances for current layout
     * @private
     */
    _createPanels() {
        const panelCount = this.layout.maxViewers;

        for (let i = 0; i < panelCount; i++) {
            this._createPanel(i);
        }

        // Set first panel as active
        if (this.panels.length > 0) {
            this.panels[0].setActive(true);
        }
    }

    /**
     * Create a single panel
     * @param {number} index - Panel index
     * @private
     */
    _createPanel(index) {
        const panel = new ViewerPanel(
            `panel-${index}`,
            this.element,
            {
                title: `Visualiseur ${index + 1}`,
                showHeader: true,
                showClose: this.layout.maxViewers > 1,
                onSlideSelect: (p) => this._handleSlideSelect(p, index),
                onClose: (p) => this._handlePanelClose(p, index),
            },
        );

        this.panels.push(panel);

        // Set active on click
        panel.element.addEventListener('click', () => {
            this.setActivePanel(index);
        });
    }

    /**
     * Create sync controls bar
     * @private
     */
    _createSyncControls() {
        this.syncControls = new SyncControls(this.container, {
            onLayoutChange: (preset) => this.applyLayoutPreset(preset),
            onSyncToggle: (enabled) => this._handleSyncToggle(enabled),
            onSyncModeChange: (mode) => this._handleSyncModeChange(mode),
        });
    }

    /**
     * Setup event listeners
     * @private
     */
    _setupEventListeners() {
        // Listen for layout changes from manager
        this._unsubscribers.push(
            eventBus.on(Events.LAYOUT_CHANGED, (layout) => {
                // Sync our layout with manager's layout
                if (layout.columns !== this.layout.columns || layout.rows !== this.layout.rows) {
                    this.setLayout(layout.columns, layout.rows, false);
                }
            }),
        );
    }

    /**
     * Handle slide select for a panel
     * @param {ViewerPanel} panel - Panel instance
     * @param {number} index - Panel index
     * @private
     */
    _handleSlideSelect(panel, index) {
        if (this.options.onSlideSelect) {
            this.options.onSlideSelect(panel, index);
        } else {
            eventBus.emit(Events.SLIDE_SELECTED, {
                panelId: panel.id,
                panelIndex: index,
            });
        }
    }

    /**
     * Handle panel close
     * @param {ViewerPanel} panel - Panel instance
     * @param {number} index - Panel index
     * @private
     */
    _handlePanelClose(panel, index) {
        // Don't close if only one panel
        if (this.panels.length <= 1) {
            console.warn('[CompareLayout] Cannot close last panel');
            return;
        }

        // Remove panel
        this.panels.splice(index, 1);
        panel.destroy();

        // Recalculate layout
        const remaining = this.panels.length;
        const cols = Math.ceil(Math.sqrt(remaining));
        const rows = Math.ceil(remaining / cols);
        this.layout = { columns: cols, rows, maxViewers: remaining };

        this._applyLayoutClass();

        // Update manager
        viewerManager.setLayout(cols, rows);

        console.warn(`[CompareLayout] Panel closed, ${remaining} remaining`);
    }

    /**
     * Handle sync toggle
     * @param {boolean} enabled - New sync state
     * @private
     */
    async _handleSyncToggle(enabled) {
        if (enabled) {
            await viewerManager.enableSync();
            this.panels.forEach(p => p.setSynced(true));
        } else {
            viewerManager.disableSync();
            this.panels.forEach(p => p.setSynced(false));
        }
    }

    /**
     * Handle sync mode change
     * @param {string} mode - New sync mode (full, panOnly, zoomOnly)
     * @private
     */
    _handleSyncModeChange(mode) {
        viewerManager.setSyncMode(mode);
        eventBus.emit(Events.SYNC_MODE_CHANGED, { mode });
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    /**
     * Set grid layout
     * @param {number} columns - Number of columns
     * @param {number} rows - Number of rows
     * @param {boolean} [updateManager=true] - Update ViewerManager
     */
    setLayout(columns, rows, updateManager = true) {
        const newMax = columns * rows;
        const currentCount = this.panels.length;

        // Update layout config
        this.layout = { columns, rows, maxViewers: newMax };

        // IMPORTANT: Update ViewerManager BEFORE creating new panels
        // This ensures max viewers limit is set correctly
        if (updateManager) {
            viewerManager.setLayout(columns, rows);
        }

        // Add panels if needed
        if (newMax > currentCount) {
            for (let i = currentCount; i < newMax; i++) {
                this._createPanel(i);
            }
        } else if (newMax < currentCount) {
            // Remove panels if needed
            for (let i = currentCount - 1; i >= newMax; i--) {
                const panel = this.panels.pop();
                panel.destroy();
            }
        }

        // Apply CSS class
        this._applyLayoutClass();

        // Update sync controls if exists
        if (this.syncControls) {
            this.syncControls.updateLayout(columns, rows);
        }

        console.warn(`[CompareLayout] Layout set to ${columns}x${rows}`);
    }

    /**
     * Apply a layout preset
     * @param {string} presetName - Preset name (e.g., 'SINGLE', 'SIDE_BY_SIDE')
     */
    applyLayoutPreset(presetName) {
        const preset = LayoutPresets[presetName];

        if (!preset) {
            console.warn(`[CompareLayout] Unknown preset: ${presetName}`);
            return;
        }

        this.setLayout(preset.columns, preset.rows);
    }

    /**
     * Load a slide in a specific panel
     * @param {number} panelIndex - Panel index (0-based)
     * @param {string} slideId - Slide ID
     * @param {string} [slideName] - Slide name for display
     * @returns {Promise<void>}
     */
    async loadSlideAt(panelIndex, slideId, slideName = '') {
        if (panelIndex < 0 || panelIndex >= this.panels.length) {
            throw new Error(`Invalid panel index: ${panelIndex}`);
        }

        await this.panels[panelIndex].loadSlide(slideId, slideName);
    }

    /**
     * Load a slide in the active panel
     * @param {string} slideId - Slide ID
     * @param {string} [slideName] - Slide name for display
     * @returns {Promise<void>}
     */
    async loadSlide(slideId, slideName = '') {
        if (this.panels.length === 0) {
            throw new Error('No panels available');
        }

        await this.panels[this.activePanelIndex].loadSlide(slideId, slideName);
    }

    /**
     * Get panel at index
     * @param {number} index - Panel index
     * @returns {ViewerPanel|null} Panel or null
     */
    getPanel(index) {
        return this.panels[index] || null;
    }

    /**
     * Get active panel
     * @returns {ViewerPanel} Active panel
     */
    getActivePanel() {
        return this.panels[this.activePanelIndex];
    }

    /**
     * Set active panel by index
     * @param {number} index - Panel index
     */
    setActivePanel(index) {
        if (index < 0 || index >= this.panels.length) {
            return;
        }

        // Deactivate current
        this.panels.forEach(p => p.setActive(false));

        // Activate new
        this.activePanelIndex = index;
        this.panels[index].setActive(true);
    }

    /**
     * Get all panels
     * @returns {ViewerPanel[]} Array of panels
     */
    getAllPanels() {
        return [...this.panels];
    }

    /**
     * Get panel count
     * @returns {number} Number of panels
     */
    getPanelCount() {
        return this.panels.length;
    }

    /**
     * Add a new panel
     * @returns {ViewerPanel} New panel
     */
    addPanel() {
        const newIndex = this.panels.length;

        // Recalculate layout
        const cols = Math.ceil(Math.sqrt(newIndex + 1));
        const rows = Math.ceil((newIndex + 1) / cols);

        this.setLayout(cols, rows);

        return this.panels[newIndex];
    }

    /**
     * Remove a panel
     * @param {number} index - Panel index to remove
     */
    removePanel(index) {
        if (index < 0 || index >= this.panels.length) {
            return;
        }

        this._handlePanelClose(this.panels[index], index);
    }

    /**
     * Enable synchronization
     */
    async enableSync() {
        await viewerManager.enableSync();
        this.panels.forEach(p => p.setSynced(true));

        if (this.syncControls) {
            this.syncControls.setSyncState(true);
        }
    }

    /**
     * Disable synchronization
     */
    disableSync() {
        viewerManager.disableSync();
        this.panels.forEach(p => p.setSynced(false));

        if (this.syncControls) {
            this.syncControls.setSyncState(false);
        }
    }

    /**
     * Toggle synchronization
     * @returns {Promise<boolean>} New sync state
     */
    async toggleSync() {
        const newState = await viewerManager.toggleSync();
        this.panels.forEach(p => p.setSynced(newState));

        if (this.syncControls) {
            this.syncControls.setSyncState(newState);
        }

        return newState;
    }

    /**
     * Get layout state
     * @returns {Object} Layout state
     */
    getState() {
        return {
            layout: this.layout,
            activePanelIndex: this.activePanelIndex,
            panelCount: this.panels.length,
            syncEnabled: viewerManager.isSyncEnabled(),
            panels: this.panels.map(p => p.getState()),
        };
    }

    /**
     * Reset all panels
     */
    resetAll() {
        this.panels.forEach(panel => {
            panel.unloadSlide();
            panel.resetView();
        });
    }

    /**
     * Destroy the layout
     */
    destroy() {
        console.warn('[CompareLayout] Destroying');

        // Clean up EventBus subscriptions
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];

        // Destroy sync controls
        if (this.syncControls) {
            this.syncControls.destroy();
            this.syncControls = null;
        }

        // Destroy all panels
        this.panels.forEach(panel => panel.destroy());
        this.panels = [];

        // Remove from DOM
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }

        this.element = null;
        this.container = null;
    }
}

export { CompareLayout };
export default CompareLayout;
