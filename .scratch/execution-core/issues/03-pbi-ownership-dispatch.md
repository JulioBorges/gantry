# PBI Execution Ownership, dispatch, and capacity accounting

Type: issue
Status: ready-for-agent
Slice: execution-core#03
Spec: [`../spec.md`](../spec.md) (spec 01, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/execution-core/spec.md`](../spec.md)

## What to build

Implement the PBI state machine from `planned` through `awaiting_dependency`, `queued`, `implementing`, `handoff_pending`, `awaiting_review`, and `awaiting_operator`, via `pbi.schedule`, `pbi.dispatch`, `pbi.claimOwnership`, and `pbi.releaseSlot`, using the fake harness driver. This slice owns the `awaiting_review` state itself — the review-pending state a PBI occupies between implementation and merge authorization — which later specs consume rather than define.

An Assignment record carries an ownership generation, role, driver reference, and supersession marker, so a PBI has at most one active execution owner and taking over reconciles the previous assignment before claiming. A PBI occupies an execution slot while it has an active assignment or an in-flight operation; entering `awaiting_review` or `awaiting_operator` with neither releases the slot while preserving worktree, evidence, and state, and leaving those states requires `pbi.claimOwnership` to reacquire a slot and revalidate Dependency Readiness and the current target. The execution's `running` ⇄ `waiting` transitions follow from this.

Add the operator-channel operation `pbi.answer`, which returns a PBI from `awaiting_operator` to `queued` carrying the operator's answer as continuity input for the next dispatch, so a PBI blocked on a question resumes with the answer attached rather than losing it.

## Acceptance criteria

- [ ] `pbi.dispatch` against a PBI with unmet prerequisites is rejected `dependency_not_ready`, and against a full capacity limit `capacity_unavailable`; neither leaves a partial assignment.
- [ ] A second `pbi.claimOwnership` supersedes the first, increments the ownership generation, and reconciles the prior assignment before the new one becomes active.
- [ ] Releasing a slot on entry to `awaiting_operator` frees capacity for another eligible PBI, and the released PBI cannot resume active work without reacquiring a slot and passing revalidation.
- [ ] `awaiting_dependency`, `awaiting_review`, and `awaiting_operator` are distinguishable in `state.project`, and only `awaiting_operator` is reachable from an agent-reported blocked result carrying questions.
- [ ] An execution with no active assignment and no in-flight operation but work pending a decision projects as `waiting`, not `running`.
- [ ] `awaiting_review` is a distinct PBI state with its own entry and exit transitions, reachable only once implementation is complete and not conflated with `awaiting_operator`.
- [ ] `pbi.answer` from the operator channel returns a PBI from `awaiting_operator` to `queued` with the operator's answer recorded as continuity input and available to the next dispatch; the same call from a non-operator channel is rejected `operator_channel_required`.

## Blocked by

- `execution-core#01` — the `invoke` seam, the atomic transition primitive, the fake harness driver, and the state builders.
- `gtp-protocol#02` — the builder task envelope shape carried by a dispatch.
- `gtp-protocol#03` — the non-mutating role task envelope shapes for the remaining dispatchable roles.
- `config-and-snapshot#01` — the capacity limit values consulted by slot accounting.
