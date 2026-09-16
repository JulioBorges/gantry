# Execute any role in a selected native harness

Type: issue
Status: ready-for-agent
Slice: `role-execution-selection#03`
Spec: `.scratch/role-execution-selection/spec.md`
Created: 2026-09-15

## Parent

`role-execution-selection`

## What to build

Dispatch bounded role invocations to Codex CLI, Claude Code or OpenCode while the Host Harness retains coordination; unsupported installed versions are explicitly rejected.

### Files to read

- `.agents/skills/gantry/reference/plan-workflow.md`
- `.agents/skills/gantry/reference/round-workflow.md`
- `.agents/skills/gantry/scripts/result.py`
- `.agents/skills/gantry/scripts/runlog.py`

## Acceptance criteria

- [ ] Contract tests exercise every role and derived-role mapping with independent harness/model/effort selection and canonical assigned working directories.
- [ ] External results pass result.py validation; missing or invalid results retain existing protocol-failure semantics.
- [ ] Critic invocation verifies the delivered revision and independently runs acceptance and gates; permission or tool limitations fail visibly rather than accepting a summary.
- [ ] Selection identity is recorded honestly and native/configured automatic model fallback is disabled or detected and rejected.
- [ ] Existing command and edit approval policies are preserved without introducing an engine or persistent supervisor.

## Blocked by

- role-execution-selection#02

## Comments

Draft proposal only; implementation requires operator approval.
