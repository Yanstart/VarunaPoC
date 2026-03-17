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

import { viewerManager } from '../viewers/ViewerManager.js';
import { eventBus } from '../core/EventBus.js';
import { Events, CSSClasses, ViewerStates } from '../core/Constants.js';
import { MLPanel } from './MLPanel.js';
import { HeatmapOverlay } from './HeatmapOverlay.js';
import { AnnotationLayer } from './AnnotationLayer.js';
import { DrawingTools } from './DrawingTools.js';
import { DetectionPanel } from './DetectionPanel.js';
import { CellCountingPanel } from './CellCountingPanel.js';
import { ClusteringPanel } from './ClusteringPanel.js';
import { LayerManager } from './LayerManager.js';
import { CountingPanel } from './CountingPanel.js';
import { QualityPanel } from './QualityPanel.js';
import { FocusAssistPanel } from './FocusAssistPanel.js';
import { SimilarityPanel } from './SimilarityPanel.js';
import { MLTabsContainer } from './MLTabsContainer.js';
import { ScaleBar } from './ScaleBar.js';
import { annotationStore } from '../services/AnnotationStore.js';
import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';

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
            title: i18nService.t('viewer.title'),
            showHeader: true,
            showClose: true,
            onSlideSelect: null,
            onClose: null,
            ...options,
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
         * ML Tabs container component
         * @type {MLTabsContainer|null}
         */
        this.mlTabsContainer = null;

        /**
         * ML Panel component
         * @type {MLPanel|null}
         */
        this.mlPanel = null;

        /**
         * Cell counting panel component
         * @type {CellCountingPanel|null}
         */
        this.cellCountingPanel = null;

        /**
         * Clustering panel component
         * @type {ClusteringPanel|null}
         */
        this.clusteringPanel = null;

        /**
         * Heatmap overlay component
         * @type {HeatmapOverlay|null}
         */
        this.heatmapOverlay = null;

        /**
         * Annotation layer component
         * @type {AnnotationLayer|null}
         */
        this.annotationLayer = null;

        /**
         * Drawing tools component
         * @type {DrawingTools|null}
         */
        this.drawingTools = null;

        /**
         * Detection panel component
         * @type {DetectionPanel|null}
         */
        this.detectionPanel = null;

        /**
         * Focus Assist panel component
         * @type {FocusAssistPanel|null}
         */
        this.focusAssistPanel = null;

        /**
         * Similarity panel component
         * @type {SimilarityPanel|null}
         */
        this.similarityPanel = null;

        /**
         * Layer manager component
         * @type {LayerManager|null}
         */
        this.layerManager = null;

        /**
         * Counting panel component
         * @type {CountingPanel|null}
         */
        this.countingPanel = null;

        /**
         * Quality panel component
         * @type {QualityPanel|null}
         */
        this.qualityPanel = null;

        /**
         * Magnification bar element
         * @type {HTMLElement|null}
         */
        this.magBar = null;

        /**
         * Scale bar component
         * @type {ScaleBar|null}
         */
        this.scaleBar = null;

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

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

        console.warn(`[ViewerPanel] Created panel "${this.id}"`);
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
        selectBtn.title = i18nService.t('viewer.selectSlide');
        selectBtn.setAttribute('aria-label', i18nService.t('viewer.selectSlide'));
        selectBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg>';
        selectBtn.addEventListener('click', () => this._onSelectSlide());

        // Reset view button
        const resetBtn = document.createElement('button');
        resetBtn.className = 'viewer-panel-action';
        resetBtn.title = i18nService.t('viewer.resetView');
        resetBtn.setAttribute('aria-label', i18nService.t('viewer.resetView'));
        resetBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>';
        resetBtn.addEventListener('click', () => this.resetView());

        // ML Analysis button
        const mlBtn = document.createElement('button');
        mlBtn.className = 'viewer-panel-action viewer-panel-action--ml';
        mlBtn.title = i18nService.t('viewer.aiAnalysis');
        mlBtn.setAttribute('aria-label', i18nService.t('viewer.aiAnalysis'));
        mlBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>';
        mlBtn.addEventListener('click', () => this._toggleMLPanel());

        actions.appendChild(selectBtn);
        actions.appendChild(resetBtn);
        actions.appendChild(mlBtn);

        // Close button
        if (this.options.showClose) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'viewer-panel-action';
            closeBtn.title = i18nService.t('viewer.closePanel');
            closeBtn.setAttribute('aria-label', i18nService.t('viewer.closePanel'));
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
        // Note: i18n strings are safe (from static JSON locale files, not user input)
        emptyState.innerHTML = `
            <div class="viewer-empty-icon">+</div>
            <div class="viewer-empty-text">${i18nService.t('viewer.noSlideLoaded')}</div>
            <button class="viewer-empty-action">${i18nService.t('viewer.selectSlideBtn')}</button>
        `;

        const selectBtn = emptyState.querySelector('.viewer-empty-action');
        selectBtn.addEventListener('click', () => this._onSelectSlide());

        this.viewerContainer.appendChild(emptyState);
        this.viewerContainer.classList.add('is-empty');

        // Magnification bar
        this.magBar = document.createElement('div');
        this.magBar.className = 'magnification-bar';
        this.magBar.textContent = '\u00d71';
        this.viewerContainer.appendChild(this.magBar);

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
            { showNavigator: true },
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
        this._unsubscribers.push(
            eventBus.on(Events.SYNC_ENABLED, ({ viewerIds }) => {
                if (this.viewer && viewerIds.includes(this.viewer.id)) {
                    this.setSynced(true);
                }
            }),
            eventBus.on(Events.SYNC_DISABLED, () => {
                this.setSynced(false);
            }),
        );

        // Magnification bar updates on viewport change
        this._unsubscribers.push(
            eventBus.on(Events.VIEWER_VIEWPORT_CHANGE, (data) => {
                if (data.viewerId === this.viewer?.id) {
                    this._updateMagnification();
                }
            }),
        );
    }

    /**
     * Update magnification bar display
     * @private
     */
    _updateMagnification() {
        if (!this.viewer || !this.magBar) {
            return;
        }
        const mag = this.viewer.getOpticalMagnification();
        this.magBar.textContent = '\u00d7' + mag;
        this.magBar.classList.toggle('magnification-bar--diagnostic', mag >= 10);
    }

    /**
     * Handle slide select action
     * @private
     */
    _onSelectSlide() {
        if (this.options.onSlideSelect) {
            this.options.onSlideSelect(this);
        } else {
            console.warn(`[ViewerPanel] Slide select requested for panel "${this.id}"`);
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
        // Create tabs container if not exists
        if (!this.mlTabsContainer) {
            this.mlTabsContainer = new MLTabsContainer(this.viewerContainer);

            // MLPanel + FocusAssistPanel in "analyse" tab
            const analysePane = this.mlTabsContainer.getPane('analyse');
            this.mlPanel = new MLPanel(analysePane, {
                viewerId: this.viewer ? this.viewer.id : this.id,
                viewerInstance: this.viewer,
            });
            const separator = document.createElement('div');
            separator.className = 'ml-tabs__separator';
            analysePane.appendChild(separator);
            this.focusAssistPanel = new FocusAssistPanel(analysePane, {
                slideId: this.slideId,
            });

            // DetectionPanel in "detection" tab
            const detectionPane = this.mlTabsContainer.getPane('detection');
            this.detectionPanel = new DetectionPanel(detectionPane, {
                slideId: this.slideId,
                viewerInstance: this.viewer,
            });

            // CellCountingPanel in "comptage" tab
            const comptagePane = this.mlTabsContainer.getPane('comptage');
            this.cellCountingPanel = new CellCountingPanel(comptagePane, {
                slideId: this.slideId,
                viewerInstance: this.viewer,
            });

            // ClusteringPanel in "clustering" tab
            const clusteringPane = this.mlTabsContainer.getPane('clustering');
            this.clusteringPanel = new ClusteringPanel(clusteringPane, {
                slideId: this.slideId,
            });

            // SimilarityPanel in "analyse" tab (after focus assist)
            this.similarityPanel = new SimilarityPanel(analysePane, {
                slideId: this.slideId,
            });

            // Set current slide if loaded
            if (this.slideId) {
                this.mlPanel.setSlide(this.slideId);
            }
        }

        // Toggle tabs container visibility
        this.mlTabsContainer.element.classList.toggle('is-hidden');

        // Update button state
        const mlBtn = this.element.querySelector('.viewer-panel-action--ml');
        if (mlBtn) {
            mlBtn.classList.toggle('is-active', !this.mlTabsContainer.element.classList.contains('is-hidden'));
        }
    }

    /**
     * Initialize heatmap overlay
     * @private
     */
    _initHeatmapOverlay() {
        if (this.viewer && !this.heatmapOverlay) {
            this.heatmapOverlay = new HeatmapOverlay(this.viewer, {
                opacity: 0.5,
            });
        }
    }

    /**
     * Initialize annotation components (lazy, once per panel)
     * @private
     */
    _initAnnotationComponents() {
        if (this.annotationLayer) {return;}

        this.annotationLayer = new AnnotationLayer(this.viewer);
        this.drawingTools = new DrawingTools(this.viewer, this.annotationLayer);

        const layerContainer = document.createElement('div');
        layerContainer.className = 'viewer-panel__layers';
        this.element.appendChild(layerContainer);
        this.layerManager = new LayerManager(layerContainer);

        // Counting panel for annotation statistics
        const countingContainer = document.createElement('div');
        countingContainer.className = 'viewer-panel__counting';
        this.element.appendChild(countingContainer);
        this.countingPanel = new CountingPanel(countingContainer);

        // Quality panel for inter-annotator agreement
        const qualityContainer = document.createElement('div');
        qualityContainer.className = 'viewer-panel__quality';
        this.element.appendChild(qualityContainer);
        this.qualityPanel = new QualityPanel(qualityContainer);
    }

    /**
     * Fetch MPP from backend and initialize scale bar + ruler measurements
     * @param {string} slideId
     * @private
     */
    async _initMeasurementTools(slideId) {
        let mpp = null;
        try {
            const resp = await apiService.get(`/api/v1/slides/${slideId}/mpp`);
            if (resp && resp.mpp_x) {
                mpp = resp.mpp_x;
            }
        } catch (err) {
            console.warn('[ViewerPanel] MPP fetch failed, falling back to pixel units:', err);
        }

        // Scale bar
        if (this.viewer && this.viewer.viewer) {
            if (this.scaleBar) {
                this.scaleBar.setMpp(mpp);
            } else {
                this.scaleBar = new ScaleBar(this.viewer.viewer, mpp);
                if (this.scaleBar.element) {
                    this.viewerContainer.appendChild(this.scaleBar.element);
                }
            }
        }

        // Pass MPP to drawing tools for ruler measurements
        if (this.drawingTools) {
            this.drawingTools.setMpp(mpp);
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

        // Initialize annotation components (lazy, once per panel)
        this._initAnnotationComponents();

        // Notify ML panel if it exists
        if (this.mlPanel) {
            this.mlPanel.setSlide(slideId);
        }

        // Notify detection panel if it exists
        if (this.detectionPanel) {
            this.detectionPanel.setSlide(slideId);
        }

        // Notify focus assist panel if it exists
        if (this.focusAssistPanel) {
            this.focusAssistPanel.setSlide(slideId);
        }

        // Notify similarity panel if it exists
        if (this.similarityPanel) {
            this.similarityPanel.setSlide(slideId);
        }

        // Notify cell counting panel if it exists
        if (this.cellCountingPanel) {
            this.cellCountingPanel.setSlide(slideId);
        }

        // Notify clustering panel if it exists
        if (this.clusteringPanel) {
            this.clusteringPanel.setSlide(slideId);
        }

        // Notify quality panel if it exists
        if (this.qualityPanel) {
            this.qualityPanel.setSlide(slideId);
        }

        // Note: SLIDE_LOADED event is already emitted by ViewerInstance's OSD 'open' handler.
        // Do NOT emit it again here - double emission causes MLPanel.setSlide() to be called
        // twice, resetting prediction state and making heatmap non-reactivable.

        // Fire-and-forget: MPP fetch is non-blocking — scale bar/ruler are
        // optional enhancements that should not delay slide display. Errors are
        // caught internally by _initMeasurementTools.
        this._initMeasurementTools(slideId);

        // Auto-tag: fetch and display slide tags
        this._loadSlideTags(slideId);
        console.warn(`[ViewerPanel] Loaded slide "${slideId}" in panel "${this.id}"`);
    }

    /**
     * Load and display auto-detected tags for the current slide
     * @param {string} slideId
     * @private
     */
    async _loadSlideTags(slideId) {
        try {
            const result = await apiService.getSlideTags(slideId);
            this._renderTagBadge(result.tags);
        } catch (err) {
            console.warn('[ViewerPanel] Tag fetch failed:', err);
        }
    }

    /**
     * Render tag badge in the viewer header
     * @param {Object} tags - Tags object with organ, stain, etc.
     * @private
     */
    _renderTagBadge(tags) {
        // Remove existing badge
        const existing = this.element.querySelector('.viewer-panel-tags');
        if (existing) {
            existing.remove();
        }

        const parts = [tags.organ, tags.stain, tags.pathology].filter(Boolean);
        if (parts.length === 0) {
            return;
        }

        const badge = document.createElement('div');
        badge.className = 'viewer-panel-tags';
        badge.textContent = parts.join(' \u2014 ');

        const header = this.element.querySelector('.viewer-panel-header');
        if (header) {
            header.appendChild(badge);
        }
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

        // Switch annotation context to this panel's slide
        if (active && this.slideId) {
            annotationStore.setSlide(this.slideId);
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
            viewerState: this.viewer ? this.viewer.getState() : null,
        };
    }

    /**
     * Destroy the panel
     */
    destroy() {
        console.warn(`[ViewerPanel] Destroying panel "${this.id}"`);

        // Unsubscribe from event listeners
        this._unsubscribers.forEach(unsubscribe => unsubscribe());
        this._unsubscribers = [];

        // Destroy ML panel and tabs container
        if (this.mlPanel) {
            this.mlPanel.destroy();
            this.mlPanel = null;
        }
        if (this.cellCountingPanel) {
            this.cellCountingPanel.destroy();
            this.cellCountingPanel = null;
        }
        if (this.clusteringPanel) {
            this.clusteringPanel.destroy();
            this.clusteringPanel = null;
        }
        if (this.mlTabsContainer) {
            this.mlTabsContainer.destroy();
            this.mlTabsContainer = null;
        }

        // Destroy scale bar
        if (this.scaleBar) {
            this.scaleBar.destroy();
            this.scaleBar = null;
        }

        // Destroy heatmap overlay
        if (this.heatmapOverlay) {
            this.heatmapOverlay.destroy();
            this.heatmapOverlay = null;
        }

        // Destroy annotation components
        if (this.annotationLayer) {
            this.annotationLayer.destroy();
            this.annotationLayer = null;
        }
        if (this.drawingTools) {
            this.drawingTools.destroy();
            this.drawingTools = null;
        }
        if (this.detectionPanel) {
            this.detectionPanel.destroy();
            this.detectionPanel = null;
        }
        if (this.focusAssistPanel) {
            this.focusAssistPanel.destroy();
            this.focusAssistPanel = null;
        }
        if (this.similarityPanel) {
            this.similarityPanel.destroy();
            this.similarityPanel = null;
        }
        if (this.layerManager) {
            this.layerManager.destroy();
            this.layerManager = null;
        }
        if (this.countingPanel) {
            this.countingPanel.destroy();
            this.countingPanel = null;
        }
        if (this.qualityPanel) {
            this.qualityPanel.destroy();
            this.qualityPanel = null;
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
