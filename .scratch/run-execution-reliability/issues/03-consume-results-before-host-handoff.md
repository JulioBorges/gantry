# Consume pending role results before ending the Host execution turn

Type: issue
Status: ready-for-agent
Slice: `run-execution-reliability#03`
Spec: `.scratch/run-execution-reliability/spec.md`
Created: 2026-10-03
User stories covered: 11, 12, 13, 14, 15, 22, 24, 28, 30, 32

## Parent

`run-execution-reliability` — [Spec](../spec.md)

## What to build

Carry an authorized Run from a launched role through result consumption, independent acceptance, serial integration and final reporting while the supported Host remains active. A progress/status question must not quietly abandon the ongoing execution objective. Define and record real handoff boundaries for operator interruption, execution failure, required decisions and an unavailable Host capability. Expose result-ready versus result-consumed observations in the existing Run reporting path when the harness can establish them, and preserve an explicit unknown when it cannot.

### Files to read

- `.agents/skills/gantry/reference/round-workflow.md`
- `.agents/skills/gantry/scripts/runlog.py`

### Focused follow-up exploration

Locate the relevant Host coordination rules, canonical delayed-result fixtures, lifecycle tests and external dispatch/result handling. Use focused reads of the large canonical workflow suite. Dashboard presentation of these states is completed by Issue 05; the public workflow result and Run events must already demonstrate this slice independently.

## Acceptance criteria

- [ ] A canonical supported Host fixture launches a deliberately delayed role and consumes its result without another operator message. A status request during the wait is answered while the authorized workflow remains active; a still-running child is not reported as completed delivery.
- [ ] An accepted Critic result proceeds through the existing clean-tree and post-integration gates and authoritative completion writer before the execution report concludes. The fixture proves the completed Issue and branch state rather than merely checking a prompt string.
- [ ] Refuted, malformed or execution-unavailable role results follow their existing correction, protocol-failure or explicit-recovery path and never pass through the successful completion path. A red integration gate still stops integration.
- [ ] An actually configured post-Critic human gate is preserved and reported with its requested decision. With no such pending gate, Critic completion does not create a new operator-approval requirement. Planning, changed execution settings, PR and cleanup approvals remain separate.
- [ ] An explicit stop/cancellation or a Host capability loss produces an honest handoff identifying the pending result/work, latest available activity and supported resumption path. No daemon or continuation after the Host closes is promised.
- [ ] Validated resumption reconciles available results with the existing Run, Issue, delivered revision and assigned worktree before advancing. It neither launches duplicate code work for a matching usable result nor accepts stale/mismatched results, and preserves spent correction counts.
- [ ] The supported invocation path records attributable result availability and consumption when observable. Liveness means only the observed process/transport state; an unobservable model-progress interval remains unknown. Logs retain existing data-minimization restrictions.
- [ ] Evidence includes delayed completion, status steering, actual approval wait and interruption/resumption through the canonical seam. A bounded real Host/role trace establishes the claimed live continuation path; simulated workflow coverage is labelled separately, and unsupported conversational guarantees are not advertised.

## Blocked by

- `run-execution-reliability#01`

## Comments

- 2026-10-03 — Prepared through to-issues as a complete vertical slice. The operator approved all five slices, story coverage and dependency relationships in conversation. Planning approval does not authorize implementation.
