# MCP transport adapter bootstrap

Type: issue
Status: ready-for-agent
Slice: mcp-server#01
Spec: [`../spec.md`](../spec.md) (spec 16, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/mcp-server/spec.md`](../spec.md)

## What to build

Stand up `gantry mcp` as a server process speaking MCP over stdio, wired to the shared operation core in the same process. Build the single generic handler factory that every tool will use: it takes an operation name, constructs an `OperationRequest` with `channel: "mcp"`, `actor.kind: "agent"`, actor provenance drawn from the connection, and an idempotency key taken from the caller or derived from the operation and its input, then renders the `OperationOutcome` as tool output with the rejection `code` preserved as a contractual value an agent can branch on.

Tool output leaves through the Output Redaction sink rather than around it, so the output path is compliant from the very first tool instead of being retrofitted once many writers exist. The handler holds nothing between calls: no cached authorization, no cached approval, no Execution State.

Prove the whole path with exactly two tools — one read operation and one mutating operation. This slice adds no behavior and no validation of its own; the parity test asserts delegation, and what the operations do is tested at the core in the spec that owns them.

## Acceptance criteria

- [ ] `gantry mcp` starts, completes an MCP handshake, and lists its two tools.
- [ ] Invoking either tool produces exactly one core invocation, with `channel: "mcp"` and `actor.kind: "agent"` asserted, verified against an instrumented core.
- [ ] A successful call renders the receipt and the resulting state projection; a rejected call renders the rejection with its `code` field intact and branchable.
- [ ] Tool output cannot be emitted without a redaction pipeline result — demonstrated by the sink refusing unprocessed content, not by a convention.
- [ ] Restarting the server between two calls of the same sequence changes no outcome, proving no cached authorization, approval, or Execution State.
- [ ] The parity test asserts delegation only; no assertion describes what the operation does.

## Blocked by

- `execution-core#01` — provides the operation catalog and the `core.invoke` request, outcome, and rejection shapes.
- `data-handling#01` — provides the redaction sink enforcement interface that tool output must pass through.
