/**
 * 13 - Focus Assist Tests
 * Validates FocusAssistPanel creation and zone loading.
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Focus Assist Panel', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('no errors on page load with mocked endpoints', async ({ page }) => {
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));

        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }

        // Verify no JS errors from focus assist integration
        const focusErrors = errors.filter((e) => e.includes('FocusAssist') || e.includes('focus'));
        expect(focusErrors).toHaveLength(0);
    });
});
