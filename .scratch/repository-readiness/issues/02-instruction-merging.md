# Instruction merging and constitution ensuring

Type: issue
Status: ready-for-agent
Slice: repository-readiness#02
Spec: [`../spec.md`](../spec.md) (spec 06, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/repository-readiness/spec.md`](../spec.md)

## What to build

Gantry owns a delimited section of the root `AGENTS.md`, bounded by the markers `<!-- gantry:begin -->` and `<!-- gantry:end -->`, and writes only between them. Content outside the markers is never read for modification. Re-running init replaces the section's content in place; a missing marker pair appends the section; a malformed or duplicated pair blocks with a `resolve_conflict` required action rather than guessing which pair is authoritative.

When no `AGENTS.md` exists, create a minimal file containing only the marked section, at the location the Artifact Location Mapping resolved. When no `CONSTITUTION.md` exists, create one with the required structure and no invented architectural invariants — invariants are the operator's to state, and a generated constitution full of plausible rules would be treated as governance at precedence level 3 without anyone having decided it.

The readiness report names the required instruction sections explicitly — the ASDLC workflow summary, the Artifact Location Mapping reference, the approved verification commands reference, and the Governance Precedence pointer — as `instructions` and `governance` items, each with its own status.

## Acceptance criteria

- [ ] An existing `AGENTS.md` is byte-identical outside the markers after init, and a second init run replaces the section without duplicating it or accumulating whitespace.
- [ ] Malformed markers and two marker pairs each produce a `blocked` item with a `resolve_conflict` action, and neither writes to the file.
- [ ] A repository with no `AGENTS.md` gets a file containing only the marked section, at the location the mapping resolved.
- [ ] A created `CONSTITUTION.md` contains the required structure and zero invariant statements, asserted against the generated content.
- [ ] Each required instruction section appears as its own report item with a status, and a missing section leaves `afkEligible` false.

## Blocked by

- `repository-readiness#01` — the Artifact Location Mapping that resolves where `AGENTS.md` and `CONSTITUTION.md` live, plus the report item and producer registry this slice attaches to.
