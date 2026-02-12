/**
 * HeatmapOverlay - Heatmap visualization overlay for OpenSeadragon
 *
 * Renders ML-generated attention heatmaps as a semi-transparent overlay
 * on the slide viewer, allowing pathologists to see model attention areas.
 *
 * @module components/HeatmapOverlay
 */

import OpenSeadragon from 'openseadragon';
import { apiService } from '../services/ApiService.js';
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

/**
 * HeatmapOverlay component
 */
class HeatmapOverlay {
    /**
     * Create HeatmapOverlay
     * @param {Object} viewerInstance - OpenSeadragon viewer instance wrapper
     * @param {Object} options - Configuration options
     */
    constructor(viewerInstance, options = {}) {
        this.viewerInstance = viewerInstance;
        this.viewer = viewerInstance.viewer; // OSD viewer
        this.viewerId = viewerInstance.id;

        // State
        this.slideId = null;
        this.predictionClass = null;
        this.heatmapData = null;
        this.isVisible = false;
        this.opacity = options.opacity || 0.5;
        this.colormap = options.colormap || 'jet';
        this.isLoading = false;

        // Canvas overlay
        this.canvas = null;
        this.ctx = null;
        this.overlayElement = null;

        /** @type {HTMLImageElement|null} Cached decoded heatmap image */
        this._cachedImage = null;

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

        /** @type {boolean} Deduplication flag for requestAnimationFrame */
        this._renderPending = false;

        this._boundRender = this._onViewportChange.bind(this);
        this._boundResize = this._onResize.bind(this);

        this._setupEventListeners();
    }

    /**
     * Setup event listeners
     * @private
     */
    _setupEventListeners() {
        // Listen for heatmap toggle - Store unsubscribe functions
        this._unsubscribers.push(
            eventBus.on(Events.ML_HEATMAP_TOGGLE, (data) => {
                if (data.viewerId === this.viewerId) {
                    if (data.visible) {
                        this.show(data.slideId, data.predictionClass, data.opacity);
                    } else {
                        this.hide();
                    }
                }
            }),
        );

        // Listen for opacity changes
        this._unsubscribers.push(
            eventBus.on(Events.ML_HEATMAP_OPACITY_CHANGE, (data) => {
                if (data.viewerId === this.viewerId) {
                    this.setOpacity(data.opacity);
                }
            }),
        );

        // Listen for viewport changes to update overlay position
        if (this.viewer) {
            this.viewer.addHandler('viewport-change', this._boundRender);
            this.viewer.addHandler('animation-finish', this._boundRender);
            this.viewer.addHandler('resize', this._boundResize);
        }
    }

    /**
     * Show heatmap overlay
     * @param {string} slideId - Slide ID
     * @param {string} predictionClass - Target class
     * @param {number} [opacity=0.5] - Opacity (0-1)
     */
    async show(slideId, predictionClass, opacity = 0.5) {
        if (this.isLoading) {return;}

        this.slideId = slideId;
        this.predictionClass = predictionClass;
        this.opacity = opacity;
        this.isLoading = true;
        this._cachedImage = null;

        eventBus.emit(Events.ML_HEATMAP_LOADING, {
            viewerId: this.viewerId,
            slideId,
        });

        try {
            // Fetch heatmap from API
            const result = await apiService.generateHeatmap(
                slideId,
                predictionClass,
                { resolutionLevel: 2, colormap: this.colormap },
            );

            this.heatmapData = result;

            // Pre-load and cache the heatmap image
            this._cachedImage = await this._loadHeatmapImage();

            // Create overlay if needed
            if (!this.overlayElement) {
                this._createOverlay();
            }

            // Render heatmap
            this._resizeCanvas();
            this._renderHeatmap();

            this.isVisible = true;
            this.overlayElement.style.display = 'block';
            this.overlayElement.style.opacity = this.opacity;

            eventBus.emit(Events.ML_HEATMAP_READY, {
                viewerId: this.viewerId,
                slideId,
            });

        } catch (error) {
            console.error('Failed to load heatmap:', error);

            eventBus.emit(Events.ML_HEATMAP_ERROR, {
                viewerId: this.viewerId,
                slideId,
                error: error.message,
            });
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Hide heatmap overlay
     */
    hide() {
        this.isVisible = false;
        if (this.overlayElement) {
            this.overlayElement.style.display = 'none';
        }
    }

    /**
     * Set heatmap opacity
     * @param {number} opacity - Opacity (0-1)
     */
    setOpacity(opacity) {
        this.opacity = opacity;
        if (this.overlayElement) {
            this.overlayElement.style.opacity = opacity;
        }
    }

    /**
     * Create canvas overlay element
     * @private
     */
    _createOverlay() {
        // Create container
        this.overlayElement = document.createElement('div');
        this.overlayElement.className = 'heatmap-overlay';
        this.overlayElement.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: ${this.opacity};
            z-index: 150;
            display: none;
            overflow: hidden;
        `;

        // Create canvas
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'heatmap-canvas';
        this.canvas.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        `;

        this.overlayElement.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        // Add to viewer container
        const container = this.viewer.container;
        container.appendChild(this.overlayElement);

        // Set initial canvas size
        this._resizeCanvas();
    }

    /**
     * Resize canvas to match viewer container
     * @private
     */
    _resizeCanvas() {
        if (!this.canvas || !this.viewer) {return;}

        const container = this.viewer.container;
        const w = container.clientWidth;
        const h = container.clientHeight;

        if (this.canvas.width !== w || this.canvas.height !== h) {
            this.canvas.width = w;
            this.canvas.height = h;
        }
    }

    /**
     * Render heatmap to canvas using cached image
     * @private
     */
    _renderHeatmap() {
        if (!this._cachedImage || !this.ctx || !this.viewer || !this.heatmapData) {return;}

        // Validate coords BEFORE clearing canvas to avoid blank frame
        const tiledImage = this.viewer.world.getItemAt(0);
        if (!tiledImage) {return;}

        const imageBounds = tiledImage.getBounds(true);

        const topLeft = this.viewer.viewport.viewportToViewerElementCoordinates(
            new OpenSeadragon.Point(imageBounds.x, imageBounds.y),
        );
        const bottomRight = this.viewer.viewport.viewportToViewerElementCoordinates(
            new OpenSeadragon.Point(
                imageBounds.x + imageBounds.width,
                imageBounds.y + imageBounds.height,
            ),
        );

        const destX = topLeft.x;
        const destY = topLeft.y;
        const destWidth = bottomRight.x - topLeft.x;
        const destHeight = bottomRight.y - topLeft.y;

        if (destWidth <= 0 || destHeight <= 0) {return;}

        // Only now: clear + draw
        const { canvas, ctx } = this;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(this._cachedImage, destX, destY, destWidth, destHeight);
    }

    /**
     * Load heatmap as image (called once, result is cached)
     * @returns {Promise<HTMLImageElement|null>}
     * @private
     */
    async _loadHeatmapImage() {
        if (!this.heatmapData) {return null;}

        // Check if we have base64 image data
        if (this.heatmapData.heatmap_base64) {
            return new Promise((resolve) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = () => {
                    console.error('[HeatmapOverlay] Failed to decode base64 image');
                    resolve(null);
                };
                img.src = `data:image/png;base64,${this.heatmapData.heatmap_base64}`;
            });
        }

        // If we have raw heatmap array, render to image
        if (this.heatmapData.heatmap) {
            return this._arrayToImage(this.heatmapData.heatmap);
        }

        return null;
    }

    /**
     * Convert heatmap array to image using colormap
     * @param {Array} heatmapArray - 2D heatmap values (0-1)
     * @returns {Promise<HTMLImageElement>}
     * @private
     */
    async _arrayToImage(heatmapArray) {
        // Create temporary canvas
        const tempCanvas = document.createElement('canvas');
        const height = heatmapArray.length;
        const width = heatmapArray[0]?.length || 0;

        tempCanvas.width = width;
        tempCanvas.height = height;

        const ctx = tempCanvas.getContext('2d');
        const imageData = ctx.createImageData(width, height);

        // Apply colormap
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const value = heatmapArray[y][x];
                const color = this._valueToColor(value);
                const idx = (y * width + x) * 4;

                imageData.data[idx] = color.r;
                imageData.data[idx + 1] = color.g;
                imageData.data[idx + 2] = color.b;
                imageData.data[idx + 3] = color.a;
            }
        }

        ctx.putImageData(imageData, 0, 0);

        // Convert to image
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.src = tempCanvas.toDataURL();
        });
    }

    /**
     * Convert value to RGBA color using jet colormap
     * @param {number} value - Value between 0 and 1
     * @returns {{r: number, g: number, b: number, a: number}}
     * @private
     */
    _valueToColor(value) {
        const v = Math.max(0, Math.min(1, value));

        let r, g, b;

        if (v < 0.25) {
            r = 0;
            g = Math.round(4 * v * 255);
            b = 255;
        } else if (v < 0.5) {
            r = 0;
            g = 255;
            b = Math.round((1 - 4 * (v - 0.25)) * 255);
        } else if (v < 0.75) {
            r = Math.round(4 * (v - 0.5) * 255);
            g = 255;
            b = 0;
        } else {
            r = 255;
            g = Math.round((1 - 4 * (v - 0.75)) * 255);
            b = 0;
        }

        // Alpha based on value (low values more transparent)
        const a = Math.round(v * 200); // Max alpha 200 for overlay effect

        return { r, g, b, a };
    }

    /**
     * Handle viewport change - re-render heatmap at new position
     * @private
     */
    _onViewportChange() {
        if (!this.isVisible) {return;}
        if (this._renderPending) {return;}
        this._renderPending = true;
        requestAnimationFrame(() => {
            this._renderPending = false;
            this._renderHeatmap();
        });
    }

    /**
     * Handle container resize
     * @private
     */
    _onResize() {
        if (!this.isVisible) {return;}
        this._resizeCanvas();
        this._renderHeatmap();
    }

    /**
     * Destroy the overlay
     */
    destroy() {
        // Properly unsubscribe from all event listeners
        this._unsubscribers.forEach(unsubscribe => unsubscribe());
        this._unsubscribers = [];

        if (this.viewer) {
            this.viewer.removeHandler('viewport-change', this._boundRender);
            this.viewer.removeHandler('animation-finish', this._boundRender);
            this.viewer.removeHandler('resize', this._boundResize);
        }

        if (this.overlayElement) {
            this.overlayElement.remove();
        }

        this.canvas = null;
        this.ctx = null;
        this.heatmapData = null;
        this._cachedImage = null;
    }
}

export { HeatmapOverlay };
export default HeatmapOverlay;
