# Read the board

Type: issue
Status: ready-for-agent
Slice: `gantry-cli#01`
Spec: `.scratch/gantry-cli/spec.md`
Created: 2026-10-17
User stories covered: 1–3, 29

## Parent

`gantry-cli`

## What to build

Deterministic commands that list Issues, Specs and the frontier as structured output. Each Issue reports whether the frontier blocks it and which blockers are open. A Spec is a supporting document, with no execute action. The commands create no branch, worktree or agent.

## Acceptance criteria

- [ ] List Issues and Specs from a fixture repository using the paths in policy.
- [ ] Report, for each Issue, whether the frontier blocks it and which blockers are open.
- [ ] A Spec is presented as a supporting document and is not executable.
- [ ] Structured output and the exit code distinguish success from a repository whose pack cannot be read.

## Blocked by

None - can start immediately

## Comments

- 2026-10-17 — Operator approved this slice as the first of six. Planning approval does not authorize implementation.
