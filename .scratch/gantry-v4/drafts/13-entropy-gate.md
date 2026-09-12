## Spec 13 — entropy-gate

This spec owns the **Entropy Gate**: the differential decision over already-produced Comparison Evidence for a merge candidate against its current target. It classifies each matched finding individually — introduced, aggravated, preexisting, improved — evaluates absolute mandatory rules outside that differential, runs a verification-integrity comparison of the mandatory test set and enabled check configuration, optionally consolidates an add-only Adversarial Review, and decides whether correction is warranted within the PBI's Correction Budget. It produces no analysis of its own and no aggregate score. The risk sits in three places. First, **classification correctness is the whole spec** — "aggravated" (severity raised, or count raised under spec 12's count fallback) is the rule everything else branches on, and getting it wrong either blocks every delivery or blocks none. Second, **fail-closed discipline is easy to erode**: missing evidence, a stale target revision, a failed critic, and an unapproved verification weakening must each leave the gate unapproved, and each is a separate place where a convenient default would silently approve. Third, **assertion weakening is bounded, not covered** — layer 1 is an evadable syntactic warning and layer 2 is a reviewer opinion; only the opt-in mutation adapter is deterministic, and the projection has to make that visible so the warning does not manufacture confidence it has not earned.

### Slices

---

**01 — Gate decision record and differential classification**

- **What to build**: The tracer bullet through the whole spec. Define the gate decision record family in SQLite (subject: unit, PBI, target revision, candidate revision, snapshot identity; classifications; blocking reasons; evidence references), register the `gate.evaluate` handler on the shared operation core, and implement matching-and-classification over target and candidate reports supplied as evidence. Each matched problem identity is classified individually as introduced, aggravated, preexisting, or improved; aggravated means the identity exists in the target but at lower severity in the candidate, or — for identities matched by count under spec 12's no-location fallback — at a lower count, and it is treated exactly as introduced for blocking. Per-check-purpose blocking severity thresholds apply (default `blocker` and `major`), `minor` and `info` are recorded only, and the decision carries no score, total, or netting anywhere in its shape or its persistence. The decision is surfaced as structured data through the core's read projection with per-finding classification and an explicit list of blocking reasons, and is written through the redaction sink.
- **Acceptance criteria**:
  - A finding present in the candidate and absent from the target classifies `introduced` and fails the gate at the configured threshold; the same identity present in both classifies `preexisting` and does not.
  - A finding whose severity rose classifies `aggravated` and blocks; a count-matched identity whose count rose also classifies `aggravated`; a finding absent from the candidate classifies `improved` and changes no outcome.
  - One introduced blocker alongside five improvements still fails, and no field in the persisted decision or the projection holds a score, total, or count that could express netting.
  - A `minor` introduced finding does not block; the outcome names each blocking cause individually with its problem identity.
  - A surviving-mutant finding (`rule: "mutation:<operator>"`) is classified by the same differential path with no branch specific to mutation.
  - The persisted decision records the snapshot identity, both revisions, and the rule and tool versions that produced each report; one parity test proves a transport delegates the read rather than reimplementing it.
- **Blocked by**: None. Needs the normalized finding shape and problem-identity derivation (including the no-symbol and no-location fallbacks) from `verification-adapters`, and the gate state machine plus `gate.evaluate` catalog entry from `execution-core`; both can be stubbed to their published shapes to start.
- **Parallelizable with**: —

---

**02 — Absolute mandatory rules and fail-closed evidence handling**

- **What to build**: The two paths that sit outside the differential. Rules flagged absolute are evaluated against the candidate alone: any occurrence blocks whether or not the target has it, and violations are recorded in a field separate from the differential classifications so the two can never be conflated or offset. Separately, evidence that is missing or invalid — a finding lacking rule, path, severity, or problem identity, or a report lacking subject revision, tool version, rule-set version, or declared coverage — yields a distinct blocked-on-incomplete-evidence outcome and is never read as zero findings. A `pass_fail` check outcome satisfies its mandatory role and contributes no classification to the differential.
- **Acceptance criteria**:
  - An absolute-rule violation present in both target and candidate blocks the gate.
  - Absolute violations appear in the decision separately from the differential classifications, and no code path routes one through classification.
  - A report with a finding missing any required field yields the incomplete-evidence outcome, not a passing decision and not zero findings.
  - A `pass_fail` outcome for a mandatory check satisfies the mandatory role, produces no classification, and cannot on its own establish non-regression.
  - A check purpose whose absolute-rule set is empty behaves identically to the pre-slice behavior, proving the path is additive.
- **Blocked by**: 01 (the decision record and classification pipeline it writes into). Needs the evidence-completeness required-field list and the `pass_fail` outcome variant from `verification-adapters`, and the absolute-rule and threshold configuration section from `config-and-snapshot`.
- **Parallelizable with**: 03, 04, 06

---

**03 — Evidence consolidation: reuse, target currency, and invalidation**

- **What to build**: How the gate gets its evidence without becoming an analyzer. The gate requests check results for both revisions from the configured checks, reusing an existing report only when the subject revision, rule-set version, tool version, and approved command reference all match what is being assessed, and requesting a fresh run otherwise. Target evidence is always obtained against the *current* target revision at decision time, because the target advances as other PBIs integrate. Any subsequent change to the candidate revision, the target revision, or the rule version returns the gate to `pending` and requires a fresh comparison, with the prior decision retained as history rather than carried forward.
- **Acceptance criteria**:
  - A report matching on revision, rules, tool version, and command is reused; changing any one of the four triggers a fresh run request.
  - Target evidence is requested against the current target revision; a target that advanced since the previous decision produces a fresh comparison rather than reusing the earlier target report.
  - A target advancing after a passing decision returns the gate to `pending`; any candidate change does the same.
  - A check adapter fake that fails the test when invoked outside an evidence request proves the gate runs no analysis of its own.
  - Declared coverage travels with each reused or freshly obtained report into the decision.
- **Blocked by**: 01. Needs the check adapter interface and its run input/outcome shapes from `verification-adapters`, and the approved command reference from `repository-readiness`.
- **Parallelizable with**: 02, 04, 06

---

**04 — Verification integrity comparison, assertion-shape warning, and operator approval**

- **What to build**: The comparison of the verification itself between target and candidate, producing integrity findings that block independently of whether every check passed. Deterministic kinds: a mandatory check removed or disabled in the candidate's configuration, a mandatory test removed or skipped relative to the target's collected test set, and an approved acceptance criterion losing its covering verification entry. On top of those, an always-on warning-severity assertion-shape comparison over the candidate's modified test files — assertion count per test and matcher class ordered from discriminating to permissive — which is a syntactic heuristic and is labelled as one. This slice also produces the **covered test-change set**: which candidate-modified test files cover which approved criteria, used here for coverage reduction and consumed by slice 05. An integrity finding blocks until an operator explicitly approves the change through the operator channel, which records provenance and clears that finding for that candidate only. The projection surfaces whether the mutation adapter is enabled alongside any assertion-shape warning, so the strength of the answer is visible with the answer.
- **Acceptance criteria**:
  - A mandatory test present in the target's collected set and skipped in the candidate's is an integrity finding that blocks the gate even when every check passes.
  - A check disabled in the candidate configuration, and an approved criterion losing its covering verification entry, each produce an integrity finding.
  - Adding or strengthening a test produces neither an integrity finding nor an assertion-shape warning; changing an equality assertion to a presence assertion produces an assertion-shape warning at warning severity that does not block on its own.
  - An operator approval through the operator channel clears a named integrity finding and records provenance; the same request through a non-operator channel is rejected with the operator-channel-required rejection.
  - A green check result accompanied by an unapproved integrity finding cannot produce a passing gate.
  - The projection shows, next to any assertion-shape warning, whether the mutation adapter is enabled for that check configuration.
- **Blocked by**: 01. Needs the **collected mandatory test identity set, with per-test skip status, reported by `mandatory_test` adapters** from `verification-adapters` (see risks — this output is not in that spec's published report shape); criterion identity from `spec-validation`; the PBI criteria list carrying its spec criterion references from `slicing-and-approval`; declared coverage entries from `repository-readiness`; and the operator channel assertion from `execution-core`.
- **Parallelizable with**: 02, 03, 06

---

**05 — Adversarial review: ordering, add-only, and failure behavior**

- **What to build**: The optional review layer, which never runs before the deterministic layer. When the configured mode enables it, the critic receives a task envelope containing the PBI, constitution and ADR references, the diff reference, and the deterministic findings already produced; its result may only add findings in the four allowed classes, and the payload shape itself has no field capable of clearing or downgrading a deterministic finding. A critic blocker fails the gate; a critic warning records an advisory event only. When enabled, a valid review with no blockers is required in addition to the deterministic layer passing — an unavailable critic, a failed execution, or a missing or malformed result leaves the gate awaiting review with the failure recorded and no fallback to static-only. This slice also owns **critic requirement resolution**: the review is required when the global mode enables it, *or* automatically when the candidate modifies test files covering approved criteria, which overrides a global `static` setting for that PBI.
- **Acceptance criteria**:
  - The deterministic layer runs first in every configuration; a clean deterministic result plus a critic blocker fails the gate, and a critic warning records an advisory event without blocking.
  - A critic result cannot clear or downgrade a deterministic finding, demonstrated by the absence of any such field in the accepted payload rather than by a runtime check.
  - An absent, malformed, or failed critic leaves the gate awaiting review with the failure recorded; no path produces a passing static-only decision when the critic is required.
  - A critic infrastructure failure spends the infrastructure allowance; a malformed result is handled as a Protocol Failure and spends neither the infrastructure allowance nor a correction attempt.
  - A candidate modifying test files that cover approved criteria requires the critic even when the global mode is static; a candidate touching no such test file does not trigger the escalation.
  - With the critic disabled, review is deterministic-only and the Requirement Critic in `spec-validation` is unaffected by this setting.
- **Blocked by**: 01, and 04 for the covered test-change set that the automatic escalation keys on. Needs the `adversarial_critic` task and result contracts and the Protocol Failure semantics from `gtp-protocol`, the infrastructure retry allowance and failure classification from `execution-core`, and the adversarial mode setting from `config-and-snapshot`.
- **Parallelizable with**: 06 (and with 02, 03 once 04 lands)

---

**06 — Correction loop: subject derivation, attempt accounting, and exhaustion**

- **What to build**: What happens after a decision blocks. The gate derives a correction subject from its blocking reasons — the concrete findings to fix, named individually — and dispatches a correction assignment, consuming exactly one attempt from the PBI's shared allowance at dispatch, followed by revalidation with fresh evidence. The initial evaluation consumes nothing. An integrity finding cleared by operator approval rather than by correction consumes no attempt, because nothing was corrected. Exhaustion with unresolved blocking findings moves the gate to failed, stops automatic correction, and keeps merge prohibited; an operator grant permits further attempts additively without resetting the count.
- **Acceptance criteria**:
  - The initial gate evaluation consumes no correction attempt; each correction dispatch consumes exactly one, at dispatch.
  - The correction subject names each blocking finding individually and carries no aggregate framing.
  - Revalidation after a correction obtains fresh evidence rather than reusing the pre-correction candidate report.
  - Attempts exhausted with an unresolved blocker yields a failed gate, stops automatic correction, and leaves merge prohibited.
  - An operator grant permits further attempts and the consumed count does not reset.
  - An operator-approved integrity finding is cleared with no attempt consumed.
- **Blocked by**: 01. Needs the correction budget accounting rule (consumed at dispatch) and the `correction.dispatch` / `correction.grantAttempts` operations from `execution-core`.
- **Parallelizable with**: 02, 03, 04, 05

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Normalized finding shape and problem-identity derivation (rule + path + symbol + content anchor), with the no-symbol and no-location count fallbacks | `verification-adapters` | 01, 02 |
| Structured report shape (subject revision, tool version, rule-set version, command, declared coverage) and the `pass_fail` outcome variant | `verification-adapters` | 01, 02, 03 |
| Check adapter interface and evidence run request/outcome | `verification-adapters` | 03 |
| Evidence-completeness required-field list, and the operator finding classification escape scoped to one finding in one report version | `verification-adapters` | 02 |
| Collected mandatory test identity set with per-test skip status, from `mandatory_test` adapters | `verification-adapters` | 04 — **not currently in that spec's published report shape** |
| Mutation finding rule namespace and the mutation-adapter-enabled state for a check configuration | `verification-adapters` | 01 (classification), 04 (projection) |
| Gate state machine and the `gate.evaluate` operation catalog entry | `execution-core` | 01 |
| Operator channel assertion and the operator-channel-required rejection | `execution-core` | 04, 06 |
| Correction budget accounting consumed at dispatch; `correction.dispatch`, `correction.grantAttempts` | `execution-core` | 06 |
| Infrastructure retry allowance and the failure classification table | `execution-core` | 05 |
| Redaction sink enforcement interface | `data-handling` | 01 (every subsequent slice writes through it) |
| Execution rule snapshot identity and its binding on gate results | `config-and-snapshot` | 01, 03 |
| Gate blocking-threshold, absolute-rule, and adversarial-mode configuration section | `config-and-snapshot` | 02, 05 |
| `adversarial_critic` task and result envelope, restricted to four finding classes with no clearing field | `gtp-protocol` | 05 |
| Protocol Failure semantics, not reclassifiable as infrastructure | `gtp-protocol` | 05 |
| Approved verification command reference and its declared coverage | `repository-readiness` | 03, 04 |
| Criterion identity (required, stable, never generated) | `spec-validation` | 04 |
| PBI acceptance criteria list carrying spec criterion references | `slicing-and-approval` | 04 |
| Candidate and current-target revision pair for a PBI | `git-integration` | 01, 03 (tests construct it as data, so it does not block) |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Specs waiting on it |
|---|---|---|
| **Aggravated classification rules** — severity raised, or count raised under the count fallback; both treated as introduced | 01 | Internal to 04 and 06; read by `baseline-transitions` |
| Gate decision structured result: per-finding classification, individual blocking reasons, no score field | 01 | `git-integration` (references a specific passing decision), `dashboard`, `mcp-server`, `demo-mode` |
| Gate outcome vocabulary, including the awaiting-review outcome for a required-but-unavailable critic | 01, 02, 05 | `execution-core` (its gate state machine must admit it), `dashboard`, `git-integration` |
| Passing-gate precondition for merge authorization | 01 | `git-integration` |
| Integrity finding shape and its operator-approval clearing with provenance | 04 | `git-integration` (merge prohibition), `dashboard` |
| Mutation-adapter-enabled visibility alongside the assertion-shape warning | 04 | `dashboard` |
| Adversarial review requirement resolution: global mode plus automatic escalation on covered test-file changes | 05 | `config-and-snapshot` (mode field semantics), `harness-adapters` / `gtp-protocol` (dispatch), `dashboard` |
| Correction subject derived from individual blocking reasons | 06 | `pbi-execution-loop` (dispatches the builder; content is mine) |

### Risks / judgement calls

1. **A missing upstream contract.** Spec 13's integrity comparison needs "the set of collected mandatory test identities reported by the test adapters", including skip status. Spec 12's published `StructuredReport` has no such field — it has `findings`, and a skipped test is not a finding. Slice 04 cannot be built without this. Either spec 12 adds a collected-test-set output to the `mandatory_test` adapter contract, or spec 13 defines it and spec 12 implements it. I recommend the former (identity derivation and tool-output parsing are 12's) and flagged it as a blocker on 04 rather than silently assuming a shape.

2. **An outcome value spec 01's gate state machine does not have.** Spec 13's decision outcome union includes `pending_review`; spec 01's gate states are `pending`, `evaluating`, `passed`, `failed`, `blocked_incomplete_evidence`, `blocked_infrastructure`. A required-but-unavailable critic needs somewhere to land. This is a one-line addition to 01's state machine, but someone must make it rather than each spec assuming the other did.

3. **Config section not enumerated.** Spec 02's configuration shape lists budgets, capacity, Git policy, verification commands, data handling, dashboard — it does not enumerate gate blocking thresholds, absolute-rule flags, or `gates.adversarial.mode`, all of which spec 13 declares out of scope as 02's. Slices 02 and 05 need those keys to exist. Same resolution question as above.

4. **Slice 04 is the biggest and I was tempted to split it.** Assertion-shape comparison is arguably its own slice: it is a different mechanism (syntactic heuristic over modified test files) from the five deterministic integrity kinds (set comparison over collected tests and configuration). I kept them together because `assertion_shape_weakened` is a variant of the same integrity finding type, both need the same covered test-change set, and splitting would have added a third blocking edge for an agent to wait on. If 04 proves too large in practice, the natural cut is: deterministic integrity kinds + operator approval in one slice, assertion-shape warning + covered test-change set + mutation visibility in another, with 05 then blocked by the second.

5. **The one real blocking chain is 04 → 05.** Slice 05's automatic escalation keys on "the candidate modifies test files covering approved criteria", which is the same predicate slice 04 needs for coverage reduction. I put the predicate in 04 rather than duplicating it. Everything else fans out from 01, so the shape is 01 → {02, 03, 04, 06} → 05. If 05 needs to start earlier, an agent can build critic ordering, add-only enforcement, severity handling, and failure behavior against the global mode alone, and land the escalation criterion once 04 is in.

6. **Who supplies the candidate and target revisions is genuinely ambiguous.** Spec 11 owns the PBI worktree branch, spec 14 owns the merge candidate and the current target, and spec 14 is blocked by 13 in the map. Since tests construct the gate subject as data, this does not block any slice, but the production wiring has no declared owner and will surface at integration time.

7. **The correction boundary with spec 11.** Spec 11 says "what to correct is spec 13's", so I gave slice 06 the correction-subject derivation and the attempt accounting; spec 11 keeps the builder dispatch and the loop. The seam is a correction subject handed to `correction.dispatch`. If spec 11's issues take a different view, this is where the two will collide.

8. **Ordering of 02 and 03 after 01.** Both amend the same decision path. They are genuinely independent in behavior but will touch adjacent code, so two agents running them concurrently will likely conflict textually even though they do not conflict semantically. I judged the parallelism worth the merge cost; an operator who disagrees should sequence 03 after 02.
