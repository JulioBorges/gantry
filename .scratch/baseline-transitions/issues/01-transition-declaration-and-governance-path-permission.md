# Transition declaration and governance-path permission

Type: issue
Status: ready-for-agent
Slice: baseline-transitions#01
Spec: [`../spec.md`](../spec.md) (spec 15, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/baseline-transitions/spec.md`](../spec.md)

## What to build

Establish the Governance Baseline Transition as a persisted record with a lifecycle — declared, evidence gathered, then adopted or abandoned — registered against the shared operation core's record families and state machine. The transition operations are added to the shared operation catalog rather than to a parallel surface, under the settled names `baseline.declare`, `baseline.propose`, `baseline.adopt` and `baseline.abandon`. This slice registers the family and implements `baseline.declare`; `baseline.propose` lands with the manifest in `baseline-transitions#02` and `baseline.adopt` / `baseline.abandon` land in `baseline-transitions#05`, all in the same catalog.

A PBI declares a transition during planning with the affected categories, the exact governance paths it may change, and a rationale. The declaration is validated at plan proposal — paths must resolve inside the repository's protected governance set, must be non-empty, and must not be wildcards — and is carried by Planning Approval. Approving the plan approves the intent to attempt the change and to show results; it does not approve adoption.

The declared paths are then materialized as an explicit permission on every assignment for that PBI. **This permission is the published contract that `gtp-protocol#07`'s governance protection rule reads, and it is on the project's lock-before-issues list** — it must be settled here and written down, because `gtp-protocol` would otherwise have to specify it a second time. An assignment for a PBI with no declaration carries no permission at all, and an assignment for a transition PBI carries exactly the declared paths and no more.

## Acceptance criteria

- [ ] A result from an ordinary assignment reporting a change under a protected governance path is a violation; the same change under an assignment carrying a declaration that names that path is accepted.
- [ ] A declaration naming one ADR path yields a permission that rejects a change to the constitution, proving the permission is path-scoped and not category-scoped.
- [ ] A declaration with an empty path list, a path outside the protected governance set, or a glob is rejected at plan proposal with a typed rejection code.
- [ ] Approving the plan records the declaration as approved intent; no adoption record exists and the old configuration remains authoritative after approval alone.
- [ ] The transition record and its declaration are written through the redaction sink and carry the actor provenance and snapshot identity of the approval.
- [ ] The transition PBI is schedulable, dispatchable, and gateable through the same states as any other PBI — no alternate workflow exists.

## Blocked by

- `gtp-protocol#07` — the protected governance path set resolved from the Artifact Location Mapping, and the protection rule that honors an explicit permission; the permission contract itself flows the other way, so build against the declared path set and integrate when it lands.
- `slicing-and-approval#01` — the plan proposal record and plan version identity the declaration is carried in and bound to.
- `slicing-and-approval#06` — Planning Approval, which carries the declaration as approved intent.
- `execution-core#01` — the operation catalog, record families, state machine registration, and the atomic transition-plus-audit persistence the transition record is written through.
- `execution-core#02` — actor provenance derived from the transport channel, and the operator-only channel table.
- `data-handling#01` — the redaction sink enforcement interface the transition record is written through.

## Notes

- 2026-09-12 — `gtp-protocol#07` no longer waits on this slice: it declares the interface it needs and tests against a fake; this slice implements or produces to that declared interface (see `gtp-protocol#07` notes and `slice-index.md`, *Dependency graph repair*).
