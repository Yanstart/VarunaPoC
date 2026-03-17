/**
 * Home Component - Page d'accueil
 *
 * Focus: Détection et listing des lames disponibles
 *
 * Fonctionnalités:
 * - Affichage liste complète des lames détectées dans /Slides
 * - Recherche/filtrage temps réel
 * - Statistiques (total, supportées, non-supportées)
 * - Affichage structure fichiers (joints, companion dirs)
 * - Clic sur lame → Navigation vers Viewer
 *
 * Design Pattern:
 * - Component autonome retournant DOM ready
 * - Callback onSlideSelect pour navigation
 */

import { createSlideList } from './SlideList.js';
import { i18nService } from '../services/I18nService.js';

/**
 * Crée la page d'accueil.
 *
 * @param {Array} slides - Liste des lames depuis API
 * @param {Function} onSlideSelect - Callback (slide) => navigation vers viewer
 * @returns {HTMLElement} Container de la page d'accueil
 */
export function createHomePage(slides, onSlideSelect) {
    const container = document.createElement('div');
    container.className = 'home-page';

    // Header avec titre et toolbar
    const header = document.createElement('div');
    header.className = 'home-header';
    header.innerHTML = `
        <div class="home-title">
            <h1>VarunaPoC</h1>
            <p class="subtitle">${i18nService.t('app.subtitle')}</p>
        </div>
        <div class="home-toolbar">
            <div class="search-box">
                <input type="text" id="search-input" placeholder="${i18nService.t('home.searchPlaceholder')}" />
            </div>
            <button class="open-local-btn" id="open-local-btn">
                ${i18nService.t('home.openLocal')}
            </button>
            <input type="file" id="file-input" style="display: none;" accept=".svs,.tif,.tiff,.ndpi,.vms,.vmu,.scn,.mrxs,.bif,.svslide,.czi" multiple />
        </div>
        <div class="stats" id="stats"></div>
    `;

    // Section principale avec liste
    const main = document.createElement('div');
    main.className = 'home-main';
    // i18n values are from static locale JSON files, not user input
    main.innerHTML = `
        <div class="home-section-header">
            <h2>${i18nService.t('home.detectedSlides')}</h2>
            <p class="section-description">
                ${i18nService.t('home.detectedDesc')}
            </p>
        </div>
        <div id="slide-list-container" class="slide-list-container"></div>
    `;

    container.appendChild(header);
    container.appendChild(main);

    // Afficher stats initiales
    updateHomeStats(slides, slides);

    // Afficher liste des lames
    const listContainer = main.querySelector('#slide-list-container');
    const slideList = createSlideList(slides, (slide) => {
        console.warn('Slide selected:', slide.name);
        onSlideSelect(slide);
    });
    listContainer.appendChild(slideList);

    // Ajouter filtrage en temps réel
    const searchInput = header.querySelector('#search-input');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = slides.filter(s =>
            s.name.toLowerCase().includes(query) ||
            s.format.toLowerCase().includes(query) ||
            s.format_string.toLowerCase().includes(query) ||
            (s.notes && s.notes.toLowerCase().includes(query)),
        );

        // Mettre à jour liste
        listContainer.innerHTML = '';
        const newList = createSlideList(filtered, onSlideSelect);
        listContainer.appendChild(newList);

        // Mettre à jour stats
        updateHomeStats(filtered, slides);
    });

    // Gestion ouverture fichiers locaux
    const openLocalBtn = header.querySelector('#open-local-btn');
    const fileInput = header.querySelector('#file-input');

    openLocalBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            handleLocalFiles(files);
        }
    });

    return container;
}

/**
 * Gère l'ouverture de fichiers locaux sélectionnés par l'utilisateur.
 * Note: Pour l'instant, affiche juste une alerte. L'intégration complète
 * nécessiterait un endpoint backend pour uploader/analyser les fichiers.
 *
 * @param {File[]} files - Fichiers sélectionnés
 */
function handleLocalFiles(files) {
    console.warn('Fichiers sélectionnés:', files);

    const fileNames = files.map(f => f.name).join(', ');
    alert(`📂 Fichiers sélectionnés (${files.length}):\n\n${fileNames}\n\n⚠️ Note: L'upload de fichiers locaux nécessite une intégration backend.\nPour l'instant, utilisez les lames du dossier /Slides.`);

    // TODO Phase 2: Implémenter upload vers backend
    // - Créer endpoint POST /api/slides/upload
    // - Uploader fichiers + dépendances
    // - Analyser avec OpenSlide
    // - Ajouter à la liste des lames
}

/**
 * Met à jour les statistiques de la page d'accueil.
 *
 * @param {Array} filtered - Lames filtrées affichées
 * @param {Array} total - Toutes les lames
 */
function updateHomeStats(filtered, total) {
    const statsDiv = document.querySelector('#stats');
    if (!statsDiv) {return;}

    const unsupported = filtered.filter(s => s.is_supported === false).length;

    // Compter types de structures
    const singleFile = filtered.filter(s => s.structure_type === 'single-file').length;
    const multiFile = filtered.filter(s => s.structure_type === 'multi-file').length;
    const withCompanion = filtered.filter(s => s.structure_type === 'with-companion-dir').length;

    // i18n values are from static locale JSON files, not user input
    statsDiv.innerHTML = `
        <div class="stat-row">
            <span class="stat-item primary">
                <strong>${i18nService.t('home.slidesCount', { filtered: filtered.length, total: total.length })}</strong>
            </span>
            ${unsupported > 0 ? `
                <span class="stat-item warning">
                    ${i18nService.t('home.unsupported', { count: unsupported })}
                </span>
            ` : ''}
        </div>
        ${filtered.length > 0 ? `
            <div class="stat-row structure-stats">
                <span class="stat-badge" title="${i18nService.t('slide.singleFile')}">📄 ${singleFile}</span>
                <span class="stat-badge" title="${i18nService.t('slide.multiFile')}">📚 ${multiFile}</span>
                <span class="stat-badge" title="${i18nService.t('slide.withCompanion')}">🗂️ ${withCompanion}</span>
            </div>
        ` : ''}
    `;
}
