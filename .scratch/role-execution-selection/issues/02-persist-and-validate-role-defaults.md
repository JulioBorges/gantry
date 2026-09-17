# Start a Run from validated repository role defaults

Type: issue
Status: done
Slice: `role-execution-selection#02`
Spec: `.scratch/role-execution-selection/spec.md`
Created: 2026-09-15

## Parent

`role-execution-selection`

## What to build

Extend setup and preflight so tracked execution defaults and temporary overrides produce a validated effective selection for every role (including `antigravity`), and provision Antigravity lifecycle hooks via `.agents/hooks.json`.

### Files to read

- `.agents/skills/gantry-setup/SKILL.md`
- `.agents/skills/gantry/scripts/setup.py`
- `.agents/skills/gantry/scripts/common.py`
- `.agents/skills/gantry/capabilities/antigravity.json`
- `tests/test_gantry_setup.py`

## Acceptance criteria

- [x] Setup preview and merge tests persist execution.roles in .gantry/config.json while preserving unrelated policy, hooks and Caveman settings, and configure .agents/hooks.json when Antigravity is detected.
- [x] Git ignore tests show canonical root policy is trackable while transient state and credentials remain excluded.
- [x] Preflight tests demonstrate precedence, explicit defaults and derived-role inheritance (including Antigravity with Gemini models), and start no implementation when a selected combination fails authentication or execution validation.
- [x] Model strength guidance is advisory; a valid cross-family selection is not blocked by a guessed ranking.

## Blocked by

- role-execution-selection#01

## Comments

Draft proposal only; implementation requires operator approval.
