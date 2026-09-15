# Apply Caveman lite to round agents

Type: issue
Status: ready-for-agent
Slice: `caveman-setup#03`
Spec: `.scratch/caveman-setup/spec.md`
Created: 2026-09-15

## Parent

`caveman-setup`

## What to build

Extend the approved activation contract to Implementer, Reviewer, Critic and optional Learner throughout a Run. Fresh agents, review fixes, correction passes, retries and later rounds retain the lite conversational scope when supported. Delivered artifacts and verification evidence remain complete, and the optimization cannot change completion or integration decisions.

### Files to read

- `.agents/skills/gantry/reference/round-workflow.md`
- `.agents/skills/gantry/SKILL.md`
- `tests/test_legacy_workflow_smoke.py`
- `tests/test_learner_workflow.py`
- `tests/test_draft_pr_offer.py`

## Acceptance criteria

- [ ] Every invoked round role, including the optional Learner, receives supported external-skill access and lite conversational instructions in initial calls, retries, review fixes and correction passes.
- [ ] Resolved activation and shared warning state survive later rounds; missing or unsupported activation uses normal behavior and produces at most one warning for the entire Run.
- [ ] Code, documentation, lesson candidates, PR descriptions and persisted role results retain required detail, complete contract fields and acceptance-evidence references; exact commands and errors remain intact.
- [ ] Verification gates, correction budgets, isolated worktrees, serial integration, roadmap completion and all operator approval boundaries remain unchanged.
- [ ] Fixture coverage exercises actual round invocation paths and a multi-round Run with fake skill availability and an agent recorder, including optional Learner and retry/correction paths, without global installation or paid model calls.
- [ ] Round and user-facing documentation explains scope and fallback without claiming live token savings or universal harness support; the manual harness-neutral path carries the same instructions.

## Blocked by

- `caveman-setup#01`

## Comments

- 2026-09-15 — Operator approved this three-slice breakdown; publication does not start implementation. Issues 02 and 03 may proceed concurrently after 01; keep edits to shared coordinating instructions in 01 and role-specific changes in their respective workflows.

