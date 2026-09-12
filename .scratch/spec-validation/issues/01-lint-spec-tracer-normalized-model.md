# `gantry lint-spec` tracer with the normalized spec model and content-presence rules

Type: issue
Status: ready-for-agent
Slice: spec-validation#01
Spec: [`../spec.md`](../spec.md) (spec 08, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/spec-validation/spec.md`](../spec.md)

## What to build

Establish the scaffolding this spec runs on and prove it end-to-end with the four simplest rules. A normalizer reads a spec document and produces the normalized spec model: source path, normalized content hash, detected format, a mapping from each canonical section to the source heading that satisfied it with `declared | matched | absent` confidence, the identified content blocks, and an `unmapped` list of sections Gantry does not require.

A structural rule registry holds rules as declared data with stable identities and a rule set version. Evaluation walks the normalized model and never the headings, and emits one structural finding per failing rule carrying rule identity, location, and severity. This slice ships the registry with `SPEC-PROBLEM`, `SPEC-NONGOALS`, `SPEC-SECURITY` and `SPEC-ARCHITECTURE`, a single generic content-signal format, the operation-core handler that persists the validation result, and the `gantry lint-spec` command that renders it.

The structural finding shape defined here is deliberately narrower than the normalized finding shape owned by `verification-adapters#01`: findings over prose documents need rule identity, location and severity, but neither content anchors nor tree-sitter symbol derivation. The two shapes must stay compatible without either blocking the other, so every field they have in common carries an identical name. Format plurality and operator mapping override arrive in `spec-validation#04`; until then `confidence` only ever holds `matched` or `absent`.

## Acceptance criteria

- [ ] A fixture document whose non-goals sit under a heading named "Out of Scope" passes `SPEC-NONGOALS`, and the rendered mapping shows which source heading resolved it.
- [ ] A fixture missing non-goals fails `SPEC-NONGOALS` and the finding names a location in the document.
- [ ] Sections Gantry does not require appear in `unmapped` and cause no rule to fail.
- [ ] Validation completes with no harness driver invoked and no network access — asserted by a fake driver that fails the test if called.
- [ ] The persisted validation result records the rule set version and the normalized content hash of the source document.
- [ ] `gantry lint-spec` has one parity test proving it delegates to the operation core rather than reimplementing evaluation.
- [ ] Every field the structural finding shape shares with the normalized finding shape of `verification-adapters#01` is named identically, asserted so a rename on either side is caught.

## Blocked by

- `execution-core#01` — the shared operation core `invoke` seam, the operation catalog and rejection codes, and the persistence record families this operation's result is stored in.
- `data-handling#01` — normalized content hashing (line-ending normalization) for the source content hash, and the redaction sink enforcement interface for persisted output.
