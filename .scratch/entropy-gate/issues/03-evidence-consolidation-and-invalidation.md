# Evidence consolidation: reuse, target currency, and invalidation

Type: issue
Status: ready-for-agent
Slice: entropy-gate#03
Spec: [`../spec.md`](../spec.md) (spec 13, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/entropy-gate/spec.md`](../spec.md)

## What to build

How the gate obtains its evidence without becoming an analyzer. The gate requests check results for both revisions from the configured checks and reuses an existing report only when the subject revision, the rule-set version, the tool version, and the approved command reference all match what is being assessed; if any one of the four differs, it requests a fresh run. The gate itself runs no analysis: every finding it reasons about arrived from a check adapter through an evidence request.

Target evidence is always obtained against the *current* target revision at decision time, never a cached earlier one, because the target advances as other PBIs integrate. Any subsequent change to the candidate revision, the target revision, or the rule version invalidates the decision: the gate returns to `pending` and a fresh comparison is required. The prior decision is retained as history rather than carried forward, so an approval is never inherited across an advancing branch.

Declared coverage travels with every report — reused or freshly obtained — into the decision, so the scope of what was verified is visible wherever the evidence appears.

## Acceptance criteria

- [ ] A report matching on revision, rules, tool version, and command is reused; changing any one of the four triggers a fresh run request.
- [ ] Target evidence is requested against the current target revision; a target that advanced since the previous decision produces a fresh comparison rather than reusing the earlier target report.
- [ ] A target advancing after a passing decision returns the gate to `pending`; any candidate change does the same.
- [ ] A check adapter fake that fails the test when invoked outside an evidence request proves the gate runs no analysis of its own.
- [ ] Declared coverage travels with each reused or freshly obtained report into the decision.

## Blocked by

- `entropy-gate#01` — provides the gate decision record and the evidence references this slice populates.
- `verification-adapters#01` — provides the check adapter interface and its run request and outcome shapes.
- `verification-adapters#03` — provides the consumption-time report reuse verdict over revision, rule-set version, tool version, grammar version and command reference.
- `repository-readiness#04` — provides the approved verification command reference and the declared coverage that travels with it.
- `config-and-snapshot#04` — provides the Execution Rule Snapshot identity that binds each obtained report to the rules in force.

## Notes

`#02` and `#03` are semantically independent but both amend the same decision path and will touch adjacent code. Whoever runs them concurrently should expect a textual merge; sequencing `#03` after `#02` is the fallback.
