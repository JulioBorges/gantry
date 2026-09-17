import { test, expect } from '@playwright/test';

test.describe('Narrative & Capability Sections (gantry-site#04)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/gantry/');
  });

  test.describe('Problem vs Solution Section', () => {
    test('renders problem vs solution section with correct heading hierarchy and core thesis', async ({ page }) => {
      const section = page.getByTestId('problem-solution-section');
      await expect(section).toBeVisible();

      // Heading hierarchy check: section has an h2
      const heading = section.locator('h2');
      await expect(heading).toBeVisible();
      await expect(heading).toContainText(/Why Raw Agents Fail/i);

      // Core thesis banner
      const thesis = section.getByTestId('core-thesis-banner');
      await expect(thesis).toBeVisible();
      await expect(thesis).toContainText('Agents + code > agents alone');
      await expect(thesis).toContainText('ADR-0004');
    });

    test('renders structured comparison cards contrasting failure modes with Gantry principles', async ({ page }) => {
      const section = page.getByTestId('problem-solution-section');

      // Card 1: Context degradation
      const contextCard = section.getByTestId('problem-card-context');
      await expect(contextCard).toBeVisible();
      await expect(contextCard).toContainText(/Context Degradation/i);
      await expect(contextCard).toContainText(/Bounded Context/i);
      await expect(contextCard).toContainText(/budget\.py/i);

      // Card 2: Mock escapes & test tampering
      const mocksCard = section.getByTestId('problem-card-mocks');
      await expect(mocksCard).toBeVisible();
      await expect(mocksCard).toContainText(/Mock Escapes/i);
      await expect(mocksCard).toContainText(/Adversarial Verification/i);

      // Card 3: Unearned self-approval
      const approvalCard = section.getByTestId('problem-card-approval');
      await expect(approvalCard).toBeVisible();
      await expect(approvalCard).toContainText(/Self-Approval/i);
      await expect(approvalCard).toContainText(/Zero Self-Approval/i);
      await expect(approvalCard).toContainText(/Critic/i);

      // Card 4: Integration drift & broken branches
      const driftCard = section.getByTestId('problem-card-drift');
      await expect(driftCard).toBeVisible();
      await expect(driftCard).toContainText(/Integration/i);
      await expect(driftCard).toContainText(/gates\.py/i);
      await expect(driftCard).toContainText(/frontier\.py/i);
    });
  });

  test.describe('Three Skills Pack Section', () => {
    test('renders skills pack section with heading, telemetry badge, and three delineated skills', async ({ page }) => {
      const section = page.getByTestId('skills-section');
      await expect(section).toBeVisible();

      const heading = section.locator('h2');
      await expect(heading).toBeVisible();
      await expect(heading).toContainText(/The Three Skills/i);

      // Skill 1: gantry
      const gantryCard = section.getByTestId('skill-card-gantry');
      await expect(gantryCard).toBeVisible();
      await expect(gantryCard).toContainText('gantry');
      await expect(gantryCard).toContainText(/Core Workflow/i);
      await expect(gantryCard).toContainText(/TDD/i);
      await expect(gantryCard).toContainText(/Adversarial Critic/i);

      // Skill 2: gantry-setup
      const setupCard = section.getByTestId('skill-card-gantry-setup');
      await expect(setupCard).toBeVisible();
      await expect(setupCard).toContainText('gantry-setup');
      await expect(setupCard).toContainText(/Policy & Governance/i);
      await expect(setupCard).toContainText(/\.gantry\/config\.json/);
      await expect(setupCard).toContainText(/AGENTS\.md/);

      // Skill 3: gantry-dashboard
      const dashCard = section.getByTestId('skill-card-gantry-dashboard');
      await expect(dashCard).toBeVisible();
      await expect(dashCard).toContainText('gantry-dashboard');
      await expect(dashCard).toContainText(/Observability/i);
      await expect(dashCard).toContainText(/localhost:42687/);
      await expect(dashCard).toContainText(/Read-only/i);
    });

    test('validates link integrity across skill cards', async ({ page }) => {
      const section = page.getByTestId('skills-section');
      const links = section.locator('a');
      const count = await links.count();
      expect(count).toBeGreaterThanOrEqual(3);

      for (let i = 0; i < count; i++) {
        const link = links.nth(i);
        const href = await link.getAttribute('href');
        expect(href).toBeTruthy();
        expect(href).not.toBe('#');
      }
    });
  });

  test.describe('Harness Compatibility Matrix Section', () => {
    test('renders tier definitions and honest capabilities without fabricated claims', async ({ page }) => {
      const section = page.getByTestId('harness-matrix-section');
      await expect(section).toBeVisible();

      const heading = section.locator('h2');
      await expect(heading).toBeVisible();
      await expect(heading).toContainText(/Harness Compatibility/i);

      // Tier definitions container
      const tierDefs = section.getByTestId('tier-definitions');
      await expect(tierDefs).toBeVisible();
      await expect(tierDefs).toContainText('REFERENCE');
      await expect(tierDefs).toContainText('SUPPORTED');
      await expect(tierDefs).toContainText('COMPATIBLE');

      // Table check
      const table = section.getByTestId('harness-matrix-table');
      await expect(table).toBeVisible();

      // Verify specific rows and honest tier claims
      const rows = table.locator('tbody tr');
      await expect(rows).toHaveCount(5);

      // Claude Code
      const claudeRow = table.locator('tr', { hasText: 'Claude Code' });
      await expect(claudeRow).toContainText(/Reference/i);
      await expect(claudeRow).toContainText(/fixture/i);

      // Gemini / Antigravity
      const agyRow = table.locator('tr', { hasText: 'Antigravity' });
      await expect(agyRow).toContainText(/Supported/i);

      // Codex CLI
      const codexRow = table.locator('tr', { hasText: 'Codex' });
      await expect(codexRow).toContainText(/Supported/i);

      // OpenCode
      const opencodeRow = table.locator('tr', { hasText: 'OpenCode' });
      await expect(opencodeRow).toContainText(/Compatible/i);

      // Cursor
      const cursorRow = table.locator('tr', { hasText: 'Cursor' });
      await expect(cursorRow).toContainText(/Compatible/i);

      // Honest disclaimer callout
      const disclaimer = section.getByTestId('honest-disclaimer-callout');
      await expect(disclaimer).toBeVisible();
      await expect(disclaimer).toContainText(/A declared tier does not prove every harness version has been exercised/i);
      await expect(disclaimer).toContainText('PRD §13');
    });
  });

  test.describe('Responsive Grid & Viewport Verification', () => {
    test('sections adapt to mobile viewport without horizontal overflow', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/gantry/');

      const problemSection = page.getByTestId('problem-solution-section');
      await expect(problemSection).toBeVisible();

      const skillsSection = page.getByTestId('skills-section');
      await expect(skillsSection).toBeVisible();

      const matrixSection = page.getByTestId('harness-matrix-section');
      await expect(matrixSection).toBeVisible();

      // Verify the three narrative sections fit within the viewport width without overflowing
      const sectionFits = await page.evaluate(() => {
        const docWidth = window.innerWidth;
        const testIds = ['problem-solution-section', 'skills-section', 'harness-matrix-section'];
        const results = [];
        for (const tid of testIds) {
          const el = document.querySelector(`[data-testid="${tid}"]`);
          if (el) {
            const rect = el.getBoundingClientRect();
            results.push({
              testId: tid,
              fits: rect.width <= docWidth + 2,
              rectWidth: rect.width,
              docWidth,
            });
          }
        }
        return results;
      });

      for (const result of sectionFits) {
        expect(result.fits).toBe(true);
      }

      // Verify page body does not scroll horizontally
      const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth <= window.innerWidth + 2);
      expect(bodyScrollWidth).toBe(true);
    });
  });
});
