# Withheld output and blocked-for-review

Type: issue
Status: ready-for-agent
Slice: data-handling#03
Spec: [`../spec.md`](../spec.md) (spec 04, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/data-handling/spec.md`](../spec.md)

## What to build

Confidence classification by declared rule rather than inference, and the propagation that makes withholding visible. Output becomes `uncertain` when a detector errors, when it exceeds the configured inspection bound, when it is not decodable text, or when a detector reports a partial match it cannot resolve.

An `uncertain` outcome stores no content at all, marks the associated operation or check blocked for review with its reason, surfaces that in the state projection, and prevents the gate that depended on it from passing. A redaction failure is never reported as a passing check — that is the invariant this slice exists to prove.

The failing-closed friction here is real and deliberate: an oversized build log or a tool emitting binary output will withhold content and block a check for review. The two dials that control it — the inspection bound and the undecodable-output treatment — are configurable by design, so a repository can widen them deliberately rather than having the pipeline guess.

## Acceptance criteria

- [ ] A scripted detector error, an undecodable byte sequence, and an output exceeding the inspection bound each produce `uncertain`, persist no content, and record a reason.
- [ ] The affected operation or check is marked blocked for review and the state projection exposes both the withheld condition and its reason.
- [ ] An Entropy Gate whose Comparison Evidence was withheld as `uncertain` does not reach a passed state; it remains blocked on incomplete evidence rather than passing or failing silently.
- [ ] The inspection bound and the undecodable-output treatment are read from configuration, so a repository can widen them deliberately.
- [ ] A withheld output's metadata still records the ruleset version and any detector hits observed before the uncertainty arose.

## Blocked by

- `data-handling#01` — the pipeline and the `uncertain` variant of `RedactionOutcome` this slice classifies into.
- `execution-core#01` — the operation core seam, the atomic transition primitive, and the state projection that surfaces the blocked-for-review condition.
- `execution-core#05` — the gate state machine, including `pending` and the `blocked_incomplete_evidence` fail-closed state a withheld evidence outcome lands in.
- `config-and-snapshot#01` — the data-handling configuration section carrying the inspection bound and the undecodable-output treatment keys.
