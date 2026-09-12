# Gate state, Correction Budget accounting, and operator grants

Type: issue
Status: ready-for-agent
Slice: execution-core#05
Spec: [`../spec.md`](../spec.md) (spec 01, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/execution-core/spec.md`](../spec.md)

## What to build

Implement the gate state machine (`pending`, `evaluating`, `passed`, `failed`, `pending_review`, `blocked_incomplete_evidence`, `blocked_infrastructure`) and the PBI's `in_gates` ⇄ `correcting` loop through `gate.evaluate`, `gate.classifyFinding`, `correction.dispatch`, and `correction.grantAttempts`, using the fake check adapter. `pending_review` is this slice's state for a gate whose required adversarial critic is unavailable: the gate neither passes nor fails, it waits, and merge stays prohibited while it waits.

One Correction Budget per PBI, shared by all its gates, consumed when `correction.dispatch` is accepted rather than when revalidation completes, so an interrupted cycle stays consumed and a resume continues the same attempt. The initial `gate.evaluate` consumes nothing. Exhaustion with unresolved findings moves the PBI to `gates_failed`, stops automatic correction, and keeps merge prohibited; `correction.grantAttempts` records an additive operator grant with its reason and there is no reset.

A `passed` gate returns to `pending` when the merge candidate revision, the target revision, or the rule version changes, and structurally incomplete comparison evidence fails closed into `blocked_incomplete_evidence`.

## Acceptance criteria

- [ ] Five Correction Attempts are consumed, the sixth is rejected `correction_budget_exhausted`, and the gate reads `failed` with the PBI in `gates_failed`.
- [ ] An operator grant of further attempts permits correction to continue while the cumulative consumed count is preserved and visible, never reset.
- [ ] A correction cycle interrupted between dispatch and revalidation and then resumed consumes no second attempt and returns none.
- [ ] A `passed` gate returns to `pending` when the candidate revision changes, when the target revision advances, and when the rule version changes — three separate cases, each asserted.
- [ ] A check result missing the identity or context needed for comparison leaves the gate `blocked_incomplete_evidence` and the PBI unable to reach `awaiting_review`.
- [ ] The Correction Budget is unchanged across a handoff, an agent replacement, a cancellation, and a resumption.
- [ ] A gate whose required adversarial critic is unavailable reads `pending_review` rather than `passed` or `failed`, consumes no Correction Attempt, leaves merge prohibited, and returns to evaluation once the critic becomes available.

## Blocked by

- `execution-core#01` — the `invoke` seam, the atomic transition primitive with counter changes in one transaction, the fake check adapter, and the state builders.
- `verification-adapters#01` — the normalized finding shape the gate records and compares.
- `verification-adapters#03` — the Evidence Completeness rules that drive the fail-closed path.
- `config-and-snapshot#01` — the Correction Budget default value.
