# Resume an existing Run with an approved host transition

Type: issue
Status: done
Slice: `host-harness-resolution#04`
Spec: `.scratch/host-harness-resolution/spec.md`
Created: 2026-09-30
User stories covered: 22–24

## Parent

`host-harness-resolution`

## What to build

On resumption, resolve the current invocation again and compare it with the prior Run host. Require a concrete operator decision for a host transition, record it, and continue through the existing workflow in the same Run and assigned worktrees. Preserve role overrides and spent correction budgets. Document and prove the resumption path rather than treating resumption as a new Run.

### Files to read

- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/scripts/runlog.py`
- `tests/test_round_workflow_lifecycle_hooks.py`

### Focused follow-up exploration

Keep the initial package within the existing context budget. Locate the relevant host-routing, Run lifecycle and regression scenarios with targeted searches before loading further material. Consult these additional sources on demand, reading only the relevant sections per step: `.agents/skills/gantry/SKILL.md`, `.agents/skills/gantry/reference/round-workflow.md`, `tests/test_cross_harness_proof.py`, `tests/test_runlog.py`. Do not preload every reference or the entire canonical workflow test module. All approved integration coverage remains required.

## Acceptance criteria

- [x] Resumption with unknown, conflicting or unsupported host identity performs no new role work; another Run's host record cannot resolve the ambiguity.
- [x] An unchanged resolved host resumes through the normal existing recovery path. A changed host presents old/new identity and requested effects before continuation.
- [x] Declining a host transition leaves worktrees, revisions, role overrides and correction counts unchanged; no new Run or worktree silently substitutes for the existing one.
- [x] Approving the transition records sanitized old/new host and confirmation provenance under the same Run and uses the newly resolved host for capabilities and role routing.
- [x] Resumed workflow fixture evidence demonstrates existing Issue worktrees and spent correction attempts survive the transition; missing older host metadata requires explicit establishment rather than a guessed fallback.
- [x] Concurrent worktree/Run tests prove transition metadata isolation; documentation and final verification receipts identify simulated coverage and any live resumption evidence separately.

## Blocked by

- `host-harness-resolution#02`

## Comments

- 2026-09-30 — Operator approved the Spec, test seams and four-Issue breakdown in conversation. Planning approval does not authorize implementation.
- 2026-09-30 — Budget audit narrowed the initial reading package; additional approved integration references remain available through focused follow-up exploration. Scope, acceptance criteria and dependencies are unchanged.
