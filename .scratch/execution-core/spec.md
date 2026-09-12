# Execution core: operations, state machine, and persistence

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 01, wave 0)
Source: `PRD.md` §8.1, §6.1, §6.2, §5.4.6
Created: 2026-09-11

## Problem Statement

An operator wants to run a software factory through their own harness and trust its guarantees. Today
they cannot, because nothing holds the guarantees. `PRD.md` states what must never happen — a PBI
must not complete on an agent's claim, a merge must not be authorized from implementation completion
alone, a cancelled execution must not resume implicitly, a lost mutation response must not be retried
blindly, a correction budget must not reset when an agent is replaced — but it deliberately leaves the
mechanism undefined, repeating "remains to be specified" for the state machine, the operation
catalog, the persistence schema, ownership arbitration, budget accounting, and reconciliation.

The consequence is that every other part of the product has nowhere to stand. A CLI command, an MCP
tool, and a dashboard button would each have to re-implement the same invariants, and the operator's
real question — "is this state authoritative, or is it something an agent told me?" — would have three
different answers. The PRD says as much: "no interface may bypass an invariant", and "specify final
schemas and state transitions together before implementing persistence".

An operator also cannot currently distinguish the three failure modes they care most about, because
nothing records them separately: work that is waiting on them, work that is waiting on infrastructure,
and work that has exhausted its allowance and stopped.

## Solution

One shared operation core owns every state change in the factory. Every action an operator, a host
harness, or an agent can take is a named operation invoked against that core, which validates
authorization, actor provenance, current PBI Execution Ownership, the requested state transition, and
the evidence supporting it, then persists the transition and its audit record atomically and returns
either a receipt or a typed rejection.

The core carries four state machines — for executions, PBIs, gates, and external operations — where
each transition declares its allowed source states and the evidence it requires. Illegal or
under-evidenced transitions are rejected at the boundary rather than being caught later by a gate.
Canonical documents remain the source of truth for the plan; SQLite owns execution state; a status
written in a Markdown file is a projection with no authority.

External effects are handled by writing the intent before requesting the mutation, so a lost or
uncertain response becomes a reconciliation task against authoritative Git or provider state rather
than a speculative retry. Budgets are per PBI, consumed at a defined moment, and survive handoffs,
agent replacement, cancellation, and resumption.

CLI, MCP, and dashboard in later specs are transports over this core. They present state and carry
requests; they never write execution state.

## User Stories

1. As an operator, I want every factory action to go through one validated entry point, so that the CLI, the MCP server, and the dashboard cannot disagree about what is allowed.
2. As an operator, I want a rejected action to tell me which invariant refused it, so that I can fix the cause instead of guessing.
3. As an operator, I want the authoritative execution state kept separately from Markdown documents, so that editing a status line in a file cannot advance my factory.
4. As an operator, I want each execution bound to the clone it runs in, so that two clones of the same repository never share state or serialize against each other.
5. As an operator, I want all worktrees of one clone to share a single Repository Execution Unit, so that merges into that clone's target are serialized even when work happens in different directories.
6. As an operator, I want a moved clone to keep its execution history, so that relocating a directory does not orphan my work.
7. As an operator, I want my planning approval recorded against the exact artifact version I reviewed, so that a later edit cannot inherit my approval.
8. As an operator, I want an agent's claim that I approved something to be rejected, so that approval means a decision I actually made.
9. As an operator, I want approvals to be accepted only from my own command invocation or from an authenticated dashboard action, so that an agent holding an MCP connection cannot approve on my behalf.
10. As an operator, I want implementation completion and merge authorization to be separate states, so that finished code does not imply permission to integrate.
11. As an operator, I want merge authorization bound to a specific merge candidate and target revision, so that an advancing target silently invalidates stale permission instead of merging against it.
12. As an operator, I want merges serialized per Repository Execution Unit, so that two concurrent Gantry processes cannot integrate into the same target at once.
13. As an operator, I want the merge lock's scope stated plainly as one unit on one machine, so that I do not mistake it for a distributed guarantee across clones.
14. As an operator, I want a crashed process's merge lock to be reclaimable only after its operation is reconciled, so that recovery cannot integrate twice.
15. As an operator, I want a local merge to require my confirmation immediately before it happens, so that a prior plan approval never mutates my target branch on its own.
16. As an operator, I want each PBI to have at most one active execution owner, so that two harness sessions cannot drive the same slice into conflicting states.
17. As an operator, I want results from a superseded assignment retained but powerless, so that a late-returning agent cannot advance work it no longer owns.
18. As an operator, I want taking over a PBI to reconcile the previous agent first, so that takeover does not assume the old agent stopped.
19. As an operator, I want an identical repeated submission to return its original receipt, so that a retried request does not duplicate transitions, counters, or downstream dispatch.
20. As an operator, I want different content under the same submission identity rejected, so that a receipt always describes what was actually accepted.
21. As an operator, I want a corrected submission recorded as a new attempt linked to the previous one, so that history shows the correction rather than overwriting it.
22. As an operator, I want each PBI to share one correction allowance across all its gates, so that a stubborn slice cannot consume five attempts per gate.
23. As an operator, I want the first gate evaluation to consume no correction attempt, so that my allowance pays for corrections rather than for being measured.
24. As an operator, I want a correction attempt consumed when correction is dispatched, so that an interrupted cycle cannot be replayed for free.
25. As an operator, I want the correction count preserved across handoffs, agent replacement, cancellation, and resumption, so that restarting is not a way to reset the budget.
26. As an operator, I want an exhausted correction allowance to fail the gate and stop automatic correction, so that the factory stops rather than looping.
27. As an operator, I want granting extra correction attempts to be an explicit, recorded decision, so that the grant is auditable and distinct from a reset.
28. As an operator, I want infrastructure failures retried from their own allowance, so that a flaky network does not consume the budget meant for fixing code.
29. As an operator, I want infrastructure failures classified explicitly, so that an invalid agent result or a failing check is never retried as though it were a network blip.
30. As an operator, I want a permanent authorization or configuration failure to block instead of retrying, so that the factory does not waste attempts on something only I can fix.
31. As an operator, I want an exhausted infrastructure allowance to leave the execution blocked with the gate unapproved, so that merge stays prohibited.
32. As an operator, I want infrastructure blocking distinguished from an agent-reported `blocked` result, so that I am not asked for answers to a question no agent posed.
33. As an operator, I want the intent of an external mutation persisted before it is requested, so that an uncertain response can be resolved afterwards.
34. As an operator, I want an operation with an unknown outcome to block until reconciled, so that Gantry never guesses whether my Pull Request was already created.
35. As an operator, I want a confirmed-completed operation recorded from observation rather than repeated, so that reconciliation does not duplicate an external effect.
36. As an operator, I want retry permitted only after confirming the mutation did not occur, so that recovery is safe by construction.
37. As an operator, I want cancellation to stop new dispatch and preserve everything, so that stopping is not the same as discarding.
38. As an operator, I want cancellation to leave branches, worktrees, Pull Requests, and evidence untouched, so that each undo remains a separate decision I make knowingly.
39. As an operator, I want a cancelled execution to require explicit resumption, so that it cannot drift back into running.
40. As an operator, I want resumption to reconcile pending agents and operations before progressing, so that reopening my harness does not produce duplicate work.
41. As an operator, I want resumption to retain budgets, approvals, and the execution rule snapshot, so that continuing is continuing rather than starting over.
42. As an operator, I want a PBI waiting on my review to release its execution slot, so that other eligible slices keep moving while I take my time.
43. As an operator, I want a waiting PBI to reacquire capacity and revalidate before resuming active work, so that releasing a slot is not a way around the capacity limit.
44. As an operator, I want cleanup to be proposed as an explicit manifest and then authorized, so that nothing is deleted as a side effect of an outcome.
45. As an operator, I want cleanup refused while anything still depends on the artifacts, so that removal cannot strand an active execution.
46. As an operator, I want the minimum records needed to explain an execution and its external effects retained after cleanup, so that an audit survives tidying up.
47. As an operator, I want each execution to record the engine and protocol versions that governed it, so that an upgrade cannot silently reinterpret my state.
48. As an operator, I want resumption under an incompatible runtime refused, so that I am told to migrate explicitly rather than having approvals reinterpreted.
49. As an operator, I want a migration to retain the prior version's provenance and flag affected evidence, so that I know what must be revalidated.
50. As a host harness, I want to request dispatch and receive a typed rejection when a prerequisite is unmet, so that I can report the real reason instead of retrying blindly.
51. As a host harness, I want a dispatch rejected when the PBI is not eligible for capacity, dependency, or ownership reasons, so that I never start work the factory will not accept.
52. As a host harness, I want the current state projection available as a read operation, so that I can render progress without reading the database directly.
53. As a builder agent, I want a submitted result checked against current ownership before it changes anything, so that my work is preserved for audit even when my assignment was superseded.
54. As an auditor, I want each accepted transition stored atomically with its audit record, so that a crash cannot leave a state change without its explanation.
55. As an auditor, I want every transition to record which actor, channel, and rule version produced it, so that I can reconstruct who decided what and under which rules.
56. As a Gantry implementer, I want the operation catalog and the state graphs specified together, so that adding a transport means mapping onto existing operations rather than inventing new state changes.
57. As a Gantry implementer, I want one testing seam at the operation core, so that invariants are proven once instead of per transport.

## Implementation Decisions

### Shared operation core

A single in-process core module owns state changes. Its public surface is one invocation function
taking a named operation, so authorization, provenance, ownership, transition legality, and evidence
validation are enforced in one place rather than per transport.

The v1 operation catalog:

- Unit and execution lifecycle: `unit.register`, `execution.create`, `execution.cancel`, `execution.resume`, `execution.migrateRuntime`
- Planning: `plan.propose`, `plan.approve`, `plan.amend`
- PBI work: `pbi.schedule`, `pbi.dispatch`, `pbi.submitResult`, `pbi.claimOwnership`, `pbi.releaseSlot`
- Gates and correction: `gate.evaluate`, `gate.classifyFinding`, `correction.dispatch`, `correction.grantAttempts`
- Integration: `merge.authorize`, `merge.confirmLocal`, `merge.recordOutcome`
- Operations: `operation.declareIntent`, `operation.recordOutcome`, `operation.reconcile`
- Cleanup: `cleanup.propose`, `cleanup.authorize`
- Reads: `state.project`, `audit.query`

Read operations are separated from mutating operations so a transport can expose reads without a
capability token.

The request and outcome shapes, which encode the decision that provenance and idempotency are
mandatory rather than optional fields:

```ts
type OperationRequest<N extends OperationName> = {
  operation: N;
  unit: RepositoryExecutionUnitId;
  execution?: ExecutionId;
  requestId: string;                 // idempotency key, stable across retries of the same intent
  actor: {
    kind: "operator" | "agent" | "system";
    channel: "cli" | "dashboard" | "mcp" | "internal";
    provenance: ActorProvenance;     // session/token reference; never a credential value
  };
  input: OperationInput[N];
};

type OperationOutcome<N extends OperationName> =
  | { ok: true; receipt: Receipt; state: StateProjection; output: OperationOutput[N] }
  | { ok: false; rejection: Rejection };

type Rejection = {
  code:
    | "operator_channel_required"    // an agent attempted an operator-only decision
    | "not_authorized"
    | "illegal_transition"
    | "stale_assignment"             // superseded PBI Execution Ownership
    | "approval_required"
    | "approval_version_mismatch"    // artifact changed after the approval
    | "dependency_not_ready"
    | "capacity_unavailable"
    | "incomplete_evidence"
    | "correction_budget_exhausted"
    | "infrastructure_budget_exhausted"
    | "reconciliation_required"      // an operation outcome is unknown
    | "duplicate_conflict"           // same requestId, different content
    | "incompatible_runtime"
    | "lock_unavailable";
  detail: string;
  blockingState: StateRef;
};
```

Rejection codes are part of the contract, not diagnostics: transports and tests assert on codes.

### Actor provenance and the operator channel

`plan.approve`, `plan.amend`, `merge.confirmLocal`, `correction.grantAttempts`, `cleanup.authorize`,
and `execution.migrateRuntime` require `actor.kind === "operator"`. The core derives actor kind from
the transport channel; it never accepts it as an agent-supplied assertion.

- The `cli` channel may assert operator only for an invocation in an interactive operator session.
- The `dashboard` channel may assert operator only with a valid Dashboard Capability Token, scoped to
  its session and Repository Execution Unit.
- The `mcp` channel can never assert operator. An MCP request for an operator-only operation is
  rejected with `operator_channel_required`.

This resolves the PRD's requirement that "an agent's report of operator approval is insufficient"
without adding a second approval stage: the same reviewed proposal is approved once, through a
channel the core can attribute.

Every approval record stores the artifact identity, its content hash, the actor provenance, the
channel, the timestamp, and the governing rule snapshot. A changed content hash invalidates the
approval and yields `approval_version_mismatch`.

### Repository Execution Unit identity

Identity is derived from the canonical Git common directory of the checkout, resolved through its real
path. All worktrees of one clone resolve to the same common directory and therefore to the same unit.
Separate clones resolve to different common directories and stay independent even when their remotes
are identical. A remote URL is never an identity input.

Registration stores a generated unit identifier, the resolved common directory path, and a fingerprint
of stable repository properties. On open, a matching fingerprint with a changed path is treated as
relocation: the path is updated and the relocation recorded, preserving the unit identifier and its
history. A matching path with a changed fingerprint blocks and requires operator classification.

Path resolution has to be stricter than it looks, and the cases that break it are all Windows cases. A
case-insensitive filesystem means `C:\Repo` and `c:\repo` are the same directory with different strings,
so comparison is case-normalized where the filesystem is case-insensitive and exact where it is not. A
UNC path and a mapped drive letter can name the same directory, so both resolve to a canonical form before
comparison. Short 8.3 names resolve to their long form. And path length limits interact with nested
worktrees, so a resolved path exceeding the platform limit blocks at registration with a clear message
rather than failing later in an unrelated operation. Each of these is a case where two strings name one
unit, and treating them as two units would silently split an execution's history.

### Execution State Machine

Four state machines. Each transition declares allowed source states, required evidence, the required
actor kind, and the resulting state; the boundary rejects anything else.

```text
Execution
  initializing ──rule snapshot captured──> awaiting_plan_approval
  awaiting_plan_approval ──operator approval, version bound──> running
  running ──no active assignment or in-flight operation, work pending a decision──> waiting
  waiting ──capacity reacquired + state revalidated──> running
  running | waiting ──infrastructure budget exhausted | unknown operation outcome──> blocked
  blocked ──cause resolved + reconciliation complete──> running
  running | waiting | blocked ──operator cancellation──> cancelled
  cancelled ──explicit resume + reconciliation + ownership reacquired──> running
  running ──all PBIs integrated or closed──> completed

PBI
  planned ──> awaiting_dependency ──all prerequisites integrated into the applicable target──> queued
  queued ──capacity + ownership claimed──> implementing
  implementing ──> handoff_pending ──replacement dispatched──> implementing
  implementing ──agent-reported blocked with questions──> awaiting_operator
  implementing ──valid result, all criteria completed, none pending,
                  mandatory tests verified on the delivered revision──> implementation_complete
  implementation_complete ──> in_gates
  in_gates ──findings, attempts remaining──> correcting ──revalidation──> in_gates
  in_gates ──correction budget exhausted with unresolved findings──> gates_failed
  in_gates ──all applicable gates passed──> awaiting_review
  awaiting_review ──candidate and target revalidated──> merge_authorized
  merge_authorized ──serialized integration observed──> integrated
  awaiting_review | merge_authorized ──merged outside Gantry──> externally_integrated
  any ──execution cancelled──> cancelled

Gate
  pending ──> evaluating ──> passed | failed
  evaluating ──required comparison evidence invalid or absent──> blocked_incomplete_evidence
  evaluating ──evaluation prevented by infrastructure──> blocked_infrastructure
  passed ──candidate or target revision changed, or rule version changed──> pending

Operation (external effect)
  intended ──request issued──> in_flight
  in_flight ──response observed──> confirmed | failed
  in_flight ──response lost, uncertain, or process restarted──> unknown
  unknown ──authoritative Git or provider state consulted──> reconciled_completed | reconciled_not_performed
  reconciled_not_performed ──authorization and validation still satisfied──> intended
```

Only `reconciled_not_performed` permits reissuing a mutation. `unknown` blocks. `awaiting_dependency`
and `awaiting_review` are scheduling and review states, distinct from `awaiting_operator`, which is
reserved for an agent-reported `blocked` result carrying questions. `blocked_infrastructure` is
likewise distinct from `awaiting_operator`.

A gate returning to `pending` when the candidate, target, or rule version changes is what implements
"a changed target or candidate invalidates the comparison"; approval is never carried across.

### Budget accounting

**Correction Budget.** One allowance per PBI, default five, shared by all of that PBI's gates. It is
consumed when `correction.dispatch` is accepted, not when revalidation completes — so an interrupted
cycle stays consumed and cannot be replayed for free, and a resume continues the same attempt without
consuming another. The initial `gate.evaluate` consumes nothing. Exhaustion with unresolved findings
moves the PBI to `gates_failed`, stops automatic correction, and keeps merge prohibited.
`correction.grantAttempts` is an operator-only operation that records an additive grant with its
reason; there is no reset. Handoff, agent replacement, cancellation, and resumption never alter the
counter.

**Infrastructure Retry.** A separate allowance of three automatic retries after an initial failure,
tracked per operation class, with exponential backoff and jitter from a configured base. It never
consumes correction attempts and never approves a gate. Failure classification is explicit:

| Class | Examples | Behavior |
|---|---|---|
| Infrastructure | driver process unavailable, network timeout, provider rate limit, exit without any result | retry from the infrastructure allowance |
| Protocol | missing or malformed result, wrong role payload, schema violation | Protocol Failure; never retried as infrastructure |
| Deterministic finding | a check ran and reported findings or a failing assertion | gate failure; correction path |
| Permanent | invalid or insufficient credentials, missing approval, configuration error | block immediately; no retry |

An operation whose outcome is uncertain must reach `reconciled_not_performed` before any retry; the
infrastructure allowance is not permission to repeat an unverified mutation.

### Operation intent, idempotency, and reconciliation

`operation.declareIntent` persists the intended external effect — its class, target, candidate,
authorization reference, and requestId — before the mutation is requested. The core refuses to issue a
mutation without a persisted intent.

Idempotency is keyed on `requestId` within the unit and execution. An accepted request replayed with
identical content returns the original receipt without repeating transitions, counters, acceptance
events, or downstream dispatch. Identical `requestId` with different content is rejected with
`duplicate_conflict`. A corrected submission uses a new `requestId` carrying a link to the previous
attempt; the link preserves history and does not bypass ownership, role, or transition checks.

Acceptance is atomic: the state transition, the receipt, the audit record, and any counter change are
written in one transaction. A crash either leaves all of it or none of it.

### Merge serialization

Serialization is a lease row in SQLite, acquired in an immediate transaction, scoped to one Repository
Execution Unit, holding the owner identity, a heartbeat, and an expiry. An expired lease may be taken
only after the previous holder's operation has been reconciled; an expired lease whose operation is
`unknown` blocks with `reconciliation_required`. The scope is stated explicitly in the operator-facing
projection: one unit on one machine, not a distributed lock across clones (per ADR-0002 and §8.1).

### Capacity accounting

A PBI occupies an execution slot while it has an active assignment or an in-flight operation. Entering
`awaiting_review` or `awaiting_operator` with neither active releases the slot while preserving its
worktree, evidence, and state. Leaving those states requires `pbi.claimOwnership` to reacquire a slot
and revalidate dependency readiness and current target; releasing a slot is never a path around the
limit. The limit values themselves come from spec 02.

### Cancellation, resumption, and cleanup

`execution.cancel` stops new dispatch, marks the execution cancelled, and enqueues reconciliation of
active assignments and in-flight operations. It deletes nothing, closes no Pull Request, reverts no
commit, and resets no branch.

`execution.resume` is operator-only. It requires every `unknown` operation reconciled and every active
assignment reconciled, then reacquires current ownership. It retains budgets, approvals, and the rule
snapshot, and never issues a speculative duplicate dispatch.

Cleanup is two steps. `cleanup.propose` returns a manifest listing the exact local paths, branches,
provider objects, and evidence records affected, plus the dependency and pending-operation checks it
ran. `cleanup.authorize` is operator-only, references a specific manifest, and is refused if anything
changed since the proposal or if any active execution or unresolved operation still depends on the
artifacts. Records required to explain the execution and its external effects are always retained.

### Version compatibility

Each execution records the engine version, the GTP protocol version, and the rule snapshot identity
that governed it. Resumption under a different engine or protocol version requires a declared
compatibility range. Outside it, the execution is preserved and resumption is rejected with
`incompatible_runtime`. `execution.migrateRuntime` is operator-only, retains the prior version
provenance, and marks affected evidence and approvals for revalidation.

### Persistence

SQLite at `~/.gantry/gantry.sqlite` in WAL mode, rows scoped by Repository Execution Unit. WAL is a
storage choice; concurrency control remains the lease, the ownership checks, and the transactions
above. Schema versioning is forward-only with an explicit version check on open; an unknown schema
version refuses to open rather than guessing.

Record families and their responsibilities:

| Family | Responsibility |
|---|---|
| Units | Unit identity, resolved common directory, fingerprint, relocation history |
| Executions | State, engine and protocol versions, rule snapshot reference, capacity holdings |
| PBIs | State, dependency readiness, budgets, current assignment |
| Assignments | Ownership generation, role, driver reference, supersession |
| Proposals and approvals | Artifact identity and content hash, actor provenance, channel, invalidation |
| Gates and findings | Subject revision, rule and tool versions, evidence completeness status |
| Operations and submissions | Intent, requestId, receipt, outcome, reconciliation result |
| Audit | Transition log with actor, channel, rule version, redacted references |

### Documents are projections

Canonical Markdown documents remain the source of truth for the plan: spec content, acceptance
criteria, PBI decomposition, dependencies, governance. They never carry execution authority. A status
rendered in a document is a projection of the core's state. The core neither reads nor trusts a
document status field when deciding a transition.

## Testing Decisions

**What makes a good test here.** A test drives the core through `invoke` and asserts only on what the
operator or a transport can observe: the returned receipt or rejection code, and the subsequent state
projection. Tests never assert on SQL, table or column names, module layout, or the order of internal
calls — those change freely. A test that would still pass after the persistence layer is rewritten,
and would fail if an invariant were removed, is the target.

**The seam.** One seam: the operation core's `invoke`, called in process. Below it, two real
dependencies and two fakes:

- Real temporary SQLite database file, WAL enabled, one per test, deleted afterwards. The database is
  real because WAL behavior, immediate transactions, and lease contention are part of what is being
  specified.
- Real temporary Git repository built by a fixture helper, because unit identity is derived from an
  actual Git common directory, and worktree and clone relationships must be genuine.
- Fake harness driver returning scripted envelopes, including malformed results, late results from
  superseded assignments, and process exits with no result.
- Fake check adapter returning scripted findings, including structurally incomplete evidence.

An injected clock drives backoff, heartbeats, and lease expiry. No test sleeps.

**Modules under test.** The operation core and everything it owns: the operation catalog and its
authorization and provenance rules, the four state machines, budget accounting, operation intent and
reconciliation, idempotency and receipts, the merge lease, capacity accounting, cancellation,
resumption, cleanup authorization, version compatibility, and the persistence layer behind them — all
exercised only through `invoke`.

**Concurrency.** Lease and ownership contention are tested across two separate OS processes against
the same database file, not two async calls in one process. An in-process mutex would pass a
same-process test while failing the actual requirement.

**Prior art.** None — this repository has no code. This spec establishes the convention, which later
specs follow rather than re-litigate: Vitest as the runner (consistent with the approved TypeScript
adapter set in PRD §14.1), tests under a top-level `tests/` directory, fixture builders for the
temporary repository and database, and named fake drivers and adapters shared across specs.

**Scenarios that must exist**, drawn from PRD §14.3 items 3, 6, and 7:

- An identical submission replayed returns the original receipt with no second transition, no counter
  change, and no downstream dispatch.
- The same requestId with altered content is rejected `duplicate_conflict`.
- A result from a superseded assignment is stored and rejected `stale_assignment`, leaving state
  unchanged.
- Five correction attempts are consumed, the sixth is rejected `correction_budget_exhausted`, and the
  gate is `failed`; an operator grant then permits further attempts without resetting the count.
- A correction cycle interrupted mid-flight and resumed does not consume a second attempt and does not
  return the consumed one.
- Three infrastructure retries occur with increasing backoff on the injected clock, the fourth blocks,
  and the correction counter is untouched throughout.
- An operation whose response is lost becomes `unknown` and blocks `reconciliation_required`;
  reconciliation to `reconciled_completed` records the outcome without reissuing, and to
  `reconciled_not_performed` permits exactly one reissue.
- A crash simulated between intent and outcome leaves a reconcilable intent, never a silent gap.
- Cancellation preserves branches, worktrees, evidence, and receipts; resumption reconciles first,
  retains budgets and the rule snapshot, and issues no duplicate dispatch.
- An MCP-channel request for `plan.approve` is rejected `operator_channel_required`.
- An approval is invalidated by a changed artifact content hash and yields
  `approval_version_mismatch`.
- Two worktrees of one clone resolve to one unit and serialize; two clones of the same remote resolve
  to two units and do not.
- A relocated clone keeps its unit identifier and history.
- On a case-insensitive filesystem, paths differing only in case resolve to one unit; on a case-sensitive
  one, they do not.
- A UNC path and a mapped drive letter naming the same directory resolve to one unit.
- A resolved path exceeding the platform's length limit blocks at registration with a clear message.
- Merge authorization is invalidated by an advanced target revision and requires revalidation.
- A `passed` gate returns to `pending` when the candidate revision or rule version changes.
- A cleanup authorization referencing a stale manifest, or one with a dependent active execution, is
  refused.
- Resumption under an out-of-range engine or protocol version is rejected `incompatible_runtime` with
  the execution preserved.

**Parity tests for later transports.** Each transport spec adds exactly one test proving its commands
or tools delegate to a core operation and write no execution state of their own. Behavior stays tested
at the core.

## Out of Scope

Everything below belongs to a named sibling spec in [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md)
and must not be absorbed here.

- **Config values and governance resolution** (spec 02): ConfigStore layering and validation, Execution Rule Snapshot capture and migration mechanics, Governance Precedence resolution, and the numeric limits this spec consumes — capacity, correction, and infrastructure defaults. This spec defines the accounting; spec 02 defines the values and where they come from.
- **GTP payloads** (spec 03): role-specific task and result contract shapes, boundary schema validation, status semantics, and Implementation Completion evidence rules. This spec defines the transitions `pbi.dispatch` and `pbi.submitResult` drive, and that ownership is checked before content; the envelope content is spec 03's.
- **Redaction, retention, and egress** (spec 04): what may be persisted or displayed and what must leave the local environment. This spec's audit family stores references; spec 04 decides what a safe reference is.
- **Machine and repository onboarding** (specs 05, 06): `gantry setup`, `gantry init`, artifact location mapping, verification command approval, preparation authorization, and Dirty Working Tree detection and classification. This spec assumes a registered unit and a captured snapshot exist.
- **Spec and PBI authoring and validation** (specs 08, 09): lint rules, Requirement Review, context budget estimation, and dependency declaration schemas. This spec stores approvals and dependency readiness; it does not compute them.
- **Harness adapters** (spec 10): actual Codex and OpenCode invocation, capability declaration, usage extraction, and interruption. This spec's driver is a fake.
- **PBI execution loop** (spec 11): worktree creation, watermark observation, handoff memo construction, and micro-commits. This spec owns the states those actions move between.
- **Verification and gates** (specs 12, 13, 15): check adapters, comparison evidence normalization, the entropy differential decision, adversarial review, and baseline transitions. This spec owns gate state and evidence-completeness blocking, not what constitutes a finding.
- **Git and provider operations** (spec 14): branch and worktree commands, Pull Request creation and observation, provider identity, and protection authority. This spec owns the operation intent and reconciliation contract those operations use.
- **Transports** (specs 16, 17): the MCP tool catalog, the dashboard, SSE, Settings, and Dashboard Capability Token issuance. This spec defines the channel and provenance rules those transports must satisfy; token issuance is spec 17's.
- **Compound learning and release engineering** (specs 18, 19).

Also out of scope by product decision, not deferral:

- Distributed locking across clones or machines. Serialization is scoped to one Repository Execution Unit (§8.1, ADR-0002).
- A background service that progresses work after the host harness closes. AFK Execution requires the harness to remain active, and closure requires explicit resumption (§6.1, ADR-0001).
- Operating-system isolation of harness actions. The core guarantees the transitions it accepts; a native harness can act outside Gantry's APIs and that limitation is documented rather than papered over (§14.2).
- Multi-user authorization. The operator channel distinction is a provenance mechanism, not an authentication system (§8.2).

## Further Notes

**Binding decisions.** ADR-0001 fixes the harness-first control boundary: this core validates
transitions and authorizes integration; it does not supervise agents. ADR-0002 fixes worktree
isolation and serialized integration, which the unit-scoped lease and candidate/target revalidation
implement. Nothing here contradicts either.

**Glossary alignment.** The state and record names follow `CONTEXT.md`. In particular, Implementation
Completion and Merge Authorization are separate states because the glossary defines them as separate
concepts and marks the conflation as a term to avoid; `awaiting_dependency` exists because Dependency
Readiness is explicitly not an agent-reported blocked result; and `blocked_infrastructure` exists
because Infrastructure Retry is explicitly not a Correction Attempt.

**Glossary gap for `/domain-modeling`.** Three concepts this spec introduces have no glossary entry
yet and should get one: the shared operation core itself, the operation intent record that precedes an
external mutation, and the rejection code as a contractual value rather than a diagnostic string.

**Where the risk actually sits.** The three decisions most likely to need revision under real use are
the moment a correction attempt is consumed (dispatch, chosen so interruption cannot be replayed for
free), the derivation of unit identity from the Git common directory (which must be verified on
Windows, still an unvalidated platform per §14.1), and the lease heartbeat and expiry values, which
trade recovery latency against the risk of reclaiming from a live holder. Each is isolated behind the
core's interface, so revising one does not ripple into the transports.

**Sequencing note.** Specs 02 and 03 are near-simultaneous with this one: the state machine is hollow
without envelope evidence, and envelope evidence has nowhere to land without the state machine. They
are separate specs because their contracts are separable, but expect their issues to interleave, and
expect spec 03 to propose small additions to this catalog rather than a parallel one.
