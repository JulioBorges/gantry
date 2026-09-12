# Absolute mandatory rules and fail-closed evidence handling

Type: issue
Status: ready-for-agent
Slice: entropy-gate#02
Spec: [`../spec.md`](../spec.md) (spec 13, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/entropy-gate/spec.md`](../spec.md)

## What to build

The two paths that sit outside the differential. Rules configured as absolute are evaluated against the candidate alone: any occurrence blocks, whether or not the target has it too. Absolute violations are recorded in a field of the decision separate from the differential classifications, so the two can never be conflated and a violation can never be offset by an improvement. No code path routes an absolute violation through classification.

Separately, fail-closed evidence handling. A finding lacking `rule`, `path`, `severity`, or its problem identity, or a report lacking subject revision, tool version, rule-set version, or declared coverage, is invalid Comparison Evidence: the decision takes the distinct blocked-on-incomplete-evidence outcome. Missing or invalid evidence is never read as zero findings, and there is no default that turns an absent report into a clean one. A `pass_fail` check outcome satisfies its mandatory role and contributes no classification to the differential, so it cannot on its own establish non-regression.

Both paths are additive: a check purpose whose absolute-rule set is empty must behave exactly as it did before this slice.

## Acceptance criteria

- [ ] An absolute-rule violation present in both the target and the candidate blocks the gate.
- [ ] Absolute violations appear in the decision separately from the differential classifications, and no code path routes one through classification.
- [ ] A report with a finding missing any required field yields the incomplete-evidence outcome, not a passing decision and not zero findings.
- [ ] A `pass_fail` outcome for a mandatory check satisfies the mandatory role, produces no classification, and cannot on its own establish non-regression.
- [ ] A check purpose whose absolute-rule set is empty behaves identically to the pre-slice behavior, proving the path is additive.

## Blocked by

- `entropy-gate#01` — provides the gate decision record and the classification pipeline this slice writes into.
- `verification-adapters#03` — provides the Evidence Completeness required-field list, the operator finding classification escape scoped to one finding in one report version, and the `pass_fail` outcome that is structurally rejected by the comparison input.
- `config-and-snapshot#01` — provides the `gates.*` configuration section carrying the per-check-purpose blocking thresholds and the per-rule absolute flags.

## Notes

`#02` and `#03` are semantically independent but both amend the same decision path and will touch adjacent code. Whoever runs them concurrently should expect a textual merge; sequencing `#03` after `#02` is the fallback.
