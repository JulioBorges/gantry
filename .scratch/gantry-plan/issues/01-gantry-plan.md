# Prefactor and add planning milestone telemetry in runlog and dashboard

Type: issue
Status: done
Slice: `gantry-plan#01`
Spec: `.scratch/gantry-plan/spec.md`
Created: 2026-09-19

## Parent

`gantry-plan`

## What to build

Prefactor and extend `runlog.py` and `dashboard.py` to support spec milestone tracking (`<slug>#00`) in the `Plan` column.

When `gantry-plan` starts, it initializes tracking for the spec milestone using `<slug>#00` (which conforms to `ISSUE_RE`). Enable `phase.started` for `Plan` to record `data.operatorWaiting: true` and current activity (e.g. `"Socratic Interview"` or `"Awaiting Plan Approval"`). Update `dashboard.py` to display the card in the `Plan` column with an `"Awaiting Operator"` badge, update `operatorWaiting: false` on `operator.approved`, and conclude the milestone card when `issue.done` is logged.

### Files to read

- `.agents/skills/gantry/scripts/runlog.py`
- `.agents/skills/gantry/scripts/dashboard.py`
- `tests/test_runlog.py`
- `tests/test_dashboard.py`

## Acceptance criteria

- [x] `runlog.py append` accepts `phase.started` with `issue="<slug>#00"`, `phase="Plan"`, and `data={"operatorWaiting": true}`.
- [x] `dashboard.py` places `<slug>#00` in the `Plan` column and displays `liveActivity: "Awaiting Operator"` when `operatorWaiting` is true.
- [x] Logging `operator.approved` updates the `<slug>#00` state in `dashboard.py` clearing `operatorWaiting`.
- [x] Logging `issue.done` for `<slug>#00` transitions the card to `Done` and freezes cycle time.
- [x] Unit tests in `tests/test_runlog.py` and `tests/test_dashboard.py` pass cleanly.

## Blocked by

- None
