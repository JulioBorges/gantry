# Propagate the Run ID into git hooks' environment

Type: issue
Status: draft
Slice: `gantry-migration#19`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-14

## Parent

`gantry-migration`

## What to build

Give the tracked git hooks (`.agents/skills/gantry/hooks/git/pre-commit`, `pre-push`) a reliable way to
resolve the active `GANTRY_RUN_ID` (and `GANTRY_STATE_ROOT`) so a real denial in production is recorded,
not only a denial provoked under a test that sets the variable itself. Per
`docs/adr/0005-git-hooks-enforce-git-rules.md`, recording is documented as best-effort today because
nothing in this pack exports `GANTRY_RUN_ID` into a subagent's Bash environment before it shells out to
`git`. This Issue closes that gap. The chosen mechanism must stay correct when multiple worktrees of the
same execution unit run Rounds concurrently (`docs/adr/0002-worktree-isolation-and-serialized-integration.md`):
a naive single "current run" marker keyed only by unit ID would misattribute one worktree's denial to
another worktree's Run, which is worse than an unrecorded denial. Two directions to weigh: (a) have the
round workflow (`.agents/skills/gantry/reference/round-workflow.md`) export `GANTRY_RUN_ID` and
`GANTRY_STATE_ROOT` into every subagent invocation it starts (`requestRole`/`agent()` call sites for
Implementer, Reviewer and Critic), scoped so two worktrees never share a value; or (b) have `runlog.py`
record a marker keyed by the real, resolved worktree path (not just the shared unit ID) that the hooks
read as a fallback when the environment variable is absent, updated on `run.started`/`run.resumed` and
cleared on `run.cancelled`/`run.finished` for that same worktree. Either direction must not change what a
hook denies -- only whether the denial is recorded.

## Acceptance criteria

- [ ] A test provokes a `pre-commit` denial and a `pre-push` denial in a temporary repository where the
  test does not set `GANTRY_RUN_ID` (only whatever the chosen mechanism sets up ahead of time, e.g. a
  seeded marker or a round-workflow invocation), and `hook.denied` is still appended for each denial.
- [ ] A second concurrent worktree of the same execution unit, running a different Run, never has the
  first worktree's denials attributed to its own Run: each worktree's `hook.denied` events land only in
  that worktree's own Run log.
- [ ] `docs/adr/0005-git-hooks-enforce-git-rules.md`'s decision paragraph is restored to state the actual
  propagation mechanism this Issue builds, replacing the "best-effort ... deferred" language.
- [ ] `.scratch/gantry-migration/spec.md`'s Constraints section is updated back to state that a hook
  denial's recording is guaranteed (not conditional on an operator- or test-set environment variable),
  and the Spec Changelog receives an English entry in the same merge.

## Blocked by

- `gantry-migration#09` — consumes the git hooks' `hook.denied` recording contract and `runlog.py`'s
  event/append surface.
- `gantry-migration#14` — consumes the round workflow's subagent-spawn call sites, if direction (a) is
  chosen.

## Comments

- 2026-09-14 — Opened while `gantry-migration#09`'s round-3 critic feedback asked the operator to choose
  between guaranteed and best-effort `hook.denied` recording; the operator had not answered by the time
  that round had to proceed, so best-effort recording was kept as the lower-risk default (see the comment
  and Changelog entry on `gantry-migration#09`) and this Issue was opened as the owner of closing the gap
  later. Enforcement itself (a hook denies the operation) is unconditional and unaffected either way; only
  whether the denial is *recorded* in the Run log is currently best-effort, gated on `GANTRY_RUN_ID` being
  present in the environment. Left `Status: draft` because the mechanism (round-workflow env export vs. a
  runlog-recorded per-worktree marker) is an open design choice, and the concurrency-correctness
  requirement above needs operator sign-off before slicing -- as does confirming best-effort recording is
  acceptable to keep in the meantime.
