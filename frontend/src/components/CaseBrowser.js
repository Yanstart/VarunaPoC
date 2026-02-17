/**
 * Case Browser Component - Navigation par cas (dossiers parent)
 *
 * Regroupe les lames par dossier parent en "cartes de cas".
 * Chaque dossier = un cas, avec liste de lames, coloration
 * et comptage.
 *
 * API:
 * - GET /api/slides/browse?path=/ (dossiers racine)
 * - GET /api/slides/browse?path={folder} (lames par dossier)
 *
 * @module components/CaseBrowser
 */

import { apiService } from '../services/ApiService.js';

/**
 * Extract stain type from a slide filename.
 *
 * @param {string} slideName - Slide filename (e.g. "2024-0847_HE.svs")
 * @returns {string|null} Detected stain or null
 */
function extractStain(slideName) {
    const stem = slideName.replace(/\.[^.]+$/, '').toUpperCase();
    const stains = [
        'H&E', 'HE', 'CK5/6', 'CK5', 'CK7', 'CK20',
        'P63', 'P53', 'KI-67', 'KI67',
        'HER2', 'ER', 'PR', 'PD-L1',
        'CD3', 'CD20', 'CD45',
        'PAS', 'MASSON',
    ];
    return stains.find(s => stem.includes(s.replace(/[/-]/g, ''))) || null;
}

/**
 * Get a display-friendly stain name.
 *
 * @param {string} stain - Raw stain identifier
 * @returns {string} Display name
 */
function normalizeStainDisplay(stain) {
    const map = {
        'HE': 'H&E',
        'KI67': 'Ki-67',
        'KI-67': 'Ki-67',
        'CK5/6': 'CK5/6',
        'PD-L1': 'PD-L1',
    };
    return map[stain] || stain;
}

/**
 * Check if a stain is H&E type (for badge coloring).
 *
 * @param {string} stain - Stain identifier
 * @returns {boolean}
 */
function isHEStain(stain) {
    return stain === 'H&E' || stain === 'HE';
}

/**
 * Build the browser header using safe DOM methods.
 *
 * @param {Function|null} onViewToggle - Optional toggle callback
 * @returns {HTMLElement} The header element
 */
function buildHeader(onViewToggle) {
    const header = document.createElement('div');
    header.className = 'browser-header';

    // Title block
    const titleBlock = document.createElement('div');
    titleBlock.className = 'home-title';

    const h1 = document.createElement('h1');
    h1.textContent = 'VarunaPoC';
    titleBlock.appendChild(h1);

    const subtitle = document.createElement('p');
    subtitle.className = 'subtitle';
    subtitle.textContent = 'Visualiseur de pathologie num\u00e9rique';
    titleBlock.appendChild(subtitle);

    header.appendChild(titleBlock);

    // Toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'home-toolbar';

    // Search box
    const searchBox = document.createElement('div');
    searchBox.className = 'search-box';

    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.id = 'case-search-input';
    searchInput.placeholder = 'Rechercher un cas...';
    searchBox.appendChild(searchInput);

    toolbar.appendChild(searchBox);

    // Open local button
    const openLocalBtn = document.createElement('button');
    openLocalBtn.className = 'open-local-btn';
    openLocalBtn.id = 'case-open-local-btn';
    openLocalBtn.textContent = 'Ouvrir fichier local';
    toolbar.appendChild(openLocalBtn);

    // Hidden file input
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.id = 'case-file-input';
    fileInput.style.display = 'none';
    fileInput.accept = '.svs,.tif,.tiff,.ndpi,.vms,.vmu,.scn,.mrxs,.bif,.svslide,.czi';
    fileInput.multiple = true;
    toolbar.appendChild(fileInput);

    // Toggle button
    if (onViewToggle) {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'view-toggle-btn';
        toggleBtn.textContent = 'Explorateur';
        toggleBtn.title = 'Basculer vers la vue explorateur de fichiers';
        toggleBtn.addEventListener('click', () => {
            localStorage.setItem('varuna_home_view', 'explorer');
            onViewToggle('explorer');
        });
        toolbar.appendChild(toggleBtn);
    }

    header.appendChild(toolbar);

    return header;
}

/**
 * Create the CaseBrowser component.
 *
 * @param {Function} onSlideSelect - Callback when a slide is directly selected
 * @param {Function} onCaseSelect - Callback when a case card is clicked
 * @param {Function} [onViewToggle] - Callback to switch to explorer view
 * @returns {HTMLElement} The case browser container element
 */
export function createCaseBrowser(onSlideSelect, onCaseSelect, onViewToggle) {
    const container = document.createElement('div');
    container.className = 'case-browser';

    // Header
    const header = buildHeader(onViewToggle);

    // Main grid area
    const grid = document.createElement('div');
    grid.className = 'case-browser__grid';
    grid.id = 'case-browser-grid';

    container.appendChild(header);
    container.appendChild(grid);

    // ---- Internal state ----
    let allCases = [];

    // ---- Load cases ----
    loadCases();

    /**
     * Load root folders and fetch slides per folder to build case list.
     */
    async function loadCases() {
        grid.textContent = '';
        const loading = document.createElement('div');
        loading.className = 'case-browser__loading';
        loading.textContent = 'Chargement des cas...';
        grid.appendChild(loading);

        try {
            const rootData = await apiService.browse('/');
            const folders = (rootData.folders || []).filter(f => f.item_count > 0);

            // Fetch slides for each folder in parallel
            const casePromises = folders.map(async (folder) => {
                try {
                    const folderData = await apiService.browse(folder.path);
                    const slides = folderData.slides || [];
                    const stains = slides
                        .map(s => extractStain(s.name))
                        .filter(Boolean);
                    const uniqueStains = [...new Set(stains)];

                    return {
                        name: folder.name,
                        path: folder.path,
                        slides: slides,
                        stains: uniqueStains,
                        lastModified: folder.last_modified || null,
                    };
                } catch (err) {
                    console.error(`[CaseBrowser] Failed to load folder ${folder.name}:`, err);
                    return {
                        name: folder.name,
                        path: folder.path,
                        slides: [],
                        stains: [],
                        lastModified: null,
                    };
                }
            });

            allCases = await Promise.all(casePromises);

            // Also include root-level slides as an "uncategorized" case if any
            const rootSlides = rootData.slides || [];
            if (rootSlides.length > 0) {
                const rootStains = rootSlides
                    .map(s => extractStain(s.name))
                    .filter(Boolean);
                allCases.push({
                    name: 'Lames non classees',
                    path: '/',
                    slides: rootSlides,
                    stains: [...new Set(rootStains)],
                    lastModified: null,
                });
            }

            renderCases(allCases);

        } catch (err) {
            console.error('[CaseBrowser] Failed to load cases:', err);
            grid.textContent = '';
            const errorEl = document.createElement('div');
            errorEl.className = 'case-browser__error';
            errorEl.textContent = 'Erreur lors du chargement des cas';
            grid.appendChild(errorEl);
        }
    }

    /**
     * Render the case cards into the grid.
     *
     * @param {Array} cases - Array of case objects
     */
    function renderCases(cases) {
        grid.textContent = '';

        if (cases.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'case-browser__empty';
            empty.textContent = 'Aucun cas trouve';
            grid.appendChild(empty);
            return;
        }

        cases.forEach(caseData => {
            const card = createCaseCard(caseData);
            grid.appendChild(card);
        });
    }

    /**
     * Create a single case card element.
     *
     * @param {Object} caseData - Case object with name, path, slides, stains
     * @returns {HTMLElement} The case card element
     */
    function createCaseCard(caseData) {
        const card = document.createElement('div');
        card.className = 'case-card';

        // Case name
        const nameEl = document.createElement('div');
        nameEl.className = 'case-card__name';
        nameEl.textContent = caseData.name;
        card.appendChild(nameEl);

        // Meta line: slide count + stains summary
        const metaEl = document.createElement('div');
        metaEl.className = 'case-card__meta';
        const slideCount = caseData.slides.length;
        const stainList = caseData.stains.map(normalizeStainDisplay).join(', ');
        metaEl.textContent = `${slideCount} lame${slideCount !== 1 ? 's' : ''}` +
            (stainList ? ` \u2014 ${stainList}` : '');
        card.appendChild(metaEl);

        // Stain badges
        if (caseData.stains.length > 0) {
            const stainsContainer = document.createElement('div');
            stainsContainer.className = 'case-card__stains';

            caseData.stains.forEach(stain => {
                const badge = document.createElement('span');
                badge.className = 'stain-badge';
                if (isHEStain(stain)) {
                    badge.classList.add('stain-badge--he');
                } else {
                    badge.classList.add('stain-badge--ihc');
                }
                badge.textContent = normalizeStainDisplay(stain);
                stainsContainer.appendChild(badge);
            });

            card.appendChild(stainsContainer);
        }

        // Date
        if (caseData.lastModified) {
            const dateEl = document.createElement('div');
            dateEl.className = 'case-card__date';
            dateEl.textContent = caseData.lastModified;
            card.appendChild(dateEl);
        }

        // Slide preview list (collapsed)
        if (caseData.slides.length > 0) {
            const preview = document.createElement('div');
            preview.className = 'case-card__slides-preview';

            const maxPreview = 3;
            const slidesToShow = caseData.slides.slice(0, maxPreview);
            slidesToShow.forEach(slide => {
                const slideItem = document.createElement('div');
                slideItem.className = 'case-card__slide-item';
                slideItem.textContent = slide.name;
                preview.appendChild(slideItem);
            });

            if (caseData.slides.length > maxPreview) {
                const more = document.createElement('div');
                more.className = 'case-card__slide-item';
                more.textContent = `+ ${caseData.slides.length - maxPreview} autre(s)`;
                preview.appendChild(more);
            }

            card.appendChild(preview);
        }

        // Click handler
        card.addEventListener('click', () => {
            if (onCaseSelect) {
                onCaseSelect(caseData);
            }
        });

        return card;
    }

    // ---- Search filtering ----
    const searchInput = header.querySelector('#case-search-input');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = allCases.filter(c =>
            c.name.toLowerCase().includes(query),
        );
        renderCases(filtered);
    });

    // ---- Local file picker ----
    const openLocalBtn = header.querySelector('#case-open-local-btn');
    const fileInput = header.querySelector('#case-file-input');

    openLocalBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            const fileNames = files.map(f => f.name).join(', ');
            console.warn('Fichiers selectionnes:', fileNames);
        }
    });

    return container;
}
