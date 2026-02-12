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
import { authService } from './AuthService.js';

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
            const headers = { 'Accept': 'application/json' };
            this._injectAuthHeader(headers);

            const response = await fetch(url, { method: 'GET', headers });

            if (response.status === 401) {
                // Try token refresh once
                const refreshed = await authService.refreshTokenSilently();
                if (refreshed) {
                    this._injectAuthHeader(headers);
                    const retryResponse = await fetch(url, { method: 'GET', headers });
                    if (retryResponse.ok) return retryResponse.json();
                }
                // Redirect to login
                if (authService.authEnabled) {
                    authService.login();
                    return;
                }
            }

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
            const headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            };
            this._injectAuthHeader(headers);

            const response = await fetch(url, {
                method,
                headers,
                body: JSON.stringify(body)
            });

            if (response.status === 401) {
                const refreshed = await authService.refreshTokenSilently();
                if (refreshed) {
                    this._injectAuthHeader(headers);
                    const retryResponse = await fetch(url, {
                        method, headers, body: JSON.stringify(body)
                    });
                    if (retryResponse.ok) return retryResponse.json();
                }
                if (authService.authEnabled) {
                    authService.login();
                    return;
                }
            }

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

    /**
     * Inject Authorization Bearer header if token available.
     * @param {Object} headers - Headers object to modify
     * @private
     */
    _injectAuthHeader(headers) {
        const token = authService.accessToken;
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
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
        return this.post('/api/ml/models/reload', {
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
        const body = {};

        if (options.region) {
            body.region = options.region;
        }
        if (options.modelId) {
            body.model_id = options.modelId;
        }
        if (options.numMcSamples) {
            body.num_mc_samples = options.numMcSamples;
        }

        return this.post(`/api/ml/predict/${encodeURIComponent(slideId)}`, body);
    }

    /**
     * Generate heatmap for a slide
     * @param {string} slideId - Slide ID
     * @param {string} predictionClass - Target class for heatmap
     * @param {Object} [options={}] - Heatmap options
     * @returns {Promise<Object>} Heatmap result with base64 image
     */
    async generateHeatmap(slideId, predictionClass, options = {}) {
        const params = new URLSearchParams({
            prediction_class: predictionClass,
            resolution_level: options.resolutionLevel || 2,
            colormap: options.colormap || 'jet'
        });
        return this.get(`/api/ml/heatmap/${encodeURIComponent(slideId)}?${params}`);
    }

    /**
     * Extract features from a slide
     * @param {string} slideId - Slide ID
     * @param {Object} [options={}] - Extraction options
     * @returns {Promise<Object>} Feature extraction result
     */
    async extractFeatures(slideId, options = {}) {
        return this.post(`/api/ml/features/${encodeURIComponent(slideId)}`, {
            tile_size: options.tileSize || 224,
            overlap: options.overlap || 0
        });
    }

    // ==========================================
    // ANNOTATIONS API
    // ==========================================

    /**
     * Create an annotation on a slide
     * @param {string} slideId - Slide ID
     * @param {Object} data - Annotation data (geometry, geometry_type, annotation_type, etc.)
     * @returns {Promise<Object>} Created annotation
     */
    async createAnnotation(slideId, data) {
        return this.post(`/api/annotations/${encodeURIComponent(slideId)}`, data);
    }

    /**
     * Get annotations for a slide
     * @param {string} slideId - Slide ID
     * @param {Object} [params={}] - Query parameters (annotation_type, label_id, bbox_*)
     * @returns {Promise<Array>} List of annotations
     */
    async getAnnotations(slideId, params = {}) {
        return this.get(`/api/annotations/${encodeURIComponent(slideId)}`, {
            useCache: false,
            params,
        });
    }

    /**
     * Update an annotation
     * @param {string} slideId - Slide ID
     * @param {string} annotationId - Annotation UUID
     * @param {Object} data - Fields to update
     * @returns {Promise<Object>} Updated annotation
     */
    async updateAnnotation(slideId, annotationId, data) {
        const url = `${this.baseUrl}/api/annotations/${encodeURIComponent(slideId)}/${annotationId}`;
        return this._fetchWithBody(url, 'PUT', data);
    }

    /**
     * Delete an annotation
     * @param {string} slideId - Slide ID
     * @param {string} annotationId - Annotation UUID
     * @returns {Promise<void>}
     */
    async deleteAnnotation(slideId, annotationId) {
        const url = `${this.baseUrl}/api/annotations/${encodeURIComponent(slideId)}/${annotationId}`;
        const headers = {};
        this._injectAuthHeader(headers);
        const response = await fetch(url, { method: 'DELETE', headers });
        if (!response.ok && response.status !== 204) {
            throw new ApiError(`Delete failed: ${response.status}`, response.status);
        }
    }

    /**
     * Batch create annotations
     * @param {string} slideId - Slide ID
     * @param {Array} annotations - Array of annotation data
     * @returns {Promise<Array>} Created annotations
     */
    async batchCreateAnnotations(slideId, annotations) {
        return this.post(`/api/annotations/${encodeURIComponent(slideId)}/batch`, {
            annotations,
        });
    }

    /**
     * Export annotations as GeoJSON
     * @param {string} slideId - Slide ID
     * @returns {Promise<Object>} GeoJSON FeatureCollection
     */
    async exportAnnotations(slideId) {
        return this.get(`/api/annotations/${encodeURIComponent(slideId)}/export`, {
            useCache: false,
        });
    }

    /**
     * Get annotation statistics for a slide
     * @param {string} slideId - Slide ID
     * @returns {Promise<Object>} Stats with total, by_type, by_label, confidence_distribution
     */
    async getAnnotationStats(slideId) {
        return this.get(`/api/annotations/${encodeURIComponent(slideId)}/stats`, {
            useCache: false,
        });
    }

    // ==========================================
    // LABELS API
    // ==========================================

    /**
     * Get all annotation labels
     * @returns {Promise<Array>} List of labels
     */
    async getLabels() {
        return this.get('/api/labels/');
    }

    /**
     * Create a new label
     * @param {Object} data - {name, color, category, description}
     * @returns {Promise<Object>} Created label
     */
    async createLabel(data) {
        return this.post('/api/labels/', data);
    }

    // ==========================================
    // DETECTION API
    // ==========================================

    /**
     * Run auto-detection on a slide
     * @param {string} slideId - Slide ID
     * @param {Object} [params={}] - Detection parameters
     * @returns {Promise<Object>} Detection result with GeoJSON
     */
    async detect(slideId, params = {}) {
        const queryParams = new URLSearchParams();
        if (params.threshold !== undefined) queryParams.set('threshold', params.threshold);
        if (params.min_area !== undefined) queryParams.set('min_area', params.min_area);
        if (params.simplify_tolerance !== undefined) queryParams.set('simplify_tolerance', params.simplify_tolerance);
        if (params.resolution_level !== undefined) queryParams.set('resolution_level', params.resolution_level);
        if (params.prediction_class) queryParams.set('prediction_class', params.prediction_class);

        const qs = queryParams.toString();
        const url = `/api/ml/detect/${encodeURIComponent(slideId)}${qs ? '?' + qs : ''}`;
        return this.post(url, {});
    }

    // ==========================================
    // AUTH API (Phase 3)
    // ==========================================

    /**
     * Get current user info
     * @returns {Promise<Object>} Auth status with user info
     */
    async getAuthMe() {
        return this.get('/api/auth/me', { useCache: false });
    }

    /**
     * Activate break-glass emergency access
     * @param {string} reason - Medical justification
     * @param {number} [durationMinutes=30] - Duration in minutes
     * @returns {Promise<Object>} Break-glass activation result
     */
    async activateBreakGlass(reason, durationMinutes = 30) {
        return this.post('/api/auth/break-glass', {
            reason,
            duration_minutes: durationMinutes,
        });
    }

    /**
     * Save session state for roaming
     * @param {Object} state - Viewer state to save
     * @returns {Promise<Object>} Save confirmation
     */
    async saveSessionState(state) {
        return this.post('/api/auth/session', state);
    }

    /**
     * Load saved session state
     * @returns {Promise<Object>} Saved session state
     */
    async loadSessionState() {
        return this.get('/api/auth/session', { useCache: false });
    }

    // ==========================================
    // QUALITY METRICS API (Phase 4)
    // ==========================================

    /**
     * Get annotators for a slide
     * @param {string} slideId - Slide ID
     * @returns {Promise<Array>} List of annotator info
     */
    async getAnnotators(slideId) {
        return this.get(`/api/quality/${encodeURIComponent(slideId)}/annotators`, {
            useCache: false,
        });
    }

    /**
     * Compute Cohen's kappa between two annotators
     * @param {string} slideId - Slide ID
     * @param {Object} params - {annotator_a, annotator_b, iou_threshold, matching_strategy}
     * @returns {Promise<Object>} KappaResult
     */
    async computeKappa(slideId, params) {
        return this.post(`/api/quality/${encodeURIComponent(slideId)}/kappa`, params);
    }

    /**
     * Compute Fleiss' kappa for multiple annotators
     * @param {string} slideId - Slide ID
     * @param {Object} params - {annotators, grid_cell_size}
     * @returns {Promise<Object>} FleissKappaResult
     */
    async computeFleissKappa(slideId, params) {
        return this.post(`/api/quality/${encodeURIComponent(slideId)}/fleiss`, params);
    }

    /**
     * Compute confusion matrix between two annotators
     * @param {string} slideId - Slide ID
     * @param {Object} params - PairwiseRequest
     * @returns {Promise<Object>} ConfusionMatrixResult
     */
    async computeConfusionMatrix(slideId, params) {
        return this.post(`/api/quality/${encodeURIComponent(slideId)}/confusion-matrix`, params);
    }

    /**
     * Compute per-label F1/precision/recall
     * @param {string} slideId - Slide ID
     * @param {Object} params - PairwiseRequest
     * @returns {Promise<Object>} PerLabelMetricsResult
     */
    async computeF1Metrics(slideId, params) {
        return this.post(`/api/quality/${encodeURIComponent(slideId)}/f1`, params);
    }

    /**
     * Compute IoU distribution between two annotators
     * @param {string} slideId - Slide ID
     * @param {Object} params - PairwiseRequest
     * @returns {Promise<Object>} IoUDistributionResult
     */
    async computeIoUDistribution(slideId, params) {
        return this.post(`/api/quality/${encodeURIComponent(slideId)}/iou-distribution`, params);
    }

    /**
     * Get disagreement regions as GeoJSON
     * @param {string} slideId - Slide ID
     * @param {Object} params - PairwiseRequest
     * @returns {Promise<Object>} DisagreementHeatmapResult (GeoJSON FeatureCollection)
     */
    async getDisagreements(slideId, params) {
        return this.post(`/api/quality/${encodeURIComponent(slideId)}/disagreements`, params);
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
