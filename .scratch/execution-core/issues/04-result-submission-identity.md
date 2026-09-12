# Result Submission identity, receipts, and stale assignment rejection

Type: issue
Status: ready-for-agent
Slice: execution-core#04
Spec: [`../spec.md`](../spec.md) (spec 01, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/execution-core/spec.md`](../spec.md)

## What to build

Implement `pbi.submitResult` and the transition to `implementation_complete`. Ownership is checked before content, so a result arriving from a superseded assignment is stored for audit and rejected without changing state.

Submission identity follows the operation core's `requestId` idempotency with submission-specific rules layered on: an identical accepted replay returns the prior receipt with no second transition, no counter change, and no downstream dispatch; identical identity with corrected content is rejected `duplicate_conflict`; and a genuine correction arrives as a new submission carrying a link to the previous attempt, which preserves history without bypassing ownership, role, or transition checks.

Extend `state.project` to show the current submission, its receipt, and the chain of linked attempts.

## Acceptance criteria

- [ ] A late result from a superseded assignment is persisted and rejected `stale_assignment`, and the PBI's state and counters are byte-identical before and after.
- [ ] Replaying an accepted submission returns the original receipt and triggers no downstream dispatch, verifiable through the fake harness driver's call record.
- [ ] A corrected submission with a new identity linking the prior attempt is accepted, and both attempts remain queryable through `audit.query`.
- [ ] A result that does not satisfy the completion evidence rules leaves the PBI in `implementing` with a typed rejection rather than advancing to `implementation_complete`.
- [ ] `implementation_complete` is reachable without any merge permission being granted, and `state.project` exposes them as separate facts.

## Blocked by

- `execution-core#03` — the PBI state machine, Assignment records, and the ownership generation this checks before content.
- `gtp-protocol#02` — the result contract carried by a submission.
- `gtp-protocol#04` — status semantics and precedence over the reported result.
- `gtp-protocol#05` — the Implementation Completion evidence rules that gate the transition.
- `gtp-protocol#01` — the `extensions` lifting rule that fixes the persisted envelope shape.
