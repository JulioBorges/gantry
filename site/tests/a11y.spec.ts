import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility (a11y) Verification Suite', () => {
  test('should pass automated a11y audit on initial load (English)', async ({ page }) => {
    await page.goto('/gantry/');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should pass automated a11y audit in Portuguese (PT-BR)', async ({ page }) => {
    await page.goto('/gantry/');
    const ptBtn = page.getByTestId('lang-btn-pt');
    await ptBtn.click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'pt-br');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should pass automated a11y audit across simulator stages', async ({ page }) => {
    await page.goto('/gantry/');
    const stageIds = ['spec', 'plan', 'implement', 'review', 'critic', 'gate'];

    for (const id of stageIds) {
      const tab = page.getByTestId(`stage-tab-${id}`);
      await tab.click();
      await expect(tab).toHaveAttribute('data-active', 'true');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('[data-testid="pipeline-simulator"]')
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    }
  });

  test('should pass automated a11y audit across install widget tabs', async ({ page }) => {
    await page.goto('/gantry/');
    const tabs = ['claude', 'opencode', 'codex', 'antigravity', 'cursor'];

    for (const harness of tabs) {
      const tab = page.getByTestId(`tab-${harness}`);
      await tab.click();
      await expect(tab).toHaveAttribute('aria-selected', 'true');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('[data-testid="install-widget"]')
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    }
  });
});
