/**
 * EventBus - Central event management system (Observer/Pub-Sub pattern)
 *
 * Provides a centralized communication channel between components
 * without direct coupling. Essential for multi-viewer synchronization.
 *
 * @module core/EventBus
 * @example
 * // Subscribe to an event
 * EventBus.on('viewer:pan', (data) => console.log('Pan event:', data));
 *
 * // Emit an event
 * EventBus.emit('viewer:pan', { x: 100, y: 200, viewerId: 'viewer-1' });
 *
 * // Unsubscribe
 * EventBus.off('viewer:pan', handlerFunction);
 */

/**
 * Singleton EventBus instance
 * @type {EventBus|null}
 */
let instance = null;

/**
 * EventBus class implementing Singleton pattern
 * Manages event subscriptions and publications across the application
 */
class EventBus {
    constructor() {
        if (instance) {
            return instance;
        }

        /**
         * Map of event names to their subscriber callbacks
         * @type {Map<string, Set<Function>>}
         */
        this._listeners = new Map();

        /**
         * Map of one-time event listeners
         * @type {Map<string, Set<Function>>}
         */
        this._onceListeners = new Map();

        /**
         * Debug mode flag - logs all events when enabled
         * @type {boolean}
         */
        this._debug = false;

        instance = this;
    }

    /**
     * Get the singleton EventBus instance
     * @returns {EventBus} The singleton instance
     */
    static getInstance() {
        if (!instance) {
            instance = new EventBus();
        }
        return instance;
    }

    /**
     * Subscribe to an event
     * @param {string} event - Event name (e.g., 'viewer:pan', 'sync:enable')
     * @param {Function} callback - Function to call when event is emitted
     * @returns {Function} Unsubscribe function for convenience
     *
     * @example
     * const unsubscribe = EventBus.getInstance().on('viewer:zoom', (data) => {
     *     console.log('Zoom level:', data.zoom);
     * });
     * // Later: unsubscribe();
     */
    on(event, callback) {
        if (typeof callback !== 'function') {
            throw new TypeError('EventBus.on: callback must be a function');
        }

        if (!this._listeners.has(event)) {
            this._listeners.set(event, new Set());
        }

        this._listeners.get(event).add(callback);

        if (this._debug) {
            console.warn(`[EventBus] Subscribed to "${event}"`);
        }

        // Return unsubscribe function for convenience
        return () => this.off(event, callback);
    }

    /**
     * Subscribe to an event only once
     * Callback is automatically removed after first invocation
     * @param {string} event - Event name
     * @param {Function} callback - Function to call once
     * @returns {Function} Unsubscribe function
     */
    once(event, callback) {
        if (typeof callback !== 'function') {
            throw new TypeError('EventBus.once: callback must be a function');
        }

        if (!this._onceListeners.has(event)) {
            this._onceListeners.set(event, new Set());
        }

        this._onceListeners.get(event).add(callback);

        if (this._debug) {
            console.warn(`[EventBus] Subscribed once to "${event}"`);
        }

        return () => {
            const listeners = this._onceListeners.get(event);
            if (listeners) {
                listeners.delete(callback);
            }
        };
    }

    /**
     * Unsubscribe from an event
     * @param {string} event - Event name
     * @param {Function} callback - The exact callback function to remove
     * @returns {boolean} True if callback was found and removed
     */
    off(event, callback) {
        const listeners = this._listeners.get(event);
        if (listeners) {
            const deleted = listeners.delete(callback);

            if (this._debug && deleted) {
                console.warn(`[EventBus] Unsubscribed from "${event}"`);
            }

            // Clean up empty sets
            if (listeners.size === 0) {
                this._listeners.delete(event);
            }

            return deleted;
        }
        return false;
    }

    /**
     * Emit an event to all subscribers
     * @param {string} event - Event name
     * @param {*} [data] - Data to pass to callbacks
     * @returns {number} Number of callbacks invoked
     *
     * @example
     * EventBus.getInstance().emit('viewer:pan', {
     *     viewerId: 'viewer-1',
     *     viewport: { x: 0.5, y: 0.5, width: 0.2, height: 0.2 }
     * });
     */
    emit(event, data) {
        let invokedCount = 0;

        if (this._debug) {
            console.warn(`[EventBus] Emitting "${event}"`, data);
        }

        // Invoke regular listeners
        const listeners = this._listeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                    invokedCount++;
                } catch (error) {
                    console.error(`[EventBus] Error in listener for "${event}":`, error);
                }
            });
        }

        // Invoke one-time listeners and remove them
        const onceListeners = this._onceListeners.get(event);
        if (onceListeners) {
            onceListeners.forEach(callback => {
                try {
                    callback(data);
                    invokedCount++;
                } catch (error) {
                    console.error(`[EventBus] Error in once-listener for "${event}":`, error);
                }
            });
            this._onceListeners.delete(event);
        }

        return invokedCount;
    }

    /**
     * Check if event has any subscribers
     * @param {string} event - Event name
     * @returns {boolean} True if event has subscribers
     */
    hasListeners(event) {
        const regular = this._listeners.get(event)?.size || 0;
        const once = this._onceListeners.get(event)?.size || 0;
        return (regular + once) > 0;
    }

    /**
     * Get count of subscribers for an event
     * @param {string} event - Event name
     * @returns {number} Number of subscribers
     */
    listenerCount(event) {
        const regular = this._listeners.get(event)?.size || 0;
        const once = this._onceListeners.get(event)?.size || 0;
        return regular + once;
    }

    /**
     * Remove all listeners for a specific event or all events
     * @param {string} [event] - Event name. If omitted, clears all events.
     */
    clear(event) {
        if (event) {
            this._listeners.delete(event);
            this._onceListeners.delete(event);

            if (this._debug) {
                console.warn(`[EventBus] Cleared all listeners for "${event}"`);
            }
        } else {
            this._listeners.clear();
            this._onceListeners.clear();

            if (this._debug) {
                console.warn('[EventBus] Cleared all listeners');
            }
        }
    }

    /**
     * Enable or disable debug mode
     * When enabled, all event activity is logged to console
     * @param {boolean} enabled - Whether to enable debug mode
     */
    setDebug(enabled) {
        this._debug = enabled;
        console.warn(`[EventBus] Debug mode ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Get list of all registered event names
     * @returns {string[]} Array of event names
     */
    getEventNames() {
        const regular = [...this._listeners.keys()];
        const once = [...this._onceListeners.keys()];
        return [...new Set([...regular, ...once])];
    }
}

// Export singleton instance and class
export const eventBus = EventBus.getInstance();
export { EventBus };
export default eventBus;
