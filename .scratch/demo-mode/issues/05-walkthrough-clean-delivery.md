# Scripted walkthrough: clean delivery, Protocol Failure, and the dependency wait

Type: issue
Status: ready-for-agent
Slice: demo-mode#05
Spec: [`../spec.md`](../spec.md) (spec 07, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/demo-mode/spec.md`](../spec.md)

## What to build

Author the fixture's canonical spec and PBI breakdown, record the Planning Approval, and drive the first scripted PBI end to end through the real operation core: dispatch, all criteria completed with evidence, mandatory tests verified on the delivered revision, Implementation Completion, gates passed, local merge confirmed, `integrated`. Nothing in the walkthrough may take a shortcut around the core; the whole point is that what an evaluator sees is actual behaviour.

In the same walkthrough, script one dispatch that returns an invalid result so a Protocol Failure occurs — preserving the completed work and advancing nothing — and declare one PBI dependent on another so it waits in `awaiting_dependency` until Dependency Readiness is satisfied by the prerequisite's integration. These two moments are brief but present because they are the behaviours hardest to believe without seeing.

Assertions are on the sequence of Execution States each PBI passes through and on the resulting projections, never on rendered text. This slice and `demo-mode#06` share one fixture plan: agree the fixture's PBI list, dependency edges, and criterion identities once here, at the start, and treat them as fixed thereafter.

**Scheduling note.** Unlike `#01`–`#04`, this slice encodes concrete state sequences rather than interface shapes. Do not start it until `git-integration`'s issues exist, or the expected sequences will have to be rewritten.

## Acceptance criteria

- [ ] The first PBI's state sequence reaches `integrated` through `implementation_complete`, `in_gates`, `awaiting_review`, and `merge_authorized`, with no state skipped.
- [ ] The invalid scripted result produces a Protocol Failure; the PBI's state is unchanged afterwards and the prior completed work is still retrievable.
- [ ] The dependent PBI remains in `awaiting_dependency` while the prerequisite is unintegrated and becomes eligible only after the prerequisite reaches `integrated`.
- [ ] Local merge requires the operator confirmation step; the walkthrough supplies it through an operator channel and a test proves an agent channel is refused.
- [ ] The whole walkthrough runs with no network access and creates no provider object.

## Blocked by

- `demo-mode#02` — the provisioned fixture, the registered demo unit, and `demo.reset` for a fresh run.
- `demo-mode#03` — the stub harness drivers and the scripted envelopes, including the deliberately invalid result.
- `demo-mode#04` — the stub check adapters and the scripted mandatory-test evidence the gates consume.
- `execution-core#02` — operator channel provenance, so the confirmation can be asserted from `cli` and refused from an agent channel, and version-bound Planning Approval.
- `pbi-execution-loop#01` — PBI Worktree lifecycle and the worktree lease.
- `pbi-execution-loop#02` — dispatch scheduling and the eligibility conjunction that holds a PBI in `awaiting_dependency`.
- `pbi-execution-loop#05` — result handling and micro-commits that advance a PBI on a delivered result.
- `gtp-protocol#01` — Protocol Failure semantics: work preserved, nothing advanced.
- `gtp-protocol#05` — criterion accounting and Implementation Completion.
- `git-integration#01` — Git Workflow Policy resolution in local mode and the integration operation surface.
- `git-integration#03` — local merge, the Mutation Approval Boundary confirmation, and its Operation Reconciliation.
