/**
 * 15 - Cell Counting Tests
 * Validates CellCountingPanel creation and display.
 *
 * Reference: Issue #83 [W4-ML02]
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Cell Counting Panel', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('no errors on page load with cell counting mocked', async ({ page }) => {
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));

        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        // Verify no JS errors from cell counting integration
        const countingErrors = errors.filter(
            (e) => e.includes('CellCounting') || e.includes('cellCounting') || e.includes('countCells'),
        );
        expect(countingErrors).toHaveLength(0);
    });

    test('panel is present in ML container', async ({ page }) => {
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        const panel = page.locator('.cell-counting-panel');
        await expect(panel).toBeAttached();
    });

    test('panel header shows Comptage cellulaire', async ({ page }) => {
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        const header = page.locator('.cell-counting-panel__title');
        await expect(header).toHaveText('Comptage cellulaire');
    });
});
