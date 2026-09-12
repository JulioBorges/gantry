# Settings screen

Type: issue
Status: ready-for-agent
Slice: dashboard#06
Spec: [`../spec.md`](../spec.md) (spec 17, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/dashboard/spec.md`](../spec.md)

## What to build

Both configuration layers editable from forms, written through the same `ConfigStore` and the same whole-document validation every other interface uses. The screen displays which layer supplies each effective value, previews each role's resolved command live, and badges roles that are never invoked as dead configuration — all read from the store rather than recomputed here, because the form must not become a second source of configuration truth.

No field accepts a secret value. Credential fields accept environment variable names rather than values, which is what makes the screen safe to screen-share. Sections follow the specified set: harness and host, roles, gates, Git workflow, context limits, execution capacity, repository readiness, and data handling. A global-layer write requires a token carrying `globalSettings: true`; a repository-scoped token cannot reach it.

Test seam: validation, layering, backup, secret rejection, and dead-configuration computation are `config-and-snapshot`'s behavior and are tested there, so this slice gets one parity test per write endpoint. The dashboard-owned part is specific: scope enforcement on the global layer, and that the form cannot construct a request carrying a secret value.

## Acceptance criteria

- [ ] A write with any invalid field is rejected as a whole and no file is written; a valid write produces a `.bak` sibling of the target layer's previous file.
- [ ] A repository-layer write attempting to raise a global limit is rejected with the store's rejection code, surfaced by code.
- [ ] Field provenance, resolved role commands, and dead-configuration badges all appear in the Settings projection and are sourced from the store.
- [ ] No form field accepts a secret-shaped value; credential inputs are validated as environment variable names and never as values.
- [ ] A repository-scoped token cannot write the global layer; a `globalSettings` token cannot advance an execution.
- [ ] Each write endpoint produces exactly one core invocation, proven by one parity test.

## Blocked by

- `dashboard#02` — the capability token and the `globalSettings` scope dimension that gates global-layer writes.
- `config-and-snapshot#01` — `ConfigStore` layering, the effective document, per-field provenance, and the `config.read` operation.
- `config-and-snapshot#02` — whole-document validation and secret rejection.
- `config-and-snapshot#03` — the `config.write` operation with per-layer write authorization and the `.bak` on save.
- `config-and-snapshot#07` — resolved role command computation and the dead-configuration determination the badges display.
