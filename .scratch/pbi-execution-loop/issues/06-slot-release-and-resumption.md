# Slot release during review, reacquisition, and resumption

Type: issue
Status: ready-for-agent
Slice: pbi-execution-loop#06
Spec: [`../spec.md`](../spec.md) (spec 11, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/pbi-execution-loop/spec.md`](../spec.md)

## What to build

A PBI entering `awaiting_review` or `awaiting_operator` with no active assignment and no in-flight operation releases its capacity slot while keeping its worktree, lease, evidence, and state. Its dependents stay ineligible, because the prerequisite is not integrated. Waiting is not losing: nothing is cancelled and no history is discarded.

Resuming requires reacquiring a slot and revalidating dependency readiness, current target, approval currency, and the worktree lease, so releasing a slot is never a path around the capacity limit. Each of the four revalidations must be independently provable by making exactly one of them stale.

Execution resumption after a simulated harness closure reconciles pending assignments and operations first, then reuses the existing worktree and branch, and issues no duplicate dispatch for an assignment that was already in flight. The loop requires the host harness to remain active — there is no background service, progress is persisted at every transition, and closing the harness costs continuity rather than work.

## Acceptance criteria

- [ ] A PBI entering `awaiting_review` releases its slot, another PBI starts in that slot, and the waiting PBI's worktree, lease, and evidence are intact afterward.
- [ ] Dependents of a waiting PBI remain `awaiting_dependency` for as long as the prerequisite is not integrated.
- [ ] Resuming a waiting PBI fails when no slot is available, and on success revalidates all four of dependency readiness, current target, approval currency, and lease ownership — each independently provable by making exactly one of them stale.
- [ ] Resumption after a simulated harness closure reconciles before progressing, reuses the existing worktree and branch, and issues no duplicate dispatch for an assignment that was already in flight.
- [ ] A PBI with an in-flight operation does not release its slot even while nominally waiting.
- [ ] The CLI surface for slot release and reacquisition gets one parity test proving delegation.

## Blocked by

- `pbi-execution-loop#01` — the worktree lease that survives the wait and is revalidated on resume.
- `pbi-execution-loop#02` — the joint capacity accounting a released slot returns to and a resuming PBI reacquires from.
- `execution-core#03` — the PBI state `awaiting_review`, `pbi.releaseSlot`, `pbi.claimOwnership`, and the slot-occupancy rule.
- `execution-core#06` — the Operation Reconciliation that must clear before progression resumes.
- `execution-core#08` — `execution.resume` and its reconciliation-before-progression requirement.
