## Spec 09 — slicing-and-approval

This spec owns the planning half of the factory: turning a technically ready Living Spec into a set of PBIs, each with a complete narrow behavior, criteria traced back to the spec's criterion identifiers, declared verification, explicit prerequisites, story coverage, and an Initial Context Budget estimate — then linting that breakdown, getting one explicit Planning Approval over an identified plan version, and gating dispatch on it. The risk sits in four places, in descending order of danger. First, the **plan version hash**: it is the identity that `pbi-execution-loop` gates dispatch on and that `baseline-transitions` reads, so if its definition is loose or its inputs are unnormalized, approval silently leaks across edits. Second, **Dependency Readiness**, which must be evaluated against Git at dispatch rather than against any recorded status — the stale-base failure is invisible to a status field. Third, the **upper-bound budget comparison**: using the point estimate instead of `upperBoundFraction` turns the uncertainty margin into decoration. Fourth, the **behavioral-versus-internal change classification**, which the spec openly admits cannot be fully mechanized; the mitigation is that everything touching a recorded artifact is behavioral by default and every classification carries a recorded rationale.

### Slices

---

**01 — Plan proposal and plan version identity**

- **What to build**: Stand up the plan record family and the `plan.propose` operation end to end. A slicer role result — proposed PBIs with behavior, criteria carrying spec criterion identifiers, verification entries, prerequisites, story coverage, scope hint, and a context estimate — is validated for shape, persisted, and reduced to a `PlanVersion` whose identity is a hash over the spec content hash, the ordered per-PBI content hashes, and the dependency graph. The story coverage map is derived and stored as part of the version. `gantry slice-spec` drives this from the CLI against a fake slicer harness driver, and the state projection exposes the proposal and its version identity. This slice defines the hash inputs, their ordering, and their normalization; it does not lint, estimate, or approve.
- **Acceptance criteria**:
  - A slicer result persists a plan proposal and returns a stable `PlanVersionId`; re-proposing byte-identical content yields the same identity.
  - Reordering PBIs in the slicer payload does not change the identity; editing any PBI's content, the spec content, or an edge in the dependency graph does change it.
  - Plan version hashing is computed over normalized content, so `core.autocrlf` line-ending differences do not alter the identity.
  - The stored proposal records the story coverage map keyed by spec user story identifier.
  - A proposal whose criteria carry identifiers not present in the normalized spec model is rejected at the operation boundary.
  - `gantry slice-spec` is one parity test proving delegation to `invoke`, not behavior.
- **Blocked by**: needs the operation core `invoke` surface, request/outcome shapes and record families from `execution-core`; needs the slicer role task and result payload contract from `gtp-protocol`; needs the criterion identity rule and normalized spec model (criteria ids, user story ids, spec content hash) from `spec-validation`; needs normalized content hashing (line endings) from `data-handling`; needs the Artifact Location Mapping schema from `repository-readiness` to locate spec and PBI documents.
- **Parallelizable with**: None (bootstrap).

---

**02 — PBI lint rules and breakdown coverage**

- **What to build**: Implement `gantry lint-pbi` as an operation over a persisted plan proposal, evaluating the declared rules as data with stable rule identities and emitting findings in the shared structured shape. Per-PBI: `PBI-BEHAVIOR`, `PBI-CRITERIA-ID`, `PBI-VERIFICATION`, `PBI-CRITERIA-COVERED`, `PBI-STORY-COVERAGE` as blockers and `PBI-FILE-COUNT` as the sole warning, carrying the threshold value in the message. At the breakdown level: every approved user story is covered by at least one PBI. Test duration is not a rule and no rule may reference it. `PBI-BUDGET` and `PBI-DEPS-RESOLVABLE` belong to slices 03 and 04 and are absent here.
- **Acceptance criteria**:
  - A PBI whose criteria do not trace to spec criterion identifiers fails `PBI-CRITERIA-ID`; a criterion with no covering verification entry fails `PBI-CRITERIA-COVERED`; a PBI with no verification definition fails `PBI-VERIFICATION`.
  - A PBI with slow but defined verification passes, and no rule identity or message references duration.
  - A PBI touching seven files produces the `PBI-FILE-COUNT` warning with the threshold visible, still passes lint, and remains eligible for approval.
  - A breakdown leaving an approved user story uncovered fails the breakdown-level coverage rule; a PBI covering no story fails `PBI-STORY-COVERAGE`.
  - Lint results are persisted against the plan version they were evaluated on, and lint success alone produces no approval record.
  - `gantry lint-pbi` is one parity test proving delegation.
- **Blocked by**: 01; needs the file-count threshold and Initial Context Budget values from `config-and-snapshot`'s context policy; needs the approved verification command reference (`ApprovedCommandRef`) from `repository-readiness` (Verification Command Approval).
- **Parallelizable with**: 03, 04, 05, 06

---

**03 — Context estimation and the upper-bound budget**

- **What to build**: Implement the `ContextEstimate` computation and the `PBI-BUDGET` rule. A pluggable tokenizer (injected, deterministic stub in tests) counts known components — instructions, spec, PBI text, contracts, governance — and records `sampled` or `declared` basis for unknown ones such as source files, with the basis mandatory per component. The estimate records tokenizer id and version, assumed model and window, per-component tokens and basis, total, uncertainty margin, `upperBoundFraction`, and method. `PBI-BUDGET` compares the upper bound — never the point estimate — against the configured budget. The same evaluator is exposed for a continuity package including a handoff memo, with no separate allowance, and a package that cannot fit without dropping contracts, criteria, or governance produces a review pause rather than a trimmed package. The state projection carries estimated and observed context as separate fields with observed `unknown` until measured.
- **Acceptance criteria**:
  - An estimate whose point value is under budget but whose upper bound exceeds it fails `PBI-BUDGET`.
  - An estimate missing tokenizer, assumed window, margin, method, or any component's basis is rejected as invalid rather than defaulted.
  - Evaluating a continuity package that includes the handoff memo uses the same budget value and the same comparison; no code path applies a reduced or separate allowance.
  - A package whose mandatory content alone exceeds the budget yields a review pause; no output path drops contracts, criteria, or governance content.
  - The projection exposes estimated and observed as distinct fields, and observed is `unknown` before any integration reports a measurement — there is no code path that writes an estimate into the observed field.
  - Assertions are structural (fields present, comparison uses the upper bound); no test asserts an exact token count.
- **Blocked by**: 01; needs the Initial Context Budget limit value and assumed-window/model configuration from `config-and-snapshot`.
- **Parallelizable with**: 02, 04, 05, 06

---

**04 — Dependency graph validation at planning**

- **What to build**: Implement `PBI-DEPS-RESOLVABLE` and the breakdown-level acyclicity rule over the persisted prerequisites. Every prerequisite must resolve to a PBI in the same plan, self-dependency is rejected, and the whole graph is validated acyclic with the offending cycle named in the finding. The validated graph is the same structure that feeds the plan version hash from slice 01, so a graph edit changes the plan identity. Output is a resolved graph projection the dashboard and the execution loop can read without re-deriving it.
- **Acceptance criteria**:
  - A cyclic graph, a self-dependency, and a prerequisite referencing a nonexistent PBI each fail `PBI-DEPS-RESOLVABLE`.
  - A cycle finding names the participating PBI identifiers, not just the fact of a cycle.
  - A valid graph produces a persisted resolved-graph projection; adding or removing an edge produces a different `PlanVersionId`.
  - No dependency rule consults integration state or any PBI status — validation is purely structural at this stage.
- **Blocked by**: 01
- **Parallelizable with**: 02, 03, 05, 06

---

**05 — Dependency Readiness evaluated against Git**

- **What to build**: Implement the readiness predicate consumed at dispatch. A PBI is dependency-ready only when every prerequisite's state is `integrated` or `externally_integrated` **and** the dependent's starting base actually contains each prerequisite's integrated changes, verified against the real Git repository rather than a status field. An unmet prerequisite produces `dependency_not_ready` naming the specific prerequisite and which of the two conditions failed, and the PBI rests in `awaiting_dependency` — a scheduling state distinct from `awaiting_operator`. Expose the predicate through the core so the execution loop calls it rather than reimplementing it.
- **Acceptance criteria**:
  - Dispatch of a dependent whose prerequisite is `implementation_complete` is rejected `dependency_not_ready`; so is one whose prerequisite has passing gates and an open Pull Request.
  - Dispatch of a dependent whose prerequisite is `integrated` but whose starting base predates the integration is rejected, proving the second condition is evaluated independently of the first.
  - Dispatch succeeds once the prerequisite is integrated and the base contains it; until then the PBI is `awaiting_dependency` and never `awaiting_operator`.
  - The rejection names the unmet prerequisite and the failing condition.
  - Two dependency-ready PBIs are both eligible concurrently; a dependent of an unintegrated PBI is not.
  - Readiness is computed at evaluation time and never read from a persisted readiness field.
- **Blocked by**: 01; needs "the applicable target" and starting-base resolution under the Git Workflow Policy from `git-integration`; needs the PBI integration states (`integrated`, `externally_integrated`) and the `awaiting_dependency` scheduling state from `execution-core`'s state machine.
- **Parallelizable with**: 02, 03, 04, 06

---

**06 — Planning Approval and dispatch gating**

- **What to build**: Implement `plan.approve` as an operator-only operation bound to a specific `PlanVersionId`, recording actor provenance, channel, execution rule snapshot, and the proposal exactly as presented so an audit can reconstruct what the operator saw. Approval covers behavior, story coverage, granularity, and dependencies as one decision. An approval attempted through the MCP channel is rejected `operator_channel_required`; an agent result asserting approval creates no record; a stale version is rejected `approval_version_mismatch`. Wire the dispatch precondition: builder dispatch requires a recorded approval for the *current* plan version, so passing lint never authorizes work. Surfaces: a CLI approval command, and one MCP parity test proving the channel rejection.
- **Acceptance criteria**:
  - `plan.approve` from an MCP channel is rejected `operator_channel_required`; from an interactive CLI session it succeeds.
  - An agent result payload asserting approval produces no approval record and no state change.
  - Approving a superseded or otherwise stale `PlanVersionId` is rejected `approval_version_mismatch`.
  - The approval record stores the snapshot identity and the presented proposal content.
  - Builder dispatch without a recorded approval for the current plan version is rejected with a typed code; a fully passing lint result does not satisfy the precondition.
  - Editing a PBI's criteria after approval produces a new plan version identity and leaves the prior approval no longer current.
- **Blocked by**: 01; needs the operator-channel rule and `operator_channel_required` rejection from `execution-core`; needs the snapshot identity from `config-and-snapshot`.
- **Parallelizable with**: 02, 03, 04, 05

---

**07 — Change classification and Plan Amendment**

- **What to build**: Implement the classification of a proposed plan change into `behavioral` or `internal`, and the `plan.amend` operation. Anything touching recorded behavior, criteria, contracts, dependencies, or decomposition is behavioral by default and requires operator-only `plan.amend`, producing a new plan version with `supersedes` set and retaining the prior version. `internal` proceeds automatically only when behavior, contracts, criteria, dependencies, and decomposition are all preserved, and records its rationale. Amendment invalidates and reruns exactly the validations its changes affect — readiness for a changed spec, lint for changed PBIs, gate results for PBIs whose criteria or contracts changed — while unaffected PBIs continue running. An agent proposes a change; it can never edit the approved plan.
- **Acceptance criteria**:
  - A behavioral change requires `plan.amend`, produces a new version with `supersedes` pointing at the prior one, and the prior version remains retrievable.
  - An amendment invalidates only the affected validations, and a test proves an unaffected PBI keeps running through it.
  - An amendment touching a PBI's criteria returns that PBI's gate results to pending; an amendment touching only another PBI does not.
  - An internal change proceeds without operator involvement and persists its classification with its rationale.
  - A change proposal asserting `internal` while altering criteria, contracts, dependencies, or decomposition is reclassified as behavioral and blocked pending approval.
  - An agent attempting to write the approved plan directly is rejected; only a proposal is accepted.
- **Blocked by**: 06; needs the gate result invalidation hook from `entropy-gate`; needs snapshot migration semantics from `config-and-snapshot` where an amendment coincides with a rule change.
- **Parallelizable with**: 02, 03, 04, 05 (once 06 lands)

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Operation core `invoke`, request/outcome shapes, record families, rejection codes | `execution-core` | 01, 02, 03, 04, 05, 06, 07 |
| Operator channel rule and `operator_channel_required` | `execution-core` | 06, 07 |
| PBI integration states (`integrated`, `externally_integrated`) and the `awaiting_dependency` scheduling state | `execution-core` | 05 |
| Slicer role task and result payload contract | `gtp-protocol` | 01 |
| Criterion identity rule (required, never generated, stable) and the normalized spec model | `spec-validation` | 01, 02 |
| Normalized content hashing (line endings) | `data-handling` | 01 |
| Redaction sink enforcement interface | `data-handling` | 01, 02, 03 (every persisted proposal/finding) |
| Execution Rule Snapshot identity; Initial Context Budget value; file-count threshold; assumed model window | `config-and-snapshot` | 02, 03, 06 |
| Snapshot migration invalidation semantics | `config-and-snapshot` | 07 |
| Artifact Location Mapping schema | `repository-readiness` | 01 |
| Approved verification command reference (`ApprovedCommandRef`) | `repository-readiness` | 02 |
| "The applicable target" and starting-base resolution under Git Workflow Policy | `git-integration` | 05 |
| Gate result invalidation hook | `entropy-gate` | 07 |
| MCP schema derivation from operation schemas | `mcp-server` | 06 (parity test only) |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| **Plan version hash definition** (hash inputs, ordering, normalization) | 01 | `pbi-execution-loop` (dispatch gating), `baseline-transitions` |
| `ProposedPbi` shape and the persisted plan proposal record | 01 | `gtp-protocol` (slicer result payload), `pbi-execution-loop`, `baseline-transitions` (transition declared per PBI), `dashboard` |
| Story coverage map projection | 01, 02 | `dashboard` |
| `ContextEstimate` shape and the upper-bound budget comparison | 03 | `pbi-execution-loop` (continuity package evaluation at handoff), `dashboard` (estimated vs observed fields), `harness-adapters` (later margin calibration against reported measurements) |
| Resolved dependency graph projection | 04 | `pbi-execution-loop`, `dashboard` |
| Dependency Readiness predicate and `dependency_not_ready` rejection | 05 | `pbi-execution-loop` (dispatch eligibility condition 1) |
| Planning approval record and the dispatch-requires-approval precondition | 06 | `pbi-execution-loop` (dispatch eligibility condition 2), `baseline-transitions` (approving the plan approves the transition declaration), `dashboard` |
| Plan amendment record, `supersedes` chain, and the validation-invalidation contract | 07 | `entropy-gate` (gate results returned to pending), `baseline-transitions`, `dashboard` |

### Risks / judgement calls

**The file-count threshold has no clear owner.** Spec 09 states "exceeding five files" but `config-and-snapshot` §configuration shape lists only watermark and PBI context budget under context policy. I have written slice 02 to read the threshold from config, which likely requires spec 02 to add the field. If the operator prefers it hardcoded, slice 02 shrinks slightly — but then user story 10 ("the threshold visible in the warning") is satisfied with a constant, which is weaker.

**Slices 04 and 05 were tempting to merge** into one "dependencies" slice. I kept them apart because 04 is pure structural validation with no Git and no cross-spec blocker, while 05 needs `git-integration`'s applicable-target contract and a real temporary repository with actual integration history. Merging would let 05's blocker stall 04, which is the cheapest and most parallelizable work in the spec.

**Slice 03 carries the continuity-package evaluator** even though the handoff that triggers it lives in `pbi-execution-loop`. My reading of the spec is deliberate on this — "there is no separate smaller allowance for continuity" is a property of the budget evaluator, not of the handoff. Putting it here means spec 11 calls one function. If the operator prefers the evaluator to be budget-only and spec 11 to assemble the continuity package, the "no separate allowance" test moves to spec 11 and becomes harder to prove.

**Slice 07 is the only one with a real blocking chain** (after 06). I considered making classification independent of approval so it could run in parallel, but a change classification has no meaning without an approved baseline to be classified against — the `internal` branch is defined as "preserves the approved plan." The chain is genuine, not conservative.

**Slice 01 is doing a lot for a bootstrap slice** — proposal persistence, version identity, and coverage map derivation. I kept them together because the coverage map is an input to the hash and splitting them would mean two slices editing the same identity definition. It is the slice most likely to want splitting if it proves too large in practice; the natural cut would be "persist the proposal" from "derive and hash the version," at the cost of publishing the plan version hash contract one slice later, which delays specs 11 and 15.

**`PBI-BUDGET` and `PBI-DEPS-RESOLVABLE` live outside slice 02**, so slice 02 ships a lint command that does not yet run every declared rule. Each rule is independently demoable, and the rule set is data with stable identities, so adding two rules is additive rather than a rewrite. A reviewer who wants `gantry lint-pbi` complete on first delivery should merge 02, 03, and 04 — but that is one large slice and three concurrent agents become one.
