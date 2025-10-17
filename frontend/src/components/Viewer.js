/**
 * OpenSeadragon Viewer Component
 *
 * PRINCIPE SIMPLE - Phase 1:
 * On utilise OpenSeadragon en mode "image simple" (type: 'image').
 * Pas de DZI complexe, pas de tiling manuel.
 * L'overview s'affiche dans la mini-map (navigator).
 *
 * Documentation:
 *   - OpenSeadragon Docs: https://openseadragon.github.io/docs/
 *   - Options: https://openseadragon.github.io/docs/OpenSeadragon.html#.Options
 *   - Image simple: https://openseadragon.github.io/examples/tilesource-image/
 */

import OpenSeadragon from 'openseadragon';

/**
 * Initialise viewer OpenSeadragon.
 *
 * @param {string} elementId - ID de l'élément DOM container
 * @returns {OpenSeadragon.Viewer} Instance du viewer
 *
 * Technical Notes:
 *   - showNavigator: true → Active mini-map (affichera overview!)
 *   - navigatorPosition: BOTTOM_RIGHT → Coin bas-droit
 *   - Zone principale reste noire (placeholder Phase 1)
 *   - Phase 2: DZI tiling pour navigation interactive
 */
export function initViewer(elementId) {
    return OpenSeadragon({
        id: elementId,

        // Prefix pour icônes UI OpenSeadragon (zoom, home, fullscreen)
        // CDN officiel OpenSeadragon
        prefixUrl: 'https://cdn.jsdelivr.net/npm/openseadragon@4.1/build/openseadragon/images/',

        // Mini-map (NOTRE OVERVIEW!)
        showNavigator: true,
        navigatorPosition: 'BOTTOM_RIGHT',
        navigatorSizeRatio: 0.25,  // 25% de la taille viewer

        // Boutons navigation
        showNavigationControl: true,
        navigationControlAnchor: OpenSeadragon.ControlAnchor.TOP_LEFT,

        // Boutons zoom/home
        showZoomControl: true,
        showHomeControl: true,
        showFullPageControl: true,

        // Placeholder au démarrage (noir)
        tileSources: null
    });
}

/**
 * Charge overview dans viewer comme image simple.
 *
 * MÉTHODE SIMPLE - Phase 1:
 * OpenSeadragon peut afficher une image normale avec type: 'image'.
 * Pas besoin de DZI/tiling pour juste afficher overview.
 *
 * Doc: https://openseadragon.github.io/examples/tilesource-image/
 *
 * @param {OpenSeadragon.Viewer} viewer - Instance viewer
 * @param {string} overviewUrl - URL vers image overview (JPEG)
 *
 * Technical Notes:
 *   - type: 'image' → OpenSeadragon affiche image telle quelle
 *   - Overview apparaît dans mini-map (navigator)
 *   - Zone principale affiche aussi overview (zoomable)
 *   - Phase 2: Remplacer par DZI pour tiling vrai niveaux pyramidaux
 */
export function loadOverview(viewer, overviewUrl) {
    const tileSource = {
        type: 'image',
        url: overviewUrl
    };

    viewer.open(tileSource);
}
