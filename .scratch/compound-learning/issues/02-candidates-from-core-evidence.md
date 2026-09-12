# Candidates from Correction Attempts, Protocol Failures, and state transitions

Type: issue
Status: ready-for-agent
Slice: compound-learning#02
Spec: [`../spec.md`](../spec.md) (spec 18, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/compound-learning/spec.md`](../spec.md)

## What to build

Extend candidate production across three more retained families that all live close to the core. Correction Attempt accounting records yield observations about slices that consumed repeated attempts against the same rule. Protocol Failure conditions yield observations about a recurring contract mistake on a role. The audit transition log yields observations about a recurring state path — repeatedly entering a blocked condition for the same reason, for example.

Each source tags its candidates with its `sourceKinds` entry, so the per-source rejection backoff built later can attribute a rejection to the family that produced it. Nothing about the producer contract changes: these families use the same grouping, the same evidence-resolvability rule, and the same instruction-versus-observation validation delivered in slice `compound-learning#01`. As there, an occurrence whose evidence reference does not resolve at production time is dropped and a candidate left with none is not produced.

## Acceptance criteria

- [ ] Seeding a PBI that consumed four Correction Attempts against one rule produces a candidate whose source kind is the correction attempt and whose occurrences cite the correction records.
- [ ] Seeding two Protocol Failures of the same class on one role produces a single candidate citing both, not two candidates.
- [ ] A recurring state-transition path produces a candidate citing audit records; a single non-recurring transition does not.
- [ ] Each produced candidate's `sourceKinds` matches the family it was read from, and candidates from these sources honour the same unresolvable-reference and restatement refusals proven in slice 01.

## Blocked by

- `compound-learning#01` — the producer contract, the learning record families, and the two production validations these sources reuse unchanged.
- `execution-core#05` — Correction Attempt accounting records, the count consumed and the rule each attempt was against.
- `entropy-gate#06` — the correction loop's attempt records and subject derivation, which name what was being corrected.
- `gtp-protocol#01` — Protocol Failure as a persistent condition on an assignment, including its class.
- `execution-core#01` — the audit transition log and its record fields, the source for a recurring state path.
