# Native subagent adapter

Type: issue
Status: ready-for-agent
Slice: harness-adapters#03
Spec: [`../spec.md`](../spec.md) (spec 10, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/harness-adapters/spec.md`](../spec.md)

## What to build

Implement the adapter for the case where the Host Harness spawns its own subagent and Gantry hands over a task envelope through a skill or an MCP tool, holding no process handle at all. Gantry does not acquire lifecycle control merely by exposing those surfaces, so the consequences must be stated in the type rather than worked around beside it: `liveness` is `unknown` unless the integration exposes a way to ask, `requestStop` returns `requested_cooperatively` or `unsupported` and never `stopped`, and `reconcile` derives its answer from the result path, the observed worktree activity and the persisted assignment rather than from process state.

Ensure no code path spawns a replacement CLI for a native assignment — the operator's own harness session and authentication are the reason to route natively, and substituting a CLI silently discards both.

Register this adapter's own probe scenarios with the probe framework: one that proves native spawning, and one that proves which result channel the integration actually supports.

## Acceptance criteria

- [ ] A native assignment dispatches through the host harness handover; a test asserts no child process is spawned for it.
- [ ] `observe` returns `liveness: "unknown"` and `requestStop` returns at most `requested_cooperatively`; takeover does not proceed on the assumption that the agent stopped.
- [ ] A result arriving after a cooperative stop request is reconciled as `present_valid` and is not discarded.
- [ ] A missing result at dispatch end yields the `missing_result` Protocol Failure class, never an outcome inferred from an exit code.
- [ ] The combination's limitation — a native harness can act outside Gantry's APIs — is recorded as a declared limitation, not mitigated by a claim.

## Blocked by

- `harness-adapters#01` — the `HarnessAdapter` interface, the `StopOutcome` and `ReconciliationResult` variant sets, and the injected adapter port.
- `gtp-protocol#01` — the Protocol Failure classes, `missing_result` in particular, and envelope boundary validation.
- `mcp-server#03` — Result Submission over the MCP channel, needed only for this adapter's MCP-path probe.
