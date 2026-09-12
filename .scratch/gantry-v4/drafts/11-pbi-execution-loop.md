## Spec 11 — pbi-execution-loop

This spec owns everything between "an approved PBI exists" and "a candidate is ready for gates": the PBI Worktree and its lease, the eligibility conjunction and capacity accounting that decide when a PBI may be dispatched, Context Watermark observation at whatever granularity the integration proved, the handoff sequence that replaces an agent without losing or duplicating work, result handling for `blocked` / `needs_handoff` / `complete` / `failed`, micro-commits on Gantry-run verification, and slot release while a PBI waits for review. The risk concentrates in two places. First, the handoff sequence ordering — save point → compile → stop → reconcile → dispatch — is the only thing standing between a replacement agent and a corrupted branch, and the read-only freeze during steps 3–5 introduces a new failure mode (an agent that ignores the stop request gets a permission error whose surfacing is harness-dependent). Second, the eligibility conjunction is the single point where five independent conditions must hold jointly; any slice that lets one condition be evaluated in isolation reintroduces the bypass the spec exists to prevent. Everything else in this spec is bookkeeping that must be exactly right but is not conceptually hard.

### Slices

---

**01 — PBI Worktree lifecycle and worktree lease**

- **What to build**: Dispatching a PBI creates a dedicated worktree and branch from the starting branch the repository's Git Workflow Policy names, and records a worktree lease in SQLite holding the unit, PBI, path, branch, holder assignment, heartbeat, expiry, an activity marker, and a freeze flag. The activity marker is derived from observed Git state — a hash of `.git/index` plus a fingerprint of `git status --porcelain` — never from file timestamps. Concurrent write detection is the conjunction of lease ownership and marker advancement: a marker that moved under a non-holder records a conflict and reports the worktree as `active`. Freeze and thaw are exposed as lease-level primitives (worktree made read-only, freeze recorded on the lease) so a crash mid-freeze leaves a state reconciliation can recognize; the handoff sequence that calls them is slice 04. Worktree creation is refused until a working tree treatment is recorded, worktrees are never removed implicitly, and resumption reacquires the lease on the existing worktree and branch rather than recreating either.

- **Acceptance criteria**:
  - Two PBIs dispatched in the same Repository Execution Unit get distinct worktree paths and distinct branches, both created from the policy's starting branch, verified against the real temporary Git repository.
  - Dispatch is rejected and no worktree is created when no working tree treatment is recorded for the unit.
  - A non-holder mutating the worktree is reported as `active` with a conflict recorded on the lease.
  - Rewriting a file with identical content does not advance the activity marker; changing content while preserving mtime does advance it.
  - A frozen worktree rejects writes, and a lease left `frozen: true` by a simulated crash is recognized and thawed by reconciliation rather than being treated as normal.
  - Re-running dispatch after a simulated harness restart reuses the existing worktree and branch and reacquires the lease; no second worktree is created and no branch is reset.
  - Removing a worktree without a cleanup authorization is refused.

- **Blocked by**: needs `WorkingTreeTreatment` (recorded treatment, and the rule that no worktree exists before it) from `repository-readiness`; needs the starting-branch resolution and branch-naming rule of the Git Workflow Policy from `git-integration`; needs `pbi.dispatch`, the assignment/ownership-generation record, and the `Rejection` code set from `execution-core`.
- **Parallelizable with**: none at the start (this is the bootstrap); 02, 03, 05 open once it lands.

---

**02 — Eligibility conjunction, joint capacity accounting, and typed dispatch rejections**

- **What to build**: `pbi.schedule` answers the host harness with either a dispatch or a typed reason, and `pbi.dispatch` evaluates eligibility as a conjunction of five conditions — Dependency Readiness verified against Git, a recorded planning approval for the current plan version, capacity available at every applicable limit evaluated jointly, no competing current ownership, and check resources available. A failed condition produces a rejection naming that specific condition. Capacity is evaluated across global, repository, and driver limits together, and a repository or driver setting can never raise the global ceiling. Waiting states are persistent and distinct: `awaiting_dependency` for the dependency condition and `queued` for the capacity condition, with `awaiting_operator` reserved exclusively for an agent-reported `blocked` result. Condition five is consulted through an injected resource-availability port whose real implementation lands in slice 07. The scheduling operation gets one CLI and one MCP parity test.

- **Acceptance criteria**:
  - Dispatch is rejected with the specific unmet condition named, separately, for each of: unready dependency, missing or stale planning approval, exhausted capacity, competing ownership, occupied check resource.
  - A repository capacity limit configured above the global limit yields effective capacity equal to the global limit.
  - Under a global limit of two, a third eligible PBI stays `queued` and is dispatched when a slot frees, with no dispatch above the limit at any point.
  - `awaiting_dependency`, `queued`, and `awaiting_operator` are distinguishable in the projection, and a PBI waiting on a prerequisite is never presented as needing an operator answer.
  - Two concurrent start requests for one PBI resolve to exactly one owner; two concurrent start requests for distinct eligible PBIs both proceed.
  - The CLI and MCP surfaces for scheduling delegate to `invoke` and return the same outcome as the in-process call.

- **Blocked by**: 01 (the dispatch success path needs a worktree and lease). Needs Dependency Readiness evaluation, plan version identity, and the approval-binding rule from `slicing-and-approval`; needs capacity limit values (global / repository / driver) from `config-and-snapshot`; needs `pbi.schedule`, `pbi.claimOwnership`, ownership arbitration, and the `capacity_unavailable` / `dependency_not_ready` / `approval_required` rejection codes from `execution-core`.
- **Parallelizable with**: 03, 05.

---

**03 — Context Watermark observation per declared granularity**

- **What to build**: The loop observes context usage through the adapter at the granularity the integration's conformance probe declared, and decides when a handoff is required. `per_tool_call` is evaluated between tool calls so the watermark can be acted on within a turn; `between_turns` is evaluated after each result, so the watermark can be exceeded within a turn; `self_reported` uses only what the agent reports; `none` performs no observation and triggers only on an agent's `needs_handoff`. Crossing the watermark, or receiving `needs_handoff`, moves the PBI to `handoff_pending` and reports that a handoff is required; performing it is slice 04. The state projection states which granularity applies and renders no strict ceiling for any of the lower three, and never renders a numeric usage value when `ContextUsage` is `unknown`. The watermark default is forty percent of the configured nominal window and is described as a trigger, not a limit.

- **Acceptance criteria**:
  - With `per_tool_call`, a scripted adapter crossing the watermark mid-turn produces `handoff_pending` before the turn's result arrives; with `between_turns`, only after the result; with `self_reported`, only from the agent's own reported value; with `none`, never from observation.
  - With `none`, an agent result of `needs_handoff` still produces `handoff_pending`.
  - No projection renders a strict ceiling for `between_turns`, `self_reported`, or `none`, and the declared granularity is present in the projection.
  - A `ContextUsage` of `unknown` produces no numeric context value anywhere in the projection.
  - The watermark value is read from the Execution Rule Snapshot, and changing live configuration mid-execution does not change the trigger point for a running PBI.
  - The dashboard projection gets one parity test proving it renders the core's projection without recomputing it.

- **Blocked by**: 01. Needs `HarnessAdapter.observe`, `AgentObservation`, the `ContextUsage` union including `unknown`, and `IntegrationCapabilities` context-monitoring granularity from `harness-adapters`; needs the watermark value and nominal window from `config-and-snapshot`; needs the `needs_handoff` status and its required continuity content from `gtp-protocol`.
- **Parallelizable with**: 02, 05.

---

**04 — The handoff sequence and the State Compaction memo**

- **What to build**: Handoff is an operation the host harness invokes, not logic it reimplements, and it executes in a fixed order: commit a save point on the PBI branch as a marked work-in-progress commit; compile the memo deterministically; freeze the worktree read-only and request a stop through whatever mechanism the adapter exposes; reconcile to establish liveness, whether a result appeared, and whether the worktree is quiescent; then thaw and dispatch the replacement with a new assignment and an incremented ownership generation. Step four gates step five absolutely — an `active` or `unknown` worktree activity result blocks the replacement and requires operator resolution. The memo carries the handoff index, trigger, context usage at handoff, completed and pending criterion identities, the relevant failing error, modified file references, and the save point revision, and carries no conversation history, tool transcript, or build log. The replacement's complete package is estimated against the same Initial Context Budget as any start, memo included, and a package that cannot fit without dropping contracts, criteria, or governance pauses for review instead of silently truncating.

```text
1 save point → 2 compile memo → 3 freeze + requestStop → 4 reconcile → 5 thaw + dispatch replacement
```

- **Acceptance criteria**:
  - The save point commit is present on the PBI branch before any stop request is issued, verified by commit order in the real temporary repository; no stash is used.
  - A write to the worktree between the stop request and the replacement dispatch fails; the freeze is released exactly once, on replacement dispatch or on abandonment.
  - The compiled memo contains completed criteria, pending criteria, changed file references, the relevant failure, and the save point revision, and contains none of: conversation history, tool call transcripts, build logs.
  - A reconciliation returning `active` or `unknown` worktree activity blocks the replacement dispatch and leaves the PBI awaiting operator resolution; a `StopOutcome` of `unsupported` or `requested_cooperatively` still requires reconciliation to clear before dispatch.
  - The replacement assignment carries an incremented ownership generation, and a late result from the replaced assignment is retained and rejected `stale_generation` with state unchanged.
  - Correction count, plan version, and Execution Rule Snapshot are byte-identical across the handoff; memos are numbered and all prior memos remain retrievable.
  - A replacement package whose estimated upper bound exceeds the budget pauses for review and dispatches nothing.

- **Blocked by**: 01 (lease, freeze/thaw), 03 (the trigger). Needs `StopOutcome` and `ReconciliationResult` variants and `DispatchHandle` from `harness-adapters`; needs the `needs_handoff` continuity fields, criterion identities, and the `stale_generation` Protocol Failure class from `gtp-protocol`; needs the Initial Context Budget estimator and its upper-bound comparison from `slicing-and-approval`; needs the redaction sink and memo retention rules from `data-handling`.
- **Parallelizable with**: 05 (both touch result handling only at the boundary — 04 owns the `needs_handoff` path, 05 owns the rest).

---

**05 — Result handling, micro-commits, and correction dispatch**

- **What to build**: A submitted result drives the loop according to spec 03's fixed status precedence. `blocked` stops the loop, moves the PBI to `awaiting_operator`, surfaces `questionsForOperator`, and releases the slot; the operator's answer is recorded and carried into the redispatch as continuity input so answering is sufficient to continue. `complete` triggers Implementation Completion evaluation and, on success, advances toward gates. `failed` records evidence and schedules a correction attempt only within the PBI's remaining allowance, with exhaustion stopping automatic work rather than spawning another agent. A micro-commit is made only when Gantry's own execution of the PBI's mandatory verification passes — never on an agent's reported pass — with a deterministic message identifying the PBI and the verification, and nothing is ever pushed by the loop. An exit code with no result advances nothing and produces no commit.

- **Acceptance criteria**:
  - A `blocked` result moves the PBI to `awaiting_operator`, surfaces the questions, releases the slot, and lets another queued PBI start; recording an answer resumes the loop for that PBI.
  - A result carrying both `blocked` and completed criteria resolves as `blocked`; one carrying `needs_handoff` and completed criteria resolves as `needs_handoff` and enters the handoff sequence.
  - A micro-commit appears on the PBI branch after Gantry runs the mandatory verification and it passes, and no commit appears when the agent reports a pass that Gantry's run contradicts.
  - No push occurs at any point in the loop, asserted against the real temporary repository's remote refs.
  - Correction attempts are consumed at correction dispatch; exhausting the allowance leaves the gate failed, dispatches no further agent, and produces `correction_budget_exhausted`.
  - A process exit with status zero and no submitted result produces no micro-commit and no state advancement.
  - The MCP result-submission surface gets one parity test proving delegation to `invoke`.

- **Blocked by**: 01. Needs `GtpStatus` precedence, the `questionsForOperator` requirement, Implementation Completion rules, and Result Submission identity from `gtp-protocol`; needs the correction-budget value and the dispatch-time consumption rule from `config-and-snapshot` and `execution-core`; needs the check execution interface (run a declared mandatory check, get a pass/fail with evidence) from `verification-adapters`; needs the correction-dispatch entry point from `entropy-gate` (this slice dispatches within the allowance; what to correct is not its decision).
- **Parallelizable with**: 02, 03, 04.

---

**06 — Slot release during review, reacquisition, and resumption**

- **What to build**: A PBI entering `awaiting_review` or `awaiting_operator` with no active assignment and no in-flight operation releases its capacity slot while keeping its worktree, lease, evidence, and state; its dependents stay ineligible because the prerequisite is not integrated. Resuming requires reacquiring a slot and revalidating dependency readiness, current target, approval currency, and the worktree lease, so releasing a slot is never a path around the capacity limit. Execution resumption after a simulated harness closure reconciles pending assignments and operations first, reuses the existing worktree and branch, and issues no duplicate dispatch. The loop requires the host harness to remain active — there is no background service, progress is persisted at every transition, and closing the harness costs continuity rather than work.

- **Acceptance criteria**:
  - A PBI entering `awaiting_review` releases its slot, another PBI starts in that slot, and the waiting PBI's worktree, lease, and evidence are intact afterward.
  - Dependents of a waiting PBI remain `awaiting_dependency` for as long as the prerequisite is not integrated.
  - Resuming a waiting PBI fails when no slot is available, and on success revalidates all four of dependency readiness, current target, approval currency, and lease ownership — each independently provable by making exactly one of them stale.
  - Resumption after a simulated harness closure reconciles before progressing, reuses the existing worktree and branch, and issues no duplicate dispatch for an assignment that was already in flight.
  - A PBI with an in-flight operation does not release its slot even while nominally waiting.
  - The CLI surface for slot release and reacquisition gets one parity test proving delegation.

- **Blocked by**: 02 (capacity accounting), 01 (lease). Needs `pbi.releaseSlot`, `pbi.claimOwnership`, `execution.resume`, the slot-occupancy rule, and the reconciliation-before-progression requirement from `execution-core`.
- **Parallelizable with**: 03, 04, 05, 07.

---

**07 — Check Resource serialization in scheduling**

- **What to build**: Replace slice 02's injected resource-availability port with a real consultation of the declared Check Resources for a PBI's verification. A resource declared `isolatable` is provisioned per execution and imposes no constraint; a resource shared at unit or machine scope makes a PBI ineligible while another PBI holds it, keeping it `queued` with a rejection naming the resource. This is why observed parallelism can be lower than the configured capacity limit — separate worktrees do not isolate a port or a database, so two PBIs whose checks need the same shared resource serialize regardless of available capacity. Spec 12 owns the declarations and the locks; this slice consults them for eligibility and never takes a lock of its own.

- **Acceptance criteria**:
  - Two PBIs whose verification declares the same machine-scoped resource never run concurrently, even with two capacity slots free, and the second's rejection names the resource.
  - Two PBIs whose verification declares only `isolatable` resources run concurrently under sufficient capacity.
  - Machine-scoped serialization holds across two Repository Execution Units in the same test, proving the scope is not unit-local.
  - Releasing the resource makes the waiting PBI eligible without operator intervention.
  - The scheduler consults declarations and does not acquire or release a resource lock itself; the lock lifecycle remains with the check runner.
  - Effective parallelism reported in the projection reflects resource-bound serialization rather than the configured limit.

- **Blocked by**: 02. Needs `CheckResourceDeclaration` with its sharing scope (`machine` / `unit` / `isolatable`) and the resource lease/lock lifecycle from `verification-adapters`.
- **Parallelizable with**: 03, 04, 05, 06.

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| `invoke` seam, `OperationRequest` / `OperationOutcome` / `Rejection` code set | `execution-core` | all |
| PBI state machine states and legal transitions (`queued`, `implementing`, `handoff_pending`, `awaiting_operator`, `awaiting_review`) | `execution-core` | 01, 02, 04, 05, 06 |
| `pbi.dispatch`, `pbi.schedule`, `pbi.submitResult`, `pbi.claimOwnership`, `pbi.releaseSlot` | `execution-core` | 01, 02, 05, 06 |
| Assignment record and ownership generation / arbitration | `execution-core` | 01, 02, 04 |
| Slot occupancy rule and `execution.resume` reconciliation requirement | `execution-core` | 06 |
| Cleanup authorization manifest (no implicit worktree removal) | `execution-core` | 01 |
| `WorkingTreeTreatment` and the "no worktree before treatment" rule | `repository-readiness` | 01 |
| Git Workflow Policy starting-branch resolution and branch naming | `git-integration` | 01 |
| `HarnessAdapter` surface: `dispatch`, `observe`, `requestStop`, `reconcile`, `capabilities`, `DispatchHandle` | `harness-adapters` | 03, 04, 05 |
| `StopOutcome` variants (incl. `unsupported`, `requested_cooperatively`) and `ReconciliationResult` variants | `harness-adapters` | 04 |
| `ContextUsage` union incl. `unknown`; `IntegrationCapabilities` context-monitoring granularity | `harness-adapters` | 03 |
| Dependency Readiness evaluation rule | `slicing-and-approval` | 02 |
| Plan version identity and planning-approval version binding | `slicing-and-approval` | 02, 04 |
| Initial Context Budget estimator and upper-bound comparison | `slicing-and-approval` | 04 |
| `GtpStatus` precedence, `questionsForOperator` requirement, `needs_handoff` continuity fields | `gtp-protocol` | 03, 04, 05 |
| Implementation Completion rule; criterion identity | `gtp-protocol` | 04, 05 |
| `stale_generation` Protocol Failure class; Result Submission identity | `gtp-protocol` | 04, 05 |
| Capacity limit values (global / repository / driver) and the no-raise rule | `config-and-snapshot` | 02 |
| Context watermark value and assumed nominal window; Execution Rule Snapshot | `config-and-snapshot` | 03, 04 |
| Correction budget value | `config-and-snapshot` | 05 |
| Redaction sink interface and memo retention rules | `data-handling` | 04 |
| `CheckResourceDeclaration` with sharing scope; resource lease lifecycle | `verification-adapters` | 07 |
| Check execution interface (run a declared mandatory check, get pass/fail with evidence) | `verification-adapters` | 05 |
| Correction dispatch entry point (what to correct) | `entropy-gate` | 05 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| **Handoff sequence ordering** — save point → compile → stop → reconcile → dispatch, with step 4 gating step 5 absolutely | 04 | `harness-adapters` (conformance suite must record per-integration behavior against a frozen worktree), `git-integration`, `execution-core`, `entropy-gate` |
| `WorktreeLease` shape: holder, heartbeat, expiry, Git-derived activity marker, freeze flag | 01 | `git-integration` (candidate preparation, worktree removal), `execution-core` (cleanup manifest contents), `dashboard` (projection) |
| Worktree freeze/thaw semantics and the "advisory, not isolation" boundary | 01 | `harness-adapters`, `dashboard` (must not describe it as prevention) |
| `HandoffMemo` field set and its exclusion list (no history, no transcripts, no build logs) | 04 | `data-handling` (retention and redaction), `gtp-protocol` (continuity content), `dashboard`, `compound-learning` |
| Eligibility conjunction and the typed dispatch rejection vocabulary | 02 | `dashboard`, `mcp-server`, `slicing-and-approval` |
| Waiting-state vocabulary: `awaiting_dependency` vs `queued` vs `awaiting_operator` | 02 | `dashboard`, `execution-core` |
| Context observation behavior per declared granularity, and the "no strict ceiling below `per_tool_call`" projection rule | 03 | `dashboard`, `harness-adapters`, `machine-setup` (compatibility matrix rows) |
| Micro-commit rule: only on Gantry-run verification, deterministic message, never pushed | 05 | `git-integration` (candidate preparation must decide whether to preserve or consolidate save-point and micro-commit history), `compound-learning` |
| Slot release / reacquisition semantics for review waiting | 06 | `dashboard`, `execution-core` |
| Resource-availability port consulted by the scheduler (consults, never locks) | 07 | `verification-adapters` |

### Risks / judgement calls

**Splitting 02 from 07.** I put check-resource serialization in its own slice behind an injected availability port so that slice 02 does not block on `verification-adapters` landing its `CheckResourceDeclaration`. The cost is that for the duration of 02, condition five of the conjunction is satisfied by a fake. I think that is acceptable — the conjunction's shape is what matters, and 02's acceptance criteria still require a rejection naming the occupied resource — but an operator who wants the five conditions to be real from day one should merge 02 and 07 and accept the cross-spec block.

**Slice 03 is the thinnest.** Observation plus projection honesty is a small amount of code, and I was tempted to fold it into 04. I kept it separate because the four granularity behaviors are independently testable and because folding them in would make 04 — already the largest slice — carry both the trigger and the sequence. If the operator prefers fewer, meatier slices, merging 03 into 04 is the merge I would make.

**Ordering versus the spec's sequencing note.** The spec says the handoff ordering is the thing to settle first, but the ordering cannot be *built* first because it depends on the lease and the freeze. I resolved this by requiring slice 01 to land the freeze/thaw primitives and the lease's `frozen` field in a shape that matches the five-step sequence, and by stating the ordering explicitly in slice 04. Slice 01's author must not design the freeze around a different sequence.

**Replacement package budgeting folded into 04.** It is arguably its own behavior (estimate, compare against upper bound, pause for review), but it is one acceptance criterion and it has no meaning outside the handoff, so a separate slice would not be independently demoable.

**`awaiting_review` is not in the PBI state graph as drafted in spec 01**, though spec 01's capacity section names it. Slice 06 needs it; whoever writes 06 should confirm with `execution-core` rather than adding a state unilaterally.

**Resuming after `blocked` needs an operation that does not exist in spec 01's v1 catalog.** User story 29 requires that answering is sufficient to continue, but there is no `pbi.answer`. Slice 05 assumes the answer is recorded and carried as continuity input into a redispatch driven by `pbi.claimOwnership`. Following the handoff's guidance that specs propose small additions to spec 01's catalog rather than a parallel one, this may warrant one added operation — flagging it rather than deciding it.

**Concurrent-write detection is specified in process.** Spec 12 tests its resource lock across two OS processes; I did not require that here, because the activity marker is derived from Git state and a direct mutation of the real temporary repository from the test is indistinguishable from a mutation by another process. If the operator wants the freeze itself proven against a separate process, that is a two-process test and should be called out explicitly in slice 01.

**Windows.** Two divergences land in this spec's slices: `requestStop` may declare `agentInterruption: "none"`, so slice 04 must have a path where step 3 is a no-op and reconciliation carries the whole weight; and the read-only freeze is implemented by permissions, which behave differently on Windows. Neither is a reason to change the slicing, but slice 04's author should not assume a cooperative stop exists.
