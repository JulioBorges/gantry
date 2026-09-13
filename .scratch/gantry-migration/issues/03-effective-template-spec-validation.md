# Effective-template Spec validation

Type: issue
Status: blocked
Slice: `gantry-migration#03`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add `.agents/skills/gantry/scripts/spec.py` and extend the canonical policy resolver to locate pack or repository Spec templates and `templates.headingMap`. Derive required headings, their order, placeholder detection, and well-formed scenarios from the effective template. Wire `spec.py --check` into the canonical plan workflow before planning starts; it reports structural failures but never edits a Spec.

## Acceptance criteria

- [ ] `python3 .agents/skills/gantry/scripts/spec.py --check <spec> --json` exits 1 and names each missing, out-of-order, placeholder, or malformed-scenario requirement, exits 0 for a structurally valid 200 KB Spec in under one second, and prints usage with `--help`.
- [ ] A test repository whose `.gantry/config.json` maps `## Delivery contract` to `## Contract` passes that equivalent heading while a Spec omitting `## Changelog` fails and explicitly reports `## Changelog` missing.
- [ ] A plan-workflow test proves structural validation runs before any planner write; when it fails, no Issue file is created and the operator-facing report carries the script finding.
- [ ] The Spec Changelog receives an English entry in the same merge, and `spec.py` passes the standard-library-only import test and its runnable test command.

## Blocked by

- `gantry-migration#02` — consumes the canonical template and policy-resolution locations.

## Comments
- 2026-09-13 — Critic refuted completion: the approved Spec fails structural validation because line 153 contains invalid Gherkin ('And, on yes, ...'). Operator must amend and approve the Spec before this Issue can continue. Issue worktree: /Users/julioborges/src/personal/gantry-issue-03 (branch gantry/gantry-migration-03).
