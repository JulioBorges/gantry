# PBI lint rules and breakdown coverage

Type: issue
Status: ready-for-agent
Slice: slicing-and-approval#02
Spec: [`../spec.md`](../spec.md) (spec 09, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/slicing-and-approval/spec.md`](../spec.md)

## What to build

Implement `gantry lint-pbi` as an operation over a persisted plan proposal, evaluating the declared rules as data with stable rule identities and emitting findings in the shared structured shape. Per-PBI: `PBI-BEHAVIOR`, `PBI-CRITERIA-ID`, `PBI-VERIFICATION`, `PBI-CRITERIA-COVERED` and `PBI-STORY-COVERAGE` as blockers, and `PBI-FILE-COUNT` as the sole warning, carrying the threshold value in the message. At the breakdown level: every approved user story is covered by at least one PBI.

The file-count threshold is a **configuration field under context policy**, owned by `config-and-snapshot#01` and read from the effective configuration document — not a hardcoded constant. Reading it from configuration is what makes the warning message honest about which threshold triggered it.

Test duration is not a rule and no rule may reference it. `PBI-BUDGET` and `PBI-DEPS-RESOLVABLE` belong to slices `slicing-and-approval#03` and `slicing-and-approval#04` and are absent here; the rule set is data with stable identities, so adding them later is additive.

## Acceptance criteria

- [ ] A PBI whose criteria do not trace to spec criterion identifiers fails `PBI-CRITERIA-ID`; a criterion with no covering verification entry fails `PBI-CRITERIA-COVERED`; a PBI with no verification definition fails `PBI-VERIFICATION`.
- [ ] A PBI with slow but defined verification passes, and no rule identity or message references duration.
- [ ] A PBI touching seven files produces the `PBI-FILE-COUNT` warning with the threshold visible, still passes lint, and remains eligible for approval.
- [ ] A breakdown leaving an approved user story uncovered fails the breakdown-level coverage rule; a PBI covering no story fails `PBI-STORY-COVERAGE`.
- [ ] Lint results are persisted against the plan version they were evaluated on, and lint success alone produces no approval record.
- [ ] `gantry lint-pbi` is one parity test proving delegation.

## Blocked by

- `slicing-and-approval#01` — provides the persisted plan proposal, the `ProposedPbi` shape, and the plan version identity that lint results are recorded against.
- `config-and-snapshot#01` — provides the PBI file-count threshold and the Initial Context Budget values under context policy in the effective configuration document.
- `repository-readiness#04` — provides the approved verification command reference (`ApprovedCommandRef`) under Verification Command Approval.
