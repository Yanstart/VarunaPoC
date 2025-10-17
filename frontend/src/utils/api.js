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

const API_BASE = 'http://localhost:8000';

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
    const res = await fetch(`${API_BASE}/api/slides`);
    if (!res.ok) throw new Error('Failed to fetch slides');
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
 *   - Appelle GET /api/slides/{id}/info
 *   - Retourne infos OpenSlide (dimensions, niveaux pyramidaux)
 */
export async function getSlideInfo(slideId) {
    const res = await fetch(`${API_BASE}/api/slides/${slideId}/info`);
    if (!res.ok) throw new Error('Failed to fetch slide info');
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
    return `${API_BASE}/api/slides/${slideId}/overview`;
}
