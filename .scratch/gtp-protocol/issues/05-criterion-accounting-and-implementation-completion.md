# Criterion accounting and Implementation Completion

Type: issue
Status: ready-for-agent
Slice: gtp-protocol#05
Spec: [`../spec.md`](../spec.md) (spec 03, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/gtp-protocol/spec.md`](../spec.md)

## What to build

The rule that turns a builder's completion claim into the `implementation_complete` state, and no further. Every criterion identity the assigned PBI declares must appear in the result exactly once, every one must be `completed`, and each must carry an evidence reference naming the verification command that covers it and the revision it was observed on.

Gantry then re-executes the PBI's approved mandatory verification commands against the delivered revision through the check adapter and uses its own result. The agent's verification records are retained as context and as a discrepancy signal, never as the basis for completion; a disagreement between the agent's reported pass and Gantry's observed failure is recorded as a verification-integrity finding. Completion advances the PBI to `in_gates` and nothing further. The check adapter is consumed here as an injected fake returning scripted verification results, so this wave-0 slice exercises the interface without waiting on the real adapter set.

This slice and `gtp-protocol#07` run in parallel. `gtp-protocol#07` records a scope violation as a finding; this slice owns the completion rule that consults that record. Whichever of the two lands second wires the consultation and carries the "out-of-scope change refuses completion" scenario.

## Acceptance criteria

- [ ] A valid builder result with every criterion completed and Gantry's own mandatory test run passing leaves the PBI in `in_gates`, not merge-authorized.
- [ ] A single `pending` criterion refuses completion even when the test run is green.
- [ ] All criteria completed with Gantry's own test run failing refuses completion.
- [ ] An agent reporting a pass where the check adapter is scripted to fail refuses completion and records a verification-integrity finding.
- [ ] A criterion identity absent from the result, and a criterion identity the PBI does not declare, are both `criteria_mismatch`.
- [ ] A completed criterion with no evidence reference refuses completion.

## Blocked by

- `gtp-protocol#02` — provides the builder result payload with per-criterion status and evidence references.
- `gtp-protocol#04` — provides `complete` as a claim rather than a transition.
- `verification-adapters#01` — provides the check adapter signature: run one approved verification command against a named revision and return a normalized pass/fail plus findings. Consumed here as an injected fake.
- `config-and-snapshot#01` — provides the approved mandatory verification command set.
- `spec-validation#02` — provides the criterion identity rule (required, never generated, stable).
