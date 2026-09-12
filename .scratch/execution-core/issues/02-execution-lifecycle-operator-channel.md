# Execution lifecycle, operator channel provenance, and version-bound Planning Approval

Type: issue
Status: ready-for-agent
Slice: execution-core#02
Spec: [`../spec.md`](../spec.md) (spec 01, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/execution-core/spec.md`](../spec.md)

## What to build

Implement the execution state machine's entry path — `initializing` to `awaiting_plan_approval` on rule snapshot capture, to `running` on a version-bound operator approval — via `execution.create`, `plan.propose`, `plan.approve`, and `plan.amend`.

The core derives actor kind from the transport channel and never accepts it as an agent-supplied assertion: the `cli` channel may assert operator only for an interactive operator session, the `dashboard` channel only with a valid Dashboard Capability Token scoped to its session and unit, and the `mcp` channel never. The set of operator-only operations is driven from a table so a later-added one cannot be forgotten.

Every approval record stores artifact identity, content hash, actor provenance, channel, timestamp, and the governing Execution Rule Snapshot identity, and a changed content hash invalidates the approval. The execution record also captures the engine and GTP protocol versions that govern it.

## Acceptance criteria

- [ ] An `mcp`-channel request for `plan.approve`, `plan.amend`, `merge.confirmLocal`, `correction.grantAttempts`, `cleanup.authorize`, or `execution.migrateRuntime` is rejected `operator_channel_required` for every one of them, driven from a table so a later-added operator-only operation cannot be forgotten.
- [ ] A `dashboard`-channel approval without a valid capability token, or with a token scoped to a different unit, is rejected; with a valid scoped token it is accepted and the provenance is recorded.
- [ ] Approving an artifact, editing it, then acting on the approval yields `approval_version_mismatch`.
- [ ] An execution cannot leave `initializing` without a captured rule snapshot reference, and cannot reach `running` without a recorded operator approval bound to the approved artifact version.
- [ ] `state.project` reports the execution state, the approval provenance and channel, and the governing snapshot identity, with no field that could hold a credential value.

## Blocked by

- `execution-core#01` — the `invoke` seam, the atomic transition primitive, the rejection vocabulary, and the state builders.
- `config-and-snapshot#04` — Execution Rule Snapshot capture and identity, the reference this slice stores on the execution.
- `data-handling#01` — normalized content hashing (line-ending normalization) for approval content hashes.
- `slicing-and-approval#01` — the plan version hash definition the approval binds to.
- `dashboard#02` — the Dashboard Capability Token verification interface for `dashboard`-channel provenance.
