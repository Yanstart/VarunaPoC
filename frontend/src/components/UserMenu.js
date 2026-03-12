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
import { i18nService } from '../services/I18nService.js';

const ROLE_LABELS = {
    ADMIN_TECHNIQUE: 'Admin',
    MEDECIN: 'M\u00e9decin',
    INFIRMIER: 'Infirmier',
    LECTURE_SEULE: 'Lecture seule',
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
        const _t = (k, p) => i18nService.t(k, p);

        // Build via DOM API for safety (only static SVG uses innerHTML)
        const trigger = document.createElement('button');
        trigger.className = 'user-menu-trigger';
        trigger.title = _t('user.menu');
        const avatar = document.createElement('span');
        avatar.className = 'user-avatar';
        avatar.textContent = this._getInitials(username);
        trigger.appendChild(avatar);
        const nameSpan = document.createElement('span');
        nameSpan.className = 'user-name';
        nameSpan.textContent = username;
        trigger.appendChild(nameSpan);
        const roleBadge = document.createElement('span');
        roleBadge.className = 'user-role-badge';
        roleBadge.style.background = roleColor;
        roleBadge.textContent = roleLabel;
        trigger.appendChild(roleBadge);
        this.element.appendChild(trigger);

        const dropdown = document.createElement('div');
        dropdown.className = 'user-menu-dropdown';

        const ddHeader = document.createElement('div');
        ddHeader.className = 'user-menu-header';
        const ddUser = document.createElement('span');
        ddUser.className = 'user-menu-username';
        ddUser.textContent = username;
        ddHeader.appendChild(ddUser);
        const ddRole = document.createElement('span');
        ddRole.className = 'user-menu-role';
        ddRole.textContent = roleLabel;
        ddHeader.appendChild(ddRole);
        dropdown.appendChild(ddHeader);
        dropdown.appendChild(this._divider());

        if (authService.hasRole('MEDECIN', 'ADMIN_TECHNIQUE')) {
            dropdown.appendChild(this._menuItem('break-glass', _t('user.breakGlass'),
                '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2"><path d="M12 9v2m0 4h.01"/><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>'));
        }

        dropdown.appendChild(this._menuItem('save-session', _t('user.saveSession'),
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>'));

        dropdown.appendChild(this._menuItem('restore-session', _t('user.restoreSession'),
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>'));

        dropdown.appendChild(this._divider());

        dropdown.appendChild(this._menuItem('logout', _t('user.logout'),
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'));

        this.element.appendChild(dropdown);

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

    /**
     * Create a menu item button
     * @param {string} action - data-action value
     * @param {string} label - Text label
     * @param {string} iconSvg - Static SVG icon string (not user input)
     * @returns {HTMLElement}
     */
    _menuItem(action, label, iconSvg) {
        const btn = document.createElement('button');
        btn.className = 'user-menu-item';
        btn.dataset.action = action;
        // Static SVG icon constant - not user input
        btn.innerHTML = iconSvg;
        btn.appendChild(document.createTextNode(' ' + label));
        return btn;
    }

    /**
     * Create a divider element
     * @returns {HTMLElement}
     */
    _divider() {
        const div = document.createElement('div');
        div.className = 'user-menu-divider';
        return div;
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
        const _t = (k, p) => i18nService.t(k, p);
        const reason = prompt(_t('user.breakGlassPrompt'));
        if (!reason || reason.length < 10) {
            if (reason !== null) {alert(_t('user.breakGlassMinChars'));}
            return;
        }
        try {
            const result = await apiService.activateBreakGlass(reason, 30);
            alert(_t('user.breakGlassActivated', { time: new Date(result.expires_at).toLocaleTimeString() }));
        } catch (err) {
            alert(_t('user.breakGlassFailed', { error: err.message }));
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
            console.warn('[UserMenu] Session saved');
        } catch (err) {
            console.error('[UserMenu] Save session failed:', err);
        }
    }

    async _handleRestoreSession() {
        this._close();
        try {
            const result = await apiService.loadSessionState();
            if (result.state && result.state.slide_id) {
                console.warn('[UserMenu] Restoring session, slide:', result.state.slide_id);
                // Emit event to navigate to the slide
                const { eventBus } = await import('../core/EventBus.js');
                const { Events } = await import('../core/Constants.js');
                eventBus.emit(Events.PAGE_CHANGED, {
                    page: 'viewer',
                    slideId: result.state.slide_id,
                });
            } else {
                console.warn('[UserMenu] No saved session');
            }
        } catch (err) {
            console.error('[UserMenu] Restore session failed:', err);
        }
    }

    _getInitials(name) {
        if (!name || name === 'anonymous') {return '?';}
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
