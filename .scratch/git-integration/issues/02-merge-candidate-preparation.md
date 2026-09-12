# Merge Candidate preparation and the Merge Authorization binding

Type: issue
Status: ready-for-agent
Slice: git-integration#02
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

Candidate preparation merges the current integration target revision into the PBI branch and records the resulting `candidateRevision`. It merges, never rebases: rebasing rewrites the micro-commits and save points that retained evidence points at, and that evidence has to stay reachable from the candidate. Optional history consolidation is a policy setting that produces a new candidate revision and therefore forces revalidation. Gates and integration checks are driven against `candidateRevision`, not against the pre-merge branch tip.

The Merge Authorization binding record and its invalidation rule are owned by `execution-core#07`. This slice does not redefine either. It owns Merge Candidate preparation and the Git and provider mechanics that produce the revisions the binding refers to, and it **consumes** the published invalidation predicate — asserting against it rather than reimplementing it — so that a moved target, a moved candidate or a replaced snapshot invalidates authorization, returns the gate to `pending`, and requires a fresh candidate and a fresh comparison.

This slice additionally owns the production wiring of the merge candidate and current target revision pair, including its touched-path diff, which is consumed downstream by the entropy gate's correction loop and by the opt-in mutation adapter.

## Acceptance criteria

- [ ] Against a real temporary Git repository, preparation produces a merge commit whose parents are the PBI branch tip and the target revision; the recorded `candidateRevision` equals that commit, and every micro-commit and save point revision remains reachable from it.
- [ ] The injected check adapters observe the candidate revision as their subject; a test asserts they are never invoked against the pre-merge branch tip.
- [ ] Enabling history consolidation yields a different `candidateRevision`, and an authorization that was valid before consolidation is invalid after.
- [ ] Advancing the target after authorization invalidates it and the gate record transitions to `pending`; a commit on the PBI branch after authorization does the same.
- [ ] The invalidation predicate published by `execution-core#07` is exercised through this slice's preparation path with a table of (target moved, candidate moved, snapshot replaced) combinations; no combination leaves authorization valid except all-unchanged, and no local re-implementation of the predicate exists.
- [ ] A conflicting merge during preparation yields a typed `candidate_conflicted` outcome and records no authorization.
- [ ] The merge candidate and current target revision pair, with its touched-path diff, is produced by production wiring — not constructed by tests — and is readable by the entropy gate correction loop and by the mutation adapter in the shape they consume.

## Blocked by

- `git-integration#01` — provides the resolved Git Workflow Policy, the integration target and the `integration.*` operation surface.
- `execution-core#07` — owns the Merge Authorization binding record and publishes the invalidation predicate this slice asserts against.
- `entropy-gate#01` — provides the gate decision record and its subject identity.
- `entropy-gate#03` — provides the return to `pending` on a changed candidate or target revision.
- `pbi-execution-loop#01` — provides the PBI branch and worktree lifecycle.
- `pbi-execution-loop#05` — provides the micro-commits and save points that must remain reachable from the candidate.
- `verification-adapters#01` — provides check execution against a named revision.
- `config-and-snapshot#04` — provides the Execution Rule Snapshot identity bound into the authorization.
