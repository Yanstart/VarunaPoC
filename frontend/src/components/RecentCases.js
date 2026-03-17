/**
 * Recent Cases Component - "Cas recents" section
 *
 * Displays a horizontal scrollable row of recently viewed case cards.
 *
 * API:
 * - GET /api/slides/history?limit=20
 *
 * @module components/RecentCases
 */

import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';

/**
 * Format an ISO datetime string to a human-readable relative time.
 *
 * @param {string} isoDatetime - ISO datetime string
 * @returns {string} Formatted relative time
 */
function formatRelativeTime(isoDatetime) {
    try {
        const date = new Date(isoDatetime);
        const now = new Date();
        const diffMs = now - date;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMinutes < 1) return i18nService.t('time.justNow');
        if (diffMinutes < 60) return i18nService.t('time.minutesAgo', { minutes: diffMinutes });
        if (diffHours < 24) return i18nService.t('time.hoursAgo', { hours: diffHours });
        if (diffDays === 1) return i18nService.t('time.yesterday');
        if (diffDays < 7) return i18nService.t('time.daysAgo', { days: diffDays });
        return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
    } catch {
        return isoDatetime;
    }
}

/**
 * Create the RecentCases component.
 *
 * @param {Function} onSlideSelect - Callback when a case card is clicked
 * @returns {HTMLElement} The recent cases container element
 */
export function createRecentCases(onSlideSelect) {
    const container = document.createElement('div');
    container.className = 'recent-cases';

    // Title
    const title = document.createElement('div');
    title.className = 'recent-cases__title';
    title.textContent = i18nService.t('case.recent');
    container.appendChild(title);

    // Scrollable row
    const scrollRow = document.createElement('div');
    scrollRow.className = 'recent-cases__scroll';
    container.appendChild(scrollRow);

    // Load data
    loadHistory();

    /**
     * Load history data from API.
     */
    async function loadHistory() {
        scrollRow.textContent = '';

        const loadingEl = document.createElement('div');
        loadingEl.className = 'recent-cases__loading';
        loadingEl.textContent = i18nService.t('generic.loading');
        scrollRow.appendChild(loadingEl);

        try {
            const data = await apiService.getHistory(10);
            const items = data.items || [];

            scrollRow.textContent = '';

            if (items.length === 0) {
                const empty = document.createElement('div');
                empty.className = 'recent-cases__empty';
                empty.textContent = i18nService.t('case.noneRecent');
                scrollRow.appendChild(empty);
                return;
            }

            items.forEach(item => {
                const card = createCard(item);
                scrollRow.appendChild(card);
            });
        } catch (err) {
            console.error('[RecentCases] Failed to load history:', err);
            scrollRow.textContent = '';
            const errorEl = document.createElement('div');
            errorEl.className = 'recent-cases__error';
            errorEl.textContent = i18nService.t('generic.errorLoading');
            scrollRow.appendChild(errorEl);
        }
    }

    /**
     * Create a single recent case card element.
     *
     * @param {Object} item - HistoryItem data
     * @returns {HTMLElement} The card element
     */
    function createCard(item) {
        const card = document.createElement('div');
        card.className = 'recent-cases__card';

        // Slide name
        const nameEl = document.createElement('div');
        nameEl.className = 'recent-cases__name';
        nameEl.textContent = item.slide_name;
        nameEl.title = item.slide_name;
        card.appendChild(nameEl);

        // Last viewed time
        const timeEl = document.createElement('div');
        timeEl.className = 'recent-cases__time';
        timeEl.textContent = formatRelativeTime(item.viewed_at);
        card.appendChild(timeEl);

        // View count
        const countEl = document.createElement('div');
        countEl.className = 'recent-cases__count';
        countEl.textContent = item.view_count === 1
            ? i18nService.t('case.viewCount', { count: item.view_count })
            : i18nService.t('case.viewCountPlural', { count: item.view_count });
        card.appendChild(countEl);

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
