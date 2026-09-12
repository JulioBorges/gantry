# Reference-first retention and replayable references

Type: issue
Status: ready-for-agent
Slice: data-handling#04
Spec: [`../spec.md`](../spec.md) (spec 04, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/data-handling/spec.md`](../spec.md)

## What to build

The default Telemetry Retention record and the references that make it replayable. A retained record holds identities, timestamps, statuses, normalized content hashes, redacted summaries, and evidence metadata, plus at least one reference locating the versioned content — a Git revision and path, a provider object identity, a PBI Worktree location, or an Execution Rule Snapshot field.

Build the resolver too: a reference is only replayable if it resolves. A reference whose source cannot be resolved is a missing-source condition that blocks reconciliation and resumption rather than being treated as a complete record. Worktree references are the weakest kind, since cleanup can remove them, so records depending on them must be surfaced to the cleanup manifest.

```ts
type ReplayableReference =
  | { kind: "git";       unit: RepositoryExecutionUnitId; revision: string; path?: string }
  | { kind: "provider";  provider: string; objectKind: string; objectId: string }
  | { kind: "worktree";  unit: RepositoryExecutionUnitId; pbi: PbiId; path: string }
  | { kind: "snapshot";  snapshot: SnapshotId; field: string };
```

## Acceptance criteria

- [ ] After a completed PBI, its records hold references, hashes, and redacted summaries rather than diffs, prompts, source files, or build logs, and each summarizing record carries at least one reference.
- [ ] Every reference in those records resolves against the real temporary Git repository or the stored snapshot.
- [ ] A record whose Git revision no longer exists blocks reconciliation with the core's reconciliation-required rejection instead of being treated as complete.
- [ ] A cleanup proposal lists the records that depend on a worktree reference it would remove.
- [ ] The dispatch payload and the retained record are distinguishable: a dispatch carrying full approved context leaves behind a reference-first record, proven by asserting the record does not contain the payload body.
- [ ] A handoff memo persists only remaining criteria, completed criteria, modified file references, and the relevant failure — no conversation history, tool transcript, or build log.

## Blocked by

- `data-handling#01` — the pipeline, the sink signature, and the normalized content hashing rule the record's hash fields use.
- `execution-core#01` — the record persistence families and the audit read this slice's records are written into and read back through.
- `execution-core#06` — the Operation Reconciliation flow and its `reconciliation_required` rejection, which a missing-source reference must trigger.
- `execution-core#08` — the Cleanup Authorization proposal manifest that must list records depending on a worktree reference.
- `pbi-execution-loop#04` — the handoff memo field set, needed for the memo criterion only; the other criteria do not wait on it.
