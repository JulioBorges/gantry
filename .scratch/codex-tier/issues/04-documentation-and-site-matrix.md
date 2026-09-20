# Update PRD, README, documentation, and Astro site harness matrix for Codex

Type: issue
Status: ready
Slice: `codex-tier#04`
Spec: `.scratch/codex-tier/spec.md`
Created: 2026-09-20

## Parent

`codex-tier`

## What to build

Harmonize all user-facing documentation, product specifications, and website showcase components to reflect Codex in the Supported Tier. Update `PRD.md`, `README.md`, and `docs/role-execution.md` to document the hybrid process runner and independent Critic verification. Update the Astro website component (`site/src/components/HarnessMatrix.astro`), its English and Portuguese translations in `translations.ts`, and run Playwright tests to ensure accessibility and visual presentation.

### Files to read

- `PRD.md`
- `README.md`
- `docs/role-execution.md`
- `site/src/components/HarnessMatrix.astro`
- `site/src/i18n/translations.ts`
- `site/tests/narrative.spec.ts`

## Acceptance criteria

- [ ] `PRD.md` updates the harness matrix to declare Codex under Supported Tier with hybrid runner and Critic verification.
- [ ] `README.md` and `docs/role-execution.md` describe Codex installation commands, setup options, and supported capabilities.
- [ ] `site/src/components/HarnessMatrix.astro` and `site/src/i18n/translations.ts` present synchronized Supported status in EN and PT-BR.
- [ ] Automated Playwright tests (`site/tests/narrative.spec.ts`, `site/tests/hero.spec.ts`, `site/tests/a11y.spec.ts`) pass cleanly.

## Blocked by

- `codex-tier#03`
