# Dirty Working Tree detection and treatment

Type: issue
Status: ready-for-agent
Slice: repository-readiness#07
Spec: [`../spec.md`](../spec.md) (spec 06, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/repository-readiness/spec.md`](../spec.md)

## What to build

Detect uncommitted modifications and untracked files in the relevant base checkout, and expose that detection as a precondition callable at all three moments — `gantry init`, Planning Approval and PBI dispatch. This slice wires the `gantry init` call site and publishes the predicate the other two specs call. The other two call sites belong to `slicing-and-approval#06` (Planning Approval) and `pbi-execution-loop#01` (dispatch and worktree creation), and **those specs carry the tests for their own call sites** — so "detected at three moments" is not left proven at only one. Until a treatment is recorded the governed workflow is blocked, no PBI Worktree is created and no comparison baseline is captured.

```ts
type WorkingTreeTreatment =
  | { kind: "excluded"; acknowledgedPaths: string[] }
  | { kind: "intentional_base"; revision: string; note: string }
  | { kind: "moved_to_branch"; branch: string; revision: string };
```

Gantry never discards changes: `excluded` leaves files in place and records them as outside the execution, `intentional_base` refuses until the changes are committed so the recorded revision is real, and `moved_to_branch` creates and records an explicit branch. A treatment is bound to the revision it was recorded against, so changes appearing afterwards require a new classification rather than inheriting the old one.

## Acceptance criteria

- [ ] Fixtures with uncommitted modifications and with untracked files both produce a `working_tree` item with a `classify_working_tree` action and `afkEligible` false.
- [ ] Recording a treatment is operator-only; an agent channel is rejected.
- [ ] `excluded` leaves every file on disk unchanged; `intentional_base` against an uncommitted tree is rejected; `moved_to_branch` creates the branch and records its revision, verified against real Git state.
- [ ] No worktree creation is attempted before a treatment exists, proven by a fake that fails the test if called.
- [ ] Mutating the tree after a treatment is recorded invalidates it and returns the item to `needs_decision` against the new revision.

## Blocked by

- `repository-readiness#01` — the readiness report skeleton, the producer registry the `working_tree` item attaches to, and the temporary Git repository fixture builder.
- `execution-core#02` — operator-channel derivation and the `operator_channel_required` rejection for recording a treatment.
