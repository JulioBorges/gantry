# Honest host identification and capability-gated tools

Type: issue
Status: ready-for-agent
Slice: mcp-server#04
Spec: [`../spec.md`](../spec.md) (spec 16, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/mcp-server/spec.md`](../spec.md)

## What to build

Report host and integration information from the validated Integration Capability declaration and from nothing else. The server must not read its parent process name, must not treat `GANTRY_HOST_COMMAND` or any other environment variable as authority, and must not conclude that native subagent control is available because a harness launched it. This is the most tempting place in the system to infer control, precisely because the server genuinely does run inside the harness — and the inference would still be wrong. Where the configured integration declares a capability absent, the tools depending on it return a typed rejection naming the limitation rather than an approximation.

Where host identification surfaces is deliberately left open: it may be a field on the MCP `initialize` response, which is arguably its natural home as transport metadata, or a read tool backed by an operation in the core catalog. Either is acceptable; record the choice made. The binding constraint is the sourcing rule, which does not change with the placement.

The context usage tool returns the `ContextUsage` union including its `unknown` variant with a reason, so a subagent deciding whether to request a handoff is never told zero when usage cannot be measured. That tool needs the context usage read operation registered in the shared operation catalog by `pbi-execution-loop#03` — see the blockers. Any remaining illustrative tool name with no operation behind it is the intended behavior of a derived catalog, not a defect: the fix is to add the operation to the core, never to hand-write the tool in this server.

## Acceptance criteria

- [ ] Host identification reflects the validated capability declaration; a test that sets a misleading parent process name and `GANTRY_HOST_COMMAND` produces identical output.
- [ ] The context usage tool returns `unknown` with a reason for an integration that cannot measure usage, and the `unknown` variant is not collapsible to a number anywhere on the path.
- [ ] A tool depending on a capability the integration declares absent returns a typed rejection naming the limitation.
- [ ] The server reports the integration's declared limitations when asked, so an agent can tell what is unavailable before attempting it.
- [ ] No code path derives capability from process environment, argv, or launch context — enforced by the identification source having no access to them, not by review.

## Blocked by

- `mcp-server#01` — provides the handler factory, outcome rendering, and the redacted output path.
- `harness-adapters#02` — provides the validated Integration Capability declaration and the conformance probe results that host identification is sourced from.
- `gtp-protocol#04` — provides the `ContextUsage` union including the `unknown` variant with a reason.
- `pbi-execution-loop#03` — context usage read operation registered in the shared operation catalog, returning a `ContextUsage` value including the `unknown` variant.
