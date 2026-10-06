# Reuse technical plans safely across corrections and resumption

Type: issue
Status: ready-for-agent
Slice: `issue-implementation-plan#03`
Spec: `.scratch/issue-implementation-plan/spec.md`
Created: 2026-10-06
User stories covered: 13–17, 21–22

## Parent

`issue-implementation-plan` — Spec in the local Markdown tracker.

## What to build

Deliver retained plan reuse from execution artifacts through correction and same-Run resumption to the implementation checkpoint. Check Issue/Spec identity, assigned worktree, revision and relevant source/standing-decision content. Changed HEAD triggers evaluation rather than invalidating every plan after its own implementation commits. Reuse valid findings, refresh only affected findings and coverage, and stop for operator approval when approved scope or contracts change. Preserve existing result continuation, selected role overrides and correction counts.

## Acceptance criteria

- [ ] Review fixes and Critic corrections reuse a valid plan without unconditionally invoking full Research-and-Plan again; correction-budget semantics remain unchanged.
- [ ] A real temporary Git history proves that own implementation commits and unrelated changes can retain valid findings after freshness evaluation.
- [ ] Changed relevant source, Issue, Spec or standing decisions prevent stale handoff; affected findings and criterion coverage are refreshed before affected implementation.
- [ ] A changed approved contract or dependency requests an operator decision rather than automatically rewriting the approved Issue breakdown.
- [ ] Interruption after a validated plan retains a machine-local artifact; same-Run recovery verifies its identity, detects missing/corrupted or mismatched artifacts and cannot reuse another Issue/worktree result.
- [ ] Recovery does not repeat already consumed valid work, reset correction attempts, change execution selection silently or grant delivery completion.
- [ ] Public workflow/continuation tests exercise valid reuse, targeted replanning and refusal paths for native and manual execution semantics.

## Blocked by

- issue-implementation-plan#01

## Comments

Testing seams, four-Issue breakdown and dependencies approved for publication when the operator requested a PR to main on 2026-10-06. Implementation remains separately authorized; no criterion is complete.
