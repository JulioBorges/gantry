# Planning Approval and dispatch gating

Type: issue
Status: ready-for-agent
Slice: slicing-and-approval#06
Spec: [`../spec.md`](../spec.md) (spec 09, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/slicing-and-approval/spec.md`](../spec.md)

## What to build

Implement `plan.approve` as an operator-only operation bound to a specific `PlanVersionId`, recording actor provenance, channel, execution rule snapshot identity, and the proposal exactly as presented, so an audit can reconstruct what the operator saw. Planning Approval covers behavior, story coverage, granularity, and dependencies as one decision. An approval attempted through the MCP channel is rejected `operator_channel_required`; an agent result asserting approval creates no record; a stale version is rejected `approval_version_mismatch`.

Wire the dispatch precondition: builder dispatch requires a recorded approval for the *current* plan version, so passing lint never authorizes work.

This slice also carries one of the three call sites of the working-tree precondition predicate published by `repository-readiness#07`: Planning Approval is refused while an unclassified Dirty Working Tree exists in a relevant checkout. Spec 06 relies on this spec to prove that call site.

Surfaces: a CLI approval command, and one MCP parity test proving the channel rejection.

## Acceptance criteria

- [ ] `plan.approve` from an MCP channel is rejected `operator_channel_required`; from an interactive CLI session it succeeds.
- [ ] An agent result payload asserting approval produces no approval record and no state change.
- [ ] Approving a superseded or otherwise stale `PlanVersionId` is rejected `approval_version_mismatch`.
- [ ] The approval record stores the snapshot identity and the presented proposal content.
- [ ] Builder dispatch without a recorded approval for the current plan version is rejected with a typed code; a fully passing lint result does not satisfy the precondition.
- [ ] Editing a PBI's criteria after approval produces a new plan version identity and leaves the prior approval no longer current.
- [ ] Planning Approval is refused while an unclassified Dirty Working Tree exists, using the working-tree precondition predicate rather than a local re-implementation.

## Blocked by

- `slicing-and-approval#01` — provides the `PlanVersionId` the approval binds to and the proposal content recorded as presented.
- `execution-core#02` — provides the operator-channel rule, actor provenance, and the `operator_channel_required` rejection.
- `config-and-snapshot#04` — provides the Execution Rule Snapshot identity stored on the approval record.
- `repository-readiness#07` — provides the working-tree precondition predicate and the Dirty Working Tree classification it tests.
- `mcp-server#02` — provides MCP schema derivation from operation schemas, for the channel-rejection parity test only.
