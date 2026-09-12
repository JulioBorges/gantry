# Demo fixture lifecycle: `gantry init --demo` and `demo.reset`

Type: issue
Status: ready-for-agent
Slice: demo-mode#02
Spec: [`../spec.md`](../spec.md) (spec 07, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/demo-mode/spec.md`](../spec.md)

## What to build

Materialize the fixture project from templates shipped in the package into a dedicated directory under the machine factory — never the current working directory, never a user repository — printing the path before anything is created. The fixture is a real Git repository: initialized, committed, and with no remote configured, so external effects are structurally impossible rather than suppressed. Unit identity derives from an actual Git common directory and worktree behaviour has to be genuine, which is why a simulated repository is not an option here.

`gantry init --demo` must work as the very first Gantry command a person runs, so it provisions the minimum machine factory it needs — the database at the current schema version plus a demo-scoped configuration — without requiring a prior `gantry setup`, then registers the fixture as a demo-mode Repository Execution Unit.

Add `demo.reset` to the operation catalog: it removes the demo unit's records, worktrees, and fixture, and rebuilds them. It is **deliberately exempt** from the two-step Cleanup Authorization manifest, and that exemption is not a gap to be closed later. The justification is specific rather than general — the demo unit has no remote, no provider objects, no external effects, and no dependent executions, so there is nothing for a manifest to protect. The exemption is kept narrow by *rejecting `demo.reset` against a live unit*, not by loosening cleanup authorization for anyone. Do not "fix" this by routing `demo.reset` through the manifest; that would weaken the guarantee rather than strengthen it.

This slice depends only on the shape of its blockers' interfaces, so it can be picked up as soon as they land.

## Acceptance criteria

- [ ] `gantry init --demo` succeeds on a machine with no prior `gantry setup`, no credential, and network access blocked.
- [ ] The printed path is the only path created; the current working directory and any repository under it are byte-identical before and after.
- [ ] The fixture resolves to a valid Repository Execution Unit identity and has zero configured remotes.
- [ ] `demo.reset` against the demo unit removes and rebuilds the fixture without producing a cleanup manifest; `demo.reset` against a live unit is rejected and the live unit is unmodified.
- [ ] Demo Git Workflow Policy resolves to local mode, and no provider operation is attempted anywhere in the run.

## Blocked by

- `demo-mode#01` — the mode field on the state projection and the demo-side boundary tests the registered fixture unit must satisfy.
- `execution-core#01` — the operation catalog and its runtime input schemas, `unit.register`, and Repository Execution Unit identity derivation.
- `execution-core#02` — operator channel derivation, so a `cli` invocation may assert the operator.
- `execution-core#08` — the two-step Cleanup Authorization manifest semantics that `demo.reset` is narrowly exempted from.
- `config-and-snapshot#01` — configuration layering and the effective document the demo-scoped configuration is an instance of.
- `config-and-snapshot#04` — Execution Rule Snapshot capture and identity for the demo execution.
- `machine-setup#01` — machine factory location convention and database initialization at the current schema version.
- `data-handling#01` — the redaction sink enforcement interface every demo record passes through unexempted.
