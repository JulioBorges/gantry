# Approve and open the pull request

Type: issue
Status: ready-for-agent
Slice: `gantry-cli#05`
Spec: `.scratch/gantry-cli/spec.md`
Created: 2026-10-17
User stories covered: 23–26

## Parent

`gantry-cli`

## What to build

A command separate from the Run that has already passed review and Critic. In the existing worktree, if the closing commit is not on the branch, it marks the Issue and the roadmap done, pushes, and opens the pull request. If that commit is already on the branch, it only opens the pull request. The target does not change until merge. The command does not watch the merge.

## Acceptance criteria

- [ ] Without the closing commit, the command records the Issue and roadmap as done, pushes, and opens the pull request against the target.
- [ ] That closing commit is the latest commit on the branch, on top of the work already committed.
- [ ] When the closing commit is already on the branch, the command only opens the pull request and creates no other commit.
- [ ] The target stays without done until merge. The command writes nothing on the target.
- [ ] The execute process that left the Run ready does not perform this push.

## Blocked by

- `gantry-cli#02`

## Comments

- 2026-10-17 — Operator approved this slice. Planning approval does not authorize implementation.
