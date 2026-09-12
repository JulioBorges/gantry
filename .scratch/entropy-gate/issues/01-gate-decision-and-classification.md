# Gate decision record and differential classification

Type: issue
Status: ready-for-agent
Slice: entropy-gate#01
Spec: [`../spec.md`](../spec.md) (spec 13, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/entropy-gate/spec.md`](../spec.md)

## What to build

The tracer bullet through the whole spec. Define the gate decision record family in SQLite — subject (Repository Execution Unit, PBI, target revision, candidate revision, Execution Rule Snapshot identity), per-finding classifications, blocking reasons, and evidence references — register the `gate.evaluate` handler on the shared operation core, and implement matching and classification over target and candidate reports supplied as Comparison Evidence. Everything else in this spec writes into this record.

The differential decision function classifies each matched problem identity individually, and only individually: `introduced` when the identity is present in the candidate and absent from the target; `preexisting` when it is present in both at the same severity and count; `improved` when it is present in the target and absent from the candidate; `aggravated` when it is present in the target but at a lower severity in the candidate, or — for identities matched by count under the no-location fallback — at a lower count in the target than in the candidate. **Aggravated is treated exactly as introduced for blocking purposes**, with the target's severity retained on the classification as the previous severity. Blocking severity thresholds are configured per check purpose and default to `blocker` and `major`; `minor` and `info` findings are recorded and do not block.

The decision carries no score, no total, and no netting anywhere in its shape or its persistence — `blockingReasons` is a list of individual causes, each naming its problem identity, so a decision can never be explained as an average. The decision is surfaced as structured data through the operation core's read projection with each finding's classification and the explicit list of blocking reasons, and every write goes through the redaction sink.

## Acceptance criteria

- [ ] A finding present in the candidate and absent from the target classifies `introduced` and fails the gate at the configured threshold; the same identity present in both classifies `preexisting` and does not.
- [ ] A finding whose severity rose classifies `aggravated` and blocks; a count-matched identity whose count rose also classifies `aggravated`; a finding absent from the candidate classifies `improved` and changes no outcome.
- [ ] One introduced blocker alongside five improvements still fails, and no field in the persisted decision or in the projection holds a score, total, or count that could express netting.
- [ ] A `minor` introduced finding does not block; the outcome names each blocking cause individually with its problem identity.
- [ ] A surviving-mutant finding (`rule: "mutation:<operator>"`) is classified by the same differential path with no branch specific to mutation.
- [ ] The persisted decision records the Execution Rule Snapshot identity, both revisions, and the rule and tool versions that produced each report; one parity test proves a transport delegates the read rather than reimplementing it.

## Blocked by

- `verification-adapters#01` — provides the normalized finding shape, the `StructuredReport` shape carrying subject revision, tool version, rule-set version and declared coverage, the content-anchor problem identity, and the no-location count fallback that `aggravated` keys on.
- `verification-adapters#02` — provides the enclosing-symbol derivation and its no-symbol fallback, which identities are matched under.
- `execution-core#01` — provides the operation core `invoke` seam, the operation catalog entry for `gate.evaluate`, and the record family and persistence conventions.
- `execution-core#05` — provides the gate state machine and the outcome vocabulary the decision reports into.
- `data-handling#01` — provides the redaction sink the decision record and its evidence references are written through.
- `config-and-snapshot#04` — provides the Execution Rule Snapshot identity bound onto every decision.
