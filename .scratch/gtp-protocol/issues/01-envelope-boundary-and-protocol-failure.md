# Envelope boundary, extensions, and Protocol Failure

Type: issue
Status: ready-for-agent
Slice: gtp-protocol#01
Spec: [`../spec.md`](../spec.md) (spec 03, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/gtp-protocol/spec.md`](../spec.md)

## What to build

The common identity layer carried by every task and every result envelope, and the fixed validation order at the boundary: protocol version, then common identities, then the current-assignment check through the operation core, then the role payload. Alongside it, the forward-compatibility rule: unknown keys are lifted into `extensions` and persisted verbatim rather than left inline, while a known field of the wrong type is always a violation.

```ts
// the decision, not the whole type: validation order is positional, and version is a major marker
gtpVersion: "1";            // additive minor changes do not move it
ownershipGeneration: number; // checked before the payload is interpreted at all
extensions?: Record<string, unknown>; // preserved verbatim, never interpreted
```

Envelopes are stored append-only under their assignment and iteration, and every dispatch and every result writes a telemetry event in the same transaction as the transition it evidences. Protocol Failure lands here as a persistent condition on the assignment, with its full class taxonomy: it preserves the agent's work and the raw submission, requires no questions from the agent, and is classified as protocol so it never consumes the infrastructure retry allowance.

A single minimal builder payload exists only so the dispatch-and-submit round trip is demoable end to end; the real role payloads arrive in `gtp-protocol#02` and `gtp-protocol#03`. Two of the six Protocol Failure classes are declared here but raised elsewhere — `role_mismatch` by `gtp-protocol#02` and `criteria_mismatch` by `gtp-protocol#05`. That is deliberate, not an omission: the taxonomy is defined once here so those slices fan out from this one instead of chaining behind a separate Protocol Failure slice.

## Acceptance criteria

- [ ] A dispatch returns a task envelope carrying every common identity — execution, unit, assignment, ownership generation, role, correlation, rule snapshot, plan version — and a dispatch missing any of them is refused before an agent is launched.
- [ ] A result whose common identities reference a different execution or plan version is rejected as `identity_mismatch` without its payload being interpreted; a result for an assignment never dispatched is the same class.
- [ ] A result carrying a stale ownership generation is stored and rejected as `stale_generation` with the state projection unchanged.
- [ ] Unknown fields survive a store-and-read round trip inside `extensions`; a known field with a wrong type is rejected as `malformed_result` with the raw submission retained.
- [ ] A dispatch that ends with exit code zero and no result is `missing_result`: the work is preserved, nothing advances, and the infrastructure retry allowance is unchanged.
- [ ] No Protocol Failure class requires `questionsForOperator`, and every class is readable from the audit trail with its cause.
- [ ] Iteration N+1 envelopes do not overwrite iteration N; both remain retrievable for the same assignment.

## Blocked by

- `execution-core#01` — provides the operation core `invoke` seam, the `Rejection` code set, and atomic acceptance (transition, receipt and audit in one transaction).
- `execution-core#03` — provides the `pbi.dispatch` operation shell and the PBI Execution Ownership generation and supersession rule.
- `execution-core#04` — provides the `pbi.submitResult` operation shell and stale assignment rejection.
- `data-handling#01` — provides the redaction sink interface the retained envelope record must write through.
- `config-and-snapshot#04` — provides the Execution Rule Snapshot identity bound on every envelope.
- `slicing-and-approval#01` — provides the plan version identity bound on every envelope.
