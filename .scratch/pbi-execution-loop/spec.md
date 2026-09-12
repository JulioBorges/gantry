# PBI execution loop: worktrees, scheduling, and context handoff

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 11, wave 3)
Source: `PRD.md` §7.4, §4.1, §4.3, §6.2
Created: 2026-09-11

## Problem Statement

This is where the first bottleneck in `PRD.md` actually bites. An agent implementing a slice
accumulates conversation history, tool output, and build logs until its reasoning degrades — "attention
dilution and hallucinations well before the window limit" — and the answer is to hand off to a fresh
agent carrying compacted continuity rather than raw history. The default watermark is forty percent,
and the PRD is careful that it is "an operating policy, not a scientific threshold", enforceable only
where the integration supports it.

Several failures converge on this loop.

Parallel builders sharing a working directory corrupt each other, so each active PBI needs its own
worktree and branch — and ADR-0002 accepts worktree lifecycle management as the cost. But separate
worktrees do not isolate ports, databases, or temporary directories, so concurrency is bounded by more
than a capacity number.

A handoff has to stop one agent and start another without losing work or duplicating it, using whatever
the integration exposes. The PRD's handoff diagram says "reconcile and stop or hand off the current
agent through supported integration capabilities", and §5.4 adds that a takeover "must not assume that
superseding an assignment stopped the old agent". Two agents writing one worktree is the concrete
disaster.

A PBI waiting on human review should not hold a capacity slot, but releasing it must not cancel the PBI
or let it resume without revalidating. And an agent reporting `blocked` must stop the loop rather than
improvise.

The mechanisms are deferred throughout: "the precise capability contract and measurement rules remain to
be specified", "its persistent state representation remains to be specified" for dependency waiting,
"ownership arbitration, assignment schema, and prevention of concurrent worktree writes during takeover
remain to be specified", "detailed polling and slot accounting remain to be specified".

## Solution

A scheduler evaluates eligibility as a conjunction — dependency readiness, recorded planning approval,
available capacity at every applicable limit, no competing ownership, and available check resources —
and dispatches only when all hold. Each dispatched PBI gets a dedicated worktree and branch created from
the starting branch its Git workflow policy names, and a worktree lease that makes concurrent writes
detectable rather than merely discouraged.

The loop observes context at whatever granularity the integration proved in spec 10 and coordinates a
handoff at the watermark or on an agent's `needs_handoff`. A handoff commits a save point, compiles a
memo containing remaining criteria, completed criteria, modified file references, and the relevant
failure — discarding raw history — requests a stop through the available mechanism, reconciles to
establish whether the old agent actually stopped and whether the worktree is quiescent, and only then
dispatches a replacement. The replacement's package is budgeted exactly like any start.

`blocked` stops the loop and surfaces the agent's questions. Green verification produces a micro-commit.
Correction stays within the PBI's shared allowance. A PBI waiting for review releases its slot while
keeping its worktree and state, and reacquires capacity and revalidates before resuming.

## User Stories

1. As an operator, I want each active PBI in its own worktree and branch, so that parallel builders cannot corrupt each other.
2. As an operator, I want branches named and based according to my Git workflow policy, so that Gantry fits my conventions.
3. As an operator, I want worktree creation to happen only after my working tree treatment is recorded, so that the baseline is definite.
4. As an operator, I want a worktree lease that detects concurrent writes, so that two agents in one directory is caught rather than assumed impossible.
5. As an operator, I want worktrees preserved after a run, so that I can inspect the work and resume it.
6. As an operator, I want worktrees reused on resumption rather than recreated, so that progress survives.
7. As an operator, I want dispatch to require dependency readiness, recorded approval, capacity, ownership, and resources together, so that no single check can be bypassed.
8. As an operator, I want a rejected dispatch to name which condition failed, so that I can act on it.
9. As an operator, I want the global capacity limit respected regardless of repository or driver settings, so that one repository cannot consume my machine.
10. As an operator, I want per-repository and per-driver limits honored too, so that I can tune concurrency where it matters.
11. As an operator, I want actual parallelism to drop below the limit when dependencies or shared resources require it, so that a limit is a ceiling rather than a target.
12. As an operator, I want queued PBIs to wait for capacity rather than starting above the limit, so that the limit holds under load.
13. As an operator, I want checks needing the same shared resource serialized, so that two slices do not fight over a port or a database.
14. As an operator, I want context observed at whatever granularity my integration actually supports, so that monitoring is real rather than claimed.
15. As an operator, I want a handoff coordinated at the watermark, so that an agent is replaced before its reasoning degrades.
16. As an operator, I want an agent to be able to request a handoff itself, so that it can act on degradation I cannot observe.
17. As an operator, I want no strict ceiling claimed where my integration cannot enforce one, so that the projection matches reality.
18. As an operator, I want a save point committed before a handoff, so that partial work is never lost.
19. As an operator, I want the handoff memo to carry remaining criteria, completed criteria, changed files, and the relevant failure, so that the replacement resumes from evidence.
20. As an operator, I want raw conversation history, tool calls, and build logs discarded from the memo, so that compaction actually compacts.
21. As an operator, I want the replacement's package budgeted like any start, so that continuity work is bounded.
22. As an operator, I want a package that cannot fit without dropping required content to pause for review, so that nothing mandatory is silently omitted.
23. As an operator, I want the old agent asked to stop through whatever mechanism exists, so that the best available behavior is used.
24. As an operator, I want reconciliation to confirm the old agent's state before the replacement starts, so that two agents never share a worktree.
25. As an operator, I want a late result from a replaced agent retained but powerless, so that stale work cannot advance the PBI.
26. As an operator, I want handoffs numbered and their memos retained, so that I can see how a slice progressed.
27. As an operator, I want the correction count preserved across handoffs, so that replacement is not a budget reset.
28. As an operator, I want a `blocked` result to stop the loop and show me the agent's questions, so that it never improvises past something it cannot decide.
29. As an operator, I want the loop to resume after I answer, so that answering is enough to continue.
30. As an operator, I want a micro-commit on every green verification, so that progress is durable and reviewable.
31. As an operator, I want micro-commits made only on verification Gantry ran, so that a commit reflects an actual pass.
32. As an operator, I want micro-commits never pushed automatically, so that nothing leaves my machine without the integration step.
33. As an operator, I want correction attempts bounded by the PBI's shared allowance, so that a stubborn slice stops instead of looping.
34. As an operator, I want exhausted correction to stop automatic work rather than spawn more agents, so that the failure is visible.
35. As an operator, I want a PBI waiting for review to release its capacity slot, so that other work continues while I review.
36. As an operator, I want a released slot not to cancel the PBI or discard its history, so that waiting is not losing.
37. As an operator, I want a waiting PBI to reacquire capacity and revalidate before resuming, so that releasing a slot is not a way around the limit.
38. As an operator, I want dependents to stay ineligible while a prerequisite waits, so that order holds during review.
39. As an operator, I want waiting on a dependency represented as a scheduling state distinct from being blocked, so that I am not asked to answer a question nobody posed.
40. As an operator, I want concurrent start requests for one PBI to produce one owner, so that two harness sessions cannot both drive it.
41. As an operator, I want parallel work on distinct eligible PBIs to continue, so that ownership protection does not serialize everything.
42. As an operator, I want the loop to require my harness to stay active, so that expectations match ADR-0001 rather than promising a background service.
43. As an operator, I want progress persisted so I can resume explicitly after reopening my harness, so that closing it costs continuity rather than work.
44. As a host harness, I want to ask for the next eligible PBI and get either a dispatch or a typed reason, so that I can drive the loop without inferring state.
45. As a host harness, I want handoff to be an operation I invoke rather than logic I reimplement, so that compaction and reconciliation stay consistent.
46. As an auditor, I want every dispatch, handoff, micro-commit, and slot change recorded, so that the run is reconstructible.

## Implementation Decisions

### Worktree lifecycle and lease

A worktree and branch are created at dispatch from the starting branch the Git workflow policy names
(spec 14 resolves it; `pbi/{id}` is an example, not a rule). Creation happens only after the working tree
treatment from spec 06 is recorded, so the baseline is definite.

```ts
type WorktreeLease = {
  unit: RepositoryExecutionUnitId;
  pbi: PbiId;
  path: string;
  branch: string;
  holder: AssignmentId;
  heartbeat: string;
  expiresAt: string;
  activityMarker: {           // derived from observed Git state, not from file timestamps
    indexHash: string;        // hash of .git/index
    statusFingerprint: string; // hash of `git status --porcelain` output
    observedAt: string;
  };
  frozen: boolean;            // worktree made read-only during the handoff reconciliation window
};
```

The lease lives in the database. Concurrent write detection is the conjunction of lease ownership and the
activity marker: a worktree whose marker advanced under a non-holder is `active` with a conflict recorded.

The marker is derived from observed Git state rather than from file timestamps — the hash of `.git/index`
plus a fingerprint of `git status --porcelain`. Timestamps are a poor signal here: a tool that rewrites a
file with identical content changes mtime without changing anything, and an editor that preserves mtime
changes content without changing the signal. Git's own view of the working tree is the thing that actually
matters to a merge candidate, so it is what the marker observes.

**Freeze during the reconciliation window.** Detection alone cannot stop a write that is already
happening, so during steps 3 through 5 of the handoff sequence the worktree is made read-only. An agent
that ignored the stop request fails with a permission error instead of corrupting a branch mid-takeover.
The freeze is released when the replacement is dispatched or when the handoff is abandoned, and the lease
records it so a crash mid-handoff leaves a frozen worktree that reconciliation can recognize and thaw.

This closes the window where the damage would occur. It is not general isolation: outside a handoff, a
native agent can still write to a worktree Gantry believes is idle, and that remains detection rather than
prevention, consistent with ADR-0001. Read-only permissions are also advisory against a process running
with sufficient privilege — the freeze raises the cost of the failure, it does not make it impossible.

Worktrees are never deleted implicitly; removal requires cleanup authorization from spec 01.

Resumption reuses the existing worktree and branch and reacquires the lease. It does not recreate either.

### Eligibility and scheduling

Dispatch requires all of:

1. Dependency Readiness per spec 09, verified against Git.
2. A recorded planning approval for the current plan version.
3. Capacity available at every applicable limit — global, repository, driver — evaluated together.
4. No competing current ownership for the PBI.
5. Every declared check resource for this PBI's verification either isolatable or currently free.

A failed condition produces a typed rejection naming it. Condition 3 evaluates all limits jointly, and a
repository or driver setting never raises the global ceiling. Condition 5 is why observed parallelism can
be lower than the configured limit: separate worktrees do not isolate a port or a database, so two PBIs
whose checks need the same shared resource serialize regardless of capacity.

Waiting states are distinct and persistent: `awaiting_dependency` for condition 1, `queued` for
condition 3, and `awaiting_operator` reserved exclusively for an agent-reported `blocked` result.

Concurrent start requests for one PBI resolve to one owner through the ownership claim in spec 01;
distinct eligible PBIs proceed in parallel.

### Context observation and the watermark

Observation granularity comes from the integration's proven capability:

| Declared monitoring | Observation behavior |
|---|---|
| `per_tool_call` | Evaluated between tool calls; the watermark can be acted on within a turn |
| `between_turns` | Evaluated after each result; the watermark can be exceeded within a turn |
| `self_reported` | Evaluated only from what the agent reports; no independent observation |
| `none` | No observation; handoff occurs only on an agent's `needs_handoff` |

The projection states which of these applies and never renders a strict ceiling for the lower three.
The default watermark is forty percent of the configured nominal window, configurable per spec 02, and
it is described as a handoff trigger rather than a limit.

### Handoff

Ordered, with reconciliation before the replacement:

1. Commit a save point on the PBI branch — a marked work-in-progress commit rather than a stash, since a
   stash is easy to lose and invisible to the worktree's history.
2. Compile the memo deterministically.
3. Freeze the worktree read-only, then request a stop through the adapter's available mechanism.
4. Reconcile: establish liveness, whether a result appeared, and whether the worktree is quiescent.
5. Thaw the worktree and dispatch the replacement with a new assignment and an incremented ownership
   generation, carrying the task envelope, the memo, and the touched-file references.

```ts
type HandoffMemo = {
  pbi: PbiId;
  handoffIndex: number;
  trigger: "watermark" | "agent_requested";
  contextUsageAtHandoff: ContextUsage;      // may be unknown
  completedCriteria: string[];              // criterion identities
  pendingCriteria: string[];
  lastFailingError?: string;
  activeModifiedFiles: string[];            // references, not content
  savePointRevision: string;
};
```

What is discarded: raw conversation history, tool call transcripts, and build logs. What is kept is the
list above. Memos are retained under spec 04's rules and numbered, so the progression of a slice is
readable.

Step 4 gates step 5 absolutely. A reconciliation returning `active` or `unknown` worktree activity blocks
the replacement dispatch and requires operator resolution. A late result from the replaced assignment is
retained and rejected as `stale_generation` per spec 03.

The replacement's complete package is estimated against the same budget as any start, including the
memo, per spec 09. A package that cannot fit without dropping contracts, criteria, or governance pauses
for context or decomposition review.

The correction count, the plan version, and the rule snapshot all carry across unchanged.

### Result handling in the loop

| Result status | Loop action |
|---|---|
| `blocked` | Stop the loop, move to `awaiting_operator`, surface `questionsForOperator`, release the slot |
| `needs_handoff` | Run the handoff sequence above |
| `complete` | Evaluate Implementation Completion per spec 03; on success advance to gates, otherwise record and continue or correct |
| `failed` | Record evidence; schedule correction only within the remaining allowance |

Status precedence is spec 03's. The loop never improvises past a `blocked` result and never interprets an
exit code as a status.

### Micro-commits

A micro-commit is made when Gantry's own execution of the PBI's mandatory verification passes — not when
an agent reports a pass. The message is deterministic and identifies the PBI and the verification that
passed. Commits stay local; nothing is pushed by the loop, since integration is spec 14's and requires
its own authorization.

### Capacity release during review

A PBI entering `awaiting_review` or `awaiting_operator` with no active assignment and no in-flight
operation releases its slot. Its worktree, lease, evidence, and state persist. Dependents remain
ineligible, because the prerequisite is not integrated.

Resuming requires reacquiring a slot and revalidating dependency readiness, current target, approval
currency, and the worktree lease. Releasing a slot is therefore never a path around the capacity limit.

### AFK lifecycle

The loop requires the host harness to remain active. There is no background service. Progress is
persisted at every transition, and resumption is the explicit operation in spec 01, which reconciles
pending agents and operations before progression continues. Closing the harness is not assumed to have
stopped a detached process.

## Testing Decisions

**What makes a good test here.** Tests drive the loop through the core with a scripted adapter and a
scripted check adapter, and assert on state sequences, the recorded memo fields, which conditions
rejected a dispatch, slot accounting, lease state, and the commits present on the PBI branch. Git
assertions are on the real temporary repository: branch existence, commit count, and the save point's
presence.

**The seam.** Unchanged. The scheduler, the watermark observer, and the handoff sequence are never called
directly — a handoff compiled correctly but never triggered would pass a direct test and fail the
product.

**Modules under test.** Worktree creation and lease acquisition, concurrent write detection, eligibility
evaluation and its rejection reasons, joint capacity accounting, check resource serialization, watermark
observation per declared granularity, the handoff sequence and its ordering, memo compilation and
exclusions, replacement dispatch gating on reconciliation, result status handling, micro-commit
conditions, slot release and reacquisition, and resumption reuse of worktrees.

**Scenarios that must exist**, from PRD §14.3 items 6 and 7:

- Two parallel PBIs get distinct worktrees and branches, both created from the policy's starting branch.
- Worktree creation is refused before a working tree treatment is recorded.
- A non-holder mutating a worktree is detected as `active` with a conflict recorded.
- A file rewritten with identical content does not advance the marker; a content change with a preserved timestamp does.
- The worktree is read-only between the stop request and the replacement dispatch; a write attempt during that window fails.
- A crash mid-handoff leaves a frozen worktree that reconciliation recognizes and thaws.
- Outside a handoff, a non-holder write is detected but not prevented, and the projection says so.
- Dispatch is rejected with the specific unmet condition for each of: unready dependency, missing approval, exhausted capacity, competing ownership, and occupied check resource.
- A repository limit higher than the global limit does not raise effective capacity.
- Two PBIs whose checks need the same shared resource serialize even with capacity available.
- A third PBI stays `queued` under a limit of two and starts when a slot frees.
- With `per_tool_call` monitoring, a handoff is coordinated within a turn; with `between_turns`, only after a result; with `none`, only on `needs_handoff`.
- No projection renders a strict ceiling for `between_turns`, `self_reported`, or `none`.
- A handoff commits a save point before requesting a stop, and the commit is present on the branch.
- The memo contains completed and pending criteria, changed file references, the relevant failure, and the save point revision, and contains no conversation history, tool transcript, or build log.
- A reconciliation returning `active` or `unknown` worktree activity blocks the replacement dispatch.
- A replacement dispatch carries a new assignment with an incremented ownership generation.
- A late result from the replaced assignment is retained and rejected `stale_generation`.
- The correction count, plan version, and rule snapshot are unchanged across a handoff.
- A replacement package exceeding the budget pauses for review rather than dropping required content.
- A `blocked` result stops the loop, surfaces the questions, releases the slot, and moves to `awaiting_operator`; answering resumes it.
- A `needs_handoff` result runs the handoff sequence even when criteria are reported complete.
- An exit code of zero with no result does not produce a micro-commit or any advancement.
- A micro-commit is made on Gantry's own passing verification and not on an agent's reported pass.
- No push occurs during the loop.
- Exhausted correction stops automatic work without spawning another agent.
- A PBI entering `awaiting_review` releases its slot, keeps its worktree and lease, and lets another PBI start; its dependents remain ineligible.
- Resuming a waiting PBI reacquires a slot and revalidates dependency readiness, target, approval, and lease.
- Resumption after simulated harness closure reuses the existing worktree and branch, reconciles first, and issues no duplicate dispatch.

## Out of Scope

- **Operations, state machine, ownership arbitration, budgets, cancellation, resumption, cleanup** (spec 01).
- **Limits, watermark values, snapshot** (spec 02).
- **Envelope contracts, status semantics, completion rules, Protocol Failure classes** (spec 03).
- **Memo retention and redaction** (spec 04): this spec decides the memo's fields; spec 04 decides what persists.
- **Working tree treatment and approved commands** (spec 06).
- **Dependency readiness definition, planning approval, context estimation** (spec 09): this spec evaluates readiness and consumes approval and estimates.
- **Adapter primitives: dispatch, observe, stop, reconcile, capabilities** (spec 10): this spec orchestrates them.
- **Check execution, resource declaration semantics, stability** (spec 12): this spec serializes on declared resources; spec 12 runs the checks and owns the locks.
- **Gate evaluation and correction content** (spec 13): this spec dispatches correction within the allowance; what to correct is spec 13's.
- **Branch naming policy, starting branch resolution, integration, push** (spec 14).

Out of scope by product decision:

- A background service continuing after the harness closes. §6.1 and ADR-0001 require an active harness and explicit resumption.
- Shared working directories for parallel builders. ADR-0002 requires dedicated worktrees.
- A stash-based save point. A commit on the PBI branch is visible and recoverable; a stash is neither.
- Automatic pushing of micro-commits. Integration is separately authorized.
- Container orchestration for check isolation. §7.5 states it is not required for v4; serialization covers shared resources.
- A separate handoff count limit or elapsed-time limit. §6.2 establishes neither.

## Further Notes

**Binding decisions.** ADR-0001 shapes the watermark table: monitoring granularity is a property of the
integration, and the loop's behavior differs accordingly rather than pretending uniformity. ADR-0002
shapes the worktree lease: isolation is accepted as a cost, and the lease is what makes it real.

**Glossary alignment.** PBI Worktree, Context Watermark, Correction Budget, Dependency Readiness, AFK
Execution, and Execution Resumption follow `CONTEXT.md`, including the terms it marks to avoid: a
worktree is not a shared builder checkout; AFK execution is not an unattended background service;
resumption is not a new pipeline or a budget reset.

**Glossary gap for `/domain-modeling`.** Worktree lease, activity marker, save point, and micro-commit
are introduced here without entries and should get them.

**Where the risk actually sits.** The freeze closes the handoff window, which was the dangerous one, and
moves the residual risk to two narrower places. Outside a handoff, a native agent writing to a worktree
Gantry believes is idle is still detected after the fact rather than prevented — the honest position given
ADR-0001, since Gantry guarantees its accepted transitions and not isolation of arbitrary harness actions.
And the freeze itself is advisory against a process running with sufficient privilege, so it raises the
cost of the failure without making it impossible.

The freeze also introduces a failure mode the previous design did not have: an agent that ignores the stop
request now receives a permission error, and how a given harness surfaces that is unpredictable. It may
report a confusing failure, retry in a loop, or write a result claiming an unrelated problem. That is
still better than a corrupted branch, but the conformance suite in spec 10 should record how each
integration behaves against a frozen worktree, because the answer shapes what the operator sees when a
handoff goes wrong.

The second risk is the save point. Committing work-in-progress onto the PBI branch means the branch
history contains commits that never passed verification, which matters when the branch becomes a merge
candidate. The mitigation belongs to spec 14: candidate preparation decides whether to preserve or
consolidate that history under the repository's policy. Raising it here because the decision to commit
rather than stash is what creates the obligation.

**Sequencing note.** This spec depends on specs 09, 10, and 06, and it is the last piece before the
pipeline can run end to end against a real harness. The handoff sequence's ordering — save point,
compile, stop, reconcile, dispatch — is the piece to settle first, because every later change to it
invalidates the scenarios that prove work is never lost or duplicated.
