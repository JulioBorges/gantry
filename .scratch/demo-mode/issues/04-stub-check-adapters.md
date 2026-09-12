# Stub check adapters and scripted Comparison Evidence

Type: issue
Status: ready-for-agent
Slice: demo-mode#04
Spec: [`../spec.md`](../spec.md) (spec 07, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/demo-mode/spec.md`](../spec.md)

## What to build

Implement the stub check adapters against the same `CheckAdapter` interface the real adapters implement, returning pre-recorded structured reports whose findings carry the full normalized shape — rule, path, symbol, severity, content anchor, problem identity — so the real comparison logic can match them without a demo-only branch anywhere in the comparison path.

Script the finding sets per subject revision so the scenario shows the product's argument rather than a happy path: one PBI's Merge Candidate carries a finding absent from the current target, which is a genuine Quality Regression; one PBI's initial evaluation produces findings that the scripted correction resolves; and the remaining PBI is clean. Also script a mandatory-test check, so Gantry's own re-verification on the delivered revision has evidence to consume rather than nothing.

Declare check stability and resource needs through the same declarations real adapters use. Version the scripted reports with the package and validate them against the report schema in the test suite, so a change to the report contract updates the demo in the same commit instead of leaving scripted evidence that no longer describes anything real.

This slice depends only on the shape of its blockers' interfaces, so it can be picked up as soon as they land.

## Acceptance criteria

- [ ] The stub satisfies the `CheckAdapter` type with no added methods and no demo-only branch in the comparison path.
- [ ] Every scripted finding carries enough identity to satisfy Evidence Completeness; an incomplete scripted finding fails closed exactly as a real one would.
- [ ] Running the same scripted check twice against the same revision produces identical reports, satisfying the declared stability requirement.
- [ ] Candidate-versus-target scripted evidence yields exactly one differential regression for the designated PBI and zero for the others.
- [ ] Scripted reports are versioned with the package and validated against the report schema in the test suite.

## Blocked by

- `verification-adapters#01` — the check adapter seam, `StructuredReport`, `NormalizedFinding`, the problem-identity rule, and the collected mandatory-test identities on the `mandatory_test` report.
- `verification-adapters#03` — Evidence Completeness and the fail-closed treatment of incomplete evidence.
- `verification-adapters#04` — the Check Stability declaration and adapter failure classification.
- `verification-adapters#05` — the scoped Check Resource declaration real adapters use.
