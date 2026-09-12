## Spec 04 — data-handling

This spec owns the three data-boundary policies of the factory: **Output Redaction** (one pipeline every output passes through before it reaches any sink), **Telemetry Retention** (reference-first records that locate versioned content rather than copying it), and **Data Egress Policy** (a declared role × driver × payload-class matrix that permits or blocks a dispatch). Its risk is almost entirely *structural rather than algorithmic*. The detectors are ordinary pattern matching; the retention record is ordinary schema; the matrix is ordinary lookup. What is hard is that compliance must be impossible to forget — a writer added six specs later must not be able to persist a raw string — and that the whole thing fails closed, which means every dial (inspection bound, undecodable output, ambiguous allowance) converts a routine condition into blocked work an operator feels as friction. The handoff names this spec's redaction sink interface "the one to build first regardless of spec order", and it is right: retrofitting it means auditing every writer in the system. A second, quieter cross-spec obligation sits here too — **normalized content hashing** — because `core.autocrlf` makes filesystem-byte hashes platform-dependent, and spec 12's content anchors and spec 02's governance document hashes both inherit whatever this spec decides.

### Slices

---

- **01 — Redaction sink boundary and normalized content hashing**
- **What to build**: One pipeline producing a three-way outcome (`clean` / `redacted` / `uncertain`) carrying metadata of detector identity, hit count, and ruleset version — and a sink signature that accepts *only* a pipeline result, so a raw string is not a valid argument to anything that persists or displays. Wire it through one real record write in the shared operation core, so a fake harness driver emitting output with a planted token is stored masked. Ship the normalized content hashing rule in the same slice — a single line-ending convention and a consistent trailing-newline rule — and apply it to that record's content hash field, because every writer in the system consumes both of these and they should have one unblock point. Only enough built-in pattern detectors to prove the path; the detector catalog is slice 02.

  The outcome shape encodes the decision that there is no partial-content variant:

  ```ts
  type RedactionOutcome =
    | { confidence: "clean";     content: string; metadata: RedactionMetadata }
    | { confidence: "redacted";  content: string; metadata: RedactionMetadata }
    | { confidence: "uncertain"; content: null;   metadata: RedactionMetadata; reason: string };
  ```

- **Acceptance criteria**:
  - A fake harness driver output containing a planted bearer token is persisted with the token replaced by a marker, and the stored record is readable through the core's audit read operation with the marker in place.
  - Stored redaction metadata contains detector identity, hit count, and ruleset version, and contains no offset, length, prefix, or hash of matched content — asserted by schema shape, not by inspection.
  - Passing a raw string to a sink fails to compile, and a runtime refusal exists for content arriving without a pipeline result across a dynamic boundary.
  - The same content hashed with CRLF endings and with LF endings yields one identical hash; the trailing-newline rule produces one hash for both the present and absent case as declared.
  - Redaction is applied on the error path: a scripted driver failure whose failure output carries a planted secret is stored masked, not stored raw and not dropped.
- **Blocked by**: Needs the **`invoke` seam and the audit record family** from `execution-core` for the end-to-end proof. The pipeline interface, the outcome type, the sink signature, and the hashing rule can all start immediately and should be published ahead of that, per the handoff's sequencing note.
- **Parallelizable with**: 06

---

- **02 — Detector sources and ruleset versioning**
- **What to build**: The three declared detector sources, in precedence order: the literal values of environment variables referenced by the effective configuration (matched as values, never stored), a versioned catalog of pattern detectors for common shapes (bearer tokens, API key formats, PEM private key blocks, signed URL query parameters, connection strings with embedded credentials), and the repository's configured secret scanner rules where one exists, so redaction agrees with the scanner the repository already trusts. Ruleset version is emitted with every outcome and is derived from the composed source set, so adding a repository scanner changes the version. This is the one place in the spec where tests bind to the pipeline interface directly rather than through a sink — the spec authorizes that exception explicitly, and those tests assert only on the outcome, never on internals.
- **Acceptance criteria**:
  - An output containing the value of an environment variable named in the effective configuration is redacted, and the variable's value appears nowhere in the stored record or in the metadata.
  - Each pattern detector in the catalog has a positive case and a negative near-miss case, and a detector's identity appears in metadata only when it hit.
  - A repository with a configured secret scanner contributes its rules; the resulting ruleset version differs from the same repository with no scanner configured.
  - Two outputs redacted under the same source set record the same ruleset version; changing any source changes it.
  - At least one detector from each of the three sources is proven end-to-end through a sink, not only through the pipeline interface.
- **Blocked by**: 01. Cross-spec: needs the **effective configuration document with its environment variable references** from `config-and-snapshot`, and the **repository secret scanner detection result** from `repository-readiness`.
- **Parallelizable with**: 03, 04, 06

---

- **03 — Withheld output and blocked-for-review**
- **What to build**: Confidence classification by declared rule rather than inference, and the propagation that makes withholding visible. Output becomes `uncertain` when a detector errors, when it exceeds the configured inspection bound, when it is not decodable text, or when a detector reports a partial match it cannot resolve. An `uncertain` outcome stores no content at all, marks the associated operation or check blocked for review with its reason, surfaces that in the state projection, and prevents the gate that depended on it from passing. A redaction failure is never reported as a passing check — that is the invariant this slice exists to prove.
- **Acceptance criteria**:
  - A scripted detector error, an undecodable byte sequence, and an output exceeding the inspection bound each produce `uncertain`, persist no content, and record a reason.
  - The affected operation or check is marked blocked for review and the state projection exposes both the withheld condition and its reason.
  - An Entropy Gate whose Comparison Evidence was withheld as `uncertain` does not reach a passed state; it remains blocked on incomplete evidence rather than passing or failing silently.
  - The inspection bound and the undecodable-output treatment are read from configuration, so a repository can widen them deliberately.
  - A withheld output's metadata still records the ruleset version and any detector hits observed before the uncertainty arose.
- **Blocked by**: 01. Cross-spec: needs the **blocked-state transitions and the gate `pending` / blocked-on-incomplete-evidence states** from `execution-core`, and the **inspection bound and undecodable-output configuration keys** from `config-and-snapshot`.
- **Parallelizable with**: 02, 04, 06

---

- **04 — Reference-first retention and replayable references**
- **What to build**: The default Telemetry Retention record and the references that make it replayable. A retained record holds identities, timestamps, statuses, normalized content hashes, redacted summaries, and evidence metadata, plus at least one reference locating the versioned content — a Git revision and path, a provider object identity, a PBI Worktree location, or an Execution Rule Snapshot field. Build the resolver too: a reference is only replayable if it resolves. A reference whose source cannot be resolved is a missing-source condition that blocks reconciliation and resumption rather than being treated as a complete record. Worktree references are the weakest kind, since cleanup can remove them, so records depending on them must be surfaced to the cleanup manifest.

  ```ts
  type ReplayableReference =
    | { kind: "git";       unit: RepositoryExecutionUnitId; revision: string; path?: string }
    | { kind: "provider";  provider: string; objectKind: string; objectId: string }
    | { kind: "worktree";  unit: RepositoryExecutionUnitId; pbi: PbiId; path: string }
    | { kind: "snapshot";  snapshot: SnapshotId; field: string };
  ```

- **Acceptance criteria**:
  - After a completed PBI, its records hold references, hashes, and redacted summaries rather than diffs, prompts, source files, or build logs, and each summarizing record carries at least one reference.
  - Every reference in those records resolves against the real temporary Git repository or the stored snapshot.
  - A record whose Git revision no longer exists blocks reconciliation with the core's reconciliation-required rejection instead of being treated as complete.
  - A cleanup proposal lists the records that depend on a worktree reference it would remove.
  - The dispatch payload and the retained record are distinguishable: a dispatch carrying full approved context leaves behind a reference-first record, proven by asserting the record does not contain the payload body.
  - A handoff memo persists only remaining criteria, completed criteria, modified file references, and the relevant failure — no conversation history, tool transcript, or build log.
- **Blocked by**: 01. Cross-spec: needs the **record persistence families and the cleanup manifest** from `execution-core`, and the **handoff memo field set** from `pbi-execution-loop` for the memo criterion (the other criteria do not wait on it).
- **Parallelizable with**: 02, 03, 06

---

- **05 — Detailed retention opt-in and evidence invalidation**
- **What to build**: The per-repository opt-in that trades storage for depth, and the invalidation that keeps it honest. Detailed retention stores fuller content, still through the pipeline and still subject to `uncertain` withholding, so opting in never opts out of Output Redaction. The retention level in effect for a record is the one captured in its Execution Rule Snapshot, not the current setting, so changing it does not retroactively alter a running execution's records. Turning detailed retention off invalidates evidence that depended on content no longer kept: affected gate results return to pending and the invalidation is recorded, following the snapshot-migration classification.
- **Acceptance criteria**:
  - With detailed retention enabled, a record stores fuller content and that content is still redacted by the pipeline.
  - A record written under a snapshot capturing the default level keeps default-level content even after the current setting is raised.
  - Disabling detailed retention returns gate results that depended on the dropped content to pending, and records an invalidation naming the cause.
  - Gate results that did not depend on the dropped content keep their original binding and are not invalidated.
  - Detailed retention with an `uncertain` outcome still stores no content and still marks the operation or check blocked for review.
- **Blocked by**: 04. Cross-spec: needs the **retention level field in the data-handling configuration section and its capture in the Execution Rule Snapshot**, plus the **snapshot migration record classification**, both from `config-and-snapshot`.
- **Parallelizable with**: 02, 03, 07

---

- **06 — Egress matrix resolution and dispatch enforcement**
- **What to build**: The declared Data Egress Policy matrix and the enforcement point at dispatch. A dispatch is permitted only when an allowance matches its role and its *resolved* driver and lists every payload class the dispatch carries. Absence blocks and ambiguity blocks — two allowances disagreeing for the same role and driver resolve to neither — with a rejection that names the missing or conflicting allowance. Destination is classified by where processing actually occurs, taken from the driver's declaration rather than from the location of the executable, so a detached CLI reaching a remote model is remote and a stub driver is local. Secrets are prohibited regardless of allowance: the pipeline runs before dispatch payload assembly as well as before retention, so approving a destination never approves sending credentials to it.

  ```ts
  type PayloadClass =
    | "spec_text" | "pbi_text" | "governance_doc"
    | "source_context" | "diff"
    | "check_report" | "finding"
    | "prompt_template" | "agent_output";
  ```

- **Acceptance criteria**:
  - A dispatch whose role and resolved driver are absent from the matrix is blocked, and the rejection names the missing allowance.
  - A dispatch carrying a payload class the matrix does not allow for that destination is blocked, and the rejection names the class.
  - Two conflicting allowances for the same role and driver block rather than resolving to either one.
  - A driver declared to reach a remote model is classified remote even when launched locally; a stub driver is classified local.
  - A repository configured for local-only processing completes a full dispatch with no remote destination recorded anywhere.
  - A secret-shaped string in a dispatch payload is redacted before assembly even when the destination is approved for that payload class.
- **Blocked by**: None intra-spec — the matrix schema, resolution, blocking, and destination classification can start immediately. Consumes slice 01's pipeline interface for the pre-assembly redaction criterion only, and can be developed against that interface before 01 lands. Cross-spec: needs the **egress matrix configuration section** from `config-and-snapshot`, the **resolved driver identity and its declared processing destination** from `harness-adapters`, the **role identity and dispatch payload assembly point** from `gtp-protocol`, and the **onboarding interview result that produces the matrix** from `repository-readiness`.
- **Parallelizable with**: 01, 02, 03, 04

---

- **07 — Egress audit trail and driver-change reauthorization**
- **What to build**: The record that lets an audit answer *what* was sent and not only *where*. Each dispatch records its resolved driver, its destination, the provider identity for a remote destination, and the payload classes it carried. The matrix is captured in the Execution Rule Snapshot, so a change applies to new executions rather than to work already in flight. Changing a role's driver invalidates the prior egress authorization and blocks dispatch until reauthorized, because the data boundary changed even though the role did not. The enforcement boundary is stated in the projection rather than implied: coverage is Gantry-mediated dispatch, not every action a Host Harness can take through its own channels.
- **Acceptance criteria**:
  - Every dispatch record names its resolved driver, destination, provider identity where remote, and the payload classes carried.
  - A remote destination without a recorded provider identity is rejected rather than recorded as anonymous.
  - The matrix in effect for an in-flight execution is the one captured in its snapshot, not the current configuration.
  - Changing a role's driver blocks the next dispatch with a rejection naming reauthorization, and a fresh authorization unblocks it.
  - The state projection carries the enforcement-boundary statement, so no surface can present Gantry-mediated egress control as control over all harness traffic.
- **Blocked by**: 06. Cross-spec: needs the **snapshot capture of the egress matrix** from `config-and-snapshot` and the **driver replacement flow** from `harness-adapters`.
- **Parallelizable with**: 02, 03, 04, 05

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Shared operation core `invoke` seam and operation catalog | `execution-core` | 01, 03, 04, 05, 06, 07 |
| SQLite record families (audit, gates and findings, operations and submissions) | `execution-core` | 01, 04, 05, 07 |
| Blocked-state transitions and gate `pending` / incomplete-evidence states | `execution-core` | 03, 05 |
| Reconciliation flow and `reconciliation_required` rejection | `execution-core` | 04 |
| Cleanup proposal manifest | `execution-core` | 04 |
| Effective configuration document and its environment variable references | `config-and-snapshot` | 02 |
| Data-handling configuration section (egress matrix, retention level, detector ruleset reference, inspection bound) | `config-and-snapshot` | 03, 05, 06 |
| Execution Rule Snapshot capture | `config-and-snapshot` | 05, 07 |
| Snapshot migration record classification | `config-and-snapshot` | 05 |
| Role identity and dispatch payload assembly point | `gtp-protocol` | 06, 07 |
| Resolved driver identity and declared processing destination | `harness-adapters` | 06, 07 |
| Driver replacement flow | `harness-adapters` | 07 |
| Repository secret scanner detection result | `repository-readiness` | 02 |
| Egress matrix onboarding interview result | `repository-readiness` | 06 |
| Handoff memo field set | `pbi-execution-loop` | 04 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| **Redaction sink enforcement interface** (`RedactionOutcome`, sink signature, "no raw string is a valid sink input") | 01 | **Every writer in the system** — `execution-core`, `gtp-protocol`, `config-and-snapshot`, `harness-adapters`, `pbi-execution-loop`, `verification-adapters`, `entropy-gate`, `git-integration`, `dashboard`, `compound-learning`, `mcp-server`, `demo-mode` |
| **Normalized content hashing** (line-ending convention, trailing-newline rule) | 01 | `verification-adapters` (content anchors), `config-and-snapshot` (governance document and snapshot hashes), `baseline-transitions`, every retained record |
| Redaction metadata shape (detector identity, hit count, ruleset version; no offsets or lengths) | 01, extended by 02 | `dashboard`, `execution-core` audit family |
| Withheld-content semantics: `uncertain` → blocked for review → gate cannot pass | 03 | `entropy-gate`, `verification-adapters`, `dashboard` |
| `ReplayableReference` kinds and the missing-source blocking rule | 04 | `execution-core` (cleanup, reconciliation), `config-and-snapshot` (governance document recovery), `pbi-execution-loop`, `verification-adapters`, `git-integration` |
| Telemetry Retention default record shape and detailed-retention invalidation rule | 04, 05 | `config-and-snapshot` (snapshot migration), `entropy-gate`, `pbi-execution-loop` |
| `PayloadClass` enum and `EgressAllowance` shape, plus the block-on-absence/ambiguity rule | 06 | `config-and-snapshot` (schema), `repository-readiness` (interview), `harness-adapters`, `pbi-execution-loop` (dispatch) |
| Egress audit fields and the driver-change reauthorization rule | 07 | `harness-adapters`, `git-integration`, `dashboard` |

### Risks / judgement calls

**Normalized content hashing has no slice of its own — I folded it into slice 01.** Alone it is a normalization function plus a hash, too thin to be a PBI, but it is one of the widest contracts in the handoff's table (read by spec 12's content anchors, spec 02's snapshot hashes, and every retained record). Putting it in the bootstrap makes slice 01 the single unblock point for "the two things every writer consumes". The cost is that slice 01 is the largest of the seven. If the operator would rather 01 stay minimal, hashing splits out cleanly as a 4.5-sized slice — but then specs 12 and 02 wait two levels instead of one.

**Slice 01's blocker is soft, and someone has to decide how.** The handoff says build this before any other writer; but an end-to-end tracer needs a sink, and the sinks live in `execution-core`. Two options: ship 01 as an interface package that `execution-core` adopts as it builds its record families (fastest, but 01 is then not independently demoable until `execution-core` lands), or let 01 wait for `execution-core`'s audit family and prove itself there (demoable, but the "build first" instruction becomes advisory). I wrote the slice assuming the second, with the interface published early. This is the one ordering call I am least sure about, and it is coordination with whoever slices `execution-core`, not a technical unknown.

**Slice 02's tests bind to the pipeline interface, not through a sink.** That is a deliberate exception the spec grants — enumerating detector cases through operations would be slow and would obscure the assertion — but it looks like a seam violation to a reviewer holding the standing testing decision. It is scoped: those tests assert only on the outcome value, and slice 02 still carries one end-to-end criterion per detector source.

**I was tempted to split slice 04.** "Define the reference kinds" and "resolve them, and block on a missing source" read like two slices. I kept them together because a reference you cannot replay is not a replayable reference, and splitting would produce exactly the horizontal layer slice the brief rules out. It is the second-largest slice as a result.

**I was tempted to merge 06 and 07.** Kept apart because 07's driver-change reauthorization depends on `harness-adapters`' driver replacement flow, which sits in wave 3 and will land well after the matrix is needed. Merging would drag the whole egress surface behind a wave-3 dependency.

**Slice 05's real blocker may be `config-and-snapshot`, not my slice 04.** Its invalidation behavior is defined as "following the snapshot-migration classification in spec 02". If that classification is still in flight, slice 05 can build the opt-in and the redaction-still-applies half but cannot finish the invalidation half. Worth sequencing 05 after `config-and-snapshot`'s snapshot-migration issue regardless of where my 04 lands.

**This spec has no transport surface of its own.** There is no `gantry` subcommand and no MCP tool that belongs to data-handling — the observable surfaces are the state projection, the audit read, and rejection codes, all owned by `execution-core`. So no slice here carries a CLI/MCP/dashboard parity test, and the "redaction applies to the dashboard feed" user story is proven on the projection data rather than through spec 17's renderer. If the team lead expects every spec to contribute a parity test, this one legitimately does not.

**The failing-closed friction is real and is not a slice.** An oversized build log or a tool emitting binary output will withhold content and block a check for review, and operators will feel it. The two dials are the inspection bound and the undecodable-output rule, both configuration, both landing in slice 03. Whether their defaults are set wide or narrow is a product call I did not make — I only required that they be configurable rather than guessed.
