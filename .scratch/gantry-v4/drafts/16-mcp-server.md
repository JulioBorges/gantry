## Spec 16 — mcp-server

This spec owns `gantry mcp`: a transport adapter that exposes the shared operation core as typed MCP tools, plus the rule that the tool catalog is *derived* from the operation catalog rather than hand-written. It owns no behavior, no validation, and no state — every tool handler builds an `OperationRequest` with `channel: "mcp"`, `actor.kind: "agent"`, and returns the rendered receipt or typed rejection. The risk is not that it is hard; it is that it is thin enough to thicken accidentally. Three pressures push against thinness: a convenience tool that composes two operations (forbidden — a needed composite is a missing operation in the core), a hand-written schema that quietly diverges from its operation's schema, and the standing temptation to infer authority or Integration Capability from the parent process. A fourth, quieter risk sits under schema derivation: TypeScript types are erased at runtime, so derivation only works if the shared operation core publishes its input schemas as runtime *data*. If it does not, every tool schema becomes hand-written and the anti-drift guarantee this spec exists to provide evaporates.

### Slices

---

**01 — MCP transport adapter bootstrap**

- **What to build**: Stand up `gantry mcp` as a server process speaking MCP over stdio, wired to the shared operation core in the same process. Build the single generic handler factory: it takes an operation name, constructs an `OperationRequest` with `channel: "mcp"`, `actor.kind: "agent"`, actor provenance drawn from the connection, and an idempotency key taken from the caller or derived from the operation and input, then renders the `OperationOutcome` as tool output with the rejection code preserved as a contractual value. Tool output leaves through the Output Redaction sink, not around it, so the path is correct from the first tool rather than retrofitted. Prove the whole path with exactly two tools — one read operation and one mutating operation — and establish that the server caches nothing between calls.
- **Acceptance criteria**:
  - `gantry mcp` starts, completes an MCP handshake, and lists its two tools.
  - Invoking either tool produces exactly one core invocation, with `channel: "mcp"` and `actor.kind: "agent"` asserted, verified against an instrumented core.
  - A successful call renders the receipt and the resulting state projection; a rejected call renders the rejection with its `code` field intact and branchable.
  - Tool output cannot be emitted without a redaction pipeline result — demonstrated by the sink refusing unprocessed content, not by a convention.
  - Restarting the server between two calls of the same sequence changes no outcome, proving no cached authorization, approval, or Execution State.
  - The parity test asserts delegation only; no assertion describes what the operation does.
- **Blocked by**: needs the **operation catalog and `core.invoke` request/outcome/rejection shapes** from `execution-core`; needs the **redaction sink enforcement interface** from `data-handling`.
- **Parallelizable with**: none (this is the bootstrap)

---

**02 — Derived tool catalog and drift guard**

- **What to build**: Generate the full tool catalog from the operation catalog rather than declaring tools by hand. Each tool's name is its operation's name in MCP convention, its input schema is derived from that operation's registered input schema, and its handler is the factory from slice 01 with no per-tool code. Mark each tool as a read or a mutating operation so a client can distinguish the surface. Expose operator-only operations as tools rather than hiding them, so an agent calling one receives `operator_channel_required` from the core — a rejection it can act on — instead of a missing tool it cannot reason about. Ship the structural completeness test that is the actual anti-drift mechanism.
- **Acceptance criteria**:
  - Every mutating operation in the core catalog has a corresponding tool, and every tool maps to an existing operation; the test is over data on both sides and fails when either drifts.
  - Adding an operation to the core catalog surfaces a tool with no hand-written code and no edit to this spec's slices.
  - Each tool's input schema is provably derived from its operation's schema — asserted by identity against the source schema, not by an equivalent hand-written copy.
  - Every operator-only operation (plan approval and amendment, local merge confirmation, correction grants, cleanup authorization, runtime migration) is present as a tool and returns `operator_channel_required`, with the rejection originating from the core invocation rather than a handler pre-check.
  - An authenticated connection changes none of the above; connection provenance is recorded for audit and grants nothing.
  - No tool schema accepts or returns a credential value; credentials appear only as environment-variable names.
- **Blocked by**: 01; needs **operation input schemas published as runtime data** from `execution-core` (see risks — this may not exist yet)
- **Parallelizable with**: 04

---

**03 — Result Submission over the MCP channel**

- **What to build**: Make the dispatch and Result Submission tools first-class rather than incidental members of the generated catalog. The dispatch tool hands the Host Harness a complete task envelope for a role so it can spawn a subagent with a full contract; the submission tool accepts a result envelope. The submission tool is the alternative result channel for integrations whose agents cannot reliably write a result file, so it must be provably equivalent to the file path — same validation, same submission identity, same idempotency, same receipt. Prove equivalence rather than asserting it.
- **Acceptance criteria**:
  - A result submitted through MCP is validated identically to one read from a result file, demonstrated by the same envelope producing the same outcome through both paths.
  - An identical resubmission through MCP returns the original receipt with no second transition and no second dispatch.
  - Altered content under the same submission identity is rejected by the core, with the rejection surfaced unchanged.
  - Two concurrent MCP connections submitting for the same assignment produce one accepted submission and one ownership or idempotency rejection, decided by the core and not by coordination in the transport.
  - Envelope content passes through unchanged; the transport adds, removes, and reinterprets no field.
  - An integration probed as `resultChannel: "mcp"` completes a dispatch-and-submit round trip end to end.
- **Blocked by**: 02; needs **Result Submission identity, receipts, and the role task/result envelope contracts** from `gtp-protocol`; needs the **`resultChannel` probe outcome (`"file" | "mcp" | "both"`)** from `harness-adapters`
- **Parallelizable with**: 04

---

**04 — Honest host identification and capability-gated tools**

- **What to build**: Report host and integration information from the validated Integration Capability declaration and from nothing else. The server must not read its parent process name, must not treat `GANTRY_HOST_COMMAND` or any other environment variable as authority, and must not conclude that native subagent control is available because a harness launched it. Where the configured integration declares a capability absent, the tools depending on it return a typed rejection rather than an approximation. The context usage tool returns the `ContextUsage` union including its `unknown` variant with a reason, so a subagent deciding whether to request a handoff is never told zero when usage cannot be measured.
- **Acceptance criteria**:
  - Host identification reflects the validated capability declaration; a test that sets a misleading parent process name and `GANTRY_HOST_COMMAND` produces identical output.
  - The context usage tool returns `unknown` with a reason for an integration that cannot measure usage, and the `unknown` variant is not collapsible to a number anywhere on the path.
  - A tool depending on a capability the integration declares absent returns a typed rejection naming the limitation.
  - The server reports the integration's declared limitations when asked, so an agent can tell what is unavailable before attempting it.
  - No code path derives capability from process environment, argv, or launch context — enforced by the identification source having no access to them, not by review.
- **Blocked by**: 01; needs the **validated Integration Capability declaration and conformance probe results** from `harness-adapters`; needs a **context usage read operation in the operation catalog** from `execution-core` (see risks)
- **Parallelizable with**: 02, 03

---

**05 — Harness conformance for the MCP surface**

- **What to build**: Prove the same tool sequence works under both Codex and OpenCode, including a cross-harness dispatch driven from inside one harness while a role is routed to the other. This is the slice that turns "the adapter is thin" into an observed fact across the two supported hosts rather than a property of one. It contributes MCP cases to the existing conformance suite rather than building a parallel harness test rig.
- **Acceptance criteria**:
  - An identical tool sequence — read state, dispatch, submit result — completes under Codex and under OpenCode with equivalent outcomes.
  - A cross-harness dispatch is drivable end to end through MCP tools from a single host session.
  - Each run records which `resultChannel` the validated integration used, and the sequence passes for both `file` and `mcp` channels.
  - Failures report which harness and which tool diverged, distinguishing an integration limitation from an adapter defect.
  - The suite adds no behavior assertions; divergence in operation semantics fails at the core's own tests, not here.
- **Blocked by**: 02, 03, 04; needs the **conformance suite and its harness fixtures** from `harness-adapters`; needs **installed harness assets** from `machine-setup`
- **Parallelizable with**: none (it is the closing slice)

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Operation catalog, `OperationRequest` / `OperationOutcome` / `Rejection` shapes, `core.invoke` | `execution-core` | 01 |
| **Runtime schema registry for operation inputs** — each operation's input schema published as runtime data keyed by operation name, not as erased TypeScript types; schema derivation and therefore the anti-drift guarantee are impossible without it | `execution-core` | 02 |
| Channel authority rule — `mcp` can never assert operator; `operator_channel_required` | `execution-core` | 02 |
| Read vs mutating operation classification | `execution-core` | 02 |
| Context usage read operation (catalog addition) | `execution-core` | 04 |
| Redaction sink enforcement interface | `data-handling` | 01 |
| Role task envelope and result envelope contracts | `gtp-protocol` | 03 |
| Result Submission identity, receipts, idempotency rule | `gtp-protocol` | 03 |
| `ContextUsage` union including `unknown` with reason | `gtp-protocol` | 04 |
| Validated Integration Capability declaration | `harness-adapters` | 04 |
| `resultChannel` probe outcome (`"file" \| "mcp" \| "both"`) | `harness-adapters` | 03, 05 |
| Conformance suite and harness fixtures | `harness-adapters` | 05 |
| Installed MCP server assets and harness registration | `machine-setup` | 05 |
| Credentials referenced by environment-variable name only | `config-and-snapshot` | 02 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| MCP schema derivation from operation schemas (the anti-drift mechanism named in the handoff) | 02 | any spec adding an operation to the catalog — `spec-validation`, `slicing-and-approval`, `entropy-gate`, `git-integration`, `baseline-transitions` — all inherit a tool for free and must not hand-write one |
| Catalog completeness invariant (every mutating operation has a tool; every tool has an operation) | 02 | same set; it is the test that fails when a spec adds an operation without a schema |
| MCP as a Result Submission channel, equivalent to the result file | 03 | `harness-adapters` (an integration probing `resultChannel: "mcp"` depends on this existing) |
| `mcp` transport parity test as the single MCP test obligation | 01 | every spec that would otherwise be tempted to write MCP behavior tests |

### Risks / judgement calls

**The tool catalog is one slice, not one slice per tool group — and that is the whole point.** I was asked to decide this explicitly. Per-tool-group slicing would mean hand-written tools, which is precisely the drift the spec exists to prevent; the catalog is data on both sides, so generating all of it is barely more work than generating one group, and the completeness test is only meaningful over the whole catalog. Slice 03 is the sole exception, and it earns its separation not by being a different tool group but by being the one place where MCP is a load-bearing data path rather than a mirror of the CLI.

**Schema derivation may not be derivable yet.** This is the sharpest item and it should be settled before slice 02 starts. The spec says each tool's input schema is "derived from that operation's input schema", but `execution-core` currently expresses `OperationInput[N]` as a TypeScript mapped type, which does not survive to runtime. Derivation therefore requires `execution-core` to own a runtime schema registry keyed by operation name. If it declines, slice 02's central acceptance criterion — schema identity against the source — degrades to a structural shape comparison, and the anti-drift guarantee becomes a convention. I did not assume the registry exists; I named it as a consumed contract. The operator should confirm with `execution-core` rather than letting slice 02 discover it.

**Several §11 illustrative tool names have no operation behind them.** `gantry_context_check`, `gantry_lint_spec`, and host/integration reporting are not in the v1 operation catalog. The spec's own rule resolves this correctly — add the operation to the core, never implement it in the server — but the consequence is that slice 04 cannot complete until a context usage read operation exists, and the completeness test in slice 02 will be honest-but-partial until later specs land their operations. That is the intended behavior of a derived catalog, not a defect, and it is worth stating to reviewers so nobody "fixes" it by hand-writing the missing tools.

**Host identification may belong in the handshake, not in a tool.** I placed it in slice 04 without deciding whether it surfaces as an MCP `initialize` response field or as a read tool. The handshake is arguably the more natural home — it is transport metadata, and a tool would need a backing operation. Either works; the binding constraint is the *sourcing* rule, which is unchanged. Left open deliberately.

**A slice I was tempted to split and did not.** Output Redaction, credential prohibition, and statelessness could have been a fifth slice. I folded redaction into slice 01 instead, because the handoff records that spec 04's sink interface must exist before any writer and that retrofitting it means auditing every writer — so the MCP output path must be a compliant sink from its first tool, not from a later cleanup pass. Statelessness went to 01 for the same reason (it is a property of how the handler is constructed), and the credential assertion went to 02 because it is a catalog-level structural check. If slice 01 feels overloaded to the operator, splitting redaction out is the safe cut — but it must then block, not follow, slice 02.

**Ordering I am least sure about.** Slice 03 is declared blocked by 02 to avoid two agents both creating the dispatch and submission tool entries. Substantively it needs only slice 01's handler factory, so if parallelism matters more than collision risk, 03 can start against 01 with 02 agreeing to leave those two entries alone. That makes the chain two deep instead of three, at the cost of a coordination point.
