import { test, expect } from '@playwright/test';

test.describe('Hero Section & Multi-Harness Install Widget (gantry-site#02)', () => {
  test.beforeEach(async ({ page, context }) => {
    // Grant clipboard permissions for testing copy interactions
    try {
      await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    } catch {
      // Some browsers / environments might not support permissions grant
    }
    await page.goto('/gantry/');
  });

  test('hero displays primary tagline, value proposition, status badges, and crane visual motif', async ({ page }) => {
    // 1. Verify Hero Section visibility
    const heroSection = page.getByTestId('hero-section');
    await expect(heroSection).toBeVisible();

    // 2. Verify Primary Tagline
    const tagline = page.getByTestId('hero-tagline');
    await expect(tagline).toBeVisible();
    await expect(tagline).toHaveText(
      'Turn an approved Spec into verified software deliveries inside your coding harness.'
    );

    // 3. Verify Value Proposition
    const valueProp = page.getByTestId('hero-value-prop');
    await expect(valueProp).toBeVisible();
    await expect(valueProp).toContainText('Gantry is a skill pack, not an execution engine');
    await expect(valueProp).toContainText('operator holds approval authority');

    // 4. Verify Status Badges
    const badges = page.getByTestId('status-badges');
    await expect(badges).toBeVisible();
    await expect(badges).toContainText('STATUS: SPEC-VERIFIED');
    await expect(badges).toContainText('HARNESS-NEUTRAL');
    await expect(badges).toContainText('APACHE-2.0');
    await expect(badges).toContainText('ZERO AI-SLOP');

    // 5. Verify Crane Visual Motif
    const craneRig = page.getByTestId('crane-visual-rig');
    await expect(craneRig).toBeVisible();
    const craneImg = craneRig.locator('img');
    await expect(craneImg).toBeVisible();
    await expect(craneImg).toHaveAttribute('src', /\/gantry\.png/);
    await expect(craneRig).toContainText('GANTRY CRANE // RIG MK-IV');
  });

  test('quick install widget provides switchable tabs for supported harnesses with accurate CLI commands', async ({ page }) => {
    const widget = page.getByTestId('install-widget');
    await expect(widget).toBeVisible();

    // Default tab: Claude Code
    const claudeTab = page.getByTestId('tab-claude');
    await expect(claudeTab).toHaveAttribute('aria-selected', 'true');
    const command = page.getByTestId('install-command');
    await expect(command).toHaveText('npx skills add JulioBorges/gantry');
    await expect(widget).toContainText('TIER: REFERENCE');

    // Switch to OpenCode
    const opencodeTab = page.getByTestId('tab-opencode');
    await opencodeTab.click();
    await expect(opencodeTab).toHaveAttribute('aria-selected', 'true');
    await expect(claudeTab).toHaveAttribute('aria-selected', 'false');
    await expect(command).toHaveText('npx skills add JulioBorges/gantry');
    await expect(widget).toContainText('TIER: COMPATIBLE');
    await expect(widget).toContainText('opencode');

    // Switch to Codex
    const codexTab = page.getByTestId('tab-codex');
    await codexTab.click();
    await expect(codexTab).toHaveAttribute('aria-selected', 'true');
    await expect(widget).toContainText('TIER: SUPPORTED');
    await expect(widget).toContainText('codex');

    // Switch to Gemini / Antigravity
    const agyTab = page.getByTestId('tab-antigravity');
    await agyTab.click();
    await expect(agyTab).toHaveAttribute('aria-selected', 'true');
    await expect(widget).toContainText('TIER: SUPPORTED');
    await expect(widget).toContainText('antigravity');

    // Switch to Cursor
    const cursorTab = page.getByTestId('tab-cursor');
    await cursorTab.click();
    await expect(cursorTab).toHaveAttribute('aria-selected', 'true');
    await expect(widget).toContainText('TIER: COMPATIBLE');
    await expect(widget).toContainText('cursor');
  });

  test('copy button copies command and shows visual copy confirmation', async ({ page }) => {
    const copyBtn = page.getByTestId('copy-btn');
    await expect(copyBtn).toBeVisible();
    await expect(copyBtn).toContainText('COPY');

    // Click copy button
    await copyBtn.click();

    // Verify visual confirmation
    await expect(copyBtn).toContainText('COPIED!');
  });

  test('hero section is responsive on mobile viewport', async ({ page }) => {
    // Set viewport to standard mobile width (iPhone SE / 375px)
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/gantry/');

    const heroSection = page.getByTestId('hero-section');
    await expect(heroSection).toBeVisible();

    const craneRig = page.getByTestId('crane-visual-rig');
    await expect(craneRig).toBeVisible();

    const widget = page.getByTestId('install-widget');
    await expect(widget).toBeVisible();

    const copyBtn = page.getByTestId('copy-btn');
    await expect(copyBtn).toBeVisible();
    await copyBtn.click();
    await expect(copyBtn).toContainText('COPIED!');
  });
});
