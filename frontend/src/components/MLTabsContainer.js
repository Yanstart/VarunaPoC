/**
 * MLTabsContainer - Tabbed container for all ML panels
 *
 * Replaces the 5 stacked accordions with a tab-based layout:
 * - Tab "Analyse" (MLPanel + FocusAssistPanel)
 * - Tab "Detection" (DetectionPanel)
 * - Tab "Comptage" (CellCountingPanel)
 * - Tab "Clustering" (ClusteringPanel)
 *
 * Features:
 * - Single tab visible at a time (no scrolling needed)
 * - Notification badges when results are available
 * - Active tab persisted in localStorage
 * - Compact tab bar with icons
 *
 * Note: innerHTML usage is safe here — only static SVG icons defined
 * as code constants are interpolated, no user-supplied data.
 *
 * @module components/MLTabsContainer
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { i18nService } from '../services/I18nService.js';

/** @type {string} localStorage key for active tab */
const STORAGE_KEY = 'varuna_ml_active_tab';

/**
 * Tab definitions with i18n keys and icons (static SVG, no user data)
 * @type {Array<{id: string, i18nKey: string, icon: string}>}
 */
const TAB_DEFS = [
    {
        id: 'analyse',
        i18nKey: 'tabs.analyse',
        icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
    },
    {
        id: 'detection',
        i18nKey: 'tabs.detection',
        icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    },
    {
        id: 'comptage',
        i18nKey: 'tabs.counting',
        icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" stroke-dasharray="4 2"/></svg>',
    },
    {
        id: 'clustering',
        i18nKey: 'tabs.clustering',
        icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="8" cy="8" r="3"/><circle cx="16" cy="16" r="3"/><circle cx="16" cy="8" r="2"/><circle cx="8" cy="16" r="2"/></svg>',
    },
    {
        id: 'similaire',
        i18nKey: 'tabs.similarity',
        icon: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="8" height="10" rx="1"/><rect x="14" y="3" width="8" height="10" rx="1"/><path d="M6 17v2M18 17v2M12 14v5"/></svg>',
    },
];

class MLTabsContainer {
    /**
     * @param {HTMLElement} container - Parent element to append the tabs to
     */
    constructor(container) {
        this.container = container;

        /** @type {HTMLElement} Root element */
        this.element = null;

        /** @type {HTMLElement} Tab bar element */
        this._tabBar = null;

        /** @type {Map<string, HTMLElement>} Tab pane containers keyed by tab ID */
        this._panes = new Map();

        /** @type {Map<string, HTMLElement>} Tab button elements keyed by tab ID */
        this._tabButtons = new Map();

        /** @type {Map<string, boolean>} Notification badge state per tab */
        this._badges = new Map();

        /** @type {string} Currently active tab ID */
        this._activeTab = this._loadActiveTab();

        /** @type {Array<Function>} Unsubscribe functions */
        this._unsubscribers = [];

        this._build();
        this._setupEventListeners();
    }

    /**
     * Build the DOM structure
     * @private
     */
    _build() {
        this.element = document.createElement('div');
        this.element.className = 'ml-tabs';

        // Tab bar
        this._tabBar = document.createElement('div');
        this._tabBar.className = 'ml-tabs__bar';
        this._tabBar.setAttribute('role', 'tablist');

        for (const def of TAB_DEFS) {
            const btn = document.createElement('button');
            btn.className = 'ml-tabs__tab';
            btn.dataset.tabId = def.id;
            const label = i18nService.t(def.i18nKey);
            btn.title = label;
            btn.setAttribute('role', 'tab');
            btn.setAttribute('aria-selected', def.id === this._activeTab ? 'true' : 'false');
            btn.setAttribute('aria-controls', `ml-tabpanel-${def.id}`);
            btn.id = `ml-tab-${def.id}`;

            // Icon (static SVG, safe)
            const iconSpan = document.createElement('span');
            iconSpan.className = 'ml-tabs__tab-icon';
            iconSpan.innerHTML = def.icon; // Safe: static SVG constant, no user data

            // Label
            const labelSpan = document.createElement('span');
            labelSpan.className = 'ml-tabs__tab-label';
            labelSpan.textContent = label;

            // Badge
            const badgeSpan = document.createElement('span');
            badgeSpan.className = 'ml-tabs__tab-badge';
            badgeSpan.style.display = 'none';

            btn.appendChild(iconSpan);
            btn.appendChild(labelSpan);
            btn.appendChild(badgeSpan);

            btn.addEventListener('click', () => this._activateTab(def.id));
            this._tabBar.appendChild(btn);
            this._tabButtons.set(def.id, btn);
        }

        this.element.appendChild(this._tabBar);

        // Pane containers
        const paneWrapper = document.createElement('div');
        paneWrapper.className = 'ml-tabs__panes';

        for (const def of TAB_DEFS) {
            const pane = document.createElement('div');
            pane.className = 'ml-tabs__pane';
            pane.dataset.tabId = def.id;
            pane.setAttribute('role', 'tabpanel');
            pane.id = `ml-tabpanel-${def.id}`;
            pane.setAttribute('aria-labelledby', `ml-tab-${def.id}`);
            paneWrapper.appendChild(pane);
            this._panes.set(def.id, pane);
        }

        this.element.appendChild(paneWrapper);
        this.container.appendChild(this.element);

        // Set initial active tab
        this._activateTab(this._activeTab);
    }

    /**
     * Setup event listeners for notification badges
     * @private
     */
    _setupEventListeners() {
        // Show badge on prediction complete
        this._unsubscribers.push(
            eventBus.on(Events.ML_PREDICTION_COMPLETE, () => {
                this._showBadge('analyse');
            }),
        );

        // Show badge on detection complete
        this._unsubscribers.push(
            eventBus.on(Events.DETECTION_COMPLETE, () => {
                this._showBadge('detection');
            }),
        );

        // Show badge on cell counting complete
        this._unsubscribers.push(
            eventBus.on(Events.CELL_COUNTING_COMPLETE, () => {
                this._showBadge('comptage');
            }),
        );

        // Show badge on clustering complete
        this._unsubscribers.push(
            eventBus.on(Events.CLUSTERING_COMPLETE, () => {
                this._showBadge('clustering');
            }),
        );
    }

    /**
     * Get the pane container for a given tab
     * @param {string} tabId - Tab ID
     * @returns {HTMLElement|null}
     */
    getPane(tabId) {
        return this._panes.get(tabId) || null;
    }

    /**
     * Activate a tab
     * @param {string} tabId - Tab ID to activate
     * @private
     */
    _activateTab(tabId) {
        this._activeTab = tabId;
        this._saveActiveTab(tabId);

        // Update tab buttons
        for (const [id, btn] of this._tabButtons) {
            btn.classList.toggle('ml-tabs__tab--active', id === tabId);
            btn.setAttribute('aria-selected', id === tabId ? 'true' : 'false');
        }

        // Update panes
        for (const [id, pane] of this._panes) {
            pane.classList.toggle('ml-tabs__pane--active', id === tabId);
        }

        // Clear badge for the activated tab
        this._hideBadge(tabId);
    }

    /**
     * Show notification badge on a tab
     * @param {string} tabId - Tab ID
     * @private
     */
    _showBadge(tabId) {
        // Don't show badge if this is the currently active tab
        if (tabId === this._activeTab) {
            return;
        }

        this._badges.set(tabId, true);
        const btn = this._tabButtons.get(tabId);
        if (btn) {
            const badge = btn.querySelector('.ml-tabs__tab-badge');
            if (badge) {
                badge.style.display = '';
            }
        }
    }

    /**
     * Hide notification badge on a tab
     * @param {string} tabId - Tab ID
     * @private
     */
    _hideBadge(tabId) {
        this._badges.delete(tabId);
        const btn = this._tabButtons.get(tabId);
        if (btn) {
            const badge = btn.querySelector('.ml-tabs__tab-badge');
            if (badge) {
                badge.style.display = 'none';
            }
        }
    }

    /**
     * Load active tab from localStorage
     * @returns {string} Active tab ID
     * @private
     */
    _loadActiveTab() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved && TAB_DEFS.some(d => d.id === saved)) {
                return saved;
            }
        } catch (_) {
            // noop
        }
        return 'analyse';
    }

    /**
     * Save active tab to localStorage
     * @param {string} tabId
     * @private
     */
    _saveActiveTab(tabId) {
        try {
            localStorage.setItem(STORAGE_KEY, tabId);
        } catch (_) {
            // noop
        }
    }

    /**
     * Destroy the container and clean up
     */
    destroy() {
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];

        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }

        this.element = null;
        this._tabBar = null;
        this._panes.clear();
        this._tabButtons.clear();
        this._badges.clear();
    }
}

export { MLTabsContainer };
export default MLTabsContainer;
