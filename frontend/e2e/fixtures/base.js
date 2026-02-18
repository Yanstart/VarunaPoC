/**
 * Shared Playwright fixtures for VarunaPoC E2E tests.
 *
 * Provides:
 * - apiUrl: backend API base URL
 * - waitForApp: helper to wait until #app is present in DOM
 * - mockSlideData: deterministic slide data for mocking
 */
import { test as base } from '@playwright/test';

export const test = base.extend({
    /** Backend API base URL */
    apiUrl: [process.env.API_URL || 'http://localhost:8000', { option: true }],

    /**
     * Override page fixture to force explorer home view by default.
     * Wave 3 changed the default to CaseBrowser, but existing tests
     * expect FolderBrowser. Individual tests can override via addInitScript.
     */
    page: async ({ page }, use) => {
        await page.addInitScript(() => {
            localStorage.setItem('varuna_home_view', 'explorer');
        });
        await use(page);
    },

    /** Wait for the app container to be rendered */
    waitForApp: async ({ page }, use) => {
        const helper = async () => {
            await page.waitForSelector('#app', { state: 'attached', timeout: 15_000 });
        };
        await use(helper);
    },

    /** Deterministic mock slide data */
    // eslint-disable-next-line no-empty-pattern
    mockSlideData: async ({}, use) => {
        const data = {
            slide: {
                id: 'test-slide-001',
                name: 'TestSlide.svs',
                format: 'SVS',
                structure_type: 'single_file',
                is_supported: true,
                has_joint_files: false,
                joint_files_count: 0,
                has_companion_dirs: false,
                companion_dirs_count: 0,
                notes: null,
            },
            slideInfo: {
                dimensions: [50000, 40000],
                level_count: 5,
                vendor: 'Aperio',
                mpp: 0.25,
            },
            browseRoot: {
                current_path: '/',
                parent_path: null,
                breadcrumb: ['/'],
                folders: [
                    { name: '3DHistech', path: '/3DHistech', item_count: 3 },
                    { name: 'Aperio', path: '/Aperio', item_count: 5 },
                ],
                slides: [
                    {
                        id: 'test-slide-001',
                        name: 'TestSlide.svs',
                        format: 'SVS',
                        structure_type: 'single_file',
                        is_supported: true,
                        has_joint_files: false,
                        joint_files_count: 0,
                        has_companion_dirs: false,
                        companion_dirs_count: 0,
                        notes: null,
                    },
                ],
                files: [],
            },
            browseSubfolder: {
                current_path: '/3DHistech',
                parent_path: '/',
                breadcrumb: ['/', '/3DHistech'],
                folders: [],
                slides: [
                    {
                        id: 'histech-slide-001',
                        name: 'Sample_MRXS.mrxs',
                        format: 'MRXS',
                        structure_type: 'multi_file',
                        is_supported: true,
                        has_joint_files: true,
                        joint_files_count: 12,
                        has_companion_dirs: true,
                        companion_dirs_count: 1,
                        notes: null,
                    },
                ],
                files: [],
            },
            browseEmpty: {
                current_path: '/EmptyFolder',
                parent_path: '/',
                breadcrumb: ['/', '/EmptyFolder'],
                folders: [],
                slides: [],
                files: [],
            },
            annotations: [
                {
                    id: 'ann-001',
                    slide_id: 'test-slide-001',
                    type: 'rectangle',
                    label: 'Tumor',
                    color: '#e74c3c',
                    geometry: { x: 1000, y: 2000, width: 500, height: 300 },
                    created_by: 'anonymous',
                },
                {
                    id: 'ann-002',
                    slide_id: 'test-slide-001',
                    type: 'polygon',
                    label: 'Normal',
                    color: '#2ecc71',
                    geometry: { points: [[100, 200], [300, 200], [300, 400], [100, 400]] },
                    created_by: 'anonymous',
                },
            ],
        };
        await use(data);
    },
});

export { expect } from '@playwright/test';
