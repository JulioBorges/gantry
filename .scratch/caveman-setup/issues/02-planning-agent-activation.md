# Apply Caveman lite to planning agents

Type: issue
Status: ready-for-agent
Slice: `caveman-setup#02`
Spec: `.scratch/caveman-setup/spec.md`
Created: 2026-09-15

## Parent

`caveman-setup`

## What to build

Extend the approved activation contract to every planning agent: Requirement Critic, research, Planner and Plan Critic. Each fresh invocation, including invalid-result retries, receives access to the external skill and the lite conversational scope through supported host-harness mechanisms. Planning remains usable with normal behavior where activation is unavailable.

### Files to read

- `.agents/skills/gantry/reference/plan-workflow.md`
- `.agents/skills/gantry/SKILL.md`
- `tests/test_canonical_gantry_workflow.py`
- `tests/test_legacy_workflow_smoke.py`

## Acceptance criteria

- [ ] Every planning-role invocation, including research and retries, receives supported external-skill access and lite instructions when the repository preference is enabled and availability is established.
- [ ] Disabled or unavailable activation uses normal behavior and the shared once-per-Run warning contract; planning does not block solely on Caveman.
- [ ] Specs, draft Issues, persisted role results, exact errors/commands and required evidence retain implementation and review detail despite conversational compression.
- [ ] Requirement Review, Result Contract validation, initial-context budgeting and the planning approval stop retain their existing semantics.
- [ ] Fixture coverage checks actual planning invocation paths, research calls and retries using a fake external skill and agent recorder, and exercises enabled, disabled and unavailable states without global installation or paid calls.
- [ ] Planning documentation distinguishes tested propagation contracts from live model behavior and unmeasured savings; the manual harness-neutral path carries the same instructions.

## Blocked by

- `caveman-setup#01`

## Comments

- 2026-09-15 — Operator approved this three-slice breakdown; publication does not start implementation. Issues 02 and 03 may proceed concurrently after 01; keep edits to shared coordinating instructions in 01 and role-specific changes in their respective workflows.

