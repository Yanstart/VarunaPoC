/**
 * MagnificationBar - Floating magnification display badge
 *
 * Shows the current optical magnification (e.g., x10, x20, x40) as a small
 * floating badge in the viewer area bottom-left. Listens to OSD viewport zoom
 * events and calculates the nearest standard magnification.
 *
 * Formula:
 *   magnification = objective_power * (viewport_mpp / slide_mpp)
 *   where viewport_mpp = slide_mpp / viewer.viewport.getZoom(true)
 *
 * Simplifies to: magnification = objective_power * (1 / zoom) when mpp cancels.
 * Actual calculation uses ratio of current zoom to max zoom scaled by objective_power.
 *
 * @module components/MagnificationBar
 */

/** Standard magnification levels for snapping */
const STANDARD_MAGNIFICATIONS = [1, 2, 5, 10, 20, 40, 60, 100];

/** Default objective power when metadata is unavailable */
const DEFAULT_OBJECTIVE_POWER = 40;

/** Default microns-per-pixel when metadata is unavailable */
const DEFAULT_MPP = 0.25;

class MagnificationBar {
    /**
     * @param {OpenSeadragon.Viewer} osdViewer - The OSD viewer instance
     * @param {Object} [options={}] - Configuration options
     * @param {number} [options.objectivePower] - Objective power from slide metadata
     * @param {number} [options.slideMpp] - Slide microns-per-pixel from metadata
     */
    constructor(osdViewer, options = {}) {
        this.viewer = osdViewer;
        this.objectivePower = options.objectivePower || DEFAULT_OBJECTIVE_POWER;
        this.slideMpp = options.slideMpp || DEFAULT_MPP;

        /** @type {HTMLElement|null} */
        this.element = null;

        /** @type {Function|null} Bound handler reference for cleanup */
        this._boundHandler = null;

        this._createBadge();
        this._bindEvents();
    }

    /**
     * Create the badge DOM element
     * @private
     */
    _createBadge() {
        this.element = document.createElement('div');
        this.element.className = 'magnification-bar';
        this.element.textContent = '\u00d71';
    }

    /**
     * Bind OSD viewport zoom/change events
     * @private
     */
    _bindEvents() {
        this._boundHandler = () => this.update();
        this.viewer.addHandler('zoom', this._boundHandler);
        this.viewer.addHandler('open', this._boundHandler);
        this.viewer.addHandler('viewport-change', this._boundHandler);
    }

    /**
     * Calculate the current magnification and update the badge display
     */
    update() {
        if (!this.viewer || !this.viewer.viewport) {
            return;
        }

        const zoom = this.viewer.viewport.getZoom(true);
        const maxZoom = this.viewer.viewport.getMaxZoom();

        // ratio represents where we are in the zoom range (0 to 1 at max)
        const ratio = zoom / maxZoom;
        const rawMag = ratio * this.objectivePower;

        // Snap to nearest standard magnification
        const nearest = this._snapToNearest(rawMag);

        this.element.textContent = '\u00d7' + nearest;
        this.element.classList.toggle('magnification-bar--diagnostic', nearest >= 10);
    }

    /**
     * Find the nearest standard magnification value
     * @param {number} rawMag - Raw calculated magnification
     * @returns {number} Nearest standard magnification
     * @private
     */
    _snapToNearest(rawMag) {
        let closest = STANDARD_MAGNIFICATIONS[0];
        let minDiff = Math.abs(closest - rawMag);

        for (const std of STANDARD_MAGNIFICATIONS) {
            const diff = Math.abs(std - rawMag);
            if (diff < minDiff) {
                minDiff = diff;
                closest = std;
            }
        }
        return closest;
    }

    /**
     * Update slide metadata (e.g., after loading a new slide)
     * @param {Object} metadata - Slide metadata object
     */
    setMetadata(metadata) {
        if (metadata) {
            const props = metadata.properties || metadata;
            this.objectivePower = parseFloat(
                props['openslide.objective-power'] || DEFAULT_OBJECTIVE_POWER,
            );
            this.slideMpp = parseFloat(
                props['openslide.mpp-x'] || DEFAULT_MPP,
            );
        }
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
        }
        this._boundHandler = null;

        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
        this.viewer = null;
    }
}

export { MagnificationBar };
export default MagnificationBar;
