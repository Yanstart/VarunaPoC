/**
 * API Client pour backend VarunaPoC
 *
 * Fournit fonctions pour communiquer avec FastAPI backend.
 *
 * Technical Notes:
 *   - Backend sur http://localhost:8000
 *   - Toutes requêtes sont GET (read-only PoC)
 *   - Erreurs HTTP propagées comme exceptions
 */

// Read VITE_API_URL with `??` so an explicitly-empty value (prod build served
// through nginx) yields same-origin relative URLs. `||` would fall back to dev.
const rawApiUrl = import.meta.env?.VITE_API_URL ?? 'http://localhost:8000';
export const API_BASE = rawApiUrl.replace(/\/$/, '');

/**
 * Récupère liste des lames depuis backend.
 *
 * @returns {Promise<Object>} { count: number, slides: Array }
 * @throws {Error} Si requête échoue
 *
 * Technical Notes:
 *   - Appelle GET /api/slides
 *   - Retourne toutes lames détectées dans /Slides
 */
export async function fetchSlides() {
    const res = await fetch(`${API_BASE}/api/v1/slides/`);
    if (!res.ok) {throw new Error('Failed to fetch slides');}
    return res.json();
}

/**
 * Récupère métadonnées d'une lame.
 *
 * @param {string} slideId - ID unique de la lame
 * @returns {Promise<Object>} Métadonnées (dimensions, levels, vendor, etc.)
 * @throws {Error} Si requête échoue ou lame introuvable
 *
 * Technical Notes:
 *   - Appelle GET /api/v1/slides/{id}/info
 *   - Retourne infos OpenSlide (dimensions, niveaux pyramidaux)
 */
export async function getSlideInfo(slideId) {
    const res = await fetch(`${API_BASE}/api/v1/slides/${slideId}/info`);
    if (!res.ok) {throw new Error('Failed to fetch slide info');}
    return res.json();
}

/**
 * Génère URL pour image overview d'une lame.
 *
 * @param {string} slideId - ID unique de la lame
 * @returns {string} URL vers endpoint overview (JPEG)
 *
 * Technical Notes:
 *   - Retourne URL, pas l'image elle-même
 *   - Utilisé par OpenSeadragon et <img> tags
 *   - Backend génère JPEG optimisé (~100-500KB)
 */
export function getOverviewUrl(slideId) {
    return `${API_BASE}/api/v1/slides/${slideId}/overview`;
}

/**
 * Navigation hiérarchique - Récupère le contenu d'un dossier.
 *
 * @param {string} path - Chemin relatif depuis /Slides (ex: "/", "/3DHistech")
 * @returns {Promise<Object>} { current_path, parent_path, breadcrumb, folders, slides, files }
 * @throws {Error} Si requête échoue ou chemin invalide
 *
 * Technical Notes:
 *   - Appelle GET /api/v1/slides/browse?path={path}
 *   - Lecture non-récursive (un seul niveau de profondeur)
 *   - Sécurité: path traversal bloqué par backend
 *   - Voir docs/Manuel/02-NAVIGATION_DOSSIERS.md
 */
export async function fetchBrowse(path = '/') {
    // Delegate to ApiService so the Authorization Bearer header is injected
    // consistently with the rest of the app. Avoids a 401 when AUTH_ENABLED=true.
    const { apiService } = await import('../services/ApiService.js');
    return apiService.browse(path);
}
