# Spec format detection, mapping override, and canonical location

Type: issue
Status: ready-for-agent
Slice: spec-validation#04
Spec: [`../spec.md`](../spec.md) (spec 08, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/spec-validation/spec.md`](../spec.md)

## What to build

Replace the single generic format from `spec-validation#01` with a declared set of formats, each carrying its own mapping table: the `to-spec` structure this repository uses, the Gantry structure, and the generic content-signal fallback. Detection selects a format, the selection and the resulting mapping are shown to the operator, and the operator can override either, because normalization is a proposal and not a verdict. An override sets mapping confidence to `declared`.

This slice also adds `SPEC-LOCATION`, which fails when the document does not sit at the canonical location the repository's Artifact Location Mapping resolves for specs. This spec enforces the mapping and never resolves it.

## Acceptance criteria

- [ ] The same fixture content, presented under `to-spec` headings and under Gantry headings, yields the same canonical content in the normalized model and the same set of passing rules.
- [ ] The rendered result names the detected format and every canonical-section-to-source-heading pair with its confidence.
- [ ] An operator-supplied mapping override changes the resolution, is reflected with `declared` confidence, and re-running validation without the override restores the detected mapping.
- [ ] A spec document placed outside the mapped canonical location fails `SPEC-LOCATION`; the same document at the mapped location passes.
- [ ] A document in no recognized format still normalizes through the generic fallback rather than being rejected.

## Blocked by

- `spec-validation#01` — the normalizer and the rule registry this slice extends with format plurality.
- `repository-readiness#01` — the Artifact Location Mapping schema and resolution that `SPEC-LOCATION` enforces.
