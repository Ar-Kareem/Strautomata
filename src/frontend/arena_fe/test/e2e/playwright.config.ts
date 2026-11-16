import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';

// E2E_BASE_URL reuses a dev server that is already running (e.g. http://127.0.0.1:4299);
// otherwise one is started on PORT for the run.
const PORT = Number(process.env.E2E_PORT ?? 4320);
const baseURL = process.env.E2E_BASE_URL ?? `http://127.0.0.1:${PORT}`;
const appDir = path.resolve(__dirname, '../..');

export default defineConfig({
  testDir: __dirname,
  testMatch: '*.e2e.ts',
  outputDir: path.join(__dirname, 'test-results'),
  // Pyodide boots a full Python runtime per page; matches run inside it
  timeout: 240_000,
  expect: { timeout: 30_000 },
  // every test gets its own page and runtimes, so tests are independent. Past half the cores the
  // runtimes compete for CPU and the run gets no faster. E2E_WORKERS overrides.
  fullyParallel: true,
  workers: process.env.E2E_WORKERS ? Number(process.env.E2E_WORKERS) : '50%',
  reporter: [['list'], ['html', { outputFolder: path.join(__dirname, 'playwright-report'), open: 'never' }]],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    viewport: { width: 1400, height: 900 }
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1400, height: 900 } } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], viewport: { width: 1400, height: 900 } } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], viewport: { width: 1400, height: 900 } } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'] } }
  ],
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: `bash scripts/node-run.sh node_modules/@angular/cli/bin/ng.js serve --host 127.0.0.1 --port ${PORT}`,
        cwd: appDir,
        url: baseURL,
        reuseExistingServer: true,
        timeout: 600_000
      }
});
