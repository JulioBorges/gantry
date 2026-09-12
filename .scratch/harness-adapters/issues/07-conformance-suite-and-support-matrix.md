# Cross-harness conformance suite and the support matrix

Type: issue
Status: ready-for-agent
Slice: harness-adapters#07
Spec: [`../spec.md`](../spec.md) (spec 10, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/harness-adapters/spec.md`](../spec.md)

## What to build

Build the conformance suite as a separate test layer that runs the real adapters against real installed harnesses, and run it across the four approved combinations: Codex hosting Codex-native agents, OpenCode hosting OpenCode-native agents, OpenCode hosting a role through the detached Codex CLI, and Codex hosting a role through the detached OpenCode CLI. Its output is the support matrix as data — one row per combination carrying the harness versions, the observed Integration Capabilities, the validated `resultChannel` as `file`, `mcp` or `both`, and the limitations. A passing native row establishes nothing about a cross-harness row, and the matrix says so per row rather than in aggregate. An operation an integration does not support is rejected with a named rejection code rather than approximated.

This suite cannot be fully green in continuous integration, and that is by design. It needs real Codex and OpenCode installations, so in most environments it records skips. A skipped run records an explicit reason and produces an unsupported status; a skipped probe means an absent capability, never an inherited one. The definition of done for this slice is therefore that the suite runs and the matrix is correct, including in the case where everything skips — not that all four rows pass.

Whether a genuine four-row pass is a release gate or a separate manual milestone is an open operator decision owned by `release-engineering#06`. Build the matrix as data so that either answer can consume it without change here.

## Acceptance criteria

- [ ] The suite runs the applicable acceptance scenarios — dispatch, valid and invalid results, gates, handoff, interruption, reconciliation, explicit resumption — identically against each combination.
- [ ] The support matrix records the four combinations separately with versions, capabilities and limitations; a native-only pass leaves both cross-harness rows unsupported.
- [ ] An absent harness produces a skipped row with a recorded reason and an unsupported status, never a pass.
- [ ] For each combination the matrix names the validated `resultChannel`; a combination where neither the file path nor the MCP channel works is recorded unsupported rather than degraded.
- [ ] An identical result submitted through both channels produces one accepted submission and one idempotent replay.
- [ ] An operation outside a combination's declared capabilities is rejected with a named rejection code rather than approximated.

## Blocked by

- `harness-adapters#02` — the Integration Capability declaration, the probe framework and the probe result shape each matrix row records.
- `harness-adapters#03` — the native subagent adapter exercised by the two native rows.
- `harness-adapters#04` — the detached CLI adapter exercised by the two cross-harness rows.
- `harness-adapters#05` — the gateway adapter and its declared capabilities.
- `machine-setup#02` — the harness compatibility matrix as data and harness presence detection, which decides whether a row runs or skips.
- `gtp-protocol#06` — Result Submission identity and idempotency, for the dual-channel replay row.
- `mcp-server#03` — Result Submission over the MCP channel, the second of the two channels a row can validate.
