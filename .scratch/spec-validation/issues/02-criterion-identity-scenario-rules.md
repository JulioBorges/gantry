# Criterion identity and Given-When-Then scenario rules

Type: issue
Status: ready-for-agent
Slice: spec-validation#02
Spec: [`../spec.md`](../spec.md) (spec 08, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/spec-validation/spec.md`](../spec.md)

## What to build

Extend the rule registry with the two rule families that make a spec's behavioral content addressable. Acceptance criteria are extracted into the normalized spec model as individually identified items with text and location, and criterion identifiers are required rather than generated — a generated identifier renumbers on insertion and silently breaks every downstream reference. `SPEC-CRITERIA-PRESENT` fails when criteria are absent or not individually identifiable; `SPEC-CRITERIA-ID` fails when any criterion lacks a stable identifier. Scenarios are parsed into given, when and then parts; `SPEC-SCENARIOS-COUNT` requires at least three and `SPEC-SCENARIOS-PARSE` requires each one to parse into all three parts.

**This slice establishes a published contract: the criterion identity rule — required, never generated, stable.** It is one of the widest-read contracts in the project. `gtp-protocol#02`, `gtp-protocol#03` and `gtp-protocol#05` reference criteria by identifier in task and result envelopes and in criterion accounting; `slicing-and-approval` carries criterion references from spec into PBIs; `entropy-gate` relies on the same identities. Three other specs are waiting on the shape settled here, so it must be decided deliberately rather than incidentally.

Be aware of the ordering: `SPEC-CRITERIA-ID` on a document a team already maintains is the most intrusive requirement in this spec. This slice makes it fail; `spec-validation#06` makes it fixable by proposing the identifiers as a complement. Anyone demoing this slice before `#06` exists will see a failure that can only be resolved by hand-editing the document. That is acceptable ordering, but it should not come as a surprise.

## Acceptance criteria

- [ ] A fixture with unnumbered criteria fails `SPEC-CRITERIA-ID`; a fixture whose criteria carry identifiers passes it and the identifiers appear unchanged in the normalized model.
- [ ] Inserting a new criterion into a fixture leaves every pre-existing criterion's identifier unchanged.
- [ ] A fixture with two scenarios fails `SPEC-SCENARIOS-COUNT`; a fixture with three passes.
- [ ] A fixture containing a scenario with no `then` part fails `SPEC-SCENARIOS-PARSE` with a location pointing at that scenario.
- [ ] Every assertion in this slice's tests is on rule identity, not on message text.

## Blocked by

- `spec-validation#01` — the rule registry, the normalized spec model, and the structural finding shape.
