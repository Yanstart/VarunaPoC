/**
 * VarunaPoC Frontend - Entry Point
 *
 * Point d'entrée principal de l'application.
 * Orchestre les components et gère le flux de données.
 *
 * Flow:
 *   1. Init UI (sidebar + viewer area)
 *   2. Init OpenSeadragon viewer
 *   3. Fetch slides depuis backend
 *   4. Afficher liste dans sidebar
 *   5. Au clic: charger overview dans mini-map
 */

import './style.css';
import { fetchSlides, getSlideInfo, getOverviewUrl } from './utils/api.js';
import { createSlideList } from './components/SlideList.js';
import { initViewer, loadOverview } from './components/Viewer.js';

// Global viewer instance
let viewer = null;

/**
 * Initialise l'application.
 *
 * Technical Notes:
 *   - Génère HTML structure dynamiquement
 *   - Init OpenSeadragon avant de charger slides
 *   - Gestion erreurs si backend indisponible
 */
async function init() {
    // Générer layout HTML
    document.querySelector('#app').innerHTML = `
        <div class="container">
            <aside class="sidebar">
                <h1>VarunaPoC</h1>
                <div class="search-box">
                    <input type="text" id="search-input" placeholder="Rechercher une lame..." />
                    <div class="stats" id="stats"></div>
                </div>
                <h2>Slides</h2>
                <div id="slide-list"></div>
            </aside>

            <main class="viewer-area">
                <div id="viewer" class="viewer"></div>
                <div id="info" class="info">
                    <p>Select a slide to view</p>
                </div>
            </main>
        </div>
    `;

    // Initialiser OpenSeadragon viewer
    viewer = initViewer('viewer');

    // Charger liste des lames
    try {
        const { slides } = await fetchSlides();

        // Afficher stats
        updateStats(slides, slides);

        // Afficher liste
        const listContainer = document.querySelector('#slide-list');
        const list = createSlideList(slides, handleSlideClick);
        listContainer.appendChild(list);

        // Ajouter filtre de recherche
        const searchInput = document.querySelector('#search-input');
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = slides.filter(s =>
                s.name.toLowerCase().includes(query) ||
                s.format.toLowerCase().includes(query) ||
                (s.notes && s.notes.toLowerCase().includes(query))
            );

            // Mettre à jour liste
            listContainer.innerHTML = '';
            const newList = createSlideList(filtered, handleSlideClick);
            listContainer.appendChild(newList);

            // Mettre à jour stats
            updateStats(filtered, slides);
        });

    } catch (err) {
        console.error('Init failed:', err);
        document.querySelector('#app').innerHTML =
            `<div class="error">Error: ${err.message}<br><br>Is backend running? (uvicorn main:app --reload)</div>`;
    }
}

/**
 * Met à jour les statistiques affichées.
 *
 * @param {Array} filtered - Lames filtrées actuellement affichées
 * @param {Array} total - Toutes les lames
 */
function updateStats(filtered, total) {
    const statsDiv = document.querySelector('#stats');
    const supported = filtered.filter(s => s.is_supported !== false).length;
    const unsupported = filtered.filter(s => s.is_supported === false).length;

    statsDiv.innerHTML = `
        <span class="stat-item">${filtered.length} / ${total.length} lames</span>
        ${unsupported > 0 ? `<span class="stat-item warning">${unsupported} non supportées</span>` : ''}
    `;
}

/**
 * Gestionnaire de clic sur lame.
 *
 * @param {Object} slide - Objet lame depuis API
 *
 * Flow:
 *   1. Afficher loading
 *   2. Fetch métadonnées
 *   3. Charger overview dans OpenSeadragon
 *   4. Afficher métadonnées dans info panel
 *
 * Technical Notes:
 *   - Appels API séquentiels (info puis overview)
 *   - Erreurs affichées dans info panel
 */
async function handleSlideClick(slide) {
    console.log('Loading slide:', slide.name);

    try {
        // Afficher loading
        updateInfo({ loading: true, name: slide.name });

        // Récupérer métadonnées
        const metadata = await getSlideInfo(slide.id);

        // Charger overview dans viewer
        const overviewUrl = getOverviewUrl(slide.id);
        loadOverview(viewer, overviewUrl);

        // Afficher métadonnées
        updateInfo({
            name: slide.name,
            format: metadata.format,
            dimensions: metadata.dimensions,
            levels: metadata.level_count
        });

    } catch (err) {
        console.error('Load failed:', err);
        updateInfo({ error: err.message });
    }
}

/**
 * Met à jour panneau info avec données lame.
 *
 * @param {Object} data - Données à afficher
 *
 * Technical Notes:
 *   - Gère 3 états: loading, success, error
 *   - Formate dimensions avec separateurs milliers
 */
function updateInfo(data) {
    const info = document.querySelector('#info');

    if (data.loading) {
        info.innerHTML = `<p>Loading ${data.name}...</p>`;
        return;
    }

    if (data.error) {
        info.innerHTML = `<p class="error">Error: ${data.error}</p>`;
        return;
    }

    const [w, h] = data.dimensions;
    info.innerHTML = `
        <h3>${data.name}</h3>
        <dl>
            <dt>Format</dt><dd>${data.format}</dd>
            <dt>Size</dt><dd>${w.toLocaleString()} × ${h.toLocaleString()} px</dd>
            <dt>Levels</dt><dd>${data.levels}</dd>
        </dl>
        <p class="note">
            <strong>Phase 1 Hello World:</strong><br>
            Overview displayed in mini-map (bottom-right).<br>
            Main area is placeholder for future navigation.
        </p>
    `;
}

// Start application
init();
