# Show attributable Run waiting states and nonoverlapping timing

Type: issue
Status: ready-for-agent
Slice: `run-execution-reliability#05`
Spec: `.scratch/run-execution-reliability/spec.md`
Created: 2026-10-03
User stories covered: 20, 21, 22, 23, 24, 25, 26, 29, 31, 32

## Parent

`run-execution-reliability` — [Spec](../spec.md)

## What to build

Deliver consistent Run state and timing through the existing read-only reporting/data interface and Dashboard. Render execution, known verification pause, explicit operator decision, result pending Host handling, completion and unknown/stale observations from their actual lifecycle causes. Freeze known paused phase-work intervals without hiding total elapsed wall time, and stop interpreting Critic completion alone as a request for approval. Preserve existing explicitly authorized Dashboard controls and genuinely configured gates; the new observation views grant no completion or approval authority.

### Files to read

- `.agents/skills/gantry/scripts/dashboard.py`
- `.agents/skills/gantry/dashboard/static/app.js`

### Focused follow-up exploration

Read targeted Dashboard HTTP/history tests, stylesheet and browser test scenarios, Run event validation and final-report workflow sections. Inspect the Run-log module on demand after locating the relevant event contracts; it is not part of the initial package. Prefer one canonical event fixture reused through data, report and browser assertions. Do not preload every UI/test file or duplicate the reducer in the tests.

## Acceptance criteria

- [ ] The read-only Run data, final report and visible Dashboard agree on executing, verification-paused, decision-required, result-pending-integration, done and unknown/stale states. Every known wait has an explicit cause; Critic completion alone never creates an operator decision.
- [ ] A paused interval is recorded/reduced separately from phase-work intervals, while total wall time remains visible. Replaying the historical pause/resume shape no longer charges the entire pause to Critic execution. Labels explicitly describe which measured or observed intervals each duration includes.
- [ ] Result-ready and result-consumed observations from Issue 03 identify pending Host handling without claiming a known cause for missing observations. Unknown legacy result timing remains unknown rather than being backfilled from later completion.
- [ ] Parallel Issue intervals do not sum into an inflated Run duration. Retry, correction, interrupted and resumed intervals retain attribution without double counting; malformed ordering, duplicate starts, missing finishes and post-finish records yield visible incomplete evidence rather than invented precision.
- [ ] Known suspension can be reflected only when the declared harness/adapter supplies actual provenance. No macOS-specific collector or machine-setting change is required; an event gap alone stays unknown/stale. A heartbeat is not labelled as model reasoning or useful progress.
- [ ] Legacy logs remain readable without modifying their bytes, and completed counters are unchanged by the observational migration. Structured timing/state metadata contains no prompts, raw command output, diffs or secrets.
- [ ] Playwright exercises real Dashboard rendering on desktop and mobile fixtures, keyboard navigation, accessible state/timing labels and transition behavior. The paused, real-approval, accepted-result-pending and incomplete-history cases produce no browser errors or regressions in existing authorized controls.
- [ ] Public documentation and final-report examples explain wall time, observed phase intervals, known waits and unknown coverage. Existing deterministic acceptance, configured human gates, serial integration, Issue status authority and read-only observation endpoints retain their semantics.

## Blocked by

- `run-execution-reliability#03`
- `run-execution-reliability#04`

## Comments

- 2026-10-03 — Prepared through to-issues as a complete vertical slice. The operator approved all five slices, story coverage and dependency relationships in conversation. Planning approval does not authorize implementation.
- 2026-10-03 — Initial context audit moved Run-log exploration to focused follow-up reading; behavior, acceptance criteria and dependencies are unchanged.
