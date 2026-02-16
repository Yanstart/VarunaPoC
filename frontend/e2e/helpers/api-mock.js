/**
 * API mock helpers for VarunaPoC E2E tests.
 *
 * Uses Playwright route interception to mock backend responses,
 * enabling deterministic and fast tests without a running backend.
 */

/**
 * Mock /api/health endpoint
 * @param {import('@playwright/test').Page} page
 */
export async function mockHealthy(page) {
    await page.route('**/api/health', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ status: 'healthy' }),
        }),
    );
}

/**
 * Mock /api/slides/browse endpoint with provided data.
 * Handles both root and subfolder requests.
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 */
export async function mockSlidesApi(page, mockData) {
    await page.route('**/api/slides/browse**', (route) => {
        const url = new URL(route.request().url());
        const path = url.searchParams.get('path') || '/';

        let responseData;
        if (path === '/') {
            responseData = mockData.browseRoot;
        } else if (path === '/3DHistech') {
            responseData = mockData.browseSubfolder;
        } else if (path === '/EmptyFolder') {
            responseData = mockData.browseEmpty;
        } else {
            responseData = mockData.browseEmpty;
        }

        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(responseData),
        });
    });

    // Also mock /api/slides (recursive list for slide picker)
    await page.route('**/api/slides', (route) => {
        if (route.request().url().includes('/browse')) { return route.fallback(); }
        if (route.request().url().includes('/by-name')) { return route.fallback(); }
        if (route.request().url().match(/\/api\/slides\/[^/]+\//)) { return route.fallback(); }

        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                slides: mockData.browseRoot.slides,
                total: mockData.browseRoot.slides.length,
            }),
        });
    });
}

/**
 * Mock /api/slides/{id}/info endpoint
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 */
export async function mockSlideInfo(page, mockData) {
    await page.route('**/api/slides/*/info', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockData.slideInfo),
        }),
    );
}

/**
 * Mock /api/slides/{id}/overview with a small placeholder image
 * @param {import('@playwright/test').Page} page
 */
export async function mockSlideOverview(page) {
    await page.route('**/api/slides/*/overview', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'image/jpeg',
            // 1x1 red JPEG placeholder
            body: Buffer.from(
                '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMCwsKCwsM' +
                'DREHGA0MDQ4MHCwkJDgnKCs0NDRMRDY5R0NTSD/2wBDAQMEBAUEBQkFBQkNLA0sDQ0NDQ0NDQ0NDQ0N' +
                'DQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ3/wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/' +
                'EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AKwA//9k=',
                'base64',
            ),
        }),
    );
}

/**
 * Mock tile endpoint with a small placeholder
 * @param {import('@playwright/test').Page} page
 */
export async function mockTiles(page) {
    await page.route('**/api/slides/*/tiles/**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'image/jpeg',
            body: Buffer.from(
                '/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMCwsKCwsM' +
                'DREHGA0MDQ4MHCwkJDgnKCs0NDRMRDY5R0NTSD/2wBDAQMEBAUEBQkFBQkNLA0sDQ0NDQ0NDQ0NDQ0N' +
                'DQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ3/wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/' +
                'EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AKwA//9k=',
                'base64',
            ),
        }),
    );
}

/**
 * Mock DZI (Deep Zoom Image) XML response for OpenSeadragon
 * @param {import('@playwright/test').Page} page
 */
export async function mockDzi(page) {
    await page.route('**/api/slides/*/dzi**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                width: 50000,
                height: 40000,
                tile_size: 256,
                overlap: 0,
                levels: 5,
                level_dimensions: [
                    [50000, 40000],
                    [25000, 20000],
                    [12500, 10000],
                    [6250, 5000],
                    [3125, 2500],
                ],
                level_downsamples: [1, 2, 4, 8, 16],
            }),
        }),
    );
}

/**
 * Mock /api/auth/me for anonymous mode (AUTH_ENABLED=false)
 * @param {import('@playwright/test').Page} page
 */
export async function mockAuthAnonymous(page) {
    await page.route('**/api/auth/me', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                auth_enabled: false,
                user: {
                    sub: 'anonymous',
                    preferred_username: 'anonymous',
                    realm_access: { roles: ['ADMIN_TECHNIQUE'] },
                },
            }),
        }),
    );
}

/**
 * Mock /api/auth/me for authenticated mode (AUTH_ENABLED=true, no token)
 * @param {import('@playwright/test').Page} page
 */
export async function mockAuthRequired(page) {
    await page.route('**/api/auth/me', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                auth_enabled: true,
                user: null,
            }),
        }),
    );
}

/**
 * Mock /api/auth/me for authenticated user
 * @param {import('@playwright/test').Page} page
 * @param {string} [role='MEDECIN'] - User role
 */
export async function mockAuthAuthenticated(page, role = 'MEDECIN') {
    await page.route('**/api/auth/me', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                auth_enabled: true,
                user: {
                    sub: 'user-123',
                    preferred_username: 'dr.dupont',
                    email: 'dupont@chu-namur.be',
                    realm_access: { roles: [role] },
                },
            }),
        }),
    );
}

/**
 * Mock /api/annotations/{slide_id} endpoints
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 */
export async function mockAnnotations(page, mockData) {
    // GET annotations
    await page.route('**/api/annotations/*', (route) => {
        if (route.request().method() === 'GET') {
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(mockData.annotations),
            });
        }
        // POST new annotation
        if (route.request().method() === 'POST') {
            return route.fulfill({
                status: 201,
                contentType: 'application/json',
                body: JSON.stringify({
                    id: 'ann-new-001',
                    ...JSON.parse(route.request().postData() || '{}'),
                }),
            });
        }
        // DELETE annotation
        if (route.request().method() === 'DELETE') {
            return route.fulfill({
                status: 204,
            });
        }
        return route.fallback();
    });
}

/**
 * Mock ML prediction endpoint
 * @param {import('@playwright/test').Page} page
 */
export async function mockMLPredict(page) {
    await page.route('**/api/ml/predict/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                prediction: 'Tumor',
                confidence: 0.92,
                uncertainty: 0.08,
                processing_time_ms: 1250,
            }),
        }),
    );
}

/**
 * Mock ML heatmap endpoint
 * @param {import('@playwright/test').Page} page
 */
export async function mockMLHeatmap(page) {
    await page.route('**/api/ml/heatmap/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'image/png',
            // Tiny 1x1 transparent PNG
            body: Buffer.from(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
                'base64',
            ),
        }),
    );
}

/**
 * Mock /api/slides/by-name/{name} endpoint
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 * @param {boolean} [found=true] - Whether slide should be found
 */
export async function mockSlideByName(page, mockData, found = true) {
    await page.route('**/api/slides/by-name/*', (route) => {
        if (found) {
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(mockData.slide),
            });
        }
        return route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Slide not found' }),
        });
    });
}

/**
 * Mock quality metrics endpoints
 * @param {import('@playwright/test').Page} page
 */
export async function mockQualityMetrics(page) {
    await page.route('**/api/annotations/*/annotators', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify([
                { username: 'dr.dupont', annotation_count: 15, labels_used: ['Tumor', 'Normal'] },
                { username: 'dr.martin', annotation_count: 12, labels_used: ['Tumor', 'Normal', 'Stroma'] },
            ]),
        }),
    );

    await page.route('**/api/annotations/*/quality/kappa**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                kappa: 0.78,
                interpretation: 'Substantial agreement',
                annotator_a: 'dr.dupont',
                annotator_b: 'dr.martin',
            }),
        }),
    );

    await page.route('**/api/annotations/*/quality/confusion**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                labels: ['Tumor', 'Normal', 'Stroma'],
                matrix: [[10, 2, 0], [1, 8, 1], [0, 1, 4]],
                annotator_a: 'dr.dupont',
                annotator_b: 'dr.martin',
            }),
        }),
    );
}

/**
 * Setup all common mocks for a standard test scenario.
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 */
export async function setupFullMocks(page, mockData) {
    await mockHealthy(page);
    await mockAuthAnonymous(page);
    await mockSlidesApi(page, mockData);
    await mockSlideInfo(page, mockData);
    await mockSlideOverview(page);
    await mockDzi(page);
    await mockTiles(page);
    await mockAnnotations(page, mockData);
}
