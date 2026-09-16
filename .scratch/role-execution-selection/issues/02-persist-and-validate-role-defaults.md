# Start a Run from validated repository role defaults

Type: issue
Status: ready-for-agent
Slice: `role-execution-selection#02`
Spec: `.scratch/role-execution-selection/spec.md`
Created: 2026-09-15

## Parent

`role-execution-selection`

## What to build

Extend setup and preflight so tracked execution defaults and temporary overrides produce a validated effective selection for every role.

### Files to read

- `.agents/skills/gantry-setup/SKILL.md`
- `.agents/skills/gantry/scripts/setup.py`
- `.agents/skills/gantry/scripts/common.py`
- `tests/test_gantry_setup.py`

## Acceptance criteria

- [ ] Setup preview and merge tests persist execution.roles in .gantry/config.json while preserving unrelated policy, hooks and Caveman settings.
- [ ] Git ignore tests show canonical root policy is trackable while transient state and credentials remain excluded.
- [ ] Preflight tests demonstrate precedence, explicit defaults and derived-role inheritance, and start no implementation when a selected combination fails authentication or execution validation.
- [ ] Model strength guidance is advisory; a valid cross-family selection is not blocked by a guessed ranking.

## Blocked by

- role-execution-selection#01

## Comments

Draft proposal only; implementation requires operator approval.
