/**
 * 08 - PACS Deep Link Tests
 *
 * Validates /slide/{name} URL routing, slide resolution, and error handling.
 */
import { test, expect } from '../fixtures/base.js';
import {
    mockHealthy,
    mockAuthAnonymous,
    mockSlideByName,
    mockSlideInfo,
    mockSlideOverview,
    mockDzi,
    mockTiles,
    mockAnnotations,
    mockSlidesApi,
} from '../helpers/api-mock.js';

test.describe('PACS Deep Link', () => {
    test('URL /slide/TestSlide resolves and opens viewer', async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthAnonymous(page);
        await mockSlideByName(page, mockSlideData, true);
        await mockSlideInfo(page, mockSlideData);
        await mockSlideOverview(page);
        await mockDzi(page);
        await mockTiles(page);
        await mockAnnotations(page, mockSlideData);
        await mockSlidesApi(page, mockSlideData);

        // Navigate directly to deep link
        await page.goto('/slide/TestSlide');

        // Should show loading then viewer
        await expect(page.locator('#app.page-viewer')).toBeVisible({ timeout: 15_000 });
        await expect(page.locator('#viewer')).toBeAttached();
    });

    test('slide found shows viewer with correct slide', async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthAnonymous(page);
        await mockSlideByName(page, mockSlideData, true);
        await mockSlideInfo(page, mockSlideData);
        await mockSlideOverview(page);
        await mockDzi(page);
        await mockTiles(page);
        await mockAnnotations(page, mockSlideData);
        await mockSlidesApi(page, mockSlideData);

        await page.goto('/slide/TestSlide');

        // Viewer should display slide name in header
        await expect(page.locator('.viewer-title')).toContainText('TestSlide', {
            timeout: 15_000,
        });
    });

    test('slide not found shows error page', async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthAnonymous(page);
        await mockSlideByName(page, mockSlideData, false);
        await mockSlidesApi(page, mockSlideData);

        await page.goto('/slide/NonExistentSlide');

        // Should show error page
        await expect(page.locator('.error-page')).toBeVisible({ timeout: 15_000 });
        await expect(page.locator('.error-page')).toContainText('Slide Not Found');
    });
});
