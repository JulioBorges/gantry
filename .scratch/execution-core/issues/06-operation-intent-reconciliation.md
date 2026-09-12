# Operation intent, Operation Reconciliation, and Infrastructure Retry

Type: issue
Status: ready-for-agent
Slice: execution-core#06
Spec: [`../spec.md`](../spec.md) (spec 01, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/execution-core/spec.md`](../spec.md)

## What to build

Implement the external-operation state machine via `operation.declareIntent`, `operation.recordOutcome`, and `operation.reconcile`. The core refuses to issue a mutation without a persisted intent carrying class, target, candidate, authorization reference, and `requestId`. An uncertain or lost response becomes `unknown` and blocks with `reconciliation_required`; only `reconciled_not_performed` permits reissuing, and `reconciled_completed` records the outcome from observation without repeating the effect.

```
intended ──> in_flight ──> confirmed
                       └─> failed
                       └─> unknown ──> reconciled_completed
                                   └─> reconciled_not_performed
```

Layer the explicit failure classification over this — infrastructure, protocol, deterministic finding, permanent — where only the infrastructure class draws on a separate allowance of three automatic retries with exponential backoff and jitter on the injected clock, a Protocol Failure is never retried as infrastructure, and a permanent authorization or configuration failure blocks immediately. Exhausting the infrastructure allowance leaves the execution `blocked` with the gate unapproved, distinct from an agent-reported blocked result.

## Acceptance criteria

- [ ] A mutation attempted without a persisted intent is refused, and a crash simulated between intent and outcome leaves a reconcilable intent rather than a silent gap.
- [ ] An operation whose response is lost reads `unknown` and blocks `reconciliation_required`; reconciling to `reconciled_completed` records the outcome without reissuing, and to `reconciled_not_performed` permits exactly one reissue.
- [ ] Three Infrastructure Retries occur at increasing intervals on the injected clock, the fourth is rejected `infrastructure_budget_exhausted`, and the Correction Budget counter is untouched throughout.
- [ ] Each of the four failure classes routes to its specified behavior, asserted one case per class; a malformed result is never retried and a permanent credential failure never consumes an attempt.
- [ ] An execution blocked by infrastructure exhaustion is distinguishable in `state.project` from one in `awaiting_operator`, and no gate is approved in either case.
- [ ] No test sleeps; all backoff and expiry assertions are driven by the injected clock.

## Blocked by

- `execution-core#01` — the `invoke` seam, the atomic transition primitive, the injected clock, and the state builders.
- `config-and-snapshot#01` — the Infrastructure Retry allowance and the backoff base.
