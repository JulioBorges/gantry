# Correction loop: subject derivation, attempt accounting, and exhaustion

Type: issue
Status: ready-for-agent
Slice: entropy-gate#06
Spec: [`../spec.md`](../spec.md) (spec 13, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/entropy-gate/spec.md`](../spec.md)

## What to build

What happens after a decision blocks. The gate derives a correction subject from its blocking reasons — the concrete findings to fix, named individually, with no aggregate framing — and dispatches a correction assignment, followed by revalidation with fresh evidence rather than the pre-correction candidate report.

Attempt accounting is exact. The initial gate evaluation consumes nothing. **A Correction Attempt is consumed at correction dispatch, not at revalidation**, so an interrupted cycle stays consumed and a resume continues the same attempt rather than starting a new one. An integrity finding cleared by operator approval rather than by correction consumes no attempt, because nothing was corrected.

Exhaustion of the PBI's shared allowance with unresolved blocking findings moves the gate to failed, stops automatic correction, and keeps merge prohibited. An explicit operator grant permits further attempts additively; the consumed count is preserved and never reset.

## Acceptance criteria

- [ ] The initial gate evaluation consumes no Correction Attempt; each correction dispatch consumes exactly one, at dispatch.
- [ ] The correction subject names each blocking finding individually and carries no aggregate framing.
- [ ] Revalidation after a correction obtains fresh evidence rather than reusing the pre-correction candidate report.
- [ ] Attempts exhausted with an unresolved blocker yields a failed gate, stops automatic correction, and leaves merge prohibited.
- [ ] An operator grant permits further attempts and the consumed count does not reset.
- [ ] An operator-approved integrity finding is cleared with no attempt consumed.

## Blocked by

- `entropy-gate#01` — provides the gate decision record and the individual blocking reasons the correction subject is derived from.
- `execution-core#05` — provides the Correction Budget accounting rule (consumed when `correction.dispatch` is accepted), the `correction.dispatch` and `correction.grantAttempts` operations, and the additive operator grant with no reset.

## Notes

Tests construct the gate subject — including the candidate and current target revision pair — as data, so no slice here is blocked on obtaining it. In production that pair is wired by `git-integration#02`, which owns Merge Candidate preparation and the current target.

The seam with `pbi-execution-loop` is a correction subject handed to `correction.dispatch`: this slice decides that correction is warranted and derives what to correct, while dispatching the builder and running the loop belong to `pbi-execution-loop`.
