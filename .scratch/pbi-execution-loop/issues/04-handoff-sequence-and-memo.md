# The handoff sequence and the State Compaction memo

Type: issue
Status: ready-for-agent
Slice: pbi-execution-loop#04
Spec: [`../spec.md`](../spec.md) (spec 11, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/pbi-execution-loop/spec.md`](../spec.md)

## What to build

Handoff is an operation the host harness invokes, not logic it reimplements. It executes in a fixed order, and this ordering is the contract other specs are written against:

1. **Save point** — commit the work in progress on the PBI branch as a marked work-in-progress commit. Not a stash: a stash is easy to lose and invisible to the branch's history.
2. **Compile memo** — build the State Compaction memo deterministically.
3. **Freeze and request stop** — freeze the worktree read-only, then request a stop through whatever mechanism the adapter exposes.
4. **Reconcile** — establish liveness, whether a result appeared, and whether the worktree is quiescent.
5. **Thaw and dispatch replacement** — thaw the worktree and dispatch the replacement with a new assignment and an incremented ownership generation, carrying the task envelope, the memo, and the touched-file references.

Step 4 gates step 5 absolutely: an `active` or `unknown` worktree activity result blocks the replacement and requires operator resolution, and a `StopOutcome` of `unsupported` or `requested_cooperatively` is never treated as proof that the old agent stopped. Because `requestStop` may declare `agentInterruption: "none"`, there must be a path where step 3's stop request is a no-op and reconciliation carries the whole weight of establishing quiescence — do not assume a cooperative stop mechanism exists. The read-only freeze is implemented through file permissions and therefore behaves differently on Windows; the per-platform status of these rows belongs to `release-engineering#05`, not to this slice.

The memo carries the handoff index, the trigger, the context usage at handoff, completed and pending criterion identities, the relevant failing error, modified file references, and the save point revision. It carries no conversation history, no tool call transcript, and no build log — compaction that keeps raw history is not compaction. Memos are numbered and all prior memos remain retrievable. The correction count, the plan version, and the Execution Rule Snapshot carry across the handoff unchanged, so replacing an agent is never a budget reset. The replacement's complete package is estimated against the same Initial Context Budget as any start, memo included, and a package that cannot fit without dropping contracts, criteria, or governance pauses for review instead of silently truncating.

## Acceptance criteria

- [ ] The save point commit is present on the PBI branch before any stop request is issued, verified by commit order in the real temporary repository; no stash is used.
- [ ] A write to the worktree between the stop request and the replacement dispatch fails; the freeze is released exactly once, on replacement dispatch or on abandonment.
- [ ] The compiled memo contains completed criteria, pending criteria, changed file references, the relevant failure, and the save point revision, and contains none of: conversation history, tool call transcripts, build logs.
- [ ] A reconciliation returning `active` or `unknown` worktree activity blocks the replacement dispatch and leaves the PBI awaiting operator resolution; a `StopOutcome` of `unsupported` or `requested_cooperatively` still requires reconciliation to clear before dispatch.
- [ ] The replacement assignment carries an incremented ownership generation, and a late result from the replaced assignment is retained and rejected `stale_generation` with state unchanged.
- [ ] Correction count, plan version, and Execution Rule Snapshot are byte-identical across the handoff; memos are numbered and all prior memos remain retrievable.
- [ ] A replacement package whose estimated upper bound exceeds the budget pauses for review and dispatches nothing.

## Blocked by

- `pbi-execution-loop#01` — the worktree lease and the freeze/thaw primitives with the crash-recoverable `frozen` field, designed to this five-step sequence.
- `pbi-execution-loop#03` — the watermark and `needs_handoff` trigger that enters this sequence.
- `harness-adapters#01` — the `HarnessAdapter` surface with `requestStop` and `reconcile`, the `StopOutcome` variants including `unsupported` and `requested_cooperatively`, the `ReconciliationResult` variants, and `DispatchHandle`.
- `gtp-protocol#04` — the `needs_handoff` continuity fields the memo must satisfy, and the `ContextUsage` recorded at handoff.
- `gtp-protocol#05` — criterion identities for the completed and pending criterion lists.
- `gtp-protocol#01` — the `stale_generation` Protocol Failure class applied to a late result from a replaced assignment.
- `execution-core#03` — the new assignment with an incremented ownership generation issued at step 5.
- `execution-core#04` — retention of a late result submission against a superseded assignment.
- `slicing-and-approval#03` — the Initial Context Budget estimator and its upper-bound comparison.
- `config-and-snapshot#04` — the Execution Rule Snapshot identity that must be byte-identical across the handoff.
- `data-handling#01` — the redaction sink the memo is written through.
- `data-handling#04` — reference-first retention rules for the numbered memos and their file references.
