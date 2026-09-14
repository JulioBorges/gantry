# Read-only multi-Run dashboard

Type: issue
Status: done
Slice: `gantry-migration#11`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add `.agents/skills/gantry/scripts/dashboard.py` and `.agents/skills/gantry-dashboard/SKILL.md`. Serve pack-owned static kanban files from a Python standard-library HTTP server bound only to `127.0.0.1`. Read Run logs across execution units into run swimlanes and Ready, Plan, Implement, Review, Critic, Integrate, Done, and Blocked columns; show repository, branch or worktree, role models, correction budget, elapsed phase time, compaction signal, and operator-waiting state. Determine staleness from the `staleAfterSeconds` snapshot in each `run.started`, never the current policy or a mutable dashboard action.

## Acceptance criteria

- [x] An HTTP test verifies `dashboard.py` binds `127.0.0.1`, serves only pack-owned zero-external-asset files, rejects a non-loopback bind request, and reflects an appended Run-log event within two seconds.
- [x] Fixture logs from two distinct `unit-id`s render their Issues in the correct phase columns with required badges; no endpoint mutates an Issue, policy, Run log, branch, or worktree.
- [x] With both Runs last updated 120 seconds ago, a Run snapshotting 60 seconds renders stale and a Run snapshotting 900 seconds does not; a later `policy.changed` event does not alter either result.
- [x] `gantry-dashboard` documents opening the read-only kanban and the dashboard test is runnable without third-party Python imports.
- [x] The Spec Changelog receives an English entry in the same merge, and `dashboard.py` passes the standard-library-only import test and its runnable test command.

## Blocked by

- `gantry-migration#08` — consumes Run-log event, execution-unit, and stale-threshold snapshot data.

## Comments
