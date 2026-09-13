# Requirement Critic stops ambiguous planning

Type: issue
Status: done
Slice: `gantry-migration#04`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Extend `.agents/skills/gantry/reference/plan-workflow.md` and `.agents/skills/gantry/SKILL.md` with a Requirement Critic phase after `spec.py --check` and before research or Issue slicing. Its prompt assesses ambiguity, coherence, verifiability, and non-goal coverage; a blocking finding stops the run, quotes the finding, and tells the operator to amend the Spec. It remains read-only and preserves the planning-approval boundary.

## Acceptance criteria

- [x] A workflow test using a fixture Spec with the Definition-of-Done item “the greeting should be fast” records a blocking Requirement Critic finding quoting that item, stops before the planner writes an Issue, and tells the operator to amend the Spec.
- [x] A structurally valid, non-ambiguous fixture Spec reaches the existing research and draft-planning path only after the Requirement Critic returns no blocking finding; the Critic never edits the Spec.
- [x] The workflow documentation states that structural validation and Requirement Review do not approve planning, and generated artifacts and operator reports remain English.
- [x] The Spec Changelog receives an English entry in the same merge, with the workflow test runnable from the repository.

## Blocked by

- `gantry-migration#03` — consumes the structural-validation result that gates Requirement Critic execution.

## Comments
