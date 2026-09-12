# Repository policy readiness: dependency, License Policy and egress declarations

Type: issue
Status: ready-for-agent
Slice: repository-readiness#06
Spec: [`../spec.md`](../spec.md) (spec 06, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/repository-readiness/spec.md`](../spec.md)

## What to build

Detect the repository's dependency and License Policy from existing configuration where present, and produce an `operator_input` item asking for it where absent. An approved license check becomes a mandatory check with structured evidence, reusing the approval machinery from `repository-readiness#04` rather than a parallel path.

Existing license findings are recorded as the preexisting baseline and stay visible without blocking, while a newly introduced dependency, license or license change violating the policy blocks the delivery. This slice *consumes* the differential comparison rather than reimplementing it: `entropy-gate#01` owns the differential classification mechanics, and the license rule here is that same comparison applied to license findings. Do not build a second comparison.

This slice also collects the repository's Data Egress Policy and Telemetry Retention declarations during onboarding as report items. Collection only — their meaning and enforcement belong to `data-handling`. Changing the License Policy after adoption is not re-detected here; it is a Governance Baseline Transition, and this slice rejects the change with a pointer to that path.

## Acceptance criteria

- [ ] A fixture with an existing license configuration resolves the policy without asking; a fixture without one produces an `operator_input` item and leaves `afkEligible` false.
- [ ] An existing license violation is recorded in the preexisting baseline and does not block, asserted through the projection.
- [ ] A newly introduced violation against the recorded baseline blocks, using the same differential comparison the gate consumes.
- [ ] Egress and retention declarations are persisted through the readiness operation and readable by the owning spec's enforcement path, with no policy semantics implemented here.
- [ ] Changing the License Policy after adoption is rejected here with a pointer to the Governance Baseline Transition path rather than silently re-detected.

## Blocked by

- `repository-readiness#01` — the readiness report skeleton and the producer registry the policy items attach to.
- `repository-readiness#03` — the `ApprovedCommandProposal` shape used by the license check.
- `data-handling#06` — the `PayloadClass` enum and `EgressAllowance` shape the egress declaration is collected against.
- `data-handling#04` — the Telemetry Retention record shape the retention declaration is collected against.
- `entropy-gate#01` — the differential classification this slice applies to license findings instead of reimplementing.
- `config-and-snapshot#01` — ConfigStore layering the resolved policy is persisted through.
