# MCP server: operation core as tools

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 16, wave 5)
Source: `PRD.md` §11, §8.1, §6.1
Created: 2026-09-11

## Problem Statement

The host harness is the orchestrator, which means an agent inside it needs a way to drive Gantry. A CLI
works, but shelling out to parse text output is a poor interface for an agent, and `PRD.md` specifies an
MCP server precisely so the harness can call typed tools instead: "MCP exposes the shared operation core".

The risk is that it becomes a second implementation. Three interfaces exist — CLI, MCP, dashboard — and
§8.1 requires all of them to "route equivalent actions through the same internal operations" with "no
interface may bypass an invariant or write execution state independently". An MCP tool that validates a
little differently, or that skips a check because the caller is already inside the harness, would create
exactly the divergence the shared core exists to prevent.

The subtler risk is authority. An MCP server runs as a child of something, and it is tempting to conclude
things from that: this process's parent is the harness, therefore the caller is the operator, therefore
native subagent control is available. `PRD.md` forbids both inferences — "the MCP server cannot infer
native subagent control merely from its parent process", and §8.1 adds that "an authenticated MCP
connection does not by itself replace an explicit operator decision required by an operation". An agent
asking to approve a plan is still an agent.

The PRD gives an illustrative tool list and says plainly it is not the contract: "the configuration below
is illustrative", "illustrative MCP tools (catalog to complete in implementation design)". Completing that
catalog "from this shared contract" is the deferred work.

## Solution

The MCP server is a transport adapter with no logic of its own. Each tool maps to exactly one operation in
the core's catalog, its input schema is derived from that operation's input schema rather than written
separately, and its result is the operation's outcome — a receipt or a typed rejection — rendered as tool
output. The server holds no state, caches no decisions, and performs no validation the core does not
already perform.

Its channel is `mcp`, which per spec 01 can never assert operator actorhood. Operator-only operations are
therefore unavailable through it and return `operator_channel_required` rather than a generic error, so an
agent receives an actionable message telling it to ask the human.

Host identification uses only validated integration capabilities. The server reports what the configured
and validated integration declares; it derives nothing from its own parent process, environment
variables, or the fact that it was launched by a harness.

Two tools exist because agents need them specifically: one to fetch the next task envelope for a role, and
one to submit a result. The second doubles as the alternative result channel for integrations where
writing a result file is unreliable.

## User Stories

1. As a host harness, I want typed tools rather than text output, so that I can drive Gantry without parsing.
2. As a host harness, I want each tool to correspond to one Gantry operation, so that the tool surface is predictable.
3. As a host harness, I want tool inputs validated the same way the CLI's are, so that a rejection means the same thing everywhere.
4. As a host harness, I want a typed rejection with a code, so that I can branch on the reason rather than the message.
5. As a host harness, I want to fetch the next task envelope for a role, so that I can spawn a subagent with a complete contract.
6. As a host harness, I want to submit a result envelope, so that a subagent's output is recorded and validated.
7. As a host harness, I want result submission available as a tool, so that an integration where file writing is unreliable still has a channel.
8. As a host harness, I want an idempotent resubmission to return the original receipt, so that a retry is safe.
9. As a subagent, I want to check my context usage, so that I can request a handoff before degrading.
10. As a subagent, I want an honest answer when usage cannot be measured, so that I am not told zero.
11. As a host harness, I want to read the current state projection, so that I can report progress accurately.
12. As a host harness, I want to read configuration, so that I can explain the setup without reading files.
13. As a host harness, I want a configuration write validated and rejected as a whole when invalid, so that a partial change is impossible.
14. As an operator, I want operator-only operations unavailable through MCP, so that an agent cannot approve on my behalf.
15. As an operator, I want an agent attempting one to receive a clear channel rejection, so that it asks me instead of retrying.
16. As an operator, I want an authenticated MCP connection not to count as my decision, so that connection is not consent.
17. As an operator, I want the MCP server to hold no execution state, so that there is one authority.
18. As an operator, I want the server to perform no validation the core does not, so that the two cannot diverge.
19. As an operator, I want every MCP action recorded like any other, so that the audit trail does not depend on which interface was used.
20. As an operator, I want the server unable to infer native subagent control from its parent process, so that capability claims stay honest.
21. As an operator, I want host identification based on validated capabilities only, so that discovery metadata is not treated as permission.
22. As an operator, I want the server to report an integration's limitations, so that an agent knows what is unavailable.
23. As an operator, I want an operation unsupported by my integration rejected rather than approximated, so that gaps produce errors.
24. As an operator, I want the tool catalog derived from the operation catalog, so that a new operation does not require a hand-written tool.
25. As an operator, I want read tools distinguished from mutating tools, so that the surface is understandable.
26. As an operator, I want the server to work under both Codex and OpenCode, so that my harness choice does not limit the interface.
27. As an operator, I want cross-harness dispatch drivable through MCP, so that routing a role elsewhere works from inside my harness.
28. As an operator, I want no credential value passed through or returned by any tool, so that the interface cannot leak one.
29. As an operator, I want tool output redacted, so that an agent's transcript does not accumulate secrets.
30. As a Gantry maintainer, I want one parity test proving delegation, so that behavior stays tested at the core.
31. As a Gantry maintainer, I want adding an operation to surface it as a tool automatically, so that the catalog cannot drift.

## Implementation Decisions

### One tool per operation

The tool catalog is generated from the operation catalog in spec 01. Each tool's name is the operation
name in MCP's convention, its input schema is derived from the operation's input schema, and its handler
does exactly one thing: build an `OperationRequest` with `channel: "mcp"` and invoke the core.

```ts
// The entire handler shape — deliberately trivial
const handler = (operation: OperationName) => async (input: unknown) => {
  const outcome = await core.invoke({
    operation,
    channel: "mcp",
    actor: { kind: "agent", channel: "mcp", provenance: connectionProvenance },
    requestId: input.requestId ?? derivedRequestId(operation, input),
    ...input,
  });
  return renderOutcome(outcome);   // receipt or typed rejection; no interpretation
};
```

There is no tool with logic beyond this. A tool that needed to combine operations would be evidence that
the operation catalog is missing an operation, and the fix is to add it to the core rather than to compose
in the transport.

Derived schemas mean a new operation appears as a tool without hand-written code, so the catalog cannot
drift from the core. Read operations are marked as such so a client can distinguish them.

The illustrative names in §11 map onto operations rather than becoming a parallel vocabulary:
`gantry_lint_spec` is the spec validation operation, `gantry_task_dispatch` is `pbi.dispatch`,
`gantry_task_result` is `pbi.submitResult`, `gantry_get_config` and `gantry_set_config` are `config.read`
and `config.write`, and so on. Where an illustrative name has no operation behind it, the operation is
added to the core catalog — not implemented in the server.

### Channel and authority

The server's channel is `mcp`. Per spec 01, that channel can assert `actor.kind: "agent"` and nothing
more. Operator-only operations — plan approval and amendment, local merge confirmation, verification
command approval, preparation authorization, cleanup authorization, correction grants, snapshot migration,
baseline adoption, and finding classification — are exposed as tools but always return
`operator_channel_required`.

Exposing them rather than hiding them is deliberate: an agent that calls one gets a rejection naming the
reason and telling it to ask the operator, which is more useful than a missing tool it cannot reason
about.

An authenticated connection is not a decision. The connection's provenance is recorded for audit, and it
grants nothing.

### Host identification

The server reports host and integration information from the validated capability declaration in spec 10
only. It does not read its parent process name, does not treat `GANTRY_HOST_COMMAND` or any other
environment variable as authority, and does not conclude that native subagent APIs are available because
a harness launched it.

Where the configured integration declares a capability as absent, tools depending on it return a typed
rejection rather than attempting an approximation. `gantry_context_check` returns the `ContextUsage` union
from spec 03, including `unknown` with a reason.

### Statelessness

The server holds no execution state, caches no authorization or approval, and stores nothing between
calls. Every call reads current state through the core. This is what makes multiple concurrent MCP
connections — the harness and a subagent, or two harness sessions — safe without coordination in the
transport: ownership and idempotency are enforced where they belong.

### Result submission as a channel

`pbi.submitResult` through MCP is a first-class alternative to the result file in spec 10. Same validation,
same submission identity, same idempotency. An integration whose agents cannot reliably write to a given
path uses this instead, and the conformance suite in spec 10 records which channel each validated
integration uses.

### Redaction and credentials

Tool output passes through the redaction pipeline in spec 04 before it is returned, because an agent's
transcript is a persistence sink like any other. No tool accepts or returns a credential value;
credentials are referenced by environment variable name only, consistent with the configuration rules in
spec 02.

## Testing Decisions

**What makes a good test here.** One parity test per tool, and no behavior tests. The parity test asserts
that invoking the tool results in exactly one core invocation with the expected operation and channel, and
that the tool's output is the rendered outcome. Behavior — what the operation does, which rejections it
produces — is tested at the core in the owning spec.

A second structural test asserts catalog completeness: every mutating operation in the core catalog has a
corresponding tool, and every tool maps to an existing operation. This is what prevents drift, and it is
cheap because both sides are data.

**The seam.** The same seam as spec 01, with the core instrumented to record invocations. The MCP server
is exercised through its own protocol surface against that instrumented core, so the test proves the
wiring rather than reimplementing it.

**Modules under test.** Catalog generation and completeness, schema derivation, the handler's request
construction and channel assignment, outcome rendering, operator-only rejection behavior, host
identification sourcing, statelessness across calls, and output redaction.

**Scenarios that must exist**, from PRD §14.3 item 9:

- Every mutating core operation has a tool; every tool maps to an existing operation.
- Each tool's input schema is derived from its operation's schema rather than defined independently.
- Invoking a tool produces exactly one core invocation with `channel: "mcp"` and `actor.kind: "agent"`.
- A tool's output is the rendered receipt or rejection, with the rejection code preserved.
- Each operator-only operation is exposed and returns `operator_channel_required`.
- An authenticated connection does not permit an operator-only operation.
- No tool handler performs validation absent from the core, verified by asserting that a rejection originates from the core invocation.
- Host identification reflects the validated capability declaration and ignores the parent process name and `GANTRY_HOST_COMMAND`.
- `gantry_context_check` returns `unknown` with a reason for an integration that cannot measure usage.
- A tool depending on an absent capability returns a typed rejection rather than an approximation.
- Two concurrent connections submitting results for the same assignment produce one accepted submission and one ownership or idempotency rejection, decided by the core.
- An identical resubmission through MCP returns the original receipt.
- A result submitted through MCP is validated identically to one read from a result file.
- A configuration write with any invalid field is rejected as a whole.
- No tool accepts or returns a credential value; tool output is redacted.
- The server holds no state across calls, verified by a restart between two calls of the same sequence.
- The same tool sequence works under Codex and under OpenCode in the conformance suite, including a cross-harness dispatch.

## Out of Scope

- **The operation catalog, all behavior, all invariants** (spec 01). This spec adds no behavior.
- **Every operation's semantics**: owned by the spec that defines it.
- **Envelope contracts** (spec 03): the dispatch and result tools carry them unchanged.
- **Capability declaration and validation** (spec 10): this spec consumes the validated declaration.
- **Redaction pipeline** (spec 04): this spec routes output through it.
- **Configuration schema and validation** (spec 02).
- **MCP server asset installation** (spec 05).
- **The dashboard and its capability token** (spec 17): a different transport with a different channel and a different authority model.
- **CLI command surface** (spec 19 for packaging; each operation's spec for semantics): the CLI is the other transport and gets its own parity test.

Out of scope by product decision:

- Composite tools that combine operations. A needed composite is a missing operation in the core (§8.1).
- Inferring authority or capability from the process environment (§6.1, §11, ADR-0001).
- Treating an authenticated connection as operator consent (§8.1).
- Server-side caching of state, approvals, or authorization.

## Further Notes

**Binding decisions.** ADR-0001 is why host identification is sourced exclusively from validated
declarations: the MCP server is the most tempting place to infer control, because it genuinely runs inside
the harness, and the inference would still be wrong.

**Glossary alignment.** The shared operation core, Integration Capability, and Result Submission follow
`CONTEXT.md`. The glossary's note that an authenticated connection is not an operator decision is
implemented here as a channel rule rather than as a per-tool check.

**Glossary gap for `/domain-modeling`.** Transport adapter and channel are used across specs 01, 16, and
17 without glossary entries and should get them.

**Where the risk actually sits.** The honest risk is that this spec is too thin to be wrong, which makes
it easy to thicken accidentally. The pressure will come from real use: an agent will need three calls where
one would do, and the shortest path will be a convenience tool that composes them. That is the drift the
catalog completeness test exists to catch, and the rule above — a needed composite is a missing operation —
is the discipline. Worth restating in review whenever a tool's handler grows past the trivial shape.

**Sequencing note.** This spec depends only on spec 01's catalog and can be built as soon as that exists,
which makes it a good early transport: it gives the harness a real interface long before the dashboard
exists. Its schema derivation is the piece to settle first, because hand-written schemas are how the
catalog starts drifting.
