import { test, expect } from '@playwright/test';

test.describe('Bilingual i18n Support & Language Toggle (gantry-site#05)', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test to ensure default language state
    await page.goto('/gantry/');
    await page.evaluate(() => localStorage.removeItem('gantry_locale'));
    await page.reload();
  });

  test('header contains language toggle with EN active by default', async ({ page }) => {
    const toggle = page.getByTestId('language-toggle');
    await expect(toggle).toBeVisible();

    const enBtn = page.getByTestId('lang-btn-en');
    const ptBtn = page.getByTestId('lang-btn-pt');

    await expect(enBtn).toBeVisible();
    await expect(ptBtn).toBeVisible();
    await expect(enBtn).toHaveAttribute('data-active', 'true');
    await expect(ptBtn).toHaveAttribute('data-active', 'false');

    // Document lang attribute
    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('en');
  });

  test('toggling to PT-BR translates hero, problem/solution, skills, simulator, and matrix without full reload', async ({ page }) => {
    const ptBtn = page.getByTestId('lang-btn-pt');
    await ptBtn.click();

    // Check active state on buttons
    const enBtn = page.getByTestId('lang-btn-en');
    await expect(ptBtn).toHaveAttribute('data-active', 'true');
    await expect(enBtn).toHaveAttribute('data-active', 'false');

    // Verify html lang updated
    await expect(page.locator('html')).toHaveAttribute('lang', 'pt-br');

    // 1. Hero Section translated
    const heroTagline = page.getByTestId('hero-tagline');
    await expect(heroTagline).toContainText('Transforme uma Spec aprovada');

    const heroValueProp = page.getByTestId('hero-value-prop');
    await expect(heroValueProp).toContainText('O Gantry é um pacote de skills, não um motor de execução');

    // 2. Install Widget translated
    const installWidget = page.getByTestId('install-widget');
    await expect(installWidget).toContainText('INSTALAÇÃO RÁPIDA');

    // 3. Problem vs Solution translated
    const problemSection = page.getByTestId('problem-solution-section');
    await expect(problemSection).toContainText('Por que Agentes Puros Falham — E Como o Gantry Resolve');
    await expect(problemSection).toContainText('Agentes + código > apenas agentes');

    // 4. Pipeline Simulator translated
    const simulator = page.getByTestId('pipeline-simulator');
    await expect(simulator).toContainText('SIMULADOR DE PIPELINE');
    await expect(simulator).toContainText('PROGRESSO:');
    const specTab = page.getByTestId('stage-tab-spec');
    await expect(specTab).toContainText('Spec & Crítico de Requisitos');

    // 5. Skills Section translated
    const skillsSection = page.getByTestId('skills-section');
    await expect(skillsSection).toContainText('As Três Skills');
    await expect(skillsSection).toContainText('PACOTE: 1 ROBUSTO // 2 LEVES');

    // 6. Harness Matrix translated
    const matrixSection = page.getByTestId('harness-matrix-section');
    await expect(matrixSection).toContainText('Matriz de Compatibilidade de Harnesses');
    await expect(matrixSection).toContainText('TIER REFERÊNCIA');
  });

  test('user language selection persists across page reload via localStorage', async ({ page }) => {
    // Switch to Portuguese
    const ptBtn = page.getByTestId('lang-btn-pt');
    await ptBtn.click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'pt-br');

    // Verify localStorage has pt-br
    const storedLocale = await page.evaluate(() => localStorage.getItem('gantry_locale'));
    expect(storedLocale).toBe('pt-br');

    // Reload page
    await page.reload();

    // Verify state persisted
    await expect(page.locator('html')).toHaveAttribute('lang', 'pt-br');
    const ptBtnAfterReload = page.getByTestId('lang-btn-pt');
    await expect(ptBtnAfterReload).toHaveAttribute('data-active', 'true');

    const heroTagline = page.getByTestId('hero-tagline');
    await expect(heroTagline).toContainText('Transforme uma Spec aprovada');

    // Switch back to English
    const enBtn = page.getByTestId('lang-btn-en');
    await enBtn.click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await expect(enBtn).toHaveAttribute('data-active', 'true');

    const storedLocaleEn = await page.evaluate(() => localStorage.getItem('gantry_locale'));
    expect(storedLocaleEn).toBe('en');

    await expect(heroTagline).toContainText('Turn an approved Spec into verified software deliveries');
  });

  test('toggling language retains layout stability and mobile responsiveness', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/gantry/');

    // Toggle to Portuguese
    const ptBtn = page.getByTestId('lang-btn-pt');
    await ptBtn.click();

    // Verify all primary sections remain visible and fit viewport
    await expect(page.getByTestId('hero-section')).toBeVisible();
    await expect(page.getByTestId('pipeline-simulator')).toBeVisible();
    await expect(page.getByTestId('problem-solution-section')).toBeVisible();
    await expect(page.getByTestId('skills-section')).toBeVisible();
    await expect(page.getByTestId('harness-matrix-section')).toBeVisible();

    // Verify no horizontal overflow in body
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 2); // 2px margin of error for subpixel rendering
  });
});
