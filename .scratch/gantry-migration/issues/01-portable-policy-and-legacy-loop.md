# Portable policy defaults for the legacy loop

Type: issue
Status: done
Slice: `gantry-migration#01`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Remove repository-specific assumptions from the still-present legacy `.agents/skills/asdlc/` loop while keeping it runnable. Add standard-library policy resolution to `.agents/skills/asdlc/scripts/common.py`, with sparse pack defaults and an optional repository `.gantry/config.json` overlay. Update `.agents/skills/asdlc/SKILL.md` and both files under `.agents/skills/asdlc/reference/` to pass resolved policy and repository paths through arguments instead of naming this repository, `.scratch/gantry-v4/slice-index.md`, or a fixed issue-tracker path. Preserve the existing issue parser contract for `Status:`, `Slice:`, `## Acceptance criteria`, and `## Blocked by`.

## Acceptance criteria

- [x] With no `.gantry/config.json`, automated tests exercise the default artifact, template, git, budget, and dashboard policy values, including `contextShare: 0.15` and `staleAfterSeconds: 900`; an overlay changes only supplied values and `python3 .agents/skills/asdlc/scripts/frontier.py --scope gantry-migration --include-parked --json` still executes successfully.
- [x] `python3 tests/test_legacy_workflow_smoke.py` creates an isolated no-policy repository and exercises the rendered legacy plan path through its planning-approval stop and the rendered round path through its safe no-ready-work stop; it asserts both paths use the unchanged parser for filename, `Status:`, `Slice:`, `## Acceptance criteria`, and `## Blocked by`.
- [x] `grep -r "gantry-v4\|slice-index\|the Gantry repository" .agents/skills/asdlc` has no matches, and a workflow-template test proves repository-specific paths are received through arguments rather than literals.
- [x] Parser regression tests prove existing Markdown issues using the current filename, `Status:`, `Slice:`, `## Acceptance criteria`, and `## Blocked by` conventions produce the same references, criteria, and blockers as before.
- [x] The Spec Changelog receives an English entry in the same merge, and the new Python code is covered by the standard-library-only import test and its runnable test command.

## Blocked by

- None

## Comments
