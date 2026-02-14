// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for VarunaPoC E2E tests.
 *
 * - baseURL: localhost:5173 (Vite dev) in local, localhost:80 (Docker/Nginx) in CI
 * - webServer: auto-starts `npm run dev` locally
 * - Chromium only by default for fast CI; Firefox/WebKit opt-in
 */
export default defineConfig({
    testDir: './tests',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 1 : 0,
    workers: process.env.CI ? 1 : undefined,
    timeout: 30_000,

    expect: {
        timeout: 10_000,
    },

    reporter: process.env.CI
        ? [['github'], ['html', { open: 'never', outputFolder: 'playwright-report' }]]
        : [['html', { open: 'on-failure', outputFolder: 'playwright-report' }]],

    outputDir: 'test-results',

    use: {
        baseURL: process.env.BASE_URL || 'http://localhost:5173',
        actionTimeout: 10_000,
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        // Opt-in: uncomment for broader coverage
        // {
        //     name: 'firefox',
        //     use: { ...devices['Desktop Firefox'] },
        // },
        // {
        //     name: 'webkit',
        //     use: { ...devices['Desktop Safari'] },
        // },
    ],

    // Auto-start Vite dev server when running locally (not in CI)
    ...(!process.env.CI && {
        webServer: {
            command: 'npm run dev',
            url: 'http://localhost:5173',
            reuseExistingServer: true,
            timeout: 30_000,
        },
    }),
});
