# Execute any role in a selected native harness

Type: issue
Status: done
Slice: `role-execution-selection#03`
Spec: `.scratch/role-execution-selection/spec.md`
Created: 2026-09-15

## Parent

`role-execution-selection`

## What to build

Dispatch bounded role invocations to Codex CLI, Claude Code, OpenCode or Antigravity (`agy --print`) while the Host Harness retains coordination; normalize Antigravity tools and hooks in `guard.py`; unsupported installed versions are explicitly rejected.

### Files to read

- `.agents/skills/gantry/reference/plan-workflow.md`
- `.agents/skills/gantry/reference/round-workflow.md`
- `.agents/skills/gantry/scripts/result.py`
- `.agents/skills/gantry/scripts/runlog.py`
- `.agents/skills/gantry/scripts/guard.py`
- `.agents/skills/gantry/capabilities/antigravity.json`

## Acceptance criteria

- [x] Contract tests exercise every role and derived-role mapping with independent harness/model/effort selection (including Antigravity `agy` CLI dispatch) and canonical assigned working directories.
- [x] `guard.py` normalizes Antigravity tool calls (`run_command`, `write_to_file`, `replace_file_content`) and records subagent events (`invoke_subagent`), returning JSON allow/deny decisions with exit 0.
- [x] External results pass result.py validation; missing or invalid results retain existing protocol-failure semantics.
- [x] Critic invocation verifies the delivered revision and independently runs acceptance and gates; permission or tool limitations fail visibly rather than accepting a summary.
- [x] Selection identity is recorded honestly and native/configured automatic model fallback is disabled or detected and rejected.
- [x] Existing command and edit approval policies are preserved without introducing an engine or persistent supervisor.

## Blocked by

- role-execution-selection#02

## Comments

Draft proposal only; implementation requires operator approval.
