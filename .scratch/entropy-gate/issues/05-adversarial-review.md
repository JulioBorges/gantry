# Adversarial review: ordering, add-only, and failure behavior

Type: issue
Status: ready-for-agent
Slice: entropy-gate#05
Spec: [`../spec.md`](../spec.md) (spec 13, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/entropy-gate/spec.md`](../spec.md)

## What to build

The optional Adversarial Review layer, which never runs before the deterministic layer. The order is fixed: deterministic first, always, as the floor. When the configured mode enables review, the critic receives a task envelope containing the PBI, the constitution and ADR references, the diff reference, and the deterministic findings already produced. Its result may only add findings in the four allowed classes. **The accepted payload shape has no field capable of clearing, downgrading, or approving a deterministic finding** — "may only add" is enforced by the shape itself, not by a runtime check someone could forget, and the test for it demonstrates the absence of the field rather than exercising a guard.

A critic `blocker` fails the gate; a critic `warning` records an advisory event only. When review is required, a valid review with no blockers is required *in addition to* the deterministic layer passing: an unavailable critic, a failed execution, or a missing or malformed result leaves the gate awaiting review with the failure recorded, and there is no fallback to a static-only decision. A critic infrastructure failure spends the infrastructure retry allowance; a malformed result is a Protocol Failure and spends neither the infrastructure allowance nor a Correction Attempt.

This slice also owns **critic requirement resolution**: review is required when the global adversarial mode enables it, *or* automatically when the candidate modifies test files covering approved criteria — the one condition that overrides a global `static` setting for that PBI, because the operator opted into a static-only delivery review, not into an unreviewed change to the verification itself. With the critic disabled, review is deterministic-only, and the Requirement Critic in `spec-validation` is unaffected by this setting: the two reviewers review different subjects at different times.

## Acceptance criteria

- [ ] The deterministic layer runs first in every configuration; a clean deterministic result plus a critic blocker fails the gate, and a critic warning records an advisory event without blocking.
- [ ] A critic result cannot clear or downgrade a deterministic finding, demonstrated by the absence of any such field in the accepted payload rather than by a runtime check.
- [ ] An absent, malformed, or failed critic leaves the gate awaiting review with the failure recorded; no path produces a passing static-only decision when the critic is required.
- [ ] A critic infrastructure failure spends the infrastructure allowance; a malformed result is handled as a Protocol Failure and spends neither the infrastructure allowance nor a Correction Attempt.
- [ ] A candidate modifying test files that cover approved criteria requires the critic even when the global mode is static; a candidate touching no such test file does not trigger the escalation.
- [ ] With the critic disabled, review is deterministic-only and the Requirement Critic in `spec-validation` is unaffected by this setting.

## Blocked by

- `entropy-gate#01` — provides the gate decision record, including the field the adversarial submission and its added findings are recorded in.
- `entropy-gate#04` — provides the covered test-change set (which candidate-modified test files cover which approved criteria) that the automatic escalation keys on.
- `gtp-protocol#03` — provides the `adversarial_critic` task and result contracts, restricted to the four finding classes and shaped with no clearing or downgrading field.
- `gtp-protocol#01` — provides Protocol Failure semantics, which are not reclassifiable as infrastructure.
- `execution-core#06` — provides the Infrastructure Retry allowance and the failure classification table.
- `execution-core#05` — provides the `pending_review` gate state for a required-but-unavailable critic.
- `config-and-snapshot#01` — provides the `gates.adversarial.mode` setting in the `gates.*` configuration section.

## Notes

`entropy-gate#04` is the one real blocking edge into this slice, and only for the automatic escalation. An agent can build critic ordering, add-only enforcement, severity handling, and failure behavior against the global mode alone, and land the escalation criterion once `#04` is in.
