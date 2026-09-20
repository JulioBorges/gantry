# Elevate Codex capabilities and runtime discovery to Supported tier

Type: issue
Status: done
Slice: `codex-tier#01`
Spec: `.scratch/codex-tier/spec.md`
Created: 2026-09-20

## Parent

`codex-tier`

## What to build

Update `.agents/skills/gantry/capabilities/codex.json` to declare `"tier": "supported"` with accurate model context window definitions. Enhance runtime discovery in `scripts/discovery.py` to robustly detect the `codex` CLI binary, parse version information, and query available models via `codex models`. Ensure preflight validation in `scripts/execution.py` validates Codex binary availability and authentication status, emitting clear, actionable remediation messages if missing or unauthenticated.

### Files to read

- `.agents/skills/gantry/capabilities/codex.json`
- `.agents/skills/gantry/scripts/discovery.py`
- `.agents/skills/gantry/scripts/execution.py`
- `tests/test_role_execution_dispatch.py`
- `tests/test_guard_hook_wiring.py`

## Acceptance criteria

- [x] `.agents/skills/gantry/capabilities/codex.json` declares `"tier": "supported"`, with context windows registered for `gpt-5.2-codex` and any active models.
- [x] `scripts/discovery.py` discovers installed `codex` CLI, extracts version, and enumerates available models with appropriate caching and error handling.
- [x] `execution.preflight_validate()` succeeds when Codex CLI is available and authenticated, and fails with clear remediation commands (`codex login`) when missing or unauthenticated.
- [x] Unit tests in `tests/test_role_execution_dispatch.py` verify Codex discovery, capability loading, and preflight validation contracts without regression for existing harnesses.

## Blocked by

- `dashboard-lifecycle#03`
- `gantry-plan#04`
- `interactive-dashboard#05`
