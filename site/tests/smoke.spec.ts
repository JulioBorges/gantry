import { test, expect } from '@playwright/test';

test.describe('Gantry Site Shell Smoke Tests', () => {
  test('should render shell, heading, industrial tokens, and correct metadata without errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/gantry/');

    // 1. Verify Page Title and Meta Description
    await expect(page).toHaveTitle('Gantry // Harness-Neutral Agentic SDLC');
    const description = page.locator('meta[name="description"]');
    await expect(description).toHaveAttribute('content', /Deterministic agentic SDLC skill pack/);

    // 2. Verify Industrial Header & Branding
    const brand = page.locator('header');
    await expect(brand).toBeVisible();
    await expect(brand).toContainText('GANTRY');
    await expect(brand).toContainText('RIG');

    // 3. Verify Nav Links
    await expect(page.getByRole('link', { name: 'PIPELINE' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'SKILLS' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'HARNESSES' })).toBeVisible();
    await expect(page.getByRole('link', { name: /GITHUB/i })).toBeVisible();

    // 4. Verify Main Hero Heading
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('Harness-Neutral');
    await expect(heading).toContainText('Agentic SDLC');

    // 5. Verify Industrial Design Theme (obsidian background and dark class)
    const html = page.locator('html');
    await expect(html).toHaveClass(/dark/);
    
    const body = page.locator('body');
    const bgColor = await body.evaluate((el) => window.getComputedStyle(el).backgroundColor);
    // rgb(10, 13, 20) corresponds to hex #0a0d14
    expect(bgColor).toBe('rgb(10, 13, 20)');

    // 6. Verify Telemetry Footer
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
    await expect(footer).toContainText('OPERATOR IN LOOP // HARNESS-NEUTRAL');
    await expect(footer).toContainText('APACHE-2.0');

    // 7. Verify No Console Errors
    expect(consoleErrors).toEqual([]);
  });
});
