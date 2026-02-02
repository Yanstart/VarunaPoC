/**
 * Viewer Component - Thin wrapper for backward compatibility
 *
 * This module provides legacy API compatibility with the new ViewerInstance
 * architecture. Existing code can continue using initViewer() and
 * loadSlideWithTiles() while the new multi-viewer system is used internally.
 *
 * NEW ARCHITECTURE:
 * For new code, prefer using ViewerManager and ViewerInstance directly:
 *   import { viewerManager } from '../viewers/ViewerManager.js';
 *   const viewer = viewerManager.createViewer('id', container);
 *   await viewer.loadSlide(slideId);
 *
 * LEGACY API (maintained for compatibility):
 *   import { initViewer, loadSlideWithTiles } from './Viewer.js';
 *   const viewer = initViewer('element-id');
 *   await loadSlideWithTiles(viewer, slideId);
 *
 * @module components/Viewer
 */

import OpenSeadragon from 'openseadragon';
import { API_BASE } from '../utils/api.js';
import { viewerManager } from '../viewers/ViewerManager.js';
import { ViewerFactory } from '../viewers/ViewerFactory.js';

/**
 * Legacy viewer instance reference
 * Used to track the single viewer created via initViewer()
 * @type {import('../viewers/ViewerInstance.js').ViewerInstance|null}
 */
let legacyViewerInstance = null;

/**
 * Initialise viewer OpenSeadragon avec configuration pour tile streaming.
 *
 * @deprecated Prefer using ViewerManager.createViewer() for new code
 * @param {string} elementId - ID de l'element DOM container
 * @returns {OpenSeadragon.Viewer} Instance du viewer OpenSeadragon
 *
 * @example
 * // Legacy usage (still works)
 * const viewer = initViewer('viewer-container');
 *
 * // Recommended new usage
 * import { viewerManager } from '../viewers/ViewerManager.js';
 * const instance = viewerManager.createViewer('id', document.getElementById('viewer-container'));
 */
export function initViewer(elementId) {
    // Get container element
    const container = document.getElementById(elementId);

    if (!container) {
        throw new Error(`initViewer: Element with id "${elementId}" not found`);
    }

    // Create viewer via new architecture
    legacyViewerInstance = ViewerFactory.create('legacy-viewer', container, {
        showNavigator: true,
        preset: 'default'
    });

    // Register with manager
    if (!viewerManager.hasViewer(legacyViewerInstance.id)) {
        // The factory already adds to manager, but ensure it's tracked
        console.log('[Viewer] Legacy viewer created via new architecture');
    }

    // Return the internal OSD viewer for backward compatibility
    // Note: Direct OSD access is discouraged in new code
    return legacyViewerInstance._osdViewer;
}

/**
 * Charge une lame avec streaming de tuiles DZI.
 *
 * @deprecated Prefer using ViewerInstance.loadSlide() for new code
 * @param {OpenSeadragon.Viewer} viewer - Instance viewer OSD (from initViewer)
 * @param {string} slideId - ID unique de la lame
 * @returns {Promise<void>}
 *
 * @example
 * // Legacy usage (still works)
 * await loadSlideWithTiles(viewer, 'abc123');
 *
 * // Recommended new usage
 * await viewerInstance.loadSlide('abc123');
 */
export async function loadSlideWithTiles(viewer, slideId) {
    // If we have a legacy instance, use it
    if (legacyViewerInstance && legacyViewerInstance._osdViewer === viewer) {
        await legacyViewerInstance.loadSlide(slideId);
        return;
    }

    // Fallback: Original implementation for direct OSD usage
    // This path is taken when someone passes a raw OSD viewer
    console.warn('[Viewer] Using fallback tile loading (consider migrating to ViewerInstance)');

    try {
        // 1. Fetch DZI metadata
        console.log(`[Viewer] Loading DZI metadata for slide ${slideId}`);
        const response = await fetch(`${API_BASE}/api/slides/${slideId}/dzi.json`);

        if (!response.ok) {
            throw new Error(`Failed to load DZI metadata: ${response.statusText}`);
        }

        const dziMetadata = await response.json();
        console.log(`[Viewer] DZI metadata loaded:`, dziMetadata);

        // 2. Create tile source
        const tileSource = {
            width: dziMetadata.width,
            height: dziMetadata.height,
            tileSize: dziMetadata.tile_size,
            tileOverlap: dziMetadata.overlap,
            minLevel: 0,
            maxLevel: dziMetadata.levels - 1,

            getLevelScale: function(level) {
                const openslideLevel = dziMetadata.levels - 1 - level;
                const downsample = dziMetadata.level_downsamples[openslideLevel];
                return 1.0 / downsample;
            },

            getNumTiles: function(level) {
                const openslideLevel = dziMetadata.levels - 1 - level;
                const [width, height] = dziMetadata.level_dimensions[openslideLevel];

                return {
                    x: Math.ceil(width / dziMetadata.tile_size),
                    y: Math.ceil(height / dziMetadata.tile_size)
                };
            },

            getTileUrl: function(level, x, y) {
                const openslideLevel = dziMetadata.levels - 1 - level;
                return `${API_BASE}/api/slides/${slideId}/tiles/${openslideLevel}/${x}_${y}.jpg`;
            }
        };

        console.log(`[Viewer] Opening tile source (${dziMetadata.levels} levels)`);

        // 3. Open in viewer
        viewer.open(tileSource);

        viewer.addOnceHandler('open', () => {
            console.log('[Viewer] Slide opened successfully');
        });

    } catch (error) {
        console.error(`[Viewer] Error loading slide with tiles:`, error);
        throw error;
    }
}

/**
 * Charge overview simple (legacy - Phase 1).
 *
 * @deprecated Use ViewerInstance.loadSlide() which handles all cases
 * @param {OpenSeadragon.Viewer} viewer - Instance viewer
 * @param {string} overviewUrl - URL vers image overview (JPEG)
 */
export function loadOverview(viewer, overviewUrl) {
    console.log('[Viewer] Loading overview (legacy mode)');

    const tileSource = {
        type: 'image',
        url: overviewUrl
    };

    viewer.open(tileSource);
}

/**
 * Get the legacy viewer instance
 * @returns {import('../viewers/ViewerInstance.js').ViewerInstance|null}
 */
export function getLegacyViewer() {
    return legacyViewerInstance;
}

/**
 * Destroy the legacy viewer
 */
export function destroyLegacyViewer() {
    if (legacyViewerInstance) {
        legacyViewerInstance.destroy();
        legacyViewerInstance = null;
    }
}

// Re-export new architecture for convenience
export { viewerManager } from '../viewers/ViewerManager.js';
export { ViewerFactory } from '../viewers/ViewerFactory.js';
export { ViewerInstance } from '../viewers/ViewerInstance.js';
