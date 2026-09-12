# Artifact Location Mapping and the readiness report skeleton

Type: issue
Status: ready-for-agent
Slice: repository-readiness#01
Spec: [`../spec.md`](../spec.md) (spec 06, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/repository-readiness/spec.md`](../spec.md)

## What to build

Category detectors for agent instructions, constitution, ADRs, specs, PBIs or issues, and learnings. Each category declares ordered signals — repository self-description first, then existing canonical content, then conventional directories, then the Gantry fallback — resolved first-satisfied-wins with no cross-category interference, so adding a detector for one category cannot change how another resolves. Detection is strictly read-only: it opens files, walks directories and reads manifests, and executes nothing.

Resolution produces an `ArtifactLocationMapping` that is presented before persistence, is overridable per category through an operation, and is then captured in the Execution Rule Snapshot, so authoring, linting, context loading, governance protection and execution all read one mapping for the life of an execution. A category resolved by any signal other than the fallback is never moved, renamed or duplicated.

This slice also lands the report skeleton the mapping lives inside — `ReadinessItem`, `ReadinessReport`, the `afkEligible` computation, and a producer registry keyed by category so later slices attach without editing the report. The registry is the extension point `git-integration#05` and `git-integration#06` use to contribute `provider` items; this slice ships the registry, not those items. Ship `gantry init` rendering the report, and the temporary-repository fixture builder every later slice in this spec depends on: repositories that document their own conventions, repositories with an existing `AGENTS.md`, repositories with a populated `docs/adr/` and `.scratch/`, bare repositories, repositories for each supported package manager, and repositories with uncommitted and untracked changes.

## Acceptance criteria

- [ ] A fixture repository documenting its own conventions under `docs/agents/` resolves ADRs to `docs/adr/`, specs to `.scratch/<feature>/spec.md` and PBIs to `.scratch/<feature>/issues/`, and no `.gantry/specs/` or `.gantry/adrs/` directory is created.
- [ ] A fixture with a populated `docs/adr/` and no self-description still resolves ADRs there; a fixture with no convention for exactly one category receives the Gantry fallback for that category only.
- [ ] A per-category override is persisted, captured in the snapshot, and read back identically by a subsequent read operation.
- [ ] Detection runs with a process runner fake that fails the test if invoked, proving nothing in the repository is executed.
- [ ] The fixture repository's files are byte-identical before and after diagnosis apart from Gantry's own state, and nothing is moved, renamed or duplicated for a category resolved by any signal other than the fallback.
- [ ] `afkEligible` is computed from item statuses and is false whenever any item is `missing`, `needs_approval`, `needs_decision` or `blocked`; the CLI has one parity test proving it delegates to the core.

## Blocked by

- `execution-core#01` — shared operation core `invoke`, the request/receipt/rejection-code contract, and the shared fixture kit this spec's repository fixture builder extends.
- `execution-core#02` — operator-channel derivation and the `operator_channel_required` rejection, used by the per-category override operation.
- `config-and-snapshot#01` — ConfigStore layering the resolved mapping is persisted through.
- `config-and-snapshot#04` — Execution Rule Snapshot capture and identity, which the mapping is captured into.
- `data-handling#01` — redaction sink enforcement interface for persisted report evidence.

## Notes

- 2026-09-12 — `config-and-snapshot#04` no longer waits on this slice: it declares the interface it needs and tests against a fake; this slice implements or produces to that declared interface (see `config-and-snapshot#04` notes and `slice-index.md`, *Dependency graph repair*).
