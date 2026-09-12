# Spec Adaptation by proposed complements

Type: issue
Status: ready-for-agent
Slice: spec-validation#06
Spec: [`../spec.md`](../spec.md) (spec 08, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/spec-validation/spec.md`](../spec.md)

## What to build

For a document a team already maintains, each unsatisfied rule becomes a proposed complement rather than a rewrite. A complement names the canonical section (or `criterion_identifiers`) it supplies, the rule it satisfies, the insertion location in the original document, the proposed content, and the `styleBasis` — which existing part of the document the content was patterned on, so the insertion reads like the team's own prose rather than an imported template voice.

Applying a complement edits the original document in place at its canonical location. No parallel Gantry copy is created, no heading is renamed to match a template, and applying a complement establishes no readiness and grants no approval.

This is the slice that makes `SPEC-CRITERIA-ID` fixable. Until it exists, an operator whose document has unnumbered criteria can only resolve that failure by hand-editing.

## Acceptance criteria

- [ ] Applying complements to a fixture inserts the proposed content and leaves every other byte of the document unchanged.
- [ ] No file is created anywhere outside the original document's path during adaptation.
- [ ] Every proposed complement records a `styleBasis` naming an existing part of the source document.
- [ ] Applying the `criterion_identifiers` complement makes `SPEC-CRITERIA-ID` pass on re-validation, and a later unrelated edit to the document leaves those identifiers unchanged.
- [ ] Applying complements does not set readiness; readiness only appears after validation and review run again.
- [ ] No heading present in the source document before adaptation is renamed or removed by it.

## Blocked by

- `spec-validation#01` — the structural findings that identify which rule is unsatisfied.
- `spec-validation#02` — `SPEC-CRITERIA-ID` and the criterion identity rule the `criterion_identifiers` complement supplies.
