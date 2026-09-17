# Configure GitHub Pages deployment workflow and complete E2E validation

Type: issue
Status: done
Slice: `gantry-site#06`
Spec: `.scratch/gantry-site/spec.md`
Created: 2026-09-17

## Parent

`gantry-site`

## What to build

Create the GitHub Actions workflow `.github/workflows/deploy-pages.yml` to build the Astro site and deploy to GitHub Pages via `actions/deploy-pages` whenever changes to `main` affect `site/**`. Wire repository and site test commands, verify production asset hashing and bundle sizes, and run the complete Playwright E2E suite covering all scenarios, viewports, and accessibility checks.

### Files to read

- `.scratch/gantry-site/spec.md`
- `.scratch/gantry-site/issues/05-i18n-language-toggle.md`
- `.github/workflows/ci.yml`
- `package.json`

## Acceptance criteria

- [x] GitHub Actions workflow `.github/workflows/deploy-pages.yml` builds `site/` and deploys pages artifact on `main` push.
- [x] Astro production build outputs clean static assets respecting the `/gantry/` base path.
- [x] Comprehensive Playwright suite passes cleanly on desktop and mobile viewports with zero accessibility violations.
- [x] Repository test suite and npm packaging checks continue passing without regressions.

## Blocked by

- gantry-site#05

## Comments

Approved vertical slice breakdown.
