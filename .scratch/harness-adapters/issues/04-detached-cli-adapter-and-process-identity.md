# Detached CLI adapter, result path, and process identity

Type: issue
Status: ready-for-agent
Slice: harness-adapters#04
Spec: [`../spec.md`](../spec.md) (spec 10, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/harness-adapters/spec.md`](../spec.md)

## What to build

Implement the adapter that spawns another harness's CLI deterministically from configuration: an argv template per role, a prompt file rather than an inline argument, the PBI Worktree as the working directory, and the result path passed explicitly. The agent writes its result envelope to that result path and Gantry reads and validates it; stdout and stderr go to the diagnostic sink and are never parsed for meaning. Usage extracted from the result envelope is `self_reported`, usage observed from a harness telemetry output is `measured` with its source named, and anything else is `unknown` with a reason — never zero.

Persist the spawned process's identity as a process identifier plus a start token the adapter writes, so that reconciliation after a Gantry restart distinguishes still-running from exited from identifier-reused. When the identity cannot be confirmed, `liveness` is `unknown` rather than `exited`.

Implement `requestStop` against the process Gantry started — the only case where `stopped` is returnable with process evidence — with the mechanism declared in `stopMechanism` and probed per platform. This slice carries the Windows divergence. Windows has no cooperative process signal, so either the stop is implemented through a job object and probes as `stopMechanism: "job_object"`, or no stop can be demonstrated and the integration declares `agentInterruption: "none"`. Both are acceptable implementations of this slice; what is not acceptable is claiming a stop where none exists. The platform changes the declared guarantee, and the implementation does not hide the difference. `#07` only records the resulting matrix row, and `release-engineering#05` owns the platform matrix row itself.

## Acceptance criteria

- [ ] A dispatch writes a prompt file and result path into the invocation; the agent's written envelope is read and validated; an exit code zero with no result file yields `missing_result` and a malformed envelope yields `malformed_result`, with stdout captured and never parsed.
- [ ] A process that writes its result and then exits reconciles as `liveness: "exited"`, `result: "present_valid"`.
- [ ] A process identifier reused by an unrelated process yields `liveness: "unknown"`, never a false positive, because the start token does not match.
- [ ] `requestStop` on a Gantry-started process returns `stopped` with process evidence, and reconciliation still checks for a late-written result afterwards.
- [ ] On a platform with no cooperative process signal, the stop probe yields `stopMechanism: "job_object"` or, failing that, `agentInterruption: "none"` — the declared guarantee changes with the platform and the implementation does not hide the difference.
- [ ] Usage extracted from the result envelope is `self_reported`; from a harness telemetry output it is `measured` with the source named; otherwise `unknown` with a reason — never zero.

## Blocked by

- `harness-adapters#01` — the `HarnessAdapter` interface, `DispatchIo` with its result path and diagnostic sink, and the `StopOutcome` and `ReconciliationResult` variant sets.
- `data-handling#01` — the redaction sink enforcement interface that the diagnostic sink writes through.
- `gtp-protocol#01` — envelope boundary validation and the `missing_result` and `malformed_result` Protocol Failure classes.
- `gtp-protocol#04` — the `ContextUsage` variants that distinguish `measured`, `self_reported` and `unknown`.
