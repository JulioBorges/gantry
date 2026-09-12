# Stub harness drivers and scripted result envelopes

Type: issue
Status: ready-for-agent
Slice: demo-mode#03
Spec: [`../spec.md`](../spec.md) (spec 07, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/demo-mode/spec.md`](../spec.md)

## What to build

Implement the stub drivers against the same `HarnessAdapter` interface the real adapters implement — `dispatch`, `observe`, `requestStop`, `reconcile` — resolving a pre-recorded GTP result envelope from the assignment's role, PBI, and iteration. There is no parallel demo pipeline and no demo-only escape hatch on the interface: a demo run and a live run differ only in which driver is resolved, which is precisely what makes the demo evidence about the seam rather than a bypass of it.

Declare Integration Capability honestly. Context usage is `self_reported` sourced from the scripted envelope and never `measured`, because nothing is measuring anything; handoff is triggered by a scripted `needs_handoff` status rather than by an observed watermark; and no capability is declared that has no passing conformance probe behind it. A demo is exactly where an unearned guarantee would be most tempting to advertise, which is why this is an acceptance criterion and not a code comment.

Include the deliberately invalid scripted result so Protocol Failure handling has a source to exercise. Version the scripted envelopes with the package alongside the envelope schemas, and validate every scripted envelope against its role's result contract in the test suite, so that a change to the protocol breaks the demo in the same commit instead of leaving the shipped fixture quietly stale.

This slice depends only on the shape of its blockers' interfaces, so it can be picked up as soon as they land.

## Acceptance criteria

- [ ] The stub satisfies the `HarnessAdapter` type with no added methods and no demo-only escape hatch on the interface.
- [ ] Scripted envelopes are versioned with the package alongside the envelope schemas, and every one validates against its role's result contract; an envelope that does not fails the build, so a protocol change updates the demo in the same commit.
- [ ] Stub-reported context usage projects as `self_reported`; a test asserts `measured` never appears for a demo unit.
- [ ] `requestStop` returns an honest variant for a stub (never `stopped` with fabricated evidence), and `reconcile` returns a result derived from the scripted state.
- [ ] Response resolution is deterministic: the same role, PBI, and iteration yields the same envelope across runs and processes.

## Blocked by

- `harness-adapters#01` — the `HarnessAdapter` interface, driver resolution, dispatch provenance, `StopOutcome`, and `ReconciliationResult`.
- `harness-adapters#02` — the `IntegrationCapabilities` declaration and the conformance probes that must back every declared capability.
- `gtp-protocol#01` — the envelope boundary and extension rules the deliberately invalid scripted result violates.
- `gtp-protocol#02` — the builder task and result contract scripted envelopes validate against.
- `gtp-protocol#03` — the non-mutating role contracts for the spec authoring, slicing, and review envelopes.
- `gtp-protocol#04` — `GtpStatus`, status precedence, handoff continuity, and the `self_reported` versus `measured` context usage distinction.
- `gtp-protocol#06` — result submission identity and idempotency carried on scripted envelopes.
