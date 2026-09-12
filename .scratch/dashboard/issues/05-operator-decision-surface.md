# Operator decision surface

Type: issue
Status: ready-for-agent
Slice: dashboard#05
Spec: [`../spec.md`](../spec.md) (spec 17, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/dashboard/spec.md`](../spec.md)

## What to build

The screen where the operator acts, with every action a core operation carried by an in-scope capability token. A pending decision displays the exact proposal identity and version, so the operator approves what they actually read and an approval against changed content surfaces the core's rejection rather than quietly succeeding. Plan approval, local merge confirmation with the target revision, merge candidate, and governing rule snapshot named on the confirmation itself, and execution resume and cancel all become mutating endpoints. The one-click demo pipeline re-run control lives here too, since it is an operator mutation like the others.

Each endpoint constructs an `OperationRequest` with a stable `requestId` and delegates. The server caches no approval and holds no decision state. Core rejection codes reach the operator as codes, not flattened into a generic failure message.

**Considered and declined, so it is not re-proposed:** an out-of-band confirmation code printed by the CLI and required before an irreversible mutation. It would tie the action to terminal access rather than browser access, but it adds friction to exactly the path the Settings screen exists to make friction-free, and the local attacker it would stop can generally read the code too. If the local threat model changes, this is the first mitigation to revisit.

Test seam: almost entirely the delegated side. One parity test per mutating endpoint and nothing more — the semantics of approval, merge confirmation, and resumption belong to their owning specs and are tested at the core. The dashboard-owned part is narrow: that the proposal identity and version reach the screen, and that the token check gates each endpoint.

## Acceptance criteria

- [ ] Each mutating endpoint produces exactly one core invocation with `channel: "dashboard"` and `actor.kind: "operator"`, proven by one parity test per endpoint.
- [ ] A pending decision renders the proposal identity and version taken from the projection; approving a proposal whose content changed since it was rendered surfaces the core's `approval_version_mismatch` rejection rather than succeeding.
- [ ] The local merge confirmation displays the target revision, the merge candidate, and the governing rule snapshot before the confirming control is enabled.
- [ ] The same requests without a valid in-scope token are rejected and produce no core invocation.
- [ ] The demo re-run control is offered only on a unit projecting `mode: "demo"`.
- [ ] Core rejection codes are surfaced to the operator by code, not translated into a generic failure message.

## Blocked by

- `dashboard#02` — the capability token, its two-dimensional scope enforcement, and the origin axes every mutating endpoint here passes through.
- `dashboard#03` — the projection the decision surface reads proposal identity, version, and `mode` from.
- `slicing-and-approval#01` — the plan version identity and proposal identity the pending decision renders and approval is bound to.
- `git-integration#03` — the `merge.confirmLocal` shape carrying unit, target revision, candidate revision and snapshot identity, which this confirmation surface delegates to.
- `git-integration#02` — the merge candidate and current target revision pair the confirmation displays.
- `execution-core#08` — the `execution.resume` and `execution.cancel` operations.
- `demo-mode#02` — the demo pipeline re-run operation the one-click control invokes.
