# Package gantry-plan skill, wire gantry delegation, and execution handoff

Type: issue
Status: done
Slice: `gantry-plan#04`
Spec: `.scratch/gantry-plan/spec.md`
Created: 2026-09-19

## Parent

`gantry-plan`

## What to build

Create the standalone `gantry-plan` skill pack, integrate delegation from `gantry`, and wire the approval transition and execution handoff.

1. Package `.agents/skills/gantry-plan/SKILL.md` declaring `/gantry-plan` and its argument hint: `<spec-slug | spec-path | "free-text goal">`.
2. Update `.agents/skills/gantry/SKILL.md` to automatically delegate to `gantry-plan` when a free-text goal or an unplanned spec is passed as input.
3. Wire the planning approval transition:
   - Mark approved issues `ready-for-agent` via `python3 "$skillDir/scripts/roadmap.py" status <ref> ready-for-agent`.
   - Recompute waves via `python3 "$skillDir/scripts/roadmap.py" waves`.
   - Verify integrity via `python3 "$skillDir/scripts/roadmap.py" check`.
   - Complete `<slug>#00` milestone in the Run log (`issue.done`).
4. On standalone `gantry-plan` invocation, present the computed execution waves and prompt the operator whether to launch `gantry` immediately; on delegated `gantry` invocation, automatically advance into the execution round loop.
5. Create comprehensive tests in `tests/test_gantry_plan.py` verifying skill discovery, delegation logic, and roadmap updates.

### Files to read

- `.agents/skills/gantry/SKILL.md`
- `.agents/skills/gantry/scripts/roadmap.py`
- `.agents/skills/gantry/scripts/frontier.py`
- `tests/test_canonical_gantry_workflow.py`

## Acceptance criteria

- [x] `.agents/skills/gantry-plan/SKILL.md` is registered and valid.
- [x] `.agents/skills/gantry/SKILL.md` delegates free-text goals and unplanned specs to `gantry-plan`.
- [x] Operator approval transitions issues to `ready-for-agent` and updates `ROADMAP.md` waves.
- [x] `roadmap.py check` passes with zero drift.
- [x] Standalone invocation offers interactive handoff to `gantry`; delegated invocation continues automatically.
- [x] Integration tests in `tests/test_gantry_plan.py` pass cleanly.

## Blocked by

- `gantry-plan#02`
- `gantry-plan#03`
