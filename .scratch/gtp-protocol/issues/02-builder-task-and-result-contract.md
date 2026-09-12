# Builder task and result contract

Type: issue
Status: ready-for-agent
Slice: gtp-protocol#02
Spec: [`../spec.md`](../spec.md) (spec 03, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/gtp-protocol/spec.md`](../spec.md)

## What to build

The builder branch of the role-discriminated union. The task states the PBI reference and version, the acceptance criteria with their stable identities, the approved verification commands, the allowed scope, and the continuity context when resuming after a handoff. It also states the required output contract inline, so a spawned agent knows the exact shape it must return without having to infer one.

The builder result carries per-criterion status with evidence references, the delivered revision, the reported changed paths, and the agent's own verification attempt records. Those records are retained as context only — they are never treated as establishing anything on their own.

A submitted payload whose role discriminant does not match the assignment's role is a `role_mismatch` Protocol Failure, detected before any interpretation of its content. `role_mismatch` is declared in the taxonomy from `gtp-protocol#01`; this slice is where it is first raised.

## Acceptance criteria

- [ ] A builder task envelope produced by dispatch contains every criterion identity the assigned PBI declares, the approved verification commands, and the allowed scope patterns.
- [ ] The task envelope states its required result contract, and a result conforming to it is accepted while one conforming to a different role's contract is not.
- [ ] A payload whose role discriminant differs from the assignment's role is rejected as `role_mismatch` with the submission retained.
- [ ] A builder result records the agent's verification attempts as context; the record is readable and is never treated as establishing anything on its own.
- [ ] A criterion status value outside the declared set is `malformed_result`, not a silently ignored field.

## Blocked by

- `gtp-protocol#01` — provides the common envelope layer, the validation order, and the Protocol Failure taxonomy this payload plugs into.
- `spec-validation#02` — provides the criterion identity rule (required, never generated, stable).
- `config-and-snapshot#01` — provides the approved verification command set carried in the task.
