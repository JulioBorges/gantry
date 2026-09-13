# Differential quality gates with RFC 6901 mappings

Type: issue
Status: done
Slice: `gantry-migration#07`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Extend `.agents/skills/gantry/scripts/gates.py` and policy resolution for declared absolute and differential checks. Implement RFC 6901 pointer resolution from command JSON output to a findings array and scalar `rule`, `file`, `line`, `message`, and `severity` fields. Normalize every file path repository-relative, identify findings by `(rule, file, message)`, order severity as `info < warning < error`, execute differential commands in separate base and delivery worktrees, and reject duplicate normalized identities in either source. Build self-contained temporary-repository test seams adjacent to the gate tests; the reusable fixture copies are owned by `gantry-migration#16`.

## Acceptance criteria

- [x] A self-contained gate test repository runs `gates.py --run --diff-base <base> --json` and reports a new delivery finding under `new` with `verdict: fail`, a same-identity severity increase from `warning` to `error` under `aggravated` with `verdict: fail`, base-only findings under `resolved`, and same-or-lower delivery findings under `preexisting` with `verdict: pass`.
- [x] Tests prove RFC 6901 escape handling, invalid or missing pointers and severities fail gate configuration, file paths normalize to repository-relative form, and a duplicate `(rule, file, message)` in base or delivery returns exit 1 with `verdict: fail` and an `invalid` entry naming both source and identity.
- [x] Absolute checks remain exit-code pass/fail, `no_gates` still blocks completion unless the Issue creates and proves its gates, and the Critic template consumes JSON gate results rather than paraphrasing them.
- [x] The Spec Changelog receives an English entry in the same merge, and the self-contained linter seam plus `gates.py` tests run without third-party imports in Gantry scripts.

## Blocked by

- `gantry-migration#02` — consumes the canonical gate script and effective policy location.

## Comments
