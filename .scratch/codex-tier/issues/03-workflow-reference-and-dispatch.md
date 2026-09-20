# Codex host orchestration reference workflow and hybrid dispatch validation

Type: issue
Status: ready
Slice: `codex-tier#03`
Spec: `.scratch/codex-tier/spec.md`
Created: 2026-09-20

## Parent

`codex-tier`

## What to build

Document and validate the executable workflow for Codex acting as Host Harness. Document how Codex reads `AGENTS.md` instructions and orchestrates Plan and Round execution, invoking roles via bounded `codex exec` commands (and delegating cross-harness roles such as an independent Claude Code or Antigravity Critic). Ensure Result Contracts are validated through `result.py` with proper error handling and recovery, and test defense-in-depth prompt rules and git hooks.

### Files to read

- `.agents/skills/gantry/reference/plan-workflow.md`
- `.agents/skills/gantry/reference/round-workflow.md`
- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/scripts/result.py`
- `tests/test_role_execution_dispatch.py`

## Acceptance criteria

- [ ] Reference workflow documentation in `.agents/skills/gantry/reference/` details Codex host orchestration and hybrid role dispatch.
- [ ] Bounded command dispatch via `execution.build_dispatch_command()` and execution runners handles prompt delivery and timeout/error isolation.
- [ ] Role results returned from `codex exec` conform to `result.py` contracts, with robust parsing for markdown and JSON delimiters.
- [ ] End-to-end integration tests verify a simulated Codex host run with cross-harness Critic, testing refusal when prompt invariants or git hooks are violated.

## Blocked by

- `codex-tier#02`
