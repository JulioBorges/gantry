# Conflict resolution within candidate preparation

Type: issue
Status: ready-for-agent
Slice: git-integration#04
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

When candidate preparation conflicts, the merger role may attempt resolution within the approved plan and governance rules, dispatched through the role envelope contract. Each attempt consumes one unit of the PBI's Correction Budget at dispatch, not at revalidation.

Any resolution produces a new candidate revision, which by the invalidation rule invalidates prior validation and requires all applicable gates and integration checks to rerun. Removing conflict markers establishes nothing, and no classification of a conflict as mechanical grants an exemption path.

A resolution that would require deciding behavior, or changing approved contracts, criteria, dependencies or scope, pauses and raises a Plan Amendment proposal instead of resolving.

## Acceptance criteria

- [ ] A conflicted preparation dispatches the merger role once and consumes exactly one correction attempt at dispatch, not at revalidation; an interrupted attempt stays consumed.
- [ ] A successful resolution yields a new `candidateRevision` and the applicable gates are re-invoked against it; a test asserts no code path marks a resolution as validated without a rerun.
- [ ] A resolution result that clears markers but leaves criteria unmet does not produce authorization.
- [ ] A merger result flagged as requiring a behavioral decision produces a Plan Amendment proposal and leaves the PBI paused with its work preserved.
- [ ] Exhausting the Correction Budget during conflict resolution leaves the gate failed and stops automatic resolution; the budget is not reset by anything in this path.

## Blocked by

- `git-integration#02` — provides candidate preparation and the typed `candidate_conflicted` outcome this slice starts from.
- `gtp-protocol#03` — provides the merger role task and result envelope.
- `execution-core#05` — provides Correction Budget accounting consumed at correction dispatch.
- `slicing-and-approval#07` — provides the Plan Amendment proposal.
- `entropy-gate#01` — provides the gate decision record re-invoked against the new candidate.
- `entropy-gate#03` — provides the invalidation and fresh-comparison rule a new candidate revision triggers.
