# Spend corrections and pause

Type: issue
Status: ready-for-agent
Slice: `gantry-cli#03`
Spec: `.scratch/gantry-cli/spec.md`
Created: 2026-10-17
User stories covered: 10–14, 27

## Parent

`gantry-cli`

## What to build

Execute treats a failed check, a dirty implement tree, a review fail and a Critic fail with the same `budget.corrections`. When the budget reaches zero, the pause is one JSON object on stdout and the answer on that process's stdin. Stopping does not merge and keeps the worktree.

## Acceptance criteria

- [ ] A failed check does not call review or Critic, spends one correction, and returns to implement.
- [ ] A dirty tree at the end of implement spends one correction and returns to implement.
- [ ] A review fail returns to implement and does not call Critic.
- [ ] A Critic fail returns to implement, then review and Critic run again.
- [ ] At zero budget the process pauses until it receives continue or stop.
- [ ] Continue grants one more correction for this Run only. Stop does not merge and keeps the worktree.

## Blocked by

- `gantry-cli#02`

## Comments

- 2026-10-17 — Operator approved this slice. Planning approval does not authorize implementation.
