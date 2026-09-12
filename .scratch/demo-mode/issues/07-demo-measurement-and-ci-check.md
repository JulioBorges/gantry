# Demo measurement and the pipeline regression check

Type: issue
Status: ready-for-agent
Slice: demo-mode#07
Spec: [`../spec.md`](../spec.md) (spec 07, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/demo-mode/spec.md`](../spec.md)

## What to build

Record the demo's own wall-clock duration from command invocation to a visible pipeline, persist it as a demo measurement, and report it through a channel that names it as such — explicitly distinct from any real-repository time-to-first-value target, which the PRD makes conditional on Repository Readiness and operator approvals. A fast demo is never evidence about a real pipeline, and no code path may present it as one. Expose the same measurement surface the dashboard uses for SSE latency on demo traffic, carrying the same demo-measurement label.

Then wire the scripted walkthrough into CI as a full-pipeline integration test with a duration assertion. The rationale for doing this now rather than near release is the whole reason the measurement is a slice at all: the under-two-minute budget degrades **monotonically** as later waves add stages to the pipeline — fixture creation, database provisioning, three PBIs through the full state machine, and Gantry's own re-execution of mandatory tests on each delivered revision all grow. Measured once near release, the overrun is discovered when it is unattributable and expensive; measured from the first commit, each wave's contribution is visible in the commit that adds it. That is why the budget is asserted in CI from day one.

The measurement-recording half depends only on `demo-mode#02` and can be built alongside `#05` and `#06`; only the CI wiring waits on the walkthrough being complete.

## Acceptance criteria

- [ ] The run's duration is persisted and projected labeled as a demo measurement; no code path presents it as a real-repository target.
- [ ] CI runs the scripted walkthrough as a required check and fails when its duration exceeds the configured demo budget.
- [ ] The check fails loudly with a named cause when any PBI's state sequence diverges from the scripted expectation.
- [ ] Two consecutive CI runs of the walkthrough produce identical state sequences, proving determinism.
- [ ] The SSE latency measurement surface is populated from demo traffic and carries the demo-measurement label.

## Blocked by

- `demo-mode#05` — the clean-delivery, Protocol Failure, and dependency-wait state sequences the CI check asserts on.
- `demo-mode#06` — the Correction Attempt and entropy-block state sequences the CI check asserts on.
- `release-engineering#01` — the CI required-check definition and the release pipeline the walkthrough is registered into.
- `dashboard#04` — the SSE projection channel, needed for the latency surface only; the duration measurement does not wait on it.
