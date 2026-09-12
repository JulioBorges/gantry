# Result submission identity, idempotency, and corrections

Type: issue
Status: ready-for-agent
Slice: gtp-protocol#06
Spec: [`../spec.md`](../spec.md) (spec 03, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/gtp-protocol/spec.md`](../spec.md)

## What to build

A submission identity distinct from the task correlation, so a replay is recognizable as a replay and a correction is a new linked attempt rather than an overwrite. The content hash is taken over a deterministically canonicalized payload — sorted keys, no insignificant whitespace, `extensions` included — and the submission identity maps onto the operation core's `requestId` for `pbi.submitResult`, so idempotency is enforced in one place rather than two.

An identical submission returns the original receipt with no repeated transition, counter change, acceptance event, or downstream dispatch. The same identity with different content is rejected. A correction uses a new identity carrying `supersedes`, retains the prior submission, and passes the ownership, role, and transition checks again, so correction is not a path around the rules.

## Acceptance criteria

- [ ] An identical resubmission returns the original receipt, with no second transition, no counter change, and no downstream dispatch.
- [ ] The same `submissionId` with altered content is rejected as a duplicate conflict, and the stored receipt still describes the originally accepted content.
- [ ] A new `submissionId` with `supersedes` set is accepted, and both the superseded and the superseding submission remain readable in history.
- [ ] A corrected submission from a superseded assignment is still rejected on ownership, proving correction is not a path around the rules.
- [ ] Canonicalization is deterministic: two payloads differing only in key order or insignificant whitespace produce the same content hash, and a payload differing only inside `extensions` does not.

## Blocked by

- `gtp-protocol#01` — provides the common envelope layer, the validation order, and the `extensions` lifting rule the content hash covers.
- `execution-core#04` — provides `requestId` idempotency, the receipt shape, and the `duplicate_conflict` rejection.
- `execution-core#03` — provides the PBI Execution Ownership generation and supersession rule a correction must pass again.
- `data-handling#01` — provides the normalized content hashing rule, including line-ending normalization.
