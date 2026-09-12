# Snapshot migration and approval invalidation

Type: issue
Status: ready-for-agent
Slice: config-and-snapshot#05
Spec: [`../spec.md`](../spec.md) (spec 02, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/config-and-snapshot/spec.md`](../spec.md)

## What to build

`execution.migrateRuntime` and its rule-change counterpart as operator-only operations that move an in-flight execution to a new snapshot. A migration records the old and new snapshot identities and the operator's stated reason, then classifies every existing record: approvals whose governing rules changed are invalidated, gate results whose rules or commands changed return to `pending`, and unaffected records keep their original binding. Affected work is revalidated before it advances.

Two specific invalidation rules ship with this slice: a changed Verification Command Approval invalidates Comparison Evidence produced by its previous version, and a recorded tool version change invalidates comparison evidence that depended on it.

The normal path for a rule change remains simply the next execution, which always captures a fresh snapshot. Migration exists so that moving running work is a decision the operator makes, never a side effect of an edit.

## Acceptance criteria

- [ ] A migration invalidates approvals whose governing rules changed, returns affected gates to `pending`, and leaves unaffected records bound to their original snapshot.
- [ ] A migration requested from the MCP channel is refused with `operator_channel_required`; the same request from an interactive CLI session or a dashboard request carrying a valid Dashboard Capability Token is accepted.
- [ ] A changed verification command invalidates evidence produced by the previous version of that command; unrelated evidence is untouched.
- [ ] A tool version change recorded in the new snapshot invalidates the comparison evidence that depended on it.
- [ ] The migration record names both snapshot identities and the reason, and is queryable afterwards.
- [ ] Affected work cannot advance until it has been revalidated under the new snapshot.

## Blocked by

- `config-and-snapshot#04` — snapshot capture and identity, without which there is nothing to migrate between.
- `execution-core#02` — operator-channel derivation (`operator_channel_required`) and the approval record family.
- `execution-core#05` — the gate record family and the `pending` gate state that affected gates return to.
