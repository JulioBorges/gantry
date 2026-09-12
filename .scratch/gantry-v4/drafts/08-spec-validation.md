## Spec 08 — spec-validation

This spec owns the gate between a written Living Spec and a sliceable one: `gantry lint-spec`, the normalization of an arbitrary spec document into a canonical content model, the twelve declared Spec Structural Validation rules evaluated against that model, the Requirement Review performed by the Requirement Critic as a GTP role, the conjunction of the two into technical readiness bound to the spec's content hash, Spec Adaptation of a document a team already maintains, and structured authoring. It ends at "ready to slice" and grants no Planning Approval. The risk sits in two places. First, normalization: real documents vary more than any mapping table, so every rule's correctness is downstream of a mapping that will frequently be wrong — mitigated only by making the mapping visible and overridable. Second, `SPEC-CRITERIA-ID`: requiring stable criterion identifiers means editing a document the team already owns, which is the most intrusive thing this spec asks for, and the criterion identity rule it establishes is read by three other specs, so getting it wrong propagates.

### Slices

---

**01 — `gantry lint-spec` tracer with the normalized spec model and content-presence rules**

- **What to build**: Establish the scaffolding this spec runs on and prove it end-to-end with the four simplest rules. A normalizer reads a spec document and produces the normalized spec model — source path, normalized content hash, detected format, a mapping from canonical section to the source heading that satisfied it with `declared | matched | absent` confidence, the identified content blocks, and an `unmapped` list of sections Gantry does not require. A structural rule registry holds rules as declared data with stable identities and a rule set version; evaluation walks the model, never the headings, and emits one structural finding per failing rule carrying rule identity, location, and severity. This slice ships the registry with `SPEC-PROBLEM`, `SPEC-NONGOALS`, `SPEC-SECURITY` and `SPEC-ARCHITECTURE`, a single generic content-signal format, the operation-core handler that persists the validation result, and the `gantry lint-spec` command that renders it.
- **Acceptance criteria**:
  - A fixture document whose non-goals sit under a heading named "Out of Scope" passes `SPEC-NONGOALS`, and the rendered mapping shows which source heading resolved it.
  - A fixture missing non-goals fails `SPEC-NONGOALS` and the finding names a location in the document.
  - Sections Gantry does not require appear in `unmapped` and cause no rule to fail.
  - Validation completes with no harness driver invoked and no network access — asserted by a fake driver that fails the test if called.
  - The persisted validation result records the rule set version and the normalized content hash of the source document.
  - `gantry lint-spec` has one parity test proving it delegates to the operation core rather than reimplementing evaluation.
- **Blocked by**: needs the shared operation core `invoke` seam, the operation catalog and rejection codes, and the persistence record families from `execution-core`; needs the normalized content hashing rule (line endings) and the redaction sink enforcement interface from `data-handling`.
- **Parallelizable with**: none intra-spec (this is the bootstrap); runs concurrently with every other spec's own bootstrap.

---

**02 — Criterion identity and Given-When-Then scenario rules**

- **What to build**: Extend the rule registry with the two rule families that make a spec's behavioral content addressable. Acceptance criteria are extracted into the normalized model as individually identified items with text and location, and criterion identifiers are required rather than generated — a generated identifier renumbers on insertion and silently breaks every downstream reference. `SPEC-CRITERIA-PRESENT` fails when criteria are absent or not individually identifiable; `SPEC-CRITERIA-ID` fails when any criterion lacks a stable identifier. Scenarios are parsed into given, when and then parts; `SPEC-SCENARIOS-COUNT` requires at least three and `SPEC-SCENARIOS-PARSE` requires each one to parse into all three parts. This slice establishes the criterion identity rule that specs 03, 09 and 13 read.
- **Acceptance criteria**:
  - A fixture with unnumbered criteria fails `SPEC-CRITERIA-ID`; a fixture whose criteria carry identifiers passes it and the identifiers appear unchanged in the normalized model.
  - Inserting a new criterion into a fixture leaves every pre-existing criterion's identifier unchanged.
  - A fixture with two scenarios fails `SPEC-SCENARIOS-COUNT`; a fixture with three passes.
  - A fixture containing a scenario with no `then` part fails `SPEC-SCENARIOS-PARSE` with a location pointing at that scenario.
  - Every assertion in this slice's tests is on rule identity, not on message text.
- **Blocked by**: 01 (rule registry, normalized spec model, finding shape).
- **Parallelizable with**: 03, 04, 05.

---

**03 — Declared contract validation per format**

- **What to build**: Formal contracts must be stated rather than implied, and a stated contract must be structurally validated or visibly marked as unvalidated. Declared contracts are extracted into the normalized model with their format and location. `SPEC-CONTRACT-PRESENT` requires at least one. `SPEC-CONTRACT-FORMAT` requires the format to be one Gantry can validate — JSON Schema, TypeScript type declarations, or OpenAPI fragments — and when the operator explicitly declares an unsupported format instead of converting it, the result records that no structural validation was performed rather than passing silently. `SPEC-CONTRACT-VALID` runs the per-format structural validator over each contract in a supported format.
- **Acceptance criteria**:
  - A fixture with a malformed JSON Schema fails `SPEC-CONTRACT-VALID` with a location inside the contract block.
  - A fixture whose only contract is in an unsupported format fails `SPEC-CONTRACT-FORMAT` and does not fail `SPEC-CONTRACT-VALID`.
  - When the operator declares the format of an unsupported contract, the persisted result carries an explicit marker that no structural validation was performed for it.
  - A fixture with no contract at all fails `SPEC-CONTRACT-PRESENT`.
  - Each of the three supported formats has at least one valid and one malformed fixture, and both outcomes are asserted by rule identity.
- **Blocked by**: 01 (rule registry, normalized spec model).
- **Parallelizable with**: 02, 04, 05.

---

**04 — Spec format detection, mapping override, and canonical location**

- **What to build**: Replace the single generic format from slice 01 with a declared set of formats each carrying its own mapping table — the `to-spec` structure this repository uses, the Gantry structure, and the generic content-signal fallback. Detection selects a format, the selection and the resulting mapping are shown to the operator, and the operator can override either, because normalization is a proposal and not a verdict; an override sets mapping confidence to `declared`. This slice also adds `SPEC-LOCATION`, which fails when the document does not sit at the canonical location the repository's Artifact Location Mapping resolves for specs — this spec enforces the mapping and never resolves it.
- **Acceptance criteria**:
  - The same fixture content, presented under `to-spec` headings and under Gantry headings, yields the same canonical content in the normalized model and the same set of passing rules.
  - The rendered result names the detected format and every canonical-section-to-source-heading pair with its confidence.
  - An operator-supplied mapping override changes the resolution, is reflected with `declared` confidence, and re-running validation without the override restores the detected mapping.
  - A spec document placed outside the mapped canonical location fails `SPEC-LOCATION`; the same document at the mapped location passes.
  - A document in no recognized format still normalizes through the generic fallback rather than being rejected.
- **Blocked by**: 01 (normalizer, rule registry); needs the Artifact Location Mapping schema from `repository-readiness`.
- **Parallelizable with**: 02, 03, 05.

---

**05 — Requirement Review and technical readiness**

- **What to build**: The Requirement Critic runs as a GTP role over the normalized spec model, the applicable rules, and the structural findings, and returns semantic findings in declared classes — ambiguity, incoherence, unverifiable, false premise, missing non-goal, scope undefined — each with a `blocker` or `warning` severity, location, statement and rationale, plus a stated coverage of what was reviewed. The critic is mandatory and additive: its result payload has no field capable of clearing a structural finding. Technical readiness is the conjunction — all mandatory structural rules passed, a valid review, zero blocking findings — persisted against the spec's normalized content hash and the Execution Rule Snapshot, and invalidated by any edit to the document. Readiness authorizes slicing and nothing else.

  ```
  ready = allMandatoryStructuralRulesPassed
        && reviewValid            // envelope validates, coverage stated, status complete
        && blockingFindings === 0
  ```
- **Acceptance criteria**:
  - All structural rules passing plus a clean valid review yields `ready: true`; the same with one blocking finding yields `ready: false`; the same with warnings only yields `ready: true`.
  - An absent, malformed, or failed critic result leaves `ready: false` and records the failure — there is no static-only fallback that reads as readiness.
  - A critic infrastructure failure consumes the Infrastructure Retry allowance and consumes no Correction Attempt; a Protocol Failure is recorded as such and not reclassified as infrastructure.
  - Editing the spec document after readiness invalidates both the structural result and the review, and a subsequent readiness query reports not ready.
  - The readiness record names the rule set version, the review's submission identity, and the content hash that produced it, and can be reconstructed from them.
  - A readiness record does not authorize builder dispatch and does not satisfy Planning Approval — asserted by an operation that rejects on each.
- **Blocked by**: 01 (structural result to conjoin); needs the role task and result envelope contract, boundary validation, Result Submission identity and receipts, status semantics, and Protocol Failure handling from `gtp-protocol`; needs Execution Rule Snapshot binding from `config-and-snapshot`; needs Infrastructure Retry accounting from `execution-core`; needs the redaction sink enforcement interface from `data-handling` for persisted critic output.
- **Parallelizable with**: 02, 03, 04.

---

**06 — Spec Adaptation by proposed complements**

- **What to build**: For a document a team already maintains, each unsatisfied rule becomes a proposed complement rather than a rewrite. A complement names the canonical section (or `criterion_identifiers`) it supplies, the rule it satisfies, the insertion location in the original document, the proposed content, and the `styleBasis` — which existing part of the document the content was patterned on, so the insertion reads like the team's own prose rather than an imported template voice. Applying a complement edits the original document in place at its canonical location. No parallel Gantry copy is created, no heading is renamed to match a template, and applying a complement establishes no readiness and grants no approval.
- **Acceptance criteria**:
  - Applying complements to a fixture inserts the proposed content and leaves every other byte of the document unchanged.
  - No file is created anywhere outside the original document's path during adaptation.
  - Every proposed complement records a `styleBasis` naming an existing part of the source document.
  - Applying the `criterion_identifiers` complement makes `SPEC-CRITERIA-ID` pass on re-validation, and a later unrelated edit to the document leaves those identifiers unchanged.
  - Applying complements does not set readiness; readiness only appears after validation and review run again.
  - No heading present in the source document before adaptation is renamed or removed by it.
- **Blocked by**: 01 (findings identify which rule is unsatisfied), 02 (the `criterion_identifiers` complement).
- **Parallelizable with**: 03, 04, 05, 07.

---

**07 — Structured spec authoring**

- **What to build**: Authoring produces a new spec in a structure that passes Spec Structural Validation, so that authoring and validation agree by construction. When the repository has a detected spec format, the authored document uses that format; otherwise it uses the `to-spec` structure. The authored document is written to the canonical location the Artifact Location Mapping resolves; a document written elsewhere fails `SPEC-LOCATION` rather than being silently accepted. The authoring templates are structured content, not a mandatory rewrite of anything existing — this slice adds a way to create a spec, never a requirement to convert one.
- **Acceptance criteria**:
  - In a temporary repository with a detected `to-spec` format, an authored spec is produced in that format and validates with all mandatory rules passing except those requiring operator-supplied content.
  - In a repository with a different detected format, the authored spec uses that format rather than the default.
  - The authored document lands at the mapped canonical location; an authored document directed elsewhere fails `SPEC-LOCATION`.
  - Authoring produces at least three parseable Given-When-Then scenario slots and criterion identifier slots, so a completed authored spec can reach all-rules-passing without adaptation.
  - Authoring establishes no readiness and no approval.
- **Blocked by**: 04 (format detection, canonical location, `SPEC-LOCATION`).
- **Parallelizable with**: 02, 03, 05, 06.

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Shared operation core `invoke` seam, operation catalog, rejection codes, persistence record families | `execution-core` | 01 (all slices inherit) |
| Infrastructure Retry allowance accounting, distinct from Correction Attempt | `execution-core` | 05 |
| Normalized content hashing (line-ending normalization) | `data-handling` | 01, 05 |
| Redaction sink enforcement interface | `data-handling` | 01, 05 |
| Role task and result envelope contract, boundary validation, forward compatibility, `extensions` lifting | `gtp-protocol` | 05 |
| Result Submission identity and receipts, status semantics, Protocol Failure | `gtp-protocol` | 05 |
| Execution Rule Snapshot binding and snapshot identity | `config-and-snapshot` | 05 |
| Artifact Location Mapping schema | `repository-readiness` | 04, 07 |
| Skill packaging and installation mechanism (for the conversational authoring surface) | `machine-setup` | 07 (packaging only; the operation is ours) |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| **Criterion identity rule — required, never generated, stable** | 02 | `gtp-protocol` (03), `slicing-and-approval` (09), `entropy-gate` (13) |
| Normalized spec model (canonical sections, mapping with confidence, extracted criteria/scenarios/contracts, `unmapped`) | 01 | `slicing-and-approval` (09), host harness surfaces |
| Structural rule identity set and rule set version | 01 (registry), 02/03/04 (rules) | `slicing-and-approval` (09), which mirrors the pattern for `lint-pbi` |
| Technical readiness record — the ready-to-slice gate, content-hash bound, authorizing slicing only | 05 | `slicing-and-approval` (09) |
| Requirement Critic result payload (`RequirementReview`: finding classes, severities, coverage) | 05 | `gtp-protocol` (03) role registry |
| Spec complement shape (`canonical`, `reason`, `proposedInsertion`, `styleBasis`) | 06 | `slicing-and-approval` (09) if it adopts the same in-place complement pattern for PBIs |

### Risks / judgement calls

**Slice 01 carries a generic format and slice 04 adds format plurality.** This is the one ordering I am least certain about. The alternative — full format detection and the mapping table in slice 01 — makes the bootstrap slice large enough that nothing else can start until it lands, and it front-loads the part of the spec most likely to be wrong. Splitting it means slice 01's `confidence` field only ever holds `matched` or `absent`, and the `declared` path arrives in 04. If the operator would rather settle the mapping table once, merge 04 into 01 and accept a longer critical path.

**Structural findings versus spec 12's normalized finding shape.** Spec 08 says its rules produce "findings in the same structured shape the rest of the system uses", but the normalized finding shape is owned by `verification-adapters` (spec 12), which is a wave later. I deliberately did not declare a cross-spec blocker: spec 08's findings are over prose documents and need rule identity, location and severity but not content anchors or tree-sitter symbol derivation. Slice 01 defines a structural finding shape whose overlapping fields should be named identically to spec 12's. If the operator wants one shape rather than two compatible ones, spec 12's finding identity work has to be pulled forward, and that is a bigger reordering than it looks.

**I merged criteria and scenarios into slice 02, and merged Requirement Review with readiness into slice 05.** Criteria and scenarios are both extraction-plus-two-rules and each alone was too thin to be a PBI. Requirement Review alone would deliver a critic whose result nothing consumes; readiness alone would have nothing to conjoin. Both merges trade a slightly wider initial context for a genuinely demoable outcome. Slice 02 is the one I was most tempted to split, because the criterion identity rule is a published contract three other specs read and it deserves visibility — if the operator wants it to have its own ticket for that reason alone, splitting scenarios out is clean and adds no blocking.

**Slice 05 has the widest cross-spec dependency set** — four other specs. It cannot start until `gtp-protocol` has settled its envelope and submission identity. If that lands late, slices 02, 03, 04, 06 and 07 all remain workable, so the critical path survives, but technical readiness is the thing spec 09 waits on and it is the last piece of this spec to become available.

**`SPEC-CRITERIA-ID` on an existing document is the most intrusive requirement here,** and the spec says so. Slice 02 makes it fail and slice 06 makes it fixable, so an operator who runs slice 02's work before slice 06 exists sees a failure they cannot resolve without hand-editing. That is acceptable ordering for parallel agents but worth knowing before anyone demos slice 02 in isolation.
