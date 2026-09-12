## Spec 01 — execution-core

This spec owns the single place where factory state changes: one shared operation core whose `invoke` entry point validates authorization, actor provenance, PBI Execution Ownership, transition legality, and supporting evidence before persisting anything, plus the four Execution State Machines (execution, PBI, gate, external operation), the SQLite record families behind them, Repository Execution Unit identity, Correction Budget and Infrastructure Retry accounting, operation intent and Operation Reconciliation, Execution Cancellation and Resumption, Cleanup Authorization, and engine/protocol version compatibility. Its risk is concentrated in three places the spec names itself — the moment a Correction Attempt is consumed (dispatch, not revalidation), the derivation of unit identity from the Git common directory on an unvalidated Windows platform, and the lease heartbeat/expiry tradeoff between recovery latency and reclaiming from a live holder — but the structural risk is different and larger: this is the first code in an empty repository, so slice 01 sets conventions (runner, fixture kit, transition primitive) that all eighteen other specs inherit and none of them will re-litigate. A second structural risk is that four state machines plus twenty-five operations create a natural temptation toward a horizontal "define all the types first" slice, which would produce nothing demoable for a long time; the breakdown below deliberately makes each slice carry its own types, persistence, handlers, and projection.

### Slices

---

**01 — Operation core seam and Repository Execution Unit registration**

- **What to build**: Bootstrap the repository (TypeScript, Vitest, `tests/` layout) and stand up the operation core's single `invoke` entry point with the `OperationRequest` / `OperationOutcome` / `Rejection` shapes as a contract, including the full rejection code vocabulary even though most codes are unreachable until later slices. Open a real WAL SQLite database with a forward-only schema version check that refuses to open an unknown version, and implement the atomic transition primitive — state change, receipt, audit record, and any counter change written in one transaction — plus `requestId` idempotency so an accepted request replayed with identical content returns its original receipt without repeating anything. Prove all of it end-to-end with the first two real operations, `unit.register` and `audit.query`, and a minimal `state.project`. Unit identity derives from the canonical Git common directory resolved through its real path, with case-normalization where the filesystem is case-insensitive and exact comparison where it is not, UNC and mapped-drive and 8.3 forms resolved to a canonical form, a resolved path over the platform length limit blocking at registration, a matching fingerprint with a changed path recorded as relocation preserving the unit identifier, and a matching path with a changed fingerprint blocking for operator classification. Ship the shared fixture kit this spec and every later spec binds to: temporary WAL database, temporary real Git repository with worktree and clone helpers, injected clock, named fake harness driver, named fake check adapter, and state builders that place a unit/execution/PBI/gate at a named state.
- **Acceptance criteria**:
  - Two worktrees of one clone resolve to one Repository Execution Unit; two clones of the same remote resolve to two, and a remote URL is never an identity input.
  - A relocated clone keeps its unit identifier and prior history; a changed fingerprint at the same path is rejected rather than merged.
  - Paths differing only in case resolve to one unit on a case-insensitive filesystem and to two on a case-sensitive one; a path exceeding the platform limit is rejected at registration with a message naming the limit.
  - Replaying an accepted `unit.register` with the same `requestId` and identical content returns the original receipt and produces no second audit record; different content under the same `requestId` returns `duplicate_conflict`.
  - A process killed mid-transition leaves either the complete transition with its audit record or neither, never a state change without its explanation.
  - Opening a database whose schema version is unknown to the running engine fails with a distinct error instead of proceeding.
  - No test asserts on SQL, table names, column names, or module layout; every assertion is on a receipt, a rejection code, or a state projection.
- **Blocked by**: None. Needs the redaction sink interface from `data-handling` for audit references — see risks; build against a declared interface and integrate when it lands.
- **Parallelizable with**: Nothing intra-spec; this is the bootstrap.

---

**02 — Execution lifecycle, operator channel provenance, and version-bound Planning Approval**

- **What to build**: Implement the execution state machine's entry path — `initializing` to `awaiting_plan_approval` on rule snapshot capture, to `running` on a version-bound operator approval — via `execution.create`, `plan.propose`, `plan.approve`, and `plan.amend`. The core derives actor kind from the transport channel and never accepts it as an agent-supplied assertion: the `cli` channel may assert operator only for an interactive operator session, the `dashboard` channel only with a valid Dashboard Capability Token scoped to its session and unit, and the `mcp` channel never. Every approval record stores artifact identity, content hash, actor provenance, channel, timestamp, and the governing Execution Rule Snapshot identity, and a changed content hash invalidates the approval. The execution record also captures the engine and GTP protocol versions that govern it.
- **Acceptance criteria**:
  - An `mcp`-channel request for `plan.approve`, `plan.amend`, `merge.confirmLocal`, `correction.grantAttempts`, `cleanup.authorize`, or `execution.migrateRuntime` is rejected `operator_channel_required` for every one of them, driven from a table so a later-added operator-only operation cannot be forgotten.
  - A `dashboard`-channel approval without a valid capability token, or with a token scoped to a different unit, is rejected; with a valid scoped token it is accepted and the provenance is recorded.
  - Approving an artifact, editing it, then acting on the approval yields `approval_version_mismatch`.
  - An execution cannot leave `initializing` without a captured rule snapshot reference, and cannot reach `running` without a recorded operator approval bound to the approved artifact version.
  - `state.project` reports the execution state, the approval provenance and channel, and the governing snapshot identity, with no field that could hold a credential value.
- **Blocked by**: 01. Needs the Execution Rule Snapshot capture contract from `config-and-snapshot`; needs normalized content hashing (line endings) from `data-handling`; needs the plan version hash definition from `slicing-and-approval`; needs the capability token verification interface from `dashboard`.
- **Parallelizable with**: 03, 05, 06, 08 (all can start against 01's state builders).

---

**03 — PBI Execution Ownership, dispatch, and capacity accounting**

- **What to build**: Implement the PBI state machine from `planned` through `awaiting_dependency`, `queued`, `implementing`, `handoff_pending`, and `awaiting_operator`, via `pbi.schedule`, `pbi.dispatch`, `pbi.claimOwnership`, and `pbi.releaseSlot`, using the fake harness driver. An Assignment record carries an ownership generation, role, driver reference, and supersession marker, so a PBI has at most one active execution owner and taking over reconciles the previous assignment before claiming. A PBI occupies an execution slot while it has an active assignment or an in-flight operation; entering `awaiting_review` or `awaiting_operator` with neither releases the slot while preserving worktree, evidence, and state, and leaving those states requires `pbi.claimOwnership` to reacquire a slot and revalidate Dependency Readiness and the current target. The execution's `running` ⇄ `waiting` transitions follow from this.
- **Acceptance criteria**:
  - `pbi.dispatch` against a PBI with unmet prerequisites is rejected `dependency_not_ready`, and against a full capacity limit `capacity_unavailable`; neither leaves a partial assignment.
  - A second `pbi.claimOwnership` supersedes the first, increments the ownership generation, and reconciles the prior assignment before the new one becomes active.
  - Releasing a slot on entry to `awaiting_operator` frees capacity for another eligible PBI, and the released PBI cannot resume active work without reacquiring a slot and passing revalidation.
  - `awaiting_dependency`, `awaiting_review`, and `awaiting_operator` are distinguishable in `state.project`, and only `awaiting_operator` is reachable from an agent-reported blocked result carrying questions.
  - An execution with no active assignment and no in-flight operation but work pending a decision projects as `waiting`, not `running`.
- **Blocked by**: 01. Needs the role-specific task envelope shape from `gtp-protocol`; needs capacity limit values from `config-and-snapshot`.
- **Parallelizable with**: 02, 05, 06, 08.

---

**04 — Result Submission identity, receipts, and stale assignment rejection**

- **What to build**: Implement `pbi.submitResult` and the transition to `implementation_complete`. Ownership is checked before content, so a result arriving from a superseded assignment is stored for audit and rejected without changing state. Submission identity follows the operation core's `requestId` idempotency with submission-specific rules layered on: an identical accepted replay returns the prior receipt with no second transition, no counter change, and no downstream dispatch; identical identity with corrected content is rejected `duplicate_conflict`; and a genuine correction arrives as a new submission carrying a link to the previous attempt, which preserves history without bypassing ownership, role, or transition checks. Extend `state.project` to show the current submission, its receipt, and the chain of linked attempts.
- **Acceptance criteria**:
  - A late result from a superseded assignment is persisted and rejected `stale_assignment`, and the PBI's state and counters are byte-identical before and after.
  - Replaying an accepted submission returns the original receipt and triggers no downstream dispatch, verifiable through the fake harness driver's call record.
  - A corrected submission with a new identity linking the prior attempt is accepted, and both attempts remain queryable through `audit.query`.
  - A result that does not satisfy the completion evidence rules leaves the PBI in `implementing` with a typed rejection rather than advancing to `implementation_complete`.
  - `implementation_complete` is reachable without any merge permission being granted, and `state.project` exposes them as separate facts.
- **Blocked by**: 03. Needs the result contract, status semantics, and Implementation Completion evidence rules from `gtp-protocol`; needs the `extensions` lifting rule from `gtp-protocol` for the persisted envelope shape.
- **Parallelizable with**: 02, 05, 06, 08.

---

**05 — Gate state, Correction Budget accounting, and operator grants**

- **What to build**: Implement the gate state machine (`pending`, `evaluating`, `passed`, `failed`, `blocked_incomplete_evidence`, `blocked_infrastructure`) and the PBI's `in_gates` ⇄ `correcting` loop through `gate.evaluate`, `gate.classifyFinding`, `correction.dispatch`, and `correction.grantAttempts`, using the fake check adapter. One Correction Budget per PBI, shared by all its gates, consumed when `correction.dispatch` is accepted rather than when revalidation completes, so an interrupted cycle stays consumed and a resume continues the same attempt. The initial `gate.evaluate` consumes nothing. Exhaustion with unresolved findings moves the PBI to `gates_failed`, stops automatic correction, and keeps merge prohibited; `correction.grantAttempts` records an additive operator grant with its reason and there is no reset. A `passed` gate returns to `pending` when the merge candidate revision, the target revision, or the rule version changes, and structurally incomplete comparison evidence fails closed into `blocked_incomplete_evidence`.
- **Acceptance criteria**:
  - Five Correction Attempts are consumed, the sixth is rejected `correction_budget_exhausted`, and the gate reads `failed` with the PBI in `gates_failed`.
  - An operator grant of further attempts permits correction to continue while the cumulative consumed count is preserved and visible, never reset.
  - A correction cycle interrupted between dispatch and revalidation and then resumed consumes no second attempt and returns none.
  - A `passed` gate returns to `pending` when the candidate revision changes, when the target revision advances, and when the rule version changes — three separate cases, each asserted.
  - A check result missing the identity or context needed for comparison leaves the gate `blocked_incomplete_evidence` and the PBI unable to reach `awaiting_review`.
  - The Correction Budget is unchanged across a handoff, an agent replacement, a cancellation, and a resumption.
- **Blocked by**: 01. Needs the normalized finding shape and Evidence Completeness rules from `verification-adapters`; needs the correction budget default value from `config-and-snapshot`.
- **Parallelizable with**: 02, 03, 06, 08.

---

**06 — Operation intent, Operation Reconciliation, and Infrastructure Retry**

- **What to build**: Implement the external-operation state machine (`intended`, `in_flight`, `confirmed`, `failed`, `unknown`, `reconciled_completed`, `reconciled_not_performed`) via `operation.declareIntent`, `operation.recordOutcome`, and `operation.reconcile`. The core refuses to issue a mutation without a persisted intent carrying class, target, candidate, authorization reference, and `requestId`. An uncertain or lost response becomes `unknown` and blocks with `reconciliation_required`; only `reconciled_not_performed` permits reissuing, and `reconciled_completed` records the outcome from observation without repeating the effect. Layer the explicit failure classification over this — infrastructure, protocol, deterministic finding, permanent — where only the infrastructure class draws on a separate allowance of three automatic retries with exponential backoff and jitter on the injected clock, a Protocol Failure is never retried as infrastructure, and a permanent authorization or configuration failure blocks immediately. Exhausting the infrastructure allowance leaves the execution `blocked` with the gate unapproved, distinct from an agent-reported blocked result.
- **Acceptance criteria**:
  - A mutation attempted without a persisted intent is refused, and a crash simulated between intent and outcome leaves a reconcilable intent rather than a silent gap.
  - An operation whose response is lost reads `unknown` and blocks `reconciliation_required`; reconciling to `reconciled_completed` records the outcome without reissuing, and to `reconciled_not_performed` permits exactly one reissue.
  - Three Infrastructure Retries occur at increasing intervals on the injected clock, the fourth is rejected `infrastructure_budget_exhausted`, and the Correction Budget counter is untouched throughout.
  - Each of the four failure classes routes to its specified behavior, asserted one case per class; a malformed result is never retried and a permanent credential failure never consumes an attempt.
  - An execution blocked by infrastructure exhaustion is distinguishable in `state.project` from one in `awaiting_operator`, and no gate is approved in either case.
  - No test sleeps; all backoff and expiry assertions are driven by the injected clock.
- **Blocked by**: 01.
- **Parallelizable with**: 02, 03, 05, 08.

---

**07 — Merge Authorization binding and serialized integration**

- **What to build**: Implement `merge.authorize`, `merge.confirmLocal`, and `merge.recordOutcome`, and the PBI transitions `awaiting_review` → `merge_authorized` → `integrated`, plus `externally_integrated` for a delivery merged outside Gantry. Merge Authorization is bound to a specific merge candidate and target revision, and a change to either invalidates it and forces revalidation — Implementation Completion alone never grants it. Serialization is a lease row acquired in an immediate transaction and scoped to one Repository Execution Unit, holding owner identity, heartbeat, and expiry; an expired lease may be taken only after the previous holder's operation has been reconciled, and an expired lease whose operation is `unknown` blocks with `reconciliation_required`. A direct local merge requires `merge.confirmLocal` immediately before the mutation, separate from any prior plan approval, and the projection states the lease scope plainly as one unit on one machine rather than a distributed guarantee.
- **Acceptance criteria**:
  - Merge Authorization granted against a target revision and then invalidated by an advanced target is refused until revalidated, and the invalidation is visible in `state.project`.
  - A PBI in `implementation_complete` cannot reach `merge_authorized` without the gate and review states in between.
  - Lease contention is proven across two separate operating-system processes against the same database file, not two asynchronous calls in one process; the loser receives `lock_unavailable`.
  - An expired lease whose prior holder's operation is `unknown` is not reclaimable and yields `reconciliation_required`; once reconciled, reclaiming succeeds.
  - A local merge without an immediately preceding `merge.confirmLocal` from the operator channel is refused even when a Planning Approval exists.
  - The operator-facing projection names the serialization scope as one Repository Execution Unit on one machine.
- **Blocked by**: 06 (the lease reclaim rule depends on the operation state machine), 05 (merge is reachable only past the gate states). Needs candidate preparation and target revision observation from `git-integration`; needs Provider Protection Authority observation from `git-integration` for the externally-integrated path.
- **Parallelizable with**: 08.

---

**08 — Execution Cancellation, Resumption, Cleanup Authorization, and runtime compatibility**

- **What to build**: Implement `execution.cancel`, `execution.resume`, `cleanup.propose`, `cleanup.authorize`, and `execution.migrateRuntime`. Cancellation stops new dispatch, marks the execution cancelled, and enqueues reconciliation of active assignments and in-flight operations while deleting nothing, closing no Pull Request, reverting no commit, and resetting no branch. Resumption is operator-only, requires every `unknown` operation and every active assignment reconciled before progressing, reacquires current ownership, retains budgets, approvals, and the Execution Rule Snapshot, and never issues a speculative duplicate dispatch. Cleanup is two steps: `cleanup.propose` returns a manifest of the exact local paths, branches, provider objects, and evidence records affected plus the dependency and pending-operation checks it ran, and `cleanup.authorize` is operator-only, references a specific manifest, and is refused if anything changed since the proposal or if any active execution or unresolved operation still depends on the artifacts. Resumption outside the declared engine and protocol compatibility range is rejected `incompatible_runtime` with the execution preserved, and `execution.migrateRuntime` retains the prior version provenance and marks affected evidence and approvals for revalidation.
- **Acceptance criteria**:
  - After cancellation, branches, worktrees, Pull Requests, evidence, and receipts are all still present and byte-identical, and no new dispatch is accepted.
  - A cancelled execution cannot reach `running` by any path other than `execution.resume` from the operator channel.
  - Resumption with an unreconciled `unknown` operation is rejected; after reconciliation it succeeds, retains the Correction Budget and rule snapshot, and the fake harness driver records no duplicate dispatch.
  - `cleanup.authorize` referencing a stale manifest is refused, as is one whose artifacts a live execution or unresolved operation still depends on.
  - After an authorized cleanup, the records needed to explain the execution and its external effects remain queryable through `audit.query`.
  - Resumption under an out-of-range engine or protocol version is rejected `incompatible_runtime` with the execution intact; a migration records the prior version and flags affected approvals for revalidation.
- **Blocked by**: 06 (cancellation and cleanup both depend on the operation reconciliation contract), 02 (operator channel).
- **Parallelizable with**: 07.

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Redaction sink enforcement interface | `data-handling` | 01 (audit references), then every writer in 02–08 |
| Normalized content hashing (line-ending normalization) | `data-handling` | 02 (approval content hashes), 05 (rule version identity) |
| Execution Rule Snapshot capture and identity | `config-and-snapshot` | 02 |
| Capacity limit values | `config-and-snapshot` | 03 |
| Correction Budget default, Infrastructure Retry allowance and backoff base | `config-and-snapshot` | 05, 06 |
| Role-specific task envelope shape | `gtp-protocol` | 03 |
| Result contract, status semantics, Implementation Completion evidence rules | `gtp-protocol` | 04 |
| `extensions` lifting rule (unknown keys into a side field) | `gtp-protocol` | 01 (persistence shape), 04 |
| Plan version hash definition | `slicing-and-approval` | 02 |
| Normalized finding shape and Evidence Completeness rules | `verification-adapters` | 05 |
| Candidate preparation and target revision observation | `git-integration` | 07 |
| Dashboard Capability Token verification interface | `dashboard` | 02 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| Shared operation core `invoke`, request/outcome shapes, rejection code vocabulary | 01 | all 18 |
| Repository Execution Unit identity and registration | 01 | 05, 06, 11, 14, 17 |
| Atomic transition + audit record primitive, `requestId` idempotency | 01 | 04, and every writer |
| Shared test fixture kit (temp WAL database, temp Git repository, injected clock, named fake driver and check adapter, state builders) | 01 | all 18 |
| Operator channel and provenance rule, `operator_channel_required` | 02 | 09, 14, 16, 17, 06 |
| Approval record shape and version-mismatch invalidation | 02 | 08, 09, 15 |
| PBI state machine and ownership generation / supersession | 03 | 10, 11 |
| Capacity accounting and slot release/reacquire | 03 | 11 |
| Result Submission identity and receipt reuse | 04 | 03, 10, 11 |
| Gate state machine and Correction Budget accounting | 05 | 12, 13, 15 |
| Operation intent and Operation Reconciliation contract, failure classification, Infrastructure Retry | 06 | 10, 14 |
| Merge serialization lease and authorization invalidation rule | 07 | 14 |
| Cleanup manifest and Cleanup Authorization | 08 | 07, 14 |
| Execution version compatibility and migration provenance | 08 | 02, 19 |

### Risks / judgement calls

**The state-builder fixture is load-bearing and slightly dishonest.** To get 02, 03, 05, 06, and 08 running concurrently off slice 01, I put state builders in the fixture kit that can place an execution, PBI, or gate at a named state. Where the operations exist they should replay through `invoke`; where they do not yet, the builder inserts directly. That shortcut can mask an illegal transition, so each later slice must replace the direct-insert path for the states it makes reachable. If the operator prefers correctness over parallelism here, the alternative is a strict 01 → 02 → 03 → 04 → 05 chain, which serializes most of the spec behind one agent.

**Windows path canonicalization stayed inside slice 01.** UNC forms, mapped drives, 8.3 names, case-insensitivity detection, and path length limits are a meaningful chunk of work and I was tempted to split them out. I did not, because they are the same function as the base identity derivation and a split would put two agents in one file for no parallelism gain. The consequence is that slice 01 is the largest slice here. It is also the only slice whose acceptance criteria cannot be fully proven on the development platform — §14.1 lists Windows as unvalidated — so some of those criteria will be proven by unit-level tests over a path-resolution seam rather than against a real Windows filesystem, and that should be stated when the issue is written.

**Merge authorization ownership overlaps spec 14.** The handoff's lock table assigns "merge authorization binding and its invalidation rule" to `git-integration`, while this spec owns `merge.authorize` and the candidate/target revalidation rule. I split it as: slice 07 owns the *state, the binding, and the invalidation*; `git-integration` owns the Git and provider mechanics and the observation that feeds them. This reading is consistent with both specs but it is an interpretation, not something either document states, and it is worth confirming before 07 and 14's issues are written in parallel.

**Slice 05 bundles two accounting stories.** Gate state and Correction Budget are one slice because the correction loop only exists as gate-findings-to-correction-to-revalidation; splitting them would produce a gate slice that cannot demonstrate the transition that matters. It is the second-largest slice after 01. If it needs splitting, the clean cut is `correction.grantAttempts` and the `gates_failed` terminal path as a follow-on, since exhaustion behavior is independently demoable.

**Two slices depend on 06, making it a secondary bottleneck.** Both 07 and 08 need the operation reconciliation contract — the lease reclaim rule and the resume precondition both consult it. I considered pulling the operation state machine into slice 01 to remove the chain, but that would make the bootstrap slice unreviewable. The chain is two deep at worst and 07 and 08 run concurrently with each other.

**Infrastructure Retry landed with operations rather than with budgets.** It reads like a sibling of the Correction Budget and could have joined slice 05. I put it in 06 because the retry allowance is tracked per operation class and because the rule that matters most — an uncertain outcome must reach `reconciled_not_performed` before any retry — is meaningless without the operation state machine sitting next to it.
