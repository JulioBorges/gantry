# Support Codex in setup wizard, policy configuration, and AGENTS.md policy injection

Type: issue
Status: done
Slice: `codex-tier#02`
Spec: `.scratch/codex-tier/spec.md`
Created: 2026-09-20

## Parent

`codex-tier`

## What to build

Update `scripts/setup.py` and the `gantry-setup` skill to support Codex as an interactive and non-interactive harness target. Detect the presence of the `codex` CLI or `.codex` configuration in the environment, guide the user to verify authentication, write or merge `execution.hostHarness: "codex"` and role configurations into `.gantry/config.json`, and inject explicit policy instructions and execution guardrails into `AGENTS.md` tailored for Codex.

### Files to read

- `.agents/skills/gantry-setup/SKILL.md`
- `.agents/skills/gantry/scripts/setup.py`
- `.agents/skills/gantry/scripts/common.py`
- `tests/test_gantry_setup.py`
- `tests/test_common_policy.py`

## Acceptance criteria

- [x] `setup.py` detects Codex in PATH or project root and supports `--harness codex` as an explicit or interactive option.
- [x] Setup guides operator to verify authentication (`codex login`) and tests discovery before finalizing configuration.
- [x] `.gantry/config.json` stores Codex under `execution.hostHarness` and role models when chosen, preserving existing unrelated policy.
- [x] Setup injects and idempotently maintains the marked Gantry policy block in `AGENTS.md`, including Codex-specific orchestration rules and guardrail directives.
- [x] Tests in `tests/test_gantry_setup.py` verify Codex setup, merge/overwrite behaviors, and `AGENTS.md` block preservation.

## Blocked by

- `codex-tier#01`
