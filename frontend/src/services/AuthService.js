/**
 * AuthService - OIDC PKCE Authentication Flow
 *
 * Implements OpenID Connect Authorization Code flow with PKCE (Proof Key for Code Exchange).
 * No client secret needed (public client for SPA).
 *
 * When AUTH_ENABLED=false on backend, this service stays dormant and all API calls
 * work without authentication (anonymous mode).
 *
 * @module services/AuthService
 */

import { API } from '../core/Constants.js';

/** @type {AuthService|null} */
let instance = null;

/**
 * OIDC Configuration (matches backend OIDC_* env vars)
 */
const OIDC_CONFIG = {
    issuerUrl: 'http://localhost:8180/realms/varuna',
    clientId: 'varuna-viewer',
    redirectUri: `${window.location.origin}/callback`,
    postLogoutRedirectUri: window.location.origin,
    scope: 'openid profile email',
    responseType: 'code',
};

class AuthService {
    constructor() {
        if (instance) {return instance;}

        /** @type {string|null} Access token */
        this._accessToken = null;
        /** @type {string|null} Refresh token */
        this._refreshToken = null;
        /** @type {string|null} ID token */
        this._idToken = null;
        /** @type {object|null} Decoded token claims */
        this._claims = null;
        /** @type {boolean} Whether auth is enabled on backend */
        this._authEnabled = false;
        /** @type {boolean} Whether we've checked backend auth status */
        this._initialized = false;
        /** @type {number|null} Token refresh timer */
        this._refreshTimer = null;
        /** @type {object|null} OIDC discovery document */
        this._discovery = null;

        instance = this;
    }

    static getInstance() {
        if (!instance) {
            instance = new AuthService();
        }
        return instance;
    }

    // ==========================================
    // INITIALIZATION
    // ==========================================

    /**
     * Initialize auth service: check if backend requires auth.
     * @returns {Promise<boolean>} true if auth is enabled
     */
    async init() {
        if (this._initialized) {return this._authEnabled;}

        try {
            // Check if we're on the callback page
            if (window.location.pathname === '/callback') {
                await this._handleCallback();
                this._initialized = true;
                this._authEnabled = true;
                return true;
            }

            // Check if we have stored tokens
            this._loadTokensFromStorage();

            // Check backend auth status
            const response = await fetch(`${API.BASE_URL}/api/auth/me`, {
                headers: this._accessToken
                    ? { 'Authorization': `Bearer ${this._accessToken}` }
                    : {},
            });

            if (response.ok) {
                const data = await response.json();
                this._authEnabled = data.auth_enabled;

                if (!this._authEnabled) {
                    // Anonymous mode - backend doesn't require auth
                    this._claims = {
                        sub: 'anonymous',
                        preferred_username: 'anonymous',
                        realm_access: { roles: ['ADMIN_TECHNIQUE'] },
                    };
                    this._initialized = true;
                    return false;
                }

                // Auth enabled - if we have a valid token, use it
                if (data.user && !data.user.is_anonymous) {
                    this._claims = data.user;
                    this._startRefreshTimer();
                    this._initialized = true;
                    return true;
                }
            }

            if (response.status === 401 || (this._authEnabled && !this._accessToken)) {
                this._authEnabled = true;
            }

            this._initialized = true;
            return this._authEnabled;
        } catch (err) {
            console.warn('[AuthService] Init check failed, assuming no auth:', err.message);
            this._authEnabled = false;
            this._initialized = true;
            return false;
        }
    }

    // ==========================================
    // OIDC PKCE FLOW
    // ==========================================

    /**
     * Start the OIDC login flow (redirect to IdP).
     */
    async login() {
        const discovery = await this._getDiscovery();
        const authEndpoint = discovery.authorization_endpoint;

        // Generate PKCE code verifier + challenge
        const codeVerifier = this._generateCodeVerifier();
        const codeChallenge = await this._generateCodeChallenge(codeVerifier);
        const state = this._generateState();

        // Store PKCE verifier and state for callback
        sessionStorage.setItem('oidc_code_verifier', codeVerifier);
        sessionStorage.setItem('oidc_state', state);

        // Build authorization URL
        const params = new URLSearchParams({
            response_type: OIDC_CONFIG.responseType,
            client_id: OIDC_CONFIG.clientId,
            redirect_uri: OIDC_CONFIG.redirectUri,
            scope: OIDC_CONFIG.scope,
            state: state,
            code_challenge: codeChallenge,
            code_challenge_method: 'S256',
        });

        window.location.href = `${authEndpoint}?${params}`;
    }

    /**
     * Handle the OIDC callback (exchange code for tokens).
     */
    async _handleCallback() {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');
        const state = params.get('state');
        const error = params.get('error');

        if (error) {
            throw new Error(`OIDC error: ${error} - ${params.get('error_description')}`);
        }

        if (!code) {
            throw new Error('No authorization code in callback');
        }

        // Verify state
        const storedState = sessionStorage.getItem('oidc_state');
        if (state !== storedState) {
            throw new Error('State mismatch - possible CSRF attack');
        }

        // Exchange code for tokens
        const codeVerifier = sessionStorage.getItem('oidc_code_verifier');
        const discovery = await this._getDiscovery();
        const tokenEndpoint = discovery.token_endpoint;

        const response = await fetch(tokenEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                grant_type: 'authorization_code',
                code: code,
                redirect_uri: OIDC_CONFIG.redirectUri,
                client_id: OIDC_CONFIG.clientId,
                code_verifier: codeVerifier,
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(`Token exchange failed: ${err.error_description || response.status}`);
        }

        const tokens = await response.json();
        this._setTokens(tokens);

        // Clean up PKCE state
        sessionStorage.removeItem('oidc_code_verifier');
        sessionStorage.removeItem('oidc_state');

        // Redirect to home page
        window.history.replaceState({}, '', '/');
    }

    /**
     * Logout: clear tokens and redirect to IdP logout.
     */
    async logout() {
        try {
            const discovery = await this._getDiscovery();
            const logoutEndpoint = discovery.end_session_endpoint;

            this._clearTokens();

            if (logoutEndpoint) {
                const params = new URLSearchParams({
                    id_token_hint: this._idToken || '',
                    post_logout_redirect_uri: OIDC_CONFIG.postLogoutRedirectUri,
                    client_id: OIDC_CONFIG.clientId,
                });
                window.location.href = `${logoutEndpoint}?${params}`;
                return;
            }
        } catch (err) {
            console.warn('[AuthService] Logout error:', err);
        }

        this._clearTokens();
        window.location.href = '/';
    }

    /**
     * Silently refresh the access token using the refresh token.
     */
    async refreshTokenSilently() {
        if (!this._refreshToken) {return false;}

        try {
            const discovery = await this._getDiscovery();
            const tokenEndpoint = discovery.token_endpoint;

            const response = await fetch(tokenEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    grant_type: 'refresh_token',
                    refresh_token: this._refreshToken,
                    client_id: OIDC_CONFIG.clientId,
                }),
            });

            if (!response.ok) {
                console.warn('[AuthService] Token refresh failed');
                this._clearTokens();
                return false;
            }

            const tokens = await response.json();
            this._setTokens(tokens);
            return true;
        } catch (err) {
            console.error('[AuthService] Token refresh error:', err);
            this._clearTokens();
            return false;
        }
    }

    // ==========================================
    // TOKEN MANAGEMENT
    // ==========================================

    /** @returns {string|null} Current access token */
    get accessToken() {
        return this._accessToken;
    }

    /** @returns {boolean} Whether user is authenticated */
    get isAuthenticated() {
        return !this._authEnabled || !!this._accessToken;
    }

    /** @returns {boolean} Whether auth is required */
    get authEnabled() {
        return this._authEnabled;
    }

    /** @returns {object|null} User claims from token */
    get user() {
        return this._claims;
    }

    /** @returns {string} Username */
    get username() {
        if (!this._claims) {return 'anonymous';}
        return this._claims.preferred_username || this._claims.username || this._claims.sub || 'unknown';
    }

    /** @returns {string[]} User roles */
    get roles() {
        if (!this._claims) {return [];}
        // Support both formats: CurrentUser.roles or JWT realm_access.roles
        if (Array.isArray(this._claims.roles)) {return this._claims.roles;}
        const realmAccess = this._claims.realm_access;
        if (realmAccess && Array.isArray(realmAccess.roles)) {return realmAccess.roles;}
        return [];
    }

    /** @returns {string} Primary role (highest privilege) */
    get primaryRole() {
        if (this._claims && this._claims.primary_role) {return this._claims.primary_role;}
        const priority = { ADMIN_TECHNIQUE: 4, MEDECIN: 3, INFIRMIER: 2, LECTURE_SEULE: 1 };
        const roles = this.roles;
        if (!roles.length) {return 'LECTURE_SEULE';}
        return roles.reduce((best, r) => (priority[r] || 0) > (priority[best] || 0) ? r : best, roles[0]);
    }

    /**
     * Check if user has any of the specified roles.
     * @param  {...string} roles - Required roles
     * @returns {boolean}
     */
    hasRole(...roles) {
        const userRoles = this.roles;
        return roles.some(r => userRoles.includes(r));
    }

    // ==========================================
    // INTERNAL HELPERS
    // ==========================================

    _setTokens(tokens) {
        this._accessToken = tokens.access_token;
        this._refreshToken = tokens.refresh_token || this._refreshToken;
        this._idToken = tokens.id_token || this._idToken;

        // Decode access token claims
        try {
            const payload = tokens.access_token.split('.')[1];
            this._claims = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
        } catch (e) {
            console.warn('[AuthService] Failed to decode token claims');
        }

        // Persist tokens
        localStorage.setItem('varuna_access_token', this._accessToken);
        if (this._refreshToken) {
            localStorage.setItem('varuna_refresh_token', this._refreshToken);
        }
        if (this._idToken) {
            localStorage.setItem('varuna_id_token', this._idToken);
        }

        this._startRefreshTimer();
    }

    _loadTokensFromStorage() {
        this._accessToken = localStorage.getItem('varuna_access_token');
        this._refreshToken = localStorage.getItem('varuna_refresh_token');
        this._idToken = localStorage.getItem('varuna_id_token');

        if (this._accessToken) {
            try {
                const payload = this._accessToken.split('.')[1];
                this._claims = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));

                // Check expiration
                if (this._claims.exp && Date.now() / 1000 > this._claims.exp) {
                    console.warn('[AuthService] Stored token expired');
                    this._accessToken = null;
                    this._claims = null;
                }
            } catch (e) {
                this._accessToken = null;
            }
        }
    }

    _clearTokens() {
        this._accessToken = null;
        this._refreshToken = null;
        this._idToken = null;
        this._claims = null;

        localStorage.removeItem('varuna_access_token');
        localStorage.removeItem('varuna_refresh_token');
        localStorage.removeItem('varuna_id_token');

        if (this._refreshTimer) {
            clearTimeout(this._refreshTimer);
            this._refreshTimer = null;
        }
    }

    _startRefreshTimer() {
        if (this._refreshTimer) {clearTimeout(this._refreshTimer);}
        if (!this._claims || !this._claims.exp) {return;}

        // Refresh 60 seconds before expiry
        const expiresIn = (this._claims.exp - Date.now() / 1000 - 60) * 1000;
        if (expiresIn <= 0) {
            this.refreshTokenSilently();
            return;
        }

        this._refreshTimer = setTimeout(() => {
            this.refreshTokenSilently();
        }, Math.max(expiresIn, 1000));
    }

    async _getDiscovery() {
        if (this._discovery) {return this._discovery;}

        const url = `${OIDC_CONFIG.issuerUrl}/.well-known/openid-configuration`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`OIDC discovery failed: ${response.status}`);
        }
        this._discovery = await response.json();
        return this._discovery;
    }

    _generateCodeVerifier() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return this._base64UrlEncode(array);
    }

    async _generateCodeChallenge(verifier) {
        const encoder = new TextEncoder();
        const data = encoder.encode(verifier);
        const digest = await crypto.subtle.digest('SHA-256', data);
        return this._base64UrlEncode(new Uint8Array(digest));
    }

    _generateState() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return this._base64UrlEncode(array);
    }

    _base64UrlEncode(buffer) {
        const base64 = btoa(String.fromCharCode(...buffer));
        return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }
}

export const authService = AuthService.getInstance();
export { AuthService };
export default authService;
