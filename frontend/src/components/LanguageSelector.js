/**
 * LanguageSelector - Language picker dropdown
 *
 * Displays a compact dropdown allowing the user to switch the UI language.
 * Persists the choice via I18nService (localStorage) and emits a
 * LOCALE_CHANGED event so all components can re-render.
 *
 * @module components/LanguageSelector
 */

import { i18nService } from '../services/I18nService.js';
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

/**
 * Flag labels shown next to locale codes in the dropdown
 * @type {Object<string, string>}
 */
const LOCALE_FLAGS = {
    fr: 'FR',
    nl: 'NL',
    en: 'EN',
    ja: 'JA',
    zh: 'ZH',
    hi: 'HI',
};

export class LanguageSelector {
    /**
     * @param {HTMLElement} container - Parent element to append selector into
     */
    constructor(container) {
        this.container = container;
        this.element = document.createElement('div');
        this.element.className = 'language-selector';
        this._build();
        container.appendChild(this.element);
    }

    /**
     * Build the selector DOM
     * @private
     */
    _build() {
        const current = i18nService.getLocale();
        const locales = i18nService.getSupportedLocales();

        const select = document.createElement('select');
        select.className = 'language-selector__select';
        select.title = i18nService.t('lang.selector');
        select.setAttribute('aria-label', i18nService.t('lang.selector'));

        for (const loc of locales) {
            const opt = document.createElement('option');
            opt.value = loc.code;
            opt.textContent = `${LOCALE_FLAGS[loc.code] || loc.code} ${loc.name}`;
            if (loc.code === current) {
                opt.selected = true;
            }
            select.appendChild(opt);
        }

        select.addEventListener('change', async (e) => {
            const newLocale = e.target.value;
            try {
                await i18nService.setLocale(newLocale);
                // Full page reload to apply translations everywhere
                window.location.reload();
            } catch (err) {
                console.error('[LanguageSelector] Failed to set locale:', err);
                select.value = i18nService.getLocale();
            }
        });

        this.element.appendChild(select);
    }

    /**
     * Update the selector to reflect the current locale
     */
    refresh() {
        const select = this.element.querySelector('select');
        if (select) {
            select.value = i18nService.getLocale();
            select.title = i18nService.t('lang.selector');
            select.setAttribute('aria-label', i18nService.t('lang.selector'));
        }
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}
