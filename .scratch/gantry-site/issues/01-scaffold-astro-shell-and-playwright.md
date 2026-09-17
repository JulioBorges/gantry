# Scaffold Astro site with industrial shell and Playwright harness

Type: issue
Status: done
Slice: `gantry-site#01`
Spec: `.scratch/gantry-site/spec.md`
Created: 2026-09-17

## Parent

`gantry-site`

## What to build

Initialize the Astro project in `site/` configured with Tailwind CSS, `base: '/gantry/'` for GitHub Pages hosting, and a dark industrial design theme matching `assets/gantry.png` (obsidian `#0a0d14`, amber glowing accents `#ff9900` / `#f59e0b`, technical monospace font stack). Set up the Playwright test harness in `site/` with an initial smoke test verifying page rendering, title, and theme application.

### Files to read

- `.scratch/gantry-site/spec.md`
- `assets/gantry.png`
- `README.md`
- `package.json`

## Acceptance criteria

- [x] Astro project exists under `site/` with Tailwind CSS, React/Preact integration, and builds cleanly with `base: '/gantry/'`.
- [x] Base layout and industrial theme design tokens are implemented (obsidian background, technical grid borders, glowing amber accents, monospace headers).
- [x] Playwright E2E configuration exists in `site/` and runs a smoke test verifying the page renders the shell, heading, and correct metadata without errors.

## Blocked by

- None

## Comments

Approved vertical slice breakdown.
