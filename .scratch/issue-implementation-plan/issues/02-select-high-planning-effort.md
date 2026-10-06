# Use supported high reasoning for technical planning only

Type: issue
Status: ready-for-agent
Slice: `issue-implementation-plan#02`
Spec: `.scratch/issue-implementation-plan/spec.md`
Created: 2026-10-06
User stories covered: 8–10, 17, 21

## Parent

`issue-implementation-plan` — Spec in the local Markdown tracker.

## What to build

Deliver the approved planning-effort policy through effective Implement selection, capability validation, bounded invocation, result handling and reporting. Inherit the selected harness/model after profile, Run and Issue overrides. Request high when supported; otherwise use the greatest supported effort at or below high, or the model default when effort is not configurable. An unknown capability is not evidence that effort is unavailable. Keep the implementation invocation at its original configured effort and avoid persisted default changes. Preserve explicit recovery on execution failure without model/harness substitution.

## Acceptance criteria

- [ ] Controlled public dispatch proves high is requested for technical planning while a medium-configured implementation still requests medium on the same effective harness/model.
- [ ] Fixtures cover high support, low/medium-only support and a model with no configurable effort; each produces the documented requested selection and observed evidence without invented identity.
- [ ] Unknown effort capabilities stop for existing readiness/recovery handling rather than silently selecting an assumed setting.
- [ ] Run and Issue selection overrides reach planning and implementation; saved operator profiles and repository role defaults remain unchanged.
- [ ] An unavailable selected execution pauses visibly and preserves the plan/worktree without automatic model or harness fallback or correction-budget consumption.
- [ ] Native and manual paths report the accepted effort policy and distinguish requested effort from provider-observed execution.

## Blocked by

- issue-implementation-plan#01

## Comments

Testing seams, four-Issue breakdown and dependencies approved for publication when the operator requested a PR to main on 2026-10-06. Implementation remains separately authorized; no criterion is complete.
