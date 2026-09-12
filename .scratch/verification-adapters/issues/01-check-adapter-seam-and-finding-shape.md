# Check adapter seam and normalized finding shape

Type: issue
Status: ready-for-agent
Slice: verification-adapters#01
Spec: [`../spec.md`](../spec.md) (spec 12, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/verification-adapters/spec.md`](../spec.md)

## What to build

The `CheckAdapter` interface, the `CheckRun` / `CheckOutcome` / `StructuredReport` / `NormalizedFinding` types, and the operation-core operation that runs an approved verification command against a stated revision and persists its report bound to revision, tool version, rule set version, command reference, and declared coverage. `CheckOutcome` carries all three shapes — `report`, `pass_fail`, and `adapter_failure` — from the start, even though only the report shape is exercised here.

The finding identity tuple is the contract this spec exists to publish: `rule` + `path` + `symbol` + `contentAnchor`, with the message excluded from identity entirely. This slice lands it in its content-anchor form — `rule` + normalized `path` + `contentAnchor` hashed over the normalized reported line plus a fixed number of neighbouring lines — together with the no-location fallback to `rule` + `path` matched by count per identity. The derivation actually used is recorded on every finding. Line and column are persisted for display and are structurally excluded from identity. Identity is deliberately narrower than the final contract until `verification-adapters#02` adds the Gantry-derived enclosing symbol; `entropy-gate` and `baseline-transitions` are written against the final tuple and therefore effectively wait for `#02`.

A report produced by an adapter serving the `mandatory_test` purpose additionally carries the collected mandatory-test identities including each one's skip status. A skipped test is not a finding, so the `findings` collection alone cannot express it, and `entropy-gate#04`'s verification integrity comparison cannot be built without this field. Ship the Gitleaks adapter as the reference parser — it is language-agnostic, flat, and needs no package-manager resolution — so the slice is demonstrable end to end from recorded tool output to a persisted, retrievable report.

The adapter contract also includes an optional rule-mapping declaration: an adapter may report rule renames it knows about between two tool versions, and an adapter that knows none declares none. It stays optional because most adapters cannot maintain a rename table, and the per-rule count fallback already covers that case. `baseline-transitions#03` consumes the declaration, records `source: "adapter"` on the mappings it takes from here, and falls back to operator-supplied mappings plus the count fallback when an adapter supplies nothing.

## Acceptance criteria

- [ ] Invoking the check-run operation with an approved Gitleaks command and recorded output persists a report and returns findings carrying rule, path, severity, `problemIdentity`, and the recorded derivation.
- [ ] Parsing the same recorded output twice yields identical problem identities; a report differing only in reported line and column yields identical identities.
- [ ] Two occurrences of the same rule in the same file receive different identities via their content anchors.
- [ ] A tool reporting no location at all yields `rule` + `path` identity with the count-fallback derivation recorded; target two / candidate three resolves to one introduced finding, target two / candidate one to a recorded improvement crediting nothing.
- [ ] A report from a `mandatory_test` adapter carries the collected mandatory-test identities with each one's skip status, and a skipped test appears there rather than as a finding.
- [ ] An adapter that knows a rule rename between two tool versions reports it as a rule mapping carrying both rule identities and the version pair; an adapter with no known renames reports an empty mapping set rather than an error, and neither case affects the identity tuple of any finding.
- [ ] The Gitleaks adapter passes a conformance test against captured fixture output with no live tool invocation.
- [ ] Reports and findings are written through the redaction sink; no writer bypasses it.

## Blocked by

- `execution-core#01` — operation catalog registration, the in-process invoke seam, record families, and persistence conventions.
- `data-handling#01` — normalized content hashing over line endings, and the redaction sink enforcement interface.
- `repository-readiness#04` — the approved verification command reference and its declared coverage.
- `execution-core#05` — provides the `CheckAdapter` seam interface, the `NormalizedFinding` shape and the fake adapter this slice implements for real tools.

## Notes

- 2026-09-12 — `execution-core#05` no longer waits on this slice: it declares the interface it needs and tests against a fake; this slice implements or produces to that declared interface (see `execution-core#05` notes and `slice-index.md`, *Dependency graph repair*).

- 2026-09-12 — `gtp-protocol#03` no longer waits on this slice: it declares the interface it needs and tests against a fake; this slice implements or produces to that declared interface (see `gtp-protocol#03` notes and `slice-index.md`, *Dependency graph repair*).

- 2026-09-12 — `gtp-protocol#05` no longer waits on this slice: it declares the interface it needs and tests against a fake; this slice implements or produces to that declared interface (see `gtp-protocol#05` notes and `slice-index.md`, *Dependency graph repair*).
