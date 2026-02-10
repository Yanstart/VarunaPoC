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
import { Events, Pages } from './core/Constants.js';

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
import { CompareLayout } from './components/CompareLayout.js';
import { MLPanel } from './components/MLPanel.js';
import { HeatmapOverlay } from './components/HeatmapOverlay.js';

// Phase 2: Annotations
import { AnnotationLayer } from './components/AnnotationLayer.js';
import { DrawingTools } from './components/DrawingTools.js';
import { LayerManager } from './components/LayerManager.js';
import { DetectionPanel } from './components/DetectionPanel.js';
import { CountingPanel } from './components/CountingPanel.js';

// Legacy support
import { initViewer, loadSlideWithTiles, getLegacyViewer } from './components/Viewer.js';

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
    userMenu: null
};

// ==========================================
// INITIALIZATION
// ==========================================

/**
 * Initialize the application
 */
async function init() {
    try {
        console.log('[App] Initializing VarunaPoC...');

        // Check backend availability
        const isAvailable = await apiService.isAvailable();
        if (!isAvailable) {
            throw new Error('Backend is not available');
        }

        // Phase 3: Check auth requirement
        const authRequired = await authService.init();

        if (authRequired && !authService.isAuthenticated) {
            // Show login page
            showLoginPage();
            return;
        }

        // Setup event listeners
        setupEventListeners();

        // Show home page
        showHomePage();

        console.log('[App] Initialization complete');

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
    eventBus.on(Events.SLIDE_SELECTED, ({ panelId, panelIndex }) => {
        if (appState.currentPage === Pages.COMPARE && appState.compareLayout) {
            // Store pending panel index
            appState.pendingSlideForPanel = panelIndex;

            // Show slide picker
            showSlidePicker();
        }
    });

    // Listen for page changes
    eventBus.on(Events.PAGE_CHANGED, ({ page }) => {
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
    app.innerHTML = '';
    app.className = 'page-home';

    // Create folder browser
    appState.folderBrowser = createFolderBrowser(handleSlideSelect);
    app.appendChild(appState.folderBrowser);

    // Add compare mode button
    const compareBtn = document.createElement('button');
    compareBtn.className = 'compare-mode-button';
    compareBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="8" height="18" rx="1"/>
            <rect x="13" y="3" width="8" height="18" rx="1"/>
        </svg>
        Compare Mode
    `;
    compareBtn.title = 'Open compare mode for side-by-side viewing';
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
                    Back
                </button>
                <div class="viewer-title">
                    <h1>${slide.name}</h1>
                    <p class="slide-info">
                        ${slide.format} | ${slide.structure_type}
                        ${slide.is_supported === false ? ' | <span class="warning">Not supported</span>' : ''}
                    </p>
                </div>
                <button id="compare-btn" class="header-button" title="Open in compare mode">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="8" height="18" rx="1"/>
                        <rect x="13" y="3" width="8" height="18" rx="1"/>
                    </svg>
                </button>
                <button id="ml-btn" class="header-button header-button--ml" title="ML Analysis">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </button>
                <div id="user-menu-slot" class="header-user-menu"></div>
            </header>

            <main class="viewer-main">
                <div class="viewer-area">
                    <div id="viewer" class="viewer"></div>
                    <div id="ml-panel-container"></div>
                </div>
                <div id="info" class="info">
                    <div class="loading">Loading slide...</div>
                </div>
            </main>
        </div>
    `;

    // Back button
    document.querySelector('#back-btn').addEventListener('click', showHomePage);

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
    appState.mlPanel = new MLPanel(mlContainer, { viewerId });
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
            appState.detectionPanel = new DetectionPanel(detectionContainer, { slideId: slide.id });
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

    eventBus.emit(Events.PAGE_CHANGED, { page: Pages.VIEWER });
}

/**
 * Toggle ML Panel visibility
 * @param {Object} slide - Current slide
 */
function toggleMLPanel(slide) {
    if (!appState.mlPanel) return;

    const mlContainer = document.querySelector('#ml-panel-container');
    if (!mlContainer) return;

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
                    Back
                </button>
                <h1 class="compare-title">Compare Mode</h1>
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
        }
    });

    // Load initial slide if provided
    if (initialSlide) {
        await appState.compareLayout.loadSlideAt(0, initialSlide.id, initialSlide.name);
    }

    eventBus.emit(Events.PAGE_CHANGED, { page: Pages.COMPARE });
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
                <h2>Select Slide</h2>
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
            container.innerHTML = '<p class="empty">No slides found</p>';
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
                        slide.name
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
    console.log('[App] Navigating to viewer for:', slide.name);
    showViewerPage(slide);
}

/**
 * Load slide in single viewer mode
 * @param {Object} slide - Slide to load
 */
async function loadSlide(slide) {
    const infoPanel = document.querySelector('#info');

    try {
        infoPanel.innerHTML = '<div class="loading">Loading metadata...</div>';

        // Get metadata
        const metadata = await apiService.getSlideInfo(slide.id);

        infoPanel.innerHTML = '<div class="loading">Loading tiles (DZI streaming)...</div>';

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
                <dt>Levels</dt>
                <dd>${metadata.level_count} pyramid levels</dd>
                <dt>Structure</dt>
                <dd>${slide.structure_type}</dd>
                ${slide.has_joint_files ? `
                    <dt>Joint files</dt>
                    <dd>${slide.joint_files_count}</dd>
                ` : ''}
                ${slide.has_companion_dirs ? `
                    <dt>Companion dirs</dt>
                    <dd>${slide.companion_dirs_count}</dd>
                ` : ''}
            </dl>
            <p class="note">
                <strong>Tile Streaming Active:</strong><br>
                256x256 tiles loaded on demand<br>
                ${metadata.level_count} zoom levels available<br>
                Mini-map shows current position
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
        if (mlBtn) mlBtn.style.display = 'none';
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
    apiService
};
