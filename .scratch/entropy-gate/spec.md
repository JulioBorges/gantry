# Entropy gate: differential decision, integrity, and correction

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 13, wave 4)
Source: `PRD.md` §7.5, §6.2
Created: 2026-09-11

## Problem Statement

`PRD.md` names invisible architectural debt as the third bottleneck: code that passes its tests while
introducing forbidden coupling or a layer violation. The obvious response — require a clean report before
merging — fails immediately on any real repository, because existing debt would block every slice and the
gate would be turned off within a week.

So the decision has to be differential: block what this delivery introduces or aggravates relative to the
current target, leave existing debt visible but unremediated. `PRD.md` sets that policy precisely, and
attaches four constraints that are each easy to violate.

Individual evaluation. "Findings are evaluated individually; improvements elsewhere cannot offset a
blocking regression or mandatory violation through an aggregate score." A quality score would let a
delivery buy its way past a violation.

Absolute rules survive. "This differential policy does not waive configured absolute mandatory rules:
their violations remain blocking regardless of origin." A committed secret is not acceptable because it was
already there.

Consolidation, not a second audit. The gate "consumes the evidence produced by the configured
architecture and quality checks" and "does not perform a duplicate independent audit or introduce another
autonomous reviewer role". When the optional adversarial critic is enabled it "may only add" findings and
"cannot replace deterministic evidence, clear its findings, or bypass mandatory checks".

Verification integrity. An agent may improve tests, but "removing or disabling a mandatory check, reducing
verification of approved criteria, or weakening an assertion to circumvent a failure requires explicit
operator review", and "a green result obtained through unapproved weakening cannot authorize merge".

And the comparison is fragile: "a changed target or candidate invalidates the comparison and requires
revalidation". Mechanisms are deferred throughout — "measurable checks and finding matching across
revisions remain to be specified", "evidence schema, check adapters, and consolidation interfaces remain
to be specified", "detection rules and evidence requirements remain to be specified" for integrity.

## Solution

The gate is a decision function over matched evidence, not an analyzer. Deterministic checks run first
against both the current target revision and the merge candidate under identical rules and tool versions.
Their findings are matched by problem identity from spec 12, and each matched pair is classified
individually: introduced, aggravated, preexisting, or improved. Introduced and aggravated findings at or
above the configured blocking severity block. Preexisting findings are recorded and do not. Improvements
are recorded and credit nothing.

Absolute mandatory rules are evaluated outside the differential: any violation in the candidate blocks
regardless of whether the target has it too.

Verification integrity is checked as a comparison of its own — the collected mandatory test set and the
enabled check configuration between target and candidate. A removed, skipped, or disabled mandatory check
is an integrity finding that blocks until an operator approves the change. Semantic weakening of an
assertion is not deterministically detectable, and the spec says so rather than implying it is covered.

When adversarial review is enabled, it runs after the deterministic layer, receives its findings, and can
only add. A valid review with no blockers is then required alongside deterministic passing; an unavailable
or failed critic leaves the gate pending with no static-only fallback.

Findings that block produce correction within the PBI's shared allowance. Exhaustion fails the gate. Any
change to the candidate or the target invalidates the decision and requires a fresh comparison.

## User Stories

1. As an operator, I want a delivery blocked for the problems it introduces, so that quality does not erode slice by slice.
2. As an operator, I want existing debt left alone, so that adopting the gate does not require fixing my whole repository first.
3. As an operator, I want an aggravated problem treated as introduced, so that making something worse is not free.
4. As an operator, I want each finding judged on its own, so that improvements elsewhere cannot offset a regression.
5. As an operator, I want no aggregate quality score, so that nothing can be bought past the gate.
6. As an operator, I want the blocking finding named concretely, so that I know exactly what to fix.
7. As an operator, I want preexisting findings visible in the result, so that I can see my debt without being forced to fix it.
8. As an operator, I want improvements recorded, so that progress is visible even though it credits nothing.
9. As an operator, I want absolute mandatory rules to block regardless of origin, so that a preexisting secret is not acceptable.
10. As an operator, I want absolute rules configurable per rule, so that I decide which violations are never tolerable.
11. As an operator, I want the gate to consume my checks' evidence rather than re-auditing, so that there is one source of findings.
12. As an operator, I want no additional autonomous reviewer role introduced, so that the gate is a decision rather than another agent.
13. As an operator, I want evidence reused only when revision, rules, and tool versions match, so that stale results cannot decide a gate.
14. As an operator, I want fresh evidence obtained when any of those change, so that I do not have to track it.
15. As an operator, I want missing or invalid comparison evidence to leave the gate unapproved, so that an absent report is not read as clean.
16. As an operator, I want a pass-or-fail-only check to satisfy its mandatory role without establishing non-regression, so that its limits are respected.
17. As an operator, I want the target evidence taken from the current target revision, so that the comparison baseline is real.
18. As an operator, I want a changed target to invalidate the decision, so that approval is never carried across an advancing branch.
19. As an operator, I want a changed candidate to invalidate the decision, so that any edit is revalidated.
20. As an operator, I want the deterministic layer to run first and always, so that it is the floor rather than an option.
21. As an operator, I want the optional adversarial critic to only add findings, so that it cannot clear a deterministic one.
22. As an operator, I want a critic blocker to flip the gate and a warning to be advisory, so that severity means something.
23. As an operator, I want an enabled critic's valid review required before the gate can pass, so that enabling it is meaningful.
24. As an operator, I want an unavailable or failed critic to leave the gate pending rather than falling back to static-only, so that a failure is not a silent downgrade.
25. As an operator, I want a critic infrastructure failure to spend the infrastructure allowance rather than a correction attempt, so that budgets stay distinct.
26. As an operator, I want a critic protocol failure not reclassified as infrastructure, so that a malformed result is handled as what it is.
27. As an operator, I want the spec-preparation Requirement Critic unaffected by whether delivery review is enabled, so that the two reviewers stay separate.
28. As an operator, I want agents free to add or improve tests, so that the gate does not discourage better verification.
29. As an operator, I want a removed or disabled mandatory check detected, so that a green result cannot come from deleting the check.
30. As an operator, I want a skipped mandatory test detected, so that skipping is not a quiet workaround.
31. As an operator, I want reduced verification of an approved criterion detected, so that coverage cannot shrink silently.
32. As an operator, I want an integrity finding to block until I explicitly approve the change, so that weakening is my decision.
33. As an operator, I want a green result obtained through unapproved weakening unable to authorize merge, so that the outcome does not reward it.
34. As an operator, I want the limits of integrity detection stated honestly, so that I know semantic assertion weakening is not deterministically caught.
35. As an operator, I want blocking findings to trigger correction within my PBI's allowance, so that the factory attempts a fix before stopping.
36. As an operator, I want the initial evaluation to consume no attempt, so that my allowance pays for corrections.
37. As an operator, I want revalidation after each correction, so that a fix is verified rather than assumed.
38. As an operator, I want exhausted attempts to fail the gate and stop automatic correction, so that the factory stops rather than looping.
39. As an operator, I want merge to remain prohibited after a failed gate, so that a stopped correction cannot proceed.
40. As an operator, I want the gate result to record which rules, tool versions, and revisions produced it, so that the decision is reconstructible.
41. As an operator, I want passing feature tests alone to be insufficient, so that tests are a floor rather than the whole gate.
42. As a host harness, I want the gate result as structured data with each finding's classification, so that I can present and act on it.
43. As an auditor, I want every gate decision traceable to its evidence and rule snapshot, so that I can explain any authorized merge.

## Implementation Decisions

### The decision function

```ts
type GateSubject = {
  unit: RepositoryExecutionUnitId;
  pbi: PbiId;
  targetRevision: string;
  candidateRevision: string;
  snapshot: SnapshotId;
};

type FindingClassification2 =
  | { kind: "introduced"; finding: NormalizedFinding }
  | { kind: "aggravated"; finding: NormalizedFinding; previousSeverity: Severity }
  | { kind: "preexisting"; finding: NormalizedFinding }
  | { kind: "improved"; problemIdentity: string; previousSeverity: Severity };

type GateDecision = {
  subject: GateSubject;
  classifications: FindingClassification2[];
  absoluteViolations: NormalizedFinding[];
  integrityFindings: IntegrityFinding[];
  adversarial?: { submissionId: string; addedFindings: NormalizedFinding[]; blockers: number };
  outcome: "passed" | "failed" | "blocked_incomplete_evidence" | "blocked_infrastructure" | "pending_review";
  blockingReasons: Array<{ reason: string; problemIdentity?: string }>;
  evidence: Array<{ report: string; role: "target" | "candidate" }>;
};
```

There is no score field, no total, and no netting. `blockingReasons` is a list of individual causes, so a
decision can never be explained as an average.

`aggravated` is defined as a finding whose problem identity exists in the target but whose severity is
higher in the candidate, or — for identities matched by count per spec 12 — whose count increased. Both
are treated exactly as `introduced` for blocking purposes.

Blocking threshold is configured per check purpose, defaulting to `blocker` and `major`. `minor` and
`info` findings are recorded and do not block unless the rule is absolute.

### Absolute rules

Rules configured as absolute are evaluated outside the comparison: any occurrence in the candidate blocks,
present in the target or not. This is the one place existing debt is not tolerated, and it is opt-in per
rule so the operator decides which violations are categorically unacceptable — typically committed
secrets, known-critical vulnerabilities, and license incompatibilities.

An absolute violation cannot be corrected away by classification and cannot be offset. It appears in
`absoluteViolations` separately from the differential classifications so the two are never confused.

### Consolidation, not audit

The gate runs no analysis of its own. It requests evidence from the configured checks in spec 12 for both
revisions, matches, classifies, and decides. Evidence is reused only when `subjectRevision`,
`ruleSetVersion`, `toolVersion`, and the command reference all match what is being assessed; otherwise a
fresh run is requested.

Target evidence is obtained against the current target revision at decision time, not a cached earlier
one, because the target advances as other PBIs integrate. A change to either revision after the decision
invalidates it: the gate returns to `pending` per spec 01's gate state machine and a fresh comparison runs.

Invalid or missing required comparison evidence yields `blocked_incomplete_evidence`. It is never
interpreted as zero findings. A `pass_fail` check satisfies its mandatory role and contributes nothing to
the differential.

### Verification integrity

A comparison of the verification itself, between target and candidate:

```ts
type IntegrityFinding = {
  kind:
    | "mandatory_check_removed"
    | "mandatory_check_disabled"
    | "mandatory_test_skipped"
    | "mandatory_test_removed"
    | "criterion_coverage_reduced"
    | "assertion_shape_weakened";   // warning severity; heuristic, see below
  severity: "blocker" | "warning";
  detail: string;
  approvedBy?: ActorProvenance;    // an operator-approved change clears the finding
};
```

Detection compares two things that are both machine-readable: the set of collected mandatory test
identities reported by the test adapters, and the enabled check configuration. A mandatory test present in
the target's collection and absent or skipped in the candidate's, a check disabled in the candidate's
configuration, or an approved criterion losing its covering verification entry, each produce an integrity
finding.

Integrity findings block until an operator explicitly approves the change, through the operator channel in
spec 01. An approved change records the provenance and clears the finding for that candidate. A green
result produced by an unapproved weakening cannot authorize merge, because the integrity finding is itself
a blocking reason independent of the check results.

Agents remain free to add or strengthen tests: only reduction is a finding.

**Assertion weakening: three layers, in increasing strength.** A test changed from an equality assertion
to a presence assertion still runs, still passes, and still covers its criterion, so none of the five
blocking kinds above catch it. Three mechanisms address it, and their honesty differs:

1. **Assertion shape comparison** — always on, `warning` only. The candidate's modified test files are
   compared against the target's by assertion count per test and by matcher class, ordered from
   discriminating (equality, structural match) to permissive (truthiness, definedness, no-throw). A drop
   produces `assertion_shape_weakened`. This is a syntactic heuristic and is evadable by anyone who
   intends to evade it — extract a helper, rename a matcher, restructure the test. It costs nothing and
   catches the careless case, which is why it is a warning rather than a blocker.

2. **Adversarial critic escalation** — automatic, not global. When the candidate modifies test files
   covering approved criteria, the adversarial critic is required for that PBI even when
   `gates.adversarial.mode` is `static`. The operator opted into a static-only delivery review, not into
   an unreviewed change to the verification itself, and this is the one condition that overrides the
   setting. Its findings land under `spec-deviation` or `scope-creep` as usual.

3. **Mutation comparison** — deterministic, opt-in, from spec 12. A mutant that the target's tests killed
   by assertion and the candidate's tests no longer kill is a surviving mutant, which arrives as an
   ordinary `NormalizedFinding` with `rule: "mutation:<operator>"` and is classified `introduced` by the
   same differential logic as everything else. No special case in this spec. This is the only one of the
   three that measures verification strength rather than inferring it, and it is the reason the gap is
   now bounded rather than open.

The limit that remains, stated rather than implied: with the mutation adapter disabled, layers 1 and 2 are
a heuristic and a reviewer opinion. Neither is deterministic, and a repository that wants a deterministic
answer has to enable layer 3 and accept its cost. Claiming that layers 1 and 2 close the gap would be
exactly the overstatement the PRD review corrected in the security and architecture tables.

### Adversarial review

Order is fixed: deterministic first, always, as the floor. Then, when
`gates.adversarial.mode = static_and_llm`, the critic receives a GTP envelope containing the PBI, the
constitution and ADR references, the diff reference, and the deterministic findings already produced.

Its result may only add findings in the four allowed classes, and its payload has no field capable of
clearing or downgrading a deterministic one — enforced by shape in spec 03. A `blocker` severity flips the
gate; a `warning` records an advisory event only.

When enabled, a valid review with no blockers is required in addition to the deterministic layer passing.
An unavailable critic, a failed execution, or a missing or malformed result leaves the gate `pending_review`
and records the failure. There is no automatic fallback to static-only. Infrastructure failures spend the
infrastructure allowance from spec 02; protocol failures follow spec 03 and are not reclassified as
infrastructure.

The Requirement Critic in spec 08 is unaffected by this setting. The two reviewers review different
subjects at different times, and the PRD review specifically corrected the impression that they share an
opt-in.

### Correction

The initial gate evaluation consumes no correction attempt. Each blocking outcome eligible for correction
dispatches a correction assignment, consuming one attempt from the PBI's shared allowance at dispatch per
spec 01, followed by revalidation with fresh evidence.

Exhaustion with unresolved blocking findings moves the gate to `failed`, stops automatic correction, and
keeps merge prohibited. Further attempts require an explicit operator grant. Integrity findings and
absolute violations are correctable in principle — a removed test can be restored, a secret can be
removed — but an integrity finding cleared by operator approval rather than by correction consumes no
attempt, since nothing was corrected.

## Testing Decisions

**What makes a good test here.** Tests construct target and candidate evidence as data, drive
`gate.evaluate` through the core, and assert on the classification of each finding, the outcome, and the
list of blocking reasons. Constructing evidence directly is the right level: spec 12 proves that adapters
produce it correctly, and this spec proves that the decision over it is correct. Duplicating adapter
parsing here would test spec 12 twice and this spec not at all.

**The seam.** Unchanged: `core.invoke`. A scripted check adapter returns the constructed reports, and a
scripted harness driver returns adversarial critic results including clean, blocking, warning-only,
malformed, and absent.

**Modules under test.** Classification of introduced, aggravated, preexisting, and improved findings;
severity thresholds; absolute rule evaluation; evidence reuse and invalidation; incomplete evidence
blocking; target revision currency; integrity comparison and its approval clearing; adversarial ordering,
add-only enforcement, severity handling, and failure behavior; correction dispatch, attempt accounting, and
exhaustion.

**Scenarios that must exist**, from PRD §14.3 item 4:

- A finding present in the candidate and absent from the target is `introduced` and blocks at the configured severity.
- The same finding present in both is `preexisting` and does not block.
- A finding whose severity rose is `aggravated` and blocks; one whose count rose is also `aggravated`.
- A finding removed in the candidate is `improved` and credits nothing.
- One introduced blocker alongside five improvements still fails, and the decision carries no score or total.
- A `minor` introduced finding does not block unless its rule is absolute.
- An absolute-rule violation present in both target and candidate blocks.
- An absolute violation appears separately from the differential classifications.
- The gate performs no analysis of its own, verified by a check adapter fake that fails the test if invoked outside the evidence requests.
- Evidence is reused when revision, rules, tool version, and command match, and a fresh run is requested when any differs.
- Target evidence is taken against the current target revision; a target that advanced after the previous decision produces a fresh comparison.
- A target advancing after a `passed` decision returns the gate to `pending`.
- Any candidate change returns the gate to `pending`.
- A finding missing required fields yields `blocked_incomplete_evidence`, never zero findings.
- A `pass_fail` check satisfies its mandatory role and contributes no classification.
- Passing mandatory tests with an introduced architecture blocker still fails.
- A mandatory test present in the target's collection and skipped in the candidate's is an integrity finding that blocks despite all checks passing.
- A check disabled in the candidate configuration is an integrity finding.
- An approved criterion losing its covering verification entry is an integrity finding.
- An operator approval clears an integrity finding, records provenance, and consumes no correction attempt; a non-operator channel cannot clear it.
- Adding or strengthening a test produces no integrity finding, and produces no assertion-shape warning.
- An equality assertion changed to a presence assertion produces `assertion_shape_weakened` at warning severity, which does not block on its own.
- The same change with the mutation adapter enabled produces surviving mutants classified `introduced`, which do block.
- A candidate modifying test files that cover approved criteria requires the adversarial critic even when the global mode is `static`.
- A candidate touching no test file does not trigger that escalation.
- A mutation finding is classified by the ordinary differential logic, with no special case in the gate.
- With the critic disabled, review is static-only and the Requirement Critic in spec 08 is unaffected.
- With the critic enabled, the deterministic layer runs first; a clean deterministic result plus a critic blocker fails.
- A critic warning records an advisory event and does not block.
- A critic result cannot clear or downgrade a deterministic finding, demonstrated by the absence of any such field.
- An absent, malformed, or failed critic yields `pending_review` with the failure recorded and no static-only fallback.
- A critic infrastructure failure spends the infrastructure allowance; a malformed result does not.
- The initial evaluation consumes no correction attempt; each correction dispatch consumes exactly one.
- Five corrections followed by an unresolved blocker yields `failed`, stops correction, and leaves merge prohibited.
- An operator grant permits further attempts without resetting the count.

## Out of Scope

- **Evidence production, parsing, identity derivation, matching primitives, stability, resources** (spec 12): this spec consumes matched evidence.
- **Operations, gate state machine, budget accounting, channels** (spec 01) and **thresholds, absolute rule configuration, snapshot** (spec 02).
- **Envelope contracts and the critic payload shape** (spec 03).
- **Requirement review of specs** (spec 08): a different reviewer on a different subject.
- **Approved command definitions and coverage declarations** (spec 06).
- **Correction implementation** (spec 11): this spec decides that correction is warranted and accounts for the attempt; dispatching the builder and running the loop is spec 11's.
- **Merge authorization, candidate preparation, conflict resolution, provider checks** (spec 14): a passed gate is a precondition, not an authorization.
- **Changing rules, tools, or coverage** (spec 15): this spec binds decisions to versions; changing them is a baseline transition.
- **Redaction of findings and reports** (spec 04).

Out of scope by product decision:

- An aggregate quality score. §7.5 forbids offsetting through one, and the glossary marks it as a term to avoid.
- Requiring remediation of existing debt in every PBI. §7.5 states existing debt remains visible without requiring remediation.
- A second autonomous reviewer role beyond the optional adversarial critic. §7.5 explicitly rules it out.
- A static-only fallback when an enabled critic fails. §7.5 point 4 forbids it.
- Deterministic detection of semantic assertion weakening. Stated as a gap rather than claimed.
- LLM findings as a substitute for deterministic evidence. §7.5 forbids it.

## Further Notes

**Binding decisions.** ADR-0002 is why the decision is bound to a specific candidate and target and
invalidated by a change to either: serialized integration means the target moves between decisions, and a
gate result that survived that movement would be exactly the stale approval the ADR exists to prevent.

**Glossary alignment.** Entropy Gate, Quality Regression, Comparison Evidence, Adversarial Review, and
Correction Attempt follow `CONTEXT.md`, including the terms it marks to avoid: the entropy gate is not a
feature test suite and not a secret entropy scan; a quality regression is not all existing debt and not an
aggregate score; adversarial review is not a replacement for deterministic gates; a correction attempt is
not an individual gate execution or the initial evaluation.

**Glossary gap for `/domain-modeling`.** Absolute mandatory rule, integrity finding, and blocking reason
are introduced here without entries and should get them.

**Where the risk actually sits.** Assertion weakening is now bounded rather than open, but the bound
depends on a setting. With the mutation adapter enabled there is a deterministic answer: a test that stops
discriminating stops killing mutants, and the finding blocks like any other. With it disabled — the
default — what remains is a syntactic warning that an intentional actor evades trivially, plus a reviewer
whose escalation is automatic but whose judgment is not deterministic. That is a real improvement over an
open gap, and it is not the same thing as coverage.

The consequence worth watching is that the warning-level `assertion_shape_weakened` finding could create
exactly the false confidence the previous version of this spec warned against. A repository seeing the
warning fire and clear repeatedly may conclude the case is handled when the deterministic layer is off.
The projection should therefore surface whether the mutation adapter is enabled alongside the warning, so
the strength of the answer is visible with the answer.

The second risk is threshold configuration. Defaulting to blocking on `blocker` and `major` will produce
friction on repositories whose linters classify aggressively, and the pressure will be to lower the
threshold globally rather than fix the rule configuration. Per-purpose thresholds exist so the adjustment
can be targeted, but the failure mode to watch for is an operator setting everything to `blocker`-only and
quietly losing the architecture signal.

**Sequencing note.** This spec depends entirely on spec 12's matched evidence and is the precondition for
spec 14. The classification rules — particularly what counts as aggravated — are the piece to settle
first, because the integrity comparison and the correction loop both branch on them.
