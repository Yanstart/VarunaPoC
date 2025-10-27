/**
 * OpenSeadragon Viewer Component - Phase 1.8: Tile Streaming
 *
 * PRINCIPE - Phase 1.8:
 * On utilise OpenSeadragon en mode DZI (Deep Zoom Image) pour streaming de tuiles.
 * Chaque tuile est chargée à la demande depuis le backend via tile_server.py.
 * Mini-carte (navigator) affiche l'overview pour orientation.
 *
 * Formats supportés: .bif, .tif, .mrxs
 *
 * Documentation:
 *   - OpenSeadragon Docs: https://openseadragon.github.io/docs/
 *   - Options: https://openseadragon.github.io/docs/OpenSeadragon.html#.Options
 *   - Custom Tile Sources: https://openseadragon.github.io/examples/tilesource-custom/
 *   - DZI Format: https://openseadragon.github.io/examples/tilesource-dzi/
 */

import OpenSeadragon from 'openseadragon';
import { API_BASE } from '../utils/api.js';

/**
 * Initialise viewer OpenSeadragon avec configuration pour tile streaming.
 *
 * @param {string} elementId - ID de l'élément DOM container
 * @returns {OpenSeadragon.Viewer} Instance du viewer
 *
 * Technical Notes:
 *   - showNavigator: true → Active mini-map (affichera overview!)
 *   - navigatorPosition: BOTTOM_RIGHT → Coin bas-droit
 *   - maxZoomPixelRatio: 2 → Permet zoom jusqu'à 2x résolution native
 *   - visibilityRatio: 1 → Empêche zoom hors limites image
 *   - constrainDuringPan: true → Empêche pan hors limites
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
        navigatorAutoFade: false,   // Toujours visible

        // Boutons navigation
        showNavigationControl: true,
        navigationControlAnchor: OpenSeadragon.ControlAnchor.TOP_LEFT,

        // Boutons zoom/home
        showZoomControl: true,
        showHomeControl: true,
        showFullPageControl: true,

        // Contraintes de navigation
        visibilityRatio: 1.0,         // Empêche zoom hors limites
        constrainDuringPan: true,     // Empêche pan hors limites
        minZoomLevel: 0.5,            // Zoom minimum (vue complète)
        maxZoomPixelRatio: 2,         // Zoom maximum (2x résolution native)

        // Performance
        immediateRender: true,        // Rendu immédiat des tuiles
        blendTime: 0.1,              // Transition rapide entre niveaux
        animationTime: 1.2,          // Animation zoom fluide

        // Placeholder au démarrage
        tileSources: null
    });
}

/**
 * Charge une lame avec streaming de tuiles DZI.
 *
 * MÉTHODE STREAMING - Phase 1.8:
 * 1. Récupère métadonnées DZI depuis /api/slides/{id}/dzi.json
 * 2. Configure TileSource custom pour OpenSeadragon
 * 3. OpenSeadragon charge les tuiles à la demande via getTileUrl()
 *
 * @param {OpenSeadragon.Viewer} viewer - Instance viewer
 * @param {string} slideId - ID unique de la lame
 *
 * Technical Notes:
 *   - getTileUrl() génère URLs vers /api/slides/{id}/tiles/{level}/{col}_{row}.jpg
 *   - OpenSeadragon gère automatiquement:
 *     - Détection du niveau à charger selon zoom
 *     - Cache des tuiles
 *     - Chargement progressif
 *   - Mini-map charge overview via /api/slides/{id}/overview
 *   - Voir: backend/services/tile_server.py pour logique extraction
 *
 * Examples:
 *   await loadSlideWithTiles(viewer, 'a1b2c3d4e5f6');
 */
export async function loadSlideWithTiles(viewer, slideId) {
    try {
        // 1. Récupérer métadonnées DZI
        console.log(`[Viewer] Loading DZI metadata for slide ${slideId}`);
        const response = await fetch(`${API_BASE}/api/slides/${slideId}/dzi.json`);

        if (!response.ok) {
            throw new Error(`Failed to load DZI metadata: ${response.statusText}`);
        }

        const dziMetadata = await response.json();
        console.log(`[Viewer] DZI metadata loaded:`, dziMetadata);

        // 2. Configurer TileSource pour OpenSeadragon
        const tileSource = {
            // Dimensions niveau 0 (pleine résolution)
            width: dziMetadata.width,
            height: dziMetadata.height,

            // Configuration tuiles
            tileSize: dziMetadata.tile_size,  // 256px standard
            tileOverlap: dziMetadata.overlap, // 0 pour simplicité
            format: dziMetadata.format,       // "jpeg"

            // Niveaux pyramidaux
            minLevel: 0,                      // Niveau 0 = haute résolution
            maxLevel: dziMetadata.levels - 1, // Niveau max = overview

            // Fonction génération URL tuiles
            // OpenSeadragon appelle cette fonction pour chaque tuile visible
            getTileUrl: function(level, x, y) {
                // Mapping niveaux OpenSeadragon → OpenSlide
                // OpenSeadragon: level 0 = bas, level max = haut
                // OpenSlide: level 0 = haut, level max = bas
                // Donc: openslide_level = (max_level - osd_level)
                const openslideLevel = dziMetadata.levels - 1 - level;

                const url = `${API_BASE}/api/slides/${slideId}/tiles/${openslideLevel}/${x}_${y}.jpg`;
                return url;
            }
        };

        console.log(`[Viewer] Opening tile source (${dziMetadata.levels} levels)`);

        // 3. Ouvrir dans OpenSeadragon
        viewer.open(tileSource);

        // 4. Charger overview dans mini-map (navigator)
        // OpenSeadragon utilise automatiquement le tileSource,
        // mais on peut améliorer en chargeant l'overview dédié
        viewer.addOnceHandler('open', () => {
            console.log('[Viewer] Slide opened successfully');

            // Optionnel: Charger overview dans navigator
            // Pour l'instant, le navigator utilise déjà les tuiles du niveau le plus bas
            // Phase future: optimiser avec image overview dédiée
        });

    } catch (error) {
        console.error(`[Viewer] Error loading slide with tiles:`, error);
        throw error;
    }
}

/**
 * Charge overview simple (legacy - Phase 1).
 *
 * MÉTHODE SIMPLE - Phase 1 (LEGACY):
 * Charge image overview complète en une seule requête.
 * Utilisé comme fallback si streaming de tuiles échoue.
 *
 * @param {OpenSeadragon.Viewer} viewer - Instance viewer
 * @param {string} overviewUrl - URL vers image overview (JPEG)
 *
 * Technical Notes:
 *   - type: 'image' → OpenSeadragon affiche image telle quelle
 *   - Pas de streaming, image chargée en une fois
 *   - Utilisé en Phase 1, maintenant remplacé par loadSlideWithTiles()
 */
export function loadOverview(viewer, overviewUrl) {
    console.log('[Viewer] Loading overview (legacy mode)');

    const tileSource = {
        type: 'image',
        url: overviewUrl
    };

    viewer.open(tileSource);
}
