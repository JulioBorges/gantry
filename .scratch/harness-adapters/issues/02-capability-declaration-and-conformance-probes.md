# Integration Capability declaration and conformance probes

Type: issue
Status: ready-for-agent
Slice: harness-adapters#02
Spec: [`../spec.md`](../spec.md) (spec 10, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/harness-adapters/spec.md`](../spec.md)

## What to build

Build the probe runner and the rule that turns probes into declarations. The rule is ADR-0001 applied structurally and is the point of this slice: every non-`none` Integration Capability requires a passing probe recorded with the harness version, its evidence and its timestamp, and a capability whose probe failed or never ran is declared `none` or omitted. A claim is evidence, never an assertion, and an absent capability is the safe outcome rather than a degraded one.

Persist probe results against the harness version, so that a version change invalidates them and forces a re-run instead of letting the prior result be inherited. Encode the granularity rule structurally rather than by convention: `contextMonitoring` is one of `per_tool_call` | `between_turns` | `self_reported` | `none`, and a probe that only observes usage between turns cannot yield `per_tool_call`, because the `per_tool_call` probe requires usage observed between tool calls within a single turn. The other declared capability sets are equally closed: `agentInterruption` is `supported` | `cooperative_only` | `none`, `stopMechanism` is `process_signal` | `job_object` | `cooperative_request` | `none`, and `resultChannel` is `file` | `mcp` | `both` and is always probed, never assumed.

This slice owns the probe framework only. The probe scenarios themselves are registered by each adapter slice, so `#03`, `#04`, `#05` and `#06` can build concurrently against it. Expose a CLI command that runs an integration's probe set and prints the resulting capability declaration with its evidence.

## Acceptance criteria

- [ ] A declaration asserting a capability with no passing probe is refused; the resulting stored capability set has the capability absent, not false-but-present.
- [ ] Changing the recorded harness version marks prior probe results invalid; the declaration degrades to `none` until probes are re-run.
- [ ] A probe observing usage only between turns produces `contextMonitoring: "between_turns"`; no code path upgrades it to `per_tool_call`.
- [ ] An integration declaring `between_turns` produces no projection asserting a strict context ceiling.
- [ ] A skipped probe records an explicit reason and yields an absent capability, never an inherited one.
- [ ] One CLI parity test proves the probe command delegates to the operation core.

## Blocked by

- `harness-adapters#01` — the `HarnessAdapter` interface and the injected adapter port the probes run against.
- `machine-setup#02` — the harness compatibility matrix and the harness presence type a probe run is keyed to.

## Notes

- 2026-09-12 — Dependency on `mcp-server#03` removed to break a cycle in the blocker graph. The `resultChannel` probe runs against a declared result-channel interface with a fake MCP channel; mcp-server#03 implements the real channel and extends the conformance run. Recorded in `.scratch/gantry-v4/slice-index.md`, *Dependency graph repair*.
