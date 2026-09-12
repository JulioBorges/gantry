# Harness conformance for the MCP surface

Type: issue
Status: ready-for-agent
Slice: mcp-server#05
Spec: [`../spec.md`](../spec.md) (spec 16, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/mcp-server/spec.md`](../spec.md)

## What to build

Prove the same tool sequence works under both Codex and OpenCode, including a cross-harness dispatch driven from inside one harness while a role is routed to the other. This is the slice that turns "the adapter is thin" from a claim into an observed fact across both supported hosts rather than a property of one.

Contribute MCP cases to the existing cross-harness conformance suite rather than building a parallel test rig. The suite adds no behavior assertions of its own: if operation semantics diverge, that must fail at the core's own tests, and a failure here should tell the reader which harness and which tool diverged and whether the cause is an integration limitation or an adapter defect.

## Acceptance criteria

- [ ] An identical tool sequence — read state, dispatch, submit result — completes under Codex and under OpenCode with equivalent outcomes.
- [ ] A cross-harness dispatch is drivable end to end through MCP tools from a single host session.
- [ ] Each run records which `resultChannel` the validated integration used, and the sequence passes for both the `file` and `mcp` channels.
- [ ] Failures report which harness and which tool diverged, distinguishing an integration limitation from an adapter defect.
- [ ] The suite adds no behavior assertions; divergence in operation semantics fails at the core's own tests, not here.

## Blocked by

- `mcp-server#02` — provides the derived tool catalog the sequence is drawn from.
- `mcp-server#03` — provides the dispatch and Result Submission tools the sequence exercises.
- `mcp-server#04` — provides honest host and capability reporting, which distinguishes an integration limitation from an adapter defect.
- `harness-adapters#07` — provides the cross-harness conformance suite and its harness fixtures.
- `harness-adapters#02` — provides the `resultChannel` probe outcome recorded per run.
- `machine-setup#03` — provides the installed MCP server assets and their registration into harness conventions.
