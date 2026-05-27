/**
 * WorkflowEventService - Subscribes to backend WorkflowEvents over WebSocket
 * and dispatches them through the EventBus.
 *
 * Backend endpoint: GET /ws/events?token=<JWT> (sprint 15).
 *
 * Events received from the backend are emitted on the EventBus under the
 * `workflow:<event_type>` channel (e.g. `workflow:report_signed`,
 * `workflow:annotation_created`). Components that care subscribe to those
 * channels via `EventBus.on('workflow:report_signed', handler)`.
 *
 * Reconnection
 * ------------
 * The service auto-reconnects on disconnect with exponential backoff
 * (1s, 2s, 4s, 8s, capped at 30s). On manual stop() the reconnect loop
 * is cancelled.
 *
 * Auth
 * ----
 * The token is read from AuthService at connect time. If AUTH_ENABLED=false
 * on the backend, the token is ignored — the connection still establishes.
 *
 * @module services/WorkflowEventService
 */

import { eventBus } from '../core/EventBus.js';

/** @type {WorkflowEventService|null} */
let instance = null;

class WorkflowEventService {
    constructor() {
        if (instance) {
            return instance;
        }

        /** @type {WebSocket|null} */
        this._ws = null;

        /** @type {boolean} */
        this._stopRequested = false;

        /** @type {number} */
        this._reconnectDelayMs = 1000;

        /** @type {number} */
        this._reconnectMaxMs = 30000;

        /** @type {number|null} */
        this._reconnectTimer = null;

        /** @type {number|null} */
        this._pingInterval = null;

        /** @type {boolean} Last hello-frame received state */
        this._isAuthenticated = false;

        /** @type {object|null} User info from the hello frame */
        this._user = null;

        instance = this;
    }

    static getInstance() {
        if (!instance) {
            instance = new WorkflowEventService();
        }
        return instance;
    }

    /**
     * Open the WebSocket connection. Idempotent — calling start() on an
     * already-open service is a no-op.
     *
     * @param {object} opts
     * @param {string|null} [opts.token] - JWT bearer token (omit when AUTH_ENABLED=false)
     * @param {string} [opts.url] - Override the WS URL (default derived from window.location)
     */
    start({ token = null, url = null } = {}) {
        if (this._ws && (this._ws.readyState === WebSocket.OPEN || this._ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        this._stopRequested = false;

        const wsUrl = url ?? this._buildUrl(token);

        try {
            this._ws = new WebSocket(wsUrl);
        } catch (err) {
            console.warn('[WorkflowEventService] WebSocket constructor failed:', err);
            this._scheduleReconnect();
            return;
        }

        this._ws.addEventListener('open', this._onOpen.bind(this));
        this._ws.addEventListener('message', this._onMessage.bind(this));
        this._ws.addEventListener('close', this._onClose.bind(this));
        this._ws.addEventListener('error', this._onError.bind(this));
    }

    /** Close the WebSocket and stop the reconnect loop. */
    stop() {
        this._stopRequested = true;
        if (this._reconnectTimer !== null) {
            clearTimeout(this._reconnectTimer);
            this._reconnectTimer = null;
        }
        if (this._pingInterval !== null) {
            clearInterval(this._pingInterval);
            this._pingInterval = null;
        }
        if (this._ws) {
            try {
                this._ws.close();
            } catch (err) {
                // Already closing — ignore.
            }
            this._ws = null;
        }
        this._isAuthenticated = false;
        this._user = null;
    }

    /** @returns {boolean} True if the WebSocket is open AND auth-confirmed. */
    isConnected() {
        return this._ws !== null
            && this._ws.readyState === WebSocket.OPEN
            && this._isAuthenticated;
    }

    /** @returns {object|null} The user info from the backend hello frame. */
    getUser() {
        return this._user;
    }

    // -- internals ----------------------------------------------------------

    _buildUrl(token) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Backend exposes /ws/events at the api_v1 prefix in main.py — match that.
        // Default: same host as the frontend, but the API typically runs on a
        // different port (8000) in dev. We honour an explicit override in
        // localStorage for dev so devs don't have to edit code.
        const overrideHost = (typeof localStorage !== 'undefined')
            ? localStorage.getItem('varuna_ws_host')
            : null;
        // Same-origin by default (nginx proxies /api/v1/ws/events to backend).
        // Vite dev server on :5173 needs explicit :8000 since it has no proxy.
        const isViteDev = window.location.port === '5173';
        const host = overrideHost
            || (isViteDev ? `${window.location.hostname}:8000` : window.location.host);
        const params = new URLSearchParams();
        if (token) params.set('token', token);
        const query = params.toString();
        // Backend mounts the ws router under the /api/v1 prefix in main.py.
        return `${protocol}//${host}/api/v1/ws/events${query ? '?' + query : ''}`;
    }

    _onOpen() {
        this._reconnectDelayMs = 1000;  // reset backoff on successful open
        eventBus.emit('workflow:ws:open', {});
        // Start ping loop to keep the connection warm (matches backend's
        // ping/pong handler in routes/ws.py:events_websocket).
        if (this._pingInterval !== null) clearInterval(this._pingInterval);
        this._pingInterval = setInterval(() => {
            if (this._ws && this._ws.readyState === WebSocket.OPEN) {
                try {
                    this._ws.send(JSON.stringify({ type: 'ping' }));
                } catch (err) {
                    // Send failure on a closing socket — let onclose handle it.
                }
            }
        }, 25000);
    }

    _onMessage(event) {
        let data;
        try {
            data = JSON.parse(event.data);
        } catch (err) {
            console.warn('[WorkflowEventService] Non-JSON frame:', event.data);
            return;
        }

        // Hello frame from the backend marks auth confirmation.
        if (data.type === 'hello') {
            this._isAuthenticated = true;
            this._user = data.user || null;
            eventBus.emit('workflow:ws:hello', data);
            return;
        }

        // Pong frame — backend confirmed our ping; nothing to do beyond
        // logging at debug level.
        if (data.type === 'pong') return;

        // WorkflowEvent payload: { event_type, slide_id, user_id, timestamp, metadata }
        if (data.event_type) {
            eventBus.emit(`workflow:${data.event_type}`, data);
            // Also emit a generic channel so consumers can listen to
            // every event without enumerating types.
            eventBus.emit('workflow:event', data);
        }
    }

    _onClose(event) {
        this._isAuthenticated = false;
        this._user = null;
        if (this._pingInterval !== null) {
            clearInterval(this._pingInterval);
            this._pingInterval = null;
        }
        eventBus.emit('workflow:ws:close', { code: event.code, reason: event.reason });

        if (!this._stopRequested) {
            this._scheduleReconnect();
        }
    }

    _onError(event) {
        // The browser fires a generic Error event without details; the
        // close event that follows carries the actionable info.
        eventBus.emit('workflow:ws:error', { event });
    }

    _scheduleReconnect() {
        if (this._reconnectTimer !== null) return;

        const delay = Math.min(this._reconnectDelayMs, this._reconnectMaxMs);
        this._reconnectTimer = setTimeout(async () => {
            this._reconnectTimer = null;
            // Exponential backoff (capped). On the next failure, this
            // grows; on success the open handler resets it to 1s.
            this._reconnectDelayMs = Math.min(this._reconnectDelayMs * 2, this._reconnectMaxMs);
            // Re-resolve token at reconnect time from AuthService — _lastToken
            // is captured at the initial start() and goes stale after a silent
            // refresh, producing an infinite 403 loop on the rejected old token.
            // Dynamic import avoids a circular dep at module load.
            let token = this._lastToken ?? null;
            try {
                const mod = await import('./AuthService.js');
                token = mod.authService.accessToken || token;
            } catch (_e) {
                // AuthService unavailable — fall back to _lastToken.
            }
            this.start({ token });
        }, delay);
    }
}

export const workflowEventService = WorkflowEventService.getInstance();
export { WorkflowEventService };
export default workflowEventService;
