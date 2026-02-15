/**
 * 03 - Viewer Tests
 *
 * Validates slide viewer loading, OpenSeadragon canvas, metadata, and navigation.
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Slide Viewer', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('clicking slide opens viewer page', async ({ page }) => {
        // Click on a slide in the list
        await page.locator('.slides-section').waitFor();
        await page.locator('.slide-item, .slide-card', { hasText: 'TestSlide' }).first().click();

        // Should switch to viewer page
        await expect(page.locator('#app.page-viewer')).toBeVisible({ timeout: 10_000 });
        await expect(page.locator('#viewer')).toBeVisible();
    });

    test('OpenSeadragon canvas is rendered', async ({ page }) => {
        // Navigate to viewer
        await page.locator('.slide-item, .slide-card', { hasText: 'TestSlide' }).first().click();
        await page.locator('#viewer').waitFor();

        // OSD creates canvas elements inside the viewer container
        await expect(page.locator('#viewer canvas').first()).toBeVisible({
            timeout: 10_000,
        });
    });

    test('metadata panel shows slide dimensions and format', async ({ page }) => {
        // Navigate to viewer
        await page.locator('.slide-item, .slide-card', { hasText: 'TestSlide' }).first().click();

        // Wait for metadata to load in info panel
        const infoPanel = page.locator('#info');
        await expect(infoPanel).toBeVisible();

        // Should display dimensions
        await expect(infoPanel).toContainText('50,000', { timeout: 10_000 });
        await expect(infoPanel).toContainText('40,000');

        // Should display format
        await expect(infoPanel).toContainText('SVS');
    });

    test('back button returns to home page', async ({ page }) => {
        // Navigate to viewer
        await page.locator('.slide-item, .slide-card', { hasText: 'TestSlide' }).first().click();
        await expect(page.locator('#app.page-viewer')).toBeVisible({ timeout: 10_000 });

        // Click back button
        await page.locator('#back-btn').click();

        // Should be back on home page
        await expect(page.locator('.folder-browser')).toBeVisible();
    });

    test('compare button switches to compare mode', async ({ page, mockSlideData }) => {
        // Navigate to viewer
        await page.locator('.slide-item, .slide-card', { hasText: 'TestSlide' }).first().click();
        await expect(page.locator('#app.page-viewer')).toBeVisible({ timeout: 10_000 });

        // Mock the slides list for compare picker
        await page.route('**/api/slides', (route) => {
            if (route.request().url().includes('/browse')) { return route.fallback(); }
            if (route.request().url().includes('/by-name')) { return route.fallback(); }
            if (route.request().url().match(/\/api\/slides\/[^/]+\//)) { return route.fallback(); }
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    slides: mockSlideData.browseRoot.slides,
                    total: 1,
                }),
            });
        });

        // Click compare button
        await page.locator('#compare-btn').click();

        // Should switch to compare page
        await expect(page.locator('#app.page-compare')).toBeVisible({ timeout: 10_000 });
    });
});
