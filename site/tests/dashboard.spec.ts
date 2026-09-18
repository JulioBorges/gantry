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

  test('should display project selector defaulting to ALL and filter unified kanban board', async ({ page }) => {
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

    // 1. Verify Project selector exists and defaults to ALL
    const projectSelect = page.locator('#project-select');
    await expect(projectSelect).toBeVisible();
    await expect(projectSelect).toHaveValue('ALL');

    // 2. Wait for columns to appear
    await page.waitForSelector('.swimlane', { timeout: 3000 });
    const columns = page.locator('.column');
    await expect(columns).toHaveCount(8);

    // 3. Verify options contain ALL
    const options = await projectSelect.locator('option').allInnerTexts();
    expect(options).toContain('ALL');

    // 4. Verify cards have project badges and test filtering if cards exist
    const cards = page.locator('.card');
    const cardCount = await cards.count();
    if (cardCount > 0) {
      const firstCardBadge = cards.first().locator('.badge.project');
      await expect(firstCardBadge).toBeVisible();

      // If multiple options exist, test filtering
      const projectOptions = await projectSelect.locator('option').all();
      if (projectOptions.length > 1) {
        const targetValue = await projectOptions[1].getAttribute('value');
        if (targetValue && targetValue !== 'ALL') {
          await projectSelect.selectOption(targetValue);
          await expect(page.locator('.column')).toHaveCount(8);

          const filteredCards = page.locator('.card');
          const filteredCount = await filteredCards.count();
          for (let i = 0; i < filteredCount; i++) {
            await expect(filteredCards.nth(i)).toHaveAttribute('data-unit-id', targetValue);
          }

          // Switch back to ALL
          await projectSelect.selectOption('ALL');
          await expect(page.locator('.column')).toHaveCount(8);
          await expect(page.locator('.card')).toHaveCount(cardCount);
        }
      }
    }
  });

  test('should open execution modal on card click, render live activity badges and toggle thinking block', async ({ page }) => {
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

    // Ensure modal element exists in DOM
    const modal = page.locator('#execution-modal');
    await expect(modal).toHaveCount(1);
    await expect(modal).toHaveClass(/hidden/);

    const cards = page.locator('.card');
    const cardCount = await cards.count();
    if (cardCount > 0) {
      const firstCard = cards.first();
      // Click first card to open modal
      await firstCard.click();
      await expect(modal).toBeVisible();
      await expect(modal).not.toHaveClass(/hidden/);

      // Verify modal header and metadata
      const modalTitle = page.locator('#modal-issue-title');
      await expect(modalTitle).toBeVisible();
      await expect(modalTitle).toContainText('ISSUE:');

      // Check if thinking blocks exist in transcript, test toggle
      const thinkingHeader = page.locator('.thinking-header').first();
      if (await thinkingHeader.count() > 0) {
        await expect(thinkingHeader).toBeVisible();
        const thinkingContent = page.locator('.thinking-content').first();
        await expect(thinkingContent).toHaveClass(/collapsed/);

        // Click to expand
        await thinkingHeader.click();
        await expect(thinkingContent).not.toHaveClass(/collapsed/);

        // Click to collapse
        await thinkingHeader.click();
        await expect(thinkingContent).toHaveClass(/collapsed/);
      }

      // Close modal using close button
      const closeBtn = page.locator('#modal-close-btn');
      await closeBtn.click();
      await expect(modal).toHaveClass(/hidden/);
    }
  });
});
