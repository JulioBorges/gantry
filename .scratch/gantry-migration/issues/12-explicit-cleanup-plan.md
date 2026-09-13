# Explicit cleanup plan and execution

Type: issue
Status: done
Slice: `gantry-migration#12`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add `.agents/skills/gantry/scripts/cleanup.py` and the end-of-Run cleanup-plan invocation in `.agents/skills/gantry/SKILL.md`. Inspect Issue status files, Git worktrees, issue branches, and the run branch to identify only worktrees and branches belonging to `Status: done` Issues that are already merged into the run branch. Keep the default action read-only; require the operator’s explicit `--yes` to remove exactly the objects printed in the plan.

## Acceptance criteria

- [x] A temporary multi-worktree Git test proves `cleanup.py --plan --json` lists only a done Issue’s already-merged worktree and branch, excluding draft, blocked, unmerged, unknown, and unrelated worktrees or branches.
- [x] In an unchanged temporary multi-worktree fixture state, a test runs `cleanup.py --plan --json` and records its listed worktree and branch; a following `cleanup.py --yes` removes exactly those recorded objects. Without `--yes`, no Git object or file is removed.
- [x] `cleanup.py --help` works, no automatic cleanup is called by the workflow, and the run report presents the plan for operator authorization rather than executing it.
- [x] The Spec Changelog receives an English entry in the same merge, and `cleanup.py` passes the standard-library-only import test and its runnable test command.

## Blocked by

- `gantry-migration#02` — consumes canonical Issue status parsing and Run-branch workflow terminology.

## Comments
