# Initial context budget and capabilities

Type: issue
Status: done
Slice: `gantry-migration#05`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add `.agents/skills/gantry/scripts/budget.py` and the three capability declarations in `.agents/skills/gantry/capabilities/{claude-code,opencode,codex}.json`. Define every architecture field and a `models` object mapping each exact model ID to `{ "contextWindow": <positive integer> }`. Estimate an Issue’s initial package from the Issue, parent Spec, and explicitly named repository-relative files as UTF-8 bytes divided by four, applying the policy `budget.contextShare` default of 0.15. Unknown model IDs are fail-closed configuration errors. Make the plan critic refute an over-budget Issue with measured values; retain the correction-budget ceiling of two in workflow prompts.

## Acceptance criteria

- [x] `python3 .agents/skills/gantry/scripts/budget.py <issue> --model <known-id> --json` prints estimated tokens, assumed window, effective share, and an over-budget verdict; `--help` works and a 200 KB package completes in under one second.
- [x] Tests prove a policy `contextShare` overrides the 0.15 default, a package above its share is refuted with the numeric estimate in the plan critic result, and unlisted files do not affect the estimate.
- [x] `capabilities/claude-code.json`, `capabilities/opencode.json`, and `capabilities/codex.json` each declare `tier`, `hooks`, `structured_output`, `worktree_isolation`, `per_role_model`, `parallel_round`, `skills_path`, `hook_events`, `payload_fields`, and `models` whose exact IDs map to `{ "contextWindow": <positive integer> }`.
- [x] Tests prove known model IDs use their declared positive `contextWindow`, while `budget.py <issue> --model unknown-model --json` exits 1 with a configuration error and cannot invent or default a window.
- [x] The Spec Changelog receives an English entry in the same merge, and `budget.py` passes the standard-library-only import test and its runnable test command.

## Blocked by

- `gantry-migration#02` — consumes the canonical planning workflow and policy defaults.

## Comments
