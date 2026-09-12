# PBI Worktree lifecycle and worktree lease

Type: issue
Status: ready-for-agent
Slice: pbi-execution-loop#01
Spec: [`../spec.md`](../spec.md) (spec 11, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/pbi-execution-loop/spec.md`](../spec.md)

## What to build

Dispatching a PBI creates a dedicated worktree and branch from the starting branch the repository's Git Workflow Policy names, and records a worktree lease in SQLite holding the unit, the PBI, the path, the branch, the holder assignment, a heartbeat, an expiry, an activity marker, and a freeze flag. The activity marker is derived from observed Git state — a hash of the Git index plus a fingerprint of `git status --porcelain` output — never from file timestamps, because a tool that rewrites a file with identical content changes the timestamp without changing anything and an editor that preserves the timestamp changes content without changing the signal. Concurrent write detection is the conjunction of lease ownership and marker advancement: a marker that moved under a non-holder records a conflict and reports the worktree as `active`. Worktree creation is refused until a working tree treatment is recorded, worktrees are never removed implicitly, and resumption reacquires the lease on the existing worktree and branch rather than recreating either.

Freeze and thaw are exposed as lease-level primitives — the worktree is made read-only and the freeze is recorded on the lease — so a crash mid-freeze leaves a state that reconciliation can recognize and thaw. **These primitives must be designed to fit the five-step handoff sequence that `pbi-execution-loop#04` implements: save point → compile memo → freeze and request stop → reconcile → thaw and dispatch replacement.** The freeze is acquired at step 3 and released exactly once, at step 5 or on abandonment, and the `frozen` field on the lease is the crash-recoverable record of that window. Do not design the freeze around a different sequence or a different release point; every later change to the ordering invalidates the scenarios that prove work is never lost or duplicated.

Two boundaries are load-bearing. First, `harness-adapters#01` ships an adapter-independent Git-state observer behind an injectable port and owns the `ReconciliationResult.worktreeActivity` variant set; this slice supersedes that observer with the lease-aware marker by injecting its own implementation, and must not reopen or widen the adapter interface. Second, the freeze is **advisory, not isolation**: it does not stop a process running with sufficient privilege, and outside a handoff a native agent can still write to a worktree Gantry believes is idle, which remains detection after the fact rather than prevention. No surface, projection, or documentation this slice produces may describe the freeze as preventing concurrent writes. Concurrent-write detection is proven in-process here, because the marker derives from Git state and a direct mutation of the real temporary repository from the test is indistinguishable from a mutation by another OS process; if the freeze itself is to be proven against a separate process, that is a two-process test and is a deliberate addition to this slice rather than an assumed part of it.

## Acceptance criteria

- [ ] Two PBIs dispatched in the same Repository Execution Unit get distinct worktree paths and distinct branches, both created from the policy's starting branch, verified against the real temporary Git repository.
- [ ] Dispatch is rejected and no worktree is created when no working tree treatment is recorded for the unit.
- [ ] A non-holder mutating the worktree is reported as `active` with a conflict recorded on the lease.
- [ ] Rewriting a file with identical content does not advance the activity marker; changing content while preserving the modification time does advance it.
- [ ] A frozen worktree rejects writes, and a lease left `frozen: true` by a simulated crash is recognized and thawed by reconciliation rather than being treated as normal.
- [ ] Re-running dispatch after a simulated harness restart reuses the existing worktree and branch and reacquires the lease; no second worktree is created and no branch is reset.
- [ ] Removing a worktree without a cleanup authorization is refused.

## Blocked by

- `execution-core#01` — the `invoke` seam, the `Rejection` code set, and the real temporary Git repository fixture builders.
- `execution-core#03` — `pbi.dispatch` and the assignment record carrying the ownership generation that the lease holder references.
- `execution-core#08` — the Cleanup Authorization that gates worktree removal.
- `repository-readiness#07` — `WorkingTreeTreatment` and the rule that no worktree exists before a treatment is recorded.
- `git-integration#01` — Git Workflow Policy starting-branch resolution and the branch-naming rule.
- `harness-adapters#01` — the `ReconciliationResult.worktreeActivity` variant set and the injectable Git-state observer this slice supersedes.
