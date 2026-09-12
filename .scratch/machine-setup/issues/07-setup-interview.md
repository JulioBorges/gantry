# The conversational setup interview

Type: issue
Status: ready-for-agent
Slice: machine-setup#07
Spec: [`../spec.md`](../spec.md) (spec 05, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/machine-setup/spec.md`](../spec.md)

## What to build

Package the interview as a `gantry-*` skill that collects host and role routing, context policy values, capacity and budget values, Git workflow preferences, and data handling defaults, then writes them through the ConfigStore as a whole validated document — so a conversation producing an invalid combination is rejected with the field path rather than persisted.

The interview runs as an agent, so its channel can never assert operator actorhood. Plan approval, local merge confirmation, Verification Command Approval, Preparation Authorization, Cleanup Authorization, and snapshot migration are all unavailable to it and return the operator-channel rejection. Skipping the interview yields the approved defaults with no prompting.

The interview's substance is the configuration write path and the channel restriction, both testable through the core with no skill installed anywhere; this slice is deliberately not blocked on skill installation.

## Acceptance criteria

- [ ] An interview transcript producing a valid combination results in a configuration readable back through the core with those values.
- [ ] An invalid combination is rejected as a whole document with the offending field path, and nothing is persisted.
- [ ] Each of the six operator-only operations invoked through the interview's channel returns `operator_channel_required`, enumerated one test per operation.
- [ ] Skipping the interview produces exactly the approved defaults, compared against the defaults read directly from the ConfigStore.
- [ ] The interview writes no credential value and no Integration Capability claim.

## Blocked by

- `machine-setup#01` — the factory and the ConfigStore write path the interview persists through.
- `machine-setup#06` — the routing presets the interview offers.
- `execution-core#02` — the actor channel rule and the `operator_channel_required` rejection code.
