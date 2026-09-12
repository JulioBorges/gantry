# Declared contract validation per format

Type: issue
Status: ready-for-agent
Slice: spec-validation#03
Spec: [`../spec.md`](../spec.md) (spec 08, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/spec-validation/spec.md`](../spec.md)

## What to build

Formal contracts must be stated rather than implied, and a stated contract must be structurally validated or visibly marked as unvalidated. Declared contracts are extracted into the normalized spec model with their format and location.

`SPEC-CONTRACT-PRESENT` requires at least one declared contract. `SPEC-CONTRACT-FORMAT` requires the format to be one Gantry can validate — JSON Schema, TypeScript type declarations, or OpenAPI fragments — and when the operator explicitly declares an unsupported format instead of converting it, the result records that no structural validation was performed rather than passing silently. `SPEC-CONTRACT-VALID` runs the per-format structural validator over each contract in a supported format.

## Acceptance criteria

- [ ] A fixture with a malformed JSON Schema fails `SPEC-CONTRACT-VALID` with a location inside the contract block.
- [ ] A fixture whose only contract is in an unsupported format fails `SPEC-CONTRACT-FORMAT` and does not fail `SPEC-CONTRACT-VALID`.
- [ ] When the operator declares the format of an unsupported contract, the persisted result carries an explicit marker that no structural validation was performed for it.
- [ ] A fixture with no contract at all fails `SPEC-CONTRACT-PRESENT`.
- [ ] Each of the three supported formats has at least one valid and one malformed fixture, and both outcomes are asserted by rule identity.

## Blocked by

- `spec-validation#01` — the rule registry and the normalized spec model the extracted contracts attach to.
