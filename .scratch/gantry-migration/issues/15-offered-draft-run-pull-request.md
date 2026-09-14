# Offered draft Run pull request

Type: issue
Status: done
Slice: `gantry-migration#15`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add the end-of-Run draft pull request offer to `.agents/skills/gantry/SKILL.md` and its workflow template. After the last completed round, generate an English body from each Issue’s authoritative criteria and Critic evidence, ask the operator before calling `gh`, and open one draft pull request from the run branch to the configured target only on explicit confirmation. If `gh` is unavailable or the operator declines, report the branch instead; never merge or auto-create a pull request.

## Acceptance criteria

- [x] With a stub `gh` on `PATH` and operator confirmation, a workflow test observes exactly one draft-pull-request command targeting the configured branch and a body that contains each completed Issue’s criteria and Critic evidence.
- [x] With no `gh` executable or with operator refusal, no pull request command runs and the English Run report names the run branch and configured target as the handoff.
- [x] The offer occurs only after final `roadmap.py check`, frontier reporting, and the optional Learner phase has completed or been explicitly skipped; it states the capability-file support tier and never merges, observes provider state, or creates per-Issue pull requests.
- [x] The Spec Changelog receives an English entry in the same merge, with the pull-request workflow test runnable from the repository.

## Blocked by

- `gantry-migration#06` — consumes validated Critic criteria and evidence results.
- `gantry-migration#14` — consumes the completed-Run lifecycle and final report boundary.
- `gantry-migration#05` — consumes the declared support tier.

## Comments
