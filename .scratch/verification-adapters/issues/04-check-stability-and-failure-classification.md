# Check stability and adapter failure classification

Type: issue
Status: ready-for-agent
Slice: verification-adapters#04
Spec: [`../spec.md`](../spec.md) (spec 12, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/verification-adapters/spec.md`](../spec.md)

## What to build

The Check Stability declaration — environment, inputs, isolation requirement, and criterion — and its evaluation, so that a single passing run counts only when the declared criterion allows it. Reruns follow the check's approved policy and stop at its bound rather than looping to green. Inconsistent outcomes are appended to observed instability, surface as a check problem, and leave the dependent gate unapproved until the check is reviewed.

Adapter failures are classified `infrastructure` or `permanent` in the same slice and wired to Infrastructure Retry accounting, because the whole point is that instability and infrastructure failure are different things: instability spends no retry allowance, an infrastructure failure spends one, and a permanent failure blocks without spending any. Stability declarations and rerun bounds are read from the Execution Rule Snapshot rather than from live configuration.

## Acceptance criteria

- [ ] A check declaring `consecutive: 2` is not satisfied by one passing run; `quorum` is evaluated as declared; `single_run` is accepted.
- [ ] Inconsistent outcomes are appended as observed instability, surface as a check problem, and leave the gate unapproved.
- [ ] The rerun loop terminates at the approved bound and reports; no configuration permits unbounded reruns.
- [ ] Instability consumes no infrastructure retry allowance; an adapter `infrastructure` failure consumes one; a `permanent` failure blocks without consuming.
- [ ] A check that runs and reports findings — however many, however severe — is treated as working, not as a broken setup.
- [ ] Stability declarations and rerun bounds are read from the execution rule snapshot, not from live configuration.

## Blocked by

- `verification-adapters#01` — the `CheckOutcome` union carrying `adapter_failure` and the check-run operation whose repetition is bounded here.
- `execution-core#06` — Infrastructure Retry allowance accounting.
- `config-and-snapshot#04` — Execution Rule Snapshot binding and the limit values for rerun bounds and stability defaults.
