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

  test('should support tab navigation between Pareceres dos Gates and Histórico Completo in modal', async ({ page }) => {
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

    const modal = page.locator('#execution-modal');
    const tabGates = page.locator('#tab-btn-gates');
    const tabHistory = page.locator('#tab-btn-history');
    const paneGates = page.locator('#tab-content-gates');
    const paneHistory = page.locator('#tab-content-history');
    const popoutBtn = page.locator('#btn-popout-history');

    const cards = page.locator('.card');
    const cardCount = await cards.count();
    if (cardCount > 0) {
      await cards.first().click();
      await expect(modal).toBeVisible();

      // 1. Gates tab active by default
      await expect(tabGates).toBeVisible();
      await expect(tabGates).toHaveClass(/active/);
      await expect(paneGates).toBeVisible();
      await expect(paneGates).not.toHaveClass(/hidden/);

      // 2. Click history tab
      await expect(tabHistory).toBeVisible();
      await tabHistory.click();
      await expect(tabHistory).toHaveClass(/active/);
      await expect(tabGates).not.toHaveClass(/active/);
      await expect(paneHistory).toBeVisible();
      await expect(paneHistory).not.toHaveClass(/hidden/);
      await expect(paneGates).toHaveClass(/hidden/);

      // 3. Verify popout button in history toolbar
      await expect(popoutBtn).toBeVisible();
      await expect(popoutBtn).toContainText('Abrir em Nova Janela');

      // 4. Switch back to gates tab
      await tabGates.click();
      await expect(tabGates).toHaveClass(/active/);
      await expect(paneGates).toBeVisible();

      await page.locator('#modal-close-btn').click();
    }
  });

  test('should render standalone history page at /history.html', async ({ page }) => {
    try {
      const response = await page.goto('http://127.0.0.1:4600/history.html', { timeout: 3000 });
      if (!response || !response.ok()) {
        test.skip(true, 'Local dashboard server is not active on port 4600');
        return;
      }
    } catch {
      test.skip(true, 'Local dashboard server is not active on port 4600');
      return;
    }

    const brandTitle = page.locator('.brand-title');
    await expect(brandTitle).toBeVisible();
    await expect(brandTitle).toContainText('GANTRY');
    await expect(brandTitle).toContainText('HISTORY');

    const container = page.locator('#history-transcript-container');
    await expect(container).toBeVisible();
  });

  test('should render frozen total cycle time badge on Done cards and phase duration breakdown in modal', async ({ page }) => {
    await page.route('**/api/state', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          columns: ['Ready', 'Plan', 'Implement', 'Review', 'Critic', 'Integrate', 'Done', 'Blocked'],
          projects: [{ unitId: 'unit-done-01', name: 'DoneProject', repositoryRoot: '/repo/done' }],
          runs: [
            {
              unitId: 'unit-done-01',
              run: 'run-done-01',
              repositoryRoot: '/repo/done',
              tier: 'supported',
              staleAfterSeconds: 900,
              lastActivityAt: '2026-09-18T12:00:00Z',
              stale: false,
              issues: [
                {
                  issue: 'done#01',
                  column: 'Done',
                  branch: 'gantry/done-01',
                  worktree: '/wt/done',
                  models: { implementer: 'model-a' },
                  completedAt: '2026-09-18T12:14:20Z',
                  totalCycleSeconds: 860,
                  elapsedPhaseSeconds: 45,
                  phaseDurations: {
                    Plan: 120,
                    Implement: 480,
                    Review: 90,
                    Critic: 110,
                    Integrate: 60,
                  },
                  operatorWaiting: false,
                  project: 'DoneProject',
                  unitId: 'unit-done-01',
                  run: 'run-done-01',
                },
              ],
            },
          ],
        }),
      });
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

    const doneCard = page.locator('.column:has(.column-title:has-text("Done")) .card');
    await expect(doneCard).toBeVisible();

    const totalBadge = doneCard.locator('.badge.total-cycle');
    await expect(totalBadge).toBeVisible();
    await expect(totalBadge).toHaveText('Total: 14m 20s');

    await doneCard.click({ force: true });
    const modal = page.locator('#execution-modal');
    await expect(modal).toBeVisible();

    const durStrip = page.locator('#modal-phase-durations');
    await expect(durStrip).toBeVisible();

    await expect(page.locator('#dur-plan')).toHaveText('2m 0s');
    await expect(page.locator('#dur-implement')).toHaveText('8m 0s');
    await expect(page.locator('#dur-review')).toHaveText('1m 30s');
    await expect(page.locator('#dur-critic')).toHaveText('1m 50s');
    await expect(page.locator('#dur-integrate')).toHaveText('1m 0s');
    await expect(page.locator('#dur-total')).toHaveText('14m 20s');

    await page.locator('#modal-close-btn').click();
    await expect(modal).toHaveClass(/hidden/);
  });

  test('should render worktree badge with word wrapping within card boundaries', async ({ page }) => {
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

    await page.waitForSelector('.card');
    const wtBadge = page.locator('.badge.worktree').first();
    await expect(wtBadge).toBeVisible();

    const card = wtBadge.locator('xpath=ancestor::div[contains(@class, "card")][1]');
    const cardBox = await card.boundingBox();
    const wtBox = await wtBadge.boundingBox();
    expect(cardBox).not.toBeNull();
    expect(wtBox).not.toBeNull();
    if (cardBox && wtBox) {
      expect(wtBox.x + wtBox.width).toBeLessThanOrEqual(cardBox.x + cardBox.width + 1);
    }

    // Save screenshot for visual verification
    await card.screenshot({ path: 'site/test-results/worktree-card.png' });
    await page.screenshot({ path: 'site/test-results/full-dashboard.png' });
  });

  test('should display shutdown button, open confirmation dialog, and transition to stopped state on confirmation', async ({ page }) => {
    let statePollCount = 0;
    let shutdownCalled = false;

    await page.route('**/api/state', async (route) => {
      statePollCount++;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          columns: ['Ready', 'Plan', 'Implement', 'Review', 'Critic', 'Integrate', 'Done', 'Blocked'],
          projects: [{ unitId: 'unit-shut-01', name: 'ShutdownProject', repositoryRoot: '/repo/shut' }],
          runs: [],
        }),
      });
    });

    await page.route('**/api/shutdown', async (route) => {
      if (route.request().method() === 'POST') {
        shutdownCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'shutting_down' }),
        });
      } else {
        await route.abort();
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

    // 1. Verify shutdown button in header controls
    const shutdownBtn = page.locator('#btn-shutdown');
    await expect(shutdownBtn).toBeVisible();
    await expect(shutdownBtn).toHaveText('SHUTDOWN');

    // 2. Click shutdown button to open modal
    const shutdownModal = page.locator('#shutdown-modal');
    await expect(shutdownModal).toHaveClass(/hidden/);
    await shutdownBtn.click();
    await expect(shutdownModal).toBeVisible();
    await expect(shutdownModal).not.toHaveClass(/hidden/);
    await expect(page.locator('#shutdown-modal-title')).toHaveText('SHUTDOWN SERVER');

    // 3. Test cancellation closes modal
    const cancelBtn = page.locator('#shutdown-cancel-btn');
    await cancelBtn.click();
    await expect(shutdownModal).toHaveClass(/hidden/);
    expect(shutdownCalled).toBe(false);

    // 4. Reopen and confirm shutdown
    await shutdownBtn.click();
    await expect(shutdownModal).toBeVisible();

    const initialPollCount = statePollCount;
    const confirmBtn = page.locator('#shutdown-confirm-btn');
    await confirmBtn.click();

    // 5. Verify shutdown POST was dispatched
    expect(shutdownCalled).toBe(true);
    await expect(shutdownModal).toHaveClass(/hidden/);

    // 6. Verify SERVER STOPPED overlay is visible
    const stoppedOverlay = page.locator('#server-stopped-overlay');
    await expect(stoppedOverlay).toBeVisible();
    await expect(page.locator('.stopped-heading')).toHaveText('SERVER STOPPED');
    await expect(page.locator('.stopped-subtext')).toContainText('DISCONNECTED');

    // 7. Verify polling stopped: wait 1500ms and verify poll count did not increase
    await page.waitForTimeout(1500);
    expect(statePollCount).toBeLessThanOrEqual(initialPollCount + 1);

    // Visual screenshot verification
    await page.screenshot({ path: 'site/test-results/server-stopped.png' });
  });
});

