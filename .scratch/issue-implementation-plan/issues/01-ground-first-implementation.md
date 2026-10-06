# Require a grounded technical plan before first implementation

Type: issue
Status: ready-for-agent
Slice: `issue-implementation-plan#01`
Spec: `.scratch/issue-implementation-plan/spec.md`
Created: 2026-10-06
User stories covered: 1–8, 11–12, 17, 21–22

## Parent

`issue-implementation-plan` — Spec in the local Markdown tracker.

## What to build

Deliver the complete per-Issue path from assigned checkout through one bounded read-only Research-and-Plan call, dedicated result validation, automatic handoff to a fresh Implementer, and existing Review/Critic verification. Inherit the effective Implement harness/model and initially preserve its configured effort; the next slice adds the approved high-effort policy. Include necessary routing prefactoring within this observable slice. Keep Spec decomposition Plan separate. Cite current behavior and reusable components, map every criterion to changes and tests, and target 500–1,000 tokens without padding or losing evidence. Retain results outside sanitized Run events. Report source/Spec conflicts for the operator before edits.

## Acceptance criteria

- [ ] A one-Issue workflow fixture proves assigned checkout → Technical Plan → separate TDD Implementer → independent Review and Critic, with the effective Implement harness/model preserved.
- [ ] Public result validation rejects a missing/invalid plan, nonexistent source references or missing criterion coverage; bounded Protocol Failure handling cannot release implementation on failure.
- [ ] A reported scope or contract conflict waits for the operator without changing code, Issue/Spec content, dependencies or acceptance criteria; an accepted plan advances without routine approval.
- [ ] Technical planning makes no checkout edits; an observed unexpected change refuses handoff and reports capability limitations honestly.
- [ ] Two independent Issue chains prove that one accepted plan can release implementation while the other is still planning, in their own assigned worktrees.
- [ ] Existing protocol/execution failure behavior preserves work, selected execution identity and correction counts; planning failures consume no Critic correction attempt.
- [ ] Native and manual workflow instructions use the same dedicated technical-plan contract and checkpoint; legacy decomposition results do not satisfy it.
- [ ] Plans include concrete changes, reusable behavior and tests rather than copied requirements; scope-neutral implementation adjustments are reported with a reason and criteria remain authoritative.

## Blocked by

- None

## Comments

Testing seams, four-Issue breakdown and dependencies approved for publication when the operator requested a PR to main on 2026-10-06. Implementation remains separately authorized; no criterion is complete.
