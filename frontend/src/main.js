/**
 * VarunaPoC Frontend - Entry Point
 *
 * Refactored Architecture (Phase 2.0):
 *   - Modular design patterns (Factory, Singleton, Observer, Mediator)
 *   - Multi-viewer support with optional synchronization
 *   - Clean separation of concerns
 *
 * Pages:
 *   - HOME: Navigation hierarchique dans /Slides (explorateur de dossiers)
 *   - VIEWER: Single viewer avec streaming de tuiles
 *   - COMPARE: Multi-viewer layout avec sync optionnelle
 *
 * @module main
 */

import './style.css';

// Core
import { eventBus } from './core/EventBus.js';
import { Events, Pages, StorageKeys } from './core/Constants.js';

// Services
import { apiService } from './services/ApiService.js';
import { annotationStore } from './services/AnnotationStore.js';
import { authService } from './services/AuthService.js';

// Phase 3: Auth components
import { LoginPage } from './components/LoginPage.js';
import { UserMenu } from './components/UserMenu.js';

// Viewers
import { viewerManager } from './viewers/ViewerManager.js';

// Components
import { createFolderBrowser } from './components/FolderBrowser.js';
import { createCaseBrowser } from './components/CaseBrowser.js';
import { CompareLayout } from './components/CompareLayout.js';
import { MLPanel } from './components/MLPanel.js';
import { HeatmapOverlay } from './components/HeatmapOverlay.js';
import { CaseSidebar } from './components/CaseSidebar.js';

// Phase 2: Annotations
import { AnnotationLayer } from './components/AnnotationLayer.js';
import { DrawingTools } from './components/DrawingTools.js';
import { LayerManager } from './components/LayerManager.js';
import { DetectionPanel } from './components/DetectionPanel.js';
import { CountingPanel } from './components/CountingPanel.js';
import { CellCountingPanel } from './components/CellCountingPanel.js';
import { ClusteringPanel } from './components/ClusteringPanel.js';
import { ClusteringOverlay } from './components/ClusteringOverlay.js';
import { QualityBadge } from './components/QualityBadge.js';
import { DriftDashboard } from './components/DriftDashboard.js';
import { createWorklistView } from './components/WorklistView.js';
import { createRecentCases } from './components/RecentCases.js';
import { FocusAssistPanel } from './components/FocusAssistPanel.js';
import { AutoTagBadge } from './components/AutoTagBadge.js';
import { MagnificationBar } from './components/MagnificationBar.js';

// Legacy support
import { initViewer, loadSlideWithTiles, getLegacyViewer } from './components/Viewer.js';

// ML worker access control (tracks busy state + current job label)
import { isMLWorkerBusy } from './services/mlWorkerAccess.js';

// ==========================================
// APPLICATION STATE
// ==========================================

/**
 * Application state
 * @type {Object}
 */
const appState = {
    /** Current page: 'home' | 'viewer' | 'compare' */
    currentPage: Pages.HOME,

    /** Selected slide for single viewer */
    selectedSlide: null,

    /** Legacy viewer reference (single viewer mode) */
    viewer: null,

    /** Folder browser component */
    folderBrowser: null,

    /** Compare layout component (multi-viewer mode) */
    compareLayout: null,

    /** ML Panel component (single viewer mode) */
    mlPanel: null,

    /** Heatmap overlay component (single viewer mode) */
    heatmapOverlay: null,

    /** Phase 2: Annotation components */
    annotationLayer: null,
    drawingTools: null,
    layerManager: null,
    detectionPanel: null,

    /** Pending slide for compare mode (selected from slide picker) */
    pendingSlideForPanel: null,

    /** Phase 3: Auth components */
    loginPage: null,
    userMenu: null,

    /** Wave 4: Cell counting panel */
    cellCountingPanel: null,

    /** Wave 4: Clustering */
    clusteringPanel: null,
    clusteringOverlay: null,

    /** Wave 4: Quality badge */
    qualityBadge: null,

    /** Wave 4: Drift dashboard */
    driftDashboard: null,

    /** Waves 1-2: Focus assist, auto-tag, magnification */
    focusAssistPanel: null,
    autoTagBadge: null,
    magnificationBar: null,

    /** Wave 3: Case navigation */
    caseSidebar: null,
    currentCase: null,
};

// ==========================================
// PACS DEEP LINK HELPERS
// ==========================================

/**
 * Parse /slide/{name} from current URL path.
 * @returns {string|null} Slide name if URL matches, null otherwise
 */
function parseSlideRoute() {
    const match = window.location.pathname.match(/^\/slide\/(.+)$/);
    return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Resolve a slide by name via API and open it in the viewer.
 * Cleans the URL back to '/' after resolution.
 * @param {string} slideName - Filename stem from PACS
 */
async function openSlideByName(slideName) {
    const app = document.querySelector('#app');
    app.innerHTML = `
        <div class="loading-page">
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <p>Opening slide...</p>
                <p class="slide-name-display">${slideName}</p>
            </div>
        </div>
    `;

    try {
        const slide = await apiService.getSlideByName(slideName);
        // Clean URL to root (no router, entry point only)
        window.history.replaceState(null, '', '/');
        await showViewerPage(slide);
    } catch (err) {
        console.error('[PACS] Failed to resolve slide:', slideName, err);
        showSlideNotFoundError(slideName, err);
    }
}

/**
 * Show PACS-specific error page when slide name cannot be resolved.
 * @param {string} slideName - The name that was searched
 * @param {Error} err - The error from the API
 */
function showSlideNotFoundError(slideName, err) {
    window.history.replaceState(null, '', '/');
    const statusHint = err.status === 409
        ? 'Multiple slides match this name. Contact your administrator.'
        : 'The slide may not be scanned yet, or the name may be incorrect.';

    document.querySelector('#app').innerHTML = `
        <div class="error-page">
            <div class="error">
                <h2>Slide Not Found</h2>
                <p class="slide-name-display">${slideName}</p>
                <p>${err.message || 'Unknown error'}</p>
                <p class="note">${statusHint}</p>
                <button onclick="location.href='/'">Go to Home</button>
            </div>
        </div>
    `;
}

// ==========================================
// INITIALIZATION
// ==========================================

/**
 * Initialize the application
 */
async function init() {
    try {
        console.warn('[App] Initializing VarunaPoC...');

        // Check backend availability
        const isAvailable = await apiService.isAvailable();
        if (!isAvailable) {
            throw new Error('Backend is not available');
        }

        // PACS: detect /slide/{name} BEFORE auth redirect
        const slideRoute = parseSlideRoute();
        if (slideRoute) {
            sessionStorage.setItem(StorageKeys.PENDING_SLIDE_NAME, slideRoute);
        }

        // Phase 3: Check auth requirement
        const authRequired = await authService.init();

        if (authRequired && !authService.isAuthenticated) {
            // Show login page (pending slide saved in sessionStorage)
            showLoginPage();
            return;
        }

        // Setup event listeners
        setupEventListeners();

        // PACS: check for pending deep link (from URL or pre-auth save)
        const pendingSlide = sessionStorage.getItem(StorageKeys.PENDING_SLIDE_NAME);
        if (pendingSlide) {
            sessionStorage.removeItem(StorageKeys.PENDING_SLIDE_NAME);
            await openSlideByName(pendingSlide);
            return;
        }

        // Show home page
        showHomePage();

        console.warn('[App] Initialization complete');

    } catch (err) {
        console.error('[App] Init failed:', err);
        showError(err);
    }
}

/**
 * Setup global event listeners
 */
function setupEventListeners() {
    // Listen for slide selection in compare mode
    eventBus.on(Events.SLIDE_SELECTED, ({ panelId: _panelId, panelIndex }) => {
        if (appState.currentPage === Pages.COMPARE && appState.compareLayout) {
            // Store pending panel index
            appState.pendingSlideForPanel = panelIndex;

            // Show slide picker
            showSlidePicker();
        }
    });

    // Listen for page changes (handles drift dashboard back navigation)
    eventBus.on(Events.PAGE_CHANGED, ({ page }) => {
        if (page === Pages.HOME && appState.currentPage === 'drift') {
            showHomePage();
            return;
        }
        appState.currentPage = page;
    });
}

// ==========================================
// PAGE RENDERING
// ==========================================

/**
 * Show login page (when auth is required)
 */
function showLoginPage() {
    cleanup();
    const app = document.querySelector('#app');
    app.innerHTML = '';
    appState.loginPage = new LoginPage(app);
    eventBus.emit(Events.PAGE_CHANGED, { page: Pages.LOGIN });
}

/**
 * Show home page (folder browser)
 */
function showHomePage() {
    appState.currentPage = Pages.HOME;

    // Cleanup previous components BEFORE creating new ones
    cleanup();

    const app = document.querySelector('#app');
    app.textContent = '';
    app.className = 'page-home';

    // View toggle callback — re-renders home page with new preference
    function handleViewToggle(_newView) {
        showHomePage();
    }

    // Check user preference: default to 'cases' view
    const viewPref = localStorage.getItem('varuna_home_view') || 'cases';

    if (viewPref === 'explorer') {
        // Explorer (folder) view
        appState.folderBrowser = createFolderBrowser(handleSlideSelect, handleViewToggle);
        app.appendChild(appState.folderBrowser);
    } else if (viewPref === 'worklist') {
        // Worklist view ("Mes cas")
        const worklistView = createWorklistView(handleSlideSelect, handleViewToggle);
        app.appendChild(worklistView);
    } else {
        // Case view (default) — includes recent cases section
        const recentCases = createRecentCases(handleSlideSelect);
        app.appendChild(recentCases);
        const caseBrowser = createCaseBrowser(handleSlideSelect, handleCaseSelect, handleViewToggle);
        app.appendChild(caseBrowser);
    }

    // Worklist shortcut button
    if (viewPref !== 'worklist') {
        const worklistBtn = document.createElement('button');
        worklistBtn.className = 'worklist-shortcut-button';
        worklistBtn.textContent = 'Mes cas';
        worklistBtn.title = 'Ouvrir la liste de travail';
        worklistBtn.addEventListener('click', () => {
            localStorage.setItem('varuna_home_view', 'worklist');
            showHomePage();
        });
        app.appendChild(worklistBtn);
    }

    // Add compare mode button
    const compareBtn = document.createElement('button');
    compareBtn.className = 'compare-mode-button';
    compareBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="8" height="18" rx="1"/>
            <rect x="13" y="3" width="8" height="18" rx="1"/>
        </svg>
        Mode comparaison
    `;
    compareBtn.title = 'Ouvrir le mode comparaison';
    compareBtn.addEventListener('click', () => showComparePage());
    app.appendChild(compareBtn);

    eventBus.emit(Events.PAGE_CHANGED, { page: Pages.HOME });
}

/**
 * Show viewer page (single slide)
 * @param {Object} slide - Selected slide
 */
async function showViewerPage(slide) {
    appState.currentPage = Pages.VIEWER;
    appState.selectedSlide = slide;

    // Cleanup previous components BEFORE creating new ones
    cleanup();

    const app = document.querySelector('#app');
    app.className = 'page-viewer';
    app.innerHTML = `
        <div class="viewer-page">
            <header class="viewer-header">
                <button id="back-btn" class="back-button">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 12H5M12 19l-7-7 7-7"/>
                    </svg>
                    Retour
                </button>
                <div class="viewer-title">
                    <h1>${slide.name}</h1>
                    <p class="slide-info">
                        ${slide.format} | ${slide.structure_type}
                        ${slide.is_supported === false ? ' | <span class="warning">Non supporté</span>' : ''}
                    </p>
                </div>
                <button id="compare-btn" class="header-button" title="Open in compare mode">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="8" height="18" rx="1"/>
                        <rect x="13" y="3" width="8" height="18" rx="1"/>
                    </svg>
                </button>
                <button id="ml-btn" class="header-button header-button--ml" title="Analyse IA">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </button>
                <div id="user-menu-slot" class="header-user-menu"></div>
            </header>

            <main class="viewer-main">
                <div class="viewer-body">
                    <div class="viewer-area">
                        <div id="viewer" class="viewer"></div>
                        <div id="ml-panel-container"></div>
                    </div>
                    <div id="info" class="info">
                        <div class="loading">Loading slide...</div>
                    </div>
                    <div id="case-sidebar-container"></div>
                </div>
            </main>
        </div>
    `;

    // Back button
    document.querySelector('#back-btn').addEventListener('click', showHomePage);

    // Wave 4: Quality Badge in header
    const viewerTitle = document.querySelector('.viewer-title');
    if (viewerTitle) {
        appState.qualityBadge = new QualityBadge(slide.id, eventBus);
        viewerTitle.insertAdjacentElement('afterend', appState.qualityBadge.el);

        // Wave 2: Auto-tag badge below slide info
        appState.autoTagBadge = new AutoTagBadge(viewerTitle, { slideId: slide.id });
    }

    // Compare button
    document.querySelector('#compare-btn').addEventListener('click', () => {
        showComparePage(slide);
    });

    // ML button
    const mlBtn = document.querySelector('#ml-btn');
    mlBtn.addEventListener('click', () => {
        toggleMLPanel(slide);
    });

    // Initialize viewer (uses new architecture internally)
    appState.viewer = initViewer('viewer');

    // Load slide
    await loadSlide(slide);

    // Get the viewer instance for ML components
    const viewerInstance = getLegacyViewer();
    const viewerId = viewerInstance ? viewerInstance.id : 'legacy-viewer';

    // Initialize ML Panel (hidden by default)
    const mlContainer = document.querySelector('#ml-panel-container');
    appState.mlPanel = new MLPanel(mlContainer, { viewerId, viewerInstance });
    appState.mlPanel.setSlide(slide.id);
    mlContainer.classList.add('is-hidden');

    // Initialize Heatmap Overlay (listens for ML_HEATMAP_TOGGLE events)
    if (viewerInstance) {
        appState.heatmapOverlay = new HeatmapOverlay(viewerInstance);

        // Phase 2: Annotation Layer (SVG overlay)
        appState.annotationLayer = new AnnotationLayer(viewerInstance);

        // Phase 2: Drawing Tools (toolbar on viewer)
        appState.drawingTools = new DrawingTools(viewerInstance, appState.annotationLayer);
        const viewerArea = document.querySelector('.viewer-area');
        if (viewerArea) {
            viewerArea.appendChild(appState.drawingTools.element);
        }

        // Phase 2: Detection Panel (inside ML panel container, below ML panel)
        const mlContainer2 = document.querySelector('#ml-panel-container');
        if (mlContainer2) {
            const detectionContainer = document.createElement('div');
            detectionContainer.id = 'detection-panel-container';
            detectionContainer.style.marginTop = '8px';
            mlContainer2.appendChild(detectionContainer);
            appState.detectionPanel = new DetectionPanel(detectionContainer, { slideId: slide.id, viewerInstance });

            // Wave 4: Cell Counting Panel
            const cellCountingContainer = document.createElement('div');
            cellCountingContainer.id = 'cell-counting-panel-container';
            cellCountingContainer.style.marginTop = '8px';
            mlContainer2.appendChild(cellCountingContainer);
            appState.cellCountingPanel = new CellCountingPanel(cellCountingContainer, { slideId: slide.id, viewerInstance });

            // Wave 4: Clustering Panel
            const clusteringContainer = document.createElement('div');
            clusteringContainer.id = 'clustering-panel-container';
            clusteringContainer.style.marginTop = '8px';
            mlContainer2.appendChild(clusteringContainer);
            appState.clusteringPanel = new ClusteringPanel(clusteringContainer, { slideId: slide.id });

            // Wave 2: Focus Assist Panel
            const focusContainer = document.createElement('div');
            focusContainer.id = 'focus-assist-panel-container';
            focusContainer.style.marginTop = '8px';
            mlContainer2.appendChild(focusContainer);
            appState.focusAssistPanel = new FocusAssistPanel(focusContainer, { slideId: slide.id });
        }
    }

    // Wave 4: Clustering Overlay (canvas on OSD viewer)
    if (viewerInstance) {
        appState.clusteringOverlay = new ClusteringOverlay(viewerInstance);
    }

    // Wave 1: Magnification Bar (floating badge in viewer area)
    if (viewerInstance && viewerInstance.viewer) {
        appState.magnificationBar = new MagnificationBar(viewerInstance.viewer);
        const viewerArea = document.querySelector('.viewer-area');
        if (viewerArea && appState.magnificationBar.element) {
            viewerArea.appendChild(appState.magnificationBar.element);
        }
    }

    // Phase 2: Layer Manager (in info panel)
    const infoPanel = document.querySelector('#info');
    if (infoPanel) {
        const layerContainer = document.createElement('div');
        layerContainer.id = 'layer-manager-container';
        layerContainer.style.marginTop = '16px';
        infoPanel.appendChild(layerContainer);
        appState.layerManager = new LayerManager(layerContainer);

        // Counting Panel (annotation statistics)
        const countingContainer = document.createElement('div');
        countingContainer.id = 'counting-panel-container';
        countingContainer.style.marginTop = '12px';
        infoPanel.appendChild(countingContainer);
        appState.countingPanel = new CountingPanel(countingContainer);
    }

    // Phase 2: Load annotations for this slide
    annotationStore.setSlide(slide.id);

    // Phase 3: User menu
    const userMenuSlot = document.querySelector('#user-menu-slot');
    if (userMenuSlot && authService.authEnabled) {
        appState.userMenu = new UserMenu(userMenuSlot);
    }

    // Phase 3: Role-based UI visibility
    _applyRoleVisibility();

    // Wave 3: Case Sidebar — show sibling slides from same case
    await _initCaseSidebar(slide);

    eventBus.emit(Events.PAGE_CHANGED, { page: Pages.VIEWER });
}

/**
 * Initialize the case sidebar in the viewer.
 * Populates the sidebar container with sibling slides from the same case.
 *
 * @param {Object} slide - Current slide
 */
async function _initCaseSidebar(slide) {
    const sidebarContainer = document.querySelector('#case-sidebar-container');
    if (!sidebarContainer) { return; }

    // Determine case data: from case browser navigation or from slide info
    let casePath = null;
    let caseSlides = [];

    if (appState.currentCase && appState.currentCase.slides) {
        // Navigated from CaseBrowser — case data already available
        casePath = appState.currentCase.path;
        caseSlides = appState.currentCase.slides;
    } else {
        // Navigated from FolderBrowser or deep link — try to extract parent path
        try {
            const slideId = slide.id || '';
            // slide.id often encodes the relative path; extract parent folder
            const lastSlash = slideId.lastIndexOf('/');
            if (lastSlash > 0) {
                const parentPath = '/' + slideId.substring(0, lastSlash);
                const folderData = await apiService.browse(parentPath);
                casePath = parentPath;
                caseSlides = folderData.slides || [];
            }
        } catch (err) {
            console.warn('[App] Could not load sibling slides for sidebar:', err);
        }
    }

    if (caseSlides.length > 0) {
        appState.caseSidebar = new CaseSidebar(sidebarContainer, {
            onSlideSwitch: (newSlide) => {
                handleSlideSwitch(newSlide);
            },
        });
        appState.caseSidebar.setCase(casePath, caseSlides, slide.id);
    }
}

/**
 * Toggle ML Panel visibility
 * @param {Object} _slide - Current slide
 */
function toggleMLPanel(_slide) {
    if (!appState.mlPanel) {return;}

    const mlContainer = document.querySelector('#ml-panel-container');
    if (!mlContainer) {return;}

    const isHidden = mlContainer.classList.toggle('is-hidden');
    const mlBtn = document.querySelector('#ml-btn');
    if (mlBtn) {
        mlBtn.classList.toggle('is-active', !isHidden);
    }
}

/**
 * Show compare page (multi-viewer)
 * @param {Object} [initialSlide] - Optional slide to load in first panel
 */
async function showComparePage(initialSlide = null) {
    appState.currentPage = Pages.COMPARE;

    // Cleanup previous components BEFORE creating new ones
    cleanup();

    const app = document.querySelector('#app');
    app.className = 'page-compare';
    app.innerHTML = `
        <div class="compare-page">
            <header class="compare-header">
                <button id="back-btn" class="back-button">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 12H5M12 19l-7-7 7-7"/>
                    </svg>
                    Retour
                </button>
                <h1 class="compare-title">Mode comparaison</h1>
            </header>
            <main id="compare-container" class="compare-container"></main>
        </div>
    `;

    // Back button
    document.querySelector('#back-btn').addEventListener('click', showHomePage);

    // Create compare layout
    const container = document.querySelector('#compare-container');
    appState.compareLayout = new CompareLayout(container, {
        initialLayout: 'SIDE_BY_SIDE',
        showSyncControls: true,
        onSlideSelect: (panel, index) => {
            appState.pendingSlideForPanel = index;
            showSlidePicker();
        },
    });

    // Load initial slide if provided
    if (initialSlide) {
        await appState.compareLayout.loadSlideAt(0, initialSlide.id, initialSlide.name);
    }

    eventBus.emit(Events.PAGE_CHANGED, { page: Pages.COMPARE });
}

/**
 * Show drift monitoring dashboard (admin page)
 */
function showDriftPage() {
    cleanup();
    appState.currentPage = 'drift';

    const app = document.querySelector('#app');
    app.className = 'page-drift';
    app.textContent = '';

    appState.driftDashboard = new DriftDashboard(app);
}

/**
 * Show slide picker modal
 */
function showSlidePicker() {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'slide-picker-modal';
    modal.innerHTML = `
        <div class="slide-picker-content">
            <header class="slide-picker-header">
                <h2>Sélectionner une lame</h2>
                <button class="slide-picker-close">&times;</button>
            </header>
            <div class="slide-picker-body">
                <div class="loading">Loading...</div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Close button
    modal.querySelector('.slide-picker-close').addEventListener('click', () => {
        modal.remove();
        appState.pendingSlideForPanel = null;
    });

    // Click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
            appState.pendingSlideForPanel = null;
        }
    });

    // Load slides in picker
    loadSlidesInPicker(modal.querySelector('.slide-picker-body'));
}

/**
 * Load slides in picker modal
 * @param {HTMLElement} container - Container element
 */
async function loadSlidesInPicker(container) {
    try {
        // Use fetchSlides() for recursive scan of ALL slides
        const data = await apiService.fetchSlides();

        if (!data.slides || data.slides.length === 0) {
            container.innerHTML = '<p class="empty">Aucune lame trouvée</p>';
            return;
        }

        container.innerHTML = '';

        // Create slide list
        const list = document.createElement('div');
        list.className = 'slide-picker-list';

        data.slides.forEach(slide => {
            const item = document.createElement('button');
            item.className = 'slide-picker-item';
            item.innerHTML = `
                <span class="slide-name">${slide.name}</span>
                <span class="slide-format">${slide.format}</span>
            `;

            item.addEventListener('click', async () => {
                if (appState.pendingSlideForPanel !== null && appState.compareLayout) {
                    await appState.compareLayout.loadSlideAt(
                        appState.pendingSlideForPanel,
                        slide.id,
                        slide.name,
                    );
                }
                appState.pendingSlideForPanel = null;
                container.closest('.slide-picker-modal').remove();
            });

            list.appendChild(item);
        });

        container.appendChild(list);

    } catch (err) {
        container.innerHTML = `<p class="error">Error loading slides: ${err.message}</p>`;
    }
}

// ==========================================
// SLIDE LOADING
// ==========================================

/**
 * Handle slide selection (Home -> Viewer)
 * @param {Object} slide - Selected slide
 */
function handleSlideSelect(slide) {
    console.warn('[App] Navigating to viewer for:', slide.name);
    showViewerPage(slide);
}

/**
 * Handle case selection (Case Browser -> Viewer with first slide)
 * @param {Object} caseData - Case data with slides array
 */
function handleCaseSelect(caseData) {
    if (!caseData.slides || caseData.slides.length === 0) {
        console.warn('[App] Case has no slides:', caseData.name);
        return;
    }
    console.warn('[App] Navigating to case:', caseData.name, `(${caseData.slides.length} slides)`);
    const firstSlide = caseData.slides.find(s => s.is_supported !== false) || caseData.slides[0];
    if (firstSlide.is_supported === false) {
        console.warn('[App] No supported slides in case:', caseData.name);
    }
    // Store case data on appState for sidebar use (Task A3)
    appState.currentCase = caseData;
    showViewerPage(firstSlide);
}

/**
 * Handle intra-case slide switching (Wave 3 - Task A4).
 * Reloads viewer without navigating back to home.
 * Updates title, reloads tile source, resets annotations and ML panels.
 *
 * @param {Object} newSlide - Slide to switch to
 */
async function handleSlideSwitch(newSlide) {
    console.warn('[App] Rapid slide switch to:', newSlide.name);

    // Cancel running ML job if worker is busy
    if (isMLWorkerBusy()) {
        const confirmed = confirm(
            'Une analyse IA est en cours. Voulez-vous l\'annuler et changer de lame ?',
        );
        if (!confirmed) return;
        try {
            await apiService.cancelML();
        } catch (e) {
            console.warn('[App] ML cancel failed:', e);
        }
        eventBus.emit(Events.ML_WORKER_FREE);
    }

    // 1. Update app state
    appState.selectedSlide = newSlide;

    // 2. Update viewer header title
    const titleH1 = document.querySelector('.viewer-title h1');
    if (titleH1) { titleH1.textContent = newSlide.name; }

    const slideInfo = document.querySelector('.viewer-title .slide-info');
    if (slideInfo) {
        slideInfo.textContent = `${newSlide.format || ''} | ${newSlide.structure_type || ''}`;
    }

    // 3. Close old tile source and reload new slide
    if (appState.viewer) {
        appState.viewer.close();
    }
    await loadSlide(newSlide);

    // 4. Update sidebar active indicator
    if (appState.caseSidebar) {
        appState.caseSidebar.setActiveSlide(newSlide.id);
    }

    // 5. Reload annotations for new slide
    annotationStore.clear();
    annotationStore.setSlide(newSlide.id);

    // 6. Reset ML panel for new slide
    if (appState.mlPanel) {
        appState.mlPanel.setSlide(newSlide.id);
    }

    // 7. Reset detection panel for new slide
    if (appState.detectionPanel && appState.detectionPanel.setSlide) {
        appState.detectionPanel.setSlide(newSlide.id);
    }

    // 8. Reset cell counting panel for new slide
    if (appState.cellCountingPanel && appState.cellCountingPanel.setSlide) {
        appState.cellCountingPanel.setSlide(newSlide.id);
    }

    // 9. Reset clustering panel for new slide
    if (appState.clusteringPanel && appState.clusteringPanel.setSlide) {
        appState.clusteringPanel.setSlide(newSlide.id);
    }

    // 10. Clear clustering overlay for new slide
    if (appState.clusteringOverlay && appState.clusteringOverlay.clear) {
        appState.clusteringOverlay.clear();
    }

    // 11. Reset quality badge for new slide
    if (appState.qualityBadge && appState.qualityBadge.setSlide) {
        appState.qualityBadge.setSlide(newSlide.id);
    }

    // 12. Reset focus assist panel for new slide
    if (appState.focusAssistPanel && appState.focusAssistPanel.setSlide) {
        appState.focusAssistPanel.setSlide(newSlide.id);
    }

    // 13. Reset auto-tag badge for new slide
    if (appState.autoTagBadge && appState.autoTagBadge.setSlide) {
        appState.autoTagBadge.setSlide(newSlide.id);
    }
}

/**
 * Load slide in single viewer mode
 * @param {Object} slide - Slide to load
 */
async function loadSlide(slide) {
    const infoPanel = document.querySelector('#info');

    try {
        infoPanel.innerHTML = '<div class="loading">Chargement des métadonnées...</div>';

        // Get metadata
        const metadata = await apiService.getSlideInfo(slide.id);

        infoPanel.innerHTML = '<div class="loading">Chargement des tuiles (flux DZI)...</div>';

        // Load slide with tiles
        await loadSlideWithTiles(appState.viewer, slide.id);

        // Display metadata
        const [w, h] = metadata.dimensions;
        infoPanel.innerHTML = `
            <h3>Information</h3>
            <dl>
                <dt>Format</dt>
                <dd>${slide.format}</dd>
                <dt>Dimensions</dt>
                <dd>${w.toLocaleString()} x ${h.toLocaleString()} px</dd>
                <dt>Niveaux</dt>
                <dd>${metadata.level_count} niveaux de pyramide</dd>
                <dt>Structure</dt>
                <dd>${slide.structure_type}</dd>
                ${slide.has_joint_files ? `
                    <dt>Fichiers joints</dt>
                    <dd>${slide.joint_files_count}</dd>
                ` : ''}
                ${slide.has_companion_dirs ? `
                    <dt>Dossiers compagnons</dt>
                    <dd>${slide.companion_dirs_count}</dd>
                ` : ''}
            </dl>
            <p class="note">
                <strong>Flux de tuiles actif</strong><br>
                Tuiles 256x256 chargées à la demande<br>
                ${metadata.level_count} niveaux de zoom disponibles<br>
                La mini-carte montre la position actuelle
            </p>
        `;

    } catch (err) {
        console.error('[App] Load failed:', err);
        infoPanel.innerHTML = `
            <div class="error">
                <h3>Error opening slide</h3>
                <p>${err.message}</p>
                ${slide.is_supported === false ? `
                    <p class="note">
                        <strong>Unsupported slide</strong><br>
                        ${slide.notes || 'This format is not supported'}
                    </p>
                ` : ''}
            </div>
        `;
    }
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

/**
 * Apply role-based UI visibility.
 * Hides components that the current user's role doesn't have access to.
 */
function _applyRoleVisibility() {
    const canAnnotate = authService.hasRole('MEDECIN', 'ADMIN_TECHNIQUE');
    const canML = authService.hasRole('MEDECIN', 'ADMIN_TECHNIQUE');

    // Hide drawing tools for non-physicians
    if (!canAnnotate && appState.drawingTools) {
        appState.drawingTools.element.style.display = 'none';
    }

    // Hide ML button for non-physicians
    if (!canML) {
        const mlBtn = document.querySelector('#ml-btn');
        if (mlBtn) {mlBtn.style.display = 'none';}
    }
}

/**
 * Cleanup previous page components
 */
function cleanup() {
    // Destroy Phase 2 annotation components
    if (appState.detectionPanel) {
        appState.detectionPanel.destroy();
        appState.detectionPanel = null;
    }
    if (appState.cellCountingPanel) {
        appState.cellCountingPanel.destroy();
        appState.cellCountingPanel = null;
    }
    if (appState.clusteringPanel) {
        appState.clusteringPanel.destroy();
        appState.clusteringPanel = null;
    }
    if (appState.clusteringOverlay) {
        appState.clusteringOverlay.destroy();
        appState.clusteringOverlay = null;
    }
    if (appState.countingPanel) {
        appState.countingPanel.destroy();
        appState.countingPanel = null;
    }
    if (appState.layerManager) {
        appState.layerManager.destroy();
        appState.layerManager = null;
    }
    if (appState.drawingTools) {
        appState.drawingTools.destroy();
        appState.drawingTools = null;
    }
    if (appState.annotationLayer) {
        appState.annotationLayer.destroy();
        appState.annotationLayer = null;
    }

    // Wave 4: Quality badge
    if (appState.qualityBadge) {
        appState.qualityBadge.destroy();
        appState.qualityBadge = null;
    }

    // Wave 4: Drift dashboard
    if (appState.driftDashboard) {
        appState.driftDashboard.destroy();
        appState.driftDashboard = null;
    }

    // Waves 1-2: Focus assist, auto-tag, magnification
    if (appState.focusAssistPanel) {
        appState.focusAssistPanel.destroy();
        appState.focusAssistPanel = null;
    }
    if (appState.autoTagBadge) {
        appState.autoTagBadge.destroy();
        appState.autoTagBadge = null;
    }
    if (appState.magnificationBar) {
        appState.magnificationBar.destroy();
        appState.magnificationBar = null;
    }

    // Destroy ML components
    if (appState.heatmapOverlay) {
        appState.heatmapOverlay.destroy();
        appState.heatmapOverlay = null;
    }
    if (appState.mlPanel) {
        appState.mlPanel.destroy();
        appState.mlPanel = null;
    }

    // Destroy compare layout
    if (appState.compareLayout) {
        appState.compareLayout.destroy();
        appState.compareLayout = null;
    }

    // Wave 3: Case sidebar
    if (appState.caseSidebar) {
        appState.caseSidebar.destroy();
        appState.caseSidebar = null;
    }

    // Reset viewer manager
    viewerManager.destroyAll();

    // Clear annotation state
    annotationStore.clear();

    // Phase 3: Auth components
    if (appState.userMenu) {
        appState.userMenu.destroy();
        appState.userMenu = null;
    }
    if (appState.loginPage) {
        appState.loginPage.destroy();
        appState.loginPage = null;
    }

    // Clear references
    appState.viewer = null;
    appState.folderBrowser = null;
    appState.selectedSlide = null;
    // Note: currentCase intentionally preserved across viewer reloads
}

/**
 * Show error page
 * @param {Error} err - Error object
 */
function showError(err) {
    document.querySelector('#app').innerHTML = `
        <div class="error-page">
            <div class="error">
                <h2>Connection Error</h2>
                <p>${err.message}</p>
                <p class="note">Is the backend running?</p>
                <code>cd backend && python -m uvicorn main:app --reload</code>
                <button onclick="location.reload()">Retry</button>
            </div>
        </div>
    `;
}

// ==========================================
// ADDITIONAL CSS FOR NEW FEATURES
// ==========================================

// Inject additional styles
const additionalStyles = document.createElement('style');
additionalStyles.textContent = `
    /* Worklist shortcut button on home page */
    .worklist-shortcut-button {
        position: fixed;
        bottom: 20px;
        left: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 20px;
        background: var(--color-bg-elevated, #1a1a1a);
        color: var(--color-text-primary, #e0e0e0);
        border: 1px solid var(--color-border, #333);
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
        z-index: 100;
    }

    .worklist-shortcut-button:hover {
        border-color: var(--color-primary, #4a9eff);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
    }

    /* Compare mode button on home page */
    .compare-mode-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 20px;
        background: var(--color-primary, #4a9eff);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(74, 158, 255, 0.3);
        transition: all 0.2s ease;
        z-index: 100;
    }

    .compare-mode-button:hover {
        background: var(--color-primary-light, #6bb0ff);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(74, 158, 255, 0.4);
    }

    /* Compare page layout */
    .compare-page {
        display: flex;
        flex-direction: column;
        height: 100vh;
        background: var(--color-bg-base, #000);
    }

    .compare-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px 20px;
        background: var(--color-bg-elevated, #1a1a1a);
        border-bottom: 1px solid var(--color-border, #333);
    }

    .compare-title {
        font-size: 18px;
        font-weight: 500;
        color: var(--color-text-primary, #e0e0e0);
        margin: 0;
    }

    .compare-container {
        flex: 1;
        overflow: hidden;
    }

    /* Header button */
    .header-button {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        padding: 0;
        background: transparent;
        border: 1px solid var(--color-border, #333);
        border-radius: 6px;
        color: var(--color-text-secondary, #888);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .header-button:hover {
        background: var(--color-bg-hover, #2a2a2a);
        color: var(--color-text-primary, #e0e0e0);
        border-color: var(--color-primary, #4a9eff);
    }

    /* Slide picker modal */
    .slide-picker-modal {
        position: fixed;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.8);
        z-index: 1000;
    }

    .slide-picker-content {
        width: 90%;
        max-width: 500px;
        max-height: 80vh;
        background: var(--color-bg-elevated, #1a1a1a);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
    }

    .slide-picker-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        border-bottom: 1px solid var(--color-border, #333);
    }

    .slide-picker-header h2 {
        margin: 0;
        font-size: 18px;
        color: var(--color-text-primary, #e0e0e0);
    }

    .slide-picker-close {
        width: 32px;
        height: 32px;
        padding: 0;
        background: transparent;
        border: none;
        font-size: 24px;
        color: var(--color-text-muted, #666);
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .slide-picker-close:hover {
        background: var(--color-bg-hover, #2a2a2a);
        color: var(--color-text-primary, #e0e0e0);
    }

    .slide-picker-body {
        padding: 16px;
        max-height: 60vh;
        overflow-y: auto;
    }

    .slide-picker-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .slide-picker-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        background: var(--color-bg-surface, #0d0d0d);
        border: 1px solid var(--color-border, #333);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .slide-picker-item:hover {
        background: var(--color-bg-hover, #2a2a2a);
        border-color: var(--color-primary, #4a9eff);
    }

    .slide-picker-item .slide-name {
        font-size: 14px;
        color: var(--color-text-primary, #e0e0e0);
    }

    .slide-picker-item .slide-format {
        font-size: 12px;
        color: var(--color-text-muted, #666);
        padding: 2px 8px;
        background: var(--color-bg-overlay, #252525);
        border-radius: 4px;
    }

    /* Error page */
    .error-page {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
        padding: 20px;
    }

    .error-page .error {
        max-width: 500px;
        text-align: center;
    }

    .error-page button {
        margin-top: 20px;
        padding: 10px 24px;
        background: var(--color-primary, #4a9eff);
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
    }

    .error-page button:hover {
        background: var(--color-primary-light, #6bb0ff);
    }

    /* PACS deep link loading page */
    .loading-page {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
        padding: 20px;
    }

    .loading-content {
        text-align: center;
        color: var(--color-text-primary, #e0e0e0);
    }

    .loading-spinner {
        width: 40px;
        height: 40px;
        margin: 0 auto 16px;
        border: 3px solid var(--color-border, #333);
        border-top-color: var(--color-primary, #4a9eff);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .slide-name-display {
        font-family: monospace;
        font-size: 14px;
        color: var(--color-text-muted, #666);
        background: var(--color-bg-surface, #0d0d0d);
        padding: 4px 12px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 8px;
    }
`;
document.head.appendChild(additionalStyles);

// ==========================================
// START APPLICATION
// ==========================================

init();

// Export for debugging
window.__VarunaApp = {
    state: appState,
    eventBus,
    viewerManager,
    apiService,
};
