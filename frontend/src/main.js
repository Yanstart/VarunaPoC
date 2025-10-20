/**
 * VarunaPoC Frontend - Entry Point
 *
 * Architecture Phase 1.6:
 *   - Page HOME: Détection + Listing des lames
 *   - Page VIEWER: Ouverture + Visualisation
 *
 * Flow:
 *   1. Charger lames depuis /Slides (récursif)
 *   2. Afficher Home page avec liste + stats
 *   3. Au clic sur lame → Navigation vers Viewer
 *   4. Viewer: Charger lame + Afficher OpenSeadragon
 */

import './style.css';
import { fetchSlides, getSlideInfo, getOverviewUrl } from './utils/api.js';
import { createHomePage } from './components/Home.js';
import { initViewer, loadOverview } from './components/Viewer.js';

// Global state
let currentPage = 'home'; // 'home' | 'viewer'
let allSlides = [];
let selectedSlide = null;
let viewer = null;

/**
 * Initialise l'application.
 */
async function init() {
    try {
        // Charger toutes les lames
        const { slides } = await fetchSlides();
        allSlides = slides;

        // Afficher page d'accueil
        showHomePage();

    } catch (err) {
        console.error('Init failed:', err);
        document.querySelector('#app').innerHTML =
            `<div class="error">
                <h2>❌ Erreur de connexion</h2>
                <p>${err.message}</p>
                <p class="note">Le backend est-il démarré?</p>
                <code>cd backend && python -m uvicorn main:app --reload</code>
            </div>`;
    }
}

/**
 * Affiche la page d'accueil (liste des lames).
 */
function showHomePage() {
    currentPage = 'home';
    const app = document.querySelector('#app');
    app.innerHTML = '';

    const homePage = createHomePage(allSlides, handleSlideSelect);
    app.appendChild(homePage);
}

/**
 * Affiche la page viewer (visualisation lame).
 *
 * @param {Object} slide - Lame sélectionnée
 */
async function showViewerPage(slide) {
    currentPage = 'viewer';
    selectedSlide = slide;

    const app = document.querySelector('#app');
    app.innerHTML = `
        <div class="viewer-page">
            <header class="viewer-header">
                <button id="back-btn" class="back-button">
                    ← Retour à la liste
                </button>
                <div class="viewer-title">
                    <h1>${slide.name}</h1>
                    <p class="slide-info">
                        ${slide.format} • ${slide.structure_type}
                        ${slide.is_supported === false ? ' • <span class="warning">⚠️ Non supporté</span>' : ''}
                    </p>
                </div>
            </header>

            <main class="viewer-main">
                <div id="viewer" class="viewer"></div>
                <div id="info" class="info">
                    <div class="loading">Chargement de la lame...</div>
                </div>
            </main>
        </div>
    `;

    // Bouton retour
    document.querySelector('#back-btn').addEventListener('click', () => {
        showHomePage();
    });

    // Initialiser OpenSeadragon
    viewer = initViewer('viewer');

    // Charger la lame
    await loadSlide(slide);
}

/**
 * Gère la sélection d'une lame (navigation Home → Viewer).
 *
 * @param {Object} slide - Lame sélectionnée
 */
function handleSlideSelect(slide) {
    console.log('Navigating to viewer for:', slide.name);
    showViewerPage(slide);
}

/**
 * Charge une lame dans le viewer.
 *
 * @param {Object} slide - Lame à charger
 */
async function loadSlide(slide) {
    const infoPanel = document.querySelector('#info');

    try {
        infoPanel.innerHTML = '<div class="loading">Chargement métadonnées...</div>';

        // Récupérer métadonnées
        const metadata = await getSlideInfo(slide.id);

        infoPanel.innerHTML = '<div class="loading">Chargement overview...</div>';

        // Charger overview dans viewer
        const overviewUrl = getOverviewUrl(slide.id);
        loadOverview(viewer, overviewUrl);

        // Afficher métadonnées
        const [w, h] = metadata.dimensions;
        infoPanel.innerHTML = `
            <h3>Informations</h3>
            <dl>
                <dt>Format</dt>
                <dd>${slide.format}</dd>
                <dt>Dimensions</dt>
                <dd>${w.toLocaleString()} × ${h.toLocaleString()} px</dd>
                <dt>Niveaux</dt>
                <dd>${metadata.level_count}</dd>
                <dt>Structure</dt>
                <dd>${slide.structure_type}</dd>
                ${slide.has_joint_files ? `
                    <dt>Fichiers joints</dt>
                    <dd>${slide.joint_files_count}</dd>
                ` : ''}
                ${slide.has_companion_dirs ? `
                    <dt>Companion dirs</dt>
                    <dd>${slide.companion_dirs_count}</dd>
                ` : ''}
            </dl>
            <p class="note">
                <strong>Phase 1.6:</strong>
                Overview affiché dans mini-map (bas-droite).
                Navigation complète à venir en Phase 2.
            </p>
        `;

    } catch (err) {
        console.error('Load failed:', err);
        infoPanel.innerHTML = `
            <div class="error">
                <h3>❌ Erreur d'ouverture</h3>
                <p>${err.message}</p>
                ${slide.is_supported === false ? `
                    <p class="note">
                        <strong>Lame non supportée</strong><br>
                        ${slide.notes}
                    </p>
                ` : ''}
            </div>
        `;
    }
}

// Start application
init();
