# Requirement Review and technical readiness

Type: issue
Status: ready-for-agent
Slice: spec-validation#05
Spec: [`../spec.md`](../spec.md) (spec 08, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/spec-validation/spec.md`](../spec.md)

## What to build

The Requirement Critic runs as a GTP role over the normalized spec model, the applicable rules, and the structural findings, and returns semantic findings in declared classes — ambiguity, incoherence, unverifiable, false premise, missing non-goal, scope undefined — each with a `blocker` or `warning` severity, location, statement and rationale, plus a stated coverage of what was reviewed. The critic is mandatory and additive: its result payload has no field capable of clearing a structural finding.

Technical readiness is the conjunction — all mandatory structural rules passed, a valid review, zero blocking findings — persisted against the spec's normalized content hash and the Execution Rule Snapshot, and invalidated by any edit to the document. Readiness authorizes slicing and nothing else.

```
ready = allMandatoryStructuralRulesPassed
      && reviewValid            // envelope validates, coverage stated, status complete
      && blockingFindings === 0
```

This slice has the widest cross-spec dependency set in the spec and cannot start until the GTP envelope and submission identity have landed. If it slips, `spec-validation#02`, `#03`, `#04`, `#06` and `#07` all remain workable, so the spec's critical path survives — but technical readiness is what `slicing-and-approval` waits on and it is the last piece of this spec to become available.

## Acceptance criteria

- [ ] All structural rules passing plus a clean valid review yields `ready: true`; the same with one blocking finding yields `ready: false`; the same with warnings only yields `ready: true`.
- [ ] An absent, malformed, or failed critic result leaves `ready: false` and records the failure — there is no static-only fallback that reads as readiness.
- [ ] A critic infrastructure failure consumes the Infrastructure Retry allowance and consumes no Correction Attempt; a Protocol Failure is recorded as such and not reclassified as infrastructure.
- [ ] Editing the spec document after readiness invalidates both the structural result and the review, and a subsequent readiness query reports not ready.
- [ ] The readiness record names the rule set version, the review's submission identity, and the content hash that produced it, and can be reconstructed from them.
- [ ] A readiness record does not authorize builder dispatch and does not satisfy Planning Approval — asserted by an operation that rejects on each.

## Blocked by

- `spec-validation#01` — the structural validation result this slice conjoins into readiness.
- `gtp-protocol#01` — the role task and result envelope contract, boundary validation, forward compatibility, `extensions` lifting, and Protocol Failure classification.
- `gtp-protocol#04` — status semantics, including the `complete` status a valid review requires.
- `gtp-protocol#06` — Result Submission identity and receipts for the critic's review submission.
- `config-and-snapshot#04` — Execution Rule Snapshot capture and identity, which the readiness record binds to.
- `execution-core#06` — Infrastructure Retry allowance accounting, distinct from Correction Attempt.
- `data-handling#01` — the redaction sink enforcement interface for persisted critic output.
