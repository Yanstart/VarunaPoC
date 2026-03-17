/**
 * Worklist View Component - "Mes cas" worklist
 *
 * Displays a list of cases assigned to the current user with
 * status filtering (pending, in_progress, completed).
 *
 * API:
 * - GET /api/slides/worklist
 *
 * @module components/WorklistView
 */

import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';

/**
 * Status configuration for display.
 * @type {Object<string, {label: string, cssClass: string}>}
 */
function getStatusConfig() {
    return {
        pending: { label: i18nService.t('worklist.statusPending'), cssClass: 'worklist-view__status--pending' },
        in_progress: { label: i18nService.t('worklist.statusInProgress'), cssClass: 'worklist-view__status--in_progress' },
        completed: { label: i18nService.t('worklist.statusCompleted'), cssClass: 'worklist-view__status--completed' },
    };
}

/**
 * Filter tab definitions.
 * @type {Array<{key: string, label: string}>}
 */
function getFilterTabs() {
    return [
        { key: 'all', label: i18nService.t('worklist.all') },
        { key: 'pending', label: i18nService.t('worklist.statusPending') },
        { key: 'in_progress', label: i18nService.t('worklist.statusInProgress') },
        { key: 'completed', label: i18nService.t('worklist.statusCompletedPlural') },
    ];
}

/**
 * Format an ISO date string to a human-readable relative date.
 *
 * @param {string} isoDate - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(isoDate) {
    try {
        const date = new Date(isoDate);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return i18nService.t('worklist.today');
        if (diffDays === 1) return i18nService.t('worklist.yesterday');
        if (diffDays < 7) return i18nService.t('worklist.daysAgo', { days: diffDays });
        return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
    } catch {
        return isoDate;
    }
}

/**
 * Create the WorklistView component.
 *
 * @param {Function} onSlideSelect - Callback when a slide card is clicked
 * @param {Function} [onViewToggle] - Callback to switch views
 * @returns {HTMLElement} The worklist view container element
 */
export function createWorklistView(onSlideSelect, onViewToggle) {
    const container = document.createElement('div');
    container.className = 'worklist-view';

    // ---- Header ----
    const header = document.createElement('div');
    header.className = 'worklist-view__header';

    const title = document.createElement('h2');
    title.className = 'worklist-view__title';
    title.textContent = i18nService.t('case.myCases');
    header.appendChild(title);

    if (onViewToggle) {
        const backBtn = document.createElement('button');
        backBtn.className = 'worklist-view__back-btn';
        backBtn.textContent = i18nService.t('case.caseView');
        backBtn.title = i18nService.t('worklist.backToCases');
        backBtn.addEventListener('click', () => {
            localStorage.setItem('varuna_home_view', 'cases');
            onViewToggle('cases');
        });
        header.appendChild(backBtn);
    }

    container.appendChild(header);

    // ---- Tabs bar ----
    const tabsBar = document.createElement('div');
    tabsBar.className = 'worklist-view__tabs';
    container.appendChild(tabsBar);

    // ---- Cards area ----
    const cardsArea = document.createElement('div');
    cardsArea.className = 'worklist-view__cards';
    container.appendChild(cardsArea);

    // ---- Internal state ----
    let allItems = [];
    let counts = {};
    let activeFilter = 'all';

    // ---- Build tabs ----
    const tabElements = {};

    getFilterTabs().forEach(tabDef => {
        const tab = document.createElement('button');
        tab.className = 'worklist-view__tab';
        tab.dataset.filter = tabDef.key;

        const labelSpan = document.createElement('span');
        labelSpan.textContent = tabDef.label;
        tab.appendChild(labelSpan);

        // Count badge (will be updated after data loads)
        if (tabDef.key !== 'all') {
            const countBadge = document.createElement('span');
            countBadge.className = 'worklist-view__count';
            countBadge.style.display = 'none';
            tab.appendChild(countBadge);
        }

        tab.addEventListener('click', () => {
            activeFilter = tabDef.key;
            updateActiveTab();
            renderCards();
        });

        tabsBar.appendChild(tab);
        tabElements[tabDef.key] = tab;
    });

    // Set initial active tab
    updateActiveTab();

    // ---- Load data ----
    loadWorklist();

    /**
     * Update tab active states and count badges.
     */
    function updateActiveTab() {
        getFilterTabs().forEach(tabDef => {
            const tab = tabElements[tabDef.key];
            if (tabDef.key === activeFilter) {
                tab.classList.add('worklist-view__tab--active');
            } else {
                tab.classList.remove('worklist-view__tab--active');
            }

            // Update count badge
            if (tabDef.key !== 'all') {
                const badge = tab.querySelector('.worklist-view__count');
                if (badge && counts[tabDef.key] !== undefined) {
                    badge.textContent = String(counts[tabDef.key]);
                    badge.style.display = counts[tabDef.key] > 0 ? 'inline' : 'none';
                }
            }
        });
    }

    /**
     * Load worklist data from API.
     */
    async function loadWorklist() {
        cardsArea.textContent = '';
        const loading = document.createElement('div');
        loading.className = 'worklist-view__loading';
        loading.textContent = i18nService.t('worklist.loading');
        cardsArea.appendChild(loading);

        try {
            const data = await apiService.getWorklist();
            allItems = data.items || [];
            counts = data.counts || {};

            // Sort by date most recent first (already sorted by backend, but ensure)
            allItems.sort((a, b) => b.assigned_date.localeCompare(a.assigned_date));

            updateActiveTab();
            renderCards();
        } catch (err) {
            console.error('[WorklistView] Failed to load worklist:', err);
            cardsArea.textContent = '';
            const errorEl = document.createElement('div');
            errorEl.className = 'worklist-view__error';
            errorEl.textContent = i18nService.t('worklist.loadError');
            cardsArea.appendChild(errorEl);
        }
    }

    /**
     * Render the worklist cards based on the active filter.
     */
    function renderCards() {
        cardsArea.textContent = '';

        const filtered = activeFilter === 'all'
            ? allItems
            : allItems.filter(item => item.status === activeFilter);

        if (filtered.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'worklist-view__empty';
            empty.textContent = i18nService.t('case.noneInCategory');
            cardsArea.appendChild(empty);
            return;
        }

        filtered.forEach(item => {
            const card = createCard(item);
            cardsArea.appendChild(card);
        });
    }

    /**
     * Create a single worklist card element.
     *
     * @param {Object} item - WorklistItem data
     * @returns {HTMLElement} The card element
     */
    function createCard(item) {
        const card = document.createElement('div');
        card.className = 'worklist-view__card';

        // Top row: slide name + badges
        const topRow = document.createElement('div');
        topRow.className = 'worklist-view__card-top';

        const nameEl = document.createElement('div');
        nameEl.className = 'worklist-view__card-name';
        nameEl.textContent = item.slide_name;
        topRow.appendChild(nameEl);

        // Badges container
        const badges = document.createElement('div');
        badges.className = 'worklist-view__card-badges';

        // Status badge
        const statusConfig = getStatusConfig()[item.status] || { label: item.status, cssClass: '' };
        const statusBadge = document.createElement('span');
        statusBadge.className = 'worklist-view__status ' + statusConfig.cssClass;
        statusBadge.textContent = statusConfig.label;
        badges.appendChild(statusBadge);

        // "Nouveau" badge
        if (item.is_new) {
            const newBadge = document.createElement('span');
            newBadge.className = 'worklist-view__badge-new';
            newBadge.textContent = i18nService.t('case.new');
            badges.appendChild(newBadge);
        }

        topRow.appendChild(badges);
        card.appendChild(topRow);

        // Case path
        const pathEl = document.createElement('div');
        pathEl.className = 'worklist-view__card-path';
        pathEl.textContent = item.case_path;
        card.appendChild(pathEl);

        // Date
        const dateEl = document.createElement('div');
        dateEl.className = 'worklist-view__card-date';
        dateEl.textContent = formatDate(item.assigned_date);
        card.appendChild(dateEl);

        // Click handler
        card.addEventListener('click', () => {
            if (onSlideSelect) {
                onSlideSelect({ id: item.slide_id, name: item.slide_name });
            }
        });

        return card;
    }

    return container;
}
