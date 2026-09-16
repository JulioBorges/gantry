# Select from a complete executable model catalog

Type: issue
Status: ready-for-agent
Slice: `role-execution-selection#01`
Spec: `.scratch/role-execution-selection/spec.md`
Created: 2026-09-15

## Parent

`role-execution-selection`

## What to build

Deliver model and effort discovery usable during role selection across supported harnesses (Codex, Claude Code, OpenCode and Antigravity via `agy models`), and make the initial context budget accept discovered models without invented context windows.

### Files to read

- `.agents/skills/gantry/scripts/budget.py`
- `.agents/skills/gantry/capabilities/codex.json`
- `.agents/skills/gantry/capabilities/antigravity.json`
- `tests/test_context_budget.py`

## Acceptance criteria

- [ ] Paginated environment-specific catalog tests offer every executable model and only supported effort values across supported harnesses (including `agy models`); missing discovery produces an explicit blocking diagnostic.
- [ ] A discovered model absent from shipped declarations passes budget estimation with verified context metadata; missing metadata fails closed.
- [ ] Catalog provenance and freshness are exposed without credentials, and changing the effective provider/account invalidates stale availability.

## Blocked by

- None

## Comments

Draft proposal only; implementation requires operator approval.
