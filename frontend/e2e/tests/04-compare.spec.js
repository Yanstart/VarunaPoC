/**
 * 04 - Compare Mode Tests
 *
 * Validates multi-viewer layout, slide loading in panels, and sync controls.
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Compare Mode', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('compare mode button opens compare layout', async ({ page }) => {
        // Click the compare mode button on home page
        await page.locator('.compare-mode-button').click();

        // Should show compare page
        await expect(page.locator('.compare-page')).toBeVisible({ timeout: 10_000 });
        await expect(page.locator('.compare-title')).toHaveText('Mode comparaison');
    });

    test('compare layout shows viewer panels', async ({ page }) => {
        await page.locator('.compare-mode-button').click();
        await expect(page.locator('.compare-page')).toBeVisible({ timeout: 10_000 });

        // Should have a compare container with viewer panels
        await expect(page.locator('#compare-container')).toBeVisible();
        await expect(page.locator('.compare-layout')).toBeVisible({ timeout: 5_000 });
    });

    test('sync controls are visible', async ({ page }) => {
        await page.locator('.compare-mode-button').click();
        await expect(page.locator('.compare-page')).toBeVisible({ timeout: 10_000 });

        // Sync controls should be available
        const syncEl = page.locator('.sync-controls, .sync-button, .sync-label');
        await expect(syncEl.first()).toBeVisible({ timeout: 5_000 });
    });

    test('back button returns to home from compare', async ({ page }) => {
        await page.locator('.compare-mode-button').click();
        await expect(page.locator('.compare-page')).toBeVisible({ timeout: 10_000 });

        // Click back
        await page.locator('#back-btn').click();

        // Should return to home
        await expect(page.locator('.folder-browser')).toBeVisible();
    });
});
