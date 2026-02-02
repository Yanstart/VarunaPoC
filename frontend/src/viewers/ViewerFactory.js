/**
 * ViewerFactory - Factory Pattern for creating ViewerInstance objects
 *
 * Provides a centralized way to create viewer instances with consistent
 * configuration. Supports different viewer types and presets.
 *
 * @module viewers/ViewerFactory
 *
 * @example
 * // Create a standard viewer
 * const viewer = ViewerFactory.create('viewer-1', container);
 *
 * // Create with options
 * const viewer = ViewerFactory.create('viewer-2', container, {
 *     showNavigator: false,
 *     preset: 'minimal'
 * });
 *
 * // Create from preset
 * const viewer = ViewerFactory.createFromPreset('compare', 'viewer-3', container);
 */

import { ViewerInstance } from './ViewerInstance.js';

/**
 * Viewer presets for different use cases
 * @type {Object.<string, Object>}
 */
const VIEWER_PRESETS = {
    /**
     * Default preset - full featured viewer
     */
    default: {
        showNavigator: true,
        emitEvents: true
    },

    /**
     * Minimal preset - no navigator, lightweight
     */
    minimal: {
        showNavigator: false,
        emitEvents: true
    },

    /**
     * Compare mode - optimized for side-by-side comparison
     */
    compare: {
        showNavigator: true,
        emitEvents: true
    },

    /**
     * Thumbnail preset - small preview viewer
     */
    thumbnail: {
        showNavigator: false,
        emitEvents: false
    },

    /**
     * Fullscreen preset - single viewer focus
     */
    fullscreen: {
        showNavigator: true,
        emitEvents: true
    }
};

/**
 * ViewerFactory class - Factory for creating ViewerInstance objects
 */
class ViewerFactory {
    /**
     * Create a new ViewerInstance
     * @param {string} [id] - Unique identifier (auto-generated if omitted)
     * @param {HTMLElement|string} container - Container element or ID
     * @param {Object} [options={}] - Configuration options
     * @param {boolean} [options.showNavigator=true] - Show mini-map
     * @param {boolean} [options.emitEvents=true] - Emit global events
     * @param {string} [options.preset] - Apply a preset configuration
     * @returns {ViewerInstance} New viewer instance
     *
     * @example
     * const viewer = ViewerFactory.create('my-viewer', document.getElementById('container'));
     */
    static create(id, container, options = {}) {
        // Apply preset if specified
        const presetOptions = options.preset ? VIEWER_PRESETS[options.preset] : {};

        // Merge options: default < preset < explicit options
        const mergedOptions = {
            ...VIEWER_PRESETS.default,
            ...presetOptions,
            ...options
        };

        // Remove preset key from final options
        delete mergedOptions.preset;

        // Validate container
        const containerElement = typeof container === 'string'
            ? document.getElementById(container)
            : container;

        if (!containerElement) {
            throw new Error(`ViewerFactory.create: Container not found`);
        }

        // Create and return instance
        const instance = new ViewerInstance(id, containerElement, mergedOptions);

        console.log(`[ViewerFactory] Created viewer "${instance.id}" with options:`, mergedOptions);

        return instance;
    }

    /**
     * Create a viewer from a preset
     * @param {string} presetName - Name of the preset
     * @param {string} [id] - Unique identifier
     * @param {HTMLElement|string} container - Container element or ID
     * @param {Object} [extraOptions={}] - Additional options to merge
     * @returns {ViewerInstance} New viewer instance
     *
     * @example
     * const compareViewer = ViewerFactory.createFromPreset('compare', 'v1', container);
     */
    static createFromPreset(presetName, id, container, extraOptions = {}) {
        if (!VIEWER_PRESETS[presetName]) {
            console.warn(`[ViewerFactory] Unknown preset "${presetName}", using default`);
            presetName = 'default';
        }

        return ViewerFactory.create(id, container, {
            ...extraOptions,
            preset: presetName
        });
    }

    /**
     * Create multiple viewers for a comparison layout
     * @param {Array<Object>} configs - Array of viewer configurations
     * @param {string} configs[].id - Viewer ID
     * @param {HTMLElement|string} configs[].container - Container
     * @param {Object} [configs[].options] - Options
     * @returns {ViewerInstance[]} Array of viewer instances
     *
     * @example
     * const viewers = ViewerFactory.createMultiple([
     *     { id: 'v1', container: container1 },
     *     { id: 'v2', container: container2 }
     * ]);
     */
    static createMultiple(configs) {
        if (!Array.isArray(configs)) {
            throw new Error('ViewerFactory.createMultiple: configs must be an array');
        }

        return configs.map(config => {
            return ViewerFactory.create(
                config.id,
                config.container,
                config.options || {}
            );
        });
    }

    /**
     * Create a comparison layout with two viewers
     * @param {HTMLElement|string} container1 - First container
     * @param {HTMLElement|string} container2 - Second container
     * @param {Object} [options={}] - Shared options
     * @returns {{ viewer1: ViewerInstance, viewer2: ViewerInstance }}
     *
     * @example
     * const { viewer1, viewer2 } = ViewerFactory.createComparisonPair(
     *     document.getElementById('left'),
     *     document.getElementById('right')
     * );
     */
    static createComparisonPair(container1, container2, options = {}) {
        const viewer1 = ViewerFactory.createFromPreset('compare', null, container1, options);
        const viewer2 = ViewerFactory.createFromPreset('compare', null, container2, options);

        return { viewer1, viewer2 };
    }

    /**
     * Get available preset names
     * @returns {string[]} List of preset names
     */
    static getPresets() {
        return Object.keys(VIEWER_PRESETS);
    }

    /**
     * Get configuration for a preset
     * @param {string} presetName - Name of preset
     * @returns {Object|null} Preset configuration or null
     */
    static getPresetConfig(presetName) {
        return VIEWER_PRESETS[presetName] || null;
    }

    /**
     * Register a custom preset
     * @param {string} name - Preset name
     * @param {Object} config - Preset configuration
     */
    static registerPreset(name, config) {
        if (VIEWER_PRESETS[name]) {
            console.warn(`[ViewerFactory] Overwriting existing preset "${name}"`);
        }

        VIEWER_PRESETS[name] = { ...VIEWER_PRESETS.default, ...config };
        console.log(`[ViewerFactory] Registered preset "${name}"`);
    }

    /**
     * Create container element with proper styling
     * Utility method for dynamic viewer creation
     * @param {string} [id] - Element ID
     * @param {string} [className='viewer-container'] - CSS class
     * @returns {HTMLElement} Created container element
     */
    static createContainer(id, className = 'viewer-container') {
        const container = document.createElement('div');

        if (id) {
            container.id = id;
        }

        container.className = className;
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.position = 'relative';

        return container;
    }
}

export { ViewerFactory, VIEWER_PRESETS };
export default ViewerFactory;
