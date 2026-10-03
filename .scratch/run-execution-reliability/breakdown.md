# Approved breakdown: Reliable Run execution and truthful timing

Date: 2026-10-03
Status: approved

The Spec and three testing seams were accepted in conversation. The operator explicitly approved the five-Issue granularity, story coverage and dependencies on 2026-10-03. No implementation is authorized.

## Approved slices

1. **[Invoke selected roles through a verified harness adapter](issues/01-invoke-roles-through-verified-adapters.md)**
   - Slice: `run-execution-reliability#01`
   - Blocked by: None
   - User stories covered: 1, 2, 3, 7, 8, 9, 10, 27, 30, 32
   - Outcome: Deliver a complete bounded role invocation through the existing public execution interface and canonical workflow routing.

2. **[Preflight effective execution with honest reusable evidence](issues/02-preflight-effective-execution-once.md)**
   - Slice: `run-execution-reliability#02`
   - Blocked by: run-execution-reliability#01
   - User stories covered: 4, 5, 6, 9, 10, 27, 32
   - Outcome: Make an operator-selected execution profile travel from effective role resolution through preflight to a clear readiness outcome before dependent role work starts.

3. **[Consume pending role results before ending the Host execution turn](issues/03-consume-results-before-host-handoff.md)**
   - Slice: `run-execution-reliability#03`
   - Blocked by: run-execution-reliability#01
   - User stories covered: 11, 12, 13, 14, 15, 22, 24, 28, 30, 32
   - Outcome: Carry an authorized Run from a launched role through result consumption, independent acceptance, serial integration and final reporting while the supported Host remains active.

4. **[Pause on unavailable verification prerequisites and resume preserved work](issues/04-pause-unavailable-verification.md)**
   - Slice: `run-execution-reliability#04`
   - Blocked by: run-execution-reliability#02
   - User stories covered: 4, 16, 17, 18, 19, 20, 28, 30, 32
   - Outcome: Give an Issue whose acceptance depends on a declared external verification capability a complete readiness, pause and recovery path.

5. **[Show attributable Run waiting states and nonoverlapping timing](issues/05-show-truthful-run-state-and-time.md)**
   - Slice: `run-execution-reliability#05`
   - Blocked by: run-execution-reliability#03, run-execution-reliability#04
   - User stories covered: 20, 21, 22, 23, 24, 25, 26, 29, 31, 32
   - Outcome: Deliver consistent Run state and timing through the existing read-only reporting/data interface and Dashboard.

## Dependency rounds

1. Issue 01: verified dispatch.
2. Issues 02 and 03: preflight and Host continuation can proceed independently after 01.
3. Issue 04: prerequisite verification builds on 02.
4. Issue 05: state/timing presentation consumes the result lifecycle from 03 and verification pauses from 04.

The approved Issues occupy execution waves 30, 31, 32 and 33 after completed Wave 29; the roadmap script is the authority for their generated placement. Shared-file edits in parallel slices require normal isolated worktrees and serial integration; they are not additional logical blockers.

## Coverage and prefactoring

The union of the five story mappings covers all 32 Spec stories. Stories repeat only where cross-cutting selection, recovery, observability or authorization guarantees require integration coverage. There is no test-only, schema-only or UI-only Issue. Issue 05 is the complete read-data/report/browser behavior for truthful timing; each preceding slice has an independently observable workflow/CLI outcome and its own evidence.

Runner prefactoring happens first inside Issue 01 and is accepted through public dispatch behavior. No implementation-only refactor needs a separate Issue.

## Publication and verification

The five Issues are published in the canonical issues directory in dependency order and promoted through the roadmap status writer to ready-for-agent. The authorized Spec index entry is added and generated roadmap waves are refreshed. Structural, acceptance, DAG/frontier, context-size, drift and historical-wave checks are recorded in planning-verification.md. No implementation criterion is ticked.
