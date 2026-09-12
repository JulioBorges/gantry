# Allowed scope and governance-path protection

Type: issue
Status: ready-for-agent
Slice: gtp-protocol#07
Spec: [`../spec.md`](../spec.md) (spec 03, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/gtp-protocol/spec.md`](../spec.md)

## What to build

Every mutating task declares its allowed scope as path patterns, and a result reporting changes outside that scope is a scope violation: the result is retained, the violation is recorded as a finding, and the PBI does not complete.

Protected governance paths come from the repository's effective Artifact Location Mapping rather than from hardcoded directory names, so relocating the governance directory moves the protection with it. An ordinary assignment reporting a change to one of those paths is a violation. An assignment issued under an approved Governance Baseline Transition carries an explicit permission naming those paths, so the protection does not block the work whose entire purpose is to change them; absent that permission, the change is a violation, and a permission naming one path never authorizes another.

This slice and `gtp-protocol#05` run in parallel. This slice records the violation as a finding; `gtp-protocol#05` owns the completion rule that consults that record. Whichever of the two lands second wires the consultation and carries the "out-of-scope change refuses completion" scenario.

## Acceptance criteria

- [ ] A result reporting a changed path outside the task's allowed scope records a scope violation, retains the result, and leaves the PBI short of `implementation_complete`.
- [ ] A result reporting a change to a protected governance path under an ordinary assignment is a violation.
- [ ] The same result under an assignment carrying explicit baseline-transition permission naming those paths is accepted.
- [ ] Protected paths are resolved from the Artifact Location Mapping, proven by a fixture that relocates the governance directory and sees protection follow it.
- [ ] A baseline-transition permission naming path A does not authorize a change to path B.

## Blocked by

- `gtp-protocol#02` — provides the builder task's allowed scope and the builder result's reported changed paths.
- `repository-readiness#01` — provides the Artifact Location Mapping schema that resolves protected governance paths.
- `baseline-transitions#01` — provides the governance-path permission carried in a transition declaration.
- `verification-adapters#01` — provides the normalized finding shape used to record the violation.
