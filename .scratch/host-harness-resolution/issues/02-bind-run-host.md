# Bind new workflows to a resolved Run host

Type: issue
Status: ready-for-agent
Slice: `host-harness-resolution#02`
Spec: `.scratch/host-harness-resolution/spec.md`
Created: 2026-09-30
User stories covered: 10–17, 22, 24

## Parent

`host-harness-resolution`

## What to build

Make planning and execution entry resolve the actual host before host-dependent initialization, worktree creation or role scheduling. Propagate the resolved host into capabilities, native/external dispatch and Run metadata while preserving role precedence and independent validations. Demonstrate an intentionally external Critic under a mismatched saved preference. Deliver workflow instructions and regression evidence with the behavior.

### Files to read

- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/reference/plan-workflow.md`
- `tests/test_cross_harness_proof.py`

### Focused follow-up exploration

Keep the initial package within the existing context budget. Locate the relevant host-routing, Run lifecycle and regression scenarios with targeted searches before loading further material. Consult these additional sources on demand, reading only the relevant sections per step: `.agents/skills/gantry/scripts/runlog.py`, `.agents/skills/gantry/SKILL.md`, `.agents/skills/gantry-plan/SKILL.md`, `.agents/skills/gantry/reference/round-workflow.md`, `tests/test_canonical_gantry_workflow.py`. Do not preload every reference or the entire canonical workflow test module. All approved integration coverage remains required.

## Acceptance criteria

- [ ] Both entry paths reject unresolved or unsupported host identity before creating Run worktrees or invoking role agents; no implicit Claude Code or saved-policy fallback remains in the affected routing paths.
- [ ] A selected Claude Code host with a saved Antigravity preference uses Claude Code capability metadata, reports the mismatch and leaves repository policy unchanged.
- [ ] A resolved Codex host with a selected Claude Code Critic takes the existing external dispatch path, preserving model/effort and enforcing the Result Contract. A same-host selection takes the intended native path.
- [ ] All base and derived role selections, Issue/Run overrides, custom policy fields and independent readiness/availability checks retain their semantics.
- [ ] Concurrent new Runs retain separate resolved-host records; diagnostics and Run metadata contain only sanitized identity/provenance and no secrets.
- [ ] Existing workflow smoke/fixture seams exercise entry, routing and no-work-on-failure; include sanitized evidence of one real stale-preference invocation and distinguish it from mocked dispatch coverage.

## Blocked by

- `host-harness-resolution#01`

## Comments

- 2026-09-30 — Operator approved the Spec, test seams and four-Issue breakdown in conversation. Planning approval does not authorize implementation.
- 2026-09-30 — Budget audit narrowed the initial reading package; additional approved integration references remain available through focused follow-up exploration. Scope, acceptance criteria and dependencies are unchanged.
