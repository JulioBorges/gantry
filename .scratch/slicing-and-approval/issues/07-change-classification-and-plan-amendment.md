# Change classification and Plan Amendment

Type: issue
Status: ready-for-agent
Slice: slicing-and-approval#07
Spec: [`../spec.md`](../spec.md) (spec 09, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/slicing-and-approval/spec.md`](../spec.md)

## What to build

Implement the classification of a proposed plan change into `behavioral` or `internal`, and the `plan.amend` operation. The spec openly admits this classification cannot be fully mechanized; the mitigation is that anything touching recorded behavior, criteria, contracts, dependencies, or decomposition is behavioral by default and requires operator-only `plan.amend`, producing a new plan version with `supersedes` set and retaining the prior version. `internal` proceeds automatically only when behavior, contracts, criteria, dependencies, and decomposition are all preserved, and every classification records its rationale.

A Plan Amendment invalidates and reruns exactly the validations its changes affect — readiness for a changed spec, lint for changed PBIs, gate results for PBIs whose criteria or contracts changed — while unaffected PBIs continue running.

An agent proposes a change; it can never edit the approved plan.

## Acceptance criteria

- [ ] A behavioral change requires `plan.amend`, produces a new version with `supersedes` pointing at the prior one, and the prior version remains retrievable.
- [ ] An amendment invalidates only the affected validations, and a test proves an unaffected PBI keeps running through it.
- [ ] An amendment touching a PBI's criteria returns that PBI's gate results to pending; an amendment touching only another PBI does not.
- [ ] An internal change proceeds without operator involvement and persists its classification with its rationale.
- [ ] A change proposal asserting `internal` while altering criteria, contracts, dependencies, or decomposition is reclassified as behavioral and blocked pending approval.
- [ ] An agent attempting to write the approved plan directly is rejected; only a proposal is accepted.

## Blocked by

- `slicing-and-approval#06` — provides the approved plan baseline a change is classified against; the `internal` branch is defined as "preserves the approved plan", so classification has no meaning before Planning Approval exists.
- `entropy-gate#03` — provides the gate result invalidation hook that returns affected gate results to pending.
- `config-and-snapshot#05` — provides snapshot migration and approval invalidation semantics for an amendment that coincides with a rule change.
