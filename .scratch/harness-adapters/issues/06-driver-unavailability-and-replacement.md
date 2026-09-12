# Driver unavailability, Infrastructure Retry, and explicit replacement

Type: issue
Status: ready-for-agent
Slice: harness-adapters#06
Spec: [`../spec.md`](../spec.md) (spec 10, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/harness-adapters/spec.md`](../spec.md)

## What to build

Treat driver unavailability as an infrastructure failure rather than as a reason to improvise. Preserve the work, spend from the Infrastructure Retry allowance with increasing backoff on an injected clock, and on exhaustion block the execution with the gate unapproved. Gantry never substitutes another harness, model, gateway or endpoint automatically, because a different driver can have a different data egress destination and the operator never agreed to it. The Correction Budget is untouched throughout. Classify permanent failures — invalid credentials, a missing binary, a configuration error — as blocking immediately, without spending the allowance on something only the operator can fix.

Make driver replacement an explicit operator-channel action. It updates the Execution Rule Snapshot, requires the new driver's Integration Capability declaration to be validated, requires egress authorization for the new destination, and invalidates the validations affected by the change. Before any replacement dispatch, the prior assignment and any uncertain operations are reconciled, so that a driver failure cannot turn into duplicate work or duplicate mutations. The validated-declaration check is made against the Integration Capability shape that `harness-adapters#02` owns; build against that shape rather than serializing behind it.

## Acceptance criteria

- [ ] Driver unavailability preserves the assignment, consumes Infrastructure Retry with increasing backoff on the injected clock, and on exhaustion blocks without changing driver; the Correction Budget is untouched.
- [ ] A permanent credential failure blocks immediately and spends no Infrastructure Retry.
- [ ] Driver replacement attempted through an agent channel is rejected as requiring the operator channel.
- [ ] Replacement with an unvalidated capability declaration, or to a destination with no matching egress allowance, is rejected.
- [ ] A replacement dispatch is refused until the prior assignment and any uncertain operations are reconciled, so no duplicate work is produced.

## Blocked by

- `harness-adapters#01` — the `HarnessAdapter` interface and the injected adapter port whose dispatch fails when a driver is unavailable.
- `execution-core#06` — the Infrastructure Retry allowance, the infrastructure-versus-permanent failure classification, and Operation Reconciliation for uncertain operations.
- `config-and-snapshot#05` — Execution Rule Snapshot update and the invalidation of affected approvals on replacement.
- `data-handling#07` — driver-change egress reauthorization and the egress audit trail for the new destination.
