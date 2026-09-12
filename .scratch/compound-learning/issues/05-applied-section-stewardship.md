# Applied-section stewardship: grouping, removal, size limit, and consolidation

Type: issue
Status: ready-for-agent
Slice: compound-learning#05
Spec: [`../spec.md`](../spec.md) (spec 18, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/compound-learning/spec.md`](../spec.md)

## What to build

Keep the marked section usable. Applied learnings render grouped by theme, each with compact provenance, and an operator can remove a previously applied learning: the removal is recorded with actor provenance and timestamp, and the section re-renders without it. Everything here goes through the same rule established in slice `compound-learning#01` — the region between `<!-- gantry:begin -->` and `<!-- gantry:end -->` is **rendered from the persisted record set, never appended to or edited in place** — so removal, grouping and consolidation are all changes to records followed by a re-render, and operator-written content outside the markers stays byte-identical across every one of them.

The section carries a configured maximum. On reaching it, `learning.approve` is refused with a consolidation-required condition until the operator consolidates — shown the existing learnings grouped, then merging or removing — after which approval proceeds. An instructions file long enough that agents skim it is worse than a short one, so unbounded growth would make this mechanism actively harmful rather than merely unhelpful.

Consolidation relocates that cost rather than removing it: it is work the operator has to do at the least convenient moment, when they are trying to approve something else. The realistic failure is the limit being raised instead of consolidation happening, which returns the original problem. So the signal the operator needs to watch must be observable from the record rather than from memory: the configured limit value and **every change to it** are recorded in the audit trail with old value, new value and actor, and a read operation reports the current maximum, the current section size, the number of consolidations performed, and the full history of limit changes.

## Acceptance criteria

- [ ] Applied learnings render grouped, each with its provenance; content outside the markers stays byte-identical across every render.
- [ ] Removing an applied learning re-renders the section without it and records the removal with actor provenance and timestamp.
- [ ] With the section at its configured maximum, `learning.approve` is refused with a consolidation-required condition; after a consolidation that reduces the section below the maximum, the same approval succeeds.
- [ ] A change to the configured section maximum is recorded in the audit trail with its old and new value and the actor who made it.
- [ ] A read operation reports the current maximum, the current section size, the number of consolidations performed, and the history of limit changes.
- [ ] Consolidation and removal are operator-only; both are rejected `operator_channel_required` over the MCP channel.

## Blocked by

- `compound-learning#01` — the applied-learning record family and the render-from-records rule this slice's grouping, removal and consolidation all operate through.
- `repository-readiness#01` — the Artifact Location Mapping entries for agent instructions and learnings.
- `repository-readiness#02` — ownership of the marked-section contract whose in-place replacement rule the render must not reintroduce.
- `config-and-snapshot#01` — the configuration schema holding the section maximum.
- `config-and-snapshot#04` — Execution Rule Snapshot capture of the section maximum.
- `execution-core#01` — the audit record carrying limit changes, removals and consolidations.
