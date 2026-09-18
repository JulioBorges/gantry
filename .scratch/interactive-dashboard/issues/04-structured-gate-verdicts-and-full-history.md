# Render Structured Gate Verdicts and Full Execution History

Type: issue
Status: ready-for-agent
Slice: `interactive-dashboard#04`
Spec: `.scratch/interactive-dashboard/spec.md`
Created: 2026-09-18

## Parent

`interactive-dashboard`

## What to build

Expose structured verdicts for each delivery gate (Plan, Implement, Critic, Integrate) and provide a comprehensive execution history tab in the ticket modal with the ability to pop out into a dedicated browser window.

### Files to read

- `.agents/skills/gantry/scripts/dashboard.py`
- `.agents/skills/gantry/scripts/result.py`
- `.agents/skills/gantry/scripts/gates.py`
- `.agents/skills/gantry/dashboard/static/app.js`
- `tests/test_dashboard.py`
- `site/tests/dashboard.spec.ts`

## Acceptance criteria

- [ ] Structured gate outputs for Plan, Implement, Critic, and Integrate are persisted under `~/.gantry/state/<unit>/artifacts/<run>/<issue>/gate-<phase>.json` and queryable via `GET /api/runs/<unit>/<run>/issues/<issue>/gates`.
- [ ] The ticket detail modal features a tabbed layout: [Pareceres dos Gates] and [Histórico Completo].
- [ ] The gate tab renders the formal evaluation for Plan (criteria/scope), Implement (test proofs/TDD), Critic (verdict/evidence/failures), and Integrate (PR/merge).
- [ ] The history tab renders the full chronological timeline of events, tool calls, and outputs with an action button to open the view in a dedicated browser window/tab.
- [ ] Tests verify gate endpoint retrieval and Playwright tab navigation.

## Blocked by

- interactive-dashboard#01
- interactive-dashboard#02

## Comments

Draft proposal only; implementation requires operator approval.
