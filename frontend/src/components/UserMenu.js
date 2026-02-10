/**
 * UserMenu - Dropdown user menu showing name, role, and logout.
 *
 * Displayed in the viewer header when auth is enabled.
 * Shows role badge and provides logout action.
 *
 * @module components/UserMenu
 */

import { authService } from '../services/AuthService.js';
import { apiService } from '../services/ApiService.js';

const ROLE_LABELS = {
    ADMIN_TECHNIQUE: 'Admin',
    MEDECIN: 'Physician',
    INFIRMIER: 'Nurse',
    LECTURE_SEULE: 'Read Only',
};

const ROLE_COLORS = {
    ADMIN_TECHNIQUE: '#e74c3c',
    MEDECIN: '#3498db',
    INFIRMIER: '#2ecc71',
    LECTURE_SEULE: '#95a5a6',
};

export class UserMenu {
    /**
     * @param {HTMLElement} container - Parent element to insert menu into
     */
    constructor(container) {
        this.container = container;
        this.element = document.createElement('div');
        this.element.className = 'user-menu';
        this._isOpen = false;
        this._render();
        container.appendChild(this.element);

        // Close on outside click
        this._onDocClick = (e) => {
            if (!this.element.contains(e.target)) {
                this._close();
            }
        };
        document.addEventListener('click', this._onDocClick);
    }

    _render() {
        const username = authService.username;
        const role = authService.primaryRole;
        const roleLabel = ROLE_LABELS[role] || role;
        const roleColor = ROLE_COLORS[role] || '#666';

        this.element.innerHTML = `
            <button class="user-menu-trigger" title="User menu">
                <span class="user-avatar">${this._getInitials(username)}</span>
                <span class="user-name">${username}</span>
                <span class="user-role-badge" style="background: ${roleColor}">${roleLabel}</span>
            </button>
            <div class="user-menu-dropdown">
                <div class="user-menu-header">
                    <span class="user-menu-username">${username}</span>
                    <span class="user-menu-role">${roleLabel}</span>
                </div>
                <div class="user-menu-divider"></div>
                ${authService.hasRole('MEDECIN', 'ADMIN_TECHNIQUE') ? `
                <button class="user-menu-item" data-action="break-glass">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2">
                        <path d="M12 9v2m0 4h.01"/>
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    </svg>
                    Break-Glass (Emergency)
                </button>
                ` : ''}
                <button class="user-menu-item" data-action="save-session">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                        <polyline points="17 21 17 13 7 13 7 21"/>
                        <polyline points="7 3 7 8 15 8"/>
                    </svg>
                    Save Session
                </button>
                <button class="user-menu-item" data-action="restore-session">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="1 4 1 10 7 10"/>
                        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
                    </svg>
                    Restore Session
                </button>
                <div class="user-menu-divider"></div>
                <button class="user-menu-item" data-action="logout">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                        <polyline points="16 17 21 12 16 7"/>
                        <line x1="21" y1="12" x2="9" y2="12"/>
                    </svg>
                    Sign Out
                </button>
            </div>
        `;

        // Toggle dropdown
        this.element.querySelector('.user-menu-trigger').addEventListener('click', (e) => {
            e.stopPropagation();
            this._toggle();
        });

        // Logout
        this.element.querySelector('[data-action="logout"]').addEventListener('click', () => {
            authService.logout();
        });

        // Break-glass
        const breakGlassBtn = this.element.querySelector('[data-action="break-glass"]');
        if (breakGlassBtn) {
            breakGlassBtn.addEventListener('click', () => this._handleBreakGlass());
        }

        // Save session
        this.element.querySelector('[data-action="save-session"]').addEventListener('click', () => {
            this._handleSaveSession();
        });

        // Restore session
        this.element.querySelector('[data-action="restore-session"]').addEventListener('click', () => {
            this._handleRestoreSession();
        });
    }

    _toggle() {
        this._isOpen = !this._isOpen;
        this.element.classList.toggle('is-open', this._isOpen);
    }

    _close() {
        this._isOpen = false;
        this.element.classList.remove('is-open');
    }

    async _handleBreakGlass() {
        this._close();
        const reason = prompt(
            'Break-Glass Emergency Access\n\n' +
            'This grants temporary elevated privileges and is logged as a CRITICAL audit event.\n' +
            'A review by an administrator is required.\n\n' +
            'Enter medical justification (min 10 characters):'
        );
        if (!reason || reason.length < 10) {
            if (reason !== null) alert('Justification must be at least 10 characters.');
            return;
        }
        try {
            const result = await apiService.activateBreakGlass(reason, 30);
            alert(`Break-Glass activated until ${new Date(result.expires_at).toLocaleTimeString()}`);
        } catch (err) {
            alert(`Break-Glass failed: ${err.message}`);
        }
    }

    async _handleSaveSession() {
        this._close();
        try {
            // Gather current viewer state from window.__VarunaApp
            const appState = window.__VarunaApp?.state;
            const state = {
                slide_id: appState?.selectedSlide?.id || null,
                annotations_visible: true,
                heatmap_visible: false,
            };
            await apiService.saveSessionState(state);
            console.log('[UserMenu] Session saved');
        } catch (err) {
            console.error('[UserMenu] Save session failed:', err);
        }
    }

    async _handleRestoreSession() {
        this._close();
        try {
            const result = await apiService.loadSessionState();
            if (result.state && result.state.slide_id) {
                console.log('[UserMenu] Restoring session, slide:', result.state.slide_id);
                // Emit event to navigate to the slide
                const { eventBus } = await import('../core/EventBus.js');
                const { Events } = await import('../core/Constants.js');
                eventBus.emit(Events.PAGE_CHANGED, {
                    page: 'viewer',
                    slideId: result.state.slide_id,
                });
            } else {
                console.log('[UserMenu] No saved session');
            }
        } catch (err) {
            console.error('[UserMenu] Restore session failed:', err);
        }
    }

    _getInitials(name) {
        if (!name || name === 'anonymous') return '?';
        const parts = name.split(/[.\-_\s]/);
        if (parts.length >= 2) {
            return (parts[0][0] + parts[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }

    destroy() {
        document.removeEventListener('click', this._onDocClick);
        this.element.remove();
    }
}
