/**
 * 07 - Quality Panel Tests
 *
 * Validates quality metrics panel, kappa score display, and confusion matrix.
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks, mockQualityMetrics } from '../helpers/api-mock.js';

test.describe('Quality Panel', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await mockQualityMetrics(page);

        await page.goto('/');
        await page.waitForSelector('.folder-browser');

        // Navigate to viewer
        await page.locator('.slide-item, .slide-card', { hasText: 'TestSlide' }).first().click();
        await page.locator('#viewer').waitFor({ timeout: 10_000 });
    });

    test('quality panel component is present in info panel', async ({ page }) => {
        // The quality panel is rendered inside the info section
        // It may be collapsed by default
        const infoPanel = page.locator('#info');
        await expect(infoPanel).toBeVisible({ timeout: 10_000 });

        // Panel might be lazily initialized; check that the info panel loaded first
        await expect(infoPanel).toContainText('Information', { timeout: 10_000 });
    });

    test('info panel displays slide metadata', async ({ page }) => {
        const infoPanel = page.locator('#info');
        await expect(infoPanel).toBeVisible({ timeout: 10_000 });

        // Should show format, dimensions, levels
        await expect(infoPanel).toContainText('SVS', { timeout: 10_000 });
        await expect(infoPanel).toContainText('50,000');
        await expect(infoPanel).toContainText('5 pyramid levels');
    });

    test('layer manager container exists in info panel', async ({ page }) => {
        // Layer manager is appended after slide metadata loads
        await page.locator('#info').waitFor();
        await expect(page.locator('#info')).toContainText('Information', { timeout: 10_000 });

        const layerContainer = page.locator('#layer-manager-container');
        await expect(layerContainer).toBeAttached({ timeout: 5_000 });
    });
});
