/**
 * LoginPage - Hospital-grade login page with OIDC redirect.
 *
 * Shows "Sign in with Hospital Account" button that redirects to the
 * configured OIDC provider (Keycloak dev / Azure AD prod).
 *
 * @module components/LoginPage
 */

import { authService } from '../services/AuthService.js';
import { i18nService } from '../services/I18nService.js';

export class LoginPage {
    /**
     * @param {HTMLElement} container - Parent container to render into
     */
    constructor(container) {
        this.container = container;
        this._render();
    }

    _render() {
        this.container.innerHTML = '';
        this.container.className = 'page-login';

        const page = document.createElement('div');
        page.className = 'login-page';
        page.innerHTML = `
            <div class="login-card">
                <div class="login-logo">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary, #4a9eff)" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 6v6l4 2"/>
                        <path d="M8 2h8"/>
                    </svg>
                    <h1 class="login-title">VarunaPoC</h1>
                    <p class="login-subtitle">${i18nService.t('app.subtitle')}</p>
                </div>

                <div class="login-content">
                    <p class="login-description">
                        ${i18nService.t('login.desc')}
                    </p>

                    <button class="login-button" id="login-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                            <polyline points="10 17 15 12 10 7"/>
                            <line x1="15" y1="12" x2="3" y2="12"/>
                        </svg>
                        ${i18nService.t('login.button')}
                    </button>

                    <p class="login-hint">
                        ${i18nService.t('login.hint')}
                    </p>
                </div>

                <div class="login-footer">
                    <span>CHU UCL Namur</span>
                    <span class="login-separator">|</span>
                    <span>${i18nService.t('login.secureAccess')}</span>
                </div>
            </div>
        `;

        this.container.appendChild(page);

        // Login button handler
        page.querySelector('#login-btn').addEventListener('click', () => {
            authService.login();
        });
    }

    destroy() {
        this.container.innerHTML = '';
    }
}
