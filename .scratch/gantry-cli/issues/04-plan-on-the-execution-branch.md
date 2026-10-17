# Plan on the execution branch

Type: issue
Status: ready-for-agent
Slice: `gantry-cli#04`
Spec: `.scratch/gantry-cli/spec.md`
Created: 2026-10-17
User stories covered: 18–22

## Parent

`gantry-cli`

## What to build

When there is no Spec and no Issue, execute reserves the supplied slug and the next number, creates the branch already named for that Issue, and calls plan. Plan writes the Spec and Issue as micro commits. The Run pauses for approval or rejection. Approval continues in the same worktree. Rejection deletes the worktree and branch. A loose Spec or Issue delta returns to plan without spending a correction. If the tree is still dirty after one more call, execute pauses again: try again or reject.

## Acceptance criteria

- [ ] The branch is created with its final name before the plan agent, using the supplied slug and the next free number.
- [ ] The agent writes the Spec and the single Issue at those paths.
- [ ] Approval continues to implement in the same worktree, without another branch.
- [ ] Rejection deletes the worktree and branch and publishes no commit.
- [ ] A dirty plan tree returns to plan without spending `budget.corrections`.
- [ ] A second return that is still dirty pauses. Try again calls plan once more. Reject deletes the branch.

## Blocked by

- `gantry-cli#02`

## Comments

- 2026-10-17 — Operator approved this slice. Planning approval does not authorize implementation.
