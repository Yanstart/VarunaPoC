/**
 * 16 - Clustering Tests
 * Validates ClusteringPanel creation and display.
 *
 * Reference: Issue #92 [W4-ML04]
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Clustering Panel', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('no errors on page load with clustering mocked', async ({ page }) => {
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));

        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        // Verify no JS errors from clustering integration
        const clusteringErrors = errors.filter(
            (e) => e.includes('Clustering') || e.includes('clustering') || e.includes('clusterSlide'),
        );
        expect(clusteringErrors).toHaveLength(0);
    });

    test('panel is present in ML container', async ({ page }) => {
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        const panel = page.locator('.clustering-panel');
        await expect(panel).toBeAttached();
    });

    test('panel header shows Clustering morphologique', async ({ page }) => {
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        const header = page.locator('.clustering-panel__title');
        await expect(header).toHaveText('Clustering morphologique');
    });
});
