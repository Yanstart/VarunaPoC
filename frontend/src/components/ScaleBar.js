/**
 * ScaleBar - Dynamic physical scale bar for the slide viewer
 *
 * Displays a horizontal bar with a physical distance label (e.g. "200 um", "1 mm")
 * that updates on every zoom/viewport change. Uses MPP (microns per pixel) from
 * slide metadata to convert screen pixels to physical distances.
 *
 * Position: bottom-left of the viewer, above the magnification bar.
 *
 * @module components/ScaleBar
 */

/** Nice round numbers in micrometers for scale bar labels */
const NICE_LENGTHS_UM = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000];

/** Target bar width in screen pixels */
const TARGET_WIDTH_PX = 150;

class ScaleBar {
    /**
     * @param {OpenSeadragon.Viewer} viewer - The OSD viewer instance
     * @param {number|null} mpp - Microns per pixel at full resolution (null if unavailable)
     */
    constructor(viewer, mpp) {
        this.viewer = viewer;
        this.mpp = mpp;

        /** @type {HTMLElement|null} */
        this.element = null;

        /** @type {HTMLElement|null} */
        this._barEl = null;

        /** @type {HTMLElement|null} */
        this._labelEl = null;

        /** @type {Function|null} */
        this._boundHandler = null;

        this._createDOM();
        this._bindEvents();

        // Initial update after a short delay to let the viewer settle
        setTimeout(() => this.update(), 100);
    }

    /**
     * Create the scale bar DOM elements
     * @private
     */
    _createDOM() {
        this.element = document.createElement('div');
        this.element.className = 'scale-bar';
        this.element.setAttribute('aria-hidden', 'true');

        this._barEl = document.createElement('div');
        this._barEl.className = 'scale-bar__bar';

        this._labelEl = document.createElement('div');
        this._labelEl.className = 'scale-bar__label';
        this._labelEl.textContent = '';

        this.element.appendChild(this._barEl);
        this.element.appendChild(this._labelEl);
    }

    /**
     * Bind OSD viewport events
     * @private
     */
    _bindEvents() {
        this._boundHandler = () => this.update();
        this.viewer.addHandler('zoom', this._boundHandler);
        this.viewer.addHandler('open', this._boundHandler);
        this.viewer.addHandler('viewport-change', this._boundHandler);
        this.viewer.addHandler('resize', this._boundHandler);
    }

    /**
     * Update the scale bar display based on current zoom level
     */
    update() {
        if (!this.viewer || !this.viewer.viewport) {
            return;
        }

        const scale = this._calculateScale();
        if (!scale) {
            this.element.style.display = 'none';
            return;
        }

        this.element.style.display = '';
        this._barEl.style.width = scale.barWidthPx + 'px';
        this._labelEl.textContent = scale.label;
    }

    /**
     * Calculate the optimal scale bar size and label
     * @returns {{ barWidthPx: number, label: string }|null}
     * @private
     */
    _calculateScale() {
        if (!this.viewer.viewport) {
            return null;
        }

        const zoom = this.viewer.viewport.getZoom(true);
        if (!zoom || zoom <= 0) {
            return null;
        }

        // Get image dimensions
        const tiledImage = this.viewer.world.getItemAt(0);
        if (!tiledImage) {
            return null;
        }

        const imageWidth = tiledImage.getContentSize().x;
        const containerWidth = this.viewer.viewport.getContainerSize().x;

        if (!imageWidth || !containerWidth) {
            return null;
        }

        // At current zoom, 1 screen pixel = (imageWidth / containerWidth / zoom) image pixels
        const imagePixelsPerScreenPixel = imageWidth / containerWidth / zoom;

        if (this.mpp && this.mpp > 0) {
            // Physical distance per screen pixel in micrometers
            const umPerScreenPixel = imagePixelsPerScreenPixel * this.mpp;

            // Find the nice length whose bar width is closest to TARGET_WIDTH_PX
            let bestLength = NICE_LENGTHS_UM[0];
            let bestDiff = Infinity;

            for (const lengthUm of NICE_LENGTHS_UM) {
                const barPx = lengthUm / umPerScreenPixel;
                const diff = Math.abs(barPx - TARGET_WIDTH_PX);
                if (diff < bestDiff) {
                    bestDiff = diff;
                    bestLength = lengthUm;
                }
            }

            const barWidthPx = bestLength / umPerScreenPixel;

            // Format the label
            let label;
            if (bestLength >= 1000) {
                label = (bestLength / 1000) + ' mm';
            } else {
                label = bestLength + ' \u00b5m';
            }

            return { barWidthPx: Math.round(barWidthPx), label };
        } else {
            // Fallback: pixel units
            const pxPerScreenPixel = imagePixelsPerScreenPixel;
            const nicePixelLengths = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000];

            let bestLength = nicePixelLengths[0];
            let bestDiff = Infinity;

            for (const lengthPx of nicePixelLengths) {
                const barScreenPx = lengthPx / pxPerScreenPixel;
                const diff = Math.abs(barScreenPx - TARGET_WIDTH_PX);
                if (diff < bestDiff) {
                    bestDiff = diff;
                    bestLength = lengthPx;
                }
            }

            const barWidthPx = bestLength / pxPerScreenPixel;
            const label = bestLength.toLocaleString() + ' px';

            return { barWidthPx: Math.round(barWidthPx), label };
        }
    }

    /**
     * Update MPP value (e.g. after loading a new slide)
     * @param {number|null} mpp - New microns-per-pixel value
     */
    setMpp(mpp) {
        this.mpp = mpp;
        this.update();
    }

    /**
     * Clean up event listeners and DOM
     */
    destroy() {
        if (this.viewer && this._boundHandler) {
            this.viewer.removeHandler('zoom', this._boundHandler);
            this.viewer.removeHandler('open', this._boundHandler);
            this.viewer.removeHandler('viewport-change', this._boundHandler);
            this.viewer.removeHandler('resize', this._boundHandler);
        }
        this._boundHandler = null;

        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
        this._barEl = null;
        this._labelEl = null;
        this.viewer = null;
    }
}

export { ScaleBar };
export default ScaleBar;
