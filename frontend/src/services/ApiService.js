/**
 * ApiService - Class-based API client for VarunaPoC backend
 *
 * Provides a structured interface for all backend API calls.
 * Implements error handling, caching, and request management.
 *
 * @module services/ApiService
 *
 * @example
 * const api = ApiService.getInstance();
 * const slides = await api.fetchSlides();
 * const info = await api.getSlideInfo('abc123');
 */

import { API } from '../core/Constants.js';

/**
 * Singleton instance
 * @type {ApiService|null}
 */
let instance = null;

/**
 * ApiService class - Singleton API client
 */
class ApiService {
    /**
     * Create ApiService instance (use getInstance() instead)
     */
    constructor() {
        if (instance) {
            return instance;
        }

        /**
         * Base URL for API
         * @type {string}
         */
        this.baseUrl = API.BASE_URL;

        /**
         * Request cache (simple in-memory)
         * @type {Map<string, { data: any, timestamp: number }>}
         * @private
         */
        this._cache = new Map();

        /**
         * Cache TTL in milliseconds (5 minutes)
         * @type {number}
         */
        this.cacheTTL = 5 * 60 * 1000;

        /**
         * Pending requests (for deduplication)
         * @type {Map<string, Promise>}
         * @private
         */
        this._pending = new Map();

        instance = this;
    }

    /**
     * Get singleton instance
     * @returns {ApiService}
     */
    static getInstance() {
        if (!instance) {
            instance = new ApiService();
        }
        return instance;
    }

    // ==========================================
    // CORE REQUEST METHODS
    // ==========================================

    /**
     * Make a GET request
     * @param {string} endpoint - API endpoint (without base URL)
     * @param {Object} [options={}] - Request options
     * @param {boolean} [options.useCache=true] - Use cached response if available
     * @param {Object} [options.params] - Query parameters
     * @returns {Promise<any>} Response data
     * @throws {Error} If request fails
     */
    async get(endpoint, options = {}) {
        const { useCache = true, params = {} } = options;

        // Build URL with query params
        let url = `${this.baseUrl}${endpoint}`;
        const queryString = new URLSearchParams(params).toString();
        if (queryString) {
            url += `?${queryString}`;
        }

        // Check cache
        if (useCache) {
            const cached = this._getFromCache(url);
            if (cached) {
                return cached;
            }
        }

        // Check for pending request (deduplication)
        if (this._pending.has(url)) {
            return this._pending.get(url);
        }

        // Make request
        const requestPromise = this._fetch(url);
        this._pending.set(url, requestPromise);

        try {
            const data = await requestPromise;

            // Cache response
            if (useCache) {
                this._setCache(url, data);
            }

            return data;

        } finally {
            this._pending.delete(url);
        }
    }

    /**
     * Internal fetch with error handling
     * @param {string} url - Full URL
     * @returns {Promise<any>} Response data
     * @private
     */
    async _fetch(url) {
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const message = errorData.detail || `HTTP ${response.status}: ${response.statusText}`;
                throw new ApiError(message, response.status, errorData);
            }

            return response.json();

        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }

            // Network error
            throw new ApiError(
                `Network error: ${error.message}`,
                0,
                { originalError: error }
            );
        }
    }

    // ==========================================
    // CACHE METHODS
    // ==========================================

    /**
     * Get from cache if valid
     * @param {string} key - Cache key
     * @returns {any|null} Cached data or null
     * @private
     */
    _getFromCache(key) {
        const cached = this._cache.get(key);

        if (cached && (Date.now() - cached.timestamp) < this.cacheTTL) {
            return cached.data;
        }

        // Expired, remove from cache
        if (cached) {
            this._cache.delete(key);
        }

        return null;
    }

    /**
     * Set cache entry
     * @param {string} key - Cache key
     * @param {any} data - Data to cache
     * @private
     */
    _setCache(key, data) {
        this._cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Clear all cache
     */
    clearCache() {
        this._cache.clear();
    }

    /**
     * Clear cache for specific endpoint
     * @param {string} endpoint - Endpoint to clear
     */
    clearCacheFor(endpoint) {
        const prefix = `${this.baseUrl}${endpoint}`;

        for (const key of this._cache.keys()) {
            if (key.startsWith(prefix)) {
                this._cache.delete(key);
            }
        }
    }

    // ==========================================
    // SLIDES API
    // ==========================================

    /**
     * Fetch all slides
     * @returns {Promise<{ count: number, slides: Array }>}
     */
    async fetchSlides() {
        return this.get('/api/slides/');
    }

    /**
     * Get slide info
     * @param {string} slideId - Slide ID
     * @returns {Promise<Object>} Slide metadata
     */
    async getSlideInfo(slideId) {
        return this.get(`/api/slides/${slideId}/info`);
    }

    /**
     * Get DZI metadata for tile streaming
     * @param {string} slideId - Slide ID
     * @returns {Promise<Object>} DZI metadata
     */
    async getDziMetadata(slideId) {
        return this.get(`/api/slides/${slideId}/dzi.json`);
    }

    /**
     * Get overview image URL
     * @param {string} slideId - Slide ID
     * @returns {string} Overview image URL
     */
    getOverviewUrl(slideId) {
        return `${this.baseUrl}/api/slides/${slideId}/overview`;
    }

    /**
     * Get tile URL
     * @param {string} slideId - Slide ID
     * @param {number} level - Pyramid level
     * @param {number} x - Column
     * @param {number} y - Row
     * @returns {string} Tile URL
     */
    getTileUrl(slideId, level, x, y) {
        return `${this.baseUrl}/api/slides/${slideId}/tiles/${level}/${x}_${y}.jpg`;
    }

    // ==========================================
    // BROWSE API
    // ==========================================

    /**
     * Browse directory
     * @param {string} [path='/'] - Directory path
     * @returns {Promise<Object>} Directory contents
     */
    async browse(path = '/') {
        return this.get('/api/slides/browse', {
            params: { path }
        });
    }

    // ==========================================
    // HEALTH API
    // ==========================================

    /**
     * Check API health
     * @returns {Promise<Object>} Health status
     */
    async checkHealth() {
        return this.get('/api/health', { useCache: false });
    }

    /**
     * Check if API is available
     * @returns {Promise<boolean>}
     */
    async isAvailable() {
        try {
            await this.checkHealth();
            return true;
        } catch {
            return false;
        }
    }
}

/**
 * Custom error class for API errors
 */
class ApiError extends Error {
    /**
     * Create ApiError
     * @param {string} message - Error message
     * @param {number} status - HTTP status code
     * @param {Object} [data={}] - Additional error data
     */
    constructor(message, status, data = {}) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }

    /**
     * Check if error is a network error
     * @returns {boolean}
     */
    isNetworkError() {
        return this.status === 0;
    }

    /**
     * Check if error is a client error (4xx)
     * @returns {boolean}
     */
    isClientError() {
        return this.status >= 400 && this.status < 500;
    }

    /**
     * Check if error is a server error (5xx)
     * @returns {boolean}
     */
    isServerError() {
        return this.status >= 500;
    }

    /**
     * Check if resource not found (404)
     * @returns {boolean}
     */
    isNotFound() {
        return this.status === 404;
    }
}

// Create singleton instance
export const apiService = ApiService.getInstance();

// Export class and error for advanced usage
export { ApiService, ApiError };

// Default export
export default apiService;
