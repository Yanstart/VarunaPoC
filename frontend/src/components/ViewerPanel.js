/**
 * ViewerPanel - Single viewer panel component
 *
 * A panel containing a ViewerInstance with header, controls, and status.
 * Used as a building block for multi-viewer layouts.
 *
 * @module components/ViewerPanel
 *
 * @example
 * const panel = new ViewerPanel('panel-1', parentElement);
 * await panel.loadSlide('abc123');
 */

import { ViewerFactory } from '../viewers/ViewerFactory.js';
import { viewerManager } from '../viewers/ViewerManager.js';
import { eventBus } from '../core/EventBus.js';
import { Events, CSSClasses, ViewerStates } from '../core/Constants.js';
import { MLPanel } from './MLPanel.js';
import { HeatmapOverlay } from './HeatmapOverlay.js';

/**
 * ViewerPanel class - Panel wrapper for a single viewer
 */
class ViewerPanel {
    /**
     * Create a new ViewerPanel
     * @param {string} [id] - Panel ID (auto-generated if omitted)
     * @param {HTMLElement} parentElement - Parent element to append panel to
     * @param {Object} [options={}] - Configuration options
     * @param {string} [options.title='Slide Viewer'] - Panel title
     * @param {boolean} [options.showHeader=true] - Show panel header
     * @param {boolean} [options.showClose=true] - Show close button
     * @param {Function} [options.onSlideSelect] - Callback when slide selector clicked
     * @param {Function} [options.onClose] - Callback when close button clicked
     */
    constructor(id, parentElement, options = {}) {
        /**
         * Panel ID
         * @type {string}
         */
        this.id = id || `panel-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        /**
         * Options
         * @type {Object}
         */
        this.options = {
            title: 'Slide Viewer',
            showHeader: true,
            showClose: true,
            onSlideSelect: null,
            onClose: null,
            ...options
        };

        /**
         * Parent element reference
         * @type {HTMLElement}
         */
        this.parentElement = parentElement;

        /**
         * Panel root element
         * @type {HTMLElement}
         */
        this.element = null;

        /**
         * Viewer container element
         * @type {HTMLElement}
         */
        this.viewerContainer = null;

        /**
         * ViewerInstance reference
         * @type {import('../viewers/ViewerInstance.js').ViewerInstance|null}
         */
        this.viewer = null;

        /**
         * Current slide ID
         * @type {string|null}
         */
        this.slideId = null;

        /**
         * Current slide name (for display)
         * @type {string}
         */
        this.slideName = '';

        /**
         * Whether panel is active
         * @type {boolean}
         */
        this.isActive = false;

        /**
         * Whether panel is synced
         * @type {boolean}
         */
        this.isSynced = false;

        /**
         * ML Panel component
         * @type {MLPanel|null}
         */
        this.mlPanel = null;

        /**
         * Heatmap overlay component
         * @type {HeatmapOverlay|null}
         */
        this.heatmapOverlay = null;

        // Build the panel
        this._build();
    }

    /**
     * Build panel DOM structure
     * @private
     */
    _build() {
        // Create panel element
        this.element = document.createElement('div');
        this.element.id = this.id;
        this.element.className = CSSClasses.VIEWER_PANEL;

        // Build header if enabled
        if (this.options.showHeader) {
            this._buildHeader();
        }

        // Build viewer container
        this._buildViewerContainer();

        // Append to parent
        this.parentElement.appendChild(this.element);

        // Create viewer instance
        this._createViewer();

        // Setup event listeners
        this._setupEventListeners();

        console.log(`[ViewerPanel] Created panel "${this.id}"`);
    }

    /**
     * Build panel header
     * @private
     */
    _buildHeader() {
        const header = document.createElement('div');
        header.className = 'viewer-panel-header';

        // Title
        const title = document.createElement('div');
        title.className = 'viewer-panel-title';
        title.textContent = this.options.title;
        title.dataset.slideTitle = '';

        // Actions container
        const actions = document.createElement('div');
        actions.className = 'viewer-panel-actions';

        // Select slide button
        const selectBtn = document.createElement('button');
        selectBtn.className = 'viewer-panel-action';
        selectBtn.title = 'Select slide';
        selectBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg>';
        selectBtn.addEventListener('click', () => this._onSelectSlide());

        // Reset view button
        const resetBtn = document.createElement('button');
        resetBtn.className = 'viewer-panel-action';
        resetBtn.title = 'Reset view';
        resetBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>';
        resetBtn.addEventListener('click', () => this.resetView());

        // ML Analysis button
        const mlBtn = document.createElement('button');
        mlBtn.className = 'viewer-panel-action viewer-panel-action--ml';
        mlBtn.title = 'ML Analysis';
        mlBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>';
        mlBtn.addEventListener('click', () => this._toggleMLPanel());

        actions.appendChild(selectBtn);
        actions.appendChild(resetBtn);
        actions.appendChild(mlBtn);

        // Close button
        if (this.options.showClose) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'viewer-panel-action';
            closeBtn.title = 'Close panel';
            closeBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>';
            closeBtn.addEventListener('click', () => this._onClose());
            actions.appendChild(closeBtn);
        }

        header.appendChild(title);
        header.appendChild(actions);
        this.element.appendChild(header);
    }

    /**
     * Build viewer container
     * @private
     */
    _buildViewerContainer() {
        this.viewerContainer = document.createElement('div');
        this.viewerContainer.className = CSSClasses.VIEWER_CONTAINER;
        this.viewerContainer.id = `viewer-container-${this.id}`;

        // Add empty state
        const emptyState = document.createElement('div');
        emptyState.className = 'viewer-empty-state';
        emptyState.innerHTML = `
            <div class="viewer-empty-icon">+</div>
            <div class="viewer-empty-text">No slide loaded</div>
            <button class="viewer-empty-action">Select Slide</button>
        `;

        const selectBtn = emptyState.querySelector('.viewer-empty-action');
        selectBtn.addEventListener('click', () => this._onSelectSlide());

        this.viewerContainer.appendChild(emptyState);
        this.viewerContainer.classList.add('is-empty');

        this.element.appendChild(this.viewerContainer);
    }

    /**
     * Create viewer instance
     * @private
     */
    _createViewer() {
        // Create viewer via manager
        this.viewer = viewerManager.createViewer(
            `viewer-${this.id}`,
            this.viewerContainer,
            { showNavigator: true }
        );

        // Handle case where viewer creation failed (max viewers reached)
        if (!this.viewer) {
            console.warn(`[ViewerPanel] Could not create viewer for panel "${this.id}" - max viewers reached`);
            return;
        }

        // Listen for viewer state changes
        this.viewer.state.onTransition((oldState, newState) => {
            this._updateContainerState(newState);
        });
    }

    /**
     * Update container state classes
     * @param {string} state - Current viewer state
     * @private
     */
    _updateContainerState(state) {
        // Remove all state classes
        this.viewerContainer.classList.remove('is-empty', 'is-loading', 'is-ready', 'is-error');

        // Add current state class
        switch (state) {
            case ViewerStates.IDLE:
                this.viewerContainer.classList.add('is-empty');
                break;
            case ViewerStates.LOADING:
                this.viewerContainer.classList.add('is-loading');
                break;
            case ViewerStates.READY:
                this.viewerContainer.classList.add('is-ready');
                break;
            case ViewerStates.ERROR:
                this.viewerContainer.classList.add('is-error');
                break;
        }
    }

    /**
     * Setup event listeners
     * @private
     */
    _setupEventListeners() {
        // Click to activate
        this.element.addEventListener('click', () => {
            this.setActive(true);
        });

        // Listen for sync events
        eventBus.on(Events.SYNC_ENABLED, ({ viewerIds }) => {
            if (this.viewer && viewerIds.includes(this.viewer.id)) {
                this.setSynced(true);
            }
        });

        eventBus.on(Events.SYNC_DISABLED, () => {
            this.setSynced(false);
        });
    }

    /**
     * Handle slide select action
     * @private
     */
    _onSelectSlide() {
        if (this.options.onSlideSelect) {
            this.options.onSlideSelect(this);
        } else {
            console.log(`[ViewerPanel] Slide select requested for panel "${this.id}"`);
            // Emit event for external handling
            eventBus.emit(Events.SLIDE_SELECTED, { panelId: this.id });
        }
    }

    /**
     * Handle close action
     * @private
     */
    _onClose() {
        if (this.options.onClose) {
            this.options.onClose(this);
        } else {
            this.destroy();
        }
    }

    /**
     * Toggle ML Panel visibility
     * @private
     */
    _toggleMLPanel() {
        // Create ML panel if not exists
        if (!this.mlPanel) {
            this.mlPanel = new MLPanel(this.viewerContainer, {
                viewerId: this.viewer ? this.viewer.id : this.id
            });

            // Set current slide if loaded
            if (this.slideId) {
                this.mlPanel.setSlide(this.slideId);
            }
        }

        // Toggle visibility
        this.mlPanel.element.classList.toggle('is-hidden');

        // Update button state
        const mlBtn = this.element.querySelector('.viewer-panel-action--ml');
        if (mlBtn) {
            mlBtn.classList.toggle('is-active', !this.mlPanel.element.classList.contains('is-hidden'));
        }
    }

    /**
     * Initialize heatmap overlay
     * @private
     */
    _initHeatmapOverlay() {
        if (this.viewer && !this.heatmapOverlay) {
            this.heatmapOverlay = new HeatmapOverlay(this.viewer, {
                opacity: 0.5
            });
        }
    }

    /**
     * Load a slide into this panel
     * @param {string} slideId - Slide ID
     * @param {string} [slideName] - Slide name for display
     * @returns {Promise<void>}
     */
    async loadSlide(slideId, slideName = '') {
        if (!this.viewer) {
            throw new Error('ViewerPanel: Viewer not initialized');
        }

        this.slideId = slideId;
        this.slideName = slideName || slideId;

        // Update title
        const titleEl = this.element.querySelector('.viewer-panel-title');
        if (titleEl) {
            titleEl.textContent = this.slideName;
        }

        // Load slide in viewer
        await this.viewer.loadSlide(slideId);

        // Initialize heatmap overlay after slide is loaded
        this._initHeatmapOverlay();

        // Notify ML panel if it exists
        if (this.mlPanel) {
            this.mlPanel.setSlide(slideId);
        }

        // Emit slide loaded event for ML components
        eventBus.emit(Events.SLIDE_LOADED, {
            viewerId: this.viewer.id,
            slideId: slideId,
            slideName: this.slideName
        });

        console.log(`[ViewerPanel] Loaded slide "${slideId}" in panel "${this.id}"`);
    }

    /**
     * Unload current slide
     */
    unloadSlide() {
        if (this.viewer) {
            this.viewer.unloadSlide();
        }

        this.slideId = null;
        this.slideName = '';

        // Reset title
        const titleEl = this.element.querySelector('.viewer-panel-title');
        if (titleEl) {
            titleEl.textContent = this.options.title;
        }
    }

    /**
     * Reset view to home position
     */
    resetView() {
        if (this.viewer) {
            this.viewer.resetView();
        }
    }

    /**
     * Set panel as active
     * @param {boolean} active - Active state
     */
    setActive(active) {
        // Guard against calls after destroy
        if (!this.element) {
            return;
        }

        this.isActive = active;
        this.element.classList.toggle(CSSClasses.ACTIVE, active);

        if (active && this.viewer) {
            viewerManager.setActiveViewer(this.viewer.id);
        }
    }

    /**
     * Set panel as synced
     * @param {boolean} synced - Synced state
     */
    setSynced(synced) {
        // Guard against calls after destroy
        if (!this.element) {
            return;
        }

        this.isSynced = synced;
        this.element.classList.toggle(CSSClasses.SYNCED, synced);
    }

    /**
     * Get panel state
     * @returns {Object} Panel state
     */
    getState() {
        return {
            id: this.id,
            slideId: this.slideId,
            slideName: this.slideName,
            isActive: this.isActive,
            isSynced: this.isSynced,
            viewerState: this.viewer ? this.viewer.getState() : null
        };
    }

    /**
     * Destroy the panel
     */
    destroy() {
        console.log(`[ViewerPanel] Destroying panel "${this.id}"`);

        // Destroy ML panel
        if (this.mlPanel) {
            this.mlPanel.destroy();
            this.mlPanel = null;
        }

        // Destroy heatmap overlay
        if (this.heatmapOverlay) {
            this.heatmapOverlay.destroy();
            this.heatmapOverlay = null;
        }

        // Destroy viewer
        if (this.viewer) {
            viewerManager.destroyViewer(this.viewer.id);
            this.viewer = null;
        }

        // Remove from DOM
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }

        // Clear references
        this.element = null;
        this.viewerContainer = null;
        this.parentElement = null;
    }
}

export { ViewerPanel };
export default ViewerPanel;
