# Merge Authorization binding and serialized integration

Type: issue
Status: ready-for-agent
Slice: execution-core#07
Spec: [`../spec.md`](../spec.md) (spec 01, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/execution-core/spec.md`](../spec.md)

## What to build

Implement `merge.authorize`, `merge.confirmLocal`, and `merge.recordOutcome`, and the PBI transitions `awaiting_review` → `merge_authorized` → `integrated`, plus `externally_integrated` for a delivery merged outside Gantry. Merge Authorization is bound to a specific merge candidate and target revision, and a change to either invalidates it and forces revalidation — Implementation Completion alone never grants it.

This slice owns the Merge Authorization **binding record and its invalidation rule** and nothing else about merging: Merge Candidate preparation, the Git and provider mechanics, and the observation of candidate and target revisions belong to `git-integration#02`, which consumes the invalidation predicate defined here rather than redefining it. Build the predicate against a declared revision-observation interface so the boundary holds in both directions.

Serialization is a lease row acquired in an immediate transaction and scoped to one Repository Execution Unit, holding owner identity, heartbeat, and expiry; an expired lease may be taken only after the previous holder's operation has been reconciled, and an expired lease whose operation is `unknown` blocks with `reconciliation_required`. A direct local merge requires `merge.confirmLocal` immediately before the mutation, separate from any prior plan approval, and the projection states the lease scope plainly as one unit on one machine rather than a distributed guarantee.

## Acceptance criteria

- [ ] Merge Authorization granted against a target revision and then invalidated by an advanced target is refused until revalidated, and the invalidation is visible in `state.project`.
- [ ] A PBI in `implementation_complete` cannot reach `merge_authorized` without the gate and review states in between.
- [ ] Lease contention is proven across two separate operating-system processes against the same database file, not two asynchronous calls in one process; the loser receives `lock_unavailable`.
- [ ] An expired lease whose prior holder's operation is `unknown` is not reclaimable and yields `reconciliation_required`; once reconciled, reclaiming succeeds.
- [ ] A local merge without an immediately preceding `merge.confirmLocal` from the operator channel is refused even when a Planning Approval exists.
- [ ] The operator-facing projection names the serialization scope as one Repository Execution Unit on one machine.

## Blocked by

- `execution-core#06` — the operation state machine the lease reclaim rule consults before taking an expired lease.
- `execution-core#05` — the gate states past which merge becomes reachable.
- `git-integration#02` — Merge Candidate preparation and target revision observation; develop against the declared observation interface and integrate when it lands, since that slice consumes this one's invalidation predicate.
- `git-integration#06` — Provider Protection Authority observation for the `externally_integrated` path; same interface-first treatment.
