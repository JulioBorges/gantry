# Build interactive pipeline simulator island

Type: issue
Status: ready-for-agent
Slice: `gantry-site#03`
Spec: `.scratch/gantry-site/spec.md`
Created: 2026-09-17

## Parent

`gantry-site`

## What to build

Implement a client-side interactive island showcasing Gantry's SDLC pipeline stages: Spec & Requirement Critic, Planning & Context Budget, TDD Implementer, Two-Axis Reviewer, Adversarial Critic, and Serial Integration Gate. Visitors can step through or click individual stages to view: (1) what the deterministic script enforces (`spec.py`, `budget.py`, `frontier.py`, `acceptance.py`, `gates.py`, `roadmap.py`), (2) what the agent role proposes, and (3) realistic simulated terminal output and JSON event logs in an industrial console display.

### Files to read

- `.scratch/gantry-site/spec.md`
- `.scratch/gantry-site/issues/01-scaffold-astro-shell-and-playwright.md`
- `PRD.md`
- `CONTEXT.md`

## Acceptance criteria

- [ ] Simulator island displays all six core pipeline stages with active, completed, and pending visual indicators.
- [ ] Selecting a stage dynamically updates the stage description, script invariants, agent responsibilities, and simulated terminal log stream.
- [ ] Terminal view provides realistic syntax-highlighted commands, checks, and JSON log events for each phase.
- [ ] Playwright tests verify keyboard navigation, stage transitions, active state classes, and responsive layout scaling.

## Blocked by

- gantry-site#01

## Comments

Approved vertical slice breakdown.
