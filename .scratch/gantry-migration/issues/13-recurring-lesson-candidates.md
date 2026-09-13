# Recurring lesson candidates

Type: issue
Status: done
Slice: `gantry-migration#13`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add the optional Learner phase to `.agents/skills/gantry/reference/round-workflow.md` and final reporting in `.agents/skills/gantry/SKILL.md`, using the Learner result contract. It reads only recorded refutations and review findings from the Run log, groups recurring problems across Issues or attempts, and drafts English lesson candidates carrying their evidence and proposed target. It does not write candidates into `AGENTS.md`, `CONTEXT.md`, templates, or policy.

## Acceptance criteria

- [x] Given a Run log with “criterion 3 has no test” on `greeting#01` and `greeting#03`, and “cli.py prints to stderr” only on `greeting#02`, the Learner result contains exactly one candidate citing the two recurring references and naming its proposed target.
- [x] A test proves the Learner reads no source other than permitted Run-log refutations and review findings, emits a result validated by `schemas/learner.json`, and leaves `AGENTS.md`, `CONTEXT.md`, templates, and policy byte-identical.
- [x] The final workflow report exposes lesson candidates as operator decisions and never auto-injects them; fixture artifacts and reports remain English.
- [x] The Spec Changelog receives an English entry in the same merge, with the Learner test runnable from the repository.

## Blocked by

- `gantry-migration#08` — consumes recorded refutation and review-finding events.
- `gantry-migration#06` — consumes the Learner result contract.

## Comments
