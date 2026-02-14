/**
 * 01 - Health Check Tests
 *
 * Validates that backend and frontend are operational.
 */
import { test, expect } from '../fixtures/base.js';
import { mockHealthy, mockAuthAnonymous, mockSlidesApi } from '../helpers/api-mock.js';

test.describe('Health Checks', () => {
    test('backend /api/health returns healthy', async ({ page, apiUrl }) => {
        const response = await page.request.get(`${apiUrl}/api/health`);
        expect(response.ok()).toBeTruthy();
        const body = await response.json();
        expect(body).toHaveProperty('status', 'healthy');
    });

    test('frontend loads with correct title', async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthAnonymous(page);
        await mockSlidesApi(page, mockSlideData);

        await page.goto('/');
        await expect(page).toHaveTitle('VarunaPoC - Digital Pathology Viewer');
    });

    test('home page displays the FolderBrowser', async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthAnonymous(page);
        await mockSlidesApi(page, mockSlideData);

        await page.goto('/');
        await expect(page.locator('.folder-browser')).toBeVisible();
        await expect(page.locator('.home-title h1')).toHaveText('VarunaPoC');
    });
});
