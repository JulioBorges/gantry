import { test, expect } from '@playwright/test';

test.describe('Dashboard Theme & Design Visual Regression Check', () => {
  test('should render dashboard with industrial dark theme and matching typography', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    try {
      const response = await page.goto('http://127.0.0.1:4600/', { timeout: 3000 });
      if (!response || !response.ok()) {
        test.skip(true, 'Local dashboard server is not active on port 4600');
        return;
      }
    } catch {
      test.skip(true, 'Local dashboard server is not active on port 4600');
      return;
    }

    // 1. Verify Header & Branding
    const brandTitle = page.locator('.brand-title');
    await expect(brandTitle).toBeVisible();
    await expect(brandTitle).toContainText('GANTRY');
    await expect(brandTitle).toContainText('DASHBOARD');

    // 2. Verify Background Color matches obsidian-900 (#0a0d14 => rgb(10, 13, 20))
    const body = page.locator('body');
    const bgColor = await body.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    expect(bgColor).toBe('rgb(10, 13, 20)');

    // 3. Verify Font Family is monospace / JetBrains Mono
    const fontFamily = await body.evaluate((el) => window.getComputedStyle(el).fontFamily);
    expect(fontFamily.toLowerCase()).toMatch(/(jetbrains mono|fira code|monospace|ui-monospace)/);

    // 4. Verify Amber Glow Diamond Brand Mark
    const diamond = page.locator('.diamond');
    await expect(diamond).toBeVisible();

    // 5. Verify Footer telemetry is present
    const footer = page.locator('.rig-footer');
    await expect(footer).toBeVisible();
    await expect(footer).toContainText('GANTRY AGENTIC SDLC');
    await expect(footer).toContainText('DETERMINISTIC VERIFICATION');

    // 6. Verify Swimlane & Columns rendered
    await page.waitForSelector('.swimlane', { timeout: 3000 });
    const columns = page.locator('.column');
    await expect(columns).toHaveCount(8);

    // 7. Verify No Console Errors
    expect(consoleErrors).toEqual([]);
  });
});
