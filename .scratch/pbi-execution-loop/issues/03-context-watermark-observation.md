# Context Watermark observation per declared granularity

Type: issue
Status: ready-for-agent
Slice: pbi-execution-loop#03
Spec: [`../spec.md`](../spec.md) (spec 11, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/pbi-execution-loop/spec.md`](../spec.md)

## What to build

The loop observes context usage through the adapter at the granularity the integration's conformance probe declared, and decides when a handoff is required. `per_tool_call` is evaluated between tool calls, so the watermark can be acted on within a turn. `between_turns` is evaluated after each result, so the watermark can be exceeded within a turn. `self_reported` uses only what the agent reports, with no independent observation. `none` performs no observation at all and triggers only on an agent's `needs_handoff`.

Crossing the watermark, or receiving `needs_handoff`, moves the PBI to `handoff_pending` and reports that a handoff is required. Performing the handoff is `pbi-execution-loop#04`; this slice owns only the trigger.

The state projection states which granularity applies, renders no strict ceiling for any of the lower three granularities, and never renders a numeric usage value when `ContextUsage` is `unknown`. The watermark default is forty percent of the configured nominal window and is described everywhere as a handoff trigger, not a limit.

This slice also registers a context usage read operation in the shared operation catalog, so a host harness can ask what Gantry observed rather than inferring it or reconstructing it at a transport. The operation returns the observed usage for a PBI or an assignment as the `ContextUsage` union defined by `gtp-protocol#04`, including the `unknown` variant carrying its reason. It must return the union rather than a number: the honest-reporting guarantee this slice exists to hold is lost the moment an unmeasurable usage crosses a transport as a value that looks measured.

## Acceptance criteria

- [ ] With `per_tool_call`, a scripted adapter crossing the watermark mid-turn produces `handoff_pending` before the turn's result arrives; with `between_turns`, only after the result; with `self_reported`, only from the agent's own reported value; with `none`, never from observation.
- [ ] With `none`, an agent result of `needs_handoff` still produces `handoff_pending`.
- [ ] No projection renders a strict ceiling for `between_turns`, `self_reported`, or `none`, and the declared granularity is present in the projection.
- [ ] A `ContextUsage` of `unknown` produces no numeric context value anywhere in the projection.
- [ ] The watermark value is read from the Execution Rule Snapshot, and changing live configuration mid-execution does not change the trigger point for a running PBI.
- [ ] The dashboard projection gets one parity test proving it renders the core's projection without recomputing it.
- [ ] A context usage read operation is registered in the shared operation catalog and returns the observed usage as a `ContextUsage` value; an integration whose declared granularity is `none` returns `unknown` with a reason, and no code path renders it as zero.

## Blocked by

- `pbi-execution-loop#01` — the worktree and lease a running PBI is observed against.
- `harness-adapters#01` — `HarnessAdapter.observe`, the `AgentObservation` shape, and the scripted adapter that can be driven to each observation variant.
- `harness-adapters#02` — the probe-backed `IntegrationCapabilities` context-monitoring granularity declaration.
- `gtp-protocol#04` — the `ContextUsage` union including `unknown`, and the `needs_handoff` status with its required continuity content.
- `config-and-snapshot#01` — the watermark value and the assumed nominal window.
- `config-and-snapshot#04` — the Execution Rule Snapshot the watermark is read from for a running PBI.
