import { defineConfig, devices } from '@playwright/test';

// webServer is global. Start Astro only when this run includes a site project.
function siteProjectSelected(argv: string[]): boolean {
  const selected: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--project' || arg === '-p') {
      selected.push(argv[i + 1] ?? '');
    } else if (arg.startsWith('--project=')) {
      selected.push(arg.slice('--project='.length));
    }
  }
  return selected.length === 0 || selected.some((name) => name !== 'dashboard');
}

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:4321/gantry/',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'desktop-chrome',
      testIgnore: '**/dashboard.spec.ts',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-chrome',
      testIgnore: '**/dashboard.spec.ts',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'dashboard',
      testMatch: '**/dashboard.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://127.0.0.1:4600',
      },
    },
  ],
  webServer: siteProjectSelected(process.argv)
    ? {
        command: 'npm run build && npm run preview -- --port 4321 --host',
        url: 'http://localhost:4321/gantry/',
        reuseExistingServer: !process.env.CI,
        timeout: 120000,
      }
    : undefined,
});
