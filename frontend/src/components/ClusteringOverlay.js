/**
 * ClusteringOverlay - Canvas overlay for morphological clustering visualization
 *
 * Renders colored tile rectangles on the OpenSeadragon viewer to show
 * cluster assignments from morphological clustering analysis.
 *
 * Follows HeatmapOverlay pattern: canvas overlay, OSD viewport sync.
 *
 * @module components/ClusteringOverlay
 */

import OpenSeadragon from 'openseadragon';
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

class ClusteringOverlay {
    /**
     * Create ClusteringOverlay
     * @param {Object} viewerInstance - OpenSeadragon viewer instance wrapper
     */
    constructor(viewerInstance) {
        this.viewerInstance = viewerInstance;
        this.viewer = viewerInstance.viewer; // OSD viewer
        this.viewerId = viewerInstance.id;

        // Data
        this.clusters = [];
        this.tileAssignments = [];
        this.gridWidth = 0;
        this.gridHeight = 0;

        // Cluster color lookup: clusterId -> color string
        this._clusterColors = {};

        // Visibility
        this.visibleClusters = new Set();
        this.opacity = 0.5;
        this.isVisible = false;

        // Canvas
        this.overlayElement = null;
        this.canvas = null;
        this.ctx = null;

        this._renderPending = false;
        this._boundRender = this._onViewportChange.bind(this);
        this._boundResize = this._onResize.bind(this);
        this._unsubscribers = [];

        this._setupEventListeners();
    }

    /**
     * Setup event listeners
     * @private
     */
    _setupEventListeners() {
        // Listen for clustering complete
        this._unsubscribers.push(
            eventBus.on(Events.CLUSTERING_COMPLETE, (data) => {
                this._onClusteringComplete(data);
            }),
        );

        // Listen for per-cluster visibility toggle
        this._unsubscribers.push(
            eventBus.on(Events.CLUSTERING_OVERLAY_TOGGLE, (data) => {
                if (data.visible) {
                    this.visibleClusters.add(data.clusterId);
                } else {
                    this.visibleClusters.delete(data.clusterId);
                }
                this._render();
            }),
        );

        // Listen for opacity changes
        this._unsubscribers.push(
            eventBus.on(Events.CLUSTERING_OVERLAY_OPACITY, (data) => {
                this.opacity = data.opacity;
                if (this.overlayElement) {
                    this.overlayElement.style.opacity = this.opacity;
                }
                this._render();
            }),
        );

        // Clear overlay on clustering error (prevents stuck overlay after 429)
        this._unsubscribers.push(
            eventBus.on(Events.CLUSTERING_ERROR, () => {
                this.clusters = [];
                this.tileAssignments = [];
                this.visibleClusters.clear();
                this._clusterColors = {};
                this._render();
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.ML_OVERLAYS_TOGGLE, ({ visible }) => {
                if (this.overlayElement) {
                    this.overlayElement.style.display = visible ? '' : 'none';
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
     * Handle clustering complete event
     * @param {Object} data - Clustering result
     * @private
     */
    _onClusteringComplete(data) {
        const result = data.result;
        if (!result) return;

        this.clusters = result.clusters || [];
        this.tileAssignments = result.tile_assignments || [];

        // Build cluster color lookup
        this._clusterColors = {};
        for (const cluster of this.clusters) {
            this._clusterColors[cluster.id] = cluster.color;
        }

        // Compute grid dimensions (max x+1, max y+1)
        this.gridWidth = 0;
        this.gridHeight = 0;
        for (const tile of this.tileAssignments) {
            if (tile.x + 1 > this.gridWidth) this.gridWidth = tile.x + 1;
            if (tile.y + 1 > this.gridHeight) this.gridHeight = tile.y + 1;
        }

        // Set all clusters visible
        this.visibleClusters.clear();
        for (const cluster of this.clusters) {
            this.visibleClusters.add(cluster.id);
        }

        // Create overlay if needed
        if (!this.overlayElement) {
            this._createOverlay();
        }

        this.isVisible = true;
        this.overlayElement.style.display = 'block';
        this.overlayElement.style.opacity = this.opacity;

        this._resizeCanvas();
        this._render();
    }

    /**
     * Create canvas overlay element
     * @private
     */
    _createOverlay() {
        // Create container
        this.overlayElement = document.createElement('div');
        this.overlayElement.className = 'clustering-overlay';
        this.overlayElement.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: ${this.opacity};
            z-index: 140;
            display: none;
            overflow: hidden;
        `;

        // Create canvas
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'clustering-canvas';
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
        if (!this.canvas || !this.viewer) return;

        const container = this.viewer.container;
        const w = container.clientWidth;
        const h = container.clientHeight;

        if (this.canvas.width !== w || this.canvas.height !== h) {
            this.canvas.width = w;
            this.canvas.height = h;
        }
    }

    /**
     * Render cluster tile rectangles to canvas
     * @private
     */
    _render() {
        if (!this.canvas || !this.ctx || !this.viewer) return;
        if (this.tileAssignments.length === 0 || this.gridWidth === 0 || this.gridHeight === 0) return;

        const tiledImage = this.viewer.world.getItemAt(0);
        if (!tiledImage) return;

        const imageBounds = tiledImage.getBounds(true);
        const tileWidth = imageBounds.width / this.gridWidth;
        const tileHeight = imageBounds.height / this.gridHeight;

        // Clear canvas
        const { canvas, ctx } = this;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw each tile
        for (const tile of this.tileAssignments) {
            // Skip if cluster not visible
            if (!this.visibleClusters.has(tile.cluster_id)) continue;

            // Get cluster color
            const color = this._clusterColors[tile.cluster_id];
            if (!color) continue;

            // Compute tile rect in viewport coords
            const tileX = imageBounds.x + tile.x * tileWidth;
            const tileY = imageBounds.y + tile.y * tileHeight;

            const topLeft = this.viewer.viewport.viewportToViewerElementCoordinates(
                new OpenSeadragon.Point(tileX, tileY),
            );
            const bottomRight = this.viewer.viewport.viewportToViewerElementCoordinates(
                new OpenSeadragon.Point(tileX + tileWidth, tileY + tileHeight),
            );

            const destX = topLeft.x;
            const destY = topLeft.y;
            const destWidth = bottomRight.x - topLeft.x;
            const destHeight = bottomRight.y - topLeft.y;

            if (destWidth <= 0 || destHeight <= 0) continue;

            // Parse color and draw with alpha
            ctx.fillStyle = this._colorWithAlpha(color, 0.4);
            ctx.fillRect(destX, destY, destWidth, destHeight);
        }
    }

    /**
     * Convert a CSS color to rgba with specified alpha
     * @param {string} color - CSS color (hex or rgb)
     * @param {number} alpha - Alpha value (0-1)
     * @returns {string} rgba color string
     * @private
     */
    _colorWithAlpha(color, alpha) {
        // Handle hex colors
        if (color.startsWith('#')) {
            const hex = color.slice(1);
            let r, g, b;
            if (hex.length === 3) {
                r = parseInt(hex[0] + hex[0], 16);
                g = parseInt(hex[1] + hex[1], 16);
                b = parseInt(hex[2] + hex[2], 16);
            } else {
                r = parseInt(hex.slice(0, 2), 16);
                g = parseInt(hex.slice(2, 4), 16);
                b = parseInt(hex.slice(4, 6), 16);
            }
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        // Handle rgb() format
        if (color.startsWith('rgb(')) {
            return color.replace('rgb(', 'rgba(').replace(')', `, ${alpha})`);
        }
        // Handle rgba() format - replace existing alpha
        if (color.startsWith('rgba(')) {
            return color.replace(/,\s*[\d.]+\)$/, `, ${alpha})`);
        }
        // Fallback: return as-is
        return color;
    }

    /**
     * Handle viewport change - re-render at new position
     * @private
     */
    _onViewportChange() {
        if (!this.isVisible) return;
        if (this._renderPending) return;
        this._renderPending = true;
        requestAnimationFrame(() => {
            this._renderPending = false;
            this._render();
        });
    }

    /**
     * Handle container resize
     * @private
     */
    _onResize() {
        if (!this.isVisible) return;
        this._resizeCanvas();
        this._render();
    }

    /**
     * Clear overlay and reset data
     */
    clear() {
        this.isVisible = false;
        this.clusters = [];
        this.tileAssignments = [];
        this.gridWidth = 0;
        this.gridHeight = 0;
        this._clusterColors = {};
        this.visibleClusters.clear();

        if (this.overlayElement) {
            this.overlayElement.style.display = 'none';
        }
        if (this.ctx && this.canvas) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    /**
     * Destroy the overlay
     */
    destroy() {
        // Unsubscribe from all event listeners
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
        this.clusters = [];
        this.tileAssignments = [];
        this._clusterColors = {};
    }
}

export { ClusteringOverlay };
export default ClusteringOverlay;
