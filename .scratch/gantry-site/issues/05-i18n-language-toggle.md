# Implement bilingual i18n support with language toggle

Type: issue
Status: ready-for-agent
Slice: `gantry-site#05`
Spec: `.scratch/gantry-site/spec.md`
Created: 2026-09-17

## Parent

`gantry-site`

## What to build

Implement seamless internationalization between English (default) and Portuguese (PT-BR). Provide a lightweight language toggle in the header navigation that updates the active locale across the hero, problem/solution, interactive simulator, skills pack, and harness matrix without a full page reload, persisting user selection in local storage.

### Files to read

- `.scratch/gantry-site/spec.md`
- `.scratch/gantry-site/issues/03-interactive-pipeline-simulator.md`
- `.scratch/gantry-site/issues/04-problem-solution-skills-and-harness-matrix.md`
- `README.md`

## Acceptance criteria

- [ ] Language toggle component switches seamlessly between English (`en`) and Portuguese (`pt-br`).
- [ ] Complete translation dictionary covers all text nodes, section headings, simulator stages, terminal logs, and badges.
- [ ] User language choice is remembered across page reloads via localStorage without hydration mismatch.
- [ ] Playwright test verifies that toggling language changes all primary text content and retains layout stability.

## Blocked by

- gantry-site#02
- gantry-site#03
- gantry-site#04

## Comments

Approved vertical slice breakdown.
