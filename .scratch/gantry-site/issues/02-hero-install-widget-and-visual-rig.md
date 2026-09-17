# Build hero section with multi-harness install widget and crane visual

Type: issue
Status: ready-for-agent
Slice: `gantry-site#02`
Spec: `.scratch/gantry-site/spec.md`
Created: 2026-09-17

## Parent

`gantry-site`

## What to build

Implement the hero section of the landing page featuring Gantry's value proposition ("Turn an approved Spec into verified software deliveries inside your coding harness"), the official gantry crane visual motif, and an interactive multi-harness quick install widget. The widget provides selectable tabs for Claude Code, OpenCode, Codex, Gemini/Antigravity, and Cursor, displaying the exact CLI command (`npx skills add JulioBorges/gantry` / `npx @julioborges/gantry add`) with a copy button, clipboard integration, and visual copy confirmation.

### Files to read

- `.scratch/gantry-site/spec.md`
- `.scratch/gantry-site/issues/01-scaffold-astro-shell-and-playwright.md`
- `README.md`
- `package.json`

## Acceptance criteria

- [ ] Hero displays the primary tagline, value proposition, status badges, and crane visual motif.
- [ ] Quick install widget provides switchable tabs for supported harnesses with accurate CLI commands and flags.
- [ ] Copy button copies the selected installation command to the clipboard and gives clear visual feedback.
- [ ] Playwright test validates hero rendering, tab selection switching, copy button interaction, and mobile responsiveness.

## Blocked by

- gantry-site#01

## Comments

Approved vertical slice breakdown.
