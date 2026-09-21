import { test, expect } from '@playwright/test';

test.describe('Gantry workflow simulator', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/gantry/');
  });

  test('shows the six-step skill-first workflow with active, completed, and pending states', async ({ page }) => {
    const simulator = page.getByTestId('pipeline-simulator');
    await expect(simulator).toBeVisible();

    const stageIds = ['setup', 'plan', 'approve', 'implement', 'verify', 'handoff'];
    for (const id of stageIds) {
      await expect(page.getByTestId(`stage-tab-${id}`)).toBeVisible();
    }

    const setupTab = page.getByTestId('stage-tab-setup');
    const planTab = page.getByTestId('stage-tab-plan');
    await expect(setupTab).toHaveAttribute('data-status', 'active');
    await expect(setupTab).toContainText('ACTIVE');
    await expect(planTab).toHaveAttribute('data-status', 'pending');

    const nextBtn = page.getByTestId('next-stage-btn');
    await nextBtn.click();
    await nextBtn.click();
    await nextBtn.click();

    await expect(page.getByTestId('stage-tab-implement')).toHaveAttribute('data-status', 'active');
    await expect(setupTab).toHaveAttribute('data-status', 'completed');
    await expect(planTab).toHaveAttribute('data-status', 'completed');
  });

  test('presents slash commands for setup, planning, execution, and dashboard', async ({ page }) => {
    const terminal = page.getByTestId('terminal-stream');

    await expect(terminal).toContainText('/gantry-setup');

    await page.getByTestId('stage-tab-plan').click();
    await expect(terminal).toContainText('/gantry-plan Add login via OTP');

    await page.getByTestId('stage-tab-implement').click();
    await expect(terminal).toContainText('/gantry Implement the login-otp Spec');

    await page.getByTestId('stage-tab-handoff').click();
    await expect(terminal).toContainText('/gantry-dashboard');
    await expect(terminal).not.toContainText('python3 .agents/skills/gantry/scripts/');
  });

  test('makes approval explicit and the post-gantry phases automatic', async ({ page }) => {
    const simulator = page.getByTestId('pipeline-simulator');
    const terminal = page.getByTestId('terminal-stream');
    const jsonLog = page.getByTestId('json-event-log');

    await page.getByTestId('stage-tab-approve').click();
    await expect(simulator).toContainText('Approve Spec & Issues');
    await expect(terminal).toContainText('I approve the login-otp Spec and proposed Issues');
    await expect(jsonLog).toContainText('"event": "plan.approved"');

    await page.getByTestId('stage-tab-verify').click();
    await expect(simulator).toContainText('Automatic Review & Critic');
    await expect(simulator).toContainText('/gantry continues automatically');
    await expect(terminal).toContainText('No additional command required');
    await expect(terminal).toContainText('Critic Verdict: ACCEPTED');

    await page.getByTestId('stage-tab-handoff').click();
    await expect(simulator).toContainText('Gates, Integration & Handoff');
    await expect(terminal).toContainText('Deterministic gates passed');
    await expect(jsonLog).toContainText('"event": "run.finished"');
  });

  test('initial setup explains that it runs once per repository', async ({ page }) => {
    const terminal = page.getByTestId('terminal-stream');
    await expect(terminal).toContainText('Run once per repository');
    await expect(terminal).toContainText('Repository adapted to Gantry');
    await expect(page.getByTestId('json-event-log')).toContainText('"event": "setup.completed"');
  });

  test('stepper navigation advances and retreats stages correctly', async ({ page }) => {
    const prevBtn = page.getByTestId('prev-stage-btn');
    const nextBtn = page.getByTestId('next-stage-btn');

    await expect(prevBtn).toBeDisabled();
    await nextBtn.click();
    await expect(page.getByTestId('stage-tab-plan')).toHaveAttribute('data-active', 'true');
    await prevBtn.click();
    await expect(page.getByTestId('stage-tab-setup')).toHaveAttribute('data-active', 'true');

    for (let i = 0; i < 5; i++) await nextBtn.click();
    await expect(page.getByTestId('stage-tab-handoff')).toHaveAttribute('data-active', 'true');
    await expect(nextBtn).toBeDisabled();
  });

  test('keyboard and mobile navigation remain usable', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/gantry/');

    const setupTab = page.getByTestId('stage-tab-setup');
    await setupTab.focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.getByTestId('stage-tab-plan')).toHaveAttribute('data-active', 'true');
    await page.keyboard.press('ArrowRight');
    await expect(page.getByTestId('stage-tab-approve')).toHaveAttribute('data-active', 'true');
    await page.keyboard.press('ArrowLeft');
    await expect(page.getByTestId('stage-tab-plan')).toHaveAttribute('data-active', 'true');
    await expect(page.getByTestId('terminal-stream')).toBeVisible();
  });
});
