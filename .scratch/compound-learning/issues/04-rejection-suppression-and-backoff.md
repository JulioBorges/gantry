# Rejection, observation fingerprint suppression, and per-source backoff

Type: issue
Status: ready-for-agent
Slice: compound-learning#04
Spec: [`../spec.md`](../spec.md) (spec 18, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/compound-learning/spec.md`](../spec.md)

## What to build

The noise-control half of the mechanism, and it is the point rather than decoration: this spec's value is unprovable in advance, so the honest expectation is a small number of genuinely useful rules and a larger number of candidates the operator rejects. A learner that reproposes a rejected lesson after every PBI trains the operator to dismiss everything, including the one useful candidate.

`learning.reject` is operator-only, records the operator's reason alongside the candidate's `observationFingerprint`, and retains the candidate as a decided record. The fingerprint is computed over the normalized observation and the semantic content of the proposed rule rather than its wording, so a rephrased proposal of the same observation hashes the same and is suppressed at production. Suppression is reversible only by an explicit operator reconsideration operation — never by the producer, and never silently.

On top of that, track acceptance rate per source kind. Once a source's rejection rate passes the configured threshold over a configured minimum sample, raise the occurrence count that source needs before it may propose: throttled, not silenced, so a strong recurrence still gets through. The raised count is a configured step with a default rather than an invented curve. Expose the throttle state per source kind through a read operation and a reset operation, and record both the throttle onset and the reset in the audit trail, so the backoff is observable from the persisted records rather than requiring an audit of the producer's behaviour.

## Acceptance criteria

- [ ] A rejected candidate is retained with its reason and fingerprint; a later production run does not produce a candidate with that fingerprint, and neither does a rephrased statement of the same observation and rule.
- [ ] An explicit operator reconsideration clears the suppression and the next run produces the candidate again; no producer path clears it.
- [ ] A source kind rejected past the threshold over the minimum sample is throttled: it still proposes on stronger recurrence and produces nothing below the raised occurrence count.
- [ ] The throttle state per source kind is readable through a read operation and is resettable by the operator; both the throttle onset and the reset appear in the audit trail.
- [ ] `learning.reject` and the reconsideration operation over a non-operator channel are rejected `operator_channel_required`.

## Blocked by

- `compound-learning#01` — the candidate record family, the producer path the suppression filters, and the operator-only operation classification.
- `data-handling#01` — the normalized content hashing rule the `observationFingerprint` is computed with.
- `config-and-snapshot#01` — the configuration schema holding the rejection threshold, the minimum sample, and the raised occurrence count.
- `config-and-snapshot#04` — Execution Rule Snapshot capture, which fixes those learning settings for an execution.
- `execution-core#01` — the audit record that must carry the throttle onset and the reset.
