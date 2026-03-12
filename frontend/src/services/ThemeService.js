/**
 * ThemeService - Manages light/dark theme switching
 *
 * Handles theme initialization, toggling, localStorage persistence,
 * and respect for the system prefers-color-scheme preference.
 *
 * Theme is applied via data-theme attribute on document.documentElement,
 * which activates the corresponding CSS variable overrides in variables.css.
 *
 * @module services/ThemeService
 */

import { eventBus } from '../core/EventBus.js';
import { Events, StorageKeys } from '../core/Constants.js';

/** @type {'dark'|'light'} */
const DARK = 'dark';
/** @type {'dark'|'light'} */
const LIGHT = 'light';

class ThemeService {
    constructor() {
        /** @type {'dark'|'light'} */
        this._theme = DARK;
        this._mediaQuery = null;
    }

    /**
     * Initialize the theme service.
     * Reads from localStorage first, falls back to system preference.
     * Sets the data-theme attribute and listens for system preference changes.
     */
    init() {
        const saved = this._loadFromStorage();

        if (saved === DARK || saved === LIGHT) {
            this._theme = saved;
        } else {
            // No saved preference: respect system setting
            this._theme = this._getSystemPreference();
        }

        this._apply();
        this._listenToSystemChanges();
    }

    /**
     * Get the current theme.
     * @returns {'dark'|'light'}
     */
    get current() {
        return this._theme;
    }

    /**
     * Whether the current theme is dark.
     * @returns {boolean}
     */
    get isDark() {
        return this._theme === DARK;
    }

    /**
     * Toggle between dark and light themes.
     * Persists the choice and emits a THEME_CHANGED event.
     */
    toggle() {
        this._theme = this._theme === DARK ? LIGHT : DARK;
        this._apply();
        this._saveToStorage();
        eventBus.emit(Events.THEME_CHANGED, { theme: this._theme });
    }

    /**
     * Set a specific theme.
     * @param {'dark'|'light'} theme
     */
    set(theme) {
        if (theme !== DARK && theme !== LIGHT) { return; }
        if (theme === this._theme) { return; }
        this._theme = theme;
        this._apply();
        this._saveToStorage();
        eventBus.emit(Events.THEME_CHANGED, { theme: this._theme });
    }

    /**
     * Apply the current theme to the document.
     * @private
     */
    _apply() {
        document.documentElement.setAttribute('data-theme', this._theme);
    }

    /**
     * Read the system color scheme preference.
     * @returns {'dark'|'light'}
     * @private
     */
    _getSystemPreference() {
        if (typeof window !== 'undefined' && window.matchMedia) {
            return window.matchMedia('(prefers-color-scheme: light)').matches ? LIGHT : DARK;
        }
        return DARK;
    }

    /**
     * Listen for system color scheme changes.
     * Only applies if the user has no saved preference.
     * @private
     */
    _listenToSystemChanges() {
        if (typeof window === 'undefined' || !window.matchMedia) { return; }
        this._mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
        this._onSystemChange = (e) => {
            // Only auto-switch if user has not manually chosen a theme
            const saved = this._loadFromStorage();
            if (saved) { return; }
            this._theme = e.matches ? LIGHT : DARK;
            this._apply();
            eventBus.emit(Events.THEME_CHANGED, { theme: this._theme });
        };
        this._mediaQuery.addEventListener('change', this._onSystemChange);
    }

    /**
     * Load theme from localStorage.
     * @returns {string|null}
     * @private
     */
    _loadFromStorage() {
        try {
            return localStorage.getItem(StorageKeys.THEME);
        } catch (_) {
            return null;
        }
    }

    /**
     * Save theme to localStorage.
     * @private
     */
    _saveToStorage() {
        try {
            localStorage.setItem(StorageKeys.THEME, this._theme);
        } catch (_) {
            // localStorage unavailable (e.g., private browsing)
        }
    }
}

/** Singleton instance */
export const themeService = new ThemeService();
