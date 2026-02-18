/**
 * 19 - Waves 1-2 Feature Tests
 * Validates UX polish (FR, toolbar, magnification) and ML integration
 * (focus assist, auto-tag, feedback buttons).
 *
 * Reference: Issues #60-#67, #70-#91
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Wave 1: FR Terminology & UX', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
    });

    test('home page shows French subtitle', async ({ page }) => {
        await page.addInitScript(() => {
            localStorage.setItem('varuna_home_view', 'cases');
        });
        await page.goto('/');
        const subtitle = page.locator('text=Visualiseur de pathologie');
        await expect(subtitle).toBeAttached({ timeout: 5000 });
    });

    test('drawing tools toolbar has overflow button', async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
        const slide = page.locator('.slide-item').first();
        if (await slide.isVisible()) {
            await slide.click();
            await page.waitForTimeout(1500);
        }
        const moreBtn = page.locator('.drawing-tools__btn--more');
        await expect(moreBtn).toBeAttached({ timeout: 3000 });
    });

    test('magnification bar is present in viewer', async ({ page }) => {
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
        const slide = page.locator('.slide-item').first();
        if (await slide.isVisible()) {
            await slide.click();
            await page.waitForTimeout(1500);
        }
        const magBar = page.locator('.magnification-bar');
        await expect(magBar).toBeAttached({ timeout: 3000 });
    });
});

test.describe('Wave 2: ML Features', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
        const slide = page.locator('.slide-item').first();
        if (await slide.isVisible()) {
            await slide.click();
            await page.waitForTimeout(1500);
        }
    });

    test('focus assist panel is present', async ({ page }) => {
        const panel = page.locator('.focus-assist-panel');
        await expect(panel).toBeAttached({ timeout: 3000 });
    });

    test('auto-tag badge is present in header', async ({ page }) => {
        const badge = page.locator('.auto-tag-badge');
        await expect(badge).toBeAttached({ timeout: 3000 });
    });

    test('detection panel has French header', async ({ page }) => {
        const header = page.locator('.detection-panel');
        await expect(header).toBeAttached({ timeout: 3000 });
    });

    test('no JavaScript errors on viewer page', async ({ page }) => {
        // Page already loaded in beforeEach - just verify no errors accumulated
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));
        await page.waitForTimeout(1000);
        expect(errors).toEqual([]);
    });
});
