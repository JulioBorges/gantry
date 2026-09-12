# Execution Cancellation, Resumption, Cleanup Authorization, and runtime compatibility

Type: issue
Status: ready-for-agent
Slice: execution-core#08
Spec: [`../spec.md`](../spec.md) (spec 01, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/execution-core/spec.md`](../spec.md)

## What to build

Implement `execution.cancel`, `execution.resume`, `cleanup.propose`, `cleanup.authorize`, and `execution.migrateRuntime`. Cancellation stops new dispatch, marks the execution cancelled, and enqueues reconciliation of active assignments and in-flight operations while deleting nothing, closing no Pull Request, reverting no commit, and resetting no branch.

Resumption is operator-only, requires every `unknown` operation and every active assignment reconciled before progressing, reacquires current ownership, retains budgets, approvals, and the Execution Rule Snapshot, and never issues a speculative duplicate dispatch.

Cleanup is two steps: `cleanup.propose` returns a manifest of the exact local paths, branches, provider objects, and evidence records affected plus the dependency and pending-operation checks it ran, and `cleanup.authorize` is operator-only, references a specific manifest, and is refused if anything changed since the proposal or if any active execution or unresolved operation still depends on the artifacts. Resumption outside the declared engine and protocol compatibility range is rejected `incompatible_runtime` with the execution preserved, and `execution.migrateRuntime` retains the prior version provenance and marks affected evidence and approvals for revalidation.

## Acceptance criteria

- [ ] After cancellation, branches, worktrees, Pull Requests, evidence, and receipts are all still present and byte-identical, and no new dispatch is accepted.
- [ ] A cancelled execution cannot reach `running` by any path other than `execution.resume` from the operator channel.
- [ ] Resumption with an unreconciled `unknown` operation is rejected; after reconciliation it succeeds, retains the Correction Budget and rule snapshot, and the fake harness driver records no duplicate dispatch.
- [ ] `cleanup.authorize` referencing a stale manifest is refused, as is one whose artifacts a live execution or unresolved operation still depends on.
- [ ] After an authorized cleanup, the records needed to explain the execution and its external effects remain queryable through `audit.query`.
- [ ] Resumption under an out-of-range engine or protocol version is rejected `incompatible_runtime` with the execution intact; a migration records the prior version and flags affected approvals for revalidation.

## Blocked by

- `execution-core#06` — the Operation Reconciliation contract that cancellation enqueues and that both resumption and cleanup consult before proceeding.
- `execution-core#02` — the operator channel and provenance rule, plus the approval records resumption retains and migration flags for revalidation.
