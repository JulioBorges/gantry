# Recover an unavailable Issue role without interrupting independent work

Type: issue
Status: done
Slice: `role-execution-selection#04`
Spec: `.scratch/role-execution-selection/spec.md`
Created: 2026-09-15

## Parent

`role-execution-selection`

## What to build

Isolate runtime execution failures and support explicit retry or validated replacement for the next Issue-role invocation.

### Files to read

- `.agents/skills/gantry/reference/round-workflow.md`
- `.agents/skills/gantry/scripts/runlog.py`
- `tests/test_canonical_gantry_workflow.py`

## Acceptance criteria

- [x] A two-Issue workflow test pauses one failed execution, preserves its worktree and allows the independent accepted Issue to integrate.
- [x] The same workflow blocks the next round until explicit recovery; no automatic fallback or automatic retry substitutes a selection.
- [x] Issue-role replacement is validated and logged, does not alter active agents or saved defaults, and preserves previously spent correction budgets.
- [x] Execution-unavailability reporting is distinct from Critic refutation and invalid-result handling; authoritative completion remains owned by roadmap.py.
- [x] Run Log selection and change events contain Issue/role identity and requested/effective selection evidence without secrets or raw command output.

## Blocked by

- role-execution-selection#03

## Comments

Draft proposal only; implementation requires operator approval.
