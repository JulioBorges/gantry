# Approved breakdown: Ground implementation in a short per-Issue technical plan

Date: 2026-10-06
Status: approved

Behavior confirmed in conversation. The operator request to open a PR to main authorizes publication of the reviewed testing seams, four slices and dependencies on 2026-10-06. No implementation is authorized.

## Testing seams

1. Primary: executable per-Issue round workflow with controlled role results and real temporary repositories, proving checkpoint/handoff behavior and independent verification.
2. Supporting: public dispatch/result-validation boundary with controlled harness executables, proving selection, supported effort and contract handling.

Recovery and reporting reuse public workflow, Run query and report seams. No UI changes are proposed.

## Approved slices

1. **[Require a grounded technical plan before first implementation](issues/01-ground-first-implementation.md)**
   - Slice: `issue-implementation-plan#01`
   - Blocked by: None
   - User stories covered: 1–8, 11–12, 17, 21–22

2. **[Use supported high reasoning for technical planning only](issues/02-select-high-planning-effort.md)**
   - Slice: `issue-implementation-plan#02`
   - Blocked by: issue-implementation-plan#01
   - User stories covered: 8–10, 17, 21

3. **[Reuse technical plans safely across corrections and resumption](issues/03-reuse-and-revalidate-plan.md)**
   - Slice: `issue-implementation-plan#03`
   - Blocked by: issue-implementation-plan#01
   - User stories covered: 13–17, 21–22

4. **[Report attributable technical-planning cost and correction outcomes](issues/04-report-planning-cost.md)**
   - Slice: `issue-implementation-plan#04`
   - Blocked by: issue-implementation-plan#02, issue-implementation-plan#03
   - User stories covered: 11, 18–20, 21–22

## Dependency rounds

1. Issue 01: complete checkpoint and handoff.
2. Issues 02 and 03: effort policy and safe reuse, independently after 01.
3. Issue 04: attributable reporting across selected efforts, reuse and replanning.

All 22 stories are covered. Any required routing prefactoring happens first inside Issue 01 and is verified through the public workflow. No schema-only, refactor-only or test-only slice is proposed.

## Approval and publication

Issues are published in the canonical tracker in dependency order and transitioned to ready-for-agent through the roadmap status writer. Wave layout and counts are regenerated and checked. All implementation criteria remain unchecked. The PR delivers planning artifacts only.
