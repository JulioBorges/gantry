# Post-adoption effect, in-flight migration, and transport surface

Type: issue
Status: ready-for-agent
Slice: baseline-transitions#06
Spec: [`../spec.md`](../spec.md) (spec 15, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/baseline-transitions/spec.md`](../spec.md)

## What to build

Make adoption take effect with the scope the spec requires. A new execution created after adoption captures the new snapshot and runs under the new baseline. An execution already in flight continues under its captured snapshot and moves only when the operator explicitly requests migration to the adopted baseline, which delegates to the snapshot migration in `config-and-snapshot` and consequently invalidates affected approvals and returns affected gates to pending. Nothing migrates as a side effect of adoption.

Expose the manifest and its comparison as a structured read — configurations, comparison mode, coverage change, finding change, mapping sources, fallback indicator, adoption record — so a surface can present the decision without parsing prose.

This slice owns the `gantry baseline …` CLI surface, which was previously unowned by any spec. Design the subcommand set here over the settled catalog operations `baseline.declare`, `baseline.propose`, `baseline.adopt` and `baseline.abandon`, plus the structured manifest read. Adoption is operator-only, so the adoption subcommand is reachable only from an interactive operator CLI session or a dashboard request carrying a capability token — never over MCP. Add one parity test each for the CLI and MCP transports proving delegation to the operation core.

## Acceptance criteria

- [ ] An execution created after adoption captures the new snapshot identity; an execution created before it continues under its own, with no state change caused by adoption.
- [ ] The explicit migration request moves a named in-flight execution to the adopted snapshot, invalidates the approvals its rules affect, and returns affected gates to pending; unaffected records stay bound to their original snapshot.
- [ ] No code path migrates an execution as a side effect of adoption; a test asserting in-flight snapshot identity after adoption passes without any migration call.
- [ ] Migration requested from a non-operator channel is refused.
- [ ] The structured manifest read returns every field needed to explain the decision, including which mappings were operator-supplied and whether the count fallback was used, and is available as a read operation without a capability token.
- [ ] `gantry baseline` exposes the designed subcommand set over the catalog operations; its adoption subcommand is available only from an interactive operator CLI session or a dashboard request carrying a capability token, and is never exposed over MCP.
- [ ] One CLI parity test and one MCP parity test each prove the transport delegates to the core operation and asserts no transition behavior of its own.

## Blocked by

- `baseline-transitions#05` — adoption and abandonment, whose recorded outcome this slice gives effect to.
- `config-and-snapshot#05` — snapshot migration and its approval-invalidation classification.
- `mcp-server#01` — the transport parity harness and the single MCP test obligation.
- `mcp-server#02` — MCP tool schema derivation from the operation catalog's runtime schemas, so the transition operations inherit tools rather than hand-written ones.
