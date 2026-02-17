/**
 * 18 - Worklist & History Tests
 * Validates WorklistView and RecentCases components.
 *
 * Reference: Issues #98, #99 [W4-UX01, W4-UX02]
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Worklist View', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        // Set worklist view preference before navigating
        await page.addInitScript(() => {
            localStorage.setItem('varuna_home_view', 'worklist');
        });
        await page.goto('/');
    });

    test('worklist view is displayed when preference is set', async ({ page }) => {
        const worklist = page.locator('.worklist-view');
        await expect(worklist).toBeAttached({ timeout: 5000 });
    });

    test('worklist has title Mes cas', async ({ page }) => {
        const title = page.locator('.worklist-view__title');
        await expect(title).toHaveText('Mes cas');
    });

    test('worklist has filter tabs', async ({ page }) => {
        const tabs = page.locator('.worklist-view__tab');
        await expect(tabs).toHaveCount(4); // Tous, En attente, En cours, Termines
    });
});

test.describe('Recent Cases', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        // Ensure cases view (default) to see RecentCases
        await page.addInitScript(() => {
            localStorage.setItem('varuna_home_view', 'cases');
        });
        await page.goto('/');
    });

    test('recent cases section is displayed on cases view', async ({ page }) => {
        const recentCases = page.locator('.recent-cases');
        await expect(recentCases).toBeAttached({ timeout: 5000 });
    });

    test('recent cases has title Cas recents', async ({ page }) => {
        const title = page.locator('.recent-cases__title');
        await expect(title).toHaveText('Cas recents');
    });
});
