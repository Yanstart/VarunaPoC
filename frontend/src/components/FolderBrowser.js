/**
 * Folder Browser Component - Navigation hiérarchique dans /Slides
 *
 * Fonctionnalités:
 * - Navigation dossier par dossier (non-récursive)
 * - Fil d'Ariane (breadcrumb) pour navigation rapide
 * - Affichage dossiers + lames + fichiers non-slides
 * - Recherche dans le dossier actuel
 * - Détection intelligente des slides et dépendances
 *
 * API:
 * - GET /api/slides/browse?path={relative_path}
 *
 * Voir: docs/Manuel/02-NAVIGATION_DOSSIERS.md
 */

import { fetchBrowse } from '../utils/api.js';
import { createSlideList } from './SlideList.js';

/**
 * Crée le composant de navigation hiérarchique.
 *
 * @param {Function} onSlideSelect - Callback appelé quand une lame est sélectionnée
 * @returns {HTMLElement} Container du browser
 */
export function createFolderBrowser(onSlideSelect) {
    const container = document.createElement('div');
    container.className = 'folder-browser';

    // Header avec titre et toolbar
    const header = document.createElement('div');
    header.className = 'browser-header';
    header.innerHTML = `
        <div class="home-title">
            <h1>VarunaPoC</h1>
            <p class="subtitle">Digital Pathology Slide Viewer</p>
        </div>
        <div class="home-toolbar">
            <div class="search-box">
                <input type="text" id="search-input" placeholder="🔍 Rechercher..." />
            </div>
            <button class="open-local-btn" id="open-local-btn">
                📂 Ouvrir fichier local
            </button>
            <input type="file" id="file-input" style="display: none;"
                   accept=".svs,.tif,.tiff,.ndpi,.vms,.vmu,.scn,.mrxs,.bif,.svslide,.czi" multiple />
        </div>
    `;

    // Breadcrumb (fil d'Ariane) avec bouton retour
    const breadcrumb = document.createElement('div');
    breadcrumb.className = 'breadcrumb';
    breadcrumb.id = 'breadcrumb';
    breadcrumb.innerHTML = `
        <button class="back-button" id="back-button" style="display: none;">
            ← Retour
        </button>
        <div id="breadcrumb-content"></div>
    `;

    // Zone principale de contenu
    const main = document.createElement('div');
    main.className = 'browser-main';
    main.id = 'browser-main';

    container.appendChild(header);
    container.appendChild(breadcrumb);
    container.appendChild(main);

    // État de navigation
    let currentPath = '/';
    let allFolders = [];
    let allSlides = [];
    let allFiles = [];

    // Charger le contenu initial (racine)
    loadDirectory(currentPath);

    /**
     * Charge le contenu d'un dossier via l'API.
     *
     * @param {string} path - Chemin relatif depuis /Slides (ex: "/", "/3DHistech")
     */
    async function loadDirectory(path) {
        try {
            main.innerHTML = '<div class="loading">Chargement du dossier...</div>';

            const data = await fetchBrowse(path);
            currentPath = data.current_path;

            // Sauvegarder les données non filtrées
            allFolders = data.folders || [];
            allSlides = data.slides || [];
            allFiles = data.files || [];

            // Afficher le contenu
            renderBreadcrumb(data.breadcrumb, data.parent_path);
            renderContent(allFolders, allSlides, allFiles);

        } catch (error) {
            console.error('Error loading directory:', error);
            main.innerHTML = `
                <div class="error">
                    <p>❌ Erreur lors du chargement du dossier</p>
                    <p class="error-details">${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Affiche le fil d'Ariane.
     *
     * @param {string[]} breadcrumbSegments - Segments du chemin (ex: ["/", "/3DHistech"])
     * @param {string|null} parentPath - Chemin du parent (null si racine)
     */
    function renderBreadcrumb(breadcrumbSegments, parentPath) {
        const backButton = breadcrumb.querySelector('#back-button');
        const breadcrumbContent = breadcrumb.querySelector('#breadcrumb-content');

        if (!breadcrumbSegments || breadcrumbSegments.length === 0) {
            breadcrumbContent.innerHTML = '';
            backButton.style.display = 'none';
            return;
        }

        // Afficher/masquer bouton retour
        if (parentPath) {
            backButton.style.display = 'inline-flex';
            backButton.onclick = () => loadDirectory(parentPath);
        } else {
            backButton.style.display = 'none';
        }

        let html = '<div class="breadcrumb-items">';

        breadcrumbSegments.forEach((segment, index) => {
            const isLast = index === breadcrumbSegments.length - 1;
            const displayName = segment === '/' ? '🏠 Racine' : segment.split('/').filter(Boolean).pop();

            if (isLast) {
                // Segment actuel (non cliquable)
                html += `<span class="breadcrumb-item active">${displayName}</span>`;
            } else {
                // Segment cliquable
                html += `
                    <span class="breadcrumb-item" data-path="${segment}">
                        ${displayName}
                    </span>
                    <span class="breadcrumb-separator">›</span>
                `;
            }
        });

        html += '</div>';
        breadcrumbContent.innerHTML = html;

        // Ajouter listeners pour navigation
        breadcrumbContent.querySelectorAll('.breadcrumb-item[data-path]').forEach(item => {
            item.addEventListener('click', () => {
                const targetPath = item.dataset.path;
                loadDirectory(targetPath);
            });
        });
    }

    /**
     * Affiche le contenu du dossier (dossiers + lames + fichiers).
     *
     * @param {Array} folders - Sous-dossiers
     * @param {Array} slides - Lames détectées
     * @param {Array} files - Fichiers non-slides
     */
    function renderContent(folders, slides, files) {
        main.innerHTML = '';

        // Section dossiers
        if (folders && folders.length > 0) {
            const foldersSection = createFoldersSection(folders);
            main.appendChild(foldersSection);
        }

        // Section lames
        if (slides && slides.length > 0) {
            const slidesSection = createSlidesSection(slides);
            main.appendChild(slidesSection);
        }

        // Section fichiers non supportés
        if (files && files.length > 0) {
            const filesSection = createFilesSection(files);
            main.appendChild(filesSection);
        }

        // Message si vide
        if ((!folders || folders.length === 0) &&
            (!slides || slides.length === 0) &&
            (!files || files.length === 0)) {
            main.innerHTML = `
                <div class="empty-folder">
                    <p>📁 Dossier vide</p>
                    <p class="empty-hint">Aucun fichier ou sous-dossier trouvé</p>
                </div>
            `;
        }
    }

    /**
     * Crée la section d'affichage des dossiers.
     *
     * @param {Array} folders - Liste des dossiers
     * @returns {HTMLElement} Section des dossiers
     */
    function createFoldersSection(folders) {
        const section = document.createElement('div');
        section.className = 'content-section folders-section';
        section.innerHTML = '<h3>📁 Dossiers</h3>';

        const grid = document.createElement('div');
        grid.className = 'folders-grid';

        folders.forEach(folder => {
            const folderCard = document.createElement('div');
            folderCard.className = 'folder-card';
            folderCard.innerHTML = `
                <div class="folder-icon">📁</div>
                <div class="folder-name">${folder.name}</div>
                <div class="folder-count">${folder.item_count} items</div>
            `;

            folderCard.addEventListener('click', () => {
                loadDirectory(folder.path);
            });

            grid.appendChild(folderCard);
        });

        section.appendChild(grid);
        return section;
    }

    /**
     * Crée la section d'affichage des lames.
     *
     * @param {Array} slides - Liste des lames
     * @returns {HTMLElement} Section des lames
     */
    function createSlidesSection(slides) {
        const section = document.createElement('div');
        section.className = 'content-section slides-section';
        section.innerHTML = '<h3>🔬 Lames détectées</h3>';

        const slideList = createSlideList(slides, onSlideSelect);
        section.appendChild(slideList);

        return section;
    }

    /**
     * Crée la section d'affichage des fichiers non-slides.
     *
     * @param {Array} files - Liste des fichiers non supportés
     * @returns {HTMLElement} Section des fichiers
     */
    function createFilesSection(files) {
        const section = document.createElement('div');
        section.className = 'content-section files-section';
        section.innerHTML = '<h3>📄 Fichiers non supportés</h3>';

        const list = document.createElement('div');
        list.className = 'files-list';

        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item unsupported';
            fileItem.innerHTML = `
                <div class="file-icon">📄</div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-note">${file.notes || 'Format inconnu'}</div>
                </div>
            `;
            list.appendChild(fileItem);
        });

        section.appendChild(list);
        return section;
    }

    // Gestion de la recherche
    const searchInput = header.querySelector('#search-input');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();

        // Filtrer dossiers
        const filteredFolders = allFolders.filter(f =>
            f.name.toLowerCase().includes(query)
        );

        // Filtrer lames
        const filteredSlides = allSlides.filter(s =>
            s.name.toLowerCase().includes(query) ||
            (s.format_string && s.format_string.toLowerCase().includes(query)) ||
            (s.notes && s.notes.toLowerCase().includes(query))
        );

        // Filtrer fichiers
        const filteredFiles = allFiles.filter(f =>
            f.name.toLowerCase().includes(query)
        );

        // Réafficher avec filtres
        renderContent(filteredFolders, filteredSlides, filteredFiles);
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
 * Gère l'ouverture de fichiers locaux.
 * (Placeholder pour future implémentation)
 *
 * @param {File[]} files - Fichiers sélectionnés
 */
function handleLocalFiles(files) {
    console.log('Fichiers sélectionnés:', files);

    const fileNames = files.map(f => f.name).join(', ');
    alert(`📂 Fichiers sélectionnés (${files.length}):\n\n${fileNames}\n\n⚠️ Note: L'upload de fichiers locaux nécessite une intégration backend.\nPour l'instant, utilisez les lames du dossier /Slides.`);

    // TODO Phase 2: Implémenter upload
}
