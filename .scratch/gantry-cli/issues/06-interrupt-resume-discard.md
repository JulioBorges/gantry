# Interrupt, resume and discard

Type: issue
Status: ready-for-agent
Slice: `gantry-cli#06`
Spec: `.scratch/gantry-cli/spec.md`
Created: 2026-10-17
User stories covered: 15–17, 23

## Parent

`gantry-cli`

## What to build

A Run stopped without a merge stays interrupted in the same worktree and on the same branch. Resume continues from the last unfinished role, with the remaining budget, without reserving another number and without redoing plan when the Spec and Issue are already on the branch. At zero budget, resume only reopens the pause. Discard deletes the local worktree and branch. Resuming a Run that is already ready for approval does not call an agent.

## Acceptance criteria

- [ ] Stop without merge keeps the worktree, branch and local commits.
- [ ] Resume with remaining budget continues from the last unfinished role in the same worktree.
- [ ] Resume does not reserve another number and does not redo plan when the Spec and Issue are already on the branch.
- [ ] Resume at zero budget reopens the pause and does not call implement.
- [ ] Discard deletes the local worktree and branch.
- [ ] Resuming a Run that is ready for approval does not call an agent. It stays available for the approval command.

## Blocked by

- `gantry-cli#03`

## Comments

- 2026-10-17 — Operator approved this slice. Planning approval does not authorize implementation.
