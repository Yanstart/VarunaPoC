/**
 * CellMarkerOverlay - Canvas overlay for cell counting markers
 *
 * Renders colored dots on the viewer for positive/negative cells.
 * Follows the same canvas overlay pattern as ClusteringOverlay.
 *
 * @module components/CellMarkerOverlay
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

export class CellMarkerOverlay {
    /**
     * @param {import('../viewers/ViewerInstance.js').default} viewerInstance
     */
    constructor(viewerInstance) {
        this.viewerInstance = viewerInstance;
        this.viewer = viewerInstance._osdViewer || viewerInstance.viewer;

        this._cells = [];
        this._visible = false;
        this._opacity = 0.7;
        this._renderPending = false;
        this._unsubscribers = [];

        this._build();
        this._setupEventListeners();
    }

    _build() {
        this._container = document.createElement('div');
        this._container.className = 'cell-marker-overlay';
        this._container.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:260;';

        this._canvas = document.createElement('canvas');
        this._container.appendChild(this._canvas);
        this._ctx = this._canvas.getContext('2d');

        // Insert into viewer container
        const viewerEl = this.viewer?.container || this.viewer?.element;
        if (viewerEl) {
            viewerEl.appendChild(this._container);
        }
    }

    _setupEventListeners() {
        this._unsubscribers.push(
            eventBus.on(Events.CELL_COUNTING_COMPLETE, ({ result }) => {
                this._cells = result?.cells || [];
                if (this._visible) this._scheduleRender();
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.CELL_MARKERS_TOGGLE, ({ visible }) => {
                this._visible = visible;
                if (visible) {
                    this._scheduleRender();
                } else {
                    this._clear();
                }
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.CELL_MARKERS_OPACITY, ({ opacity }) => {
                this._opacity = opacity;
                if (this._visible) this._scheduleRender();
            }),
        );

        // OSD viewport handlers
        if (this.viewer) {
            this._boundViewportChange = () => this._scheduleRender();
            this.viewer.addHandler('viewport-change', this._boundViewportChange);
            this.viewer.addHandler('animation-finish', this._boundViewportChange);
            this.viewer.addHandler('resize', this._boundViewportChange);
        }
    }

    _scheduleRender() {
        if (this._renderPending) return;
        this._renderPending = true;
        requestAnimationFrame(() => {
            this._renderPending = false;
            this._render();
        });
    }

    _render() {
        if (!this._canvas || !this.viewer) return;

        const viewerEl = this.viewer.container || this.viewer.element;
        if (!viewerEl) return;

        const w = viewerEl.clientWidth;
        const h = viewerEl.clientHeight;

        if (this._canvas.width !== w || this._canvas.height !== h) {
            this._canvas.width = w;
            this._canvas.height = h;
        }
        this._canvas.style.width = w + 'px';
        this._canvas.style.height = h + 'px';

        this._ctx.clearRect(0, 0, w, h);

        if (!this._visible || !this._cells.length) return;

        const tiledImage = this.viewer.world.getItemAt(0);
        if (!tiledImage) return;

        const viewport = this.viewer.viewport;
        const zoom = viewport.getZoom(true);
        const radius = Math.max(2, Math.min(8, zoom * 3));

        this._ctx.globalAlpha = this._opacity;

        for (const cell of this._cells) {
            // Convert slide pixel coords -> viewport -> viewer element coords
            const vp = tiledImage.imageToViewportCoordinates(cell.x, cell.y);
            const pt = viewport.viewportToViewerElementCoordinates(vp);

            // Skip off-screen cells
            if (pt.x < -radius || pt.x > w + radius || pt.y < -radius || pt.y > h + radius) {
                continue;
            }

            this._ctx.beginPath();
            this._ctx.arc(pt.x, pt.y, radius, 0, Math.PI * 2);
            this._ctx.fillStyle = cell.positive ? '#22c55e' : '#3b82f6';
            this._ctx.fill();
        }

        this._ctx.globalAlpha = 1;
    }

    _clear() {
        if (this._canvas && this._ctx) {
            this._ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
        }
    }

    clear() {
        this._cells = [];
        this._visible = false;
        this._clear();
    }

    destroy() {
        for (const unsub of this._unsubscribers) {
            if (typeof unsub === 'function') unsub();
        }
        this._unsubscribers = [];

        if (this.viewer && this._boundViewportChange) {
            this.viewer.removeHandler('viewport-change', this._boundViewportChange);
            this.viewer.removeHandler('animation-finish', this._boundViewportChange);
            this.viewer.removeHandler('resize', this._boundViewportChange);
        }

        if (this._container && this._container.parentNode) {
            this._container.parentNode.removeChild(this._container);
        }
        this._container = null;
        this._canvas = null;
        this._ctx = null;
    }
}
