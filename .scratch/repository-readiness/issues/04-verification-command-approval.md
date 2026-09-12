# Verification Command Approval, validation run and preexisting baseline

Type: issue
Status: ready-for-agent
Slice: repository-readiness#04
Spec: [`../spec.md`](../spec.md) (spec 06, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/repository-readiness/spec.md`](../spec.md)

## What to build

An operator-only approval operation that accepts an `ApprovedCommandProposal`, binds it to the Execution Rule Snapshot, and yields an `ApprovedCommandRef` that `verification-adapters` and `entropy-gate` later cite as the provenance of evidence. Any change to the command argv, working directory, environment references or declared effects invalidates the approval, invalidates the evidence the previous version produced, and requires reapproval.

After approval, each command is executed exactly once through an injected check adapter to validate that it runs and emits its expected report. A command that runs but emits no parseable report is `blocked`, not `satisfied`; a command that runs and reports findings is `satisfied`, with those findings recorded as the preexisting finding baseline the differential policy consumes. This distinction is what keeps existing debt from looking like a setup failure.

`declaredCoverage` travels with the ref and is surfaced wherever the check's evidence appears, so a Gitleaks-only configuration is never presented as security coverage.

## Acceptance criteria

- [ ] Approval from a non-operator channel is rejected with `operator_channel_required`; the MCP channel can read proposals but never approve.
- [ ] The approved ref records the snapshot identity, and mutating any of the four bound fields invalidates prior evidence and returns the item to `needs_approval`.
- [ ] A fake adapter emitting no parseable report yields a `blocked` item; a fake adapter emitting findings yields `satisfied` plus a persisted preexisting baseline distinguishable from a setup failure.
- [ ] `afkEligible` flips to true only on a fresh report where every required check is `satisfied`.
- [ ] `declaredCoverage` is present alongside the check's evidence in the state projection, asserted through a read operation.

## Blocked by

- `repository-readiness#03` — the `ApprovedCommandProposal` shape this operation approves.
- `execution-core#02` — operator-channel derivation and the `operator_channel_required` rejection, plus the approval record shape and its version-mismatch invalidation.
- `config-and-snapshot#04` — Execution Rule Snapshot identity the approved ref binds to.
- `config-and-snapshot#05` — the snapshot-bound evidence invalidation classification this slice applies on reapproval.
- `data-handling#01` — redaction sink enforcement interface and normalized content hashing for validation-run output.
