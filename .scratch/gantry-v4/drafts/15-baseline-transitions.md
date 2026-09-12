# Spec 15 — baseline-transitions

Type: issue-breakdown draft
Status: proposal (not published as issues)
Spec: [`.scratch/baseline-transitions/spec.md`](../../baseline-transitions/spec.md)
Map: [`.scratch/gantry-v4/map.md`](../map.md) (spec 15, wave 4)
Created: 2026-09-12

## Spec 15 — baseline-transitions

This spec owns the Governance Baseline Transition: the declared, approved, evidenced path by which a
repository changes the tools, versions, rules, or verification coverage that its quality checks are built
on. It owns three mechanisms and nothing else — the governance-path permission that lets an approved
transition PBI edit files ordinary assignments may not touch, the transition manifest that identifies the
old and proposed configurations and explains their coverage and finding differences, and the adoption
decision that makes the proposed configuration authoritative going forward without touching historical
evidence. The risk is concentrated in two places. First, self-approval: the delivery introducing a
transition must be judged by the configuration in force when it started, while still being allowed to
*run* the proposed checks to produce evidence — a distinction that is easy to collapse into one code path
and impossible to detect once collapsed. Second, the comparison's honesty: `reducesCoverage` must be
computed from both configurations rather than asserted, a rule mapping supplied by an adapter or an
operator can silently carry a preexisting finding across a rename it does not actually correspond to, and
the `new_only` case has no baseline at all and must record that absence explicitly rather than let it read
as zero findings.

### Slices

- **01 — Transition declaration and governance-path permission**
- **What to build**: Establish the Governance Baseline Transition as a persisted record with a lifecycle
  (declared → evidence gathered → adopted | abandoned), registered against the shared operation core's
  record families and state machine, and add the transition operations to the core's operation catalog
  rather than creating a parallel surface. A PBI declares a transition during planning with the affected
  categories, the exact governance paths it may change, and a rationale; the declaration is validated at
  plan proposal (paths must resolve inside the repository's protected governance set, must be non-empty,
  must not be wildcards) and is carried by Planning Approval. The declared paths are then materialized as
  an explicit permission on every assignment for that PBI, published as the contract spec 03's protection
  rule reads. An assignment for a PBI with no declaration carries no permission at all, and an assignment
  for a transition PBI carries exactly the declared paths and no more.
- **Acceptance criteria**:
  - A result from an ordinary assignment reporting a change under a protected governance path is a
    violation; the same change under an assignment carrying a declaration that names that path is accepted.
  - A declaration naming one ADR path yields a permission that rejects a change to the constitution,
    proving the permission is path-scoped and not category-scoped.
  - A declaration with an empty path list, a path outside the protected governance set, or a glob is
    rejected at plan proposal with a typed rejection code.
  - Approving the plan records the declaration as approved intent; no adoption record exists and the old
    configuration remains authoritative after approval alone.
  - The transition record and its declaration are written through the redaction sink and carry the actor
    provenance and snapshot identity of the approval.
  - The transition PBI is schedulable, dispatchable, and gateable through the same states as any other PBI
    — no alternate workflow exists.
- **Blocked by**: needs the *protected governance path set and the permission-honoring protection rule*
  from `gtp-protocol`; needs the *plan declaration and plan version binding* from `slicing-and-approval`;
  needs the *operation catalog, record families, actor provenance and operator-only channel* from
  `execution-core`; needs the *redaction sink enforcement interface* from `data-handling`.
- **Parallelizable with**: none (bootstrap for this spec)

---

- **02 — Transition manifest: configurations, comparison mode, and coverage change**
- **What to build**: Build the manifest for a declared transition. Identify the old configuration from the
  execution's captured Execution Rule Snapshot and the proposed configuration from the transition PBI's
  changes — commands, tool versions, rule sets, coverage declarations. Determine the comparison mode by
  actually attempting both configurations against one representative subject revision, not by inspecting
  the declaration: `both_run` when both execute and produce parseable Comparison Evidence, `new_only` when
  no prior check existed (with the absence recorded as an explicit reason, never as a zero-finding report),
  `old_only` when the proposed configuration cannot execute, `neither` when neither can. Record both report
  identities and the single subject revision they share. Compute the coverage change — added, removed,
  unchanged — from the declared coverage of both configurations, deriving `reducesCoverage` from the removed
  set rather than accepting an assertion, and surface a reducing transition distinctly in the manifest.

  ```ts
  type ComparisonMode =
    | { kind: "both_run" }
    | { kind: "new_only"; absenceReason: string }
    | { kind: "old_only"; reason: string }
    | { kind: "neither" };
  ```
- **Acceptance criteria**:
  - `both_run` produces a manifest whose old and new reports share one `subjectRevision`, with both report
    identities recorded.
  - `new_only` records a non-empty absence reason and leaves the old report identity unset; no report with
    zero findings is synthesized for the missing prior check.
  - A proposed check that executes but emits unparseable evidence yields a manifest marked as not adoptable,
    distinct from a check that does not execute at all.
  - `old_only` and `neither` are recorded with their reason and mark the manifest not adoptable.
  - A transition removing a coverage declaration computes `reducesCoverage: true` with the removed entries
    listed; a transition adding coverage computes `reducesCoverage: false`. The flag is never taken from
    input.
  - A manifest is refused when the two reports were produced against different subject revisions.
- **Blocked by**: 01; needs the *structured report shape including `toolVersion`, `ruleSetVersion`,
  `declaredCoverage` and adapter failure classification* from `verification-adapters`; needs the *baseline
  configuration content of a snapshot (approved commands, tool versions, rule sets)* from
  `config-and-snapshot`.
- **Parallelizable with**: 04

---

- **03 — Finding change across configurations: rule mappings and the count fallback**
- **What to build**: Compute the finding difference between the old and new reports in a `both_run`
  manifest. Findings match on problem identity directly where the rule identifier is unchanged, since
  identity already excludes the message and derives the enclosing symbol. Where a configuration renames or
  splits a rule, a rule mapping bridges the two identifiers; the adapter supplies it where it knows one and
  an operator supplies it through an operator-only operation otherwise, with the source recorded on every
  mapping. Where a rule changed identifier and no mapping exists, fall back to comparing counts per rule and
  path, and mark on the manifest that the comparison relied on the fallback so a reader knows the difference
  is not attributable to individual occurrences. Report `newlySurfaced` and `noLongerSurfaced` counts derived
  from the matched set.
- **Acceptance criteria**:
  - A proposed configuration that rewords messages without renaming rules produces a full identity-level
    comparison with no mappings recorded and no fallback flag.
  - A renamed rule with an adapter-supplied mapping produces a full comparison, with the mapping recorded
    and `source: "adapter"`.
  - A renamed rule with an operator-supplied mapping produces the same comparison with `source: "operator"`;
    the mapping operation is refused from a non-operator channel.
  - A renamed rule with no mapping produces per-rule, per-path counts and sets the manifest's fallback
    indicator; `newlySurfaced` is derived from the count delta and no occurrence is attributed.
  - A mapping naming a rule absent from either configuration is rejected rather than silently ignored.
  - `newlySurfaced` and `noLongerSurfaced` are recomputed from evidence on every manifest read and never
    persisted as independently mutable values.
- **Blocked by**: 02; needs the *normalized finding shape, problem identity derivation, and its documented
  fallback order* from `verification-adapters`; needs the *adapter-supplied rule mapping across tool
  versions* from `verification-adapters`.
- **Parallelizable with**: 04, 05

---

- **04 — Old-baseline evaluation of the introducing delivery**
- **What to build**: Make the Entropy Gate decision for a transition PBI use the configuration in force
  when the PBI started, while still permitting the proposed checks to run as manifest evidence. Three rules,
  enforced structurally rather than by convention: the gate's baseline selection resolves to the execution's
  captured snapshot for a transition PBI regardless of any proposed configuration in scope; findings produced
  only by the proposed configuration are excluded from Quality Regression classification for that delivery
  and are recorded as the preexisting baseline the new check will carry forward once adopted; and the
  proposed configuration cannot clear, downgrade, or reclassify a finding the old configuration produces
  against the delivery. Publish the baseline-selection contract the Entropy Gate consumes.
- **Acceptance criteria**:
  - A transition PBI's gate decision records the old snapshot identity as its governing configuration, even
    when a proposed configuration is present in the manifest.
  - A finding surfaced only by the proposed check does not appear as introduced or aggravated in the
    transition PBI's gate decision and does not block it.
  - A finding produced by the old configuration against the transition PBI still blocks when at or above the
    blocking severity; a proposed rule that would exempt it has no effect on the outcome.
  - Findings surfaced by a `new_only` check are recorded as the preexisting baseline for that check and are
    not attributed as regressions to the PBI that added it.
  - The proposed configuration's reports are retained as manifest evidence even though they did not
    participate in the gate decision, and are distinguishable from gate evidence by role.
  - An absolute mandatory rule in the old configuration still blocks, and the transition provides no path to
    waive it.
- **Blocked by**: 01; needs the *gate subject, its snapshot binding, and the introduced / aggravated /
  preexisting classification semantics* from `entropy-gate`.
- **Parallelizable with**: 02, 03

---

- **05 — Adoption, refusal, and abandonment**
- **What to build**: Add the operator-only adoption operation, referencing a specific manifest. Adoption is
  refused when the comparison mode blocks, when required evidence is incomplete, when the proposed
  configuration failed to execute or produced unparseable evidence, when the manifest's transition PBI has
  not reached implementation completion, or when the request arrives on a non-operator channel. A successful
  adoption records the approving actor and time, produces a new Execution Rule Snapshot from the proposed
  configuration, and marks the transition adopted. Abandonment is the symmetric terminal decision: it retains
  the manifest and all its evidence as a record of what was evaluated, leaves the old configuration
  authoritative, and is itself irreversible for that manifest. Neither operation rewrites, reclassifies, or
  removes any existing finding or evidence record.
- **Acceptance criteria**:
  - Adoption of a manifest whose mode is `old_only` or `neither` is refused with a typed rejection code
    naming the mode.
  - Adoption with a missing or unparseable required report is refused; the refusal is distinguishable from a
    refusal for blocked mode.
  - Adoption from an agent channel is refused with `operator_channel_required`; the same request from an
    operator channel succeeds.
  - A successful adoption produces a new snapshot identity distinct from the old one and records it on the
    manifest alongside the approving actor's provenance.
  - Findings, reports, approvals, and Merge Authorizations recorded before adoption are byte-identical
    afterward and remain bound to their original snapshot identity.
  - An abandoned manifest retains its configurations, comparison mode, and evidence; a later adoption attempt
    against it is refused; the old configuration remains the authoritative baseline.
- **Blocked by**: 02; needs *snapshot identity and immutable snapshot creation from a supplied
  configuration* from `config-and-snapshot`; needs *operator-only channel enforcement* from `execution-core`.
- **Parallelizable with**: 03, 04

---

- **06 — Post-adoption effect, in-flight migration, and transport surface**
- **What to build**: Make adoption take effect with the scope the spec requires. A new execution created
  after adoption captures the new snapshot and runs under the new baseline. An execution already in flight
  continues under its captured snapshot and moves only when the operator explicitly requests migration to the
  adopted baseline, which delegates to the snapshot migration in spec 02 and consequently invalidates
  affected approvals and returns affected gates to pending. Expose the manifest and its comparison as a
  structured read — configurations, mode, coverage change, finding change, mapping sources, fallback
  indicator, adoption record — so a surface can present the decision without parsing prose. Add one parity
  test each for the CLI and MCP transports proving delegation to the operation core.
- **Acceptance criteria**:
  - An execution created after adoption captures the new snapshot identity; an execution created before it
    continues under its own, with no state change caused by adoption.
  - The explicit migration request moves a named in-flight execution to the adopted snapshot, invalidates the
    approvals its rules affect, and returns affected gates to pending; unaffected records stay bound to their
    original snapshot.
  - No code path migrates an execution as a side effect of adoption; a test asserting in-flight snapshot
    identity after adoption passes without any migration call.
  - Migration requested from a non-operator channel is refused.
  - The structured manifest read returns every field needed to explain the decision, including which mappings
    were operator-supplied and whether the count fallback was used, and is available as a read operation
    without a capability token.
  - One CLI parity test and one MCP parity test each prove the transport delegates to the core operation and
    asserts no transition behavior of its own.
- **Blocked by**: 05; needs *snapshot migration with its approval-invalidation classification* from
  `config-and-snapshot`; needs *transport parity harness and the MCP schema derivation rule* from
  `mcp-server`.
- **Parallelizable with**: none (terminal)

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Protected governance path set, and the protection rule that honors an explicit permission | `gtp-protocol` | 01 |
| Plan declaration carried by Planning Approval; plan version binding | `slicing-and-approval` | 01 |
| Operation catalog extension, record families, state machine registration, actor provenance, operator-only channel and `operator_channel_required` | `execution-core` | 01, 05, 06 |
| Redaction sink enforcement interface | `data-handling` | 01 |
| Structured report shape (`subjectRevision`, `toolVersion`, `ruleSetVersion`, `declaredCoverage`, command reference) and adapter failure classification | `verification-adapters` | 02 |
| Normalized finding shape, problem identity derivation, and documented fallback order | `verification-adapters` | 03 |
| Adapter-supplied rule mapping across tool versions | `verification-adapters` | 03 |
| Baseline configuration content captured in an Execution Rule Snapshot | `config-and-snapshot` | 02, 05 |
| Snapshot identity and immutable snapshot creation from a supplied configuration | `config-and-snapshot` | 05 |
| Snapshot migration and its approval-invalidation classification | `config-and-snapshot` | 06 |
| Gate subject, its snapshot binding, and introduced / aggravated / preexisting classification semantics | `entropy-gate` | 04 |
| Transport parity harness and MCP schema derivation from operation schemas | `mcp-server` | 06 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| **Governance-path permission in a transition declaration** (the handoff's locked item) | 01 | `gtp-protocol` (its protection rule reads it) |
| Governance Baseline Transition record and lifecycle states | 01 | `execution-core` (record family registration), `dashboard` |
| Transition manifest shape: configurations, comparison mode, coverage change, finding change | 02, 03 | `dashboard` (presentation), `entropy-gate` (evidence roles) |
| Baseline-selection rule for a transition PBI's gate decision | 04 | `entropy-gate` |
| Newly added check's findings as the preexisting baseline going forward | 04 | `entropy-gate`, `verification-adapters` |
| Operator-supplied rule mapping operation and its recorded source | 03 | `verification-adapters` (adapters supply the other source) |
| Adoption producing a new snapshot, and the explicit migration request | 05, 06 | `config-and-snapshot` |

### Risks / judgement calls

**Coverage change folded into slice 02 rather than standing alone.** The `reducesCoverage` computation and
its prominent surfacing carry real weight — it is the guard against a weakening presented as an improvement
— and I was tempted to give it its own slice. I folded it into 02 because it derives entirely from the two
configurations that slice already captures, and a standalone slice would have been a thin horizontal cut
over data another slice owns. If the operator wants the weakening signal to get its own reviewed PBI,
splitting 02 into "configurations and mode" / "coverage change" is a clean cut with no other consequence.

**Slice 04 is the one I would not merge.** It is the structural answer to self-approval and it sits at the
boundary with the Entropy Gate, which makes it tempting to hand to spec 13 instead. I kept it here because
the rule is about *which* baseline judges a delivery, which this spec owns, while spec 13 owns *how* the
chosen baseline decides. But the seam is real and the two slices will need to agree on one contract; if spec
13's issues are written first and already define baseline selection, slice 04 shrinks to consuming it.

**Operation naming is not settled by the spec.** Spec 15 describes adoption as "an operator-only operation"
but spec 01's v1 catalog contains no baseline operations. I assumed slice 01 adds them to the existing
catalog rather than creating a parallel surface, following the handoff's guidance for spec 03. The actual
names need a decision alongside spec 01's issues.

**No CLI command is named anywhere in the spec.** I put the transport surface in slice 06 as a parity test
only, consistent with the standing test seam. If the operator expects a user-facing `gantry` command for
adoption — which seems likely, since adoption is operator-only and the operator channel is an interactive
CLI session or a dashboard token — that command's surface design is currently unowned by any spec and should
be settled before slice 06 is picked up.

**The adoption precondition on implementation completion is my inference.** The spec says adoption is refused
when the mode blocks, evidence is incomplete, or the proposed configuration failed to execute. It does not
say whether a transition can be adopted before its PBI is integrated. I added the precondition in slice 05
because adopting a configuration whose defining files are not yet on the target would make the new snapshot
reference content that does not exist there. That is a judgement call worth confirming.

**Blocking chain depth.** The chain is 01 → 02 → 05 → 06, with 03 and 04 hanging off in parallel. Four deep
is more than I would like for a six-slice spec. The unavoidable part is that adoption needs a manifest and
migration needs an adoption. If the chain needs shortening, slice 05's adoption preconditions could be built
against a manifest fixture in parallel with 02, at the cost of a later integration step.

**This spec is the least urgent of wave 4.** A repository runs governed execution for a long time without
changing its baseline. The one piece that should not wait is slice 01's governance-path permission, because
`gtp-protocol` references it and would otherwise have to be specified twice — it is on the handoff's
lock-before-issues table for exactly that reason.
