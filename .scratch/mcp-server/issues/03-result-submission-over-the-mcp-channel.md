# Result Submission over the MCP channel

Type: issue
Status: ready-for-agent
Slice: mcp-server#03
Spec: [`../spec.md`](../spec.md) (spec 16, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/mcp-server/spec.md`](../spec.md)

## What to build

Make the dispatch and Result Submission tools first-class rather than incidental members of the generated catalog. The dispatch tool hands the Host Harness a complete task envelope for a role so it can spawn a subagent with a full contract; the submission tool accepts a result envelope. This is the one place where MCP is a load-bearing data path rather than a mirror of the CLI, which is why it is separated from the derived catalog at all.

The submission tool is the alternative result channel for integrations whose agents cannot reliably write a result file, so it must be provably equivalent to the file path: same validation, same submission identity, same idempotency, same receipt. Prove the equivalence by running the same envelope through both paths rather than asserting it. Ownership and idempotency are decided by the core; the transport coordinates nothing and reinterprets no field.

This slice is declared blocked by `mcp-server#02` so that two agents do not both create the dispatch and submission tool entries. Substantively it needs only the handler factory from `mcp-server#01`, so it may start against `#01` instead if whoever holds `#02` agrees to leave those two entries alone — that trades a shorter chain for a coordination point.

## Acceptance criteria

- [ ] A result submitted through MCP is validated identically to one read from a result file, demonstrated by the same envelope producing the same outcome through both paths.
- [ ] An identical resubmission through MCP returns the original receipt with no second transition and no second dispatch.
- [ ] Altered content under the same submission identity is rejected by the core, with the rejection surfaced unchanged.
- [ ] Two concurrent MCP connections submitting for the same assignment produce one accepted submission and one ownership or idempotency rejection, decided by the core and not by coordination in the transport.
- [ ] Envelope content passes through unchanged; the transport adds, removes, and reinterprets no field.
- [ ] An integration probed as `resultChannel: "mcp"` completes a dispatch-and-submit round trip end to end.

## Blocked by

- `mcp-server#02` — owns the generated catalog entries for the dispatch and submission operations, so this slice does not create them twice.
- `gtp-protocol#02` — provides the role task envelope and result envelope contracts carried unchanged by these tools.
- `gtp-protocol#06` — provides Result Submission identity, receipts, and the idempotency rule that replay must honor.
- `harness-adapters#02` — provides the `resultChannel` probe outcome (`"file" | "mcp" | "both"`) that selects this channel for an integration.
