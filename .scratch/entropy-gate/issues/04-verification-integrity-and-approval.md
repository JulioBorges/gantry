# Verification integrity comparison, assertion-shape warning, and operator approval

Type: issue
Status: ready-for-agent
Slice: entropy-gate#04
Spec: [`../spec.md`](../spec.md) (spec 13, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/entropy-gate/spec.md`](../spec.md)

## What to build

The comparison of the verification itself between target and candidate, producing integrity findings that block independently of whether every check passed. The deterministic kinds are: a mandatory check removed in the candidate's configuration, a mandatory check disabled in it, a mandatory test removed relative to the target's collected test set, a mandatory test skipped relative to that set, and an approved acceptance criterion losing its covering verification entry. Agents remain free to add or strengthen tests — only reduction is a finding.

On top of those, an always-on assertion-shape comparison over the candidate's modified test files, at warning severity. It compares assertion count per test and matcher class, ordered from discriminating (equality, structural match) to permissive (truthiness, definedness, no-throw); a drop produces an assertion-shape warning. This is a syntactic heuristic, is labelled as one, does not block on its own, and is evadable by anyone who intends to evade it. Because the warning can manufacture confidence it has not earned, the projection must surface, next to any assertion-shape warning, whether the opt-in mutation adapter is enabled for that check configuration — the strength of the answer visible with the answer.

This slice also produces the **covered test-change set**: which candidate-modified test files cover which approved criteria. It is used here for criterion coverage reduction, and it is the predicate `entropy-gate#05`'s automatic critic escalation keys on. An integrity finding blocks the gate until an operator explicitly approves the change through the operator channel; the approval records actor provenance and clears that finding for that candidate only. A green check result accompanied by an unapproved integrity finding can never authorize merge.

## Acceptance criteria

- [ ] A mandatory test present in the target's collected set and skipped in the candidate's is an integrity finding that blocks the gate even when every check passes.
- [ ] A check disabled in the candidate configuration, and an approved criterion losing its covering verification entry, each produce an integrity finding.
- [ ] Adding or strengthening a test produces neither an integrity finding nor an assertion-shape warning; changing an equality assertion to a presence assertion produces an assertion-shape warning at warning severity that does not block on its own.
- [ ] An operator approval through the operator channel clears a named integrity finding and records provenance; the same request through a non-operator channel is rejected with the operator-channel-required rejection.
- [ ] A green check result accompanied by an unapproved integrity finding cannot produce a passing gate.
- [ ] The projection shows, next to any assertion-shape warning, whether the mutation adapter is enabled for that check configuration.

## Blocked by

- `entropy-gate#01` — provides the gate decision record the integrity findings are written into and the blocking reasons they contribute.
- `verification-adapters#01` — provides the collected mandatory-test identity set, including per-test skip status, on the `mandatory_test` adapter report.
- `verification-adapters#08` — provides the opt-in mutation adapter and the mutation-adapter-enabled state for a check configuration that the projection surfaces.
- `spec-validation#02` — provides criterion identity, required and stable and never generated.
- `slicing-and-approval#01` — provides the PBI acceptance criteria list carrying its spec criterion references.
- `repository-readiness#04` — provides the declared coverage entries on approved verification commands that criterion coverage is measured against.
- `execution-core#02` — provides the operator channel assertion, actor provenance, and the operator-channel-required rejection.

## Notes

This slice is deliberately kept whole: the deterministic integrity kinds, the assertion-shape warning, and the operator approval ship together, because the assertion-shape finding is a variant of the same integrity finding type and both halves need the same covered test-change set. If it proves too large in practice, the natural cut line is deterministic integrity kinds plus operator approval in one slice, and assertion-shape warning plus covered test-change set plus mutation visibility in another, with `entropy-gate#05` then blocked by the second. Do not pre-split it without operator approval.
