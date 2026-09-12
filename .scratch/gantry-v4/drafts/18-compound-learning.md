## Spec 18 — compound-learning

This spec owns `gantry learn-from-pbi`: reading the *retained* execution evidence for a PBI — gate findings, Correction Attempts, Protocol Failures, handoff memos, integrity findings, and the audit transition log — and turning recurring observations into **learning candidates** that an operator approves one at a time, after which the approved rule is written inside the marked `AGENTS.md` section and nowhere else. It also owns the two self-limiting mechanisms: per-source rejection backoff and a section size limit with mandatory consolidation. The risk is not correctness, it is value and volume. Every mechanical part of this spec is cheap and testable; what is unproven is whether candidates drawn from structured evidence are worth an operator's attention at all. Two secondary risks are real and design-visible: (a) a learner that could target `CONSTITUTION.md` or an ADR would be promoting its own output's authority past Governance Precedence, so target routing is a structural constraint rather than a policy; and (b) applied learnings share a file region with `gantry init`'s own writes, so the marked section must be a render of persisted records rather than accumulated free text, or re-running init silently erases approved learnings.

### Slices

---

- **01 — Learning candidate from Entropy Gate findings, approved into the marked section**

- **What to build**: The spine, end to end. Add the learning record families (candidates, occurrences, applied learnings) to the unit-scoped store; register `learning.produce`, `learning.approve` and `learning.list` in the shared operation core's catalog; wire `gantry learn-from-pbi` and an approve command onto them. Production reads the retained gate-finding records for a named PBI, groups them into one candidate per distinct observation with its occurrence list, and enforces the two production validations: every occurrence must carry an evidence reference that resolves under the replayable-reference rules at production time (an occurrence with an unresolvable reference is dropped, and a candidate left with none is not produced), and `proposedRule` must be an instruction rather than a restatement of the observation. `learning.approve` is operator-only and renders the approved rule — with its originating PBIs, evidence references, and approval timestamp — inside the `<!-- gantry:begin -->` / `<!-- gantry:end -->` markers. The section is rendered from the persisted record set, never appended to in place, so init and learning application are the same operation over a shared source of truth. All candidate text passes the redaction pipeline before persistence.
- **Acceptance criteria**:
  - `gantry learn-from-pbi` against a seeded PBI with repeated gate findings produces at least one candidate carrying a non-empty occurrence list, each occurrence with a resolvable evidence reference.
  - A candidate whose only evidence reference no longer resolves is not produced; a candidate whose `proposedRule` restates its observation is refused as invalid at production.
  - An approved candidate appears between the markers; every byte of `AGENTS.md` outside the markers is identical before and after, and the applied record names its originating PBIs, evidence references and approval timestamp.
  - `learning.approve` over the MCP channel is rejected `operator_channel_required`, and an agent result asserting approval creates no applied-learning record.
  - Running production changes no execution state, consumes no Correction Budget or Infrastructure Retry allowance, and triggers no cleanup — asserted against the state projection and an instrumented core.
  - One CLI parity test proves delegation to `invoke`; candidate text with a secret-shaped value is redacted in the persisted record.
- **Blocked by**: `invoke` request/outcome shape and catalog registration + operator-channel derivation (**execution-core**); record-family and store conventions (**execution-core**); redaction sink enforcement interface and replayable-reference resolution (**data-handling**); normalized finding record and gate evidence record (**verification-adapters** for the shape, **entropy-gate** for the gate decision record); marked `AGENTS.md` section and its in-place replacement rule (**repository-readiness**).
- **Parallelizable with**: None — it is the bootstrap.

---

- **02 — Candidates from Correction Attempts, Protocol Failures, and state transitions**

- **What to build**: Extend candidate production across three more retained families that all live close to the core. Correction Attempt records yield observations about slices that consumed repeated attempts against the same rule; Protocol Failure conditions yield observations about a recurring contract mistake on a role; the audit transition log yields observations about a recurring state path (for example, repeatedly entering a blocked condition for the same reason). Each source tags its candidates with its `sourceKinds` entry so later backoff can be attributed. Each remains subject to the same evidence-resolvability and instruction validations from slice 01.
- **Acceptance criteria**:
  - Seeding a PBI that consumed four Correction Attempts against one rule produces a candidate whose source kind is the correction attempt and whose occurrences cite the correction records.
  - Seeding two Protocol Failures of the same class on one role produces a single candidate citing both, not two candidates.
  - A recurring state-transition path produces a candidate citing audit records; a single non-recurring transition does not.
  - Each produced candidate's `sourceKinds` matches the family it was read from, and candidates from these sources honour the same unresolvable-reference and restatement refusals proven in slice 01.
- **Blocked by**: 01. Cross-spec: Correction Attempt accounting records (**execution-core**, with the correction loop's records from **entropy-gate**); Protocol Failure as a persistent condition on an assignment (**gtp-protocol**); audit transition log fields (**execution-core**).
- **Parallelizable with**: 03, 04, 05, 06.

---

- **03 — Candidates from handoff patterns and integrity findings**

- **What to build**: Extend production across the two families owned further out in the pipeline. Retained, numbered handoff memos yield observations about slices that always need a handoff — the useful instruction there is about decomposition, so the candidate's proposed rule targets slicing guidance rather than implementation. Integrity findings yield observations about attempts to weaken verification, which are the highest-signal source in the spec and should propose the narrowest rules. Both use the slice 01 producer contract unchanged.
- **Acceptance criteria**:
  - Three PBIs each requiring a handoff at a comparable point produce one candidate with three occurrences citing the memo records and an occurrence count of three.
  - An integrity finding recurring across two PBIs produces a candidate citing both integrity finding records.
  - A single handoff on a single PBI produces no candidate under the configured minimum recurrence.
  - Memo-sourced candidates cite the memo record reference and never quote conversation history, tool transcript, or build log content, because none is retained.
- **Blocked by**: 01. Cross-spec: retained handoff memo record and handoff numbering (**pbi-execution-loop**); integrity finding record (**entropy-gate**).
- **Parallelizable with**: 02, 04, 05, 06.

---

- **04 — Rejection, observation fingerprint suppression, and per-source backoff**

- **What to build**: The noise-control half of the mechanism. `learning.reject` is operator-only, records the operator's reason alongside the candidate's `observationFingerprint`, and retains the candidate as a decided record. The fingerprint is computed over the normalized observation and the semantic content of the proposed rule rather than its wording, so a rephrased proposal of the same observation hashes the same and is suppressed at production. Suppression is reversible only by an explicit operator reconsideration operation, never by the producer. On top of that, track acceptance rate per source kind: once a source's rejection rate passes the configured threshold over a configured minimum sample, raise the occurrence count that source needs before it may propose — throttled, not silenced — and expose the throttle state and a reset operation.
- **Acceptance criteria**:
  - A rejected candidate is retained with its reason and fingerprint; a later production run does not produce a candidate with that fingerprint, and neither does a rephrased statement of the same observation and rule.
  - An explicit operator reconsideration clears the suppression and the next run produces the candidate again; no producer path clears it.
  - A source kind rejected past the threshold over the minimum sample is throttled: it still proposes on stronger recurrence and produces nothing below the raised occurrence count.
  - The throttle state per source kind is readable through a read operation and is resettable by the operator; both the throttle onset and the reset appear in the audit trail.
  - `learning.reject` and the reconsideration operation over a non-operator channel are rejected `operator_channel_required`.
- **Blocked by**: 01. Cross-spec: normalized content hashing rule (**data-handling**); configuration schema and Execution Rule Snapshot capture for the rejection threshold and minimum sample (**config-and-snapshot**).
- **Parallelizable with**: 02, 03, 05, 06.

---

- **05 — Applied-section stewardship: grouping, removal, size limit, and consolidation**

- **What to build**: Keep the marked section usable and keep the spec's honesty signal observable. Applied learnings render grouped by theme with compact provenance. An operator can remove a previously applied learning; the removal is recorded and the section re-renders without it. The section carries a configured maximum; on reaching it, `learning.approve` is refused until the operator consolidates — shown the existing learnings grouped, then merging or removing — after which approval proceeds. Critically, the configured limit value and **every change to it** are recorded in the audit trail and surfaced in a read operation alongside the count of consolidations performed, so the question the specification says to watch — whether the limit gets raised instead of consolidation happening — is answerable from the record rather than from memory.
- **Acceptance criteria**:
  - Applied learnings render grouped, each with its provenance; content outside the markers stays byte-identical across every render.
  - Removing an applied learning re-renders the section without it and records the removal with actor provenance and timestamp.
  - With the section at its configured maximum, `learning.approve` is refused with a consolidation-required condition; after a consolidation that reduces the section below the maximum, the same approval succeeds.
  - A change to the configured section maximum is recorded in the audit trail with its old and new value and the actor who made it.
  - A read operation reports the current maximum, the current section size, the number of consolidations performed, and the history of limit changes.
  - Consolidation and removal are operator-only; both are rejected `operator_channel_required` over the MCP channel.
- **Blocked by**: 01. Cross-spec: marked-section ownership and the Artifact Location Mapping entry for agent instructions (**repository-readiness**); configuration schema and snapshot capture for the section maximum (**config-and-snapshot**).
- **Parallelizable with**: 02, 03, 04, 06.

---

- **06 — Target routing by Governance Precedence and conversion to a Governance Baseline Transition**

- **What to build**: Make the precedence constraint structural. A candidate's target determines its path and the producer cannot choose freely: an `agents_section` target is an operational proposal handled by slices 01 and 05; a `constitution` or `adr` target has **no direct application path at all** and is instead converted into a governance change declaration that enters the Governance Baseline Transition path, with its originating occurrences and evidence references carried across as the transition's justification. `learning.approve` against a candidate with either higher-precedence target is refused with a routing condition rather than applying anything, so no sequence of learning operations can write to a level 3 or level 4 document.
- **Acceptance criteria**:
  - A candidate targeting `CONSTITUTION.md` produces a governance change declaration and no applied-learning record; the same holds for a candidate targeting an ADR path.
  - `learning.approve` against a `constitution` or `adr` candidate is refused, and the marked section is byte-identical afterwards.
  - The produced declaration carries the candidate's occurrences and evidence references, so the transition's justification is traceable to the same evidence the candidate cited.
  - No operation in the learning catalog can write to any document above precedence level 6, demonstrated by attempting each learning operation against a higher-precedence target.
  - The source level assigned to an applied learning is level 6, and a resolution that pits it against a higher-level assertion records the applied learning as overridden.
- **Blocked by**: 01. Cross-spec: `SourceLevel` definition and precedence resolution (**config-and-snapshot**); Governance Baseline Transition declaration intake — how a proposed governance change is declared and reaches a manifest (**baseline-transitions**).
- **Parallelizable with**: 02, 03, 04, 05.

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Operation catalog registration and `invoke` request/outcome shape (incl. `Rejection` codes) | `execution-core` | 01, 04, 05, 06 |
| Operator channel derivation and `operator_channel_required` rule | `execution-core` | 01, 04, 05, 06 |
| Record-family conventions and unit-scoped store schema versioning | `execution-core` | 01 |
| Correction Attempt accounting records | `execution-core` (with `entropy-gate`'s correction loop records) | 02 |
| Audit transition log fields (actor, channel, rule version, references) | `execution-core` | 02, 04, 05 |
| Redaction sink enforcement interface | `data-handling` | 01 (and therefore every later slice's writes) |
| Replayable reference resolution and the missing-source condition | `data-handling` | 01 |
| Normalized content hashing rule | `data-handling` | 04 |
| Normalized finding shape (rule, path, symbol, content anchor, problem identity) | `verification-adapters` | 01 |
| Gate decision and finding evidence records | `entropy-gate` | 01 |
| Integrity finding record | `entropy-gate` | 03 |
| Protocol Failure as a persistent condition on an assignment | `gtp-protocol` | 02 |
| Retained handoff memo record and handoff numbering | `pbi-execution-loop` | 03 |
| Marked `AGENTS.md` section (`gantry:begin` / `gantry:end`) and its in-place replacement rule | `repository-readiness` | 01, 05 |
| Artifact Location Mapping — agent-instructions and learnings categories | `repository-readiness` | 01, 05 |
| `SourceLevel` definition and precedence resolution | `config-and-snapshot` | 06 |
| Configuration schema and Execution Rule Snapshot capture for learning settings | `config-and-snapshot` | 04 (threshold, minimum sample), 05 (section maximum) |
| Governance Baseline Transition declaration intake | `baseline-transitions` | 06 |
| MCP schema derivation from operation schemas | `mcp-server` | 01 (parity test only) |

Retained record families read, stated precisely: gate findings and their comparison evidence (`verification-adapters` shape, `entropy-gate` decision), integrity findings (`entropy-gate`), Correction Attempt accounting (`execution-core` + `entropy-gate`), Protocol Failure conditions (`gtp-protocol`), handoff memos (`pbi-execution-loop`), and the audit transition log (`execution-core`). Every one of them is read through its replayable reference; none of them contains conversation history, tool transcripts, or build logs, and this spec adds no requirement that they should.

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| `LearningCandidate` record shape with occurrence list and occurrence count | 01 | `dashboard` (presentation), `mcp-server` (catalog derivation) |
| `learning.*` operation names and their operator-only classification | 01 | `mcp-server`, `dashboard` |
| Applied learning provenance record (originating PBIs, evidence references, approval timestamp) | 01 | `dashboard`, audit consumers |
| Observation fingerprint definition and suppression state | 04 | `dashboard` (showing why a candidate is absent) |
| Per-source-kind throttle state and reset | 04 | `dashboard` |
| Section size, maximum, consolidation count and limit-change history projection | 05 | `dashboard`; this is the spec's own honesty signal |
| Learning-sourced governance change declaration | 06 | `baseline-transitions` |

No other spec currently references this one by name, which matches its position as the most deferrable item on the map.

### Risks / judgement calls

**The init/learning collision is real and I resolved it by design.** `repository-readiness` states that re-running init "replaces the section's content in place". If approved learnings accumulate as free text in that same region, `gantry init` erases them. Slice 01 therefore specifies the marked section as a **render of persisted records** — init's standard content and applied learnings both come from the record set — so any writer re-renders rather than overwrites. This needs agreeing with spec 06's owner; it is the one cross-spec decision here that changes another spec's implementation.

**Whether `proposedRule` is produced deterministically or drafted by an agent.** The spec puts the Compound Learner role's envelope contracts out of scope and its testing decisions seed evidence and assert on the candidates produced, which reads as deterministic templating from the observation pattern. I have sliced it that way. If the intent was for a learner agent to draft the rule text, slice 01 gains a dependency on `gtp-protocol`'s role envelope and the instruction-versus-observation validation becomes a check on agent output rather than on a template. Worth confirming before slice 01 starts.

**I split the evidence sources into two slices (02 and 03) rather than one.** The split is by blocker set, not by size: 02's families are settled early (`execution-core`, `gtp-protocol`), 03's arrive late (`pbi-execution-loop`, `entropy-gate`). Merging them into one slice would make the whole thing wait for the latest dependency. If both dependency sets happen to be ready, merging them is reasonable.

**Aggregation sits in slice 01, suppression in slice 04.** Grouping occurrences into one candidate is inseparable from producing a candidate at all, so it went in the spine. Fingerprint-based suppression is a different concern with a different trigger and went with rejection. Aggregation *across executions* (as opposed to across PBIs within one) is in 01 as well, since it is the same grouping with a wider query — but it is the part most likely to want its own slice if retention across executions turns out to be more involved than a query.

**Slice 05 adds an audit requirement the specification implies but does not state.** The handoff calls out "whether the size limit ever gets raised" as the signal to watch. Nothing in the specification actually makes that observable, so slice 05 requires the limit value, every change to it, and the consolidation count to be recorded and readable. This is a small addition to scope and should be confirmed — without it the signal exists only in the operator's memory of their own config edits.

**The backoff curve is left configured rather than fixed.** The specification says throttling "raises the occurrence count required" without naming a function. Slice 04 treats the raised count as a configured step with a default rather than inventing a curve; if the operator wants a specific shape, it belongs in `config-and-snapshot`'s schema.

**Slice 06 is the one slice that can be half-delivered.** Its refusal half — that a `constitution` or `adr` candidate has no application path — depends on nothing but slice 01 and is the part that actually protects Governance Precedence. Its conversion half depends on `baseline-transitions`, which is itself late in the map. If that contract is not ready, landing the refusal alone is defensible and leaves the precedence guarantee intact; I did not split it into two slices because the resulting second slice would be too thin to be worth a PBI.
