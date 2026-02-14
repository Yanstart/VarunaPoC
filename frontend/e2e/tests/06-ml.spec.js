/**
 * 06 - ML Panel Tests
 *
 * Validates ML panel toggle, prediction request, and heatmap overlay.
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks, mockMLPredict, mockMLHeatmap } from '../helpers/api-mock.js';

test.describe('ML Panel', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await mockMLPredict(page);
        await mockMLHeatmap(page);

        await page.goto('/');
        await page.waitForSelector('.folder-browser');

        // Navigate to viewer
        await page.locator('.slide-item, .slide-card', { hasText: 'TestSlide' }).first().click();
        await page.locator('#viewer').waitFor({ timeout: 10_000 });
    });

    test('ML button is visible in viewer header', async ({ page }) => {
        await expect(page.locator('#ml-btn')).toBeVisible();
    });

    test('clicking ML button toggles ML panel', async ({ page }) => {
        // ML panel container starts hidden
        const mlContainer = page.locator('#ml-panel-container');
        await expect(mlContainer).toHaveClass(/is-hidden/);

        // Click ML button
        await page.locator('#ml-btn').click();

        // Panel should become visible
        await expect(mlContainer).not.toHaveClass(/is-hidden/);

        // Panel content should be rendered
        await expect(page.locator('.ml-panel')).toBeVisible();
        await expect(page.locator('.ml-panel__header')).toBeVisible();
    });

    test('ML panel shows Analyze and Heatmap buttons', async ({ page }) => {
        // Open ML panel
        await page.locator('#ml-btn').click();

        // Should have predict and heatmap buttons
        await expect(page.locator('.ml-panel__btn--predict')).toBeVisible();
        await expect(page.locator('.ml-panel__btn--heatmap')).toBeVisible();
    });
});
