# Harness adapters: invocation, capabilities, and reconciliation

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 10, wave 3)
Source: `PRD.md` §6.1, §14.2, §13.4
Created: 2026-09-11

## Problem Statement

Gantry's pitch is provider independence: use the harness and subscription the operator already has,
route a role to a different harness when that is better, and keep the guarantees the same. `PRD.md`
defines three invocation adapters — a native subagent inside the host harness, a detached CLI of another
harness, and a single-shot gateway — and requires Codex and OpenCode to pass the same acceptance
scenarios in four combinations, including both cross-harness directions.

The hard part is not spawning processes. It is that harnesses differ in what they expose, and the
temptation is to paper over the difference. `PRD.md` and ADR-0001 both refuse: "each integration must
explicitly identify its context-monitoring and agent-interruption capabilities", "a strict ceiling may
only be claimed when the integration can enforce it", and "Gantry does not acquire lifecycle control
merely by exposing CLI or MCP tools". A capability claimed but absent is worse than a missing one,
because the watermark handoff, the interruption on takeover, and the context guarantee all silently
become fiction.

Three specific gaps follow. Native subagents are spawned by the host harness, so Gantry cannot stop one
by killing a process it never started — and "do not assume that closing the harness stopped detached
processes". A detached CLI writes to stdout, which §5.4 rules out as the semantic channel, so there must
be a result path that is not log parsing. And a driver that becomes unavailable must not be silently
replaced, because a different driver may have a different data egress destination.

"Actual Codex/OpenCode invocation, result and usage extraction, interruption and ownership
reconciliation" are deferred to implementation, with the requirement to "execute the four approved
native/cross combinations before claiming support".

## Solution

One adapter interface, three implementations, and a capability declaration that must be proven rather
than asserted. Each adapter declares what it can do, and each declared capability is backed by a
conformance probe — an executable check run against the installed harness that demonstrates the
capability and records the harness version. A capability without a passing probe is not declared, so
configuration cannot advertise it and no downstream code can rely on it.

Results never come from stdout. Every dispatch carries a result path, the agent writes its result
envelope there, and Gantry reads it. Absence is a Protocol Failure, not an inference from an exit code.
Context usage comes from whatever the adapter can actually extract, expressed as measured,
self-reported, or unknown, with no default.

Interruption is capability-dependent and honest about it. Gantry requests a stop through the mechanism
the integration exposes — a cooperative signal for a native subagent whose lifecycle belongs to the
host harness, a process signal for a detached CLI Gantry started — and then reconciles: it observes
whether the agent is still running, whether a result appeared, and whether the worktree is still being
written, before any takeover proceeds.

Driver unavailability preserves work, spends the infrastructure allowance, and then blocks. Replacement
is an explicit operator action, because changing a driver changes the data boundary.

## User Stories

1. As an operator, I want to use the harness and subscription I already pay for, so that Gantry does not require a separate per-token API key.
2. As an operator, I want to route one role to a different harness, so that I can use the best tool for a specific job.
3. As an operator, I want the same workflow guarantees regardless of which harness executes a role, so that routing is a performance choice rather than a correctness gamble.
4. As an operator, I want each integration to state exactly what it can monitor and interrupt, so that I know which guarantees apply to my setup.
5. As an operator, I want a declared capability backed by an executable proof, so that a claim is evidence rather than an assertion.
6. As an operator, I want a capability with no passing proof left undeclared, so that my configuration never advertises something unavailable.
7. As an operator, I want the harness version recorded with each capability proof, so that an upgrade that removes a capability is detectable.
8. As an operator, I want to be told plainly which guarantees my integration does not support, so that I can plan around the limitation.
9. As an operator, I want no strict context ceiling advertised for an integration that only checks between turns, so that I am not sold a guarantee that cannot be enforced.
10. As an operator, I want self-reported usage never presented as a measurement, so that I know the difference.
11. As an operator, I want unknown usage shown as unknown, so that an integration without measurement does not appear healthy at zero.
12. As an operator, I want a native subagent spawned by my harness rather than replaced by a CLI, so that my harness's own session and authentication are used.
13. As an operator, I want Gantry not to claim lifecycle control over a native subagent, so that its limits are stated rather than discovered during an incident.
14. As an operator, I want a detached CLI invoked deterministically from configuration, so that I can see exactly what will run.
15. As an operator, I want results read from a file rather than parsed from logs, so that a chatty agent cannot corrupt the semantic channel.
16. As an operator, I want a missing result file treated as a Protocol Failure, so that an exit code cannot stand in for a result.
17. As an operator, I want stdout captured for diagnosis but never interpreted as a result, so that the two roles of output stay separate.
18. As an operator, I want a gateway available for single-shot roles, so that a router or proxy setup is usable.
19. As an operator, I want file-mutating roles unable to route to a gateway, so that a single-shot HTTP call never tries to edit my repository.
20. As an operator, I want each dispatch to record the resolved driver, command, and model, so that the dashboard always shows which harness did what.
21. As an operator, I want to preview the resolved command for a role before anything runs, so that misconfiguration is caught early.
22. As an operator, I want a stop request to use whatever mechanism my integration actually exposes, so that Gantry does not pretend to force something it cannot.
23. As an operator, I want a cooperative stop honored where that is all the integration offers, so that the best available behavior is used.
24. As an operator, I want Gantry to observe whether an agent actually stopped, so that takeover never assumes it did.
25. As an operator, I want reconciliation to check for a late result before takeover, so that finished work is not thrown away.
26. As an operator, I want reconciliation to check whether the worktree is still being written, so that two agents never write to it at once.
27. As an operator, I want closing my harness not to be assumed to have stopped a detached process, so that resumption reconciles rather than guesses.
28. As an operator, I want a detached process Gantry started to be identifiable after a restart, so that reconciliation can find it.
29. As an operator, I want an unavailable driver to preserve my work, so that an infrastructure problem costs time rather than progress.
30. As an operator, I want bounded automatic retries on driver unavailability, so that a transient failure recovers without me.
31. As an operator, I want exhausted retries to block rather than substitute another driver, so that my data boundary is never changed silently.
32. As an operator, I want replacing a driver to require my explicit action, so that egress authorization and capabilities are revalidated.
33. As an operator, I want a permanent authorization or configuration failure to block immediately, so that attempts are not wasted on something only I can fix.
34. As an operator, I want reconciliation before a replacement dispatch, so that driver failure does not produce duplicate work.
35. As an operator, I want both cross-harness directions validated, so that routing works whichever harness hosts.
36. As an operator, I want each combination's limitations recorded, so that a successful native run is not presented as cross-harness support.
37. As an operator, I want tested harness versions recorded, so that I know what the support claim is based on.
38. As an operator, I want an unsupported operation rejected rather than approximated, so that an integration's gaps produce errors instead of silent wrong behavior.
39. As a Gantry maintainer, I want one adapter interface all three implementations satisfy, so that the rest of the system has a single contract.
40. As a Gantry maintainer, I want the conformance suite runnable against a newly added harness, so that support is a test result rather than an opinion.
41. As a Gantry maintainer, I want the stub drivers from demo mode to satisfy the same interface, so that the demo exercises the real seam.
42. As an auditor, I want each dispatch traceable to its actual driver and destination, so that I can tell where work ran and where content went.

## Implementation Decisions

### The adapter interface

```ts
type HarnessAdapter = {
  identity: { harness: string; version: string; kind: "native" | "detached_cli" | "gateway" };
  capabilities: IntegrationCapabilities;          // proven, not asserted
  dispatch(envelope: GtpTask, io: DispatchIo): Promise<DispatchHandle>;
  observe(handle: DispatchHandle): Promise<AgentObservation>;
  requestStop(handle: DispatchHandle, mode: "handoff" | "cancel"): Promise<StopOutcome>;
  reconcile(handle: DispatchHandle): Promise<ReconciliationResult>;
};

type DispatchIo = {
  resultPath: string;        // where the agent must write its result envelope
  workingDirectory: string;  // the PBI worktree
  diagnosticSink: string;    // stdout and stderr capture, never parsed as a result
};

type AgentObservation = {
  liveness: "running" | "exited" | "unknown";
  contextUsage: ContextUsage;
  resultPresent: boolean;
};

type StopOutcome =
  | { kind: "stopped"; evidence: string }
  | { kind: "requested_cooperatively"; evidence: string }   // honored only if the agent complies
  | { kind: "unsupported" };

type ReconciliationResult = {
  liveness: "running" | "exited" | "unknown";
  result: "present_valid" | "present_invalid" | "absent";
  worktreeActivity: "quiescent" | "active" | "unknown";
};
```

`requestStop` returning `requested_cooperatively` or `unsupported` is the point where ADR-0001 becomes
code: those variants exist so callers must handle the case where the agent was not actually stopped, and
cannot write logic that assumes it was.

### Capability declaration and conformance probes

```ts
type IntegrationCapabilities = {
  harness: string;
  harnessVersion: string;
  contextMonitoring: "per_tool_call" | "between_turns" | "self_reported" | "none";
  agentInterruption: "supported" | "cooperative_only" | "none";
  nativeSubagents: boolean;
  resultChannel: "file" | "mcp" | "both";   // determined by probe, never assumed
  stopMechanism: "process_signal" | "job_object" | "cooperative_request" | "none";
  probes: Array<{ capability: string; probe: string; passedAt: string; evidence: string }>;
};
```

Every non-`none` capability requires a passing probe. A probe is a small executable scenario run against
the installed harness: dispatch a trivial task and read usage from the result to prove monitoring at the
claimed granularity; dispatch a long-running task and request a stop to prove interruption; dispatch and
observe a native subagent to prove native spawning. Probes record the harness version, so an upgrade
invalidates them and they are re-run rather than inherited.

A capability whose probe fails or was never run is declared `none` or omitted. Spec 05 refuses to write
unvalidated declarations into configuration, so the failure mode is a missing capability rather than a
false one.

Granularity is honest by construction: `between_turns` cannot be upgraded to `per_tool_call` by a probe
that only observes turns, because the probe for `per_tool_call` requires usage observed between tool
calls within one turn.

`resultChannel` is probed rather than assumed. One probe dispatches a trivial task and checks whether the
agent wrote to the provided result path; another checks whether it submitted through the MCP tool in spec
16. An integration where file writing is unreliable — a sandbox that rewrites paths, a subagent with no
filesystem access — is discovered here rather than in production, and a combination where neither channel
works is unsupported rather than degraded. Where both work, either is accepted: duplicate submission of
identical content is already covered by submission idempotency in spec 03, so no precedence rule is
needed.

`stopMechanism` is probed for the same reason and matters most on Windows, which has no cooperative
process signal. A detached CLI there is stopped through a job object or not at all, and an integration
that cannot demonstrate either declares `agentInterruption: "none"`. The platform therefore changes the
guarantee rather than the implementation hiding the difference — which is the ADR-0001 rule applied to
an operating system instead of to a harness.

No probe and no dispatch carries a wall-clock limit. Gantry runs AFK: an agent is expected to be dispatched
and carried through, not to finish within a budget, and §6.2 establishes no elapsed-time limit anywhere in
the workflow. Duration is recorded; it is never enforced. What bounds a stuck agent is the handoff
watermark, an agent's own `needs_handoff`, or an operator cancellation — never a clock Gantry runs against
it.

### Native subagent adapter

The host harness spawns its own subagent. Gantry hands over a task envelope through a skill or MCP tool
and validates the result. Gantry does not spawn a replacement CLI for a native assignment, and does not
hold a process handle.

Consequences stated rather than worked around: liveness is `unknown` unless the integration exposes a
way to ask; `requestStop` is `cooperative_only` at best; and reconciliation relies on the result file,
the worktree activity, and elapsed time rather than on process state. A native harness can also act
outside Gantry's APIs entirely, which is recorded as a limitation of the combination rather than
mitigated with a claim.

### Detached CLI adapter

Gantry spawns another harness's CLI. Invocation is deterministic from configuration: an argv template
per role, a prompt file rather than an inline argument, the PBI worktree as the working directory, and
the result path passed explicitly.

The result channel is a file. The agent writes its result envelope to `resultPath`; Gantry reads and
validates it. Stdout and stderr are captured to the diagnostic sink for troubleshooting and are never
parsed for meaning — the explicit replacement of "free-form stdout inference as the semantic channel"
from §5.

The spawned process's identity is persisted — process identifier plus a start token written by the
adapter — so reconciliation after a Gantry restart can distinguish "still running", "exited", and "some
other process now holds that identifier". Liveness is `unknown` rather than `exited` when the identity
cannot be confirmed.

`requestStop` acts on a process Gantry started, which is the only case where `stopped` is returnable with
process evidence. The mechanism is platform-specific and declared in `stopMechanism`: a cooperative
process signal where the platform has one, a job object on Windows where it does not, and
`cooperative_request` or `none` where neither is available. An adapter that cannot demonstrate a stop
declares `agentInterruption: "none"`, and callers handle `unsupported` as they would for a native
subagent. Even where a stop succeeds, reconciliation still checks for a late-written result, because a
process can write and then exit.

Usage extraction reads whatever the harness emits in a machine-readable form. When the harness reports
usage in the result envelope, it is `self_reported`. When the adapter can observe it from a
harness-provided telemetry output, it is `measured` with the source named. Otherwise `unknown`.

### Gateway adapter

Single-shot OpenAI-compatible HTTP for router and proxy setups. No working directory, no file mutation,
no process lifecycle. `agentInterruption` is `none` — a single-shot request can be abandoned but not
interrupted — and `contextMonitoring` is whatever the response reports, typically `self_reported`.

File-mutating roles cannot route here. The restriction is enforced in configuration validation by spec
02 and again at dispatch, because a configuration written before the rule existed must not slip through.

Destination is always `remote` for egress classification in spec 04.

### Driver unavailability and replacement

Unavailability is an infrastructure failure: preserve the work, spend from the infrastructure allowance
with backoff, and on exhaustion block the execution with the gate unapproved. Gantry never substitutes
another harness, model, gateway, or endpoint automatically.

Replacement is an explicit operator action that updates the execution rule snapshot, requires the new
driver's capability declaration to be validated, and requires egress authorization for the new
destination. Affected validations are invalidated. Before any replacement dispatch, the prior assignment
and any uncertain operations are reconciled, so a driver failure does not produce duplicate work or
duplicate mutations.

Permanent failures — invalid credentials, missing binary, configuration error — block immediately
without spending retries.

### Cross-harness conformance

Four combinations are validated before support is claimed: Codex hosting Codex-native agents, OpenCode
hosting OpenCode-native agents, OpenCode hosting a role through the detached Codex CLI, and Codex hosting
a role through the detached OpenCode CLI.

Each runs the same conformance suite: the applicable acceptance scenarios for dispatch, valid and
invalid results, gates, handoff, interruption, reconciliation, and explicit resumption. Results are
recorded per combination as a support matrix with harness versions, observed capabilities, and
limitations. A passing native run establishes nothing about cross-harness support, and the matrix says so
per row rather than in aggregate.

An operation an integration does not support is rejected rather than approximated.

## Testing Decisions

**What makes a good test here.** Two layers, because this spec is where real processes enter.

Behavioral tests use the same seam as spec 01 with a scripted adapter that satisfies the real interface
and can be told to return each variant: `unsupported` stops, `unknown` liveness, late results, absent
results, invalid results, and each `ContextUsage` variant. These prove that callers handle every variant
rather than assuming success — the failure this spec exists to prevent.

Conformance tests run the real adapters against real installed harnesses. They are a separate suite,
skipped with an explicit recorded reason when the harness is absent rather than silently passing, and
their output is the support matrix. A skipped conformance run never counts as support.

**The seam.** Unchanged: `core.invoke`. The adapter is injected, so behavioral tests script it and
conformance tests supply the real one. No test reaches into an adapter's internals.

**Modules under test.** The adapter interface contract, each implementation's dispatch and result
reading, capability declaration and probe evaluation, usage extraction per adapter, stop and
reconciliation semantics, process identity persistence, the gateway role restriction, driver
unavailability handling, and support matrix recording.

**Scenarios that must exist**, from PRD §14.3 item 1:

- A declared capability without a passing probe is refused; configuration ends with the capability absent.
- A probe observing usage only between turns cannot declare `per_tool_call`.
- A harness version change invalidates existing probes and requires re-running them.
- An integration declaring `between_turns` never produces a projection claiming a strict ceiling.
- `self_reported` usage is never rendered as `measured`; absent usage is `unknown`, never zero.
- A native assignment never causes Gantry to spawn a replacement CLI.
- A native adapter reports `unknown` liveness and at most `cooperative_only` stops, and callers handle both.
- A detached CLI writes its result to the provided path and it is read and validated.
- A detached CLI that exits zero with no result file produces `missing_result`.
- A detached CLI that writes a malformed result produces `malformed_result`; its stdout is captured and never parsed for meaning.
- A detached CLI that writes its result and then exits is reconciled as `present_valid` despite having exited.
- A process identifier reused by an unrelated process yields `unknown` liveness rather than a false positive.
- A stop request to a detached process returns `stopped` with evidence; reconciliation still checks for a late result.
- An integration whose agents cannot write to the result path probes as `resultChannel: "mcp"`; one where neither channel works is unsupported rather than degraded.
- An identical result submitted through both channels produces one accepted submission and one idempotent replay.
- A platform with no cooperative process signal probes as `job_object` or, failing that, `agentInterruption: "none"` — the declared guarantee changes with the platform.
- No dispatch or probe is terminated by a wall-clock limit; a long-running agent completes and its duration is recorded, not enforced.
- A stop request to a native subagent returns `requested_cooperatively` or `unsupported`, and takeover does not proceed on the assumption that it stopped.
- Takeover is refused while worktree activity is `active` or `unknown`.
- A file-mutating role configured to a gateway is rejected at configuration validation and again at dispatch.
- A gateway dispatch is classified `remote` for egress.
- Driver unavailability preserves work, spends the infrastructure allowance with increasing backoff on the injected clock, and blocks on exhaustion without substituting a driver.
- A permanent credential failure blocks immediately without spending retries.
- Driver replacement requires operator action, a validated capability declaration, and egress authorization, and reconciles the prior assignment before dispatching.
- The support matrix records each of the four combinations separately with versions, capabilities, and limitations; a native-only pass leaves the cross-harness rows unsupported.
- An unsupported operation is rejected rather than approximated.
- A conformance suite skipped for an absent harness records the reason and does not count as support.

## Out of Scope

- **Operations, state machine, ownership, budgets** (spec 01) and **snapshot, routing configuration, limits** (spec 02).
- **Envelope contracts and Protocol Failure classification** (spec 03): this spec produces and consumes envelopes and reports which failure class occurred; the classes are spec 03's.
- **Capability declaration persistence into configuration** (spec 05): setup refuses unvalidated declarations; this spec defines what a validated declaration is and how it is proven.
- **Egress classification and enforcement** (spec 04): this spec declares each driver's processing destination; spec 04 decides what may be sent.
- **Worktree creation, watermark policy, handoff memo construction, scheduling** (spec 11): this spec provides observation and stop primitives; spec 11 decides when to use them.
- **Check execution** (spec 12): adapters dispatch agents, not checks.
- **Stub drivers** (spec 07): they implement this interface, and the demo is where the interface's variants are exercised cheaply.
- **Provider and Git operations** (spec 14).

Out of scope by product decision:

- Operating-system isolation of harness actions. A native harness can act outside Gantry's APIs; the limitation is documented per combination (§14.2, ADR-0001).
- Harness-specific conversation continuation as a cost optimization, explicitly deferred in §6.2.
- Providers beyond Codex and OpenCode as validated support. Others are compatibility candidates until they pass the conformance suite.
- Stdout as a semantic channel. §5 replaces it explicitly.
- Automatic driver substitution on failure. §6.2 forbids it.

## Further Notes

**Binding decisions.** ADR-0001 is the entire shape of this spec. The `StopOutcome` union, the
`unknown` liveness variant, the probe requirement, and the per-combination support matrix all exist so
that an absent capability is representable and unavoidable rather than something a caller can forget to
handle.

**Glossary alignment.** Integration Capability, Context Watermark, Protocol Failure, Infrastructure
Retry, and PBI Execution Ownership follow `CONTEXT.md`. The glossary's warning against a "universal
context ceiling" is why granularity is part of the capability rather than a boolean.

**Glossary gap for `/domain-modeling`.** Conformance probe, support matrix, and result path are
introduced here without entries and should get them.

**Where the risk actually sits.** Result-by-file assumes the agent can be instructed to write a file and
will comply. A harness whose subagents cannot reliably write to a given path — or whose sandbox rewrites
it — would break the semantic channel entirely, and the fallback is not stdout parsing but an MCP tool
call that submits the result, which the MCP transport in spec 16 already provides. Validating which of
the two channels each of Codex and OpenCode supports reliably is the first thing the conformance suite
should answer, because everything downstream depends on results arriving.

The second risk is probe maintenance. Probes run real harnesses, so they are slow and they break on
harness updates, which creates pressure to skip them. The mitigation is that a skipped probe means an
absent capability rather than an inherited one, so skipping degrades guarantees visibly instead of
silently.

**Sequencing note.** This spec depends on spec 03 and is depended on by spec 11, which cannot observe a
watermark or coordinate a handoff without these primitives. The adapter interface — particularly
`StopOutcome` and `ReconciliationResult` — is the piece to settle first, since spec 11's control flow is
shaped entirely by which variants it must handle.
