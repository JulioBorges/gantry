# Deliver Unified Kanban Board and Project Selector

Type: issue
Status: ready-for-agent
Slice: `interactive-dashboard#01`
Spec: `.scratch/interactive-dashboard/spec.md`
Created: 2026-09-18

## Parent

`interactive-dashboard`

## What to build

Unify multi-project Run state into a single 8-column Kanban board with a top project selector dropdown. By default (`ALL`), all tickets from all active execution units render together in one board with project identifier badges on each card. When an operator selects a specific project, only tickets from that project are displayed.

### Files to read

- `.agents/skills/gantry/scripts/dashboard.py`
- `.agents/skills/gantry/dashboard/static/index.html`
- `.agents/skills/gantry/dashboard/static/app.js`
- `.agents/skills/gantry/dashboard/static/style.css`
- `tests/test_dashboard.py`
- `site/tests/dashboard.spec.ts`

## Acceptance criteria

- [ ] `dashboard.py` collects all active execution units under the state root and exposes project metadata and runs via `GET /api/state`.
- [ ] The dashboard header displays a project dropdown selector defaulting to `ALL` alongside individual project options.
- [ ] In `ALL` mode, a single unified set of 8 columns renders all tickets aggregated across all projects, each card carrying a distinct project badge.
- [ ] Selecting a specific project filters the 8-column board to show only tickets belonging to that project.
- [ ] Automated tests in `tests/test_dashboard.py` and Playwright tests in `site/tests/dashboard.spec.ts` pass.

## Blocked by

- gantry-migration#11
- gantry-site#06

## Comments

Draft proposal only; implementation requires operator approval.
