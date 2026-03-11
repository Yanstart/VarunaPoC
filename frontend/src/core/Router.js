/**
 * Router - Page controller and navigation manager
 *
 * Handles page rendering, component lifecycle, PACS deep links,
 * and event-driven navigation for the VarunaPoC application.
 *
 * Extracted from main.js to separate routing concerns from bootstrap.
 *
 * @module core/Router
 */

import { eventBus } from './EventBus.js';
import { Events, Pages, StorageKeys } from './Constants.js';

import { apiService } from '../services/ApiService.js';
import { annotationStore } from '../services/AnnotationStore.js';
import { authService } from '../services/AuthService.js';

import { LoginPage } from '../components/LoginPage.js';
import { UserMenu } from '../components/UserMenu.js';

import { viewerManager } from '../viewers/ViewerManager.js';

import { createFolderBrowser } from '../components/FolderBrowser.js';
import { createCaseBrowser } from '../components/CaseBrowser.js';
import { CompareLayout } from '../components/CompareLayout.js';
import { MLPanel } from '../components/MLPanel.js';
import { HeatmapOverlay } from '../components/HeatmapOverlay.js';
import { CaseSidebar } from '../components/CaseSidebar.js';

import { AnnotationLayer } from '../components/AnnotationLayer.js';
import { DrawingTools } from '../components/DrawingTools.js';
import { LayerManager } from '../components/LayerManager.js';
import { DetectionPanel } from '../components/DetectionPanel.js';
import { CountingPanel } from '../components/CountingPanel.js';
import { CellCountingPanel } from '../components/CellCountingPanel.js';
import { ClusteringPanel } from '../components/ClusteringPanel.js';
import { ClusteringOverlay } from '../components/ClusteringOverlay.js';
import { QualityBadge } from '../components/QualityBadge.js';
import { DriftDashboard } from '../components/DriftDashboard.js';
import { createWorklistView } from '../components/WorklistView.js';
import { createRecentCases } from '../components/RecentCases.js';
import { FocusAssistPanel } from '../components/FocusAssistPanel.js';
import { AutoTagBadge } from '../components/AutoTagBadge.js';
import { MagnificationBar } from '../components/MagnificationBar.js';

import { initViewer, loadSlideWithTiles, getLegacyViewer } from '../components/Viewer.js';

import { isMLWorkerBusy } from '../services/mlWorkerAccess.js';

export class Router {
    /**
     * @param {Object} appState - Shared application state (mutated by reference)
     */
    constructor(appState) {
        this._state = appState;
    }

    /**
     * Boot the application: check backend, handle auth, resolve deep links.
     */
    async start() {
        try {
            console.warn('[App] Initializing VarunaPoC...');

            const isAvailable = await apiService.isAvailable();
            if (!isAvailable) {
                throw new Error('Backend is not available');
            }

            // PACS: detect /slide/{name} BEFORE auth redirect
            const slideRoute = this._parseSlideRoute();
            if (slideRoute) {
                sessionStorage.setItem(StorageKeys.PENDING_SLIDE_NAME, slideRoute);
            }

            // Check auth requirement
            const authRequired = await authService.init();

            if (authRequired && !authService.isAuthenticated) {
                this.showLoginPage();
                return;
            }

            this._setupEventListeners();

            // PACS: check for pending deep link (from URL or pre-auth save)
            const pendingSlide = sessionStorage.getItem(StorageKeys.PENDING_SLIDE_NAME);
            if (pendingSlide) {
                sessionStorage.removeItem(StorageKeys.PENDING_SLIDE_NAME);
                await this._openSlideByName(pendingSlide);
                return;
            }

            this.showHomePage();
            console.warn('[App] Initialization complete');

        } catch (err) {
            console.error('[App] Init failed:', err);
            this.showError(err);
        }
    }

    // ==========================================
    // EVENT LISTENERS
    // ==========================================

    _setupEventListeners() {
        eventBus.on(Events.SLIDE_SELECTED, ({ panelId: _panelId, panelIndex }) => {
            if (this._state.currentPage === Pages.COMPARE && this._state.compareLayout) {
                this._state.pendingSlideForPanel = panelIndex;
                this._showSlidePicker();
            }
        });

        eventBus.on(Events.PAGE_CHANGED, ({ page }) => {
            if (page === Pages.HOME && this._state.currentPage === 'drift') {
                this.showHomePage();
                return;
            }
            this._state.currentPage = page;
        });
    }

    // ==========================================
    // PAGE RENDERING
    // ==========================================

    showLoginPage() {
        this._cleanup();
        const app = document.querySelector('#app');
        app.textContent = '';
        this._state.loginPage = new LoginPage(app);
        eventBus.emit(Events.PAGE_CHANGED, { page: Pages.LOGIN });
    }

    showHomePage() {
        this._state.currentPage = Pages.HOME;
        this._cleanup();

        const app = document.querySelector('#app');
        app.textContent = '';
        app.className = 'page-home';

        const handleViewToggle = (_newView) => {
            this.showHomePage();
        };

        const viewPref = localStorage.getItem('varuna_home_view') || 'cases';

        if (viewPref === 'explorer') {
            this._state.folderBrowser = createFolderBrowser(
                (slide) => this._handleSlideSelect(slide),
                handleViewToggle,
            );
            app.appendChild(this._state.folderBrowser);
        } else if (viewPref === 'worklist') {
            const worklistView = createWorklistView(
                (slide) => this._handleSlideSelect(slide),
                handleViewToggle,
            );
            app.appendChild(worklistView);
        } else {
            const recentCases = createRecentCases((slide) => this._handleSlideSelect(slide));
            app.appendChild(recentCases);
            const caseBrowser = createCaseBrowser(
                (slide) => this._handleSlideSelect(slide),
                (caseData) => this._handleCaseSelect(caseData),
                handleViewToggle,
            );
            app.appendChild(caseBrowser);
        }

        if (viewPref !== 'worklist') {
            const worklistBtn = document.createElement('button');
            worklistBtn.className = 'worklist-shortcut-button';
            worklistBtn.textContent = 'Mes cas';
            worklistBtn.title = 'Ouvrir la liste de travail';
            worklistBtn.addEventListener('click', () => {
                localStorage.setItem('varuna_home_view', 'worklist');
                this.showHomePage();
            });
            app.appendChild(worklistBtn);
        }

        const compareBtn = document.createElement('button');
        compareBtn.className = 'compare-mode-button';
        compareBtn.textContent = 'Mode comparaison';
        compareBtn.title = 'Ouvrir le mode comparaison';

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '20');
        svg.setAttribute('height', '20');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('stroke-width', '2');
        const rect1 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect1.setAttribute('x', '3'); rect1.setAttribute('y', '3');
        rect1.setAttribute('width', '8'); rect1.setAttribute('height', '18');
        rect1.setAttribute('rx', '1');
        const rect2 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect2.setAttribute('x', '13'); rect2.setAttribute('y', '3');
        rect2.setAttribute('width', '8'); rect2.setAttribute('height', '18');
        rect2.setAttribute('rx', '1');
        svg.appendChild(rect1);
        svg.appendChild(rect2);
        compareBtn.prepend(svg);

        compareBtn.addEventListener('click', () => this.showComparePage());
        app.appendChild(compareBtn);

        eventBus.emit(Events.PAGE_CHANGED, { page: Pages.HOME });
    }

    async showViewerPage(slide) {
        this._state.currentPage = Pages.VIEWER;
        this._state.selectedSlide = slide;
        this._cleanup();

        const app = document.querySelector('#app');
        app.className = 'page-viewer';

        // Build viewer page via DOM API
        const viewerPage = document.createElement('div');
        viewerPage.className = 'viewer-page';

        // Header
        const header = this._buildViewerHeader(slide);
        viewerPage.appendChild(header);

        // Main content
        const main = document.createElement('main');
        main.className = 'viewer-main';
        const body = document.createElement('div');
        body.className = 'viewer-body';

        const viewerArea = document.createElement('div');
        viewerArea.className = 'viewer-area';
        const viewerDiv = document.createElement('div');
        viewerDiv.id = 'viewer';
        viewerDiv.className = 'viewer';
        const mlPanelContainer = document.createElement('div');
        mlPanelContainer.id = 'ml-panel-container';
        viewerArea.appendChild(viewerDiv);
        viewerArea.appendChild(mlPanelContainer);

        const infoDiv = document.createElement('div');
        infoDiv.id = 'info';
        infoDiv.className = 'info';
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'Loading slide...';
        infoDiv.appendChild(loadingDiv);

        const sidebarContainer = document.createElement('div');
        sidebarContainer.id = 'case-sidebar-container';

        body.appendChild(viewerArea);
        body.appendChild(infoDiv);
        body.appendChild(sidebarContainer);
        main.appendChild(body);
        viewerPage.appendChild(main);

        app.textContent = '';
        app.appendChild(viewerPage);

        // Back button
        header.querySelector('#back-btn').addEventListener('click', () => this.showHomePage());

        // Quality Badge in header
        const viewerTitle = header.querySelector('.viewer-title');
        if (viewerTitle) {
            this._state.qualityBadge = new QualityBadge(slide.id, eventBus);
            viewerTitle.insertAdjacentElement('afterend', this._state.qualityBadge.el);
            this._state.autoTagBadge = new AutoTagBadge(viewerTitle, { slideId: slide.id });
        }

        // Compare button
        header.querySelector('#compare-btn').addEventListener('click', () => {
            this.showComparePage(slide);
        });

        // ML button
        const mlBtn = header.querySelector('#ml-btn');
        mlBtn.addEventListener('click', () => {
            this._toggleMLPanel(slide);
        });

        // Initialize viewer
        this._state.viewer = initViewer('viewer');
        await this._loadSlide(slide);

        const viewerInstance = getLegacyViewer();
        const viewerId = viewerInstance ? viewerInstance.id : 'legacy-viewer';

        // ML Panel (hidden by default)
        this._state.mlPanel = new MLPanel(mlPanelContainer, { viewerId, viewerInstance });
        this._state.mlPanel.setSlide(slide.id);
        mlPanelContainer.classList.add('is-hidden');

        if (viewerInstance) {
            this._state.heatmapOverlay = new HeatmapOverlay(viewerInstance);
            this._state.annotationLayer = new AnnotationLayer(viewerInstance);
            this._state.drawingTools = new DrawingTools(viewerInstance, this._state.annotationLayer);
            viewerArea.appendChild(this._state.drawingTools.element);

            this._initMLSubPanels(mlPanelContainer, slide, viewerInstance);
        }

        // Clustering Overlay (canvas on OSD viewer)
        if (viewerInstance) {
            this._state.clusteringOverlay = new ClusteringOverlay(viewerInstance);
        }

        // Magnification Bar (floating badge in viewer area)
        if (viewerInstance && viewerInstance.viewer) {
            this._state.magnificationBar = new MagnificationBar(viewerInstance.viewer);
            if (this._state.magnificationBar.element) {
                viewerArea.appendChild(this._state.magnificationBar.element);
            }
        }

        // Layer Manager (in info panel)
        this._initInfoPanelWidgets(infoDiv);

        // Load annotations for this slide
        annotationStore.setSlide(slide.id);

        // User menu
        const userMenuSlot = header.querySelector('#user-menu-slot');
        if (userMenuSlot && authService.authEnabled) {
            this._state.userMenu = new UserMenu(userMenuSlot);
        }

        this._applyRoleVisibility();
        await this._initCaseSidebar(slide);

        eventBus.emit(Events.PAGE_CHANGED, { page: Pages.VIEWER });
    }

    async showComparePage(initialSlide = null) {
        this._state.currentPage = Pages.COMPARE;
        this._cleanup();

        const app = document.querySelector('#app');
        app.className = 'page-compare';

        const page = document.createElement('div');
        page.className = 'compare-page';

        const header = document.createElement('header');
        header.className = 'compare-header';

        const backBtn = this._createBackButton();
        header.appendChild(backBtn);

        const title = document.createElement('h1');
        title.className = 'compare-title';
        title.textContent = 'Mode comparaison';
        header.appendChild(title);

        const container = document.createElement('main');
        container.id = 'compare-container';
        container.className = 'compare-container';

        page.appendChild(header);
        page.appendChild(container);
        app.textContent = '';
        app.appendChild(page);

        backBtn.addEventListener('click', () => this.showHomePage());

        this._state.compareLayout = new CompareLayout(container, {
            initialLayout: 'SIDE_BY_SIDE',
            showSyncControls: true,
            onSlideSelect: (_panel, index) => {
                this._state.pendingSlideForPanel = index;
                this._showSlidePicker();
            },
        });

        if (initialSlide) {
            await this._state.compareLayout.loadSlideAt(0, initialSlide.id, initialSlide.name);
        }

        eventBus.emit(Events.PAGE_CHANGED, { page: Pages.COMPARE });
    }

    showDriftPage() {
        this._cleanup();
        this._state.currentPage = 'drift';

        const app = document.querySelector('#app');
        app.className = 'page-drift';
        app.textContent = '';

        this._state.driftDashboard = new DriftDashboard(app);
    }

    showError(err) {
        const app = document.querySelector('#app');
        app.textContent = '';

        const page = document.createElement('div');
        page.className = 'error-page';

        const box = document.createElement('div');
        box.className = 'error';

        const h2 = document.createElement('h2');
        h2.textContent = 'Connection Error';
        box.appendChild(h2);

        const p = document.createElement('p');
        p.textContent = err.message;
        box.appendChild(p);

        const note = document.createElement('p');
        note.className = 'note';
        note.textContent = 'Is the backend running?';
        box.appendChild(note);

        const code = document.createElement('code');
        code.textContent = 'cd backend && python -m uvicorn main:app --reload';
        box.appendChild(code);

        const btn = document.createElement('button');
        btn.textContent = 'Retry';
        btn.addEventListener('click', () => location.reload());
        box.appendChild(btn);

        page.appendChild(box);
        app.appendChild(page);
    }

    // ==========================================
    // PACS DEEP LINK HELPERS
    // ==========================================

    _parseSlideRoute() {
        const match = window.location.pathname.match(/^\/slide\/(.+)$/);
        return match ? decodeURIComponent(match[1]) : null;
    }

    async _openSlideByName(slideName) {
        const app = document.querySelector('#app');
        app.textContent = '';

        const page = document.createElement('div');
        page.className = 'loading-page';

        const content = document.createElement('div');
        content.className = 'loading-content';

        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        content.appendChild(spinner);

        const msg = document.createElement('p');
        msg.textContent = 'Opening slide...';
        content.appendChild(msg);

        const nameDisplay = document.createElement('p');
        nameDisplay.className = 'slide-name-display';
        nameDisplay.textContent = slideName;
        content.appendChild(nameDisplay);

        page.appendChild(content);
        app.appendChild(page);

        try {
            const slide = await apiService.getSlideByName(slideName);
            window.history.replaceState(null, '', '/');
            await this.showViewerPage(slide);
        } catch (err) {
            console.error('[PACS] Failed to resolve slide:', slideName, err);
            this._showSlideNotFoundError(slideName, err);
        }
    }

    _showSlideNotFoundError(slideName, err) {
        window.history.replaceState(null, '', '/');
        const statusHint = err.status === 409
            ? 'Multiple slides match this name. Contact your administrator.'
            : 'The slide may not be scanned yet, or the name may be incorrect.';

        const app = document.querySelector('#app');
        app.textContent = '';

        const page = document.createElement('div');
        page.className = 'error-page';

        const box = document.createElement('div');
        box.className = 'error';

        const h2 = document.createElement('h2');
        h2.textContent = 'Slide Not Found';
        box.appendChild(h2);

        const nameDisplay = document.createElement('p');
        nameDisplay.className = 'slide-name-display';
        nameDisplay.textContent = slideName;
        box.appendChild(nameDisplay);

        const errMsg = document.createElement('p');
        errMsg.textContent = err.message || 'Unknown error';
        box.appendChild(errMsg);

        const note = document.createElement('p');
        note.className = 'note';
        note.textContent = statusHint;
        box.appendChild(note);

        const btn = document.createElement('button');
        btn.textContent = 'Go to Home';
        btn.addEventListener('click', () => { location.href = '/'; });
        box.appendChild(btn);

        page.appendChild(box);
        app.appendChild(page);
    }

    // ==========================================
    // NAVIGATION HANDLERS
    // ==========================================

    _handleSlideSelect(slide) {
        console.warn('[App] Navigating to viewer for:', slide.name);
        this.showViewerPage(slide);
    }

    _handleCaseSelect(caseData) {
        if (!caseData.slides || caseData.slides.length === 0) {
            console.warn('[App] Case has no slides:', caseData.name);
            return;
        }
        console.warn('[App] Navigating to case:', caseData.name, `(${caseData.slides.length} slides)`);
        const firstSlide = caseData.slides.find(s => s.is_supported !== false) || caseData.slides[0];
        if (firstSlide.is_supported === false) {
            console.warn('[App] No supported slides in case:', caseData.name);
        }
        this._state.currentCase = caseData;
        this.showViewerPage(firstSlide);
    }

    async _handleSlideSwitch(newSlide) {
        console.warn('[App] Rapid slide switch to:', newSlide.name);

        if (isMLWorkerBusy()) {
            const confirmed = confirm(
                'Une analyse IA est en cours. Voulez-vous l\'annuler et changer de lame ?',
            );
            if (!confirmed) { return; }
            try {
                await apiService.cancelML();
            } catch (e) {
                console.warn('[App] ML cancel failed:', e);
            }
            eventBus.emit(Events.ML_WORKER_FREE);
        }

        this._state.selectedSlide = newSlide;

        const titleH1 = document.querySelector('.viewer-title h1');
        if (titleH1) { titleH1.textContent = newSlide.name; }

        const slideInfo = document.querySelector('.viewer-title .slide-info');
        if (slideInfo) {
            slideInfo.textContent = `${newSlide.format || ''} | ${newSlide.structure_type || ''}`;
        }

        if (this._state.viewer) {
            this._state.viewer.close();
        }
        await this._loadSlide(newSlide);

        if (this._state.caseSidebar) {
            this._state.caseSidebar.setActiveSlide(newSlide.id);
        }

        annotationStore.clear();
        annotationStore.setSlide(newSlide.id);

        const resetTargets = [
            'mlPanel', 'detectionPanel', 'cellCountingPanel',
            'clusteringPanel', 'qualityBadge', 'focusAssistPanel', 'autoTagBadge',
        ];
        for (const key of resetTargets) {
            if (this._state[key] && this._state[key].setSlide) {
                this._state[key].setSlide(newSlide.id);
            }
        }

        if (this._state.clusteringOverlay && this._state.clusteringOverlay.clear) {
            this._state.clusteringOverlay.clear();
        }
    }

    // ==========================================
    // SLIDE LOADING
    // ==========================================

    async _loadSlide(slide) {
        const infoPanel = document.querySelector('#info');

        try {
            infoPanel.textContent = '';
            const loadingMeta = document.createElement('div');
            loadingMeta.className = 'loading';
            loadingMeta.textContent = 'Chargement des m\u00e9tadonn\u00e9es...';
            infoPanel.appendChild(loadingMeta);

            const metadata = await apiService.getSlideInfo(slide.id);

            infoPanel.textContent = '';
            const loadingTiles = document.createElement('div');
            loadingTiles.className = 'loading';
            loadingTiles.textContent = 'Chargement des tuiles (flux DZI)...';
            infoPanel.appendChild(loadingTiles);

            await loadSlideWithTiles(this._state.viewer, slide.id);

            // Build metadata display via DOM
            infoPanel.textContent = '';
            const h3 = document.createElement('h3');
            h3.textContent = 'Information';
            infoPanel.appendChild(h3);

            const [w, h] = metadata.dimensions;
            const dl = document.createElement('dl');
            this._addDefinition(dl, 'Format', slide.format);
            this._addDefinition(dl, 'Dimensions', `${w.toLocaleString()} x ${h.toLocaleString()} px`);
            this._addDefinition(dl, 'Niveaux', `${metadata.level_count} niveaux de pyramide`);
            this._addDefinition(dl, 'Structure', slide.structure_type);
            if (slide.has_joint_files) {
                this._addDefinition(dl, 'Fichiers joints', String(slide.joint_files_count));
            }
            if (slide.has_companion_dirs) {
                this._addDefinition(dl, 'Dossiers compagnons', String(slide.companion_dirs_count));
            }
            infoPanel.appendChild(dl);

            const note = document.createElement('p');
            note.className = 'note';
            const strong = document.createElement('strong');
            strong.textContent = 'Flux de tuiles actif';
            note.appendChild(strong);
            note.appendChild(document.createElement('br'));
            note.appendChild(document.createTextNode('Tuiles 256x256 charg\u00e9es \u00e0 la demande'));
            note.appendChild(document.createElement('br'));
            note.appendChild(document.createTextNode(`${metadata.level_count} niveaux de zoom disponibles`));
            note.appendChild(document.createElement('br'));
            note.appendChild(document.createTextNode('La mini-carte montre la position actuelle'));
            infoPanel.appendChild(note);

        } catch (err) {
            console.error('[App] Load failed:', err);
            infoPanel.textContent = '';

            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';

            const errH3 = document.createElement('h3');
            errH3.textContent = 'Error opening slide';
            errorDiv.appendChild(errH3);

            const errP = document.createElement('p');
            errP.textContent = err.message;
            errorDiv.appendChild(errP);

            if (slide.is_supported === false) {
                const errNote = document.createElement('p');
                errNote.className = 'note';
                const errStrong = document.createElement('strong');
                errStrong.textContent = 'Unsupported slide';
                errNote.appendChild(errStrong);
                errNote.appendChild(document.createElement('br'));
                errNote.appendChild(document.createTextNode(slide.notes || 'This format is not supported'));
                errorDiv.appendChild(errNote);
            }

            infoPanel.appendChild(errorDiv);
        }
    }

    // ==========================================
    // INTERNAL HELPERS
    // ==========================================

    _addDefinition(dl, term, value) {
        const dt = document.createElement('dt');
        dt.textContent = term;
        dl.appendChild(dt);
        const dd = document.createElement('dd');
        dd.textContent = value;
        dl.appendChild(dd);
    }

    _createBackButton() {
        const btn = document.createElement('button');
        btn.id = 'back-btn';
        btn.className = 'back-button';
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '16');
        svg.setAttribute('height', '16');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('stroke-width', '2');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M19 12H5M12 19l-7-7 7-7');
        svg.appendChild(path);
        btn.appendChild(svg);
        btn.appendChild(document.createTextNode(' Retour'));
        return btn;
    }

    _buildViewerHeader(slide) {
        const header = document.createElement('header');
        header.className = 'viewer-header';

        // Back button
        const backBtn = this._createBackButton();
        header.appendChild(backBtn);

        // Title block
        const titleDiv = document.createElement('div');
        titleDiv.className = 'viewer-title';
        const h1 = document.createElement('h1');
        h1.textContent = slide.name;
        titleDiv.appendChild(h1);

        const slideInfoP = document.createElement('p');
        slideInfoP.className = 'slide-info';
        slideInfoP.textContent = `${slide.format} | ${slide.structure_type}`;
        if (slide.is_supported === false) {
            slideInfoP.textContent += ' | ';
            const warn = document.createElement('span');
            warn.className = 'warning';
            warn.textContent = 'Non support\u00e9';
            slideInfoP.appendChild(warn);
        }
        titleDiv.appendChild(slideInfoP);
        header.appendChild(titleDiv);

        // Compare button
        const compareBtn = document.createElement('button');
        compareBtn.id = 'compare-btn';
        compareBtn.className = 'header-button';
        compareBtn.title = 'Open in compare mode';
        const compareSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        compareSvg.setAttribute('width', '16');
        compareSvg.setAttribute('height', '16');
        compareSvg.setAttribute('viewBox', '0 0 24 24');
        compareSvg.setAttribute('fill', 'none');
        compareSvg.setAttribute('stroke', 'currentColor');
        compareSvg.setAttribute('stroke-width', '2');
        const r1 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        r1.setAttribute('x', '3'); r1.setAttribute('y', '3');
        r1.setAttribute('width', '8'); r1.setAttribute('height', '18');
        r1.setAttribute('rx', '1');
        const r2 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        r2.setAttribute('x', '13'); r2.setAttribute('y', '3');
        r2.setAttribute('width', '8'); r2.setAttribute('height', '18');
        r2.setAttribute('rx', '1');
        compareSvg.appendChild(r1);
        compareSvg.appendChild(r2);
        compareBtn.appendChild(compareSvg);
        header.appendChild(compareBtn);

        // ML button
        const mlBtn = document.createElement('button');
        mlBtn.id = 'ml-btn';
        mlBtn.className = 'header-button header-button--ml';
        mlBtn.title = 'Analyse IA';
        const mlSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        mlSvg.setAttribute('width', '16');
        mlSvg.setAttribute('height', '16');
        mlSvg.setAttribute('viewBox', '0 0 24 24');
        mlSvg.setAttribute('fill', 'none');
        mlSvg.setAttribute('stroke', 'currentColor');
        mlSvg.setAttribute('stroke-width', '2');
        const p1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p1.setAttribute('d', 'M12 2L2 7l10 5 10-5-10-5z');
        const p2 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p2.setAttribute('d', 'M2 17l10 5 10-5');
        const p3 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p3.setAttribute('d', 'M2 12l10 5 10-5');
        mlSvg.appendChild(p1);
        mlSvg.appendChild(p2);
        mlSvg.appendChild(p3);
        mlBtn.appendChild(mlSvg);
        header.appendChild(mlBtn);

        // User menu slot
        const userSlot = document.createElement('div');
        userSlot.id = 'user-menu-slot';
        userSlot.className = 'header-user-menu';
        header.appendChild(userSlot);

        return header;
    }

    _initMLSubPanels(mlContainer, slide, viewerInstance) {
        const panels = [
            { id: 'detection-panel-container', Component: DetectionPanel, opts: { slideId: slide.id, viewerInstance }, key: 'detectionPanel' },
            { id: 'cell-counting-panel-container', Component: CellCountingPanel, opts: { slideId: slide.id, viewerInstance }, key: 'cellCountingPanel' },
            { id: 'clustering-panel-container', Component: ClusteringPanel, opts: { slideId: slide.id }, key: 'clusteringPanel' },
            { id: 'focus-assist-panel-container', Component: FocusAssistPanel, opts: { slideId: slide.id }, key: 'focusAssistPanel' },
        ];

        for (const { id, Component, opts, key } of panels) {
            const container = document.createElement('div');
            container.id = id;
            container.style.marginTop = '8px';
            mlContainer.appendChild(container);
            this._state[key] = new Component(container, opts);
        }
    }

    _initInfoPanelWidgets(infoPanel) {
        const layerContainer = document.createElement('div');
        layerContainer.id = 'layer-manager-container';
        layerContainer.style.marginTop = '16px';
        infoPanel.appendChild(layerContainer);
        this._state.layerManager = new LayerManager(layerContainer);

        const countingContainer = document.createElement('div');
        countingContainer.id = 'counting-panel-container';
        countingContainer.style.marginTop = '12px';
        infoPanel.appendChild(countingContainer);
        this._state.countingPanel = new CountingPanel(countingContainer);
    }

    async _initCaseSidebar(slide) {
        const sidebarContainer = document.querySelector('#case-sidebar-container');
        if (!sidebarContainer) { return; }

        let casePath = null;
        let caseSlides = [];

        if (this._state.currentCase && this._state.currentCase.slides) {
            casePath = this._state.currentCase.path;
            caseSlides = this._state.currentCase.slides;
        } else {
            try {
                const slideId = slide.id || '';
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
            this._state.caseSidebar = new CaseSidebar(sidebarContainer, {
                onSlideSwitch: (newSlide) => {
                    this._handleSlideSwitch(newSlide);
                },
            });
            this._state.caseSidebar.setCase(casePath, caseSlides, slide.id);
        }
    }

    _toggleMLPanel(_slide) {
        if (!this._state.mlPanel) {return;}

        const mlContainer = document.querySelector('#ml-panel-container');
        if (!mlContainer) {return;}

        const isHidden = mlContainer.classList.toggle('is-hidden');
        const mlBtn = document.querySelector('#ml-btn');
        if (mlBtn) {
            mlBtn.classList.toggle('is-active', !isHidden);
        }
    }

    _applyRoleVisibility() {
        const canAnnotate = authService.hasRole('MEDECIN', 'ADMIN_TECHNIQUE');
        const canML = authService.hasRole('MEDECIN', 'ADMIN_TECHNIQUE');

        if (!canAnnotate && this._state.drawingTools) {
            this._state.drawingTools.element.style.display = 'none';
        }

        if (!canML) {
            const mlBtn = document.querySelector('#ml-btn');
            if (mlBtn) {mlBtn.style.display = 'none';}
        }
    }

    _showSlidePicker() {
        const modal = document.createElement('div');
        modal.className = 'slide-picker-modal';

        const content = document.createElement('div');
        content.className = 'slide-picker-content';

        const header = document.createElement('header');
        header.className = 'slide-picker-header';
        const h2 = document.createElement('h2');
        h2.textContent = 'S\u00e9lectionner une lame';
        header.appendChild(h2);

        const closeBtn = document.createElement('button');
        closeBtn.className = 'slide-picker-close';
        closeBtn.textContent = '\u00d7';
        header.appendChild(closeBtn);

        const body = document.createElement('div');
        body.className = 'slide-picker-body';
        const loading = document.createElement('div');
        loading.className = 'loading';
        loading.textContent = 'Loading...';
        body.appendChild(loading);

        content.appendChild(header);
        content.appendChild(body);
        modal.appendChild(content);
        document.body.appendChild(modal);

        closeBtn.addEventListener('click', () => {
            modal.remove();
            this._state.pendingSlideForPanel = null;
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                this._state.pendingSlideForPanel = null;
            }
        });

        this._loadSlidesInPicker(body);
    }

    async _loadSlidesInPicker(container) {
        try {
            const data = await apiService.fetchSlides();

            if (!data.slides || data.slides.length === 0) {
                container.textContent = '';
                const empty = document.createElement('p');
                empty.className = 'empty';
                empty.textContent = 'Aucune lame trouv\u00e9e';
                container.appendChild(empty);
                return;
            }

            container.textContent = '';

            const list = document.createElement('div');
            list.className = 'slide-picker-list';

            data.slides.forEach(slide => {
                const item = document.createElement('button');
                item.className = 'slide-picker-item';

                const nameSpan = document.createElement('span');
                nameSpan.className = 'slide-name';
                nameSpan.textContent = slide.name;
                item.appendChild(nameSpan);

                const formatSpan = document.createElement('span');
                formatSpan.className = 'slide-format';
                formatSpan.textContent = slide.format;
                item.appendChild(formatSpan);

                item.addEventListener('click', async () => {
                    if (this._state.pendingSlideForPanel !== null && this._state.compareLayout) {
                        await this._state.compareLayout.loadSlideAt(
                            this._state.pendingSlideForPanel,
                            slide.id,
                            slide.name,
                        );
                    }
                    this._state.pendingSlideForPanel = null;
                    container.closest('.slide-picker-modal').remove();
                });

                list.appendChild(item);
            });

            container.appendChild(list);

        } catch (err) {
            container.textContent = '';
            const errP = document.createElement('p');
            errP.className = 'error';
            errP.textContent = `Error loading slides: ${err.message}`;
            container.appendChild(errP);
        }
    }

    // ==========================================
    // COMPONENT LIFECYCLE
    // ==========================================

    _cleanup() {
        const destroyKeys = [
            'detectionPanel', 'cellCountingPanel', 'clusteringPanel', 'clusteringOverlay',
            'countingPanel', 'layerManager', 'drawingTools', 'annotationLayer',
            'qualityBadge', 'driftDashboard', 'focusAssistPanel', 'autoTagBadge',
            'magnificationBar', 'heatmapOverlay', 'mlPanel', 'compareLayout', 'caseSidebar',
            'userMenu', 'loginPage',
        ];

        for (const key of destroyKeys) {
            if (this._state[key]) {
                this._state[key].destroy();
                this._state[key] = null;
            }
        }

        viewerManager.destroyAll();
        annotationStore.clear();

        this._state.viewer = null;
        this._state.folderBrowser = null;
        this._state.selectedSlide = null;
    }
}
