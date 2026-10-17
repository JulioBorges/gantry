# Execute an Issue that already exists

Type: issue
Status: ready-for-agent
Slice: `gantry-cli#02`
Spec: `.scratch/gantry-cli/spec.md`
Created: 2026-10-17
User stories covered: 4–9, 27–28

## Parent

`gantry-cli`

## What to build

`gantry execute` takes an Issue that already has a Spec through review. It validates setup before creating a branch. It refuses an open blocker without a worktree. On the happy path it creates the worktree on the Issue branch, asks implement for micro commits, runs checks, calls review and Critic with the diff against the target, and exits without a push when both pass. Each role's harness is the command configured for that role.

## Acceptance criteria

- [ ] Invalid setup exits with no branch and no worktree.
- [ ] An Issue with an open blocker exits with no worktree.
- [ ] The happy path creates the worktree on the final branch, records micro commits, and does not push.
- [ ] Review and Critic receive the diff of the branch against the target.
- [ ] When both pass, execute exits and the Run is ready for approval.
- [ ] The configured role command can be replaced. The test does not open a real harness.

## Blocked by

- `gantry-cli#01`

## Comments

- 2026-10-17 — Operator approved this slice. Planning approval does not authorize implementation.
