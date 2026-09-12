## Spec 03 — gtp-protocol

This spec owns the wire between Gantry and every agent it dispatches: a two-layer envelope (common identity layer + role-discriminated payload), the fixed validation order at the boundary, Protocol Failure as a persistent condition distinct from an agent-reported `blocked` result, Result Submission identity and receipts, the closed status set and its precedence, the Implementation Completion rule, scope and governance-path protection, and the `ContextUsage` representation that keeps an unmeasurable integration from reporting zero. The risk sits in two places. First, the completion rule requires Gantry to re-execute the PBI's mandatory verification commands on the delivered revision rather than trust the agent's records — that binds a wave-0 spec to a check adapter interface owned by `verification-adapters` in wave 3, so the interface has to be agreed now and exercised through a fake. Second, the spec is mutually referential with `execution-core`: 01 owns the transition `pbi.submitResult` performs, 03 owns what makes the submission valid, and the `extensions` lifting rule decides 01's persistence shape. Every slice below is a round trip through `core.invoke` — `pbi.dispatch` out, `pbi.submitResult` in — against a real temporary SQLite database and Git repository with a scripted fake driver, because a validator called directly would not prove the boundary runs it.

### Slices

- **01 — Envelope boundary, extensions, and Protocol Failure**
- **What to build**: The common identity layer carried by every task and result, the fixed validation order (protocol version → common identities → current-assignment check → role payload), and the forward-compatibility rule that lifts unknown keys into `extensions` and persists them verbatim while a known field of the wrong type is always a violation. Envelopes are stored append-only under their assignment and iteration, and every dispatch and every result writes a telemetry event in the same transaction as the transition it evidences. Protocol Failure lands here as a persistent condition on the assignment with its full class taxonomy, preserving the agent's work and the raw submission, requiring no questions from the agent, and classified as protocol so it never consumes the infrastructure retry allowance. A single minimal builder payload exists only so the dispatch-and-submit round trip is demoable end to end; the real role payloads arrive in 02 and 03, and `role_mismatch` and `criteria_mismatch` are declared here but raised by those slices.

```ts
// the decision, not the whole type: validation order is positional, and version is a major marker
gtpVersion: "1";            // additive minor changes do not move it
ownershipGeneration: number; // checked before the payload is interpreted at all
extensions?: Record<string, unknown>; // preserved verbatim, never interpreted
```

- **Acceptance criteria**:
  - A dispatch returns a task envelope carrying every common identity — execution, unit, assignment, ownership generation, role, correlation, rule snapshot, plan version — and a dispatch missing any of them is refused before an agent is launched.
  - A result whose common identities reference a different execution or plan version is rejected as `identity_mismatch` without its payload being interpreted; a result for an assignment never dispatched is the same class.
  - A result carrying a stale ownership generation is stored and rejected as `stale_generation` with the state projection unchanged.
  - Unknown fields survive a store-and-read round trip inside `extensions`; a known field with a wrong type is rejected as `malformed_result` with the raw submission retained.
  - A dispatch that ends with exit code zero and no result is `missing_result`: the work is preserved, nothing advances, and the infrastructure retry allowance is unchanged.
  - No Protocol Failure class requires `questionsForOperator`, and every class is readable from the audit trail with its cause.
  - Iteration N+1 envelopes do not overwrite iteration N; both remain retrievable for the same assignment.
- **Blocked by**: needs the operation core `invoke`, the `pbi.dispatch` and `pbi.submitResult` operation shells, the `Rejection` code set, and atomic acceptance (transition + receipt + audit in one transaction) from `execution-core`; needs the PBI Execution Ownership generation and supersession rule from `execution-core`; needs the redaction sink interface from `data-handling`, because the retained envelope record is a writer.
- **Parallelizable with**: none intra-spec — everything else in this spec starts from it.

---

- **02 — Builder task and result contract**
- **What to build**: The builder branch of the role-discriminated union. The task states the PBI reference and version, the acceptance criteria with their stable identities, the approved verification commands, the allowed scope, and the continuity context when resuming after a handoff; it also states the required output contract inline so a spawned agent knows the exact shape it must return. The result carries per-criterion status with evidence references, the delivered revision, reported changed paths, and the agent's own verification attempt records. A submitted payload whose role discriminant does not match the assignment's role is a `role_mismatch` Protocol Failure, detected before any interpretation of its content.
- **Acceptance criteria**:
  - A builder task envelope produced by dispatch contains every criterion identity the assigned PBI declares, the approved verification commands, and the allowed scope patterns.
  - The task envelope states its required result contract, and a result conforming to it is accepted while one conforming to a different role's contract is not.
  - A payload whose role discriminant differs from the assignment's role is rejected as `role_mismatch` with the submission retained.
  - A builder result records the agent's verification attempts as context; the record is readable and is never treated as establishing anything on its own.
  - A criterion status value outside the declared set is `malformed_result`, not a silently ignored field.
- **Blocked by**: 01. Needs the criterion identity rule (required, never generated, stable) from `spec-validation`; needs the approved verification command set from `config-and-snapshot`.
- **Parallelizable with**: 03, 04, 06.

---

- **03 — Non-mutating role contracts**
- **What to build**: The remaining eight branches of the union — requirement critic, adversarial critic, slicer, spec architect, architectural sentinel, appsec gatekeeper, merger, compound learner — each with its task inputs and its result evidence. The decision-rich part is the adversarial critic: its findings are restricted to `spec-deviation`, `adr-deviation`, `semantic-conflict`, and `scope-creep`, and its payload has no field capable of expressing approval, clearance, or downgrade of an existing finding, so "may only add" is enforced by the shape rather than by a check someone could forget. The union is closed and exhaustive, so adding a role later cannot weaken validation for the existing ones.
- **Acceptance criteria**:
  - Each of the eight roles has a task payload carrying its declared inputs and a result payload carrying its declared evidence, both validated through the boundary.
  - The adversarial critic result type has no field that can clear, downgrade, or approve a deterministic finding — demonstrated by the absence of the field, not by a runtime check.
  - An adversarial critic finding outside the four allowed classes is a validation violation.
  - A slicer result carries proposed PBIs with criterion identities, dependencies, a story coverage map, and a per-PBI context estimate with method and uncertainty, each as a structured field rather than prose.
  - Exhaustiveness over the role union is enforced at the type level, so an unhandled role fails to build rather than falling through to a permissive default.
- **Blocked by**: 01. Needs the criterion identity rule from `spec-validation`; needs the plan version hash definition and the story coverage map shape from `slicing-and-approval`; needs the normalized finding shape from `verification-adapters` for the deterministic findings passed into the adversarial critic task.
- **Parallelizable with**: 02, 04, 06.

---

- **04 — Status precedence, handoff continuity, and context usage**
- **What to build**: The closed status set `complete | failed | needs_handoff | blocked` with a fixed precedence — `blocked` outranks `needs_handoff`, which outranks any evaluation of completion — so one result can never be read two ways. `blocked` requires a non-empty list of questions for the operator; an empty list makes the result invalid rather than unblocked, and a valid one moves the PBI to `awaiting_operator`. `needs_handoff` requires a reason and continuity content and moves the PBI to `handoff_pending`. `complete` is a claim, not a transition. Context usage lands here because it arrives on results: a three-variant union with no default, where an integration that cannot measure returns `unknown` with a reason and self-reported usage is structurally distinct from measured and never establishes a watermark guarantee.

```ts
type ContextUsage =
  | { kind: "measured"; tokens: number; window: number; source: string }
  | { kind: "self_reported"; tokens: number; window?: number }
  | { kind: "unknown"; reason: string };
```

- **Acceptance criteria**:
  - A result carrying both `blocked` and completed criteria resolves as `blocked` and moves the PBI to `awaiting_operator`.
  - `blocked` with an empty question list is invalid; the result does not advance anything and is not treated as unblocked.
  - A result carrying both `needs_handoff` and completed criteria resolves as `needs_handoff`, retains the criteria progress, and moves the PBI to `handoff_pending`.
  - `needs_handoff` without a reason or without continuity content is invalid.
  - A result whose context usage is `unknown` is projected as unknown; no code path can render it as zero, and `self_reported` is never presented as a measurement.
  - `complete` on its own produces no transition past implementation until the completion rule evaluates it.
- **Blocked by**: 01.
- **Parallelizable with**: 02, 03, 06.

---

- **05 — Criterion accounting and Implementation Completion**
- **What to build**: The rule that turns a builder's completion claim into the `implementation_complete` state, and no further. Every criterion identity the assigned PBI declares must appear in the result exactly once, every one must be `completed`, and each must carry an evidence reference naming the verification command that covers it and the revision it was observed on. Gantry then re-executes the PBI's approved mandatory verification commands against the delivered revision through the check adapter and uses its own result — the agent's verification records are retained as context and as a discrepancy signal, never as the basis for completion. A disagreement between the agent's reported pass and Gantry's observed failure is recorded as a verification-integrity finding. Completion advances the PBI to `in_gates` and nothing further.
- **Acceptance criteria**:
  - A valid builder result with every criterion completed and Gantry's own mandatory test run passing leaves the PBI in `in_gates`, not merge-authorized.
  - A single `pending` criterion refuses completion even when the test run is green.
  - All criteria completed with Gantry's own test run failing refuses completion.
  - An agent reporting a pass where the check adapter is scripted to fail refuses completion and records a verification-integrity finding.
  - A criterion identity absent from the result, and a criterion identity the PBI does not declare, are both `criteria_mismatch`.
  - A completed criterion with no evidence reference refuses completion.
- **Blocked by**: 02 (the builder result payload) and 04 (`complete` as a claim). Needs the check adapter interface — run an approved verification command against a named revision and return a normalized pass/fail plus findings — from `verification-adapters`; needs the approved mandatory verification command set from `config-and-snapshot`.
- **Parallelizable with**: 03, 06, 07.

---

- **06 — Result submission identity, idempotency, and corrections**
- **What to build**: A submission identity distinct from the task correlation, so a replay is recognizable as a replay and a correction is a new linked attempt rather than an overwrite. The content hash is taken over a deterministically canonicalized payload — sorted keys, no insignificant whitespace, `extensions` included — and the submission identity maps onto the operation core's `requestId` for `pbi.submitResult`, so idempotency is enforced in one place rather than two. An identical submission returns the original receipt with no repeated transition, counter change, acceptance event, or downstream dispatch; the same identity with different content is rejected; a correction uses a new identity carrying `supersedes`, retains the prior submission, and passes ownership, role, and transition checks again.
- **Acceptance criteria**:
  - An identical resubmission returns the original receipt, with no second transition, no counter change, and no downstream dispatch.
  - The same `submissionId` with altered content is rejected as a duplicate conflict, and the stored receipt still describes the originally accepted content.
  - A new `submissionId` with `supersedes` set is accepted, and both the superseded and the superseding submission remain readable in history.
  - A corrected submission from a superseded assignment is still rejected on ownership, proving correction is not a path around the rules.
  - Canonicalization is deterministic: two payloads differing only in key order or insignificant whitespace produce the same content hash, and a payload differing only inside `extensions` does not.
- **Blocked by**: 01. Needs `requestId` idempotency, receipt shape, and the `duplicate_conflict` rejection from `execution-core`; needs the normalized content hashing rule (line endings) from `data-handling`.
- **Parallelizable with**: 02, 03, 04, 05, 07.

---

- **07 — Allowed scope and governance-path protection**
- **What to build**: Every mutating task declares its allowed scope as path patterns, and a result reporting changes outside that scope is a scope violation: the result is retained, a violation is recorded as a finding, and the PBI does not complete. Protected governance paths come from the repository's effective Artifact Location Mapping rather than hardcoded directory names, and an ordinary assignment reporting a change to one of them is a violation. An assignment issued under an approved Governance Baseline Transition carries an explicit permission naming those paths, so the protection does not block the work whose entire purpose is to change them; absent that permission, the change is a violation.
- **Acceptance criteria**:
  - A result reporting a changed path outside the task's allowed scope records a scope violation, retains the result, and leaves the PBI short of `implementation_complete`.
  - A result reporting a change to a protected governance path under an ordinary assignment is a violation.
  - The same result under an assignment carrying explicit baseline-transition permission naming those paths is accepted.
  - Protected paths are resolved from the Artifact Location Mapping, proven by a fixture that relocates the governance directory and sees protection follow it.
  - A baseline-transition permission naming path A does not authorize a change to path B.
- **Blocked by**: 02 (the builder task's allowed scope and the result's reported changed paths). Needs the Artifact Location Mapping schema from `repository-readiness`; needs the governance-path permission in a transition declaration from `baseline-transitions`; needs the normalized finding shape from `verification-adapters` for the recorded violation.
- **Parallelizable with**: 03, 04, 05, 06 — see the note in Risks about where the completion refusal is wired.

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Operation core `invoke`, `pbi.dispatch` / `pbi.submitResult` operations, `Rejection` code set, atomic acceptance | `execution-core` | 01 (all others inherit) |
| PBI Execution Ownership generation and supersession rule | `execution-core` | 01, 06 |
| `requestId` idempotency, receipt shape, `duplicate_conflict` | `execution-core` | 06 |
| Redaction sink enforcement interface | `data-handling` | 01 |
| Normalized content hashing (line endings) | `data-handling` | 06 |
| Execution Rule Snapshot identity | `config-and-snapshot` | 01 |
| Approved verification command set (including mandatory tests) | `config-and-snapshot` | 02, 05 |
| Plan version hash definition | `slicing-and-approval` | 01, 03 |
| Story coverage map and context estimate fields | `slicing-and-approval` | 03 |
| Criterion identity rule (required, never generated, stable) | `spec-validation` | 02, 03, 05 |
| Check adapter interface (run approved command against a revision) | `verification-adapters` | 05 |
| Normalized finding shape | `verification-adapters` | 03, 05, 07 |
| Artifact Location Mapping schema | `repository-readiness` | 07 |
| Governance-path permission in a transition declaration | `baseline-transitions` | 07 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| `extensions` lifting rule and persisted envelope shape | 01 | `execution-core` (persistence shape), every schema in this spec |
| `GtpCommon` envelope, validation order, `gtpVersion` compatibility range | 01 | `demo-mode`, `harness-adapters`, `pbi-execution-loop`, `mcp-server`, `dashboard` |
| Protocol Failure class taxonomy and its accounting exemption | 01 | `harness-adapters`, `pbi-execution-loop`, `execution-core` |
| Builder task and result contract (criteria status, allowed scope, verification records) | 02 | `pbi-execution-loop`, `demo-mode`, `entropy-gate` |
| Non-mutating role task/result contracts; adversarial critic add-only shape | 03 | `spec-validation`, `slicing-and-approval`, `entropy-gate`, `git-integration`, `compound-learning` |
| `ContextUsage` union (`measured` / `self_reported` / `unknown`) | 04 | `harness-adapters`, `pbi-execution-loop`, `dashboard` |
| Status precedence and `needs_handoff` continuity fields | 04 | `pbi-execution-loop`, `dashboard` |
| Implementation Completion rule (Gantry re-verifies on the delivered revision) | 05 | `pbi-execution-loop`, `entropy-gate`, `verification-adapters` |
| Result Submission identity, receipt semantics, correction linkage | 06 | `execution-core`, `harness-adapters`, `mcp-server` |
| Scope violation record and governance-path protection rule | 07 | `entropy-gate`, `baseline-transitions`, `pbi-execution-loop` |

### Risks / judgement calls

**Slice 01 is deliberately the biggest.** I folded Protocol Failure into the envelope boundary rather than giving it its own slice. Four of its six classes (`missing_result`, `malformed_result`, `identity_mismatch`, `stale_generation`) are pure common-layer validation, and the other two are raised by slices 02 and 05. Splitting it would have made 02, 03, 05 and 07 all block on a Protocol Failure slice for nothing more than an enum and a record shape, turning a fan-out into a chain. The cost is that slice 01 declares two class values it does not itself raise. If the operator prefers a smaller bootstrap, the natural cut is to move append-only storage and the telemetry-event-in-the-same-transaction rule out into their own slice, but that slice would not be independently demoable.

**Where the scope-violation refusal gets wired.** Slice 07 records the violation; slice 05 owns the completion rule. I made them parallel, with 07's violation expressed as a record that 05's completion rule consults. Whichever lands second wires the consultation, and the "out-of-scope change refuses completion" scenario belongs to that second PR. The alternative — blocking 07 on 05 — is cleaner on paper and costs a week of serialization. Worth an operator decision.

**Wave-0 spec, wave-3 dependencies.** Slice 05 needs the check adapter interface from `verification-adapters` and slices 03/05/07 need its normalized finding shape, both of which land much later in the build order. Under the standing seam these are injected fakes, so the slices are buildable now, but the *interface shapes* have to be agreed before slice 05 starts or they will be invented here and renegotiated later. The handoff already names the normalized finding shape as a cross-spec decision to lock; I would add the check adapter's "run one approved command against a named revision" signature to that list, because spec 03's strongest decision — Gantry re-runs the mandatory tests rather than trusting the agent — depends on it entirely.

**Splitting the role union.** I was tempted to keep all nine roles in one slice; the payloads are individually small. I split builder from the rest because 05 and 07 depend only on the builder half, and `spec-validation`, `slicing-and-approval`, `entropy-gate` and `compound-learning` depend only on the other half. The split buys real parallelism at the cost of two slices that share a discriminated union — whoever lands second must not weaken the exhaustiveness check the first one established.

**Context usage placed with status.** It is arguably its own concern, but as a standalone slice it is too thin to be a PBI. It arrives on results alongside `needs_handoff`, and the ADR-0001 argument for `unknown` is the same argument as the one for not letting a `complete` claim be a transition, so they read as one slice about honest reporting.
