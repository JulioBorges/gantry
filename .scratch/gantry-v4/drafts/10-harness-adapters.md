## Spec 10 — harness-adapters

This spec owns the boundary where Gantry stops being a state machine and starts talking to a real harness: one adapter interface with three implementations (native subagent, detached CLI, single-shot gateway), an Integration Capability declaration that must be proven by an executable conformance probe rather than asserted, a result path that is a file or an MCP submission but never stdout, and the observe/stop/reconcile primitives that spec 11's entire control flow is shaped around. The risk is not process spawning — it is that every shortcut here is invisible. A capability claimed without a probe turns the Context Watermark handoff, the interruption on takeover, and the egress destination record into fiction that only shows up during an incident; a `requestStop` whose caller assumes it worked lets two agents write one PBI Worktree; and a result inferred from an exit code reintroduces the stdout channel §5 replaced. Everything downstream of dispatch depends on results actually arriving, so the first thing worth proving is which result channel each of Codex and OpenCode supports reliably.

### Slices

---

**01 — Adapter interface, driver resolution, and dispatch provenance**

- **What to build**: Define the single `HarnessAdapter` interface every implementation satisfies — dispatch, observe, requestStop, reconcile — together with its variant-bearing types (`StopOutcome` with `stopped`/`requested_cooperatively`/`unsupported`, `ReconciliationResult`, `AgentObservation` with `unknown` liveness, `DispatchIo` carrying result path, working directory and diagnostic sink). Wire it into the shared operation core as an injected port so `pbi.dispatch` resolves a driver from the Execution Rule Snapshot, invokes the adapter, and records the resolved driver, command, model and processing destination on the dispatch record. Ship one scripted in-process adapter that satisfies the real interface and can be told to return every variant, plus the adapter-independent worktree-activity observer that reconcile reports (Git index hash and porcelain fingerprint of the working directory). Expose a CLI preview that prints the resolved invocation for a role without running anything.
- **Acceptance criteria**:
  - `core.invoke` on `pbi.dispatch` routes through the injected adapter port; an accepted dispatch record carries resolved driver, command, model and destination, queryable through `state.project`.
  - The scripted adapter can return each `StopOutcome` and each liveness variant, and a test asserts a caller cannot treat `requested_cooperatively` or `unsupported` as a stop.
  - Reconciliation reports `worktreeActivity` as `quiescent`, `active` or `unknown` from observed Git state, and takeover is refused while it is `active` or `unknown`.
  - The CLI preview for a configured role prints the invocation and exits without dispatching; a role with no resolvable driver fails the preview with a named rejection code.
  - One CLI parity test proves the preview delegates to the operation core.
- **Blocked by**: `operation catalog and invoke surface` (execution-core); `GTP task and result envelope, ContextUsage variants` (gtp-protocol)
- **Parallelizable with**: none (bootstrap)

---

**02 — Integration Capability declaration and conformance probes**

- **What to build**: Build the probe runner and the rule that turns probes into declarations: every non-`none` Integration Capability requires a passing probe recorded with the harness version, its evidence and its timestamp, and a capability whose probe failed or never ran is declared `none` or omitted. Persist probe results against the harness version so a version change invalidates them and forces a re-run rather than inheritance. Encode the granularity rule structurally — a probe that only observes usage between turns cannot yield `per_tool_call` — and expose a CLI command that runs an integration's probe set and prints the resulting capability declaration with its evidence.
- **Acceptance criteria**:
  - A declaration asserting a capability with no passing probe is refused; the resulting stored capability set has the capability absent, not false-but-present.
  - Changing the recorded harness version marks prior probe results invalid; the declaration degrades to `none` until probes are re-run.
  - A probe observing usage only between turns produces `contextMonitoring: "between_turns"`; no code path upgrades it to `per_tool_call`.
  - An integration declaring `between_turns` produces no projection asserting a strict context ceiling.
  - A skipped probe records an explicit reason and yields an absent capability, never an inherited one.
  - One CLI parity test proves the probe command delegates to the operation core.
- **Blocked by**: 01
- **Parallelizable with**: 03, 04, 05, 06

---

**03 — Native subagent adapter**

- **What to build**: Implement the adapter where the host harness spawns its own subagent and Gantry hands over a task envelope through a skill or MCP tool, holding no process handle. State its consequences in the type rather than around it: liveness is `unknown` unless the integration exposes a way to ask, `requestStop` returns `requested_cooperatively` or `unsupported`, and reconciliation relies on the result path, worktree activity and the persisted assignment rather than process state. Ensure no code path spawns a replacement CLI for a native assignment. Ship the adapter's own probes for native spawning and for its result channel.
- **Acceptance criteria**:
  - A native assignment dispatches through the host harness handover; a test asserts no child process is spawned for it.
  - `observe` returns `liveness: "unknown"` and `requestStop` returns at most `requested_cooperatively`; takeover does not proceed on the assumption that the agent stopped.
  - A result arriving after a cooperative stop request is reconciled as `present_valid` and is not discarded.
  - A missing result at dispatch end yields the `missing_result` Protocol Failure class, never an outcome inferred from an exit code.
  - The combination's limitation — a native harness can act outside Gantry's APIs — is recorded as a declared limitation, not mitigated by a claim.
- **Blocked by**: 01; `MCP result submission channel` (mcp-server) for the MCP-path probe only
- **Parallelizable with**: 02, 04, 05, 06

---

**04 — Detached CLI adapter, result path, and process identity**

- **What to build**: Implement the adapter that spawns another harness's CLI deterministically from configuration — an argv template per role, a prompt file rather than an inline argument, the PBI Worktree as working directory, the result path passed explicitly. The agent writes its result envelope to the result path and Gantry reads and validates it; stdout and stderr go to the diagnostic sink and are never parsed for meaning. Persist the spawned process's identity as a process identifier plus an adapter-written start token so reconciliation after a Gantry restart distinguishes still-running, exited, and identifier-reused. Implement `requestStop` against the process Gantry started, with the mechanism declared in `stopMechanism` and probed per platform — this slice carries the Windows divergence, where the absence of a cooperative process signal means a job object or a declared `agentInterruption: "none"`.
- **Acceptance criteria**:
  - A dispatch writes a prompt file and result path into the invocation; the agent's written envelope is read and validated; an exit code zero with no result file yields `missing_result` and a malformed envelope yields `malformed_result`, with stdout captured and never parsed.
  - A process that writes its result and then exits reconciles as `liveness: "exited"`, `result: "present_valid"`.
  - A process identifier reused by an unrelated process yields `liveness: "unknown"`, never a false positive, because the start token does not match.
  - `requestStop` on a Gantry-started process returns `stopped` with process evidence, and reconciliation still checks for a late-written result afterwards.
  - On a platform with no cooperative process signal, the stop probe yields `stopMechanism: "job_object"` or, failing that, `agentInterruption: "none"` — the declared guarantee changes with the platform and the implementation does not hide the difference.
  - Usage extracted from the result envelope is `self_reported`; from a harness telemetry output it is `measured` with the source named; otherwise `unknown` with a reason — never zero.
- **Blocked by**: 01; `redaction sink enforcement interface` (data-handling) for the diagnostic sink
- **Parallelizable with**: 02, 03, 05, 06

---

**05 — Gateway adapter and the file-mutating role restriction**

- **What to build**: Implement the single-shot OpenAI-compatible HTTP adapter for router and proxy setups: no working directory, no file mutation, no process lifecycle. Declare `agentInterruption: "none"` — a single-shot request can be abandoned but not interrupted — and take context monitoring from whatever the response reports, typically `self_reported`. Enforce that a file-mutating role cannot route here, both at configuration validation and again at dispatch, so a configuration written before the rule existed does not slip through. Classify the destination as `remote` for Data Egress Policy evaluation.
- **Acceptance criteria**:
  - A gateway dispatch for a non-mutating role completes and its result is read from the response through the same envelope validation as the other adapters.
  - `requestStop` returns `unsupported`; no caller path treats an abandoned request as a stop.
  - A file-mutating role configured to a gateway is rejected at configuration validation and independently rejected at dispatch, each with a named rejection code.
  - Every gateway dispatch records `destination: "remote"` and is evaluated against the egress allowance matrix before payload assembly.
  - Usage reported by the response renders as `self_reported` and never as `measured`.
- **Blocked by**: 01; `egress allowance matrix and destination classification` (data-handling); `driver routing configuration validation` (config-and-snapshot)
- **Parallelizable with**: 02, 03, 04, 06

---

**06 — Driver unavailability, Infrastructure Retry, and explicit replacement**

- **What to build**: Treat driver unavailability as an infrastructure failure: preserve the work, spend from the Infrastructure Retry allowance with increasing backoff on an injected clock, and on exhaustion block the execution with the gate unapproved — never substituting another harness, model, gateway or endpoint. Classify permanent failures (invalid credentials, missing binary, configuration error) as blocking immediately without spending the allowance. Make driver replacement an explicit operator-channel action that updates the Execution Rule Snapshot, requires the new driver's capability declaration to be validated, requires egress authorization for the new destination, invalidates affected validations, and reconciles the prior assignment and any uncertain operations before any replacement dispatch.
- **Acceptance criteria**:
  - Driver unavailability preserves the assignment, consumes Infrastructure Retry with increasing backoff on the injected clock, and on exhaustion blocks without changing driver; the Correction Budget is untouched.
  - A permanent credential failure blocks immediately and spends no Infrastructure Retry.
  - Driver replacement attempted through an agent channel is rejected as requiring the operator channel.
  - Replacement with an unvalidated capability declaration, or to a destination with no matching egress allowance, is rejected.
  - A replacement dispatch is refused until the prior assignment and any uncertain operations are reconciled, so no duplicate work is produced.
- **Blocked by**: 01; `Infrastructure Retry allowance and failure classification` (execution-core); `Execution Rule Snapshot update and revalidation` (config-and-snapshot); `egress authorization` (data-handling)
- **Parallelizable with**: 02, 03, 04, 05

---

**07 — Cross-harness conformance suite and the support matrix**

- **What to build**: Build the conformance suite as a separate test layer that runs the real adapters against real installed harnesses, and run it across the four approved combinations: Codex hosting Codex-native agents, OpenCode hosting OpenCode-native agents, OpenCode hosting a role through the detached Codex CLI, and Codex hosting a role through the detached OpenCode CLI. Its output is the support matrix as data — one row per combination with harness versions, observed Integration Capabilities, the validated result channel, and limitations. A skipped run records an explicit reason and does not count as support, and a passing native row establishes nothing about a cross-harness row. Reject an operation an integration does not support rather than approximating it.
- **Acceptance criteria**:
  - The suite runs the applicable acceptance scenarios — dispatch, valid and invalid results, gates, handoff, interruption, reconciliation, explicit resumption — identically against each combination.
  - The support matrix records the four combinations separately with versions, capabilities and limitations; a native-only pass leaves both cross-harness rows unsupported.
  - An absent harness produces a skipped row with a recorded reason and an unsupported status, never a pass.
  - For each combination the matrix names the validated `resultChannel`; a combination where neither the file path nor the MCP channel works is recorded unsupported rather than degraded.
  - An identical result submitted through both channels produces one accepted submission and one idempotent replay.
  - An operation outside a combination's declared capabilities is rejected with a named rejection code rather than approximated.
- **Blocked by**: 02, 03, 04, 05; `harness compatibility matrix as data` (machine-setup)
- **Parallelizable with**: none (integration tail)

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Operation catalog and `invoke` surface (`pbi.dispatch`, `operation.reconcile`, rejection codes) | `execution-core` | 01, 06 |
| Infrastructure Retry allowance and failure classification table | `execution-core` | 06 |
| GTP task and result envelope, boundary validation, `ContextUsage` variants | `gtp-protocol` | 01, 03, 04, 05 |
| Protocol Failure classes (`missing_result`, `malformed_result`, `identity_mismatch`) | `gtp-protocol` | 03, 04 |
| Result Submission identity and idempotency | `gtp-protocol` | 07 |
| Redaction sink enforcement interface | `data-handling` | 01 (diagnostic sink), 04 |
| Egress allowance matrix and destination classification | `data-handling` | 05, 06 |
| Execution Rule Snapshot, driver routing configuration and its validation | `config-and-snapshot` | 01, 05, 06 |
| Capability declaration persistence (setup refuses unvalidated declarations); harness presence type | `machine-setup` | 02 |
| Harness compatibility matrix as data | `machine-setup` | 07 |
| MCP result submission as a channel | `mcp-server` | 02 (result-channel probe), 03 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| Adapter interface — `HarnessAdapter`, `DispatchIo`, `AgentObservation`, `StopOutcome`, `ReconciliationResult` variants | 01 | `pbi-execution-loop` (entire control flow), `demo-mode` (stub drivers satisfy it), `dashboard` |
| Result path contract — dispatch carries a result path, the agent writes its envelope there, absence is a Protocol Failure | 01 | `gtp-protocol`, `mcp-server`, `demo-mode` |
| Dispatch provenance record — resolved driver, command, model, processing destination | 01 | `data-handling` (egress audit), `dashboard`, `git-integration` |
| Observation and stop primitives — liveness, context usage, worktree activity | 01, 03, 04 | `pbi-execution-loop` (Context Watermark, handoff, takeover) |
| `IntegrationCapabilities` and the conformance probe result shape | 02 | `machine-setup` (what a validated declaration is), `pbi-execution-loop`, `dashboard` |
| Per-driver processing destination declaration | 05 | `data-handling` |
| Gateway role restriction (file-mutating roles cannot route to a gateway) | 05 | `config-and-snapshot` |
| Support matrix — per-combination versions, capabilities, limitations | 07 | `git-integration`, `release-engineering` (documented platform status) |

### Risks / judgement calls

**The Windows divergence sits in slice 04.** The handoff names it precisely: Windows has no cooperative process signal, so `requestStop` needs job objects or declares `agentInterruption: "none"`. That is the detached CLI adapter's `stopMechanism` probe, so slice 04 implements it and its acceptance criteria assert the guarantee changes with the platform. Slice 07 only records the resulting row. Slice 03 is unaffected — a native subagent is already `cooperative_only` at best on every platform. Worth the operator's attention: if the job-object path is judged out of v4 scope, slice 04 shrinks to "declare `none` on Windows" and spec 19's platform-divergence row for agent interruption becomes permanent rather than provisional.

**Worktree activity is a boundary I had to place.** `ReconciliationResult.worktreeActivity` is in this spec's interface, but the handoff's glossary table assigns "activity marker" to spec 11. I put the Git-state fingerprint observer in slice 01 because reconcile has to return the value and the observation is adapter-independent, and left it injectable so spec 11's lease-aware marker can supersede it without reopening the interface. If the operator would rather spec 11 own the observer outright, slice 01 keeps only the variant set and gains a cross-spec blocker.

**I was tempted to split slice 04.** Result-path reading, process identity persistence, and the platform-specific stop are three distinguishable pieces, and slice 04 is the largest here. I kept them together because they are one causal chain — a process writes a result and then exits, so "did it stop" and "did a result arrive" cannot be reasoned about independently, and splitting them produces two slices that each prove half a behavior. If it proves too large in practice, the clean cut is process identity plus stop as a follow-on, leaving dispatch and result reading in 04.

**Probes are registered, not centralized.** I deliberately put the probe framework in slice 02 and the probe *scenarios* in each adapter slice, so 02–06 all run concurrently after slice 01. The cost is that slice 02 ships with only scripted probes and its real value is not visible until an adapter lands. The alternative — one slice owning framework and all probes — serializes the three adapters behind it, which the brief explicitly flags as the parallelization opportunity here.

**Slice 07 cannot be fully green in CI.** The conformance suite needs real Codex and OpenCode installations, so in most environments it records skips. That is by design — a skipped probe means an absent capability rather than an inherited one — but it means slice 07's "done" is "the suite runs and the matrix is correct, including when everything skips", not "all four rows pass". The operator should decide whether a genuine four-row pass is a release gate for spec 19 or a separate manual milestone.

**One ordering I am unsure about**: slice 06 consumes egress authorization from spec 04 and snapshot revalidation from spec 02, which are both wave-0 specs and should land early — but if either slips, slice 06's replacement path is the piece that stalls, while its unavailability-and-retry half could ship independently. I did not split on that seam because replacement without reconciliation is the duplicate-work bug this slice exists to prevent.
