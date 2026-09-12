# Structured spec authoring

Type: issue
Status: ready-for-agent
Slice: spec-validation#07
Spec: [`../spec.md`](../spec.md) (spec 08, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/spec-validation/spec.md`](../spec.md)

## What to build

Authoring produces a new spec in a structure that passes Spec Structural Validation, so that authoring and validation agree by construction. When the repository has a detected spec format, the authored document uses that format; otherwise it uses the `to-spec` structure.

The authored document is written to the canonical location the Artifact Location Mapping resolves; a document written elsewhere fails `SPEC-LOCATION` rather than being silently accepted. The authoring templates are structured content, not a mandatory rewrite of anything existing — this slice adds a way to create a spec, never a requirement to convert one.

## Acceptance criteria

- [ ] In a temporary repository with a detected `to-spec` format, an authored spec is produced in that format and validates with all mandatory rules passing except those requiring operator-supplied content.
- [ ] In a repository with a different detected format, the authored spec uses that format rather than the default.
- [ ] The authored document lands at the mapped canonical location; an authored document directed elsewhere fails `SPEC-LOCATION`.
- [ ] Authoring produces at least three parseable Given-When-Then scenario slots and criterion identifier slots, so a completed authored spec can reach all-rules-passing without adaptation.
- [ ] Authoring establishes no readiness and no approval.

## Blocked by

- `spec-validation#04` — format detection, canonical location resolution, and `SPEC-LOCATION`.
- `machine-setup#03` — the skill packaging and installation mechanism, needed only to ship the conversational authoring surface into harness conventions; the authoring operation itself belongs to this spec.
