/**
 * API mock helpers for VarunaPoC E2E tests.
 *
 * Uses Playwright route interception to mock backend responses,
 * enabling deterministic and fast tests without a running backend.
 */

/**
 * Mock /api/v1/health endpoint
 * @param {import('@playwright/test').Page} page
 */
export async function mockHealthy(page) {
    await page.route('**/api/v1/health', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ status: 'healthy' }),
        }),
    );
}

/**
 * Mock /api/v1/slides/browse endpoint with provided data.
 * Handles both root and subfolder requests.
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 */
export async function mockSlidesApi(page, mockData) {
    await page.route('**/api/v1/slides/browse**', (route) => {
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

    // Also mock /api/v1/slides (recursive list for slide picker)
    await page.route('**/api/v1/slides', (route) => {
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
 * Mock /api/v1/slides/{id}/info endpoint
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 */
export async function mockSlideInfo(page, mockData) {
    await page.route('**/api/v1/slides/*/info', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockData.slideInfo),
        }),
    );
}

/**
 * Mock /api/v1/slides/{id}/overview with a small placeholder image
 * @param {import('@playwright/test').Page} page
 */
export async function mockSlideOverview(page) {
    await page.route('**/api/v1/slides/*/overview', (route) =>
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
    await page.route('**/api/v1/slides/*/tiles/**', (route) =>
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
    await page.route('**/api/v1/slides/*/dzi**', (route) =>
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
 * Mock /api/v1/auth/me for anonymous mode (AUTH_ENABLED=false)
 * @param {import('@playwright/test').Page} page
 */
export async function mockAuthAnonymous(page) {
    await page.route('**/api/v1/auth/me', (route) =>
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
 * Mock /api/v1/auth/me for authenticated mode (AUTH_ENABLED=true, no token)
 * @param {import('@playwright/test').Page} page
 */
export async function mockAuthRequired(page) {
    await page.route('**/api/v1/auth/me', (route) =>
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
 * Mock /api/v1/auth/me for authenticated user
 * @param {import('@playwright/test').Page} page
 * @param {string} [role='MEDECIN'] - User role
 */
export async function mockAuthAuthenticated(page, role = 'MEDECIN') {
    await page.route('**/api/v1/auth/me', (route) =>
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
 * Mock /api/v1/annotations/{slide_id} endpoints
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 */
export async function mockAnnotations(page, mockData) {
    // GET annotations
    await page.route('**/api/v1/annotations/*', (route) => {
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
    await page.route('**/api/v1/ml/predict/*', (route) =>
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
    await page.route('**/api/v1/ml/heatmap/*', (route) =>
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
 * Mock /api/v1/slides/by-name/{name} endpoint
 * @param {import('@playwright/test').Page} page
 * @param {Object} mockData - mockSlideData from fixtures
 * @param {boolean} [found=true] - Whether slide should be found
 */
export async function mockSlideByName(page, mockData, found = true) {
    await page.route('**/api/v1/slides/by-name/*', (route) => {
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
    await page.route('**/api/v1/annotations/*/annotators', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify([
                { username: 'dr.dupont', annotation_count: 15, labels_used: ['Tumor', 'Normal'] },
                { username: 'dr.martin', annotation_count: 12, labels_used: ['Tumor', 'Normal', 'Stroma'] },
            ]),
        }),
    );

    await page.route('**/api/v1/annotations/*/quality/kappa**', (route) =>
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

    await page.route('**/api/v1/annotations/*/quality/confusion**', (route) =>
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
 * Mock ML focus zones endpoint (Wave 2)
 * @param {import('@playwright/test').Page} page
 */
export async function mockMLFocusZones(page) {
    await page.route('**/api/v1/ml/focus/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                slide_id: 'test-slide-001',
                zones: [
                    { rank: 1, score: 0.95, centroid: [25000, 20000], bbox: [24000, 19000, 26000, 21000], area_px: 4000000 },
                    { rank: 2, score: 0.82, centroid: [35000, 15000], bbox: [34000, 14000, 36000, 16000], area_px: 2000000 },
                    { rank: 3, score: 0.67, centroid: [10000, 30000], bbox: [9000, 29000, 11000, 31000], area_px: 1500000 },
                ],
                model_id: 'ctranspath',
                total_zones_above_threshold: 3,
            }),
        }),
    );
}

/**
 * Mock ML measurement endpoint (Wave 2)
 * @param {import('@playwright/test').Page} page
 */
export async function mockMLMeasurement(page) {
    await page.route('**/api/v1/ml/measure/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                slide_id: 'test-slide-001',
                measurements: [
                    { region_id: 0, label: 'Tumeur', feret_diameter_mm: 12.4, area_mm2: 45.2, perimeter_mm: 28.1, bbox_mm: [6.0, 4.75, 6.5, 5.25] },
                    { region_id: 1, label: 'Tumeur', feret_diameter_mm: 8.7, area_mm2: 22.8, perimeter_mm: 19.4, bbox_mm: [8.5, 3.5, 9.0, 4.0] },
                ],
                mpp: 0.25,
                unit: 'mm',
            }),
        }),
    );
}

/**
 * Mock ML feedback endpoint (Wave 2)
 * @param {import('@playwright/test').Page} page
 */
export async function mockMLFeedback(page) {
    await page.route('**/api/v1/ml/feedback/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                correction_id: 'corr-001',
                status: 'recorded',
                stats: { confirmed: 1, rejected: 0, refined: 0, relabeled: 0 },
            }),
        }),
    );
}

/**
 * Mock ML tags endpoint (Wave 2)
 * @param {import('@playwright/test').Page} page
 */
export async function mockMLTags(page) {
    await page.route('**/api/v1/ml/tags/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                slide_id: 'test-slide-001',
                tags: { organ: 'Prostate', stain: 'H&E', pathology: null },
                source: 'filename',
            }),
        }),
    );
}

/**
 * Mock ML models list endpoint (Wave 2)
 * @param {import('@playwright/test').Page} page
 */
export async function mockMLModels(page) {
    await page.route('**/api/v1/ml/models', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                models: [
                    { model_id: 'ctranspath', model_name: 'CTransPath', status: 'loaded' },
                    { model_id: 'phikon-v2', model_name: 'Phikon v2', status: 'available' },
                ],
            }),
        }),
    );
}

/**
 * Mock ML similarity search endpoint (Wave 3)
 * @param {import('@playwright/test').Page} page
 */
export async function mockMLSimilarity(page) {
    await page.route('**/api/v1/ml/similar/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                query_slide_id: 'test-slide-001',
                results: [
                    { slide_id: 'slide-002', score: 0.94, name: 'Case_B_HE.svs', overview_url: '/api/v1/slides/slide-002/overview' },
                    { slide_id: 'slide-003', score: 0.87, name: 'Case_C_HE.svs', overview_url: '/api/v1/slides/slide-003/overview' },
                ],
                index_size: 50,
            }),
        }),
    );
}

/**
 * Mock cell counting endpoint.
 * @param {import('@playwright/test').Page} page
 */
export async function mockCellCounting(page) {
    await page.route('**/api/v1/ml/count/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                total_cells: 1247,
                positive: 312,
                negative: 935,
                ratio: 0.25,
                percentage: '25.0%',
                processing_time_ms: 2800,
            }),
        }),
    );
}

/**
 * Mock clustering endpoint.
 * @param {import('@playwright/test').Page} page
 */
export async function mockClustering(page) {
    await page.route('**/api/v1/ml/cluster/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                clusters: [
                    { id: 0, color: '#e74c3c', label: 'Cluster A', tile_count: 18, centroid_embedding: [] },
                    { id: 1, color: '#2ecc71', label: 'Cluster B', tile_count: 22, centroid_embedding: [] },
                    { id: 2, color: '#3498db', label: 'Cluster C', tile_count: 14, centroid_embedding: [] },
                    { id: 3, color: '#f39c12', label: 'Cluster D', tile_count: 10, centroid_embedding: [] },
                ],
                tile_assignments: [
                    { x: 0, y: 0, cluster_id: 0 },
                    { x: 1, y: 0, cluster_id: 1 },
                    { x: 0, y: 1, cluster_id: 2 },
                    { x: 1, y: 1, cluster_id: 3 },
                ],
                processing_time_ms: 1500,
                metadata: { mode: 'mock', grid_size: 8, model_id: 'unknown' },
            }),
        }),
    );
}

/**
 * Mock slide quality endpoint (Wave 4).
 * @param {import('@playwright/test').Page} page
 */
export async function mockSlideQuality(page) {
    await page.route('**/api/v1/ml/quality/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                overall_score: 0.85,
                quality_label: 'Bonne',
                artifacts: [
                    { type: 'fold', severity: 'minor', bbox: [1000, 2000, 1500, 2500], area_percent: 2.1 },
                ],
                recommendation: 'Qualité suffisante pour diagnostic',
                processing_time_ms: 450,
            }),
        }),
    );
}

/**
 * Mock drift report endpoints (Wave 4).
 * @param {import('@playwright/test').Page} page
 */
export async function mockDriftReport(page) {
    await page.route('**/api/v1/ml/drift/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                model_id: 'ctranspath',
                report_date: '2026-02-17T12:00:00Z',
                metrics: [
                    { metric_name: 'mmd', value: 0.08, threshold: 0.10, is_drifted: false, window_size: 100 },
                    { metric_name: 'ks_statistic', value: 0.12, threshold: 0.15, is_drifted: false, window_size: 100 },
                ],
                overall_drifted: false,
                recommendation: 'No action needed',
                processing_time_ms: 320,
            }),
        }),
    );

    await page.route('**/api/v1/ml/drift', (route) => {
        // Only match exact /api/v1/ml/drift (not /api/v1/ml/drift/xxx)
        const url = route.request().url();
        if (url.match(/\/api\/ml\/drift\/[^/]+/)) return route.fallback();
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                reports: [{
                    model_id: 'ctranspath',
                    report_date: '2026-02-17T12:00:00Z',
                    metrics: [
                        { metric_name: 'mmd', value: 0.08, threshold: 0.10, is_drifted: false, window_size: 100 },
                        { metric_name: 'ks_statistic', value: 0.12, threshold: 0.15, is_drifted: false, window_size: 100 },
                    ],
                    overall_drifted: false,
                    recommendation: 'No action needed',
                    processing_time_ms: 320,
                }],
            }),
        });
    });
}

/**
 * Mock /api/v1/slides/worklist endpoint
 * @param {import('@playwright/test').Page} page
 */
export async function mockWorklist(page) {
    await page.route('**/api/v1/slides/worklist', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                items: [
                    { slide_id: 'test-slide-001', slide_name: 'HE_prostate_2024.svs', case_path: '/Cases/Patient_001', status: 'pending', assigned_date: '2026-02-15T10:00:00Z', is_new: true },
                    { slide_id: 'test-slide-002', slide_name: 'HE_breast_2024.svs', case_path: '/Cases/Patient_002', status: 'in_progress', assigned_date: '2026-02-14T09:00:00Z', is_new: false },
                ],
                counts: { pending: 1, in_progress: 1, completed: 0 },
            }),
        }),
    );
}

/**
 * Mock /api/v1/slides/history endpoint
 * @param {import('@playwright/test').Page} page
 */
export async function mockHistory(page) {
    await page.route('**/api/v1/slides/history**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                items: [
                    { slide_id: 'test-slide-001', slide_name: 'HE_prostate_2024.svs', viewed_at: '2026-02-17T11:30:00Z', view_count: 3 },
                ],
                total: 1,
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
    await mockMLTags(page);
    await mockMLFocusZones(page);
    await mockMLMeasurement(page);
    await mockMLFeedback(page);
    await mockMLModels(page);
    await mockMLSimilarity(page);
    await mockCellCounting(page);
    await mockClustering(page);
    await mockSlideQuality(page);
    await mockDriftReport(page);
    await mockWorklist(page);
    await mockHistory(page);
}
