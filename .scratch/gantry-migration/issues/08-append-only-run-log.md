# Append-only Run log and snapshots

Type: issue
Status: done
Slice: `gantry-migration#08`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add `.agents/skills/gantry/scripts/runlog.py` as the append/query format owner for JSONL events under `~/.gantry/state/<unit-id>/runs/<run-id>.jsonl`. Derive `unit-id` from the first twelve hex characters of SHA-256 of the real `git rev-parse --git-common-dir`, so worktrees share state. Validate the required lifecycle, round, phase, subagent, compaction, policy, Issue, review, and refutation event shapes without storing diffs or prohibited command output. Persist the policy hash, tier, repository root, and effective `staleAfterSeconds` supplied in a `run.started` event; add an inflight query for interrupted work. Workflow emission is owned by `gantry-migration#14`.

## Acceptance criteria

- [x] `runlog.py append` accepts a valid `run.started` event containing repository root, policy hash, tier, and effective `staleAfterSeconds`, rejects malformed or unknown event payloads with exit 1, and persists the supplied event unchanged as one JSON object per line.
- [x] Two worktrees of one clone compute the same twelve-hex `unit-id`; `runlog.py inflight <unit-id> --json` reports the Issue, phase, and worktree of an interrupted Run and excludes a finished Run.
- [x] A concurrent-writer test launches two appenders and proves every JSONL line parses, while an append up to 64 KB uses one write system call and never stores a diff or check command output; checks marked `secrets: true` record only exit codes and counts.
- [x] A `policy.changed` event is accepted without mutating the stale-threshold snapshot already written for a Run; `runlog.py inflight <unit-id> --json` derives state from valid persisted events, and `runlog.py --help` and machine-readable query output work.
- [x] The Spec Changelog receives an English entry in the same merge, and `runlog.py` passes the standard-library-only import test and its runnable test command.

## Blocked by

- `gantry-migration#02` — consumes canonical workflow paths and its resolved policy contract.

## Comments
