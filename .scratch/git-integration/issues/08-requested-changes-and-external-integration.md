# Requested changes, external integration, and Pull Requests closed without merge

Type: issue
Status: ready-for-agent
Slice: git-integration#08
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

An observed formal review requesting changes returns the PBI to correction eligibility within its *remaining* allowance, after being reconciled against current Pull Request state so a review against a superseded head revision is not replayed as a new request. Review text is untrusted feedback evaluated against the approved plan and governance, never instructions to execute; a request that would change behavior, contracts, criteria, dependencies or scope requires an operator-approved Plan Amendment.

Separately, a Pull Request merged outside Gantry is reconciled: the actually integrated changes and the resulting target revision are observed and recorded as an external integration rather than a Gantry-authorized merge, and dependents are released only after the applicable PBI criteria and Dependency Readiness are verified against the integrated content — a merged flag alone establishes nothing.

A Pull Request closed without merge pauses the PBI, preserves its work and evidence, and requires an explicit decision.

## Acceptance criteria

- [ ] A `changes_requested` review returns the PBI to correction with the budget decremented per attempt and never reset; a test asserts the remaining allowance before and after.
- [ ] A review whose recorded revision is not the current head is not replayed and produces no correction dispatch.
- [ ] A review whose text requests a behavior change produces a Plan Amendment requirement and dispatches no implementation work.
- [ ] Candidate changes originating from a review invalidate prior evidence and rerun both the local gates and the provider checks before any merge.
- [ ] An externally merged Pull Request is recorded with an outcome kind distinguishable from a Gantry-authorized merge; dependents are released only after criteria and Dependency Readiness verify against the integrated target, and a scripted merge whose integrated content fails the criteria releases nothing.
- [ ] A Pull Request closed without merge leaves the PBI paused with its worktree and evidence intact, and no reopen or replacement happens without an explicit operation.

## Blocked by

- `git-integration#07` — provides the Pull Request Observation record this slice consumes for reviews and external resolution.
- `slicing-and-approval#05` — provides the Dependency Readiness definition and the dependents-release signal.
- `slicing-and-approval#07` — provides the Plan Amendment proposal.
- `execution-core#03` — provides PBI Execution Ownership and capacity reacquisition for a PBI returning to correction.
- `execution-core#05` — provides Correction Budget accounting for the remaining allowance.
