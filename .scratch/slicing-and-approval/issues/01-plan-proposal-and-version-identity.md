# Plan proposal and plan version identity

Type: issue
Status: ready-for-agent
Slice: slicing-and-approval#01
Spec: [`../spec.md`](../spec.md) (spec 09, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/slicing-and-approval/spec.md`](../spec.md)

## What to build

Stand up the plan record family and the `plan.propose` operation end to end. A slicer role result — proposed PBIs with behavior, criteria carrying spec criterion identifiers, verification entries, prerequisites, story coverage, scope hint, and a context estimate — is validated for shape, persisted, and reduced to a `PlanVersion` whose identity is a hash over the spec content hash, the ordered per-PBI content hashes, and the dependency graph. The story coverage map is derived and stored as part of the version. `gantry slice-spec` drives this from the CLI against a fake slicer harness driver, and the state projection exposes the proposal and its version identity.

This slice defines the **plan version hash**: its inputs, their ordering, and their normalization. That definition is a published contract on the project's lock-before-issues list — `pbi-execution-loop` gates builder dispatch on it and `baseline-transitions` reads it. If the inputs are loose or unnormalized, Planning Approval silently leaks across edits, so the hash definition must be settled and written down here rather than left implicit in the implementation.

This slice does not lint, estimate, or approve. It also publishes the `ProposedPbi` shape and the persisted plan proposal record consumed by `gtp-protocol`, `pbi-execution-loop`, `baseline-transitions`, and `dashboard`.

## Acceptance criteria

- [ ] A slicer result persists a plan proposal and returns a stable `PlanVersionId`; re-proposing byte-identical content yields the same identity.
- [ ] Reordering PBIs in the slicer payload does not change the identity; editing any PBI's content, the spec content, or an edge in the dependency graph does change it.
- [ ] Plan version hashing is computed over normalized content, so `core.autocrlf` line-ending differences do not alter the identity.
- [ ] The stored proposal records the story coverage map keyed by spec user story identifier.
- [ ] A proposal whose criteria carry identifiers not present in the normalized spec model is rejected at the operation boundary.
- [ ] `gantry slice-spec` is one parity test proving delegation to `invoke`, not behavior.

## Blocked by

- `execution-core#01` — provides the operation core `invoke` surface, request/outcome shapes, record families, and rejection codes.
- `gtp-protocol#03` — provides the slicer role task and result payload contract.
- `spec-validation#01` — provides the normalized spec model, user story identifiers, and the spec content hash.
- `spec-validation#02` — provides the criterion identity rule (required, never generated, stable).
- `data-handling#01` — provides normalized content hashing (line endings) and the redaction sink enforcement interface for the persisted proposal.
- `repository-readiness#01` — provides the Artifact Location Mapping schema used to locate spec and PBI documents.
