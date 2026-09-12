# Derived tool catalog and drift guard

Type: issue
Status: ready-for-agent
Slice: mcp-server#02
Spec: [`../spec.md`](../spec.md) (spec 16, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/mcp-server/spec.md`](../spec.md)

## What to build

Generate the full tool catalog from the operation catalog rather than declaring tools by hand. Each tool's name is its operation's name in MCP convention, its input schema is derived from that operation's registered input schema, and its handler is the factory from slice 01 with no per-tool code. Mark each tool as a read or a mutating operation so a client can distinguish the surface. `execution-core` publishes operation input schemas as runtime data keyed by operation name, so derivation is real identity against the source schema rather than a hand-written copy kept in step by convention — keep it that way, because a hand-written schema is exactly the drift this slice exists to prevent.

The MCP channel is always an agent and never an operator. Operator-only operations — plan approval and amendment, local merge confirmation, correction grants, cleanup authorization, runtime migration — are therefore exposed as tools rather than hidden, so an agent that calls one receives `operator_channel_required` from the core, a rejection it can act on by asking the human, instead of a missing tool it cannot reason about. The rejection must originate from the core invocation, not from a pre-check in the handler.

Ship the structural completeness test that is the actual anti-drift mechanism: it runs over data on both sides and fails when either side moves. Note for reviewers that several illustrative tool names in the spec (context checking, spec linting, host and integration reporting) have no operation behind them in the v1 catalog, so the completeness test is honest-but-partial until later specs land their operations. That is the intended behavior of a derived catalog, not a defect — the fix for a missing tool is always to add the operation to the core, never to hand-write the tool here. A tool whose handler needs logic beyond the factory is evidence of a missing operation in the core.

## Acceptance criteria

- [ ] Every mutating operation in the core catalog has a corresponding tool, and every tool maps to an existing operation; the test runs over data on both sides and fails when either drifts.
- [ ] Adding an operation to the core catalog surfaces a tool with no hand-written code and no edit to this spec's slices.
- [ ] Each tool's input schema is provably derived from its operation's schema — asserted by identity against the source schema, not by an equivalent hand-written copy.
- [ ] Every operator-only operation (plan approval and amendment, local merge confirmation, correction grants, cleanup authorization, runtime migration) is present as a tool and returns `operator_channel_required`, with the rejection originating from the core invocation rather than a handler pre-check.
- [ ] An authenticated connection changes none of the above; connection provenance is recorded for audit and grants nothing.
- [ ] No tool schema accepts or returns a credential value; credentials appear only as environment-variable names.

## Blocked by

- `mcp-server#01` — provides the generic handler factory, outcome rendering, and the redacted output path.
- `execution-core#01` — publishes operation input schemas as runtime data keyed by operation name, and the read versus mutating classification the catalog derives from.
- `execution-core#02` — provides the channel authority rule under which `mcp` can never assert operator actorhood, producing `operator_channel_required`.
