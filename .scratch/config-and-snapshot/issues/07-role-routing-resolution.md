# Role routing resolution and dead configuration

Type: issue
Status: ready-for-agent
Slice: config-and-snapshot#07
Spec: [`../spec.md`](../spec.md) (spec 02, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/config-and-snapshot/spec.md`](../spec.md)

## What to build

Resolution of each configured role to the concrete command that will actually run, previewable before anything is dispatched, plus refusal of a dispatch whose role routing cannot be resolved — returning setup guidance so the host harness reports a fixable problem instead of failing obscurely. The reading transport is `gantry config`, which renders the resolved command per role.

Alongside it, the store computes from execution history which configured roles have never been invoked and which verification commands have never produced evidence, and exposes that on its read surface. Dead-configuration reporting is advisory and never blocks anything; it exists because a role configured with a typo is silent until the moment it matters. This is the slice that makes configuration observable rather than merely stored.

## Acceptance criteria

- [ ] The resolved command for each configured role is returned by a read operation and rendered by the CLI before any dispatch occurs.
- [ ] A dispatch whose role routing cannot be resolved is refused with a typed rejection carrying setup guidance naming the unresolved role.
- [ ] A role configured but never invoked, and a verification command that has never produced evidence, both appear in the dead-configuration report.
- [ ] The dead-configuration report never causes a rejection, a blocked state, or a refused transition in any test.
- [ ] The report is derived from execution history rather than from static configuration inspection alone.

## Blocked by

- `config-and-snapshot#01` — the host and role routing configuration section and the read surface the resolution is exposed on.
- `execution-core#03` — the dispatch operation to attach the unresolved-routing refusal to.
- `machine-setup#02` — the harness compatibility matrix as data, used to resolve a role to a driver.
