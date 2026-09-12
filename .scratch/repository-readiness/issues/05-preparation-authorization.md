# Preparation proposal, authorization and scoped application

Type: issue
Status: ready-for-agent
Slice: repository-readiness#05
Spec: [`../spec.md`](../spec.md) (spec 06, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/repository-readiness/spec.md`](../spec.md)

## What to build

A missing required check produces a `PreparationProposal` carrying a proposal identity, rationale, ordered argv commands, file changes, dependency changes at the level the operator cares about, expected effects with lockfile modification declared explicitly, and the `ApprovedCommandProposal`s it would result in. Authorization is operator-only and scoped to that proposal identity.

Application executes only the listed commands and tolerates only the listed file and dependency changes. Anything outside — an additional direct dependency, an unlisted file rewrite, a command that fails and needs a different approach — pauses application and emits an amended proposal referencing the original, requiring a fresh authorization. Application never expands implicitly.

The threshold between "declared lockfile modification proceeds" and "an unlisted direct dependency pauses" is an explicit guess the spec asks to validate against real repositories: package managers routinely rewrite lockfiles and pull transitive dependencies, so a strict reading would pause on nearly every real installation while a loose one would never pause at all. The two acceptance criteria below pin that guess deliberately, so a future change to the line shows up as a test edit rather than a silent loosening.

After application, readiness is re-diagnosed from scratch: completing a proposal is not readiness, and authorizing one is neither Planning Approval nor gate approval.

## Acceptance criteria

- [ ] Authorization from a non-operator channel is rejected; authorization of a proposal identity that has since changed is rejected.
- [ ] Application runs exactly the listed commands in order, verified by a recording fake, and runs none on authorization failure.
- [ ] A fixture where application pulls a change outside the proposal leaves the repository in the paused state with an amended proposal linked to the original, and no further command runs.
- [ ] Declared lockfile modification does not pause application; an unlisted direct dependency does.
- [ ] A successful application leaves `afkEligible` false until a fresh diagnosis is run, and grants no planning or gate approval anywhere in the state projection.

## Blocked by

- `repository-readiness#03` — the `ApprovedCommandProposal` shape carried in `resultingChecks`.
- `execution-core#02` — operator-channel derivation and the `operator_channel_required` rejection for the authorization operation.
