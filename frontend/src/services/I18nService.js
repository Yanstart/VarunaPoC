/**
 * I18nService - Service d'internationalisation (singleton)
 *
 * Fournit la traduction de l'interface utilisateur en plusieurs langues.
 * Supporte le français (par défaut), l'anglais, le japonais, le chinois
 * simplifié et le hindi.
 *
 * Charge les traductions depuis des fichiers JSON locaux avec fallback
 * vers le français si une clé n'est pas trouvée.
 *
 * @module services/I18nService
 *
 * @example
 * import { i18nService } from './services/I18nService.js';
 * await i18nService.init();
 * i18nService.setLocale('en');
 * const label = i18nService.t('nav.home'); // "Home"
 */

import { API } from '../core/Constants.js';

/**
 * Singleton instance
 * @type {I18nService|null}
 */
let instance = null;

/**
 * Supported locale codes
 * @type {string[]}
 */
const SUPPORTED_LOCALES = ['fr', 'en', 'ja', 'zh', 'hi'];

/**
 * Default locale (French - existing application language)
 * @type {string}
 */
const DEFAULT_LOCALE = 'fr';

/**
 * LocalStorage key for persisting locale preference
 * @type {string}
 */
const STORAGE_KEY = 'varuna_locale';

/**
 * I18nService class - Singleton internationalization service
 */
class I18nService {
    /**
     * Create I18nService instance (use getInstance() instead)
     */
    constructor() {
        if (instance) {
            return instance;
        }

        /**
         * Current locale code
         * @type {string}
         * @private
         */
        this._locale = DEFAULT_LOCALE;

        /**
         * Loaded translations by locale
         * @type {Object<string, Object<string, string>>}
         * @private
         */
        this._translations = {};

        /**
         * Whether the service has been initialized
         * @type {boolean}
         * @private
         */
        this._initialized = false;

        /**
         * Listeners for locale change events
         * @type {Function[]}
         * @private
         */
        this._listeners = [];

        instance = this;
    }

    /**
     * Get the singleton instance
     * @returns {I18nService}
     */
    static getInstance() {
        if (!instance) {
            instance = new I18nService();
        }
        return instance;
    }

    /**
     * Initialize the service: load saved locale and translations
     * @returns {Promise<void>}
     */
    async init() {
        if (this._initialized) {
            return;
        }

        // Restore saved locale preference
        const savedLocale = this._getSavedLocale();
        if (savedLocale && SUPPORTED_LOCALES.includes(savedLocale)) {
            this._locale = savedLocale;
        }

        // Load French translations first (fallback)
        await this._loadTranslations('fr');

        // Load current locale if different from French
        if (this._locale !== 'fr') {
            await this._loadTranslations(this._locale);
        }

        this._initialized = true;
    }

    /**
     * Translate a key to the current locale
     *
     * Falls back to French if the key is not found in the current locale.
     * Returns the key itself if not found in any locale.
     *
     * @param {string} key - Translation key (e.g., "nav.home")
     * @param {Object} [params] - Optional interpolation parameters
     * @returns {string} Translated string
     */
    t(key, params) {
        // Try current locale
        const currentTranslations = this._translations[this._locale];
        if (currentTranslations && key in currentTranslations) {
            return this._interpolate(currentTranslations[key], params);
        }

        // Fallback to French
        const frTranslations = this._translations['fr'];
        if (frTranslations && key in frTranslations) {
            return this._interpolate(frTranslations[key], params);
        }

        // Return key as last resort
        return key;
    }

    /**
     * Set the current locale
     *
     * Loads translations if not already loaded, saves preference,
     * and notifies listeners.
     *
     * @param {string} locale - Locale code (fr, en, ja, zh, hi)
     * @returns {Promise<boolean>} True if locale was set successfully
     */
    async setLocale(locale) {
        if (!SUPPORTED_LOCALES.includes(locale)) {
            console.warn(`[I18n] Unsupported locale: ${locale}`);
            return false;
        }

        if (locale === this._locale) {
            return true;
        }

        // Load translations if needed
        if (!this._translations[locale]) {
            await this._loadTranslations(locale);
        }

        this._locale = locale;
        this._saveLocale(locale);
        this._notifyListeners();

        return true;
    }

    /**
     * Get the current locale code
     * @returns {string} Current locale code
     */
    getLocale() {
        return this._locale;
    }

    /**
     * Get list of supported locales with their display names
     * @returns {Array<{code: string, name: string}>}
     */
    getSupportedLocales() {
        const names = {
            'fr': 'Fran\u00e7ais',
            'en': 'English',
            'ja': '\u65e5\u672c\u8a9e',
            'zh': '\u4e2d\u6587\u7b80\u4f53',
            'hi': '\u0939\u093f\u0928\u094d\u0926\u0940',
        };
        return SUPPORTED_LOCALES.map(code => ({
            code,
            name: names[code] || code,
        }));
    }

    /**
     * Register a listener for locale changes
     * @param {Function} callback - Called with new locale code when locale changes
     * @returns {Function} Unsubscribe function
     */
    onLocaleChange(callback) {
        this._listeners.push(callback);
        return () => {
            this._listeners = this._listeners.filter(l => l !== callback);
        };
    }

    /**
     * Check if translations are loaded for a locale
     * @param {string} locale - Locale code
     * @returns {boolean}
     */
    hasTranslations(locale) {
        return locale in this._translations && Object.keys(this._translations[locale]).length > 0;
    }

    /**
     * Get all translation keys for the current locale
     * @returns {string[]}
     */
    getKeys() {
        const translations = this._translations[this._locale] || this._translations['fr'] || {};
        return Object.keys(translations);
    }

    // ==========================================
    // Private methods
    // ==========================================

    /**
     * Load translations for a locale
     * First tries backend API, then falls back to inline data.
     * @param {string} locale
     * @returns {Promise<void>}
     * @private
     */
    async _loadTranslations(locale) {
        // Try loading from backend API
        try {
            const response = await fetch(`${API.BASE_URL}/api/regional/i18n/${locale}`);
            if (response.ok) {
                const data = await response.json();
                if (data.translations) {
                    this._translations[locale] = data.translations;
                    return;
                }
            }
        } catch {
            // Backend not available, fall through to inline
        }

        // Try loading from local JSON file
        try {
            const module = await import(`../locales/${locale}.json`);
            this._translations[locale] = module.default || module;
            return;
        } catch {
            // JSON file not available, fall through to inline fallback
        }

        // Inline fallback for French (essential minimum)
        if (locale === 'fr' && !this._translations['fr']) {
            this._translations['fr'] = {
                'nav.home': 'Accueil',
                'nav.viewer': 'Visualiseur',
                'nav.compare': 'Comparer',
                'nav.slides': 'Lames',
                'slide.loading': 'Chargement de la lame...',
                'slide.error': 'Erreur de chargement de la lame',
                'slide.select': 'S\u00e9lectionner une lame',
                'btn.save': 'Enregistrer',
                'btn.cancel': 'Annuler',
                'btn.close': 'Fermer',
                'btn.search': 'Rechercher',
                'error.generic': 'Une erreur est survenue',
                'search.placeholder': 'Rechercher une lame...',
            };
        }
    }

    /**
     * Interpolate parameters into a translation string
     * Replaces {paramName} with the corresponding value
     * @param {string} str - Translation string with placeholders
     * @param {Object} [params] - Parameter values
     * @returns {string}
     * @private
     */
    _interpolate(str, params) {
        if (!params) {
            return str;
        }
        return str.replace(/\{(\w+)\}/g, (match, key) => {
            return key in params ? String(params[key]) : match;
        });
    }

    /**
     * Get saved locale from localStorage
     * @returns {string|null}
     * @private
     */
    _getSavedLocale() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch {
            return null;
        }
    }

    /**
     * Save locale preference to localStorage
     * @param {string} locale
     * @private
     */
    _saveLocale(locale) {
        try {
            localStorage.setItem(STORAGE_KEY, locale);
        } catch {
            // localStorage not available (e.g., private browsing)
        }
    }

    /**
     * Notify all listeners of a locale change
     * @private
     */
    _notifyListeners() {
        const locale = this._locale;
        this._listeners.forEach(callback => {
            try {
                callback(locale);
            } catch (err) {
                console.error('[I18n] Listener error:', err);
            }
        });
    }
}

/**
 * Singleton instance export
 * @type {I18nService}
 */
export const i18nService = I18nService.getInstance();

export default I18nService;
