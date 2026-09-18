# Stream Live Agent Activity and Render Execution Modal

Type: issue
Status: done
Slice: `interactive-dashboard#02`
Spec: `.scratch/interactive-dashboard/spec.md`
Created: 2026-09-18

## Parent

`interactive-dashboard`

## What to build

Provide live agent activity visibility on ticket cards and within an interactive execution detail modal. Connect the dashboard to active harness session transcripts to stream system thoughts, tool invocations, and syntax-highlighted code diffs in real time.

### Files to read

- `.agents/skills/gantry/scripts/dashboard.py`
- `.agents/skills/gantry/dashboard/static/app.js`
- `.agents/skills/gantry/dashboard/static/style.css`
- `tests/test_dashboard.py`
- `site/tests/dashboard.spec.ts`

## Acceptance criteria

- [x] Ticket cards display live activity badges indicating current status (`Thinking...`, `Tool: <name>`, `Awaiting Operator`).
- [x] Clicking any ticket card opens an execution detail modal.
- [x] An endpoint `GET /api/runs/<unit>/<run>/issues/<issue>/transcript` streams incremental transcript steps (thoughts, tool calls, and diffs) discovered from the harness session.
- [x] The modal renders model reasoning in collapsible thinking blocks, formatted tool call records, and code changes with syntax highlighting.
- [x] Playwright tests verify modal opening, live badge display, and collapsible block interactions.

## Blocked by

- interactive-dashboard#01

## Comments

Draft proposal only; implementation requires operator approval.
