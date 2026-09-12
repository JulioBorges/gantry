# Candidates from handoff patterns and integrity findings

Type: issue
Status: ready-for-agent
Slice: compound-learning#03
Spec: [`../spec.md`](../spec.md) (spec 18, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/compound-learning/spec.md`](../spec.md)

## What to build

Extend production across the two families owned further out in the pipeline. Retained, numbered handoff memos yield observations about slices that always need a handoff at a comparable point; the useful instruction there is about decomposition, so the candidate's proposed rule targets slicing guidance rather than implementation. Integrity findings yield observations about attempts to weaken verification — the highest-signal source in this spec, and the one whose candidates should propose the narrowest rules.

Both use the slice `compound-learning#01` producer contract unchanged, including the configured minimum recurrence below which no candidate is produced. The thinness of the evidence is load-bearing here: a memo record holds remaining criteria, completed criteria, modified file references and the relevant failure, and nothing else. Memo-sourced candidates therefore cite the memo record reference and can never quote conversation history, tool transcript or build log content, because none of it is retained.

## Acceptance criteria

- [ ] Three PBIs each requiring a handoff at a comparable point produce one candidate with three occurrences citing the memo records and an occurrence count of three.
- [ ] An integrity finding recurring across two PBIs produces a candidate citing both integrity finding records.
- [ ] A single handoff on a single PBI produces no candidate under the configured minimum recurrence.
- [ ] Memo-sourced candidates cite the memo record reference and never quote conversation history, tool transcript, or build log content, because none is retained.

## Blocked by

- `compound-learning#01` — the producer contract, the learning record families, and the two production validations these sources reuse unchanged.
- `pbi-execution-loop#04` — the retained handoff memo record, its field set, and handoff numbering.
- `entropy-gate#04` — the integrity finding record produced by the verification integrity comparison.
