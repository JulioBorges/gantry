# Pull Request preparation, Pull Request Observation, and the local-plus-provider conjunction

Type: issue
Status: ready-for-agent
Slice: git-integration#07
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

Pull Request creation and update under plan approval, which authorizes this class of mutation and only this class, then authenticated polling with a configurable and recorded interval, backoff and observation budget. Each observation is reconciled against the Pull Request identity: a `headRevision` no longer equal to the candidate means the candidate changed and invalidates authorization, a `baseRevision` no longer equal to the target means the target advanced and does the same, and changed protection reruns the protection comparison.

Merge requires both the applicable local gates and the provider's required checks to pass for the relevant revisions — neither substitutes for the other, and a conflict between them blocks. Provider mutations persist intent before the request and resolve an `unknown` outcome against authoritative provider state, never by speculative repetition. This is the provider-side resolver of the same Operation Reconciliation contract that `git-integration#03` implements Git-side; the two consult different authoritative sources but must not diverge in shape. Webhooks and hosted callbacks are deferred; silence is never success.

Note on size: this is the largest slice in the project and is deliberately kept whole, because the invalidation checks are the point of observing and a preparation-only slice cannot demonstrate that a Pull Request ever merges. If it has to be split during execution, the named cut line is preparation plus the create and update mutations in one part, and polling plus the conjunction plus merge in the other, with the second blocked on the first.

## Acceptance criteria

- [ ] Plan approval alone authorizes Pull Request creation and update, and a test confirms it does not authorize a local merge.
- [ ] An observation whose `headRevision` differs from the candidate invalidates authorization; one whose `baseRevision` differs from the target does the same; both return the gate to `pending`.
- [ ] A `pending` required check, a missing check, a poll timeout, and an unavailable provider each fail to authorize the merge, in four separate assertions.
- [ ] Reaching the observation budget leaves the execution waiting for resumption — not failed, not approved — and the interval, backoff and budget used are readable from the recorded observations.
- [ ] Passing local gates with a failing provider check does not merge; the reverse does not merge; a direct conflict between the two blocks with a typed code.
- [ ] A Pull Request creation or merge whose response is lost produces an `unknown` operation that blocks, and reconciliation against scripted provider state records a confirmed completion without creating a duplicate Pull Request or a second merge.

## Blocked by

- `git-integration#02` — provides the Merge Candidate and the candidate/target revision pair each observation is reconciled against.
- `git-integration#05` — provides the provider interface, Provider Identity approval, and the scripted fake used to drive observations and lost responses.
- `execution-core#06` — provides the operation intent record, the receipt, the unknown-outcome blocking rule and the Operation Reconciliation contract this slice implements provider-side.
- `entropy-gate#01` — provides the gate decision the local half of the conjunction reads.
