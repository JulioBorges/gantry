# Evidence validity: completeness, operator classification, and report reuse

Type: issue
Status: ready-for-agent
Slice: verification-adapters#03
Spec: [`../spec.md`](../spec.md) (spec 12, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/verification-adapters/spec.md`](../spec.md)

## What to build

The consumption-time verdict on whether a stored report may serve as Comparison Evidence. A finding missing `rule`, `path`, `severity`, or `problemIdentity`, or a report missing `subjectRevision`, `toolVersion`, `ruleSetVersion`, or `declaredCoverage`, is invalid evidence: it leaves the dependent gate unapproved and is never read as zero findings.

The single escape is a `FindingClassification` — operator-channel only, scoped to one problem identity in one report version, recorded as additive evidence beside the tool's output and never a rewrite of it, and auto-invalidated by a revision change, a rule version change, or a change to the finding. There is no global waiver and no rule-level suppression.

Report reuse is decided at the point of consumption rather than trusted from a cache key: revision, rule set version, tool version, grammar version, and command reference must all match. `pass_fail` outcomes are accepted as mandatory checks while being structurally unable to feed the comparison. One CLI parity test covers the classification command.

## Acceptance criteria

- [ ] A finding missing `problemIdentity`, and separately a report missing `toolVersion`, `ruleSetVersion`, or `declaredCoverage`, each leave the gate unapproved; no path infers zero findings from either.
- [ ] A classification permits exactly one finding in one report version; the same problem identity in a new report version is blocked again, and the recorded evidence still shows the tool's original output.
- [ ] Each of a revision change, a rule version change, and a change to the finding invalidates the classification, with the reason recorded.
- [ ] A classification from a non-operator channel is rejected as `operator_channel_required`; a catalog-shape test proves no operation exists that waives a rule globally or suppresses by rule.
- [ ] A report is reused only when revision, rule set version, tool version, grammar version, and command all match; any difference forces a fresh run.
- [ ] A `pass_fail` outcome satisfies a mandatory check and is rejected by the comparison input, and `declaredCoverage` accompanies every surfaced report.

## Blocked by

- `verification-adapters#01` — the `StructuredReport` binding and finding fields whose absence this slice judges.
- `execution-core#02` — actor provenance and the operator-only channel with its `operator_channel_required` rejection.
- `execution-core#05` — provides the fail-closed rule and the required-field list that completeness is judged against.

## Notes

- 2026-09-12 — `execution-core#05` no longer waits on this slice: it declares the interface it needs and tests against a fake; this slice implements or produces to that declared interface (see `execution-core#05` notes and `slice-index.md`, *Dependency graph repair*).
