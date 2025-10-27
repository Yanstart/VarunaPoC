/**
 * VarunaPoC Frontend - Entry Point
 *
 * Architecture Phase 1.8:
 *   - Page HOME: Navigation hiérarchique dans /Slides (explorateur de dossiers)
 *   - Page VIEWER: Streaming de tuiles + Navigation interactive
 *
 * Flow:
 *   1. Afficher explorateur de dossiers (racine /Slides)
 *   2. Navigation dossier par dossier (fil d'Ariane)
 *   3. Détection lames dans dossier actuel
 *   4. Au clic sur lame → Navigation vers Viewer
 *   5. Viewer: Charger lame avec streaming de tuiles DZI
 *   6. Mini-carte (navigator) affiche overview pour orientation
 */

import './style.css';
import { getSlideInfo } from './utils/api.js';
import { createFolderBrowser } from './components/FolderBrowser.js';
import { initViewer, loadSlideWithTiles } from './components/Viewer.js';

// Global state
let currentPage = 'home'; // 'home' | 'viewer'
let selectedSlide = null;
let viewer = null;
let folderBrowser = null;

/**
 * Initialise l'application.
 */
async function init() {
    try {
        // Afficher page d'accueil (explorateur de dossiers)
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
 * Affiche la page d'accueil (explorateur de dossiers).
 */
function showHomePage() {
    currentPage = 'home';
    const app = document.querySelector('#app');
    app.innerHTML = '';

    // Créer le folder browser (charge la racine automatiquement)
    folderBrowser = createFolderBrowser(handleSlideSelect);
    app.appendChild(folderBrowser);
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
 * Charge une lame dans le viewer avec streaming de tuiles.
 *
 * Phase 1.8: Streaming DZI
 *   - Récupère métadonnées DZI depuis backend
 *   - Configure OpenSeadragon pour chargement tuiles à la demande
 *   - Mini-map affiche overview pour orientation
 *
 * @param {Object} slide - Lame à charger
 */
async function loadSlide(slide) {
    const infoPanel = document.querySelector('#info');

    try {
        infoPanel.innerHTML = '<div class="loading">Chargement métadonnées...</div>';

        // Récupérer métadonnées
        const metadata = await getSlideInfo(slide.id);

        infoPanel.innerHTML = '<div class="loading">Chargement tuiles (streaming DZI)...</div>';

        // Charger lame avec streaming de tuiles
        await loadSlideWithTiles(viewer, slide.id);

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
                <dd>${metadata.level_count} niveaux pyramidaux</dd>
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
                <strong>Phase 1.8 - Streaming actif:</strong><br>
                • Tuiles 256x256 chargées à la demande<br>
                • ${metadata.level_count} niveaux de zoom disponibles<br>
                • Mini-carte (bas-droite) affiche position actuelle<br>
                • Formats supportés: .bif, .tif, .mrxs
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
