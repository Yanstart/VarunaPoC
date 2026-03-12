/**
 * 02 - Navigation Tests
 *
 * Validates folder browsing, breadcrumbs, and search functionality.
 */
import { test, expect } from '../fixtures/base.js';
import { mockHealthy, mockAuthAnonymous, mockSlidesApi } from '../helpers/api-mock.js';

test.describe('Folder Navigation', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await mockHealthy(page);
        await mockAuthAnonymous(page);
        await mockSlidesApi(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('browse root displays folders and slides', async ({ page }) => {
        // Folders section should be visible
        await expect(page.locator('.folders-section')).toBeVisible();
        // At least one folder card
        await expect(page.locator('.folder-card').first()).toBeVisible();
        // Folder names
        await expect(page.locator('.folder-card .folder-name').first()).toHaveText('3DHistech');
        // Slides section
        await expect(page.locator('.slides-section')).toBeVisible();
    });

    test('clicking folder navigates and updates breadcrumb', async ({ page }) => {
        // Click on the "3DHistech" folder
        await page.locator('.folder-card', { hasText: '3DHistech' }).click();

        // Breadcrumb should show subfolder path
        await expect(page.locator('#breadcrumb-content')).toContainText('3DHistech');

        // Back button should be visible
        await expect(page.locator('#back-button')).toBeVisible();

        // Should display slides from subfolder
        await expect(page.locator('.slides-section')).toBeVisible();
    });

    test('breadcrumb root link navigates home', async ({ page }) => {
        // Navigate to subfolder first
        await page.locator('.folder-card', { hasText: '3DHistech' }).click();
        await expect(page.locator('#breadcrumb-content')).toContainText('3DHistech');

        // Click on root breadcrumb item
        await page.locator('.breadcrumb-item[data-path="/"]').click();

        // Should be back at root with folders visible
        await expect(page.locator('.folder-card', { hasText: '3DHistech' })).toBeVisible();
    });

    test('search filters results', async ({ page }) => {
        const searchInput = page.locator('#search-input');
        await searchInput.fill('Aperio');

        // "3DHistech" folder should be filtered out
        await expect(page.locator('.folder-card', { hasText: '3DHistech' })).toBeHidden();
        // "Aperio" folder should remain
        await expect(page.locator('.folder-card', { hasText: 'Aperio' })).toBeVisible();
    });

    test('empty folder shows message', async ({ page, mockSlideData }) => {
        // Override the browse mock to navigate to empty folder
        await page.route('**/api/v1/slides/browse**', (route) => {
            const url = new URL(route.request().url());
            const path = url.searchParams.get('path') || '/';
            if (path === '/EmptyFolder') {
                return route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify(mockSlideData.browseEmpty),
                });
            }
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    ...mockSlideData.browseRoot,
                    folders: [
                        ...mockSlideData.browseRoot.folders,
                        { name: 'EmptyFolder', path: '/EmptyFolder', item_count: 0 },
                    ],
                }),
            });
        });

        // Reload to pick up new mock
        await page.reload();
        await page.waitForSelector('.folder-browser');

        // Navigate to empty folder
        await page.locator('.folder-card', { hasText: 'EmptyFolder' }).click();

        // Should show empty message
        await expect(page.locator('.empty-folder')).toBeVisible();
        await expect(page.locator('.empty-folder')).toContainText('Dossier vide');
    });
});
