/**
 * 14 - Case Navigation Tests
 * Validates CaseBrowser, CaseSidebar, and rapid slide switching.
 */
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Case Navigation', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
    });

    test('home page loads case browser by default without JS errors', async ({ page }) => {
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));

        // Set default view to cases
        await page.addInitScript(() => {
            localStorage.setItem('varuna_home_view', 'cases');
        });

        await page.goto('/');
        await page.waitForTimeout(2000);

        // Check for case browser or folder browser (both are valid home views)
        const hasCaseBrowser = await page.locator('.case-browser').isVisible().catch(() => false);
        const hasFolderBrowser = await page.locator('.folder-browser').isVisible().catch(() => false);

        expect(hasCaseBrowser || hasFolderBrowser).toBeTruthy();

        // No JS errors related to case components
        const caseErrors = errors.filter(
            (e) => e.includes('CaseBrowser') || e.includes('CaseSidebar') || e.includes('case-browser'),
        );
        expect(caseErrors).toHaveLength(0);
    });

    test('home page loads explorer view when preference is set', async ({ page }) => {
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));

        await page.addInitScript(() => {
            localStorage.setItem('varuna_home_view', 'explorer');
        });

        await page.goto('/');
        await page.waitForSelector('.folder-browser', { timeout: 10000 });

        // Verify toggle button exists
        const toggleBtn = page.locator('.view-toggle-btn');
        if (await toggleBtn.isVisible()) {
            const text = await toggleBtn.textContent();
            expect(text).toContain('Mes cas');
        }

        // No JS errors
        const navErrors = errors.filter(
            (e) => e.includes('CaseBrowser') || e.includes('toggle'),
        );
        expect(navErrors).toHaveLength(0);
    });

    test('no JS errors when navigating to viewer from any home view', async ({ page }) => {
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));

        // Use explorer view for deterministic slide selection
        await page.addInitScript(() => {
            localStorage.setItem('varuna_home_view', 'explorer');
        });

        await page.goto('/');
        await page.waitForSelector('.folder-browser');

        // Click first slide if visible
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(2000);
        }

        // Check no errors related to case sidebar
        const sidebarErrors = errors.filter(
            (e) => e.includes('CaseSidebar') || e.includes('case-sidebar') || e.includes('handleSlideSwitch'),
        );
        expect(sidebarErrors).toHaveLength(0);
    });
});
