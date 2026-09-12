# Verification adapters: checks, evidence, stability, and resources

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 12, wave 3)
Source: `PRD.md` §7.5, §14.1, §6.3
Created: 2026-09-11

## Problem Statement

The entropy gate's whole argument is comparative: block what a delivery introduces or aggravates, leave
existing debt alone. That comparison needs findings that can be matched across two revisions, and `PRD.md`
is precise about why exit codes cannot do it — "exit codes alone cannot distinguish preexisting problems
from new or aggravated findings". A check that only succeeds or fails "may still serve as a mandatory
pass/fail check but cannot independently establish non-regression".

So every comparative check must produce structured findings with a rule, a location, a severity, and a
problem identity, bound to the revision, the rules, and the tool version that produced them. Matching is
the hard part: a finding's line number moves when unrelated code is edited, so identity cannot include
it, and two findings from the same rule in the same file must still be distinguishable.

Three further requirements sit on top. Incomplete evidence must fail closed — "missing or invalid required
comparison evidence leaves the entropy gate unapproved and prevents merge; it must not be interpreted as
zero findings" — with a narrow, auditable operator classification escape. Flakiness must be a recorded
problem rather than something reruns hide: "known or observed flakiness is recorded as a check problem
and cannot be hidden by unlimited reruns". And resources must be coordinated, because "separate Git
worktrees alone do not establish isolation" of a port or a database, and "resource identities must reflect
the actual shared resource rather than assuming different repositories are independent".

Everything mechanical is deferred: "the exact report schema and finding identity/matching strategy",
"classification schema and adapter conformance rules", "stability evidence and flaky-result
representation", "resource declaration, allocation, locking scope, and crash reconciliation".

## Solution

One adapter interface wraps each supported tool, running an approved command against a specified revision
and returning a structured report of normalized findings or a typed adapter failure. Adapters own the
translation from each tool's native output — ESLint JSON, Vitest JSON, Ruff JSON, dependency-cruiser JSON,
pip-audit JSON, Gitleaks JSON — into one finding shape, so the gate never parses tool output.

Problem identity deliberately excludes line numbers. It is derived from the rule, the normalized path, the
enclosing symbol where the tool reports one, and a fingerprint of the finding's message, with per-key
counting as the fallback when a tool gives no symbol. That makes a finding matchable across revisions
without being invalidated by unrelated edits.

A finding missing any required field is invalid evidence and the gate stays unapproved. The only escape is
an operator classification scoped to one finding in one report version, recorded as auditable evidence
that never rewrites tool output and is invalidated when the revision, rule version, or finding changes.

Each check declares its environment, inputs, isolation requirements, and a stability criterion, and a single
passing run counts only when it satisfies that criterion. Repeated inconsistent outcomes become a recorded
check problem. Each check also declares its resources with an explicit sharing scope — machine, unit, or
worktree — and Gantry locks at the declared scope, which is what lets a port be recognized as shared
across clones.

## User Stories

1. As an operator, I want my existing tools used rather than replaced, so that Gantry checks what my team already checks.
2. As an operator, I want each supported tool's native output translated into one finding shape, so that comparison works across tools.
3. As an operator, I want each finding to carry its rule, location, and severity, so that I can act on it.
4. As an operator, I want each finding to carry a problem identity, so that the same problem is recognizable across revisions.
5. As an operator, I want problem identity independent of line numbers, so that editing unrelated code does not make old findings look new.
6. As an operator, I want two findings of the same rule in the same file distinguishable, so that fixing one and introducing another is visible.
7. As an operator, I want each report bound to the revision it examined, so that evidence cannot be attributed to the wrong code.
8. As an operator, I want each report bound to the rule version and tool version, so that a tool upgrade does not silently change a comparison.
9. As an operator, I want a finding missing a required field treated as invalid evidence, so that incomplete output does not read as clean.
10. As an operator, I want invalid evidence to leave the gate unapproved, so that failing closed is the default.
11. As an operator, I want to classify a specific incomplete finding when I judge it acceptable, so that a tool's limitation does not block me permanently.
12. As an operator, I want that classification scoped to one finding in one report version, so that it cannot silently cover anything else.
13. As an operator, I want my classification recorded as evidence rather than rewriting tool output, so that the audit trail shows what the tool actually said.
14. As an operator, I want a classification invalidated when the revision, rule version, or finding changes, so that it cannot outlive its context.
15. As an operator, I want a pass-or-fail-only command usable as a mandatory check, so that a tool without structured output is still useful.
16. As an operator, I want such a command unable to establish non-regression, so that the comparison is not built on an exit code.
17. As an operator, I want each check to declare what it actually covers, so that I am not told security is handled when only secrets are scanned.
18. As an operator, I want the coverage declaration shown wherever the check's evidence appears, so that the limitation travels with the result.
19. As an operator, I want each check to declare its execution environment and inputs, so that a result is reproducible.
20. As an operator, I want each check to declare a stability criterion, so that "green once" means something specific.
21. As an operator, I want a single passing run accepted only when it satisfies the declared criterion, so that a flaky check cannot pass by luck.
22. As an operator, I want observed inconsistency recorded as a check problem, so that flakiness is visible rather than absorbed.
23. As an operator, I want reruns bounded by the check's approved policy, so that a green result cannot be manufactured by repetition.
24. As an operator, I want repeated inconsistent outcomes to leave the gate unapproved, so that an unreliable check blocks until it is fixed.
25. As an operator, I want flakiness distinguished from infrastructure failure, so that an unstable test is not retried as a network problem.
26. As an operator, I want each check to declare the resources it needs, so that conflicts are predictable.
27. As an operator, I want a resource's sharing scope declared explicitly, so that a port is known to be shared across my whole machine.
28. As an operator, I want checks needing the same machine-scoped resource serialized even across clones, so that two repositories do not collide on one port.
29. As an operator, I want resources isolated per execution where that is possible, so that serialization is a fallback rather than the norm.
30. As an operator, I want separate worktrees never treated as sufficient isolation, so that the real conflict is addressed.
31. As an operator, I want resource coordination applied to target and candidate validation alike, so that comparison runs do not collide either.
32. As an operator, I want a crashed process's resource lock reclaimable safely, so that a crash does not require manual cleanup.
33. As an operator, I want an adapter failure distinguished from a check finding, so that a broken tool is not reported as a code problem.
34. As an operator, I want an adapter failure classified as infrastructure or permanent, so that retries are spent only where they can help.
35. As an operator, I want a check that runs and reports findings treated as working, so that existing debt does not look like a broken setup.
36. As an operator, I want my package manager respected, so that a proposed command works in my repository.
37. As an operator, I want reports reused only when revision, rules, and tool versions all match, so that stale evidence cannot pass a gate.
38. As an operator, I want new evidence obtained automatically when any of those change, so that I do not have to remember.
39. As a Gantry maintainer, I want one adapter interface per tool with a conformance test, so that adding a tool is a bounded piece of work.
40. As a Gantry maintainer, I want the demo's stub adapter to satisfy the same interface, so that the demo exercises the real seam.
41. As an auditor, I want every report stored with its command, revision, rules, tool version, and coverage, so that a gate decision is reconstructible.

## Implementation Decisions

### The adapter interface and the finding shape

```ts
type CheckAdapter = {
  tool: { id: string; version: string };
  supports: CheckPurpose[];                 // mandatory_test | architecture | security | dependency | license
  run(input: CheckRun): Promise<CheckOutcome>;
};

type CheckRun = {
  command: ApprovedCommandRef;              // approved in spec 06, bound to the snapshot
  subject: { unit: RepositoryExecutionUnitId; revision: string; worktreePath: string };
  resources: AllocatedResource[];
};

type CheckOutcome =
  | { kind: "report"; report: StructuredReport }
  | { kind: "pass_fail"; passed: boolean; evidence: string }        // cannot establish non-regression
  | { kind: "adapter_failure"; classification: "infrastructure" | "permanent"; detail: string };

type StructuredReport = {
  subjectRevision: string;
  toolVersion: string;
  ruleSetVersion: string;
  command: ApprovedCommandRef;
  declaredCoverage: string;
  findings: NormalizedFinding[];
  producedAt: string;
};

type NormalizedFinding = {
  rule: string;
  path: string;                             // repository-relative, normalized separators
  symbol?: string;                          // enclosing symbol, derived by Gantry — see below
  severity: "blocker" | "major" | "minor" | "info";
  absolute: boolean;                        // violates a configured absolute mandatory rule
  contentAnchor?: string;                   // hash of the normalized reported line plus k neighbours
  messageFingerprint: string;               // display and diagnosis only, never part of identity
  problemIdentity: string;
  location?: { line: number; column?: number };   // for display only, never part of identity
};
```

`location` exists for the operator and is explicitly excluded from identity. `pass_fail` is a first-class
outcome so a tool without structured output is usable as a mandatory check while being structurally
incapable of feeding the comparison.

### Problem identity and matching

Identity is `rule` + normalized `path` + `symbol` + `contentAnchor`. Two things follow from that
composition, and both are deliberate.

**The message is not part of identity.** A finding's message text is display and diagnosis only. Including
it would mean that a tool upgrade rewording its output changes every identity at once, making every
preexisting finding look introduced and rendering the comparison worthless exactly when a baseline
transition needs it most. `messageFingerprint` is still computed — volatile parts removed, so it is
stable across runs of one version — because it is useful for grouping and display, but it never enters
`problemIdentity`.

**`symbol` is derived by Gantry, not taken from the tool.** The adapter layer resolves the enclosing
symbol from the file and reported line using a language-agnostic parser (tree-sitter, with grammars for
the languages in the approved adapter set). This removes the dependency on each tool reporting a symbol,
which is what previously forced most findings onto a count-based fallback. Tree-sitter is therefore an
engine dependency, shared by every adapter rather than reimplemented per tool.

**`contentAnchor`** is a hash over the normalized reported line plus a fixed number of neighbouring lines,
with whitespace collapsed and indentation removed. It distinguishes two occurrences of the same rule
within the same symbol, and it survives edits elsewhere in the file. When the anchored code itself
changes, the identity changes — which is correct rather than a defect: the finding is now about different
code.

Fallbacks, applied in order and recorded on the finding so a consumer knows which was used:

1. **No symbol** — the language has no grammar available. Identity is `rule` + `path` + `contentAnchor`.
2. **No line** — the tool reports no location at all. Identity is `rule` + `path`, and matching is by
   count per identity: target two, candidate three means one introduced finding; target two, candidate
   one is a recorded improvement crediting nothing.

Fallback 2 is the only place where "fixing one and introducing another" cannot be attributed to a specific
occurrence, and it now applies only to tools that emit no location — a much narrower case than before.
Line and column numbers are excluded from identity throughout, because including them would make every
finding in an edited file look new.

### Evidence completeness

A finding lacking `rule`, `path`, `severity`, `problemIdentity`, or a report lacking `subjectRevision`,
`toolVersion`, `ruleSetVersion`, or `declaredCoverage`, is invalid evidence. The gate stays unapproved. It
is never interpreted as zero findings.

```ts
type FindingClassification = {
  reportVersion: string;          // identity of the exact report
  problemIdentity: string;        // the single finding classified
  decision: "accept_incomplete" | "treat_as_preexisting";
  actor: ActorProvenance;         // operator-only channel
  rationale: string;
  invalidatedBy?: "revision_changed" | "rule_version_changed" | "finding_changed";
};
```

A classification is operator-only, additive evidence beside the tool's output, and never a rewrite of it.
It covers one finding in one report version. It is invalidated automatically when the assessed revision,
the rule version, or the finding itself changes. There is no global waiver and no rule-level suppression —
those would make the differential policy unfalsifiable, which the PRD review explicitly guarded against
when it separated tool validity from differential debt.

### Stability

```ts
type StabilityCriterion =
  | { kind: "single_run" }
  | { kind: "consecutive"; runs: number }
  | { kind: "quorum"; runs: number; agreeing: number };

type CheckStabilityDeclaration = {
  environment: Record<string, string>;      // variable names and declared values, never secrets
  inputs: string[];                         // paths and configuration the result depends on
  isolation: "per_execution" | "serialized" | "none";
  criterion: StabilityCriterion;
  observedInstability?: Array<{ observedAt: string; outcomes: string[] }>;
};
```

A passing run counts only when it satisfies the criterion. Reruns follow the check's approved policy, not
an unbounded loop, and are separate from the infrastructure retry allowance — an unstable check is a check
problem, not an infrastructure failure, and conflating them is how flakiness gets absorbed.

Observed inconsistency is appended to `observedInstability` and surfaces as a check problem. Repeated
inconsistent outcomes leave the dependent gate unapproved until the check is reviewed or its approved
configuration changes, which is a governance baseline transition in spec 15.

### Resources

```ts
type CheckResourceDeclaration = {
  kind: "port" | "database" | "temp_directory" | "external_service" | "other";
  identity: string;                          // the real shared thing, e.g. "tcp:5432"
  scope: "machine" | "unit" | "worktree";
  isolatable: boolean;                       // can a per-execution instance be provisioned
};
```

`scope` is the decision that makes this correct. A TCP port is `machine`, so two clones of the same
repository serialize on it — directly addressing the PRD's warning against "assuming different
repositories are independent". A temporary directory under the worktree is `worktree` and needs no lock. A
shared development database is `machine` or `unit` depending on how it is provisioned.

Allocation prefers isolation: when `isolatable`, a per-execution instance is provisioned and no lock is
taken. Otherwise a lease is acquired at the declared scope, with a heartbeat and expiry, reclaimable after
the holder is reconciled — the same pattern as the merge lease in spec 01, for the same crash-recovery
reason.

Coordination applies to target validation and candidate validation alike, since both run the same checks
and would otherwise collide with each other.

Container orchestration is not required for v4: isolation where the tool supports it, serialization
otherwise.

### Reuse and invalidation

A report may be reused only when its `subjectRevision`, `ruleSetVersion`, `toolVersion`, and command
reference all match what is being assessed. Any difference requires a fresh run. This is what prevents a
target report from a previous comparison being reused after the target advanced, and it is checked at the
point of consumption rather than trusted from a cache key.

### Initial adapter set

From §14.1, the approved initial set: npm, pnpm, and yarn with TypeScript, ESLint with typescript-eslint,
Vitest, and dependency-cruiser; uv and pip with Ruff, pytest, Import Linter, and pip-audit; Gitleaks and
license checks where configured. Each is a separate adapter with its own native-output parser and its own
conformance test against recorded real tool output.

Generic support does not imply universal analysis coverage. Each adapter's `declaredCoverage` states what
its tool actually examines, and that string travels with every report.

### Mutation adapter

An optional adapter, off by default, whose purpose is to measure verification strength rather than to find
defects in the source. It exists because removal, skipping, and disabling of tests are detectable from
configuration and collection, while an assertion weakened in place is not — a test changed from an equality
check to a presence check still runs, still passes, and still covers its criterion. A surviving mutant is
the one deterministic signal that distinguishes the two.

```ts
type MutationOutcome = {
  mutant: { operator: string; path: string; symbol?: string; contentAnchor: string };
  result: "killed_by_assertion" | "survived" | "killed_by_timeout" | "no_coverage" | "compile_error";
};
```

Decisions that make it usable:

**Scope.** Mutants are generated only for code touched by the PBI's diff and for code covered by the tests
the diff modified. Whole-repository mutation is never run.

**Only assertion kills are evidence of strength.** A mutant killed because it hung is a mutant the test
suite did not actually discriminate; it was killed by the clock. `killed_by_timeout` is recorded and
displayed, and a change in its count is visible, but it never contributes to the differential decision.
Only a transition from `killed_by_assertion` to `survived` produces a finding.

**Per-mutant limits are derived, not fixed.** A mutant can send code into an infinite loop, so some bound
per mutant is unavoidable — otherwise one mutant halts the check forever. That bound is derived from the
unmutated suite's own measured duration times a declared factor, never a wall-clock constant, so it scales
with the repository rather than with the machine.

**No wall-clock limit on the check itself.** Gantry runs AFK: the operator's expectation is that a task is
dispatched and carried through, not that it finishes inside a budget. The mutation check takes as long as
it takes, and its duration is recorded rather than enforced. This is consistent with §6.2, which
establishes no elapsed-time limit anywhere in the workflow.

**Comparability is enforced through resources, not through tolerance.** The mutation run declares a
`machine`-scoped check resource, so target and candidate runs serialize against each other and against any
other mutation run on the machine. Load variation between the two sides of a comparison is the main way a
mutation score becomes noise, and serializing removes it at the source instead of absorbing it with a
threshold.

A surviving mutant is a `NormalizedFinding` with `rule: "mutation:<operator>"` and the identity derivation
above, so the entropy gate in spec 13 compares it like any other finding with no special case.

Initial tools: Stryker for TypeScript and JavaScript, mutmut for Python. Both support incremental
operation, which is what makes diff-scoped runs practical.

**What makes a good test here.** Two layers.

Behavioral tests use the seam from spec 01 with a scripted adapter satisfying the real interface, driving
gate evaluation and asserting on completeness rejections, matching outcomes, stability behavior, resource
serialization, and reuse decisions. Matching is tested by feeding constructed target and candidate reports
and asserting which findings are classified as introduced, aggravated, preexisting, or improved.

Adapter conformance tests are separate: each adapter parses recorded real output from its tool — captured
fixture files, not a live tool run — and produces findings with the expected normalized shape and stable
identities. This keeps the suite fast and hermetic while still proving the parsers against reality.

**The seam.** Unchanged. Resource locking is tested across two OS processes, like the merge lease, because
a `machine`-scoped lock that is really an in-process mutex would pass a same-process test and fail the
requirement.

**Modules under test.** The adapter interface, each tool's parser, identity derivation and fingerprinting,
count-based matching, completeness validation, classification scope and invalidation, `pass_fail` handling,
stability criteria and instability recording, resource declaration and scoped allocation, lease reclamation
after crash, and reuse invalidation.

**Scenarios that must exist**, from PRD §14.3 item 4:

- Each supported tool's recorded output parses into normalized findings with stable identities across two runs of the same input.
- A finding's identity is unchanged when unrelated edits shift its line number.
- A finding's identity is unchanged when the tool's message text changes between versions.
- Two occurrences of one rule within the same symbol get different identities through their content anchors.
- A tool reporting no symbol still yields per-occurrence identities, because the symbol is derived from the file and line rather than taken from the tool.
- A language with no available grammar falls back to `rule` + `path` + `contentAnchor`, and the finding records which fallback was used.
- A tool reporting no location at all falls back to count matching: target two, candidate three yields one introduced finding; target two, candidate one yields a recorded improvement that credits nothing.
- An edit to the anchored code changes the identity, and the result is reported as one improvement plus one introduced finding rather than as an unchanged one.
- A mutation run scoped to the diff produces findings only for touched code and for code covered by modified tests.
- A test weakened from an equality assertion to a presence assertion produces surviving mutants that were previously killed by assertion.
- A mutant transitioning from `killed_by_assertion` to `killed_by_timeout` is recorded and displayed but produces no finding and does not block.
- The per-mutant bound is derived from the measured unmutated suite duration, not from a constant, and scales when the fixture suite is made slower.
- The mutation check has no wall-clock limit; a long run completes and records its duration.
- Two mutation runs serialize on the `machine`-scoped resource, including a target run and a candidate run of the same check.
- A finding missing `problemIdentity` leaves the gate unapproved and is not counted as zero findings.
- A report missing `toolVersion`, `ruleSetVersion`, or `declaredCoverage` is invalid evidence.
- An operator classification permits exactly one finding in one report version; the same finding in a new report version is blocked again.
- A classification is invalidated by a revision change, a rule version change, and a change to the finding itself.
- A classification from a non-operator channel is rejected.
- No classification mechanism exists that covers a rule globally or suppresses unrelated findings.
- A `pass_fail` outcome satisfies a mandatory check and cannot contribute to non-regression.
- `declaredCoverage` appears with the report wherever its evidence is surfaced.
- A check with `consecutive: 2` is not satisfied by one passing run; a `quorum` criterion is evaluated as declared.
- Inconsistent outcomes are appended as observed instability, surface as a check problem, and leave the gate unapproved.
- Instability consumes no infrastructure retry allowance; an adapter `infrastructure` failure does.
- An adapter `permanent` failure blocks without spending retries.
- A check that runs and reports findings is treated as working, not broken.
- A `machine`-scoped port is serialized across two different units; a `worktree`-scoped temporary directory is not locked.
- An `isolatable` resource is provisioned per execution and takes no lock.
- Target and candidate validation of the same check serialize against each other on a shared resource.
- A resource lease whose holder crashed is reclaimed only after reconciliation, proven across two processes.
- A report is reused when revision, rules, tool version, and command all match, and a fresh run is required when any differs.

## Out of Scope

- **The gate decision itself** (spec 13): what counts as aggravated, how absolute rules block, evidence consolidation, adversarial review, and the correction loop. This spec produces and validates evidence; spec 13 decides.
- **Operations, state machine, leases as a general mechanism, budgets** (spec 01).
- **Approved command definitions, coverage declaration collection, tool detection, missing-tooling preparation** (spec 06): this spec runs approved commands and reports their coverage.
- **Limit and configuration values, snapshot binding** (spec 02).
- **Redaction and retention of reports and tool output** (spec 04).
- **Scheduling and serialization of PBIs on resources** (spec 11): this spec owns the resource declarations and locks; spec 11 consults them for eligibility.
- **Changing an approved check, tool version, or rule set** (spec 15): this spec binds evidence to versions; spec 15 governs changing them.
- **Mandatory test re-execution for Implementation Completion** (spec 03): this spec provides the execution mechanism; the completion rule is spec 03's.
- **Provider-side checks on a Pull Request** (spec 14): those are GitHub's results, not adapter reports.

Out of scope by product decision:

- Semantic analysis beyond what the configured tools perform. §7.5 forbids claiming complete quality coverage from unimplemented checks.
- A global finding waiver or rule-level suppression. §7.5 permits only per-finding, per-report-version classification.
- Container orchestration for isolation. §7.5 states it is not required for v4.
- Unlimited reruns to obtain a green result. §7.5 forbids hiding flakiness that way.
- Line numbers in problem identity. They would invalidate every finding in an edited file.

## Further Notes

**Binding decisions.** ADR-0002 is why resource scope exists as a declared field: worktree isolation is
the accepted mechanism for source separation, and the ADR's cost — that isolation is per worktree — is
exactly why a port must be declared `machine` rather than inheriting the worktree's separation.

**Glossary alignment.** Comparison Evidence, Evidence Completeness, Check Stability, and Check Resource
follow `CONTEXT.md`, including the terms it marks to avoid: comparison evidence is not an exit code alone
or an absent report; completeness does not treat missing fields as clean and admits no global manual
waiver; stability is not a single green run or unlimited rerun; a check resource is not established by
worktree isolation alone.

**Glossary gap for `/domain-modeling`.** Problem identity, message fingerprint, and resource scope are
introduced here without entries and should get them.

**Where the risk actually sits.** The content anchor moves the weakness rather than removing it. It is
strong where code is distinctive and weak where it is repetitive: generated code, long literal tables, and
files with many structurally identical lines can produce two occurrences whose anchors collide, which
returns those specific findings to count-based behaviour within their symbol. That is a much smaller
surface than the previous fallback covered, and the finding records which derivation was used so a
consumer can tell. The alternative — line-based identity — fails far more often and more confusingly.

The second risk is tree-sitter grammar coverage. Symbol derivation is only as good as the available
grammar, so a repository in a language outside the approved adapter set falls to the no-symbol path, and a
grammar that parses a file incorrectly produces a wrong but stable symbol. Wrong-but-stable is tolerable
because identity only needs to be consistent between two revisions, not semantically correct; a grammar
that parses *inconsistently* across versions would be worse, which is why the grammar version belongs with
the tool version in the report's reuse check.

The third risk is the mutation adapter's cost profile. It is the slowest check in the system by a wide
margin, and although AFK execution makes duration acceptable, it consumes a `machine`-scoped resource that
serializes against every other mutation run — so on a machine running several repositories, mutation
checks queue behind each other and observed parallelism drops. That is the correct trade for comparable
evidence, but it is the reason the adapter is opt-in rather than default, and repositories that enable it
should expect throughput to fall.

**Sequencing note.** This spec depends on spec 06 for approved commands and is the prerequisite for spec
13, which cannot decide anything without matched evidence. The finding shape and identity derivation are
the pieces to settle first, since every adapter parser and the entire gate decision are written against
them.
