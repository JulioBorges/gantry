# Freeze Cycle Timer on Done and Track Phase Durations

Type: issue
Status: ready-for-agent
Slice: `interactive-dashboard#05`
Spec: `.scratch/interactive-dashboard/spec.md`
Created: 2026-09-18

## Parent

`interactive-dashboard`

## What to build

Freeze the elapsed delivery timer when an issue completes the Integrate phase and transitions to Done upon merge confirmation. Calculate total cycle duration and track per-phase durations (Plan, Implement, Review, Critic, Integrate) displayed in the card and modal.

### Files to read

- `.agents/skills/gantry/scripts/dashboard.py`
- `.agents/skills/gantry/dashboard/static/app.js`
- `.agents/skills/gantry/dashboard/static/style.css`
- `tests/test_dashboard.py`
- `site/tests/dashboard.spec.ts`

## Acceptance criteria

- [ ] When an issue transitions to `issue.done`, the elapsed timer ceases incrementing and fixes the final completion timestamp.
- [ ] Done cards render a frozen total cycle time badge formatted in human-readable units (e.g., `Total: 14m 20s`).
- [ ] The detail modal displays a breakdown of elapsed time spent in each individual phase (Plan, Implement, Review, Critic, Integrate).
- [ ] Delivery integration strategy (PR vs branch merge) configured in `.gantry/config.json` is respected, transitioning to Done only upon verified merge.
- [ ] Unit tests verify time calculations for finished issues and Playwright tests verify the frozen badge display.

## Blocked by

- interactive-dashboard#01
- interactive-dashboard#03
- interactive-dashboard#04

## Comments

Draft proposal only; implementation requires operator approval.
