# Scripted walkthrough: Correction Attempt and the entropy regression block

Type: issue
Status: ready-for-agent
Slice: demo-mode#06
Spec: [`../spec.md`](../spec.md) (spec 07, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/demo-mode/spec.md`](../spec.md)

## What to build

Extend the walkthrough with the two PBIs that show what the tool is actually for. The second PBI's initial gate evaluation produces findings, one Correction Attempt is dispatched and consumed, revalidation passes, and integration proceeds — with the projection showing the attempt count moving from zero to one, so the Correction Budget is visible rather than described.

The third PBI's Entropy Gate blocks on a Quality Regression present in the Merge Candidate and absent from the current target, and its projection names the concrete finding by rule and location rather than reporting a score. The walkthrough deliberately ends with a blocked PBI in the final state: a demo where everything passes teaches the wrong thing about what Gantry does, so a walkthrough that goes all green is a test failure.

This slice consumes the fixture plan agreed at the start of `demo-mode#05` — the PBI list, dependency edges, and criterion identities — and treats it as fixed rather than renegotiating it.

**Scheduling note.** Unlike `#01`–`#04`, this slice encodes concrete state sequences rather than interface shapes. Do not start it until `git-integration`'s issues exist, or the expected sequences will have to be rewritten.

## Acceptance criteria

- [ ] The second PBI consumes exactly one Correction Attempt; the projection shows the count transition and the initial evaluation consumes none.
- [ ] The second PBI reaches `integrated` after revalidation.
- [ ] The third PBI's gate result is `failed` on a differential regression, and the projection identifies the finding by rule and location rather than by an aggregate value.
- [ ] The demo's final state includes at least one blocked PBI; a walkthrough where everything passes fails the test.
- [ ] Re-running the walkthrough from a fresh fixture produces an identical sequence of Execution States.

## Blocked by

- `demo-mode#02` — the provisioned fixture, the registered demo unit, and `demo.reset` for the fresh-fixture re-run.
- `demo-mode#03` — the stub harness drivers and the scripted correction envelope.
- `demo-mode#04` — the stub check adapters and the scripted candidate-versus-target finding sets.
- `execution-core#05` — gate state and Correction Budget accounting, so the attempt count transition is visible on the projection.
- `entropy-gate#01` — the gate decision record and differential classification of a Quality Regression.
- `entropy-gate#06` — the correction loop: subject derivation, attempt accounting, and exhaustion.
- `verification-adapters#01` — Comparison Evidence normalization and the problem-identity rule the differential comparison matches on.
- `pbi-execution-loop#02` — dispatch scheduling.
- `pbi-execution-loop#05` — result handling and correction dispatch.
- `git-integration#03` — local merge for the second PBI's integration after revalidation.
