# Egress audit trail and driver-change reauthorization

Type: issue
Status: ready-for-agent
Slice: data-handling#07
Spec: [`../spec.md`](../spec.md) (spec 04, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/data-handling/spec.md`](../spec.md)

## What to build

The record that lets an audit answer *what* was sent and not only *where*. Each dispatch records its resolved driver, its destination, the provider identity for a remote destination, and the payload classes it carried.

The matrix is captured in the Execution Rule Snapshot, so a change applies to new executions rather than to work already in flight. Changing a role's driver invalidates the prior egress authorization and blocks dispatch until reauthorized, because the data boundary changed even though the role did not.

The enforcement boundary is stated in the projection rather than implied: coverage is Gantry-mediated dispatch, not every action a Host Harness can take through its own channels.

## Acceptance criteria

- [ ] Every dispatch record names its resolved driver, destination, provider identity where remote, and the payload classes carried.
- [ ] A remote destination without a recorded provider identity is rejected rather than recorded as anonymous.
- [ ] The matrix in effect for an in-flight execution is the one captured in its snapshot, not the current configuration.
- [ ] Changing a role's driver blocks the next dispatch with a rejection naming reauthorization, and a fresh authorization unblocks it.
- [ ] The state projection carries the enforcement-boundary statement, so no surface can present Gantry-mediated egress control as control over all harness traffic.

## Blocked by

- `data-handling#06` — the egress matrix, its resolution, and the dispatch enforcement point these records describe.
- `config-and-snapshot#04` — the Execution Rule Snapshot capture that freezes the egress matrix for an in-flight execution.
- `harness-adapters#06` — the explicit driver replacement flow that triggers egress reauthorization.
