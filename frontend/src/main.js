/**
 * VarunaPoC Frontend - Entry Point
 *
 * Thin bootstrap: defines application state, injects CSS overrides,
 * and starts the Router which manages all pages and navigation.
 *
 * @module main
 */

import './style.css';

import { eventBus } from './core/EventBus.js';
import { Pages } from './core/Constants.js';
import { Router } from './core/Router.js';
import { apiService } from './services/ApiService.js';
import { viewerManager } from './viewers/ViewerManager.js';
import { themeService } from './services/ThemeService.js';

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

    /** Annotation components */
    annotationLayer: null,
    drawingTools: null,
    layerManager: null,
    detectionPanel: null,

    /** Pending slide for compare mode (selected from slide picker) */
    pendingSlideForPanel: null,

    /** Auth components */
    loginPage: null,
    userMenu: null,

    /** Cell counting panel */
    cellCountingPanel: null,

    /** Clustering */
    clusteringPanel: null,
    clusteringOverlay: null,

    /** Quality badge */
    qualityBadge: null,

    /** Drift dashboard */
    driftDashboard: null,

    /** Focus assist, auto-tag, magnification */
    focusAssistPanel: null,
    autoTagBadge: null,
    magnificationBar: null,

    /** Case navigation */
    caseSidebar: null,
    currentCase: null,
};

// ==========================================
// ADDITIONAL CSS FOR NEW FEATURES
// ==========================================

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
// THEME INITIALIZATION
// ==========================================

themeService.init();

// ==========================================
// START APPLICATION
// ==========================================

const router = new Router(appState);
router.start();

// Export for debugging
window.__VarunaApp = {
    state: appState,
    eventBus,
    viewerManager,
    apiService,
    router,
    themeService,
};
