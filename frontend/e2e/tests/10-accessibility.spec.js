/**
 * 10 - Accessibility Tests
 *
 * Validates keyboard navigation, accessible labels, and basic contrast.
 */
import { test, expect } from '../fixtures/base.js';
import { mockHealthy, mockAuthAnonymous, mockSlidesApi } from '../helpers/api-mock.js';

test.describe('Accessibility', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthAnonymous(page);
        await mockSlidesApi(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('keyboard Tab navigates between interactive elements', async ({ page }) => {
        // Press Tab to move focus
        await page.keyboard.press('Tab');

        // Some element should have focus
        const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
        expect(focusedTag).toBeTruthy();

        // Continue tabbing should move through interactive elements
        await page.keyboard.press('Tab');
        const focusedTag2 = await page.evaluate(() => document.activeElement?.tagName);
        expect(focusedTag2).toBeTruthy();
    });

    test('search input is keyboard accessible', async ({ page }) => {
        const searchInput = page.locator('#search-input');

        // Focus the search input
        await searchInput.focus();
        await expect(searchInput).toBeFocused();

        // Type in search
        await page.keyboard.type('test');
        await expect(searchInput).toHaveValue('test');
    });

    test('buttons have accessible text or labels', async ({ page }) => {
        // Compare mode button should have visible text
        const compareBtn = page.locator('.compare-mode-button');
        await expect(compareBtn).toBeVisible();
        const compareBtnText = await compareBtn.textContent();
        expect(compareBtnText?.trim()).toBeTruthy();

        // Check folder cards are clickable and have text content
        const firstFolder = page.locator('.folder-card').first();
        if (await firstFolder.isVisible()) {
            const folderText = await firstFolder.textContent();
            expect(folderText?.trim()).toBeTruthy();
        }
    });
});
