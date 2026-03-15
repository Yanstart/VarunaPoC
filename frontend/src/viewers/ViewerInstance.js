/**
 * ViewerInstance - OpenSeadragon wrapper class
 *
 * Encapsulates a single OpenSeadragon viewer instance with state management,
 * event handling, and slide loading capabilities. Designed for multi-viewer
 * scenarios where each instance is independent.
 *
 * @module viewers/ViewerInstance
 *
 * @example
 * const instance = new ViewerInstance('viewer-1', document.getElementById('container'));
 * await instance.loadSlide('abc123');
 * instance.on('viewportChange', (data) => console.log('Viewport:', data));
 */

import OpenSeadragon from 'openseadragon';
import { ViewerState, ViewerStates } from './ViewerState.js';
import { eventBus } from '../core/EventBus.js';
import { Events, OSD_CONFIG, API } from '../core/Constants.js';
import { authService } from '../services/AuthService.js';

/**
 * Generate unique ID for viewer instances
 * @returns {string} Unique ID
 */
function generateId() {
    return `viewer-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * ViewerInstance class - wrapper around OpenSeadragon viewer
 */
class ViewerInstance {
    /**
     * Create a new ViewerInstance
     * @param {string} [id] - Unique identifier (auto-generated if not provided)
     * @param {HTMLElement|string} container - DOM element or element ID
     * @param {Object} [options={}] - Configuration options
     * @param {boolean} [options.showNavigator=true] - Show mini-map
     * @param {boolean} [options.emitEvents=true] - Emit events to global EventBus
     */
    constructor(id, container, options = {}) {
        /**
         * Unique identifier for this viewer instance
         * @type {string}
         */
        this.id = id || generateId();

        /**
         * Container element reference
         * @type {HTMLElement}
         */
        this.container = typeof container === 'string'
            ? document.getElementById(container)
            : container;

        if (!this.container) {
            throw new Error(`ViewerInstance: Container not found for id "${id}"`);
        }

        /**
         * Configuration options
         * @type {Object}
         */
        this.options = {
            showNavigator: true,
            emitEvents: true,
            ...options,
        };

        /**
         * OpenSeadragon viewer instance
         * @type {OpenSeadragon.Viewer|null}
         * @private
         */
        this._osdViewer = null;

        /**
         * State machine for viewer lifecycle
         * @type {ViewerState}
         */
        this.state = new ViewerState();

        /**
         * Currently loaded slide ID
         * @type {string|null}
         */
        this.slideId = null;

        /**
         * Slide metadata (dimensions, levels, etc.)
         * @type {Object|null}
         */
        this.slideMetadata = null;

        /**
         * Local event listeners
         * @type {Map<string, Set<Function>>}
         * @private
         */
        this._listeners = new Map();

        /**
         * Bound event handlers (for removal)
         * @type {Object}
         * @private
         */
        this._boundHandlers = {};

        /**
         * Whether viewport events are suppressed (during sync)
         * @type {boolean}
         */
        this.suppressViewportEvents = false;

        // Initialize the viewer
        this._initialize();
    }

    /**
     * Initialize OpenSeadragon viewer
     * @private
     */
    _initialize() {
        // Create container div for OSD if needed
        if (!this.container.id) {
            this.container.id = `osd-container-${this.id}`;
        }

        // Create OpenSeadragon instance
        this._osdViewer = OpenSeadragon({
            id: this.container.id,

            // CDN for button icons
            prefixUrl: 'https://cdn.jsdelivr.net/npm/openseadragon@4.1/build/openseadragon/images/',

            // Mini-map (navigator)
            showNavigator: this.options.showNavigator,
            navigatorPosition: OSD_CONFIG.NAVIGATOR_POSITION,
            navigatorSizeRatio: OSD_CONFIG.NAVIGATOR_SIZE_RATIO,
            navigatorAutoFade: false,

            // Navigation controls
            showNavigationControl: true,
            navigationControlAnchor: OpenSeadragon.ControlAnchor.TOP_LEFT,
            showZoomControl: OSD_CONFIG.SHOW_ZOOM_CONTROL,
            showHomeControl: OSD_CONFIG.SHOW_HOME_CONTROL,
            showFullPageControl: OSD_CONFIG.SHOW_FULLSCREEN_CONTROL,

            // Constraints
            visibilityRatio: 1.0,
            constrainDuringPan: true,
            minZoomLevel: 0.5,
            maxZoomPixelRatio: OSD_CONFIG.MAX_ZOOM_PIXEL_RATIO,

            // Performance
            immediateRender: true,
            blendTime: OSD_CONFIG.BLEND_TIME,
            animationTime: OSD_CONFIG.ANIMATION_TIME,

            // Auth: send Bearer token with tile requests
            loadTilesWithAjax: true,
            ajaxHeaders: authService.accessToken
                ? { 'Authorization': `Bearer ${authService.accessToken}` }
                : {},

            // No initial tile source
            tileSources: null,
        });

        // Bind event handlers
        this._bindEventHandlers();

        // Update OSD auth headers when token is silently refreshed
        this._boundHandlers.tokenRefreshed = ({ accessToken }) => {
            if (this._osdViewer && accessToken) {
                this._osdViewer.ajaxHeaders = { 'Authorization': `Bearer ${accessToken}` };
                console.info(`[ViewerInstance:${this.id}] Auth headers updated after token refresh`);
            }
        };
        eventBus.on(Events.AUTH_TOKEN_REFRESHED, this._boundHandlers.tokenRefreshed);

        // Accessibility: label the navigator mini-map
        if (this._osdViewer.navigator && this._osdViewer.navigator.element) {
            this._osdViewer.navigator.element.setAttribute('aria-label', 'Mini-carte de navigation');
            this._osdViewer.navigator.element.setAttribute('role', 'img');
        }

        // Emit creation event
        this._emitGlobal(Events.VIEWER_CREATED, { viewerId: this.id });

        console.warn(`[ViewerInstance] Created viewer "${this.id}"`);
    }

    /**
     * Bind OpenSeadragon event handlers
     * @private
     */
    _bindEventHandlers() {
        // Viewport change handler
        this._boundHandlers.viewportChange = (_event) => {
            if (!this.suppressViewportEvents && this.state.isReady) {
                const viewport = this.getViewport();
                this._emit('viewportChange', viewport);
                this._emitGlobal(Events.VIEWER_VIEWPORT_CHANGE, {
                    viewerId: this.id,
                    viewport,
                });
            }
        };

        // Pan handler
        this._boundHandlers.pan = (_event) => {
            if (!this.suppressViewportEvents && this.state.isReady) {
                const viewport = this.getViewport();
                this._emit('pan', viewport);
                this._emitGlobal(Events.VIEWER_PAN, {
                    viewerId: this.id,
                    viewport,
                });
            }
        };

        // Zoom handler
        this._boundHandlers.zoom = (event) => {
            if (!this.suppressViewportEvents && this.state.isReady) {
                const data = {
                    zoom: event.zoom,
                    viewport: this.getViewport(),
                };
                this._emit('zoom', data);
                this._emitGlobal(Events.VIEWER_ZOOM, {
                    viewerId: this.id,
                    ...data,
                });
            }
        };

        // Open handler (slide loaded)
        this._boundHandlers.open = () => {
            this.state.transitionTo(ViewerStates.READY);
            this._emit('ready', { slideId: this.slideId });
            this._emitGlobal(Events.SLIDE_LOADED, {
                viewerId: this.id,
                slideId: this.slideId,
            });
            console.warn(`[ViewerInstance] Slide loaded in viewer "${this.id}"`);
        };

        // Error handler
        this._boundHandlers.openFailed = (event) => {
            const error = new Error(event.message || 'Failed to open tile source');
            this.state.transitionTo(ViewerStates.ERROR, { error });
            this._emit('error', { error, slideId: this.slideId });
            this._emitGlobal(Events.SLIDE_ERROR, {
                viewerId: this.id,
                slideId: this.slideId,
                error: error.message,
            });
            console.error(`[ViewerInstance] Error in viewer "${this.id}":`, error);
        };

        // Attach handlers to OSD
        this._osdViewer.addHandler('viewport-change', this._boundHandlers.viewportChange);
        this._osdViewer.addHandler('pan', this._boundHandlers.pan);
        this._osdViewer.addHandler('zoom', this._boundHandlers.zoom);
        this._osdViewer.addHandler('open', this._boundHandlers.open);
        this._osdViewer.addHandler('open-failed', this._boundHandlers.openFailed);
    }

    /**
     * Load a slide into this viewer
     * @param {string} slideId - Unique slide identifier
     * @returns {Promise<void>}
     * @throws {Error} If slide loading fails
     */
    async loadSlide(slideId) {
        if (!slideId) {
            throw new Error('ViewerInstance.loadSlide: slideId is required');
        }

        // If already loading or same slide, skip
        if (this.state.isLoading) {
            console.warn(`[ViewerInstance] Already loading in viewer "${this.id}"`);
            return;
        }

        if (this.slideId === slideId && this.state.isReady) {
            console.warn(`[ViewerInstance] Slide "${slideId}" already loaded in viewer "${this.id}"`);
            return;
        }

        // Transition to loading state
        this.state.transitionTo(ViewerStates.LOADING);
        this._emit('loading', { slideId });
        this._emitGlobal(Events.SLIDE_LOADING, { viewerId: this.id, slideId });

        try {
            // Fetch DZI metadata
            console.warn(`[ViewerInstance] Loading DZI metadata for slide "${slideId}"`);
            const headers = {};
            if (authService.accessToken) {
                headers['Authorization'] = `Bearer ${authService.accessToken}`;
            }
            const response = await fetch(`${API.BASE_URL}/api/v1/slides/${slideId}/dzi.json`, { headers });

            if (!response.ok) {
                throw new Error(`Failed to load DZI metadata: ${response.statusText}`);
            }

            const dziMetadata = await response.json();
            this.slideMetadata = dziMetadata;
            this.slideId = slideId;

            console.warn('[ViewerInstance] DZI metadata loaded:', dziMetadata);

            // Create tile source
            const tileSource = this._createTileSource(slideId, dziMetadata);

            // Update auth headers before opening
            if (authService.accessToken) {
                this._osdViewer.ajaxHeaders = {
                    'Authorization': `Bearer ${authService.accessToken}`,
                };
            }

            // Open in OpenSeadragon
            this._osdViewer.open(tileSource);

        } catch (error) {
            this.state.transitionTo(ViewerStates.ERROR, { error });
            this._emit('error', { error, slideId });
            this._emitGlobal(Events.SLIDE_ERROR, {
                viewerId: this.id,
                slideId,
                error: error.message,
            });
            throw error;
        }
    }

    /**
     * Create OpenSeadragon tile source from DZI metadata
     * @param {string} slideId - Slide ID
     * @param {Object} metadata - DZI metadata from backend
     * @returns {Object} OpenSeadragon tile source configuration
     * @private
     */
    _createTileSource(slideId, metadata) {
        const baseUrl = API.BASE_URL;

        return {
            // Level 0 dimensions (highest resolution)
            width: metadata.width,
            height: metadata.height,

            // Tile configuration
            tileSize: metadata.tile_size,
            tileOverlap: metadata.overlap,

            // Pyramid levels
            minLevel: 0,
            maxLevel: metadata.levels - 1,

            /**
             * Get scale factor for a level
             * Maps OSD level to OpenSlide downsample
             */
            getLevelScale: function (level) {
                const openslideLevel = metadata.levels - 1 - level;
                const downsample = metadata.level_downsamples[openslideLevel];
                return 1.0 / downsample;
            },

            /**
             * Get number of tiles at a level
             */
            getNumTiles: function (level) {
                const openslideLevel = metadata.levels - 1 - level;
                const [width, height] = metadata.level_dimensions[openslideLevel];

                return {
                    x: Math.ceil(width / metadata.tile_size),
                    y: Math.ceil(height / metadata.tile_size),
                };
            },

            /**
             * Get tile URL
             */
            getTileUrl: function (level, x, y) {
                const openslideLevel = metadata.levels - 1 - level;
                return `${baseUrl}/api/v1/slides/${slideId}/tiles/${openslideLevel}/${x}_${y}.jpg`;
            },
        };
    }

    /**
     * Unload current slide
     */
    unloadSlide() {
        if (this._osdViewer && this._osdViewer.world.getItemCount() > 0) {
            this._osdViewer.world.removeAll();
        }

        const previousSlideId = this.slideId;
        this.slideId = null;
        this.slideMetadata = null;
        this.state.transitionTo(ViewerStates.IDLE, { force: true });

        this._emit('unloaded', { slideId: previousSlideId });
        this._emitGlobal(Events.SLIDE_UNLOADED, {
            viewerId: this.id,
            slideId: previousSlideId,
        });

        console.warn(`[ViewerInstance] Slide unloaded from viewer "${this.id}"`);
    }

    /**
     * Public accessor for the underlying OpenSeadragon viewer
     * @type {OpenSeadragon.Viewer|null}
     */
    get viewer() {
        return this._osdViewer;
    }

    /**
     * Get current viewport bounds (normalized 0-1 coordinates)
     * @returns {Object} Viewport bounds { x, y, width, height, zoom }
     */
    getViewport() {
        if (!this._osdViewer || !this._osdViewer.viewport) {
            return null;
        }

        const bounds = this._osdViewer.viewport.getBounds();
        const zoom = this._osdViewer.viewport.getZoom();

        return {
            x: bounds.x,
            y: bounds.y,
            width: bounds.width,
            height: bounds.height,
            zoom: zoom,
        };
    }

    /**
     * Get viewport bounds in slide pixel coordinates.
     *
     * Converts OpenSeadragon normalized viewport coords to absolute pixel
     * coordinates using tiledImage.viewportToImageCoordinates() for precision.
     *
     * @returns {Object|null} { x, y, width, height } in slide pixels, or null
     */
    getViewportPixelBounds() {
        if (!this._osdViewer || !this.slideMetadata) return null;
        const tiledImage = this._osdViewer.world.getItemAt(0);
        if (!tiledImage) return null;

        const bounds = this._osdViewer.viewport.getBounds();
        const tl = tiledImage.viewportToImageCoordinates(bounds.x, bounds.y);
        const br = tiledImage.viewportToImageCoordinates(
            bounds.x + bounds.width, bounds.y + bounds.height,
        );

        return {
            x: Math.max(0, Math.round(tl.x)),
            y: Math.max(0, Math.round(tl.y)),
            width: Math.round(Math.abs(br.x - tl.x)),
            height: Math.round(Math.abs(br.y - tl.y)),
        };
    }

    /**
     * Set viewport bounds (for sync)
     * @param {Object} viewport - Viewport bounds { x, y, width, height }
     * @param {boolean} [immediately=false] - Skip animation
     */
    setViewport(viewport, immediately = false) {
        if (!this._osdViewer || !this._osdViewer.viewport) {
            return;
        }

        // Suppress events during sync to avoid infinite loops
        this.suppressViewportEvents = true;

        const bounds = new OpenSeadragon.Rect(
            viewport.x,
            viewport.y,
            viewport.width,
            viewport.height,
        );

        this._osdViewer.viewport.fitBounds(bounds, immediately);

        // Re-enable events after animation
        setTimeout(() => {
            this.suppressViewportEvents = false;
        }, immediately ? 0 : OSD_CONFIG.ANIMATION_TIME * 1000);
    }

    /**
     * Pan to specific coordinates
     * @param {number} x - X coordinate (normalized)
     * @param {number} y - Y coordinate (normalized)
     * @param {boolean} [immediately=false] - Skip animation
     */
    panTo(x, y, immediately = false) {
        if (!this._osdViewer || !this._osdViewer.viewport) {
            return;
        }

        const point = new OpenSeadragon.Point(x, y);
        this._osdViewer.viewport.panTo(point, immediately);
    }

    /**
     * Zoom to specific level
     * @param {number} zoom - Zoom level
     * @param {boolean} [immediately=false] - Skip animation
     */
    zoomTo(zoom, immediately = false) {
        if (!this._osdViewer || !this._osdViewer.viewport) {
            return;
        }

        this._osdViewer.viewport.zoomTo(zoom, null, immediately);
    }

    /**
     * Reset view to home position (full slide view)
     */
    resetView() {
        if (!this._osdViewer || !this._osdViewer.viewport) {
            return;
        }

        this._osdViewer.viewport.goHome();
    }

    /**
     * Get current zoom level
     * @returns {number} Current zoom
     */
    getZoom() {
        if (!this._osdViewer || !this._osdViewer.viewport) {
            return 1;
        }
        return this._osdViewer.viewport.getZoom();
    }

    /**
     * Register local event listener
     * @param {string} event - Event name
     * @param {Function} callback - Handler function
     * @returns {Function} Unsubscribe function
     */
    on(event, callback) {
        if (!this._listeners.has(event)) {
            this._listeners.set(event, new Set());
        }
        this._listeners.get(event).add(callback);
        return () => this.off(event, callback);
    }

    /**
     * Remove local event listener
     * @param {string} event - Event name
     * @param {Function} callback - Handler function
     */
    off(event, callback) {
        const listeners = this._listeners.get(event);
        if (listeners) {
            listeners.delete(callback);
        }
    }

    /**
     * Emit local event
     * @param {string} event - Event name
     * @param {*} data - Event data
     * @private
     */
    _emit(event, data) {
        const listeners = this._listeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (e) {
                    console.error(`[ViewerInstance] Error in event handler for "${event}":`, e);
                }
            });
        }
    }

    /**
     * Emit event to global EventBus
     * @param {string} event - Event name
     * @param {*} data - Event data
     * @private
     */
    _emitGlobal(event, data) {
        if (this.options.emitEvents) {
            eventBus.emit(event, data);
        }
    }

    /**
     * Get state information
     * @returns {Object} Viewer state info
     */
    getState() {
        return {
            id: this.id,
            slideId: this.slideId,
            state: this.state.current,
            viewport: this.getViewport(),
            hasError: this.state.isError,
            error: this.state.error?.message || null,
        };
    }

    /**
     * Check if viewer is ready
     * @returns {boolean}
     */
    isReady() {
        return this.state.isReady;
    }

    /**
     * Get current optical-equivalent magnification.
     * Assumes 0.25 um/px at max resolution (40x objective equivalent).
     * @returns {number} Magnification value (e.g. 1, 2, 5, 10, 20, 40)
     */
    getOpticalMagnification() {
        if (!this._osdViewer || !this._osdViewer.viewport) {
            return 1;
        }
        const zoom = this._osdViewer.viewport.getZoom(true);
        const maxZoom = this._osdViewer.viewport.getMaxZoom();
        const ratio = zoom / maxZoom;
        const rawMag = ratio * 40;
        const objectives = [1, 2, 5, 10, 20, 40, 60, 100];
        let closest = objectives[0];
        for (const obj of objectives) {
            if (Math.abs(obj - rawMag) < Math.abs(closest - rawMag)) {
                closest = obj;
            }
        }
        return closest;
    }

    /**
     * Destroy the viewer instance
     * Cleans up resources and event handlers
     */
    destroy() {
        console.warn(`[ViewerInstance] Destroying viewer "${this.id}"`);

        // Transition to destroying state
        this.state.transitionTo(ViewerStates.DESTROYING, { force: true });

        // Remove OSD event handlers
        if (this._osdViewer) {
            this._osdViewer.removeHandler('viewport-change', this._boundHandlers.viewportChange);
            this._osdViewer.removeHandler('pan', this._boundHandlers.pan);
            this._osdViewer.removeHandler('zoom', this._boundHandlers.zoom);
            this._osdViewer.removeHandler('open', this._boundHandlers.open);
            this._osdViewer.removeHandler('open-failed', this._boundHandlers.openFailed);

            // Destroy OSD instance
            this._osdViewer.destroy();
            this._osdViewer = null;
        }

        // Remove global event listeners
        if (this._boundHandlers.tokenRefreshed) {
            eventBus.off(Events.AUTH_TOKEN_REFRESHED, this._boundHandlers.tokenRefreshed);
        }

        // Clear local listeners
        this._listeners.clear();
        this._boundHandlers = {};

        // Emit destruction event
        this._emitGlobal(Events.VIEWER_DESTROYED, { viewerId: this.id });

        // Clear references
        this.slideId = null;
        this.slideMetadata = null;
        this.container = null;

        console.warn(`[ViewerInstance] Viewer "${this.id}" destroyed`);
    }
}

export { ViewerInstance };
export default ViewerInstance;
