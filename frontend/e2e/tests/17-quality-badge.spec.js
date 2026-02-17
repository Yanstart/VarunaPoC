/**
 * 17 - Quality Badge Tests
 * Validates QualityBadge creation and display in viewer header.
 *
 * Reference: Issues #93, #94 [W4-QC01, W4-QC02]
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Quality Badge', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('no errors on page load with quality mocked', async ({ page }) => {
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));

        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        // Verify no JS errors from quality integration
        const qualityErrors = errors.filter(
            (e) => e.includes('Quality') || e.includes('quality') || e.includes('QualityBadge'),
        );
        expect(qualityErrors).toHaveLength(0);
    });

    test('badge is present in viewer header', async ({ page }) => {
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        const badge = page.locator('.quality-badge');
        await expect(badge).toBeAttached();
    });

    test('badge label contains Qualite', async ({ page }) => {
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        const label = page.locator('.quality-badge__label');
        await expect(label).toContainText('Qualit');
    });
});
