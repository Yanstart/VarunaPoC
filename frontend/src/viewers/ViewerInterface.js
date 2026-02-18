/**
 * ViewerInterface — Abstract interface for slide viewers.
 * Implementations: OSDViewerAdapter (OpenSeadragon), CornerstoneViewerAdapter (future)
 */
export class ViewerInterface {
    constructor() {
        if (new.target === ViewerInterface) {
            throw new Error('ViewerInterface is abstract and cannot be instantiated directly');
        }
    }

    // === Navigation ===
    /** Pan to coordinates (slide pixel space) */
    panTo(x, y) { throw new Error('Not implemented'); }

    /** Zoom to a specific level */
    zoomTo(level) { throw new Error('Not implemented'); }

    /** Fit the entire slide in view */
    fitBounds() { throw new Error('Not implemented'); }

    // === Rendering ===
    /** Set the tile source for the viewer */
    setSource(tileSource) { throw new Error('Not implemented'); }

    /** Add an HTML overlay element */
    addOverlay(element, location) { throw new Error('Not implemented'); }

    /** Remove an overlay */
    removeOverlay(element) { throw new Error('Not implemented'); }

    // === Events ===
    /** Register event listener */
    on(event, callback) { throw new Error('Not implemented'); }

    /** Remove event listener */
    off(event, callback) { throw new Error('Not implemented'); }

    // === State ===
    /** Get current viewport bounds */
    getViewport() { throw new Error('Not implemented'); }

    /** Set viewport bounds */
    setViewport(bounds) { throw new Error('Not implemented'); }

    /** Get current zoom level */
    getZoom() { throw new Error('Not implemented'); }

    // === Lifecycle ===
    /** Destroy the viewer and clean up resources */
    destroy() { throw new Error('Not implemented'); }

    // === Standard Events ===
    static Events = {
        ZOOM_CHANGED: 'viewer:zoom-changed',
        PAN_CHANGED: 'viewer:pan-changed',
        VIEWPORT_CHANGED: 'viewer:viewport-changed',
        TILE_LOADED: 'viewer:tile-loaded',
        READY: 'viewer:ready',
        ERROR: 'viewer:error',
    };
}
