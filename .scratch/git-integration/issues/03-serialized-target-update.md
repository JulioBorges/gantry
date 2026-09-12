# Serialized target update, the Mutation Approval Boundary, and local-merge Operation Reconciliation

Type: issue
Status: ready-for-agent
Slice: git-integration#03
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

The local-merge delivery path end to end. Integration acquires the unit-scoped merge lease, re-verifies the target revision inside the serialized section, and only then updates the target — a target that moved is rejected rather than integrated on stale approval.

`merge.confirmLocal` is operator-only, carries unit, target revision, candidate revision and snapshot identity, and must immediately precede the mutation. A green gate, a prior plan approval, and a successful Pull Request preparation each fail to substitute for it.

The mutation persists its operation intent before the request, and a lost or uncertain response — including across a process restart — leaves the operation `unknown`, which blocks. Resolution consults authoritative Git state for that specific operation, records a confirmed completion without repeating it, and permits a retry only on a confirmed non-occurrence. This is the Git-side resolver of the same Operation Reconciliation contract that `git-integration#07` implements on the provider side; the two resolvers consult different authoritative sources but must not diverge in shape.

## Acceptance criteria

- [ ] Two in-process integrations against one unit serialize; the loser is rejected `lock_unavailable` or revalidates, and the target advances exactly once in real Git.
- [ ] A target moved between authorization and the serialized section is rejected with a typed code and the target commit is unchanged.
- [ ] A local merge without a preceding `merge.confirmLocal` is rejected; three separate tests show a passing gate, a plan approval, and a successful Pull Request preparation each failing to authorize it.
- [ ] A confirmation naming a stale target revision, candidate revision, or snapshot is rejected; a confirmation from the MCP channel is rejected `operator_channel_required`.
- [ ] A merge whose response is lost leaves an `unknown` operation that blocks; reconciliation against real Git state to "completed" records the outcome with no second merge commit, and to "not performed" permits exactly one retry that still requires valid authorization.
- [ ] A test asserts no branch other than the configured integration target is written — no promotion between long-lived branches, no hotfix automation.

## Blocked by

- `git-integration#02` — provides the prepared Merge Candidate and the authorization this path mutates under.
- `execution-core#07` — provides the repository-execution-unit merge lease and the `merge.confirmLocal` operation.
- `execution-core#06` — provides the operation intent record, the receipt, the unknown-outcome blocking rule and the Operation Reconciliation contract this slice implements Git-side.
- `execution-core#02` — provides the operator channel assertion and the `operator_channel_required` rejection.
