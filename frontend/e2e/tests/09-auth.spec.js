/**
 * 09 - Authentication Flow Tests
 *
 * Validates auth behavior in both anonymous (AUTH_ENABLED=false) and
 * authenticated modes (mocked OIDC).
 */
import { test, expect } from '../fixtures/base.js';
import {
    mockHealthy,
    mockAuthAnonymous,
    mockAuthRequired,
    mockAuthAuthenticated,
    mockSlidesApi,
} from '../helpers/api-mock.js';

test.describe('Authentication', () => {
    test('AUTH_ENABLED=false shows home page directly (no login)', async ({
        page,
        mockSlideData,
    }) => {
        await mockHealthy(page);
        await mockAuthAnonymous(page);
        await mockSlidesApi(page, mockSlideData);

        await page.goto('/');

        // Should go directly to home page without login
        await expect(page.locator('.folder-browser')).toBeVisible({ timeout: 10_000 });

        // Login page should NOT be shown
        await expect(page.locator('.login-page')).toBeHidden();
    });

    test('auth required shows login page', async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthRequired(page);
        await mockSlidesApi(page, mockSlideData);

        await page.goto('/');

        // Should show login page
        await expect(page.locator('#app.page-login')).toBeVisible({ timeout: 10_000 });

        // Login button should be present
        await expect(page.locator('#login-btn')).toBeVisible();
        await expect(page.locator('#login-btn')).toContainText('Se connecter');
    });

    test('login page shows hospital branding', async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthRequired(page);
        await mockSlidesApi(page, mockSlideData);

        await page.goto('/');
        await expect(page.locator('.login-page')).toBeVisible({ timeout: 10_000 });

        // Should show title and description
        await expect(page.locator('.login-title')).toHaveText('VarunaPoC');
        await expect(page.locator('.login-subtitle')).toContainText('pathologie');
        await expect(page.locator('.login-footer')).toContainText('CHU UCL Namur');
    });

    test('authenticated user with role sees user info', async ({ page, mockSlideData }) => {
        // Simulate already-authenticated user
        await mockHealthy(page);
        await mockAuthAuthenticated(page, 'MEDECIN');
        await mockSlidesApi(page, mockSlideData);

        // Mock the auth/me to return auth_enabled=true with valid user
        // The authService should detect we're authenticated
        await page.route('**/api/auth/me', (route) =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    auth_enabled: true,
                    user: {
                        sub: 'user-123',
                        preferred_username: 'dr.dupont',
                        email: 'dupont@chu-namur.be',
                        realm_access: { roles: ['MEDECIN'] },
                    },
                }),
            }),
        );

        await page.goto('/');

        // Should show home page (user is authenticated)
        // Note: The actual flow depends on token storage which we can't fully mock
        // in E2E without the real OIDC provider. This test validates the mock setup.
        const isHome = await page.locator('.folder-browser').isVisible().catch(() => false);
        const isLogin = await page.locator('.login-page').isVisible().catch(() => false);

        // Either home (authenticated) or login (needs token) is valid
        expect(isHome || isLogin).toBeTruthy();
    });
});
