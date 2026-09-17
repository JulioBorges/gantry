import { test, expect } from '@playwright/test';

test.describe('Pipeline Simulator Island (gantry-site#03)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/gantry/');
  });

  test('displays all six core pipeline stages with active, completed, and pending visual indicators', async ({ page }) => {
    const simulator = page.getByTestId('pipeline-simulator');
    await expect(simulator).toBeVisible();

    const stageIds = ['spec', 'plan', 'implement', 'review', 'critic', 'gate'];

    // All 6 tabs must exist
    for (const id of stageIds) {
      const tab = page.getByTestId(`stage-tab-${id}`);
      await expect(tab).toBeVisible();
    }

    // Default: Stage 01 (spec) is active
    const specTab = page.getByTestId('stage-tab-spec');
    await expect(specTab).toHaveAttribute('data-active', 'true');
    await expect(specTab).toHaveAttribute('data-status', 'active');
    await expect(specTab).toContainText('ACTIVE');

    // Stage 02 (plan) is pending
    const planTab = page.getByTestId('stage-tab-plan');
    await expect(planTab).toHaveAttribute('data-active', 'false');
    await expect(planTab).toHaveAttribute('data-status', 'pending');
    await expect(planTab).toContainText('PENDING');

    // When advancing to Stage 03 (implement), previous stages become completed (verified)
    const nextBtn = page.getByTestId('next-stage-btn');
    await nextBtn.click(); // to stage 02 (plan)
    await nextBtn.click(); // to stage 03 (implement)

    const implementTab = page.getByTestId('stage-tab-implement');
    await expect(implementTab).toHaveAttribute('data-active', 'true');
    await expect(implementTab).toHaveAttribute('data-status', 'active');

    // Stage 01 and 02 must now have completed status
    await expect(specTab).toHaveAttribute('data-status', 'completed');
    await expect(specTab).toContainText('VERIFIED');
    await expect(planTab).toHaveAttribute('data-status', 'completed');
    await expect(planTab).toContainText('VERIFIED');
  });

  test('selecting a stage dynamically updates description, invariants, agent role, and terminal log stream', async ({ page }) => {
    const simulator = page.getByTestId('pipeline-simulator');
    await expect(simulator).toBeVisible();

    // Select Stage 05 (Adversarial Critic) directly
    const criticTab = page.getByTestId('stage-tab-critic');
    await criticTab.click();
    await expect(criticTab).toHaveAttribute('data-active', 'true');

    // Check header updates
    await expect(simulator).toContainText('Adversarial Critic');
    await expect(simulator).toContainText('Fresh independent agent verification');

    // Check script invariants update
    await expect(simulator).toContainText('DETERMINISTIC SCRIPT INVARIANTS');
    await expect(simulator).toContainText('runlog.py inflight');
    await expect(simulator).toContainText('Fresh subagent instance with zero shared memory');

    // Check agent role updates
    await expect(simulator).toContainText('AGENT ROLE: ADVERSARIAL CRITIC');
    await expect(simulator).toContainText('ADVERSARIAL');
    await expect(simulator).toContainText('Critic Model (Adversarial)');

    // Check terminal output updates
    const terminal = page.getByTestId('terminal-stream');
    await expect(terminal).toContainText('critic-verify --issue gantry-site#02');
    await expect(terminal).toContainText('Critic Verdict: ACCEPTED');

    // Check JSON Event Log updates
    const jsonLog = page.getByTestId('json-event-log');
    await expect(jsonLog).toContainText('"role": "critic"');
    await expect(jsonLog).toContainText('"verdict": "ACCEPTED"');

    // Switch to Stage 06 (Serial Integration Gate)
    const gateTab = page.getByTestId('stage-tab-gate');
    await gateTab.click();
    await expect(gateTab).toHaveAttribute('data-active', 'true');
    await expect(simulator).toContainText('Serial Integration Gate');
    await expect(simulator).toContainText('gates.py && roadmap.py done');
    await expect(terminal).toContainText('roadmap.py done gantry-site#02');
    await expect(jsonLog).toContainText('"event": "issue.done"');
  });

  test('terminal view provides realistic syntax-highlighted commands, checks, and JSON log events', async ({ page }) => {
    // Check initial stage (Spec) terminal display
    const terminal = page.getByTestId('terminal-stream');
    await expect(terminal).toBeVisible();
    await expect(terminal).toContainText('spec.py --check');
    await expect(terminal).toContainText('Structure verified: 0 schema violations');
    await expect(terminal).toContainText('Requirement Critic: ambiguity index 0.02 [CLEAN]');

    const jsonLog = page.getByTestId('json-event-log');
    await expect(jsonLog).toBeVisible();
    await expect(jsonLog).toContainText('"event": "spec.verified"');
    await expect(jsonLog).toContainText('"spec": "gantry-site"');
  });

  test('stepper navigation buttons advance and retreat stages correctly', async ({ page }) => {
    const prevBtn = page.getByTestId('prev-stage-btn');
    const nextBtn = page.getByTestId('next-stage-btn');

    // Initially at stage 0, prev is disabled
    await expect(prevBtn).toBeDisabled();
    await expect(nextBtn).toBeEnabled();

    // Advance to stage 1
    await nextBtn.click();
    await expect(prevBtn).toBeEnabled();
    const planTab = page.getByTestId('stage-tab-plan');
    await expect(planTab).toHaveAttribute('data-active', 'true');

    // Click Prev button to return to stage 0
    await prevBtn.click();
    await expect(prevBtn).toBeDisabled();
    const specTab = page.getByTestId('stage-tab-spec');
    await expect(specTab).toHaveAttribute('data-active', 'true');

    // Step all the way to stage 5 (Gate)
    for (let i = 0; i < 5; i++) {
      await nextBtn.click();
    }
    const gateTab = page.getByTestId('stage-tab-gate');
    await expect(gateTab).toHaveAttribute('data-active', 'true');
    // At last stage, next button is disabled
    await expect(nextBtn).toBeDisabled();
  });

  test('keyboard arrow navigation advances and retreats stages', async ({ page }) => {
    const specTab = page.getByTestId('stage-tab-spec');
    await expect(specTab).toHaveAttribute('data-active', 'true');
    await specTab.focus();

    // Press ArrowRight to move to next stage
    await page.keyboard.press('ArrowRight');
    const planTab = page.getByTestId('stage-tab-plan');
    await expect(planTab).toHaveAttribute('data-active', 'true');

    // Press ArrowRight again
    await page.keyboard.press('ArrowRight');
    const implementTab = page.getByTestId('stage-tab-implement');
    await expect(implementTab).toHaveAttribute('data-active', 'true');

    // Press ArrowLeft to retreat
    await page.keyboard.press('ArrowLeft');
    await expect(planTab).toHaveAttribute('data-active', 'true');
  });

  test('simulator layout is responsive on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/gantry/');

    const simulator = page.getByTestId('pipeline-simulator');
    await expect(simulator).toBeVisible();

    const specTab = page.getByTestId('stage-tab-spec');
    await expect(specTab).toBeVisible();

    const terminal = page.getByTestId('terminal-stream');
    await expect(terminal).toBeVisible();

    const nextBtn = page.getByTestId('next-stage-btn');
    await expect(nextBtn).toBeVisible();
    await nextBtn.click();

    const planTab = page.getByTestId('stage-tab-plan');
    await expect(planTab).toHaveAttribute('data-active', 'true');
  });
});
