# Demo mode on the state projection and the cross-mode boundary tests

Type: issue
Status: ready-for-agent
Slice: demo-mode#01
Spec: [`../spec.md`](../spec.md) (spec 07, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/demo-mode/spec.md`](../spec.md)

## What to build

Carry `mode: "live" | "demo"` on the state projection returned by every operation outcome, so that any surface can render the simulated-evidence marker from data instead of from a flag a call site had to remember to pass. The immutable `mode` property on the Repository Execution Unit, the validated boundary predicate at the operation boundary, and the mode-boundary rejection code are **not** defined here: they are owned by `execution-core#01`, because the operation boundary is the enforcement point and retrofitting it there costs the same as retrofitting the redaction sink. This slice consumes them and must not re-declare them.

What this slice owns beyond the projection field is the proof that the marker travels on data. One CLI parity test renders output for a demo unit and asserts the simulated-evidence marker is derived from the projection's mode field rather than supplied by the caller; a projection for a demo unit that omits the field fails a test rather than rendering a silently unmarked run.

It also owns the demo-specific tests over the boundary — the demo-side exercise of the core's predicate. These assert from the outside that a registered demo unit keeps its marker, that an operation relating a demo-unit record to a live-unit record is refused by rejection code and never by message text, and that an approval recorded in a demo unit satisfies no authorization check in a live unit. This remains the slice everything else in the spec waits on in ordering terms, because the rest of the spec produces demo records and none of them are safe to produce before the boundary is provably in place.

## Acceptance criteria

- [ ] Registering a unit with mode `demo` persists the marker; a subsequent attempt to change a registered unit's mode is rejected.
- [ ] An operation relating a demo-unit record to a live-unit record is rejected with a mode-boundary rejection code, asserted by code and not by message text.
- [ ] An approval recorded in a demo unit does not satisfy any authorization check in a live unit.
- [ ] Every state projection for a demo unit carries `mode: "demo"`; a projection that omits it fails a test.
- [ ] One CLI parity test proves the simulated-evidence marker in rendered output is derived from the projection's mode field, not passed at the call site.

## Blocked by

- `execution-core#01` — the immutable `mode` property on the Repository Execution Unit, the cross-mode boundary predicate at the operation boundary and its rejection code, `unit.register`, unit identity derivation, and `state.project`.
- `execution-core#02` — the approval record whose reach across the mode boundary this slice asserts, and operator channel provenance.
