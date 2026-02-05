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
     * Make a POST request
     * @param {string} endpoint - API endpoint
     * @param {Object} body - Request body
     * @returns {Promise<any>} Response data
     */
    async post(endpoint, body = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        return this._fetchWithBody(url, 'POST', body);
    }

    /**
     * Internal fetch with error handling (GET)
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

    /**
     * Internal fetch with body (POST/PUT/PATCH)
     * @param {string} url - Full URL
     * @param {string} method - HTTP method
     * @param {Object} body - Request body
     * @returns {Promise<any>} Response data
     * @private
     */
    async _fetchWithBody(url, method, body) {
        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
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
    // ML API
    // ==========================================

    /**
     * Get ML service health
     * @returns {Promise<Object>} ML service status
     */
    async getMLHealth() {
        return this.get('/api/ml/health', { useCache: false });
    }

    /**
     * List available ML models
     * @returns {Promise<Array>} List of models
     */
    async listModels() {
        return this.get('/api/ml/models');
    }

    /**
     * Load a model into memory
     * @param {string} modelId - Model identifier
     * @param {Object} [config={}] - Model configuration
     * @returns {Promise<Object>} Load result
     */
    async loadModel(modelId, config = {}) {
        return this.post('/api/ml/models/load', {
            model_id: modelId,
            ...config
        });
    }

    /**
     * Run prediction on a slide
     * @param {string} slideId - Slide ID
     * @param {Object} [options={}] - Prediction options
     * @param {Object} [options.region] - Region {x, y, width, height}
     * @param {string} [options.modelId] - Specific model to use
     * @param {number} [options.numMcSamples=10] - Monte Carlo samples for uncertainty
     * @returns {Promise<Object>} Prediction result
     */
    async predict(slideId, options = {}) {
        const body = {
            slide_id: slideId
        };

        if (options.region) {
            body.region = options.region;
        }
        if (options.modelId) {
            body.model_id = options.modelId;
        }
        if (options.numMcSamples) {
            body.num_mc_samples = options.numMcSamples;
        }

        return this.post('/api/ml/predict', body);
    }

    /**
     * Generate heatmap for a slide
     * @param {string} slideId - Slide ID
     * @param {string} predictionClass - Target class for heatmap
     * @param {Object} [options={}] - Heatmap options
     * @returns {Promise<Object>} Heatmap result with base64 image
     */
    async generateHeatmap(slideId, predictionClass, options = {}) {
        return this.post('/api/ml/heatmap', {
            slide_id: slideId,
            prediction_class: predictionClass,
            resolution_level: options.resolutionLevel || 2,
            colormap: options.colormap || 'jet'
        });
    }

    /**
     * Extract features from a slide
     * @param {string} slideId - Slide ID
     * @param {Object} [options={}] - Extraction options
     * @returns {Promise<Object>} Feature extraction result
     */
    async extractFeatures(slideId, options = {}) {
        return this.post('/api/ml/features/extract', {
            slide_id: slideId,
            tile_size: options.tileSize || 224,
            overlap: options.overlap || 0
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
